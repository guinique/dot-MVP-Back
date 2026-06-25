import os

from app.config import Settings
from app.observability import configure_langsmith


def test_configure_langsmith_sets_env_vars(monkeypatch):
    monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)
    monkeypatch.delenv("LANGCHAIN_PROJECT", raising=False)

    settings = Settings(
        secret_key="test",
        langchain_tracing_v2=True,
        langchain_api_key="lsv2_test_key",
        langchain_project="dot-mvp-test",
    )
    configure_langsmith(settings)

    assert os.environ["LANGCHAIN_TRACING_V2"] == "true"
    assert os.environ["LANGCHAIN_API_KEY"] == "lsv2_test_key"
    assert os.environ["LANGCHAIN_PROJECT"] == "dot-mvp-test"


def test_configure_langsmith_skips_when_disabled(monkeypatch):
    monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)

    settings = Settings(secret_key="test", langchain_tracing_v2=False)
    configure_langsmith(settings)

    assert "LANGCHAIN_TRACING_V2" not in os.environ
