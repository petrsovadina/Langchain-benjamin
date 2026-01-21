"""Unit tests for translation nodes (Feature 005 - Phase 3).

Tests Czech ↔ English medical translation with medical term preservation,
abbreviation expansion, and error handling.

TDD Workflow: These tests are written FIRST and should FAIL before implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.agent.graph import State, Context
from src.agent.nodes.translation import translate_cz_to_en_node, translate_en_to_cz_node


class TestCzToEnTranslation:
    """Test Czech → English translation for PubMed queries."""

    @pytest.mark.asyncio
    async def test_translate_cz_to_en_basic(self, sample_state, mock_runtime):
        """Test basic Czech → English translation.

        Verifies that Czech medical query is translated to English
        and research_query is populated in state.
        """
        # Arrange
        state = State(
            messages=[
                {"role": "user", "content": "Jaké jsou nejnovější studie o diabetu typu 2?"}
            ],
            next="",
            retrieved_docs=[],
        )

        # Act
        result = await translate_cz_to_en_node(state, mock_runtime)

        # Assert
        assert "research_query" in result
        assert result["research_query"] is not None
        # English translation should contain "diabetes" and "type 2"
        english_query = result["research_query"].query_text
        assert "diabetes" in english_query.lower()
        assert "type 2" in english_query.lower() or "type ii" in english_query.lower()


class TestMedicalTermPreservation:
    """Test preservation of Latin medical terms during translation."""

    @pytest.mark.asyncio
    async def test_translate_preserves_medical_terms(self, mock_runtime):
        """Test that Latin medical terms are preserved unchanged.

        Latin terms like 'diabetes mellitus', 'hypertensio' should remain
        unchanged during Czech → English translation.
        """
        # Arrange
        state = State(
            messages=[
                {"role": "user", "content": "Studie o diabetes mellitus a hypertensio"}
            ],
            next="",
            retrieved_docs=[],
        )

        # Act
        result = await translate_cz_to_en_node(state, mock_runtime)

        # Assert
        english_query = result["research_query"].query_text
        assert "diabetes mellitus" in english_query.lower()
        assert "hypertensio" in english_query.lower() or "hypertension" in english_query.lower()


class TestAbbreviationExpansion:
    """Test expansion of Czech medical abbreviations."""

    @pytest.mark.asyncio
    async def test_translate_expands_abbreviations(self, mock_runtime):
        """Test that Czech abbreviations are expanded to full English terms.

        Abbreviations like 'DM2', 'ICHS' should be expanded to
        'type 2 diabetes', 'ischemic heart disease'.
        """
        # Arrange
        state = State(
            messages=[
                {"role": "user", "content": "Léčba DM2 u pacientů s ICHS"}
            ],
            next="",
            retrieved_docs=[],
        )

        # Act
        result = await translate_cz_to_en_node(state, mock_runtime)

        # Assert
        english_query = result["research_query"].query_text
        # DM2 should be expanded
        assert (
            "type 2 diabetes" in english_query.lower()
            or "diabetes type 2" in english_query.lower()
            or "t2dm" in english_query.lower()
        )
        # ICHS should be expanded
        assert (
            "ischemic heart disease" in english_query.lower()
            or "coronary artery disease" in english_query.lower()
            or "ihd" in english_query.lower()
        )


class TestTranslationErrors:
    """Test error handling in translation nodes."""

    @pytest.mark.asyncio
    async def test_translate_empty_messages_error(self, mock_runtime):
        """Test that empty messages are handled gracefully.

        Should raise ValueError or return error message when
        state.messages is empty.
        """
        # Arrange
        state = State(
            messages=[],
            next="",
            retrieved_docs=[],
        )

        # Act & Assert
        with pytest.raises((ValueError, IndexError)):
            await translate_cz_to_en_node(state, mock_runtime)


class TestEnToCzTranslation:
    """Test English → Czech translation for PubMed abstracts."""

    @pytest.mark.asyncio
    async def test_translate_en_to_cz_multiple_docs(self, sample_pubmed_articles, mock_runtime):
        """Test translation of multiple English abstracts to Czech.

        Verifies that all retrieved_docs are translated with Czech abstracts
        while preserving metadata.
        """
        # Arrange
        from langchain_core.documents import Document

        # Create documents with English abstracts
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
            for article in sample_pubmed_articles[:3]  # Use first 3 articles
        ]

        state = State(
            messages=[{"role": "user", "content": "test"}],
            next="",
            retrieved_docs=docs,
        )

        # Act
        result = await translate_en_to_cz_node(state, mock_runtime)

        # Assert
        assert "retrieved_docs" in result
        assert len(result["retrieved_docs"]) == 3
        # Check that page_content now contains Czech abstracts
        for doc in result["retrieved_docs"]:
            assert "Abstract (CZ):" in doc.page_content or "Abstrakt (CZ):" in doc.page_content
            # Metadata should be preserved
            assert doc.metadata["source"] == "PubMed"
            assert "pmid" in doc.metadata


class TestMetadataPreservation:
    """Test that metadata is preserved during translation."""

    @pytest.mark.asyncio
    async def test_translate_preserves_metadata(self, mock_runtime):
        """Test that all metadata fields are preserved during EN→CZ translation.

        Metadata like PMID, URL, authors, journal, DOI must remain unchanged.
        """
        # Arrange
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

        # Act
        result = await translate_en_to_cz_node(state, mock_runtime)

        # Assert
        translated_doc = result["retrieved_docs"][0]
        # All metadata should be preserved
        assert translated_doc.metadata["source"] == "PubMed"
        assert translated_doc.metadata["pmid"] == "12345678"
        assert translated_doc.metadata["url"] == "https://pubmed.ncbi.nlm.nih.gov/12345678/"
        assert translated_doc.metadata["authors"] == "Smith, John"
        assert translated_doc.metadata["journal"] == "NEJM"
        assert translated_doc.metadata["doi"] == "10.1056/test"
        # Original English abstract should be preserved
        assert translated_doc.metadata["abstract_en"] == "Background: Test abstract."
