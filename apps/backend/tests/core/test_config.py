from app.core.config import Settings


def test_source_credentials_are_optional(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    for name in ["EWDS_API_KEY", "EARTHDATA_USERNAME", "EARTHDATA_PASSWORD"]:
        monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=None)

    assert settings.ewds_api_key is None
    assert settings.earthdata_username is None
    assert settings.earthdata_password is None


def test_source_credentials_are_read_from_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
    monkeypatch.setenv("EWDS_API_KEY", "ewds-key")
    monkeypatch.setenv("EARTHDATA_USERNAME", "someone")
    monkeypatch.setenv("EARTHDATA_PASSWORD", "secret")

    settings = Settings(_env_file=None)

    assert settings.ewds_api_key == "ewds-key"
    assert settings.earthdata_username == "someone"
    assert settings.earthdata_password == "secret"
