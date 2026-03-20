from datetime import datetime
from typing import Dict, Optional
from app.models.schemas import ModelCreate, ModelOut, RiskLevel, SensitivityLevel, ModelType


# ─── In-Memory Registry (swap for DB in Stage 4) ──────────────────────────────

_model_registry: Dict[int, dict] = {}
_id_counter: int = 1


# ─── Risk & Sensitivity Mappings ──────────────────────────────────────────────

RISK_SCORE_MAP = {
    RiskLevel.LOW: 0.2,
    RiskLevel.MEDIUM: 0.5,
    RiskLevel.HIGH: 0.9,
}

SENSITIVITY_SCORE_MAP = {
    SensitivityLevel.LOW: 0.1,
    SensitivityLevel.MEDIUM: 0.4,
    SensitivityLevel.HIGH: 0.7,
    SensitivityLevel.CRITICAL: 1.0,
}


# ─── CRUD Operations ──────────────────────────────────────────────────────────

def register_model(model: ModelCreate) -> ModelOut:
    global _id_counter
    record = {
        "id": _id_counter,
        **model.model_dump(),
        "created_at": datetime.utcnow(),
    }
    _model_registry[_id_counter] = record
    _id_counter += 1
    return ModelOut(**record)


def get_model(model_id: int) -> Optional[ModelOut]:
    record = _model_registry.get(model_id)
    if not record:
        return None
    return ModelOut(**record)


def get_all_models() -> list[ModelOut]:
    return [ModelOut(**record) for record in _model_registry.values()]


def deactivate_model(model_id: int) -> bool:
    if model_id not in _model_registry:
        return False
    _model_registry[model_id]["is_active"] = False
    return True


def get_model_risk_score(model_id: int) -> float:
    model = get_model(model_id)
    if not model:
        return 1.0  # default to max risk if model unknown
    return RISK_SCORE_MAP.get(model.risk_level, 0.5)


def get_model_sensitivity_score(model_id: int) -> float:
    model = get_model(model_id)
    if not model:
        return 1.0  # default to max sensitivity if model unknown
    return SENSITIVITY_SCORE_MAP.get(model.sensitivity_level, 0.5)


# ─── Seed Default Models (for development/testing) ────────────────────────────

def seed_default_models():
    defaults = [
        ModelCreate(
            name="GPT-4o",
            description="OpenAI GPT-4o via API",
            model_type=ModelType.OPENAI,
            sensitivity_level=SensitivityLevel.HIGH,
            risk_level=RiskLevel.MEDIUM,
            endpoint="https://api.openai.com/v1/chat/completions",
            is_active=True,
        ),
        ModelCreate(
            name="Mistral-7B",
            description="Local HuggingFace Mistral model",
            model_type=ModelType.HUGGINGFACE,
            sensitivity_level=SensitivityLevel.MEDIUM,
            risk_level=RiskLevel.LOW,
            endpoint="http://localhost:8001/generate",
            is_active=True,
        ),
        ModelCreate(
            name="Internal Classifier",
            description="Sensitive internal classification model",
            model_type=ModelType.LOCAL,
            sensitivity_level=SensitivityLevel.CRITICAL,
            risk_level=RiskLevel.HIGH,
            endpoint=None,
            is_active=True,
        ),
    ]
    for model in defaults:
        register_model(model)
