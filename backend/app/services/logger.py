import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.schemas import RequestDecision

LOG_FILE = Path("monitoring/request_logs.jsonl")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

_logs: list[dict] = []
_loaded_once = False


def _normalize_decision(value) -> str:
    if hasattr(value, "value"):
        return value.value
    return str(value)


def _load_logs_from_file() -> None:
    global _loaded_once, _logs

    if _loaded_once:
        return

    if LOG_FILE.exists():
        loaded: list[dict] = []
        with LOG_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    loaded.append(json.loads(line))
                except Exception:
                    continue
        _logs = loaded

    _loaded_once = True


async def log_request(
    user_id: Optional[str],
    model_id: int,
    prompt_hash: str,
    security_score: float,
    decision: RequestDecision,
    latency_ms: float,
    prompt_risk_score: Optional[float] = None,
    output_risk_score: Optional[float] = None,
    blocked: Optional[bool] = None,
    secure_mode_enabled: Optional[bool] = None,
    reason: Optional[str] = None,
) -> dict:
    _load_logs_from_file()

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "model_id": model_id,
        "prompt_hash": prompt_hash,
        "security_score": float(security_score),
        "decision": _normalize_decision(decision),
        "latency_ms": float(latency_ms),
        "prompt_risk_score": float(prompt_risk_score) if prompt_risk_score is not None else None,
        "output_risk_score": float(output_risk_score) if output_risk_score is not None else None,
        "blocked": blocked,
        "secure_mode_enabled": secure_mode_enabled,
        "reason": reason,
    }

    _logs.append(entry)

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return entry


def get_all_logs() -> list[dict]:
    _load_logs_from_file()
    return list(reversed(_logs))


def get_logs_by_user(user_id: str) -> list[dict]:
    _load_logs_from_file()
    return [log for log in _logs if log.get("user_id") == user_id]


def get_logs_by_decision(decision: RequestDecision) -> list[dict]:
    _load_logs_from_file()
    decision_value = _normalize_decision(decision)
    return [log for log in _logs if log.get("decision") == decision_value]


def get_logs_by_model(model_id: int) -> list[dict]:
    _load_logs_from_file()
    return [log for log in _logs if int(log.get("model_id", -1)) == int(model_id)]


def get_metrics_summary() -> dict:
    _load_logs_from_file()

    if not _logs:
        return {
            "total_requests": 0,
            "blocked_requests": 0,
            "challenged_requests": 0,
            "allowed_requests": 0,
            "avg_security_score": 0.0,
            "avg_latency_ms": 0.0,
            "block_rate": 0.0,
        }

    total = len(_logs)
    blocked = sum(1 for l in _logs if l.get("decision") == RequestDecision.BLOCK.value)
    challenged = sum(1 for l in _logs if l.get("decision") == RequestDecision.CHALLENGE.value)
    allowed = sum(1 for l in _logs if l.get("decision") == RequestDecision.ALLOW.value)

    avg_score = round(sum(float(l.get("security_score", 0.0)) for l in _logs) / total, 4)
    avg_latency = round(sum(float(l.get("latency_ms", 0.0)) for l in _logs) / total, 2)
    block_rate = round((blocked / total) * 100, 2)

    return {
        "total_requests": total,
        "blocked_requests": blocked,
        "challenged_requests": challenged,
        "allowed_requests": allowed,
        "avg_security_score": avg_score,
        "avg_latency_ms": avg_latency,
        "block_rate": block_rate,
    }


def flush_logs():
    global _logs, _loaded_once
    _logs = []
    _loaded_once = True
    with LOG_FILE.open("w", encoding="utf-8") as f:
        f.write("")