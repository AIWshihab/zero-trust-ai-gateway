from typing import Any


def build_chat_error(
    *,
    code: str,
    title: str,
    reason: str,
    explanation: str,
    suggested_fix: str,
    action_required: str = "admin",
    status: str = "blocked",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "title": title,
        "reason": reason,
        "explanation": explanation,
        "suggested_fix": suggested_fix,
        "action_required": action_required,
        "status": status,
        "metadata": metadata or {},
    }


def model_setup_error(
    *,
    code: str,
    title: str,
    reason: str,
    explanation: str,
    suggested_fix: str,
    action_required: str = "admin",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return build_chat_error(
        code=code,
        title=title,
        reason=reason,
        explanation=explanation,
        suggested_fix=suggested_fix,
        action_required=action_required,
        status="model_not_callable",
        metadata=metadata,
    )
