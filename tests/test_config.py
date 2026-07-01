import pytest
from pydantic import ValidationError

from app.core.config import DEFAULT_SECRET_KEY, Settings


def test_production_rejects_default_secret():
    with pytest.raises(ValidationError):
        Settings(app_env="production", secret_key=DEFAULT_SECRET_KEY)


def test_production_accepts_custom_secret():
    settings = Settings(
        app_env="production",
        secret_key="a-strong-random-production-secret-key",
    )
    assert settings.is_production
