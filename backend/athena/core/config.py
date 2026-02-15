from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

# .env dosyası proje kök dizininde (backend/../.env)
ENV_FILE = Path(__file__).resolve().parent.parent.parent.parent / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://athena:secure_password@postgres_db:5432/athena_core"

    # Redis
    redis_url: str = "redis://redis_cache:6379/0"

    # RabbitMQ
    rabbitmq_default_user: str = "athena"
    rabbitmq_default_pass: str = "rabbitmq_password"
    celery_broker_url: str = "amqp://athena:rabbitmq_password@rabbitmq_broker:5672//"
    celery_result_backend: str = "redis://redis_cache:6379/0"

    # Application
    debug: bool = True
    log_level: str = "INFO"  # Log seviyesi: DEBUG, INFO, WARNING, ERROR
    data_dir: str = "/data/library"  # PDF dosyaları için klasör

    # API Settings
    semantic_scholar_api_key: str = ""  # Semantic Scholar API key (rate limit için)
    openalex_email: str = "athena@example.com"  # OpenAlex Polite Pool için
    unpaywall_email: str = "athena@example.com"  # Unpaywall API için
    openai_api_key: str = ""  # OpenAI API key
    core_api_key: Optional[str] = None  # CORE API key (https://core.ac.uk/services/api)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
