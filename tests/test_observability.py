import os

from app.config import Settings
from app.observability import configure_langsmith


def test_configure_langsmith_sets_env_vars(monkeypatch):
    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    monkeypatch.delenv("LANGSMITH_PROJECT", raising=False)

    settings = Settings(
        secret_key="test",
        langsmith_tracing=True,
        langsmith_api_key="lsv2_test_key",
        langsmith_project="dot-mvp-test",
    )
    configure_langsmith(settings)

    assert os.environ["LANGSMITH_TRACING"] == "true"
    assert os.environ["LANGSMITH_API_KEY"] == "lsv2_test_key"
    assert os.environ["LANGSMITH_PROJECT"] == "dot-mvp-test"


def test_configure_langsmith_skips_when_disabled(monkeypatch):
    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)

    settings = Settings(secret_key="test", langsmith_tracing=False)
    configure_langsmith(settings)

    assert "LANGSMITH_TRACING" not in os.environ
