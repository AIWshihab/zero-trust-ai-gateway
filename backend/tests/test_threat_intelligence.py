import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.user import User  # noqa: F401
from app.schemas import RequestDecision
from app.services.threat_intelligence import (
    build_research_metrics,
    classify_attack_stage,
    get_user_attack_sequence_summary,
    update_attack_sequence,
)


def test_attack_stage_classification_from_flags_and_decision():
    assert classify_attack_stage(flags=[], decision=RequestDecision.ALLOW, risk_score=0.02, security_score=0.1) == "safe_prompt"
    assert classify_attack_stage(flags=["combo_system_prompt"], decision=RequestDecision.CHALLENGE, risk_score=0.4) == "prompt_injection"
    assert classify_attack_stage(flags=["extraction_prompt_leak"], decision=RequestDecision.BLOCK, risk_score=0.7) == "secret_extraction_attempt"
    assert classify_attack_stage(flags=["injection_jailbreak"], decision=RequestDecision.BLOCK, risk_score=0.8) == "jailbreak_attempt"
    assert classify_attack_stage(flags=[], decision=RequestDecision.BLOCK, risk_score=1.0, cooldown_active=True) == "cooldown_triggered"


def test_attack_sequence_persistence_and_cross_model_score():
    async def scenario():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with session_factory() as db:
            await update_attack_sequence(
                db,
                user_id=1,
                model_id=1,
                event_type="prompt_detection",
                decision=RequestDecision.CHALLENGE,
                risk_score=0.55,
                security_score=0.45,
                flags=["injection_ignore_instructions"],
                prompt_hash="hash-one",
                reason="Prompt requires challenge.",
                metadata={"note": "no raw prompt text"},
                commit=True,
            )
            await update_attack_sequence(
                db,
                user_id=1,
                model_id=2,
                event_type="safe_inference_block",
                decision=RequestDecision.BLOCK,
                risk_score=0.72,
                security_score=0.66,
                flags=["extraction_prompt_leak"],
                prompt_hash="hash-two",
                reason="Blocked.",
                commit=True,
            )
            row = await update_attack_sequence(
                db,
                user_id=1,
                model_id=2,
                event_type="safe_inference_block",
                decision=RequestDecision.BLOCK,
                risk_score=0.78,
                security_score=0.7,
                flags=["extraction_prompt_leak"],
                prompt_hash="hash-three",
                reason="Blocked again.",
                commit=True,
            )

            summary = await get_user_attack_sequence_summary(db, user_id=1)
            assert summary["cross_model_abuse_score"] >= 0.55
            assert summary["cross_model_models"] == 2
            assert summary["repeated_pattern_count"] >= 2
            assert row is not None
            assert "prompt_hash" in row.metadata_json
            assert "ignore all instructions" not in str(row.metadata_json).lower()

        await engine.dispose()

    asyncio.run(scenario())


def test_research_metrics_response_shape():
    async def scenario():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with session_factory() as db:
            await update_attack_sequence(
                db,
                user_id=7,
                model_id=1,
                event_type="cooldown_block",
                decision=RequestDecision.BLOCK,
                risk_score=1.0,
                security_score=1.0,
                cooldown_active=True,
                reason="Temporary abuse penalty active.",
                commit=True,
            )
            metrics = await build_research_metrics(db)
            assert metrics["attack_sequence_count"] == 1
            assert metrics["cooldown_triggers"] == 1
            assert "top_attack_categories" in metrics
            assert "base_risk_vs_secured_risk" in metrics
            assert "false_positive_review_helpers" in metrics

        await engine.dispose()

    asyncio.run(scenario())
