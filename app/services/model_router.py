import httpx
from fastapi import HTTPException, status
from app.models.schemas import ModelOut, ModelType
from app.core.config import get_settings

settings = get_settings()


# ─── Main Router Entry Point ──────────────────────────────────────────────────

async def route_to_model(
    model: ModelOut,
    prompt: str,
    parameters: dict = {},
) -> str:
    """
    Routes an inference request to the correct backend
    based on model type defined in the registry.
    """
    routers = {
        ModelType.OPENAI:      _call_openai,
        ModelType.HUGGINGFACE: _call_huggingface,
        ModelType.LOCAL:       _call_local,
        ModelType.CUSTOM_API:  _call_custom_api,
    }

    handler = routers.get(model.model_type)

    if not handler:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported model type: {model.model_type}",
        )

    return await handler(model, prompt, parameters)


# ─── OpenAI Handler ───────────────────────────────────────────────────────────

async def _call_openai(model: ModelOut, prompt: str, parameters: dict) -> str:
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI API key not configured",
        )

    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": parameters.get("max_tokens", 512),
        "temperature": parameters.get("temperature", 0.7),
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            model.endpoint or "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OpenAI API error: {response.text}",
        )

    data = response.json()
    return data["choices"][0]["message"]["content"]


# ─── HuggingFace Handler ──────────────────────────────────────────────────────

async def _call_huggingface(model: ModelOut, prompt: str, parameters: dict) -> str:
    if not model.endpoint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="HuggingFace model endpoint not configured",
        )

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": parameters.get("max_tokens", 256),
            "temperature":    parameters.get("temperature", 0.7),
            "return_full_text": False,
        },
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(model.endpoint, json=payload)

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"HuggingFace API error: {response.text}",
        )

    data = response.json()

    # Handle both list and dict response formats
    if isinstance(data, list):
        return data[0].get("generated_text", "")
    return data.get("generated_text", str(data))


# ─── Local Model Handler ──────────────────────────────────────────────────────

async def _call_local(model: ModelOut, prompt: str, parameters: dict) -> str:
    """
    Calls a locally hosted model endpoint (e.g. Ollama, vLLM, llama.cpp server).
    """
    if not model.endpoint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Local model endpoint not configured",
        )

    payload = {
        "prompt": prompt,
        "max_tokens": parameters.get("max_tokens", 256),
        "temperature": parameters.get("temperature", 0.7),
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(model.endpoint, json=payload)

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Local model error: {response.text}",
        )

    data = response.json()
    return data.get("output") or data.get("response") or data.get("text", "")


# ─── Custom API Handler ───────────────────────────────────────────────────────

async def _call_custom_api(model: ModelOut, prompt: str, parameters: dict) -> str:
    """
    Generic handler for any custom REST API model endpoint.
    """
    if not model.endpoint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Custom API endpoint not configured",
        )

    payload = {"prompt": prompt, **parameters}

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(model.endpoint, json=payload)

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Custom API error: {response.text}",
        )

    data = response.json()
    return data.get("output") or data.get("result") or str(data)
