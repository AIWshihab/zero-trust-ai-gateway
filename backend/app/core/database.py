import logging

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


logger.info("Database dialect configured: %s", settings.DATABASE_DIALECT)

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
    from app.models.chat import ChatSession, ChatMessage
    from app.models.extension import ExtensionPairingToken

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
        ChatSession,
        ChatMessage,
        ExtensionPairingToken,
    )

    if settings.AUTO_INIT_SCHEMA:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


async def init_additive_security_tables():
    from app.models.firewall import FirewallClient
    from app.models.model_risk_history import ModelRiskHistory
    from app.models.chat import ChatSession, ChatMessage
    from app.models.extension import ExtensionPairingToken

    async with engine.begin() as conn:
        await conn.run_sync(FirewallClient.__table__.create, checkfirst=True)
        await conn.run_sync(ModelRiskHistory.__table__.create, checkfirst=True)
        await conn.run_sync(ChatSession.__table__.create, checkfirst=True)
        await conn.run_sync(ChatMessage.__table__.create, checkfirst=True)
        await conn.run_sync(ExtensionPairingToken.__table__.create, checkfirst=True)
        columns = await conn.run_sync(
            lambda sync_conn: {
                column["name"]
                for column in inspect(sync_conn).get_columns("extension_pairing_tokens")
            }
        )
        missing_columns = {
            "setup_session_id": "VARCHAR(64)",
            "registered_device_id": "INTEGER",
            "connected_at": "TIMESTAMP",
            "browser_name": "VARCHAR(80)",
            "extension_version": "VARCHAR(32)",
        }
        for column_name, column_type in missing_columns.items():
            if column_name not in columns:
                await conn.execute(
                    text(
                        f"ALTER TABLE extension_pairing_tokens "
                        f"ADD COLUMN {column_name} {column_type}"
                    )
                )
        await conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS "
                "ix_extension_pairing_tokens_setup_session_id "
                "ON extension_pairing_tokens (setup_session_id)"
            )
        )
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS "
                "ix_extension_pairing_tokens_registered_device_id "
                "ON extension_pairing_tokens (registered_device_id)"
            )
        )
