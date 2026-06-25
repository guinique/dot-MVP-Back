import logging
from typing import Any

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_groq import ChatGroq

from app.config import get_settings
from app.models.tutor import ChatMessage, Tutor
from app.services.knowledge import fetch_source_content

logger = logging.getLogger(__name__)
settings = get_settings()


def _build_tools(source_urls: list[str]):
    urls = list(source_urls)

    @tool
    def list_knowledge_sources() -> str:
        """List configured knowledge source URLs for this tutor."""
        if not urls:
            return "No external knowledge sources configured."
        return "\n".join(f"- {url}" for url in urls)

    @tool
    def fetch_knowledge_source(url: str) -> str:
        """Fetch text content from a configured knowledge source URL."""
        if url not in urls:
            return "URL is not in the tutor's configured sources."
        return fetch_source_content(url)

    return [list_knowledge_sources, fetch_knowledge_source]


def _history_to_messages(history: list[ChatMessage]) -> list[Any]:
    messages: list[Any] = []
    for item in history:
        if item.role.value == "user":
            messages.append(HumanMessage(content=item.content))
        else:
            messages.append(AIMessage(content=item.content))
    return messages


def _mock_reply(tutor: Tutor, user_message: str) -> str:
    sources = tutor.source_urls or []
    source_hint = f" Sources: {', '.join(sources)}." if sources else ""
    return (
        f"[mock] Tutor '{tutor.title}' received: {user_message}."
        f" Instructions applied.{source_hint}"
    )


def generate_tutor_reply(tutor: Tutor, history: list[ChatMessage], user_message: str) -> str:
    if settings.llm_provider == "mock":
        return _mock_reply(tutor, user_message)

    if not settings.groq_api_key:
        logger.error("GROQ_API_KEY is not configured")
        return "AI service is not configured. Set GROQ_API_KEY or use LLM_PROVIDER=mock."

    tools = _build_tools(tutor.source_urls or [])
    llm = ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=0.2,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a personalized tutor. Follow the behavior instructions.\n"
                "Use tools to inspect knowledge sources when needed. "
                "Do not invent facts when sources are available.\n\n"
                "Tutor instructions:\n{instructions}",
            ),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=False, max_iterations=4)

    try:
        result = executor.invoke(
            {
                "instructions": tutor.system_instructions,
                "input": user_message,
                "chat_history": _history_to_messages(history),
            }
        )
        return str(result.get("output", "")).strip() or "I could not generate a response."
    except Exception as exc:
        logger.exception("Agent execution failed: %s", exc)
        return "Sorry, I had trouble generating a response. Please try again."
