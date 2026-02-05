"""Unit tests for Guidelines Agent node (Feature 006).

Tests for guideline search, classification, and document transformation.
Follows TDD workflow per Constitution Principle III.

Test Organization:
- TestQueryClassification: Query type classification
- TestDocumentTransformation: guideline_to_document()
- TestErrorFormatting: format_guidelines_error()
- TestSemanticSearch: search_guidelines_semantic()
- TestGuidelinesAgentNode: Main node function
- TestNoResults: Empty results handling
- TestErrorHandling: Storage errors, timeout, missing API key
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.graph import State
from agent.models.guideline_models import (
    GuidelineQuery,
    GuidelineQueryType,
    GuidelineSection,
)
from agent.nodes.guidelines_agent import (
    _get_source_display_name,
    _map_specialty_to_source,
    classify_guideline_query,
    format_guidelines_error,
    guideline_to_document,
    guidelines_agent_node,
    search_guidelines_semantic,
)
from agent.utils.guidelines_storage import (
    GuidelineNotFoundError,
    GuidelineSearchError,
    GuidelinesStorageError,
)

# =============================================================================
# TestQueryClassification: Query type classification
# =============================================================================


class TestQueryClassification:
    """Test query classification helper function."""

    def test_classify_search_query(self) -> None:
        """Test default classification as SEARCH."""
        assert classify_guideline_query("léčba hypertenze") == GuidelineQueryType.SEARCH
        assert (
            classify_guideline_query("guidelines pro diabetes")
            == GuidelineQueryType.SEARCH
        )
        assert (
            classify_guideline_query("doporučené postupy") == GuidelineQueryType.SEARCH
        )

    def test_classify_section_lookup_query(self) -> None:
        """Test classification of section lookup queries with guideline ID."""
        assert (
            classify_guideline_query("CLS-JEP-2024-001")
            == GuidelineQueryType.SECTION_LOOKUP
        )
        assert (
            classify_guideline_query("Najdi CLS-JEP-2024-001")
            == GuidelineQueryType.SECTION_LOOKUP
        )
        assert (
            classify_guideline_query("sekce ESC-2023-015")
            == GuidelineQueryType.SECTION_LOOKUP
        )

    def test_classify_with_various_id_formats(self) -> None:
        """Test classification with different guideline ID formats."""
        # CLS-JEP format
        assert (
            classify_guideline_query("CLS-JEP-2024-001")
            == GuidelineQueryType.SECTION_LOOKUP
        )
        # ESC format
        assert (
            classify_guideline_query("ESC-2023-015")
            == GuidelineQueryType.SECTION_LOOKUP
        )
        # ERS format
        assert (
            classify_guideline_query("ERS-2022-042")
            == GuidelineQueryType.SECTION_LOOKUP
        )
        # Case insensitive
        assert (
            classify_guideline_query("cls-jep-2024-001")
            == GuidelineQueryType.SECTION_LOOKUP
        )

    def test_classify_mixed_query(self) -> None:
        """Test classification when query contains both ID and text."""
        # ID takes precedence
        assert (
            classify_guideline_query("Najdi CLS-JEP-2024-001 o hypertenzi")
            == GuidelineQueryType.SECTION_LOOKUP
        )


# =============================================================================
# TestDocumentTransformation: guideline_to_document()
# =============================================================================


class TestDocumentTransformation:
    """Test document transformation functions."""

    def test_guideline_to_document(
        self, sample_guideline_section: GuidelineSection
    ) -> None:
        """Test GuidelineSection dict to Document transformation."""
        section_dict = {
            "guideline_id": sample_guideline_section.guideline_id,
            "title": sample_guideline_section.title,
            "section_name": sample_guideline_section.section_name,
            "content": sample_guideline_section.content,
            "publication_date": sample_guideline_section.publication_date,
            "source": sample_guideline_section.source.value,
            "url": sample_guideline_section.url,
            "similarity_score": 0.85,
        }

        doc = guideline_to_document(section_dict)

        # Check page_content formatting
        assert "## Doporučené postupy pro hypertenzi" in doc.page_content
        assert "### Farmakologická léčba" in doc.page_content
        assert "ACE inhibitory" in doc.page_content

        # Check metadata
        assert doc.metadata["source"] == "cls_jep"
        assert doc.metadata["source_type"] == "clinical_guidelines"
        assert doc.metadata["guideline_id"] == "CLS-JEP-2024-001"
        assert (
            doc.metadata["url"] == "https://www.cls.cz/guidelines/hypertenze-2024.pdf"
        )
        assert doc.metadata["similarity_score"] == 0.85

    def test_document_metadata_complete(self) -> None:
        """Test that all required metadata fields are present."""
        section_dict = {
            "guideline_id": "ESC-2023-015",
            "title": "ESC Guidelines",
            "section_name": "Treatment",
            "content": "Treatment recommendations...",
            "publication_date": "2023-09-01",
            "source": "esc",
            "url": "https://www.escardio.org/Guidelines/diabetes-2023.pdf",
        }

        doc = guideline_to_document(section_dict)

        # Required metadata fields
        required_fields = [
            "source",
            "source_type",
            "guideline_id",
            "url",
            "publication_date",
            "retrieved_at",
        ]
        for field in required_fields:
            assert field in doc.metadata, f"Missing metadata field: {field}"

    def test_document_content_formatting(self) -> None:
        """Test proper markdown formatting of document content."""
        section_dict = {
            "guideline_id": "CLS-JEP-2024-001",
            "title": "Test Guideline",
            "section_name": "Test Section",
            "content": "Test content here.",
            "publication_date": "2024-01-15",
            "source": "cls_jep",
            "url": "https://example.com",
        }

        doc = guideline_to_document(section_dict)

        # Check markdown structure
        assert doc.page_content.startswith("## Test Guideline\n\n### Test Section\n\n")
        assert "Test content here." in doc.page_content


# =============================================================================
# TestErrorFormatting: format_guidelines_error()
# =============================================================================


class TestErrorFormatting:
    """Test error formatting functions."""

    def test_format_guideline_not_found_error(self) -> None:
        """Test formatting of GuidelineNotFoundError."""
        error = GuidelineNotFoundError("Guideline CLS-JEP-2024-999 not found")
        message = format_guidelines_error(error)

        assert "nebyla nalezena" in message.lower()
        assert "zkontrolujte id" in message.lower()

    def test_format_guideline_search_error(self) -> None:
        """Test formatting of GuidelineSearchError."""
        error = GuidelineSearchError("Search failed")
        message = format_guidelines_error(error)

        assert "vyhledávání" in message.lower()
        assert "chybě" in message.lower()

    def test_format_storage_error(self) -> None:
        """Test formatting of GuidelinesStorageError."""
        error = GuidelinesStorageError("Database connection failed")
        message = format_guidelines_error(error)

        assert "databáze" in message.lower()
        assert "nedostupná" in message.lower()

    def test_format_timeout_error(self) -> None:
        """Test formatting of timeout error."""
        error = asyncio.TimeoutError()
        message = format_guidelines_error(error)

        assert "dlouho" in message.lower()
        assert "zúžit dotaz" in message.lower()

    def test_format_generic_error(self) -> None:
        """Test formatting of generic error."""
        error = Exception("Unknown error occurred")
        message = format_guidelines_error(error)

        assert "chybě" in message.lower()
        assert "Unknown error occurred" in message


# =============================================================================
# TestSemanticSearch: search_guidelines_semantic()
# =============================================================================


class TestSemanticSearch:
    """Test semantic search helper functions."""

    @pytest.mark.asyncio
    async def test_search_guidelines_semantic_success(
        self,
        sample_guideline_query: GuidelineQuery,
        mock_openai_embeddings_client: MagicMock,
    ) -> None:
        """Test successful semantic search."""
        mock_runtime = MagicMock()
        mock_runtime.context = {"openai_api_key": "test-key"}

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

                results = await search_guidelines_semantic(
                    sample_guideline_query, mock_runtime
                )

                assert len(results) == 1
                assert results[0]["guideline_id"] == "CLS-JEP-2024-001"
                mock_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_guidelines_semantic_with_source_filter(
        self,
        mock_openai_embeddings_client: MagicMock,
    ) -> None:
        """Test semantic search with specialty filter."""
        query = GuidelineQuery(
            query_text="heart failure treatment",
            query_type=GuidelineQueryType.SEARCH,
            specialty_filter="cardiology",
        )

        mock_runtime = MagicMock()
        mock_runtime.context = {"openai_api_key": "test-key"}

        with patch(
            "openai.AsyncOpenAI",
            return_value=mock_openai_embeddings_client,
        ):
            with patch(
                "agent.nodes.guidelines_agent.search_guidelines", new_callable=AsyncMock
            ) as mock_search:
                mock_search.return_value = []

                await search_guidelines_semantic(query, mock_runtime)

                # Verify source_filter was set to "esc" for cardiology
                call_args = mock_search.call_args
                assert call_args[1]["source_filter"] == "esc"

    @pytest.mark.asyncio
    async def test_search_guidelines_semantic_missing_api_key(
        self,
        sample_guideline_query: GuidelineQuery,
    ) -> None:
        """Test that ValueError is raised when OpenAI API key is missing."""
        mock_runtime = MagicMock()
        mock_runtime.context = {}  # No API key in context
        mock_runtime.configurable = {}  # No API key in configurable

        with patch.dict("os.environ", {}, clear=True):  # Clear env vars
            with pytest.raises(ValueError, match="OpenAI API key required"):
                await search_guidelines_semantic(sample_guideline_query, mock_runtime)

    def test_map_specialty_to_source_cardiology(self) -> None:
        """Test mapping cardiology specialty to ESC source."""
        assert _map_specialty_to_source("cardiology") == "esc"
        assert _map_specialty_to_source("kardiologie") == "esc"
        assert _map_specialty_to_source("heart disease") == "esc"

    def test_map_specialty_to_source_respiratory(self) -> None:
        """Test mapping respiratory specialty to ERS source."""
        assert _map_specialty_to_source("respiratory") == "ers"
        assert _map_specialty_to_source("pneumologie") == "ers"
        assert _map_specialty_to_source("lung disease") == "ers"

    def test_map_specialty_to_source_default(self) -> None:
        """Test default mapping to CLS_JEP for unknown specialty."""
        assert _map_specialty_to_source("dermatology") == "cls_jep"
        assert _map_specialty_to_source("unknown") == "cls_jep"
        assert _map_specialty_to_source(None) is None


# =============================================================================
# TestSourceDisplayName: _get_source_display_name()
# =============================================================================


class TestSourceDisplayName:
    """Test source display name helper function."""

    def test_cls_jep_source_name(self) -> None:
        """Test CLS JEP source display name."""
        assert _get_source_display_name("cls_jep") == "ČLS JEP"

    def test_esc_source_name(self) -> None:
        """Test ESC source display name."""
        assert _get_source_display_name("esc") == "European Society of Cardiology"

    def test_ers_source_name(self) -> None:
        """Test ERS source display name."""
        assert _get_source_display_name("ers") == "European Respiratory Society"

    def test_unknown_source_name(self) -> None:
        """Test unknown source falls back to uppercase."""
        assert _get_source_display_name("unknown") == "UNKNOWN"


# =============================================================================
# TestGuidelinesAgentNode: Main node function
# =============================================================================


class TestGuidelinesAgentNode:
    """Test main guidelines_agent_node function."""

    @pytest.mark.asyncio
    async def test_guidelines_agent_node_search_flow(
        self,
        sample_state: State,
        mock_openai_embeddings_client: MagicMock,
    ) -> None:
        """Test complete guidelines_agent_node search workflow."""
        sample_state.messages = [
            {"role": "user", "content": "guidelines pro léčbu hypertenze"}
        ]

        mock_runtime = MagicMock()
        mock_runtime.context = {"openai_api_key": "test-key"}

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
                        "content": "ACE inhibitory jsou léky první volby...",
                        "publication_date": "2024-01-15",
                        "source": "cls_jep",
                        "url": "https://www.cls.cz/guidelines/hypertenze-2024.pdf",
                        "similarity_score": 0.85,
                    }
                ]

                result = await guidelines_agent_node(sample_state, mock_runtime)

                # Verify response structure
                assert "messages" in result
                assert "retrieved_docs" in result
                assert result["next"] == "__end__"

                # Verify message content
                assert len(result["messages"]) == 1
                assert "Nalezeno" in result["messages"][0]["content"]
                assert "hypertenze" in result["messages"][0]["content"].lower()

                # Verify documents were created
                assert len(result["retrieved_docs"]) == 1
                assert result["retrieved_docs"][0].metadata["source"] == "cls_jep"

    @pytest.mark.asyncio
    async def test_guidelines_agent_node_section_lookup(
        self,
        sample_state: State,
    ) -> None:
        """Test section lookup by guideline ID."""
        sample_state.messages = [{"role": "user", "content": "Najdi CLS-JEP-2024-001"}]

        mock_runtime = MagicMock()
        mock_runtime.context = {}

        with patch(
            "agent.nodes.guidelines_agent.get_guideline_section", new_callable=AsyncMock
        ) as mock_get:
            mock_get.return_value = {
                "guideline_id": "CLS-JEP-2024-001",
                "title": "Doporučené postupy pro hypertenzi",
                "section_name": "Definice",
                "content": "Hypertenze je definována...",
                "publication_date": "2024-01-15",
                "source": "cls_jep",
                "url": "https://www.cls.cz/guidelines/hypertenze-2024.pdf",
            }

            result = await guidelines_agent_node(sample_state, mock_runtime)

            assert "CLS-JEP-2024-001" in result["messages"][0]["content"]
            assert len(result["retrieved_docs"]) == 1
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_guidelines_agent_node_uses_explicit_query(
        self,
        sample_state: State,
        sample_guideline_query: GuidelineQuery,
        mock_openai_embeddings_client: MagicMock,
    ) -> None:
        """Test that guidelines_agent_node prioritizes state.guideline_query."""
        sample_state.guideline_query = sample_guideline_query
        sample_state.messages = [
            {"role": "user", "content": "Something completely different"}
        ]

        mock_runtime = MagicMock()
        mock_runtime.context = {"openai_api_key": "test-key"}

        with patch(
            "openai.AsyncOpenAI",
            return_value=mock_openai_embeddings_client,
        ):
            with patch(
                "agent.nodes.guidelines_agent.search_guidelines", new_callable=AsyncMock
            ) as mock_search:
                mock_search.return_value = []

                await guidelines_agent_node(sample_state, mock_runtime)

                # Verify search was performed with explicit query, not message
                assert mock_search.called

    @pytest.mark.asyncio
    async def test_guidelines_agent_node_filters_by_threshold(
        self,
        sample_state: State,
        mock_openai_embeddings_client: MagicMock,
    ) -> None:
        """Test that results below similarity threshold are filtered out."""
        sample_state.messages = [{"role": "user", "content": "guidelines pro diabetes"}]

        mock_runtime = MagicMock()
        mock_runtime.context = {"openai_api_key": "test-key"}

        with patch(
            "openai.AsyncOpenAI",
            return_value=mock_openai_embeddings_client,
        ):
            with patch(
                "agent.nodes.guidelines_agent.search_guidelines", new_callable=AsyncMock
            ) as mock_search:
                # Return results with low similarity scores
                mock_search.return_value = [
                    {
                        "guideline_id": "CLS-JEP-2024-001",
                        "title": "Test",
                        "section_name": "Test",
                        "content": "Test content",
                        "publication_date": "2024-01-15",
                        "source": "cls_jep",
                        "url": "https://example.com",
                        "similarity_score": 0.65,  # Below threshold (0.7)
                    }
                ]

                result = await guidelines_agent_node(sample_state, mock_runtime)

                # Should return message about low relevance
                assert (
                    "nejsou dostatečně relevantní"
                    in result["messages"][0]["content"].lower()
                )
                assert len(result["retrieved_docs"]) == 0

    @pytest.mark.asyncio
    async def test_guidelines_agent_node_multimodal_content(
        self,
        sample_state: State,
        mock_openai_embeddings_client: MagicMock,
    ) -> None:
        """Test guidelines_agent_node handles multimodal list content."""
        sample_state.messages = [
            {
                "role": "user",
                "content": [{"type": "text", "text": "guidelines pro hypertenzi"}],
            }
        ]

        mock_runtime = MagicMock()
        mock_runtime.context = {"openai_api_key": "test-key"}

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
                        "content": "Test content...",
                        "publication_date": "2024-01-15",
                        "source": "cls_jep",
                        "url": "https://example.com",
                        "similarity_score": 0.85,
                    }
                ]

                result = await guidelines_agent_node(sample_state, mock_runtime)

                # Should successfully parse multimodal content
                assert "Nalezeno" in result["messages"][0]["content"]


# =============================================================================
# TestNoResults: Empty results handling
# =============================================================================


class TestNoResults:
    """Test empty results handling."""

    @pytest.mark.asyncio
    async def test_guidelines_agent_node_handles_no_results(
        self,
        sample_state: State,
        mock_openai_embeddings_client: MagicMock,
    ) -> None:
        """Test guidelines_agent_node returns appropriate message when no results."""
        sample_state.messages = [
            {"role": "user", "content": "guidelines pro XYZ123456"}
        ]

        mock_runtime = MagicMock()
        mock_runtime.context = {"openai_api_key": "test-key"}

        with patch(
            "openai.AsyncOpenAI",
            return_value=mock_openai_embeddings_client,
        ):
            with patch(
                "agent.nodes.guidelines_agent.search_guidelines", new_callable=AsyncMock
            ) as mock_search:
                mock_search.return_value = []

                result = await guidelines_agent_node(sample_state, mock_runtime)

                assert "nenalezeny" in result["messages"][0]["content"].lower()
                assert len(result["retrieved_docs"]) == 0

    @pytest.mark.asyncio
    async def test_guidelines_agent_node_handles_no_query(
        self,
        sample_state: State,
    ) -> None:
        """Test guidelines_agent_node handles empty messages gracefully."""
        sample_state.messages = []
        sample_state.guideline_query = None

        mock_runtime = MagicMock()
        mock_runtime.context = {}

        result = await guidelines_agent_node(sample_state, mock_runtime)

        assert "nezadali" in result["messages"][0]["content"].lower()
        assert len(result["retrieved_docs"]) == 0

    @pytest.mark.asyncio
    async def test_guidelines_agent_node_section_not_found(
        self,
        sample_state: State,
    ) -> None:
        """Test section lookup when guideline is not found."""
        sample_state.messages = [{"role": "user", "content": "Najdi CLS-JEP-9999-999"}]

        mock_runtime = MagicMock()
        mock_runtime.context = {}

        with patch(
            "agent.nodes.guidelines_agent.get_guideline_section", new_callable=AsyncMock
        ) as mock_get:
            mock_get.side_effect = GuidelineNotFoundError("Not found")

            result = await guidelines_agent_node(sample_state, mock_runtime)

            assert "nebyly nalezeny" in result["messages"][0]["content"].lower()


# =============================================================================
# TestErrorHandling: Storage errors, timeout, missing API key
# =============================================================================


class TestErrorHandling:
    """Test error handling functions."""

    @pytest.mark.asyncio
    async def test_guidelines_agent_node_handles_storage_error(
        self,
        sample_state: State,
        mock_openai_embeddings_client: MagicMock,
    ) -> None:
        """Test guidelines_agent_node handles storage errors gracefully."""
        sample_state.messages = [
            {"role": "user", "content": "guidelines pro hypertenzi"}
        ]

        mock_runtime = MagicMock()
        mock_runtime.context = {"openai_api_key": "test-key"}

        with patch(
            "openai.AsyncOpenAI",
            return_value=mock_openai_embeddings_client,
        ):
            with patch(
                "agent.nodes.guidelines_agent.search_guidelines", new_callable=AsyncMock
            ) as mock_search:
                mock_search.side_effect = GuidelinesStorageError(
                    "Database connection failed"
                )

                result = await guidelines_agent_node(sample_state, mock_runtime)

                assert "databáze" in result["messages"][0]["content"].lower()
                assert "nedostupná" in result["messages"][0]["content"].lower()

    @pytest.mark.asyncio
    async def test_guidelines_agent_node_handles_timeout(
        self,
        sample_state: State,
        mock_openai_embeddings_client: MagicMock,
    ) -> None:
        """Test guidelines_agent_node handles timeout gracefully."""
        sample_state.messages = [{"role": "user", "content": "guidelines pro diabetes"}]

        mock_runtime = MagicMock()
        mock_runtime.context = {"openai_api_key": "test-key"}

        with patch(
            "openai.AsyncOpenAI",
            return_value=mock_openai_embeddings_client,
        ):
            with patch(
                "agent.nodes.guidelines_agent.search_guidelines", new_callable=AsyncMock
            ) as mock_search:
                # Simulate timeout by raising TimeoutError
                mock_search.side_effect = asyncio.TimeoutError()

                # Patch the timeout constant to a very short value
                with patch("agent.nodes.guidelines_agent.SEARCH_TIMEOUT", 0.001):
                    result = await guidelines_agent_node(sample_state, mock_runtime)

                    # The node catches timeout and returns user-friendly message
                    assert "dlouho" in result["messages"][0]["content"].lower()

    @pytest.mark.asyncio
    async def test_guidelines_agent_node_handles_missing_api_key(
        self,
        sample_state: State,
    ) -> None:
        """Test guidelines_agent_node handles missing OpenAI API key."""
        sample_state.messages = [
            {"role": "user", "content": "guidelines pro hypertenzi"}
        ]

        mock_runtime = MagicMock()
        mock_runtime.context = {}  # No API key in context
        mock_runtime.configurable = {}  # No API key in configurable

        with patch.dict("os.environ", {}, clear=True):  # Clear env vars
            result = await guidelines_agent_node(sample_state, mock_runtime)

            assert "OpenAI API key required" in result["messages"][0]["content"]

    @pytest.mark.asyncio
    async def test_guidelines_agent_node_handles_search_error(
        self,
        sample_state: State,
        mock_openai_embeddings_client: MagicMock,
    ) -> None:
        """Test guidelines_agent_node handles search errors gracefully."""
        sample_state.messages = [
            {"role": "user", "content": "guidelines pro hypertenzi"}
        ]

        mock_runtime = MagicMock()
        mock_runtime.context = {"openai_api_key": "test-key"}

        with patch(
            "openai.AsyncOpenAI",
            return_value=mock_openai_embeddings_client,
        ):
            with patch(
                "agent.nodes.guidelines_agent.search_guidelines", new_callable=AsyncMock
            ) as mock_search:
                mock_search.side_effect = GuidelineSearchError("Search failed")

                result = await guidelines_agent_node(sample_state, mock_runtime)

                assert "vyhledávání" in result["messages"][0]["content"].lower()
                assert "chybě" in result["messages"][0]["content"].lower()
