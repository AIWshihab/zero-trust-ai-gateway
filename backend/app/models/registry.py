from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import ModelCreate, ModelOut, RiskLevel, SensitivityLevel, ModelType
from app.models.model import Model


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


async def register_model(db: AsyncSession, model: ModelCreate) -> ModelOut:
    db_model = Model(**model.model_dump())
    db.add(db_model)
    await db.commit()
    await db.refresh(db_model)
    return ModelOut.model_validate(db_model)


async def get_model(db: AsyncSession, model_id: int) -> Optional[ModelOut]:
    result = await db.execute(
        select(Model).where(Model.id == model_id)
    )
    db_model = result.scalar_one_or_none()

    if not db_model:
        return None

    return ModelOut.model_validate(db_model)


async def get_all_models(db: AsyncSession) -> List[ModelOut]:
    result = await db.execute(select(Model))
    models = result.scalars().all()
    return [ModelOut.model_validate(m) for m in models]


async def deactivate_model(db: AsyncSession, model_id: int) -> bool:
    result = await db.execute(
        select(Model).where(Model.id == model_id)
    )
    db_model = result.scalar_one_or_none()

    if not db_model:
        return False

    db_model.is_active = False
    await db.commit()
    return True


async def get_model_risk_score(db: AsyncSession, model_id: int) -> float:
    result = await db.execute(
        select(Model).where(Model.id == model_id)
    )
    db_model = result.scalar_one_or_none()

    if not db_model:
        return 1.0

    return RISK_SCORE_MAP.get(db_model.risk_level, 0.5)


async def get_model_sensitivity_score(db: AsyncSession, model_id: int) -> float:
    result = await db.execute(
        select(Model).where(Model.id == model_id)
    )
    db_model = result.scalar_one_or_none()

    if not db_model:
        return 1.0

    return SENSITIVITY_SCORE_MAP.get(db_model.sensitivity_level, 0.5)


async def seed_default_models(db: AsyncSession) -> None:
    result = await db.execute(select(Model).limit(1))
    existing = result.scalar_one_or_none()
    if existing:
        return

    defaults = [
        Model(
            name="GPT-4o",
            description="OpenAI GPT-4o via API",
            model_type=ModelType.OPENAI,
            sensitivity_level=SensitivityLevel.HIGH,
            risk_level=RiskLevel.MEDIUM,
            endpoint="https://api.openai.com/v1/chat/completions",
            is_active=True,
        ),
        Model(
            name="Mistral-7B",
            description="Local HuggingFace Mistral model",
            model_type=ModelType.HUGGINGFACE,
            sensitivity_level=SensitivityLevel.MEDIUM,
            risk_level=RiskLevel.LOW,
            endpoint="http://localhost:8001/generate",
            is_active=True,
        ),
        Model(
            name="Internal Classifier",
            description="Sensitive internal classification model",
            model_type=ModelType.LOCAL,
            sensitivity_level=SensitivityLevel.CRITICAL,
            risk_level=RiskLevel.HIGH,
            endpoint=None,
            is_active=True,
        ),
    ]

    db.add_all(defaults)
    await db.commit()