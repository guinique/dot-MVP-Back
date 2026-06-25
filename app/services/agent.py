import logging
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool, tool
from langchain_groq import ChatGroq

from app.config import get_settings
from app.models.tutor import ChatMessage, Tutor
from app.services.knowledge import fetch_source_content

logger = logging.getLogger(__name__)
settings = get_settings()

MAX_TOOL_ITERATIONS = 4
MAX_SOURCE_CHARS_FALLBACK = 3000


def _run_config(tutor: Tutor, session_key: str | None = None) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "tutor_id": tutor.id,
        "tutor_title": tutor.title,
    }
    if session_key:
        metadata["session_key"] = session_key

    return {
        "metadata": metadata,
        "tags": ["dot-mvp", f"tutor:{tutor.id}"],
    }


def _build_tools(source_urls: list[str]) -> list[BaseTool]:
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


def _build_system_message(tutor: Tutor) -> SystemMessage:
    return SystemMessage(
        content=(
            "You are a personalized tutor. Follow the behavior instructions.\n"
            "You have tools to list and fetch configured knowledge sources. "
            "Use them when the user asks about topics that may be covered by those sources. "
            "Do not invent facts when sources are available.\n\n"
            f"Tutor instructions:\n{tutor.system_instructions}"
        )
    )


def _build_source_context(source_urls: list[str]) -> str:
    if not source_urls:
        return ""

    blocks: list[str] = []
    for url in source_urls[:3]:
        content = fetch_source_content(url, max_chars=MAX_SOURCE_CHARS_FALLBACK)
        blocks.append(f"--- {url} ---\n{content}")

    return "\n\nReference material from configured sources:\n" + "\n\n".join(blocks)


def _direct_reply_with_sources(
    llm: ChatGroq,
    tutor: Tutor,
    history: list[ChatMessage],
    user_message: str,
    session_key: str | None = None,
) -> str:
    source_context = _build_source_context(tutor.source_urls or [])
    system_content = (
        "You are a personalized tutor. Follow the behavior instructions.\n"
        "Answer using the reference material below when relevant. "
        "Do not invent facts beyond what is provided.\n\n"
        f"Tutor instructions:\n{tutor.system_instructions}"
        f"{source_context}"
    )
    messages: list[Any] = [SystemMessage(content=system_content)]
    messages.extend(_history_to_messages(history))
    messages.append(HumanMessage(content=user_message))

    response = llm.invoke(messages, config=_run_config(tutor, session_key))
    content = getattr(response, "content", str(response))
    return str(content).strip() or "I could not generate a response."


def _run_tool_loop(
    llm: ChatGroq,
    tools: list[BaseTool],
    tutor: Tutor,
    history: list[ChatMessage],
    user_message: str,
    session_key: str | None = None,
) -> str:
    tools_by_name = {tool_item.name: tool_item for tool_item in tools}
    llm_with_tools = llm.bind_tools(tools)

    messages: list[Any] = [_build_system_message(tutor)]
    messages.extend(_history_to_messages(history))
    messages.append(HumanMessage(content=user_message))

    run_config = _run_config(tutor, session_key)

    for _ in range(MAX_TOOL_ITERATIONS):
        ai_msg = llm_with_tools.invoke(messages, config=run_config)
        if not getattr(ai_msg, "tool_calls", None):
            content = getattr(ai_msg, "content", "")
            if str(content).strip():
                return str(content).strip()

        messages.append(ai_msg)
        for tool_call in ai_msg.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call.get("args") or {}
            selected = tools_by_name.get(tool_name)
            if selected is None:
                output = f"Unknown tool: {tool_name}"
            else:
                output = selected.invoke(tool_args)
            messages.append(
                ToolMessage(
                    content=str(output),
                    tool_call_id=tool_call["id"],
                )
            )

    final = llm.invoke(messages, config=run_config)
    content = getattr(final, "content", str(final))
    return str(content).strip() or "I could not generate a response."


def generate_tutor_reply(
    tutor: Tutor,
    history: list[ChatMessage],
    user_message: str,
    session_key: str | None = None,
) -> str:
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
        streaming=False,
    )

    try:
        return _run_tool_loop(llm, tools, tutor, history, user_message, session_key)
    except Exception as exc:
        logger.warning("Tool-calling agent failed, using direct reply fallback: %s", exc)
        try:
            return _direct_reply_with_sources(llm, tutor, history, user_message, session_key)
        except Exception as fallback_exc:
            logger.exception("Direct reply fallback failed: %s", fallback_exc)
            return "Sorry, I had trouble generating a response. Please try again."
