"""Integration tests for Guidelines Agent flow (Feature 006).

Tests end-to-end workflow from user query to response with citations.
Follows TDD workflow per Constitution Principle III.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.graph import graph
from agent.models.guideline_models import GuidelineQuery, GuidelineQueryType


def get_message_content(message: dict | object) -> str:
    """Extract content from message (dict or AIMessage object)."""
    if isinstance(message, dict):
        return message.get("content", "")
    return getattr(message, "content", "")


class TestGuidelinesAgentFlow:
    """Integration tests for guidelines agent workflow."""

    @pytest.mark.asyncio
    async def test_guidelines_agent_end_to_end_search(
        self,
        mock_openai_embeddings_client: MagicMock,
    ) -> None:
        """Test complete search flow from user query to response."""
        initial_state = {
            "messages": [
                {"role": "user", "content": "doporučené postupy pro bolest zad"}
            ],
        }

        with patch(
            "openai.AsyncOpenAI",
            return_value=mock_openai_embeddings_client,
        ):
            with patch(
                "agent.nodes.guidelines_agent.search_guidelines", new_callable=AsyncMock
            ) as mock_search:
                mock_search.return_value = [
                    {
                        "guideline_id": "CLS-JEP-2024-001",
                        "title": "Doporučené postupy pro bolest zad",
                        "section_name": "Farmakologická léčba",
                        "content": "NSAIDs jsou léky první volby.",
                        "publication_date": "2024-01-15",
                        "source": "cls_jep",
                        "url": "https://www.cls.cz/guidelines/bolest-zad-2024.pdf",
                        "similarity_score": 0.85,
                    }
                ]

                # Invoke graph with context containing OpenAI API key
                result = await graph.ainvoke(
                    initial_state,
                    config={"configurable": {"openai_api_key": "test-key"}},
                )

                # Verify final state
                assert len(result["messages"]) >= 2  # User + assistant
                last_content = get_message_content(result["messages"][-1])
                assert "bolest" in last_content.lower() or "Nalezeno" in last_content
                assert len(result["retrieved_docs"]) == 1
                assert result["retrieved_docs"][0].metadata["source"] == "cls_jep"

    @pytest.mark.asyncio
    async def test_guidelines_agent_end_to_end_section_lookup(self) -> None:
        """Test complete section lookup flow by guideline ID."""
        initial_state = {
            "messages": [{"role": "user", "content": "Najdi CLS-JEP-2024-001"}],
        }

        with patch(
            "agent.nodes.guidelines_agent.get_guideline_section", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = {
                "guideline_id": "CLS-JEP-2024-001",
                "title": "Doporučené postupy pro hypertenzi",
                "section_name": "Definice a klasifikace",
                "content": "Hypertenze je definována jako opakovaně naměřený krevní tlak ≥140/90 mmHg.",
                "publication_date": "2024-01-15",
                "source": "cls_jep",
                "url": "https://www.cls.cz/guidelines/hypertenze-2024.pdf",
            }

            result = await graph.ainvoke(initial_state)

            last_content = get_message_content(result["messages"][-1])
            assert "CLS-JEP-2024-001" in last_content
            assert len(result["retrieved_docs"]) == 1

    @pytest.mark.asyncio
    async def test_guidelines_routing_from_start_with_keyword(
        self,
        mock_openai_embeddings_client: MagicMock,
    ) -> None:
        """Test routing from __start__ to guidelines_agent based on keywords.

        Uses query without research keywords to ensure proper routing.
        """
        initial_state = {
            "messages": [
                {
                    "role": "user",
                    "content": "Jaké jsou doporučené postupy pro bolest zad?",
                }
            ],
        }

        with patch(
            "openai.AsyncOpenAI",
            return_value=mock_openai_embeddings_client,
        ):
            with patch(
                "agent.nodes.guidelines_agent.search_guidelines", new_callable=AsyncMock
            ) as mock_search:
                mock_search.return_value = []

                await graph.ainvoke(
                    initial_state,
                    config={"configurable": {"openai_api_key": "test-key"}},
                )

                # Verify routing worked (guidelines_agent was called)
                assert mock_search.called

    @pytest.mark.asyncio
    async def test_guidelines_agent_with_explicit_query(
        self,
        mock_openai_embeddings_client: MagicMock,
    ) -> None:
        """Test guidelines agent flow with explicit guideline_query in state."""
        guideline_query = GuidelineQuery(
            query_text="léčba hypertenze podle ČLS JEP",
            query_type=GuidelineQueryType.SEARCH,
            specialty_filter="cardiology",
        )

        initial_state = {
            "messages": [{"role": "user", "content": "Something completely different"}],
            "guideline_query": guideline_query,
        }

        with patch(
            "openai.AsyncOpenAI",
            return_value=mock_openai_embeddings_client,
        ):
            with patch(
                "agent.nodes.guidelines_agent.search_guidelines", new_callable=AsyncMock
            ) as mock_search:
                mock_search.return_value = [
                    {
                        "guideline_id": "CLS-JEP-2024-001",
                        "title": "Hypertenze",
                        "section_name": "Léčba",
                        "content": "ACE inhibitory...",
                        "publication_date": "2024-01-15",
                        "source": "cls_jep",
                        "url": "https://example.com",
                        "similarity_score": 0.85,
                    }
                ]

                await graph.ainvoke(
                    initial_state,
                    config={"configurable": {"openai_api_key": "test-key"}},
                )

                # Verify guidelines_agent was invoked via explicit query
                assert mock_search.called
                # Verify source_filter was applied (cardiology -> esc)
                call_args = mock_search.call_args
                assert call_args[1]["source_filter"] == "esc"

    @pytest.mark.asyncio
    async def test_guidelines_agent_returns_documents_with_citations(
        self,
        mock_openai_embeddings_client: MagicMock,
    ) -> None:
        """Test that guidelines agent returns properly formatted documents."""
        initial_state = {
            "messages": [{"role": "user", "content": "guidelines pro hypertenzi"}],
        }

        with patch(
            "openai.AsyncOpenAI",
            return_value=mock_openai_embeddings_client,
        ):
            with patch(
                "agent.nodes.guidelines_agent.search_guidelines", new_callable=AsyncMock
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
                    },
                    {
                        "guideline_id": "ESC-2023-015",
                        "title": "ESC Guidelines",
                        "section_name": "Treatment",
                        "content": "Beta blockers are recommended.",
                        "publication_date": "2023-09-01",
                        "source": "esc",
                        "url": "https://www.escardio.org/Guidelines/cardio-2023.pdf",
                        "similarity_score": 0.80,
                    },
                ]

                result = await graph.ainvoke(
                    initial_state,
                    config={"configurable": {"openai_api_key": "test-key"}},
                )

                # Verify documents have proper structure
                docs = result["retrieved_docs"]
                assert len(docs) == 2

                # Check first document metadata
                assert docs[0].metadata["source_type"] == "clinical_guidelines"
                assert docs[0].metadata["guideline_id"] == "CLS-JEP-2024-001"
                assert "retrieved_at" in docs[0].metadata

                # Check second document metadata
                assert docs[1].metadata["source"] == "esc"

    @pytest.mark.asyncio
    async def test_guidelines_agent_graceful_degradation_no_api_key(self) -> None:
        """Test guidelines agent handles missing API key gracefully."""
        initial_state = {
            "messages": [{"role": "user", "content": "guidelines pro hypertenzi"}],
        }

        with patch.dict("os.environ", {}, clear=True):
            result = await graph.ainvoke(initial_state)

            # Should return error message about missing API key
            last_content = get_message_content(result["messages"][-1])
            assert "OpenAI API key required" in last_content
            assert len(result["retrieved_docs"]) == 0


class TestGuidelinesRoutingIntegration:
    """Integration tests for guidelines routing within the graph."""

    @pytest.mark.asyncio
    async def test_guidelines_keyword_routes_correctly(
        self,
        mock_openai_embeddings_client: MagicMock,
    ) -> None:
        """Test that guidelines-specific keywords route to guidelines_agent.

        Uses queries without research keywords (like diabetes, studie, etc.)
        to ensure proper routing to guidelines_agent.
        """
        # Queries without research keywords - guidelines keywords only
        test_queries = [
            "guidelines pro bolest zad",
            "doporučené postupy pro hypertenzi",
            "standardy péče o pacienty",
            "CLS JEP doporučení pro bolest",
            "ESC guidelines for arrhythmia",
        ]

        for query in test_queries:
            initial_state = {
                "messages": [{"role": "user", "content": query}],
            }

            with patch(
                "openai.AsyncOpenAI",
                return_value=mock_openai_embeddings_client,
            ):
                with patch(
                    "agent.nodes.guidelines_agent.search_guidelines",
                    new_callable=AsyncMock,
                ) as mock_search:
                    mock_search.return_value = []

                    await graph.ainvoke(
                        initial_state,
                        config={"configurable": {"openai_api_key": "test-key"}},
                    )

                    # Verify guidelines_agent was called for each query
                    assert mock_search.called, (
                        f"Guidelines agent not called for: {query}"
                    )

    @pytest.mark.asyncio
    async def test_section_lookup_id_routes_correctly(self) -> None:
        """Test that guideline ID patterns route to guidelines_agent for lookup."""
        test_ids = [
            "CLS-JEP-2024-001",
            "ESC-2023-015",
            "ERS-2022-042",
        ]

        for gid in test_ids:
            initial_state = {
                "messages": [{"role": "user", "content": f"Najdi {gid}"}],
            }

            with patch(
                "agent.nodes.guidelines_agent.get_guideline_section",
                new_callable=AsyncMock,
            ) as mock_get:
                mock_get.return_value = {
                    "guideline_id": gid,
                    "title": "Test Guideline",
                    "section_name": "Test Section",
                    "content": "Test content",
                    "publication_date": "2024-01-15",
                    "source": "cls_jep",
                    "url": "https://example.com",
                }

                await graph.ainvoke(initial_state)

                # Verify get_guideline_section was called for each ID
                assert mock_get.called, f"Section lookup not called for ID: {gid}"
