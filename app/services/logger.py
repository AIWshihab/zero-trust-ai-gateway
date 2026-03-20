import json
from datetime import datetime
from pathlib import Path
from app.models.schemas import RequestDecision

# ─── Log Storage (swap for DB in Stage 4) ────────────────────────────────────

LOG_FILE = Path("monitoring/request_logs.jsonl")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


# ─── In-Memory Store (for metrics dashboard) ──────────────────────────────────

_logs: list[dict] = []


# ─── Core Logger ──────────────────────────────────────────────────────────────

async def log_request(
    user_id: str,
    model_id: int,
    prompt_hash: str,
    security_score: float,
    decision: RequestDecision,
    latency_ms: float,
) -> dict:
    """
    Logs every request passing through the ZTA gateway.
    Writes to in-memory store and appends to JSONL file.
    Prompt is hashed — raw content is never stored.
    """
    entry = {
        "timestamp":      datetime.utcnow().isoformat(),
        "user_id":        user_id,
        "model_id":       model_id,
        "prompt_hash":    prompt_hash,
        "security_score": security_score,
        "decision":       decision.value,
        "latency_ms":     latency_ms,
    }

    # Write to in-memory list
    _logs.append(entry)

    # Append to JSONL file (one JSON object per line)
    with LOG_FILE.open("a") as f:
        f.write(json.dumps(entry) + "\n")

    return entry


# ─── Log Retrieval ────────────────────────────────────────────────────────────

def get_all_logs() -> list[dict]:
    return list(reversed(_logs))  # most recent first


def get_logs_by_user(user_id: str) -> list[dict]:
    return [log for log in _logs if log["user_id"] == user_id]


def get_logs_by_decision(decision: RequestDecision) -> list[dict]:
    return [log for log in _logs if log["decision"] == decision.value]


def get_logs_by_model(model_id: int) -> list[dict]:
    return [log for log in _logs if log["model_id"] == model_id]


# ─── Metrics Aggregation ──────────────────────────────────────────────────────

def get_metrics_summary() -> dict:
    """
    Aggregates log data for the monitoring dashboard.
    Covers Experiment 2 & 3 metrics in your evaluation plan.
    """
    if not _logs:
        return {
            "total_requests":      0,
            "blocked_requests":    0,
            "challenged_requests": 0,
            "allowed_requests":    0,
            "avg_security_score":  0.0,
            "avg_latency_ms":      0.0,
            "block_rate":          0.0,
        }

    total      = len(_logs)
    blocked    = sum(1 for l in _logs if l["decision"] == RequestDecision.BLOCK.value)
    challenged = sum(1 for l 
                     in _logs if l["decision"] == RequestDecision.CHALLENGE.value)
    allowed    = sum(1 for l in _logs if l["decision"] == RequestDecision.ALLOW.value)

    avg_score   = round(sum(l["security_score"] for l in _logs) / total, 4)
    avg_latency = round(sum(l["latency_ms"] for l in _logs) / total, 2)
    block_rate  = round((blocked / total) * 100, 2)

    return {
        "total_requests":      total,
        "blocked_requests":    blocked,
        "challenged_requests": challenged,
        "allowed_requests":    allowed,
        "avg_security_score":  avg_score,
        "avg_latency_ms":      avg_latency,
        "block_rate":          block_rate,
    }


# ─── Log Flusher (for testing) ────────────────────────────────────────────────

def flush_logs():
    """Clears in-memory logs. Used in test setup/teardown."""
    global _logs
    _logs = []
