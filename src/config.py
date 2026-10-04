"""Central settings loaded from the .env file in the backend folder."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # AI model providers
    google_api_key: str = ""
    groq_api_key: str = ""
    xai_api_key: str = ""
    primary_llm_provider: str = "gemini"
    gemini_model: str = "gemini-2.5-flash"
    groq_model: str = "llama-3.3-70b-versatile"
    xai_model: str = "grok-3-mini"
    llm_temperature: float = 0.3

    # Tools
    openweather_api_key: str = ""
    tavily_api_key: str = ""

    # Database
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "weather_search_agent"

    # Server
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
