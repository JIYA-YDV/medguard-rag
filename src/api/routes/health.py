"""
Health check endpoint.
"""

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from src.config import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str
    version: str
    environment: str
    timestamp: str

    # Component health (will be populated as components are built)
    components: dict[str, str]


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    System health check.

    Returns the status of the application and all its components.
    Used by deployment platforms and monitoring systems.
    """
    settings = get_settings()

    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version="0.1.0",
        environment=settings.app_env,
        timestamp=datetime.now(timezone.utc).isoformat(),
        components={
            "api": "healthy",
            "vector_store": "not_initialized",
            "policy_engine": "not_initialized",
            "llm": "not_initialized",
        },
    )