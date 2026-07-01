from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.services.gemini_analyzer import check_gemini_connection
from app.services.openai_analyzer import check_openai_connection

router = APIRouter(prefix="/ai", tags=["ai"])


def _determine_active_provider() -> str:
    has_gemini_key = bool(settings.gemini_api_key)
    has_openai_key = bool(settings.openai_api_key)

    if settings.ai_provider == "gemini" or (settings.ai_provider == "auto" and has_gemini_key):
        return "gemini"
    if settings.ai_provider == "openai" or (settings.ai_provider == "auto" and has_openai_key):
        return "openai"
    return "local"


@router.get("/status")
def read_ai_status() -> dict[str, str | bool]:
    provider = _determine_active_provider()

    return {
        "configured_provider": settings.ai_provider,
        "active_provider": provider,
        "has_gemini_api_key": bool(settings.gemini_api_key),
        "gemini_model": settings.gemini_model,
        "has_openai_api_key": bool(settings.openai_api_key),
        "openai_model": settings.openai_model,
    }


@router.post("/test")
def test_ai_connection() -> dict[str, str]:
    provider = _determine_active_provider()

    if provider == "local":
        raise HTTPException(status_code=400, detail="No AI provider is configured")

    try:
        if provider == "gemini":
            result = check_gemini_connection()
            model = settings.gemini_model
        else:
            result = check_openai_connection()
            model = settings.openai_model
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"{provider} connection failed: {type(exc).__name__}: {exc}",
        ) from exc

    return {
        "provider": provider,
        "model": model,
        "result": result,
    }
