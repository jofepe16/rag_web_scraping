from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or a .env file."""

    app_name: str = "BBVA Knowledge Assistant"
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite:///data/app.db"
    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "bbva_website"
    ollama_url: str = "http://ollama:11434"
    chat_model: str = "llama3.2:3b"
    embedding_model: str = "nomic-embed-text"
    history_window: int = 6
    chunk_size: int = 900
    chunk_overlap: int = 150
    retrieval_top_k: int = 8
    rerank_top_k: int = 4
    scrape_base_url: str = "https://www.bbva.com.co/"
    scrape_max_pages: int = 30
    scrape_delay_seconds: float = 0.5
    request_timeout_seconds: float = 20
    allowed_domains: List[str] = ["bbva.com.co", "www.bbva.com.co"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("allowed_domains", mode="before")
    @classmethod
    def split_domains(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("history_window", "chunk_size", "retrieval_top_k", "rerank_top_k", "scrape_max_pages")
    @classmethod
    def positive_integer(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("must be greater than zero")
        return value

    @field_validator("chunk_overlap")
    @classmethod
    def valid_overlap(cls, value: int, info) -> int:
        chunk_size = info.data.get("chunk_size", 900)
        if value < 0 or value >= chunk_size:
            raise ValueError("chunk_overlap must be non-negative and smaller than chunk_size")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()

