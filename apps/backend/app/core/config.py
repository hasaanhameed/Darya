from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# apps/backend/.env, located relative to this file so it is found from any working directory
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE)

    database_url: str

    # Data-source accounts. Only the ingestion scripts that need them check they are set.
    ewds_api_key: str | None = None  # Copernicus EWDS (GloFAS)
    earthdata_username: str | None = None  # NASA Earthdata (IMERG)
    earthdata_password: str | None = None


settings = Settings()
