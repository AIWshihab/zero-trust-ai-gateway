import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security import DetectionRule, SecurityControl
from app.schemas import RequestDecision
from app.schemas.security import DetectionRuleCreate, DetectionRuleUpdate, SecurityControlCreate, SecurityControlUpdate


DEFAULT_SECURITY_CONTROLS: list[dict[str, Any]] = [
    {
        "control_id": "LLM01",
        "name": "Prompt Injection",
        "description": "Detect and block attempts to override higher-priority instructions or manipulate model behavior.",
        "coverage": "strong",
        "status": "active",
        "control_family": "input_security",
        "mapped_capabilities": ["prompt_guard", "policy_engine", "trust_penalties", "audit_traces"],
        "recommended_actions": ["Keep prompt-injection signatures current.", "Run policy simulation before model rollout."],
    },
    {
        "control_id": "LLM02",
        "name": "Sensitive Information Disclosure",
        "description": "Prevent secrets, credentials, and personal data from being requested or emitted.",
        "coverage": "strong",
        "status": "active",
        "control_family": "data_protection",
        "mapped_capabilities": ["input_secret_detection", "output_redaction", "secure_mode"],
        "recommended_actions": ["Review output redaction logs.", "Add organization-specific secret patterns."],
    },
    {
        "control_id": "LLM03",
        "name": "Supply Chain",
        "description": "Assess third-party model source, metadata, and endpoint posture before use.",
        "coverage": "moderate",
        "status": "active",
        "control_family": "model_onboarding",
        "mapped_capabilities": ["provider_inspection", "hf_model_identity", "scan_metadata"],
        "recommended_actions": ["Require model cards and source URLs for external models."],
    },
    {
        "control_id": "LLM04",
        "name": "Data and Model Poisoning",
        "description": "Track model posture drift and risky behavior that can indicate compromised model behavior.",
        "coverage": "partial",
        "status": "active",
        "control_family": "model_integrity",
        "mapped_capabilities": ["behavioral_scan", "posture_reassessment"],
        "recommended_actions": ["Add scheduled red-team suites for high-risk models."],
    },
    {
        "control_id": "LLM05",
        "name": "Improper Output Handling",
        "description": "Inspect generated output before the user receives it and redact or block risky content.",
        "coverage": "strong",
        "status": "active",
        "control_family": "output_security",
        "mapped_capabilities": ["output_guard", "redaction", "block_on_high_risk_output"],
        "recommended_actions": ["Add downstream app-specific output rules."],
    },
    {
        "control_id": "LLM06",
        "name": "Excessive Agency",
        "description": "Gate risky model actions with secure mode, readiness checks, and challenge outcomes.",
        "coverage": "moderate",
        "status": "active",
        "control_family": "authorization",
        "mapped_capabilities": ["model_readiness", "secure_mode", "challenge_decisions"],
        "recommended_actions": ["Add tool/action allowlists before agent integrations."],
    },
    {
        "control_id": "LLM07",
        "name": "System Prompt Leakage",
        "description": "Detect attempts to reveal hidden prompts, developer messages, or system instructions.",
        "coverage": "strong",
        "status": "active",
        "control_family": "prompt_confidentiality",
        "mapped_capabilities": ["prompt_extraction_patterns", "trust_penalties", "cooldowns"],
        "recommended_actions": ["Monitor repeated prompt-leak flags by user."],
    },
    {
        "control_id": "LLM08",
        "name": "Vector and Embedding Weaknesses",
        "description": "Plan controls for RAG source isolation and indirect prompt injection in retrieved documents.",
        "coverage": "planned",
        "status": "roadmap",
        "control_family": "retrieval_security",
        "mapped_capabilities": ["rag_source_isolation", "retrieval_policy_hooks"],
        "recommended_actions": ["Add document scanning before retrieved text enters model context."],
    },
    {
        "control_id": "LLM09",
        "name": "Misinformation",
        "description": "Plan confidence, source, and citation controls for high-impact model output.",
        "coverage": "planned",
        "status": "roadmap",
        "control_family": "quality_assurance",
        "mapped_capabilities": ["citation_policy", "confidence_scoring"],
        "recommended_actions": ["Add source citation enforcement for knowledge workflows."],
    },
    {
        "control_id": "LLM10",
        "name": "Unbounded Consumption",
        "description": "Limit runaway cost, latency, and denial-of-wallet patterns.",
        "coverage": "moderate",
        "status": "active",
        "control_family": "abuse_prevention",
        "mapped_capabilities": ["rate_limiting", "abuse_cooldowns", "latency_metrics"],
        "recommended_actions": ["Add budget quotas per user and model."],
    },
]

MARKET_GRADE_CAPABILITIES: list[dict[str, str]] = [
    {
        "name": "Adaptive trust scoring",
        "status": "active",
        "description": "User trust changes from request decisions, prompt risk, rate pressure, and repeated abuse.",
    },
    {
        "name": "Provider-neutral model gateway",
        "status": "active",
        "description": "Routes OpenAI, Hugging Face, local, and custom APIs behind one policy layer.",
    },
    {
        "name": "Prompt abuse cooldowns",
        "status": "active",
        "description": "Repeated blocked or high-risk behavior triggers temporary penalties.",
    },
    {
        "name": "Secure output handling",
        "status": "active",
        "description": "Responses are inspected for secrets and PII before reaching the user.",
    },
    {
        "name": "Supply-chain model scanning",
        "status": "active",
        "description": "Onboarding checks provider reputation, metadata, endpoint posture, and behavioral safety.",
    },
    {
        "name": "RAG/vector isolation",
        "status": "roadmap",
        "description": "Next frontier: scan retrieved documents for indirect prompt injection before model context injection.",
    },
]


def _row_to_control(row: SecurityControl) -> dict[str, Any]:
    return {
        "db_id": row.id,
        "id": row.control_id,
        "control_id": row.control_id,
        "name": row.name,
        "description": row.description,
        "framework": row.framework,
        "coverage": row.coverage,
        "status": row.status,
        "control_family": row.control_family,
        "controls": list(row.mapped_capabilities or []),
        "mapped_capabilities": list(row.mapped_capabilities or []),
        "recommended_actions": list(row.recommended_actions or []),
        "enabled": bool(row.enabled),
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


async def seed_default_security_controls(db: AsyncSession) -> None:
    existing = (
        await db.execute(select(SecurityControl.control_id).where(SecurityControl.control_id.in_([c["control_id"] for c in DEFAULT_SECURITY_CONTROLS])))
    ).scalars().all()
    existing_ids = {str(value).upper() for value in existing}

    for control in DEFAULT_SECURITY_CONTROLS:
        if control["control_id"] in existing_ids:
            continue
        db.add(SecurityControl(framework="OWASP Top 10 for LLM Applications 2025", enabled=True, **control))

    await db.commit()


async def list_security_controls(db: AsyncSession, *, include_disabled: bool = False) -> list[SecurityControl]:
    query = select(SecurityControl)
    if not include_disabled:
        query = query.where(SecurityControl.enabled.is_(True))
    query = query.order_by(SecurityControl.control_id.asc())
    return list((await db.execute(query)).scalars().all())


async def create_security_control(db: AsyncSession, payload: SecurityControlCreate) -> SecurityControl:
    row = SecurityControl(**payload.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def update_security_control(db: AsyncSession, control_id: int, payload: SecurityControlUpdate) -> SecurityControl | None:
    row = (await db.execute(select(SecurityControl).where(SecurityControl.id == control_id))).scalar_one_or_none()
    if row is None:
        return None
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    await db.commit()
    await db.refresh(row)
    return row


async def disable_security_control(db: AsyncSession, control_id: int) -> SecurityControl | None:
    row = (await db.execute(select(SecurityControl).where(SecurityControl.id == control_id))).scalar_one_or_none()
    if row is None:
        return None
    row.enabled = False
    await db.commit()
    await db.refresh(row)
    return row


async def list_detection_rules(
    db: AsyncSession,
    *,
    target: str | None = None,
    include_disabled: bool = False,
) -> list[DetectionRule]:
    query = select(DetectionRule)
    if target:
        query = query.where(DetectionRule.target == target)
    if not include_disabled:
        query = query.where(DetectionRule.enabled.is_(True))
    query = query.order_by(DetectionRule.target.asc(), DetectionRule.severity.desc(), DetectionRule.name.asc())
    return list((await db.execute(query)).scalars().all())


async def create_detection_rule(db: AsyncSession, payload: DetectionRuleCreate) -> DetectionRule:
    row = DetectionRule(**payload.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def update_detection_rule(db: AsyncSession, rule_id: int, payload: DetectionRuleUpdate) -> DetectionRule | None:
    row = (await db.execute(select(DetectionRule).where(DetectionRule.id == rule_id))).scalar_one_or_none()
    if row is None:
        return None
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    await db.commit()
    await db.refresh(row)
    return row


async def disable_detection_rule(db: AsyncSession, rule_id: int) -> DetectionRule | None:
    row = (await db.execute(select(DetectionRule).where(DetectionRule.id == rule_id))).scalar_one_or_none()
    if row is None:
        return None
    row.enabled = False
    await db.commit()
    await db.refresh(row)
    return row


def match_dynamic_rules(text: str, rules: list[DetectionRule]) -> dict[str, Any]:
    risk_delta = 0.0
    flags: list[str] = []
    matches: list[dict[str, Any]] = []
    forced_decision = RequestDecision.ALLOW

    for rule in rules:
        matched = False
        if rule.match_type == "keyword":
            matched = str(rule.pattern).lower() in text.lower()
        elif rule.match_type == "regex":
            try:
                matched = re.search(rule.pattern, text, flags=re.IGNORECASE) is not None
            except re.error:
                matched = False

        if not matched:
            continue

        decision = RequestDecision(rule.decision)
        risk_delta += float(rule.risk_delta or 0.0)
        flag = f"dynamic_rule::{rule.id}::{rule.name}"
        flags.append(flag)
        matches.append(
            {
                "id": rule.id,
                "name": rule.name,
                "target": rule.target,
                "severity": rule.severity,
                "decision": decision.value,
                "risk_delta": round(float(rule.risk_delta or 0.0), 4),
                "flag": flag,
            }
        )

        if decision == RequestDecision.BLOCK:
            forced_decision = RequestDecision.BLOCK
        elif decision == RequestDecision.CHALLENGE and forced_decision != RequestDecision.BLOCK:
            forced_decision = RequestDecision.CHALLENGE

    return {
        "risk_delta": round(max(0.0, min(1.0, risk_delta)), 4),
        "flags": flags,
        "matches": matches,
        "forced_decision": forced_decision,
    }


async def build_control_plane(db: AsyncSession) -> dict[str, Any]:
    controls = [_row_to_control(row) for row in await list_security_controls(db)]
    active = sum(1 for item in MARKET_GRADE_CAPABILITIES if item["status"] == "active")
    total = len(MARKET_GRADE_CAPABILITIES)
    strong_controls = sum(1 for control in controls if control["coverage"] == "strong")
    maturity_base = active / total if total else 0.0
    coverage_bonus = (strong_controls / len(controls)) * 0.2 if controls else 0.0

    return {
        "framework": "OWASP Top 10 for LLM Applications 2025",
        "gateway_maturity": round(min(1.0, maturity_base + coverage_bonus), 2),
        "controls": controls,
        "capabilities": MARKET_GRADE_CAPABILITIES,
        "recommended_next_moves": [
            "Add RAG document isolation before retrieval content reaches prompts.",
            "Add budget controls per user and model to prevent cost abuse.",
            "Add offline red-team suites for every onboarded model before production use.",
        ],
    }
