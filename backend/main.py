import os
import logging
import time
import requests
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

app = FastAPI()

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

logger = logging.getLogger("mood-architect")
logging.basicConfig(level=logging.INFO)
logger.info("Loading env from %s (exists=%s)", env_path, env_path.exists())

if os.getenv("HUGGING_FACE_API_KEY"):
    logger.info("Hugging Face API key detected")
else:
    logger.warning("HUGGING_FACE_API_KEY not set - API calls will fail")

def _parse_allowed_origins(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def _parse_model_list(primary: str, fallback_raw: str | None) -> list[str]:
    models = [primary]
    if fallback_raw:
        models.extend(model.strip() for model in fallback_raw.split(",") if model.strip())
    # Preserve order but remove duplicates
    seen: set[str] = set()
    ordered = []
    for model in models:
        if model not in seen:
            ordered.append(model)
            seen.add(model)
    return ordered

allowed_origins = _parse_allowed_origins(os.getenv("ALLOWED_ORIGINS"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

class RequestData(BaseModel):
    name: str = Field(..., max_length=60)
    feeling: str = Field(..., max_length=160)
    details: str | None = Field(default=None, max_length=320)

class ResponseData(BaseModel):
    affirmation: str

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/affirmation", response_model=ResponseData)
async def generate_affirmation(data: RequestData):
    name = data.name.strip()
    feeling = data.feeling.strip()
    details = (data.details or "").strip()

    if not name or not feeling:
        raise HTTPException(status_code=400, detail="Name and feeling are required.")

    # Time-of-day context
    hour = datetime.now().hour
    if hour < 12:
        context = "morning"
    elif hour < 18:
        context = "afternoon"
    else:
        context = "evening"

    safety_notice = (
        "If the user expresses intent to self-harm, respond with a gentle, supportive message, "
        "encourage them to seek help from trusted people or professionals, and avoid giving advice."
    )
    system_prompt = (
        "You are a supportive companion. Always respond with 2–4 warm sentences. "
        "Always include the user's name in the affirmation. "
        "Use the user's name and feeling naturally. "
        "Add a metaphor or time-of-day context when possible. "
        "Never give medical or legal advice, and never diagnose."
    )

    user_payload = (
        f"Name: {name}\n"
        f"Feeling: {feeling}\n"
        f"Details: {details}\n"
        f"Time of day: {context}"
    )

    try:
        affirmation = _generate_affirmation(
            system_prompt=system_prompt,
            safety_notice=safety_notice,
            user_payload=user_payload,
        )
        return {"affirmation": affirmation}
    except TimeoutError as err:
        logger.exception("AI request timed out")
        raise HTTPException(
            status_code=504,
            detail="The affirmation took too long to generate. Please try again.",
        ) from err
    except Exception as err:
        logger.exception("AI request failed")
        debug = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"}
        detail = "Could not generate affirmation. Please try again later."
        if debug:
            detail = f"AI error: {type(err).__name__}: {err}"
        raise HTTPException(
            status_code=502,
            detail=detail,
        ) from err


def _generate_affirmation(
    system_prompt: str,
    safety_notice: str,
    user_payload: str,
) -> str:
    """Generate an affirmation using Hugging Face Inference API."""
    
    # Get fresh API key from environment (in case it was updated)
    api_key = os.getenv("HUGGING_FACE_API_KEY")
    if not api_key:
        raise ValueError("HUGGING_FACE_API_KEY not set in environment")
    
    primary_model = os.getenv("HUGGING_FACE_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct")
    fallback_raw = os.getenv(
        "HUGGING_FACE_FALLBACK_MODELS",
        "Qwen/Qwen2.5-7B-Instruct",
    )
    models_to_try = _parse_model_list(primary_model, fallback_raw)
    
    system_message = f"{system_prompt}\n{safety_notice}"
    
    # Retry logic per model: 3 attempts with exponential backoff
    backoff_delays = [2, 4, 8]
    last_error: Exception | None = None

    for model in models_to_try:
        hf_api_url = "https://router.huggingface.co/v1/chat/completions"
        hf_headers = {"Authorization": f"Bearer {api_key}"}
        logger.info("Trying Hugging Face model: %s", model)

        for attempt in range(3):
            try:
                logger.info("Affirmation request attempt %s/3", attempt + 1)

                response = requests.post(
                    hf_api_url,
                    headers={
                        **hf_headers,
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": user_payload},
                        ],
                        "temperature": 0.7,
                        "max_tokens": 256,
                        "stream": False,
                    },
                    timeout=60,
                )
                response.raise_for_status()

                result = response.json()
                if isinstance(result, dict) and result.get("error"):
                    raise RuntimeError(result["error"])

                text = ""
                if isinstance(result, dict):
                    choices = result.get("choices") or []
                    if choices:
                        message = choices[0].get("message") or {}
                        text = (message.get("content") or "").strip()

                if not text:
                    raise ValueError("Empty response from Hugging Face")

                logger.info("Affirmation generated successfully")
                return text

            except requests.exceptions.HTTPError as err:
                last_error = err
                status_code = err.response.status_code if err.response else None
                logger.warning("Attempt %s failed: HTTP error %s", attempt + 1, status_code)

                if status_code in {401, 403}:
                    # Invalid or unauthorized token; no point trying other models.
                    raise
                if status_code in {404, 410}:
                    # Model not hosted; move to next model immediately.
                    break

                if attempt < 2:
                    wait_time = backoff_delays[attempt]
                    logger.info("Waiting %ss before retry...", wait_time)
                    time.sleep(wait_time)
                    continue
                break

            except Exception as err:
                last_error = err
                logger.warning("Attempt %s failed: %s: %s", attempt + 1, type(err).__name__, err)
                if attempt < 2:
                    wait_time = backoff_delays[attempt]
                    logger.info("Waiting %ss before retry...", wait_time)
                    time.sleep(wait_time)
                    continue
                break

    if last_error:
        logger.error("All models failed. Last error: %s: %s", type(last_error).__name__, last_error)
    raise last_error or RuntimeError("AI request failed after all models attempted")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
