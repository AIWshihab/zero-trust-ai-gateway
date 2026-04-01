import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, HttpUrl


app = FastAPI(title="Modal API Wrapper")


MODAL_API_URL = "https://api.us-west-2.modal.direct/v1/chat/completions"
MODAL_API_TOKEN = "modalresearch_oMfipVYQvV0w8_E79XxNr52VhL2t1Cn8eu4f4tY_Ruw"


class WrapperRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    model: str = Field(default="zai-org/GLM-5-FP8")
    max_tokens: int = Field(default=500, ge=1)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


@app.post("/generate-and-forward")
async def generate_and_forward(payload: WrapperRequest):
    if not MODAL_API_TOKEN:
        raise HTTPException(status_code=500, detail="MODAL_API_TOKEN is not set")

    headers = {
        "Authorization": f"Bearer {MODAL_API_TOKEN}",
        "Content-Type": "application/json",
    }

    modal_payload = {
        "model": payload.model,
        "messages": [
            {
                "role": "user",
                "content": payload.prompt,
            }
        ],
        "max_tokens": payload.max_tokens,
        "temperature": payload.temperature,
    }

    timeout = httpx.Timeout(180.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                MODAL_API_URL,
                headers=headers,
                json=modal_payload,
            )
    except httpx.ReadTimeout:
        raise HTTPException(status_code=504, detail="Modal API timed out")
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Modal API request failed: {exc}")

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text,
        )

    return response.json()