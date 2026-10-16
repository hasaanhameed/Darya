from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# apps/backend/.env, located relative to this file so it is found from any working directory
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE)

    database_url: str


settings = Settings()
