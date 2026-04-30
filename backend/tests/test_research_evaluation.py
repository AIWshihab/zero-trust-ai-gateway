import asyncio
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.attack_sequence_event import AttackSequenceEvent  # noqa: F401
from app.models.model import Model  # noqa: F401
from app.models.request_log import RequestLog
from app.models.security import DetectionRule, SecurityControl  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.user_trust_event import UserTrustEvent  # noqa: F401
from app.services.research_evaluation import (
    build_control_effectiveness,
    build_counterfactual_analysis,
    build_policy_replay,
    build_risk_drift,
)


def _trace(**overrides):
    inputs = {
        "model_risk_score": 0.25,
        "sensitivity_score": 0.25,
        "prompt_risk_score": 0.7,
        "request_rate_score": 0.1,
        "user_trust_penalty": 0.1,
        "secure_mode_enabled": True,
        "recent_risky_events": 0,
        "recent_blocks": 0,
        "recent_challenges": 0,
        "model_base_risk_score": 30,
        "attack_sequence_severity": 0.0,
        "repeated_pattern_count": 0,
        "cross_model_abuse_score": 0.0,
    }
    inputs.update(overrides)
    return {
        "inputs": inputs,
        "effective_thresholds": {"challenge": 0.35, "block": 0.65},
        "adaptive_reasons": ["secure mode baseline hardening applied"],
    }


async def _seed_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
        db.add_all(
            [
                SecurityControl(
                    control_id="LLM01",
                    name="Prompt Injection",
                    coverage="strong",
                    status="active",
                    control_family="input_security",
                    enabled=True,
                ),
                SecurityControl(
                    control_id="LLM10",
                    name="Unbounded Consumption",
                    coverage="moderate",
                    status="active",
                    control_family="abuse_prevention",
                    enabled=True,
                ),
                RequestLog(
                    user_id=1,
                    model_id=1,
                    prompt_hash="hash-one",
                    security_score=0.62,
                    prompt_risk_score=0.7,
                    output_risk_score=0.0,
                    decision="challenge",
                    blocked=False,
                    secure_mode_enabled=True,
                    reason="Prompt injection risk; secure mode adaptive hardening active.",
                    decision_input_snapshot={"prompt_flags": ["injection_ignore_instructions"]},
                    decision_trace=_trace(),
                    latency_ms=20,
                    timestamp=datetime(2026, 4, 26, 1, 0, tzinfo=timezone.utc),
                ),
                RequestLog(
                    user_id=1,
                    model_id=2,
                    prompt_hash="hash-two",
                    security_score=0.74,
                    prompt_risk_score=0.55,
                    output_risk_score=0.0,
                    decision="block",
                    blocked=True,
                    secure_mode_enabled=True,
                    reason="Repeated abuse and cross_model risk.",
                    decision_input_snapshot={"prompt_flags": ["abuse_repeat"]},
                    decision_trace=_trace(
                        prompt_risk_score=0.55,
                        user_trust_penalty=0.35,
                        attack_sequence_severity=0.85,
                        repeated_pattern_count=5,
                        cross_model_abuse_score=0.8,
                    ),
                    latency_ms=28,
                    timestamp=datetime(2026, 4, 26, 1, 30, tzinfo=timezone.utc),
                ),
                AttackSequenceEvent(
                    user_id=1,
                    model_id=2,
                    event_type="safe_inference_block",
                    attack_stage="repeated_blocked_attempt",
                    decision="block",
                    risk_score=0.8,
                    security_score=0.74,
                    sequence_severity=0.85,
                    repeated_pattern_count=5,
                    cross_model_score=0.8,
                    timestamp=datetime(2026, 4, 26, 1, 31, tzinfo=timezone.utc),
                ),
            ]
        )
        await db.commit()
    return engine, session_factory


def test_policy_replay_output_shape_and_modes():
    async def scenario():
        engine, session_factory = await _seed_db()
        async with session_factory() as db:
            replay = await build_policy_replay(db)
            modes = {item["mode"]: item for item in replay["modes"]}
            assert replay["inference_rerun"] is False
            assert {"current", "stricter", "relaxed"} <= set(modes)
            assert modes["current"]["total_requests"] == 2
            assert "difference_vs_original" in modes["stricter"]
            assert "formal_risk_evaluation" in replay
            assert "effective_risk_distribution" in replay["formal_risk_evaluation"]
            assert "decision_consistency_metrics" in replay["formal_risk_evaluation"]
        await engine.dispose()

    asyncio.run(scenario())


def test_control_effectiveness_output_shape():
    async def scenario():
        engine, session_factory = await _seed_db()
        async with session_factory() as db:
            result = await build_control_effectiveness(db)
            controls = {item["control_id"]: item for item in result["controls"]}
            assert controls["LLM01"]["contribution_count"] >= 1
            assert controls["LLM10"]["contribution_count"] >= 1
            assert "contribution_percentage" in controls["LLM01"]
        await engine.dispose()

    asyncio.run(scenario())


def test_counterfactual_consistency():
    async def scenario():
        engine, session_factory = await _seed_db()
        async with session_factory() as db:
            result = await build_counterfactual_analysis(db)
            assert result["total_requests_analyzed"] == 2
            assert "difference_counts" in result
            assert "examples" in result
        await engine.dispose()

    asyncio.run(scenario())


def test_risk_drift_bucket_shape():
    async def scenario():
        engine, session_factory = await _seed_db()
        async with session_factory() as db:
            result = await build_risk_drift(db, bucket="hourly")
            assert result["bucket"] == "hourly"
            assert result["series"]
            assert result["series"][0]["request_count"] == 2
            assert "attack_sequence_intensity" in result["series"][0]
        await engine.dispose()

    asyncio.run(scenario())
