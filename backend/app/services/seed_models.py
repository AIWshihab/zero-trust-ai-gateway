"""
Seed global preset models that are visible to every user.
Called once at startup — idempotent (skips if already present).
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model import Model
from app.schemas import ModelType, RiskLevel, SensitivityLevel, ScanStatus


PRESET_MODELS = [
    {
        "name": "Qwen 2.5 7B Instruct",
        "description": "Qwen 2.5 7B Instruct by Alibaba — fast, capable chat model available via HuggingFace Inference Router. Available to all users.",
        "model_type": ModelType.HUGGINGFACE,
        "provider_name": "Alibaba / Qwen",
        "hf_model_id": "Qwen/Qwen2.5-7B-Instruct",
        "source_url": "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct",
        "visibility": "global",
        "owner_user_id": None,
        "is_active": True,
        "scan_status": ScanStatus.COMPLETED,
        "risk_level": RiskLevel.LOW,
        "sensitivity_level": SensitivityLevel.LOW,
        "base_trust_score": 75.0,
        "base_risk_score": 25.0,
        "secured_risk_score": 12.0,
        "has_model_card": True,
        "supports_https": True,
        "requires_auth": False,
    },
    {
        "name": "Llama 3.1 8B Instruct",
        "description": "Meta Llama 3.1 8B Instruct — open-source instruction model via HuggingFace Inference Router. Available to all users.",
        "model_type": ModelType.HUGGINGFACE,
        "provider_name": "Meta",
        "hf_model_id": "meta-llama/Llama-3.1-8B-Instruct",
        "source_url": "https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct",
        "visibility": "global",
        "owner_user_id": None,
        "is_active": True,
        "scan_status": ScanStatus.COMPLETED,
        "risk_level": RiskLevel.LOW,
        "sensitivity_level": SensitivityLevel.LOW,
        "base_trust_score": 78.0,
        "base_risk_score": 22.0,
        "secured_risk_score": 11.0,
        "has_model_card": True,
        "supports_https": True,
        "requires_auth": False,
    },
    {
        "name": "GPT-4o Mini",
        "description": "OpenAI GPT-4o Mini — fast, cost-efficient OpenAI model. Uses the configured OPENAI_API_KEY. Available to all users.",
        "model_type": ModelType.OPENAI,
        "provider_name": "OpenAI",
        "hf_model_id": "gpt-4o-mini",
        "source_url": "https://platform.openai.com/docs/models/gpt-4o-mini",
        "visibility": "global",
        "owner_user_id": None,
        "is_active": True,
        "scan_status": ScanStatus.COMPLETED,
        "risk_level": RiskLevel.LOW,
        "sensitivity_level": SensitivityLevel.MEDIUM,
        "base_trust_score": 85.0,
        "base_risk_score": 15.0,
        "secured_risk_score": 8.0,
        "has_model_card": True,
        "supports_https": True,
        "requires_auth": True,
    },
]

# Models that are known to be broken/unsupported by the HF router.
# Deactivated automatically on startup so they don't confuse users.
_BROKEN_HF_MODEL_IDS = {
    "mistralai/Mistral-7B-Instruct-v0.3",
    "mistralai/Mistral-7B-Instruct-v0.1",
    "mistralai/Mistral-Nemo-Instruct-2407",
}


async def seed_preset_models(db: AsyncSession) -> None:
    # Always-update fields — hf_model_id is included so broken rows get fixed.
    ALWAYS_PATCH = {"hf_model_id", "source_url", "description", "provider_name"}
    # Patch-if-null fields — scores added after the fact.
    PATCH_IF_NULL = {"base_trust_score", "base_risk_score", "secured_risk_score", "scan_status", "is_active"}

    for spec in PRESET_MODELS:
        result = await db.execute(
            select(Model).where(
                Model.name == spec["name"],
                Model.visibility == "global",
                Model.owner_user_id.is_(None),
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            changed = False
            for field in ALWAYS_PATCH:
                if field in spec and getattr(existing, field, None) != spec[field]:
                    setattr(existing, field, spec[field])
                    changed = True
            for field in PATCH_IF_NULL:
                if field in spec and getattr(existing, field, None) is None:
                    setattr(existing, field, spec[field])
                    changed = True
            if changed:
                existing.updated_at = datetime.now(timezone.utc)
            continue

        now = datetime.now(timezone.utc)
        db.add(Model(**spec, created_at=now, updated_at=now))

    # Deactivate known-broken global models so they don't surface to users.
    for broken_id in _BROKEN_HF_MODEL_IDS:
        result = await db.execute(
            select(Model).where(
                Model.hf_model_id == broken_id,
                Model.visibility == "global",
                Model.is_active.is_(True),
            )
        )
        broken_row = result.scalar_one_or_none()
        if broken_row is not None:
            broken_row.is_active = False
            broken_row.updated_at = datetime.now(timezone.utc)

    await db.commit()
