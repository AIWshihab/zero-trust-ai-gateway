from types import SimpleNamespace

from fastapi import HTTPException

from app.schemas import ModelType, ScanStatus
from app.services.model_readiness import ensure_model_ready
from app.services.model_runtime import ensure_model_runtime_ready, get_model_runtime_status


def _model(**overrides):
    data = {
        "id": 1,
        "name": "Test model",
        "model_type": ModelType.HUGGINGFACE,
        "provider_name": "huggingface",
        "hf_model_id": "org/model",
        "endpoint": None,
        "is_active": True,
        "base_trust_score": 80.0,
        "scan_status": ScanStatus.PROTECTED.value,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def test_model_selector_status_missing_hf_token(monkeypatch):
    monkeypatch.setattr(
        "app.services.model_runtime.get_settings",
        lambda: SimpleNamespace(HF_TOKEN="", OPENAI_API_KEY=""),
    )

    status = get_model_runtime_status(_model())

    assert status["label"] == "Missing token/config"
    assert status["runtime_ready"] is False
    assert status["can_prescreen"] is True
    assert "HF_TOKEN" in status["missing"]
    assert status["title"] == "Missing Hugging Face configuration"


def test_model_selector_status_needs_assessment(monkeypatch):
    monkeypatch.setattr(
        "app.services.model_runtime.get_settings",
        lambda: SimpleNamespace(HF_TOKEN="hf_test", OPENAI_API_KEY=""),
    )

    status = get_model_runtime_status(
        _model(base_trust_score=None, scan_status=ScanStatus.PENDING.value)
    )

    assert status["label"] == "Needs assessment"
    assert status["runtime_ready"] is False
    assert status["http_status"] == 409


def test_not_hosted_model_returns_clear_status(monkeypatch):
    monkeypatch.setattr(
        "app.services.model_runtime.get_settings",
        lambda: SimpleNamespace(HF_TOKEN="", OPENAI_API_KEY=""),
    )

    status = get_model_runtime_status(
        _model(
            model_type=ModelType.LOCAL,
            provider_name="local",
            hf_model_id=None,
            endpoint=None,
        )
    )

    assert status["label"] == "Not hosted/callable"
    assert status["runtime_ready"] is False
    assert status["missing"] == ["endpoint"]


def test_ready_model_can_send(monkeypatch):
    monkeypatch.setattr(
        "app.services.model_runtime.get_settings",
        lambda: SimpleNamespace(HF_TOKEN="hf_test", OPENAI_API_KEY=""),
    )

    status = get_model_runtime_status(_model())

    assert status["label"] == "Ready"
    assert status["runtime_ready"] is True
    ensure_model_runtime_ready(_model())


def test_missing_hf_token_raises_structured_error(monkeypatch):
    monkeypatch.setattr(
        "app.services.model_runtime.get_settings",
        lambda: SimpleNamespace(HF_TOKEN="", OPENAI_API_KEY=""),
    )

    try:
        ensure_model_runtime_ready(_model())
    except HTTPException as exc:
        assert exc.status_code == 503
        assert exc.detail["title"] == "Missing Hugging Face configuration"
        assert exc.detail["action_required"] == "admin"
        assert "HF_TOKEN" in exc.detail["metadata"]["missing"]
    else:
        raise AssertionError("Expected missing HF_TOKEN to raise HTTPException")


def test_model_not_scanned_raises_structured_error():
    try:
        ensure_model_ready(
            _model(base_trust_score=None, scan_status=ScanStatus.PENDING.value),
            action="inference",
        )
    except HTTPException as exc:
        assert exc.status_code == 409
        assert exc.detail["title"] == "Needs assessment"
        assert exc.detail["code"] == "model_needs_assessment"
    else:
        raise AssertionError("Expected unassessed model to raise HTTPException")
