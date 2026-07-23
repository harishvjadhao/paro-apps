from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="BACKEND_")

    db_path: str = Field(default="backend/data/app.db")
    data_source_mode: str = Field(default="mock")
    sync_enabled: bool = Field(default=True)
    cors_origin: str = Field(default="http://127.0.0.1:5173")

    @property
    def sqlite_url(self) -> str:
        db_file = Path(self.db_path)
        return f"sqlite:///{db_file.as_posix()}"


@lru_cache
def get_settings() -> Settings:
    return Settings()