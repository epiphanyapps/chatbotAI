"""Application configuration using pydantic-settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Database
    DATABASE_URL: str

    # Valkey (Redis-compatible)
    VALKEY_URL: str

    # JWT Configuration
    JWT_SECRET: str
    JWT_ACCESS_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    # Magic Link
    MAGIC_LINK_SECRET: str

    # Email (Resend)
    RESEND_API_KEY: str

    # Application
    APP_URL: str = "https://intimateai.chat"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # CORS
    CORS_ORIGINS: list[str] = ["https://intimateai.chat", "http://localhost:3000"]

    # LLM (OpenRouter, OpenAI-compatible)
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    # Two presets so realism/explicitness can be A/B tuned without a redeploy.
    # primary = RP finetune (voice + explicit quality); alt = frontier-permissive (memory + coherence)
    LLM_MODEL_PRIMARY: str = "sao10k/l3.3-euryale-70b"
    LLM_MODEL_ALT: str = "deepseek/deepseek-chat"
    LLM_ACTIVE_PRESET: str = "primary"  # "primary" | "alt"
    LLM_TEMPERATURE: float = 0.9
    LLM_MAX_TOKENS: int = 800
    # Number of recent turns (user+assistant messages) kept in the live context window.
    LLM_CONTEXT_TURNS: int = 20
    # When stored history exceeds this many messages, older turns get summarized.
    LLM_SUMMARY_THRESHOLD: int = 30

    @property
    def active_model(self) -> str:
        """Resolve the active model id from the selected preset."""
        return (
            self.LLM_MODEL_ALT
            if self.LLM_ACTIVE_PRESET == "alt"
            else self.LLM_MODEL_PRIMARY
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
