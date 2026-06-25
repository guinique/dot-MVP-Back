from unittest.mock import MagicMock, patch

from app.models.tutor import Tutor, TutorStatus
from app.services.agent import _direct_reply_with_sources, generate_tutor_reply


def test_generate_tutor_reply_uses_fallback_when_tool_loop_fails():
    tutor = Tutor(
        id=1,
        title="Math Tutor",
        description="Algebra",
        system_instructions="Explain step by step.",
        status=TutorStatus.ACTIVE,
        source_urls=["https://example.com/math.txt"],
    )

    with (
        patch("app.services.agent.settings") as mock_settings,
        patch("app.services.agent._run_tool_loop", side_effect=RuntimeError("tool call failed")),
        patch("app.services.agent.ChatGroq") as mock_chat_groq,
        patch(
            "app.services.agent._direct_reply_with_sources",
            return_value="Fallback answer about algebra.",
        ) as mock_fallback,
    ):
        mock_settings.llm_provider = "groq"
        mock_settings.groq_api_key = "test-key"
        mock_settings.groq_model = "llama-3.3-70b-versatile"

        reply = generate_tutor_reply(tutor, [], "What is algebra?")

    assert reply == "Fallback answer about algebra."
    mock_fallback.assert_called_once()
    mock_chat_groq.assert_called_once()


def test_direct_reply_with_sources_invokes_llm():
    tutor = Tutor(
        id=1,
        title="Math Tutor",
        description="Algebra",
        system_instructions="Explain step by step.",
        status=TutorStatus.ACTIVE,
        source_urls=["https://example.com/math.txt"],
    )
    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="Here is the explanation.")

    with patch(
        "app.services.agent.fetch_source_content",
        return_value="Algebra is about symbols.",
    ):
        reply = _direct_reply_with_sources(llm, tutor, [], "What is algebra?")

    assert reply == "Here is the explanation."
    llm.invoke.assert_called_once()
