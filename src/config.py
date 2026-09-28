"""
Centralized configuration for MedGuard RAG.

All configuration is loaded from environment variables with sensible defaults.
Uses pydantic-settings for validation and type coercion.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "MedGuard RAG"
    app_env: str = Field(default="development", pattern="^(development|staging|production)$")
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # --- OpenAI ---
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = Field(default=0.1, ge=0.0, le=1.0)
    openai_max_tokens: int = Field(default=1024, ge=1, le=4096)

    # --- Database ---
    database_url: str = "sqlite:///./medguard.db"

    # --- ChromaDB ---
    chroma_persist_directory: str = "./data/chroma"
    chroma_collection_name: str = "medguard_documents"

    # --- Retrieval ---
    embedding_model: str = "all-MiniLM-L6-v2"
    vector_search_top_k: int = Field(default=20, ge=1, le=100)
    bm25_search_top_k: int = Field(default=20, ge=1, le=100)
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    reranker_top_k: int = Field(default=5, ge=1, le=20)
    rrf_k: int = Field(default=60, ge=1, description="RRF constant for fusion scoring")

    # --- Chunking ---
    chunk_size: int = Field(default=512, ge=100, le=2048, description="Chunk size in tokens")
    chunk_overlap: int = Field(default=64, ge=0, le=256, description="Token overlap between chunks")
    min_chunk_size: int = Field(default=50, ge=10, description="Minimum chunk size in tokens")

    # --- Safety ---
    max_query_length: int = Field(default=500, ge=50, le=2000)
    rate_limit_per_minute: int = Field(default=30, ge=1)
    policy_directory: str = "policies"

    # --- Evaluation ---
    eval_output_directory: str = "evaluation/results"
    
    # --- Ingestion ---
    raw_data_directory: str = "./data/raw"
    processed_data_directory: str = "./data/processed"
    chunks_data_directory: str = "./data/chunks"
    sources_registry_path: str = "./data/sources.yaml"
    scraper_user_agent: str = "MedGuard-RAG-Bot/0.1 (Educational Research)"
    scraper_timeout_seconds: int = Field(default=30, ge=5, le=120)
    scraper_delay_seconds: float = Field(default=1.0, ge=0.0)

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get cached application settings.

    Uses lru_cache to ensure settings are loaded once and reused.
    Call get_settings.cache_clear() in tests to reset.
    """
    return Settings()