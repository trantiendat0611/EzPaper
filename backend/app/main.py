import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.routes import ai, auth, health, papers
from app.core.config import settings
from app.core.limiter import limiter

logger = logging.getLogger(__name__)

DEFAULT_SECRET_KEY = "change-this-secret-key-before-production"
if settings.secret_key == DEFAULT_SECRET_KEY:
    logger.warning(
        "SECRET_KEY is still set to the default placeholder value. "
        "Set a unique SECRET_KEY before deploying to production."
    )

app = FastAPI(title=settings.app_name)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(ai.router)
app.include_router(papers.router)
app.include_router(health.router, tags=["health"])


@app.get("/")
def read_root() -> dict[str, str]:
    return {"service": settings.app_name, "docs": "/docs"}
