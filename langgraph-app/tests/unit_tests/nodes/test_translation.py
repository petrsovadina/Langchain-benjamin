"""Unit tests for translation nodes (Feature 005 - Phase 3).

Tests Czech ↔ English medical translation with medical term preservation,
abbreviation expansion, and error handling.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.graph import State
from agent.nodes.translation import translate_cz_to_en_node, translate_en_to_cz_node


def _mock_llm(response_text: str):
    """Create a patched ChatAnthropic context manager returning response_text."""
    mock_response = MagicMock()
    mock_response.content = response_text

    mock_llm_instance = MagicMock()
    mock_llm_instance.ainvoke = AsyncMock(return_value=mock_response)

    return patch(
        "agent.nodes.translation.ChatAnthropic",
        return_value=mock_llm_instance,
    )


class TestCzToEnTranslation:
    """Test Czech → English translation for PubMed queries."""

    @pytest.mark.asyncio
    async def test_translate_cz_to_en_basic(self, sample_state, mock_runtime):
        """Test basic Czech → English translation."""
        state = State(
            messages=[
                {"role": "user", "content": "Jaké jsou nejnovější studie o diabetu typu 2?"}
            ],
            next="",
            retrieved_docs=[],
        )

        with _mock_llm("What are the latest studies on type 2 diabetes?"):
            result = await translate_cz_to_en_node(state, mock_runtime)

        assert "research_query" in result
        assert result["research_query"] is not None
        english_query = result["research_query"].query_text
        assert "diabetes" in english_query.lower()
        assert "type 2" in english_query.lower() or "type ii" in english_query.lower()


class TestMedicalTermPreservation:
    """Test preservation of Latin medical terms during translation."""

    @pytest.mark.asyncio
    async def test_translate_preserves_medical_terms(self, mock_runtime):
        """Test that Latin medical terms are preserved unchanged."""
        state = State(
            messages=[
                {"role": "user", "content": "Studie o diabetes mellitus a hypertensio"}
            ],
            next="",
            retrieved_docs=[],
        )

        with _mock_llm("Studies on diabetes mellitus and hypertension"):
            result = await translate_cz_to_en_node(state, mock_runtime)

        english_query = result["research_query"].query_text
        assert "diabetes mellitus" in english_query.lower()
        assert "hypertension" in english_query.lower()


class TestAbbreviationExpansion:
    """Test expansion of Czech medical abbreviations."""

    @pytest.mark.asyncio
    async def test_translate_expands_abbreviations(self, mock_runtime):
        """Test that Czech abbreviations are expanded to full English terms."""
        state = State(
            messages=[{"role": "user", "content": "Léčba DM2 u pacientů s ICHS"}],
            next="",
            retrieved_docs=[],
        )

        with _mock_llm("Treatment of type 2 diabetes in patients with ischemic heart disease"):
            result = await translate_cz_to_en_node(state, mock_runtime)

        english_query = result["research_query"].query_text
        assert "type 2 diabetes" in english_query.lower()
        assert "ischemic heart disease" in english_query.lower()


class TestTranslationErrors:
    """Test error handling in translation nodes."""

    @pytest.mark.asyncio
    async def test_translate_empty_messages_error(self, mock_runtime):
        """Test that empty messages raise ValueError."""
        state = State(
            messages=[],
            next="",
            retrieved_docs=[],
        )

        with pytest.raises((ValueError, IndexError)):
            await translate_cz_to_en_node(state, mock_runtime)


class TestEnToCzTranslation:
    """Test English → Czech translation for PubMed abstracts."""

    @pytest.mark.asyncio
    async def test_translate_en_to_cz_multiple_docs(
        self, sample_pubmed_articles, mock_runtime
    ):
        """Test translation of multiple English abstracts to Czech."""
        from langchain_core.documents import Document

        docs = [
            Document(
                page_content=f"Title: {article.title}\n\nAbstract (EN): {article.abstract}",
                metadata={
                    "source": "PubMed",
                    "pmid": article.pmid,
                    "url": article.pubmed_url,
                    "title": article.title,
                    "abstract_en": article.abstract,
                },
            )
            for article in sample_pubmed_articles[:3]
        ]

        state = State(
            messages=[{"role": "user", "content": "test"}],
            next="",
            retrieved_docs=docs,
        )

        with _mock_llm("Přeložený abstrakt v češtině."):
            result = await translate_en_to_cz_node(state, mock_runtime)

        assert "retrieved_docs" in result
        assert len(result["retrieved_docs"]) == 3
        for doc in result["retrieved_docs"]:
            assert "Abstract (CZ):" in doc.page_content
            assert doc.metadata["source"] == "PubMed"
            assert "pmid" in doc.metadata


class TestMetadataPreservation:
    """Test that metadata is preserved during translation."""

    @pytest.mark.asyncio
    async def test_translate_preserves_metadata(self, mock_runtime):
        """Test that all metadata fields are preserved during EN→CZ translation."""
        from langchain_core.documents import Document

        original_doc = Document(
            page_content="Title: Test\n\nAbstract (EN): Background: Test abstract.",
            metadata={
                "source": "PubMed",
                "pmid": "12345678",
                "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
                "authors": "Smith, John",
                "journal": "NEJM",
                "doi": "10.1056/test",
                "abstract_en": "Background: Test abstract.",
            },
        )

        state = State(
            messages=[{"role": "user", "content": "test"}],
            next="",
            retrieved_docs=[original_doc],
        )

        with _mock_llm("Pozadí: Testovací abstrakt."):
            result = await translate_en_to_cz_node(state, mock_runtime)

        translated_doc = result["retrieved_docs"][0]
        assert translated_doc.metadata["source"] == "PubMed"
        assert translated_doc.metadata["pmid"] == "12345678"
        assert translated_doc.metadata["url"] == "https://pubmed.ncbi.nlm.nih.gov/12345678/"
        assert translated_doc.metadata["authors"] == "Smith, John"
        assert translated_doc.metadata["journal"] == "NEJM"
        assert translated_doc.metadata["doi"] == "10.1056/test"
        assert translated_doc.metadata["abstract_en"] == "Background: Test abstract."
