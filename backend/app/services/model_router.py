import asyncio
import json
from typing import AsyncIterator

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
    messages: list | None = None,
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

    return await handler(model, prompt, parameters, messages)


async def stream_route_to_model(
    model,
    prompt: str,
    parameters: dict | None = None,
    messages: list | None = None,
) -> AsyncIterator[str]:
    parameters = parameters or {}
    model_type = model.model_type
    if isinstance(model_type, str):
        model_type = ModelType(model_type.lower())

    if model_type == ModelType.OPENAI:
        async for chunk in _stream_openai(model, prompt, parameters, messages):
            yield chunk
        return
    if model_type == ModelType.HUGGINGFACE:
        async for chunk in _stream_huggingface_chat(model, prompt, parameters, messages):
            yield chunk
        return

    output = await route_to_model(model, prompt, parameters, messages)
    if output:
        yield output


def _api_messages(prompt: str, messages: list | None) -> list:
    return messages if messages else [{"role": "user", "content": prompt}]


def _chat_delta_from_sse_line(line: str) -> str | None:
    if not line.startswith("data: "):
        return None
    raw = line.removeprefix("data: ").strip()
    if not raw or raw == "[DONE]":
        return None
    try:
        data = json.loads(raw)
        delta = data["choices"][0].get("delta") or {}
        if "content" in delta:
            return str(delta["content"])
        message = data["choices"][0].get("message") or {}
        if "content" in message:
            return str(message["content"])
    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
        return None
    return None


async def _call_openai(model, prompt: str, parameters: dict, messages: list | None = None) -> str:
    if not settings or not getattr(settings, "OPENAI_API_KEY", ""):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI API key not configured",
        )

    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    api_messages = _api_messages(prompt, messages)

    payload = {
        "model": parameters.get("model") or getattr(model, "hf_model_id", None) or "gpt-4o-mini",
        "messages": api_messages,
        "max_tokens": parameters.get("max_tokens", 512),
        "temperature": parameters.get("temperature", 0.7),
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
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


async def _call_huggingface_chat(model, prompt: str, parameters: dict, messages: list | None = None) -> str:
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

    api_messages = _api_messages(prompt, messages)

    payload = {
        "model": model_name,
        "messages": api_messages,
        "max_tokens": parameters.get("max_tokens", 256),
        "temperature": parameters.get("temperature", 0.7),
    }

    last_exc: Exception | None = None
    for attempt in range(4):
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(api_url, headers=headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                try:
                    return data["choices"][0]["message"]["content"]
                except (KeyError, IndexError, TypeError):
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="HuggingFace router response did not include chat completion content",
                    )

            if response.status_code in {429, 503} and attempt < 3:
                wait = 20.0
                if response.status_code == 503:
                    try:
                        body_json = response.json()
                        wait = min(float(body_json.get("estimated_time") or 20), 120)
                    except Exception:
                        wait = 20.0
                else:
                    wait = 30.0
                last_exc = HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"HuggingFace API error ({response.status_code}): {response.text[:300]}",
                )
                await asyncio.sleep(wait)
                continue

            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"HuggingFace API error: {response.text[:500]}",
            )
        except httpx.TimeoutException as exc:
            last_exc = HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="HuggingFace model timed out. The model may be cold-starting — try again in a few seconds.",
            )
            if attempt < 3:
                await asyncio.sleep(5.0)
                continue
            raise last_exc from exc

    raise last_exc or HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="HuggingFace request failed")


async def _call_local(model, prompt: str, parameters: dict, messages: list | None = None) -> str:
    if not model.endpoint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Local model endpoint not configured",
        )

    payload = {
        "prompt": prompt,
        "messages": _api_messages(prompt, messages),
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


async def _call_custom_api(model, prompt: str, parameters: dict, messages: list | None = None) -> str:
    if not model.endpoint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Custom API endpoint not configured",
        )

    payload = {"prompt": prompt, "messages": _api_messages(prompt, messages), **parameters}

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


async def _stream_openai(model, prompt: str, parameters: dict, messages: list | None = None) -> AsyncIterator[str]:
    if not settings or not getattr(settings, "OPENAI_API_KEY", ""):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI API key not configured",
        )

    payload = {
        "model": parameters.get("model") or getattr(model, "hf_model_id", None) or "gpt-4o-mini",
        "messages": _api_messages(prompt, messages),
        "max_tokens": parameters.get("max_tokens", 512),
        "temperature": parameters.get("temperature", 0.7),
        "stream": True,
    }
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST",
            model.endpoint or "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
        ) as response:
            if response.status_code != 200:
                text = await response.aread()
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"OpenAI API error: {text.decode('utf-8', errors='replace')}",
                )
            async for line in response.aiter_lines():
                delta = _chat_delta_from_sse_line(line)
                if delta:
                    yield delta


_WARMING_SENTINEL = "\x00WARMING\x00"


async def _stream_huggingface_chat(model, prompt: str, parameters: dict, messages: list | None = None) -> AsyncIterator[str]:
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

    payload = {
        "model": model_name,
        "messages": _api_messages(prompt, messages),
        "max_tokens": parameters.get("max_tokens", 256),
        "temperature": parameters.get("temperature", 0.7),
        "stream": True,
    }
    headers = {
        "Authorization": f"Bearer {settings.HF_TOKEN}",
        "Content-Type": "application/json",
    }

    timeout = httpx.Timeout(connect=15.0, read=300.0, write=30.0, pool=30.0)
    max_attempts = 4
    last_exc: Exception | None = None

    for attempt in range(max_attempts):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream(
                    "POST",
                    "https://router.huggingface.co/v1/chat/completions",
                    headers=headers,
                    json=payload,
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            delta = _chat_delta_from_sse_line(line)
                            if delta:
                                yield delta
                        return

                    body = await response.aread()
                    body_text = body.decode("utf-8", errors="replace")

                    if response.status_code in {503, 429} and attempt < max_attempts - 1:
                        if response.status_code == 503:
                            try:
                                body_json = json.loads(body_text)
                                wait = min(float(body_json.get("estimated_time") or 20), 90)
                                msg = f"Model is loading on HuggingFace (~{int(wait)}s). Please wait..."
                            except (json.JSONDecodeError, ValueError, TypeError):
                                wait = 20.0
                                msg = "Model is loading on HuggingFace. Please wait..."
                        else:
                            wait = 30.0
                            msg = "HuggingFace rate limit hit. Retrying in 30s..."

                        yield f"{_WARMING_SENTINEL}{msg}"
                        await asyncio.sleep(wait)
                        last_exc = HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"HuggingFace API error ({response.status_code}): {body_text[:300]}",
                        )
                        continue

                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"HuggingFace API error: {body_text[:500]}",
                    )

        except httpx.TimeoutException as exc:
            last_exc = HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="HuggingFace model timed out. The model may be cold-starting — try again.",
            )
            if attempt < max_attempts - 1:
                yield f"{_WARMING_SENTINEL}HuggingFace timed out. Retrying ({attempt + 2}/{max_attempts})..."
                await asyncio.sleep(5.0)
                continue
            raise last_exc from exc

    raise last_exc or HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="HuggingFace streaming failed")
