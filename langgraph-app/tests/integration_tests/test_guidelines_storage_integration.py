"""Integration tests for guidelines storage with real database."""

import os

import pytest

from agent.models.guideline_models import GuidelineSection, GuidelineSource
from agent.utils.guidelines_storage import (
    close_pool,
    delete_guideline_section,
    get_guideline_section,
    search_guidelines,
    store_guideline,
)

# Skip if no database configured
pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL") and not os.environ.get("SUPABASE_URL"),
    reason="No database configured",
)


@pytest.fixture(scope="module")
async def cleanup():
    """Cleanup connection pool after tests."""
    yield
    await close_pool()


@pytest.fixture
async def test_guideline_section():
    """Create and cleanup a test guideline section."""
    # Create sample guideline with embedding
    section = GuidelineSection(
        guideline_id="TEST-2024-001",
        title="Test Guideline",
        section_name="Test Section",
        content="This is a test guideline section for integration testing.",
        publication_date="2024-01-15",
        source=GuidelineSource.CLS_JEP,
        url="https://example.com/test",
        metadata={"embedding": [0.1] * 1536},  # Sample embedding
    )

    yield section

    # Cleanup: delete the test section after test
    try:
        await delete_guideline_section(
            guideline_id="TEST-2024-001", section_name="Test Section"
        )
    except Exception:
        pass  # Ignore errors during cleanup


@pytest.mark.asyncio
async def test_store_guideline(cleanup, test_guideline_section):
    """Test storing a guideline section."""
    record_id = await store_guideline(test_guideline_section)
    assert record_id > 0


@pytest.mark.asyncio
async def test_store_and_retrieve_guideline(cleanup, test_guideline_section):
    """Test storing and retrieving a guideline section."""
    # Store guideline
    record_id = await store_guideline(test_guideline_section)
    assert record_id > 0

    # Get specific section
    retrieved = await get_guideline_section(
        guideline_id="TEST-2024-001", section_name="Test Section"
    )
    assert retrieved["title"] == "Test Guideline"
    assert (
        retrieved["content"]
        == "This is a test guideline section for integration testing."
    )
    assert retrieved["source"] == "cls_jep"


@pytest.mark.asyncio
async def test_store_and_search_guideline(cleanup, test_guideline_section):
    """Test storing and searching a guideline section."""
    # Store guideline
    await store_guideline(test_guideline_section)

    # Search by embedding
    results = await search_guidelines(
        query=[0.1] * 1536, limit=5, source_filter=GuidelineSource.CLS_JEP
    )
    assert len(results) > 0
    assert any(r["guideline_id"] == "TEST-2024-001" for r in results)


@pytest.mark.asyncio
async def test_delete_guideline_section(cleanup, test_guideline_section):
    """Test deleting a guideline section."""
    # Store guideline
    await store_guideline(test_guideline_section)

    # Delete
    deleted = await delete_guideline_section(
        guideline_id="TEST-2024-001", section_name="Test Section"
    )
    assert deleted is True

    # Verify deletion
    with pytest.raises(Exception):  # Should raise GuidelineNotFoundError
        await get_guideline_section(
            guideline_id="TEST-2024-001", section_name="Test Section"
        )
