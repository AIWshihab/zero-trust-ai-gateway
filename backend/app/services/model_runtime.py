from fastapi import HTTPException, status

from app.core.config import get_settings
from app.schemas import ModelType, ScanStatus
from app.services.chat_errors import model_setup_error
from app.services.model_readiness import READY_SCAN_STATUSES, normalize_scan_status


def _as_model_type(value) -> str:
    if hasattr(value, "value"):
        value = value.value
    return str(value or "").strip().lower()


def _hf_model_id(model) -> str:
    model_id = (getattr(model, "hf_model_id", None) or "").strip()
    if model_id:
        return model_id

    source_url = (getattr(model, "source_url", None) or "").strip()
    if "huggingface.co/" not in source_url:
        return ""

    model_id = source_url.split("huggingface.co/", 1)[1].strip("/")
    return model_id.split("/tree/", 1)[0].split("/blob/", 1)[0]


def get_model_runtime_status(model) -> dict:
    settings = get_settings()
    model_type = _as_model_type(getattr(model, "model_type", None))
    provider = str(getattr(model, "provider_name", "") or "").strip().lower()
    scan_status = normalize_scan_status(getattr(model, "scan_status", None))
    base_trust_score = getattr(model, "base_trust_score", None)

    base = {
        "model_id": getattr(model, "id", None),
        "name": getattr(model, "name", None),
        "model_type": model_type,
        "provider_name": getattr(model, "provider_name", None),
        "scan_status": scan_status,
        "missing": [],
        "can_prescreen": True,
        "endpoint_checked": False,
    }

    def status_payload(
        *,
        code: str,
        label: str,
        runtime_ready: bool,
        title: str,
        reason: str,
        explanation: str,
        suggested_fix: str,
        action_required: str,
        missing: list[str] | None = None,
        http_status: int = status.HTTP_503_SERVICE_UNAVAILABLE,
        endpoint_checked: bool = False,
    ) -> dict:
        return {
            **base,
            "runtime_ready": runtime_ready,
            "can_infer": runtime_ready,
            "status": code,
            "label": label,
            "title": title,
            "reason": reason,
            "explanation": explanation,
            "message": explanation,
            "suggested_fix": suggested_fix,
            "next_step": suggested_fix,
            "action_required": action_required,
            "missing": missing or [],
            "http_status": http_status,
            "endpoint_checked": endpoint_checked,
        }

    if not bool(getattr(model, "is_active", True)):
        return status_payload(
            code="disabled_inactive",
            label="Disabled/inactive",
            runtime_ready=False,
            title="Model disabled",
            reason="This model is inactive in the registry.",
            explanation="The gateway will not send chat traffic to disabled models.",
            suggested_fix="Ask an admin to reactivate or replace this model.",
            action_required="admin",
            http_status=status.HTTP_403_FORBIDDEN,
        )

    if base_trust_score is None or scan_status not in READY_SCAN_STATUSES:
        return status_payload(
            code="needs_assessment",
            label="Needs assessment",
            runtime_ready=False,
            title="Needs assessment",
            reason=f"Scan status is '{scan_status}'.",
            explanation="The gateway can pre-screen prompts, but it will not call a model until its security assessment is completed or protected.",
            suggested_fix="Ask an admin to run the model assessment scan and enable protection.",
            action_required="admin",
            http_status=status.HTTP_409_CONFLICT,
        )

    missing: list[str] = []

    if model_type == ModelType.HUGGINGFACE.value or provider == "huggingface":
        if not getattr(settings, "HF_TOKEN", ""):
            missing.append("HF_TOKEN")
        if not _hf_model_id(model):
            missing.append("hf_model_id")
        if missing:
            return status_payload(
                code="missing_token_config",
                label="Missing token/config",
                runtime_ready=False,
                title="Missing Hugging Face configuration",
                reason=f"Missing: {', '.join(missing)}.",
                explanation="This Hugging Face model is registered and assessed, but the server cannot call it until the Hugging Face token and model id are configured.",
                suggested_fix="Ask an admin to set HF_TOKEN in backend/.env and confirm the Hugging Face model id.",
                action_required="admin",
                missing=missing,
            )
    elif model_type == ModelType.OPENAI.value or provider == "openai":
        if not getattr(settings, "OPENAI_API_KEY", ""):
            missing.append("OPENAI_API_KEY")
        if missing:
            return status_payload(
                code="missing_token_config",
                label="Missing token/config",
                runtime_ready=False,
                title="Missing OpenAI configuration",
                reason="OPENAI_API_KEY is not configured.",
                explanation="This OpenAI model is registered and assessed, but the server cannot call OpenAI until the API key is configured.",
                suggested_fix="Ask an admin to set OPENAI_API_KEY in backend/.env.",
                action_required="admin",
                missing=missing,
            )
    elif model_type in {ModelType.LOCAL.value, ModelType.CUSTOM_API.value}:
        if not getattr(model, "endpoint", None):
            return status_payload(
                code="not_hosted_callable",
                label="Not hosted/callable",
                runtime_ready=False,
                title="Model endpoint missing",
                reason="No runtime endpoint is configured for this model.",
                explanation="The model exists in the registry, but the gateway has no hosted endpoint to call for chat.",
                suggested_fix="Ask an admin to add a reachable local/custom model endpoint.",
                action_required="admin",
                missing=["endpoint"],
            )
    else:
        return status_payload(
            code="unsupported_runtime",
            label="Not hosted/callable",
            runtime_ready=False,
            title="Unsupported model runtime",
            reason=f"Model type '{model_type or 'unknown'}' is not supported by the chat router.",
            explanation="The registry record is valid as data, but the chat runtime does not know how to call this model type.",
            suggested_fix="Ask an admin to register it as OpenAI, Hugging Face, local, or custom API.",
            action_required="admin",
            missing=["supported_model_type"],
        )

    return status_payload(
        code="ready",
        label="Ready",
        runtime_ready=True,
        title="Ready",
        reason="Model assessment and runtime configuration are complete.",
        explanation="This model can receive protected chat requests through the gateway.",
        suggested_fix="Send a prompt. The gateway will still run prompt guard, policy, adaptive risk, and output guard.",
        action_required="none",
        http_status=status.HTTP_200_OK,
    )


def ensure_model_runtime_ready(model) -> None:
    runtime = get_model_runtime_status(model)
    if runtime["runtime_ready"]:
        return
    detail = model_setup_error(
        code=runtime["status"],
        title=runtime["title"],
        reason=runtime["reason"],
        explanation=runtime["explanation"],
        suggested_fix=runtime["suggested_fix"],
        action_required=runtime["action_required"],
        metadata={
            "model_id": runtime["model_id"],
            "missing": runtime["missing"],
            "label": runtime["label"],
            "can_prescreen": runtime["can_prescreen"],
            "scan_status": runtime["scan_status"],
        },
    )
    raise HTTPException(
        status_code=runtime["http_status"],
        detail=detail,
    )
