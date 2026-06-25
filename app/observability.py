import logging
import os

from app.config import Settings

logger = logging.getLogger(__name__)


def configure_langsmith(settings: Settings) -> None:
    """Enable LangSmith tracing for LangChain runs when configured."""
    if not settings.langchain_tracing_v2:
        return
    if not settings.langchain_api_key:
        logger.warning("LANGCHAIN_TRACING_V2 is enabled but LANGCHAIN_API_KEY is empty")
        return

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    if settings.langchain_endpoint:
        os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint

    logger.info("LangSmith tracing enabled for project '%s'", settings.langchain_project)
