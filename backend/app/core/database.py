from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db():
    # Import models so SQLAlchemy metadata is fully registered.
    # We intentionally avoid unconditional create_all() here to prevent
    # migration drift; schema should be managed by Alembic.
    from app.models.user import User
    from app.models.model import Model
    from app.models.request_log import RequestLog
    from app.models.user_trust_event import UserTrustEvent
    from app.models.model_posture_event import ModelPostureEvent
    from app.models.security import SecurityControl, DetectionRule
    from app.models.attack_sequence_event import AttackSequenceEvent
    from app.models.firewall import FirewallClient
    from app.models.model_risk_history import ModelRiskHistory

    _ = (
        User,
        Model,
        RequestLog,
        UserTrustEvent,
        ModelPostureEvent,
        SecurityControl,
        DetectionRule,
        AttackSequenceEvent,
        FirewallClient,
        ModelRiskHistory,
    )

    if settings.AUTO_INIT_SCHEMA:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


async def init_additive_security_tables():
    from app.models.firewall import FirewallClient
    from app.models.model_risk_history import ModelRiskHistory

    async with engine.begin() as conn:
        await conn.run_sync(FirewallClient.__table__.create, checkfirst=True)
        await conn.run_sync(ModelRiskHistory.__table__.create, checkfirst=True)
