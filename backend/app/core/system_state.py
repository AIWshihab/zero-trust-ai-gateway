"""
Unified system state integration layer.

Priority order for data sources:
  1. app.intelligence.graph (future — not yet implemented, imported safely)
  2. Live database (AttackSequenceEvent + RequestLog)
  3. get_fallback_state() — always safe, never raises
"""
from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Fallback — always valid, never raises
# ---------------------------------------------------------------------------

def get_fallback_state() -> dict[str, Any]:
    """Return a structurally complete state dict from mock values.
    Called when both the intelligence graph and the DB are unavailable.
    """
    return {
        "global_state": {"level": "normal", "block_rate": 0.0},
        "recent_activity": [
            {"user": 1, "model": 1, "stage": "probe",    "decision": "allow",     "risk": 0.18, "severity": 0.15, "timestamp": None},
            {"user": 2, "model": 1, "stage": "inject",   "decision": "block",     "risk": 0.82, "severity": 0.78, "timestamp": None},
            {"user": 1, "model": 2, "stage": "safe",     "decision": "allow",     "risk": 0.09, "severity": 0.05, "timestamp": None},
            {"user": 3, "model": 1, "stage": "escalate", "decision": "challenge", "risk": 0.55, "severity": 0.50, "timestamp": None},
        ],
        "signals": [
            {"stage": "inject",   "risk": 0.82},
            {"stage": "escalate", "risk": 0.55},
        ],
        "campaigns": [],
        "metrics": {"requests": 0, "blocks": 0},
        "_source": "fallback",
    }


# ---------------------------------------------------------------------------
# DB-backed state
# ---------------------------------------------------------------------------

async def _state_from_db(db: Any) -> dict[str, Any]:
    """Read unified state directly from the database models."""
    from sqlalchemy import func, select

    from app.models.attack_sequence_event import AttackSequenceEvent
    from app.models.request_log import RequestLog

    # Recent attack events (last 20)
    event_rows = (
        await db.execute(
            select(AttackSequenceEvent)
            .order_by(AttackSequenceEvent.timestamp.desc())
            .limit(20)
        )
    ).scalars().all()

    recent_activity = [
        {
            "user":      row.user_id,
            "model":     row.model_id,
            "stage":     row.attack_stage,
            "decision":  row.decision,
            "risk":      float(row.risk_score),
            "severity":  float(row.sequence_severity),
            "timestamp": row.timestamp.isoformat() if row.timestamp else None,
        }
        for row in event_rows
    ]

    # High-risk signals from recent activity
    signals = [
        {"stage": a["stage"], "risk": a["risk"]}
        for a in recent_activity
        if a["risk"] >= 0.6
    ]

    # Aggregate totals from RequestLog
    total_result = await db.execute(select(func.count(RequestLog.id)))
    total: int = int(total_result.scalar() or 0)

    block_result = await db.execute(
        select(func.count(RequestLog.id)).where(RequestLog.decision == "block")
    )
    blocks: int = int(block_result.scalar() or 0)

    block_rate = round((blocks / total * 100), 2) if total > 0 else 0.0
    level = (
        "critical" if block_rate >= 50
        else "elevated" if block_rate >= 25
        else "normal"
    )

    return {
        "global_state":    {"level": level, "block_rate": block_rate},
        "recent_activity": recent_activity,
        "signals":         signals,
        "campaigns":       [],
        "metrics":         {"requests": total, "blocks": blocks},
        "_source":         "db",
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def get_system_state(db: Any = None) -> dict[str, Any]:
    """
    Unified system state with three-tier fallback.

    Tries (in order):
      1. app.intelligence.graph — the future intelligence layer
      2. Live database via the supplied AsyncSession
      3. Static fallback — structurally complete, never raises
    """

    # ---- tier 1: intelligence graph (future module) ----
    try:
        from app.intelligence.graph import security_graph  # type: ignore[import]

        edges = security_graph.edges or []
        users = security_graph.user_nodes or {}
        recent = edges[-20:]

        signals: list[dict[str, Any]] = []
        for e in recent:
            try:
                s = security_graph.get_attack_signals(e["user"], e["prompt"])
                signals.append(s)
            except Exception:
                pass

        campaigns: list[dict[str, Any]] = []
        for uid in users.keys():
            try:
                campaigns.append(security_graph.get_campaign_summary(uid))
            except Exception:
                pass

        total  = len(edges)
        blocks = len([e for e in edges if e.get("decision") == "block"])

        return {
            "global_state":    security_graph.get_global_state() or {"level": "normal"},
            "recent_activity": recent,
            "signals":         signals,
            "campaigns":       campaigns,
            "metrics":         {"requests": total, "blocks": blocks},
            "_source":         "graph",
        }

    except ImportError:
        pass  # module not yet implemented — expected
    except Exception as exc:
        log.warning("intelligence graph error (non-fatal): %s", exc)

    # ---- tier 2: live database ----
    if db is not None:
        try:
            return await _state_from_db(db)
        except Exception as exc:
            log.warning("DB system state failed (non-fatal): %s", exc)

    # ---- tier 3: static fallback ----
    return get_fallback_state()
