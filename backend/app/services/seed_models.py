"""
Seed global preset models that are visible to every user.
Called once at startup — idempotent (skips if already present).
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model import Model
from app.schemas import ModelType, RiskLevel, SensitivityLevel, ScanStatus


PRESET_MODELS = [
    {
        "name": "Mistral 7B Instruct",
        "description": "Open-source 7B parameter instruction-following model by Mistral AI. Available to all users.",
        "model_type": ModelType.HUGGINGFACE,
        "provider_name": "Mistral AI",
        "hf_model_id": "mistralai/Mistral-7B-Instruct-v0.3",
        "source_url": "https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3",
        "visibility": "global",
        "owner_user_id": None,
        "is_active": True,
        "scan_status": ScanStatus.COMPLETED,
        "risk_level": RiskLevel.LOW,
        "sensitivity_level": SensitivityLevel.LOW,
        "has_model_card": True,
        "supports_https": True,
        "requires_auth": False,
    },
]


async def seed_preset_models(db: AsyncSession) -> None:
    for spec in PRESET_MODELS:
        existing = await db.execute(
            select(Model).where(
                Model.name == spec["name"],
                Model.visibility == "global",
                Model.owner_user_id.is_(None),
            )
        )
        if existing.scalar_one_or_none() is not None:
            continue

        db.add(Model(**spec))

    await db.commit()
