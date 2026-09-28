"""
FastAPI application factory.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Uses the factory pattern for testability — tests can create
    fresh app instances with different configurations.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description=(
            "Safety-constrained medical information retrieval system. "
            "Provides educational health information with deterministic "
            "safety policy enforcement."
        ),
        version="0.1.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_development else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _register_routes(app)

    return app


def _register_routes(app: FastAPI) -> None:
    """Register all route modules."""
    from src.api.routes import health, query

    app.include_router(health.router, tags=["System"])
    app.include_router(query.router, prefix="/api/v1", tags=["Query"])