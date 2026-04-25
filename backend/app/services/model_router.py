import httpx
from fastapi import HTTPException, status

from app.schemas import ModelType

try:
    from app.core.config import get_settings
    settings = get_settings()
except Exception:
    settings = None


async def route_to_model(
    model,
    prompt: str,
    parameters: dict | None = None,
) -> str:
    parameters = parameters or {}
    routers = {
        ModelType.OPENAI: _call_openai,
        ModelType.HUGGINGFACE: _call_huggingface_chat,
        ModelType.LOCAL: _call_local,
        ModelType.CUSTOM_API: _call_custom_api,
    }

    model_type = model.model_type
    if isinstance(model_type, str):
        model_type = ModelType(model_type.lower())

    handler = routers.get(model_type)

    if not handler:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported model type: {model.model_type}",
        )

    return await handler(model, prompt, parameters)


async def _call_openai(model, prompt: str, parameters: dict) -> str:
    if not settings or not getattr(settings, "OPENAI_API_KEY", ""):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI API key not configured",
        )

    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": parameters.get("model") or getattr(model, "hf_model_id", None) or "gpt-4o-mini",
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
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenAI API response did not include chat completion content",
        )


async def _call_huggingface_chat(model, prompt: str, parameters: dict) -> str:
    if not settings or not getattr(settings, "HF_TOKEN", ""):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="HF_TOKEN not configured",
        )

    model_name = (getattr(model, "hf_model_id", None) or "").strip()
    if not model_name:
        source_url = (getattr(model, "source_url", None) or "").strip()
        if "huggingface.co/" in source_url:
            model_name = source_url.split("huggingface.co/", 1)[1].strip("/")
            model_name = model_name.split("/tree/", 1)[0].split("/blob/", 1)[0]
    if not model_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="hf_model_id is required for HuggingFace chat routing",
        )

    api_url = "https://router.huggingface.co/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {settings.HF_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": parameters.get("max_tokens", 128),
        "temperature": parameters.get("temperature", 0.7),
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(api_url, headers=headers, json=payload)

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"HuggingFace API error: {response.text}",
        )

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="HuggingFace router response did not include chat completion content",
        )


async def _call_local(model, prompt: str, parameters: dict) -> str:
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


async def _call_custom_api(model, prompt: str, parameters: dict) -> str:
    if not model.endpoint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Custom API endpoint not configured",
        )

    payload = {"prompt": prompt, **parameters}

    timeout = httpx.Timeout(
        connect=20.0,
        read=180.0,
        write=30.0,
        pool=30.0,
    )

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(model.endpoint, json=payload)

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Custom API error: {response.text}",
        )

    data = response.json()
    if isinstance(data, dict):
        direct = data.get("output") or data.get("result") or data.get("response") or data.get("text")
        if direct:
            return str(direct)
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict) and message.get("content"):
                    return str(message["content"])
                if first.get("text"):
                    return str(first["text"])
    return str(data)
