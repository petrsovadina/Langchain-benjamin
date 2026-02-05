"""Integration tests for Supervisor Multi-Agent Routing (Feature 007).

Tests end-to-end workflow from user query through supervisor to agent response.
Follows TDD workflow per Constitution Principle III.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.graph import graph
from agent.models.supervisor_models import IntentResult, IntentType


def get_message_content(message: dict | object) -> str:
    """Extract content from message (dict or AIMessage object)."""
    if isinstance(message, dict):
        return message.get("content", "")
    return getattr(message, "content", "")


class TestSupervisorFlow:
    """Integration tests for supervisor routing through the graph."""

    @pytest.mark.asyncio
    async def test_supervisor_to_drug_agent_flow(
        self, mock_sukl_client: MagicMock
    ) -> None:
        """Test complete flow: supervisor -> drug_agent -> response."""
        initial_state = {
            "messages": [{"role": "user", "content": "Jaké je složení Ibalginu?"}],
        }

        mock_intent = IntentResult(
            intent_type=IntentType.DRUG_INFO,
            confidence=0.95,
            agents_to_call=["drug_agent"],
            reasoning="Drug composition query",
        )

        with patch("agent.nodes.supervisor.IntentClassifier") as mock_cls:
            mock_classifier = MagicMock()
            mock_classifier.classify_intent = AsyncMock(return_value=mock_intent)
            mock_cls.return_value = mock_classifier

            result = await graph.ainvoke(
                initial_state,
                config={
                    "configurable": {
                        "sukl_mcp_client": mock_sukl_client,
                    }
                },
            )

        assert len(result["messages"]) >= 2
        last_content = get_message_content(result["messages"][-1])
        assert last_content  # Should have a response

    @pytest.mark.asyncio
    async def test_supervisor_to_guidelines_agent_flow(
        self, mock_openai_embeddings_client: MagicMock
    ) -> None:
        """Test complete flow: supervisor -> guidelines_agent -> response."""
        initial_state = {
            "messages": [{"role": "user", "content": "Guidelines pro hypertenzi"}],
        }

        mock_intent = IntentResult(
            intent_type=IntentType.GUIDELINE_LOOKUP,
            confidence=0.95,
            agents_to_call=["guidelines_agent"],
            reasoning="Guideline query",
        )

        with patch("agent.nodes.supervisor.IntentClassifier") as mock_cls:
            mock_classifier = MagicMock()
            mock_classifier.classify_intent = AsyncMock(return_value=mock_intent)
            mock_cls.return_value = mock_classifier

            with patch(
                "openai.AsyncOpenAI",
                return_value=mock_openai_embeddings_client,
            ):
                with patch(
                    "agent.nodes.guidelines_agent.search_guidelines",
                    new_callable=AsyncMock,
                ) as mock_search:
                    mock_search.return_value = [
                        {
                            "guideline_id": "CLS-JEP-2024-001",
                            "title": "Doporučené postupy pro hypertenzi",
                            "section_name": "Farmakologická léčba",
                            "content": "ACE inhibitory jsou léky první volby.",
                            "publication_date": "2024-01-15",
                            "source": "cls_jep",
                            "url": "https://www.cls.cz/guidelines/hypertenze-2024.pdf",
                            "similarity_score": 0.85,
                        }
                    ]

                    result = await graph.ainvoke(
                        initial_state,
                        config={
                            "configurable": {"openai_api_key": "test-key"},
                        },
                    )

        assert len(result["messages"]) >= 2
        assert len(result["retrieved_docs"]) >= 1

    @pytest.mark.asyncio
    async def test_supervisor_fallback_to_placeholder(self) -> None:
        """Test supervisor falls back to placeholder when classification fails."""
        initial_state = {
            "messages": [{"role": "user", "content": "Jaké je počasí?"}],
        }

        with patch("agent.nodes.supervisor.IntentClassifier") as mock_cls:
            mock_classifier = MagicMock()
            mock_classifier.classify_intent = AsyncMock(
                side_effect=Exception("API unavailable")
            )
            mock_cls.return_value = mock_classifier

            result = await graph.ainvoke(initial_state)

        # "Jaké je počasí?" has no keywords -> placeholder echoes
        assert len(result["messages"]) >= 2
        last_content = get_message_content(result["messages"][-1])
        assert "Echo" in last_content

    @pytest.mark.asyncio
    async def test_supervisor_backward_compat_keyword_fallback(
        self, mock_sukl_client: MagicMock
    ) -> None:
        """Test that keyword fallback still routes correctly for drug queries."""
        initial_state = {
            "messages": [{"role": "user", "content": "Najdi lék Ibalgin"}],
        }

        # IntentClassifier fails -> falls back to keyword routing
        with patch("agent.nodes.supervisor.IntentClassifier") as mock_cls:
            mock_classifier = MagicMock()
            mock_classifier.classify_intent = AsyncMock(
                side_effect=Exception("API unavailable")
            )
            mock_cls.return_value = mock_classifier

            result = await graph.ainvoke(
                initial_state,
                config={
                    "configurable": {
                        "sukl_mcp_client": mock_sukl_client,
                    }
                },
            )

        # "lék" keyword -> drug_agent via fallback
        assert len(result["messages"]) >= 2
        last_content = get_message_content(result["messages"][-1])
        assert last_content  # Drug agent should respond
