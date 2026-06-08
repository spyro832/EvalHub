from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://evalhub:evalhub@localhost:5432/evalhub"
    redis_url: str = "redis://localhost:6379"
    secret_key: str = "change-me-in-production"
    debug: bool = False
    log_level: str = "INFO"
    allowed_origins: str = "http://localhost:3000"

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    huggingface_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def get_allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
