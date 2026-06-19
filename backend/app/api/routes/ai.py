from fastapi import APIRouter

from app.core.config import settings
from app.services.openai_analyzer import check_openai_connection

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status")
def read_ai_status() -> dict[str, str | bool]:
    has_api_key = bool(settings.openai_api_key)
    provider = "openai" if settings.ai_provider == "openai" or (settings.ai_provider == "auto" and has_api_key) else "local"

    return {
        "configured_provider": settings.ai_provider,
        "active_provider": provider,
        "has_openai_api_key": has_api_key,
        "openai_model": settings.openai_model,
    }


@router.post("/test")
def test_ai_connection() -> dict[str, str]:
    result = check_openai_connection()
    return {
        "provider": "openai",
        "model": settings.openai_model,
        "result": result,
    }
