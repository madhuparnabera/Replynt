from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "REPLYNT Backend"
    app_version: str = "1.0.0"
    debug: bool = False
    api_prefix: str = ""
    cors_allow_origins: List[str] = Field(default_factory=lambda: ["*"])
    models_dir: Path = Path(__file__).resolve().parents[3] / "models"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
