import logging
import os

from app.config import Settings

logger = logging.getLogger(__name__)


def configure_langsmith(settings: Settings) -> None:
    """Enable LangSmith tracing for LangChain runs when configured.

    See: https://docs.langchain.com/langsmith/trace-with-langchain
    """
    if not settings.langsmith_tracing:
        return
    if not settings.langsmith_api_key:
        logger.warning("LANGSMITH_TRACING is enabled but LANGSMITH_API_KEY is empty")
        return

    # Pydantic reads .env into Settings but does not export to os.environ;
    # LangChain/LangSmith read tracing flags from the process environment.
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    if settings.langsmith_endpoint:
        os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint

    logger.info("LangSmith tracing enabled for project '%s'", settings.langsmith_project)
