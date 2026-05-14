import pytest

from app.config.settings import Settings


def test_settings_allows_development_without_secrets():
    settings = Settings(app_env="development")

    settings.validate_runtime()


def test_settings_requires_security_in_production():
    settings = Settings(app_env="production", auth_enabled=False, signature_enabled=False)

    with pytest.raises(RuntimeError) as exc:
        settings.validate_runtime()

    assert "AUTH_ENABLED=true" in str(exc.value)
    assert "JWT_SECRET" in str(exc.value)


def test_settings_accepts_secure_production_config():
    settings = Settings(
        app_env="production",
        auth_enabled=True,
        jwt_secret="secret",
        signature_enabled=True,
        hmac_secret="secret",
    )

    settings.validate_runtime()
