"""Unit tests for Guideline models (Feature 006).

Tests for:
- GuidelineQueryType enum
- GuidelineSource enum
- GuidelineQuery model (creation, whitespace trimming, limit bounds)
- GuidelineSection model (guideline_id format, publication_date validation, guideline_url)
- GuidelineDocument model (metadata defaults)
"""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from agent.models.guideline_models import (
    GuidelineDocument,
    GuidelineQuery,
    GuidelineQueryType,
    GuidelineSection,
    GuidelineSource,
)


class TestGuidelineQueryType:
    """Test GuidelineQueryType enum."""

    def test_search_value(self):
        """Test SEARCH enum value."""
        assert GuidelineQueryType.SEARCH == "search"
        assert GuidelineQueryType.SEARCH.value == "search"

    def test_section_lookup_value(self):
        """Test SECTION_LOOKUP enum value."""
        assert GuidelineQueryType.SECTION_LOOKUP == "section_lookup"
        assert GuidelineQueryType.SECTION_LOOKUP.value == "section_lookup"

    def test_enum_from_string(self):
        """Test creating enum from string value."""
        assert GuidelineQueryType("search") == GuidelineQueryType.SEARCH
        assert GuidelineQueryType("section_lookup") == GuidelineQueryType.SECTION_LOOKUP


class TestGuidelineSource:
    """Test GuidelineSource enum."""

    def test_cls_jep_value(self):
        """Test CLS_JEP enum value."""
        assert GuidelineSource.CLS_JEP == "cls_jep"
        assert GuidelineSource.CLS_JEP.value == "cls_jep"

    def test_esc_value(self):
        """Test ESC enum value."""
        assert GuidelineSource.ESC == "esc"
        assert GuidelineSource.ESC.value == "esc"

    def test_ers_value(self):
        """Test ERS enum value."""
        assert GuidelineSource.ERS == "ers"
        assert GuidelineSource.ERS.value == "ers"

    def test_enum_from_string(self):
        """Test creating enum from string value."""
        assert GuidelineSource("cls_jep") == GuidelineSource.CLS_JEP
        assert GuidelineSource("esc") == GuidelineSource.ESC
        assert GuidelineSource("ers") == GuidelineSource.ERS


class TestGuidelineQuery:
    """Test GuidelineQuery model."""

    def test_valid_query_creation(self):
        """Test creating valid GuidelineQuery."""
        query = GuidelineQuery(
            query_text="léčba hypertenze",
            query_type=GuidelineQueryType.SEARCH,
            limit=10,
        )

        assert query.query_text == "léčba hypertenze"
        assert query.query_type == GuidelineQueryType.SEARCH
        assert query.limit == 10
        assert query.specialty_filter is None

    def test_query_with_specialty_filter(self):
        """Test GuidelineQuery with specialty filter."""
        query = GuidelineQuery(
            query_text="diabetes",
            specialty_filter="cardiology",
        )

        assert query.query_text == "diabetes"
        assert query.specialty_filter == "cardiology"

    def test_query_text_whitespace_trimming(self):
        """Test that query_text is trimmed of leading/trailing whitespace."""
        query = GuidelineQuery(query_text="  léčba hypertenze  ")

        assert query.query_text == "léčba hypertenze"

    def test_query_text_empty_raises_error(self):
        """Test that empty query_text raises ValidationError."""
        with pytest.raises(ValidationError):
            GuidelineQuery(query_text="")

    def test_query_text_whitespace_only_raises_error(self):
        """Test that whitespace-only query_text raises ValidationError."""
        with pytest.raises(ValidationError):
            GuidelineQuery(query_text="   ")

    def test_default_query_type(self):
        """Test default query_type is SEARCH."""
        query = GuidelineQuery(query_text="test")

        assert query.query_type == GuidelineQueryType.SEARCH

    def test_default_limit(self):
        """Test default limit is 10."""
        query = GuidelineQuery(query_text="test")

        assert query.limit == 10

    def test_limit_minimum_bound(self):
        """Test limit minimum bound is 1."""
        query = GuidelineQuery(query_text="test", limit=1)
        assert query.limit == 1

        with pytest.raises(ValidationError):
            GuidelineQuery(query_text="test", limit=0)

    def test_limit_maximum_bound(self):
        """Test limit maximum bound is 50."""
        query = GuidelineQuery(query_text="test", limit=50)
        assert query.limit == 50

        with pytest.raises(ValidationError):
            GuidelineQuery(query_text="test", limit=51)

    def test_section_lookup_query_type(self):
        """Test SECTION_LOOKUP query type."""
        query = GuidelineQuery(
            query_text="CLS-JEP-2024-001",
            query_type=GuidelineQueryType.SECTION_LOOKUP,
        )

        assert query.query_type == GuidelineQueryType.SECTION_LOOKUP


class TestGuidelineSection:
    """Test GuidelineSection model."""

    def test_valid_section_creation_cls_jep(self):
        """Test creating valid GuidelineSection with CLS-JEP source."""
        section = GuidelineSection(
            guideline_id="CLS-JEP-2024-001",
            title="Doporučené postupy pro hypertenzi",
            section_name="Léčba hypertenze 1. stupně",
            content="U pacientů s hypertenzí 1. stupně je doporučeno...",
            publication_date="2024-01-15",
            source=GuidelineSource.CLS_JEP,
            url="https://www.cls.cz/guidelines/hypertenze-2024.pdf",
        )

        assert section.guideline_id == "CLS-JEP-2024-001"
        assert section.source == GuidelineSource.CLS_JEP
        assert section.title == "Doporučené postupy pro hypertenzi"
        assert section.publication_date == "2024-01-15"

    def test_valid_section_creation_esc(self):
        """Test creating valid GuidelineSection with ESC source."""
        section = GuidelineSection(
            guideline_id="ESC-2023-042",
            title="ESC Guidelines on Heart Failure",
            section_name="Treatment of HFrEF",
            content="In patients with HFrEF, guideline-directed medical therapy...",
            publication_date="2023-08-25",
            source=GuidelineSource.ESC,
            url="https://www.escardio.org/guidelines/hf-2023.pdf",
        )

        assert section.guideline_id == "ESC-2023-042"
        assert section.source == GuidelineSource.ESC

    def test_valid_section_creation_ers(self):
        """Test creating valid GuidelineSection with ERS source."""
        section = GuidelineSection(
            guideline_id="ERS-2025-003",
            title="ERS Guidelines on COPD",
            section_name="Pharmacological Treatment",
            content="For stable COPD patients, long-acting bronchodilators...",
            publication_date="2025-02-01",
            source=GuidelineSource.ERS,
            url="https://www.ersnet.org/guidelines/copd-2025.pdf",
        )

        assert section.guideline_id == "ERS-2025-003"
        assert section.source == GuidelineSource.ERS

    def test_guideline_id_cls_jep_format_valid(self):
        """Test valid CLS-JEP guideline ID format."""
        section = GuidelineSection(
            guideline_id="CLS-JEP-2024-001",
            title="Test",
            section_name="Section",
            content="Content",
            publication_date="2024-01-01",
            source=GuidelineSource.CLS_JEP,
            url="https://example.com",
        )
        assert section.guideline_id == "CLS-JEP-2024-001"

    def test_guideline_id_invalid_format_raises_error(self):
        """Test invalid guideline ID format raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid guideline ID format"):
            GuidelineSection(
                guideline_id="INVALID-123",
                title="Test",
                section_name="Section",
                content="Content",
                publication_date="2024-01-01",
                source=GuidelineSource.CLS_JEP,
                url="https://example.com",
            )

    def test_guideline_id_missing_number_raises_error(self):
        """Test guideline ID without proper number format raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid guideline ID format"):
            GuidelineSection(
                guideline_id="CLS-JEP-2024",
                title="Test",
                section_name="Section",
                content="Content",
                publication_date="2024-01-01",
                source=GuidelineSource.CLS_JEP,
                url="https://example.com",
            )

    def test_guideline_id_wrong_prefix_raises_error(self):
        """Test guideline ID with wrong prefix raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid guideline ID format"):
            GuidelineSection(
                guideline_id="WHO-2024-001",
                title="Test",
                section_name="Section",
                content="Content",
                publication_date="2024-01-01",
                source=GuidelineSource.CLS_JEP,
                url="https://example.com",
            )

    def test_publication_date_valid_format(self):
        """Test valid publication date format YYYY-MM-DD."""
        section = GuidelineSection(
            guideline_id="CLS-JEP-2024-001",
            title="Test",
            section_name="Section",
            content="Content",
            publication_date="2024-06-15",
            source=GuidelineSource.CLS_JEP,
            url="https://example.com",
        )
        assert section.publication_date == "2024-06-15"

    def test_publication_date_invalid_format_raises_error(self):
        """Test invalid publication date format raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid publication date format"):
            GuidelineSection(
                guideline_id="CLS-JEP-2024-001",
                title="Test",
                section_name="Section",
                content="Content",
                publication_date="15-06-2024",
                source=GuidelineSource.CLS_JEP,
                url="https://example.com",
            )

    def test_publication_date_invalid_date_raises_error(self):
        """Test invalid date (e.g., Feb 30) raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid date"):
            GuidelineSection(
                guideline_id="CLS-JEP-2024-001",
                title="Test",
                section_name="Section",
                content="Content",
                publication_date="2024-02-30",
                source=GuidelineSource.CLS_JEP,
                url="https://example.com",
            )

    def test_publication_date_invalid_month_raises_error(self):
        """Test invalid month (13) raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid date"):
            GuidelineSection(
                guideline_id="CLS-JEP-2024-001",
                title="Test",
                section_name="Section",
                content="Content",
                publication_date="2024-13-01",
                source=GuidelineSource.CLS_JEP,
                url="https://example.com",
            )

    def test_guideline_url_cls_jep(self):
        """Test guideline_url computed field for CLS-JEP source."""
        section = GuidelineSection(
            guideline_id="CLS-JEP-2024-001",
            title="Test",
            section_name="Section",
            content="Content",
            publication_date="2024-01-01",
            source=GuidelineSource.CLS_JEP,
            url="https://example.com",
        )
        assert section.guideline_url == "https://www.cls.cz/guidelines/CLS-JEP-2024-001"

    def test_guideline_url_esc(self):
        """Test guideline_url computed field for ESC source."""
        section = GuidelineSection(
            guideline_id="ESC-2023-042",
            title="Test",
            section_name="Section",
            content="Content",
            publication_date="2023-01-01",
            source=GuidelineSource.ESC,
            url="https://example.com",
        )
        assert section.guideline_url == "https://www.escardio.org/Guidelines/ESC-2023-042"

    def test_guideline_url_ers(self):
        """Test guideline_url computed field for ERS source."""
        section = GuidelineSection(
            guideline_id="ERS-2025-003",
            title="Test",
            section_name="Section",
            content="Content",
            publication_date="2025-01-01",
            source=GuidelineSource.ERS,
            url="https://example.com",
        )
        assert section.guideline_url == "https://www.ersnet.org/guidelines/ERS-2025-003"


class TestGuidelineDocument:
    """Test GuidelineDocument model."""

    def test_valid_document_creation(self):
        """Test creating valid GuidelineDocument."""
        doc = GuidelineDocument(
            page_content="## Léčba hypertenze\n\nU pacientů s hypertenzí..."
        )

        assert doc.page_content == "## Léčba hypertenze\n\nU pacientů s hypertenzí..."
        assert "source" in doc.metadata
        assert "source_type" in doc.metadata
        assert "retrieved_at" in doc.metadata

    def test_document_default_metadata_source(self):
        """Test default metadata source is 'guidelines'."""
        doc = GuidelineDocument(page_content="Test content")

        assert doc.metadata["source"] == "guidelines"

    def test_document_default_metadata_source_type(self):
        """Test default metadata source_type is 'clinical_guidelines'."""
        doc = GuidelineDocument(page_content="Test content")

        assert doc.metadata["source_type"] == "clinical_guidelines"

    def test_document_default_metadata_retrieved_at(self):
        """Test default metadata retrieved_at is ISO format timestamp."""
        before = datetime.now().isoformat()
        doc = GuidelineDocument(page_content="Test content")
        after = datetime.now().isoformat()

        # Verify retrieved_at is between before and after
        assert doc.metadata["retrieved_at"] >= before
        assert doc.metadata["retrieved_at"] <= after

    def test_document_custom_metadata(self):
        """Test GuidelineDocument with custom metadata."""
        custom_metadata = {
            "source": "custom_source",
            "source_type": "custom_type",
            "guideline_id": "CLS-JEP-2024-001",
        }
        doc = GuidelineDocument(page_content="Test", metadata=custom_metadata)

        assert doc.metadata["source"] == "custom_source"
        assert doc.metadata["source_type"] == "custom_type"
        assert doc.metadata["guideline_id"] == "CLS-JEP-2024-001"

    def test_document_allows_empty_content(self):
        """Test that empty page_content is allowed (no min_length constraint)."""
        doc = GuidelineDocument(page_content="")
        assert doc.page_content == ""
