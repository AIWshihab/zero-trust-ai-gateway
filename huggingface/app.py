from typing import Any, Dict, Optional

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer

app = FastAPI(title="TinyLlama REST API")

BASE_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

tokenizer = None
model = None
device = "cpu"


class GenerateRequest(BaseModel):
    inputs: str
    parameters: Optional[Dict[str, Any]] = None


@app.on_event("startup")
def load_model() -> None:
    global tokenizer, model, device

    try:
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

        device = "cuda" if torch.cuda.is_available() else "cpu"

        model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            dtype=torch.float32,
        )
        model.to(device)
        model.eval()

    except Exception as e:
        raise RuntimeError(f"Failed to load model: {e}") from e


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/generate")
def generate(req: GenerateRequest):
    global tokenizer, model, device

    if tokenizer is None or model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    try:
        params = req.parameters or {}

        max_new_tokens = int(params.get("max_new_tokens", 128))
        temperature = float(params.get("temperature", 0.7))
        return_full_text = bool(params.get("return_full_text", False))

        prompt_text = f"<|user|>\n{req.inputs}\n<|assistant|>\n"

        inputs = tokenizer(prompt_text, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}

        do_sample = temperature > 0

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=do_sample,
                temperature=temperature if do_sample else 1.0,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )

        decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)

        if return_full_text:
            generated_text = decoded
        else:
            generated_text = (
                decoded[len(prompt_text):].strip()
                if decoded.startswith(prompt_text)
                else decoded.strip()
            )

        return [{"generated_text": generated_text}]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))