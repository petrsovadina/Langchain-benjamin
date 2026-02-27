"""Unit tests for guidelines storage utilities.

Tests async storage functions for guidelines with pgvector support,
including insert, search, lookup, and error handling.

These tests target the Supabase schema with the following column mapping:
  - guideline_id  -> external_id
  - section_name  -> organization
  - content       -> full_content
  - source (text) -> source_type (enum, cast with ::source_type)
  - id (int)      -> id (UUID)
  - NEW: publication_year, keywords, icd10_codes

Returned Python dicts use backward-compatible keys so callers are unaffected.
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from agent.models.guideline_models import GuidelineSection, GuidelineSource
from agent.utils.guidelines_storage import (
    DatabaseConfig,
    EmbeddingMissingError,
    GuidelineInsertError,
    GuidelineNotFoundError,
    GuidelineSearchError,
    GuidelinesStorageError,
    delete_guideline_section,
    get_guideline_section,
    search_guidelines,
    store_guideline,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_embedding() -> list[float]:
    """Provide a sample 1536-dimensional embedding vector."""
    return [0.1] * 1536


@pytest.fixture
def sample_guideline_with_embedding(sample_embedding: list[float]) -> GuidelineSection:
    """Provide a sample GuidelineSection with embedding in metadata."""
    return GuidelineSection(
        guideline_id="CLS-JEP-2024-001",
        title="Doporučené postupy pro hypertenzi",
        section_name="Farmakologická léčba",
        content="ACE inhibitory jsou léky první volby u většiny pacientů.",
        publication_date="2024-01-15",
        source=GuidelineSource.CLS_JEP,
        url="https://www.cls.cz/guidelines/hypertenze-2024.pdf",
        metadata={"embedding": sample_embedding, "chunk_index": 1},
    )


@pytest.fixture
def sample_guideline_without_embedding() -> GuidelineSection:
    """Provide a sample GuidelineSection without embedding."""
    return GuidelineSection(
        guideline_id="CLS-JEP-2024-002",
        title="Doporučené postupy pro diabetes",
        section_name="Úvod",
        content="Diabetes mellitus je metabolické onemocnění.",
        publication_date="2024-02-20",
        source=GuidelineSource.CLS_JEP,
        url="https://www.cls.cz/guidelines/diabetes-2024.pdf",
    )


@pytest.fixture
def mock_pool() -> MagicMock:
    """Provide a mock asyncpg connection pool."""
    pool = MagicMock()
    pool.acquire = MagicMock()
    return pool


@pytest.fixture
def mock_connection() -> MagicMock:
    """Provide a mock asyncpg connection."""
    conn = MagicMock()
    conn.fetchrow = AsyncMock()
    conn.fetch = AsyncMock()
    conn.execute = AsyncMock()
    return conn


# =============================================================================
# DatabaseConfig Tests
# =============================================================================


class TestDatabaseConfig:
    """Tests for DatabaseConfig."""

    def test_from_env_with_database_url_sslmode_require(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test config creation from DATABASE_URL with sslmode=require."""
        import ssl as ssl_module

        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql://user:pass@localhost:5432/testdb?sslmode=require",
        )
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)

        config = DatabaseConfig.from_env()

        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "testdb"
        assert config.user == "user"
        assert config.password == "pass"
        # SSL should be an SSLContext for 'require' mode
        assert isinstance(config.ssl, ssl_module.SSLContext)

    def test_from_env_with_database_url_sslmode_prefer(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test config creation from DATABASE_URL with sslmode=prefer."""
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql://user:pass@localhost:5432/testdb?sslmode=prefer",
        )
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)

        config = DatabaseConfig.from_env()

        # SSL should be True for 'prefer' mode
        assert config.ssl is True

    def test_from_env_with_database_url_sslmode_disable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test config creation from DATABASE_URL with sslmode=disable."""
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql://user:pass@localhost:5432/testdb?sslmode=disable",
        )
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)

        config = DatabaseConfig.from_env()

        # SSL should be False for 'disable' mode
        assert config.ssl is False

    def test_from_env_with_database_url_no_sslmode(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test config creation from DATABASE_URL without sslmode defaults to prefer."""
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql://user:pass@localhost:5432/testdb",
        )
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)

        config = DatabaseConfig.from_env()

        # Default should be 'prefer' which maps to True
        assert config.ssl is True

    def test_from_env_with_supabase(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test config creation from Supabase env vars."""
        import ssl as ssl_module

        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("SUPABASE_URL", "https://myproject.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "my-service-role-key")

        config = DatabaseConfig.from_env()

        assert config.host == "db.myproject.supabase.co"
        assert config.port == 5432
        assert config.database == "postgres"
        assert config.user == "postgres"
        assert config.password == "my-service-role-key"
        # Supabase mandates SSL - should be SSLContext
        assert isinstance(config.ssl, ssl_module.SSLContext)

    def test_from_env_missing_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test error when no database config is found."""
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)

        with pytest.raises(ValueError, match="No database configuration found"):
            DatabaseConfig.from_env()


# =============================================================================
# store_guideline Tests
# =============================================================================


class TestStoreGuideline:
    """Tests for store_guideline function."""

    @pytest.mark.asyncio
    async def test_successful_insert(
        self,
        sample_guideline_with_embedding: GuidelineSection,
        mock_pool: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test successful guideline section insertion returns UUID string.

        The Supabase schema uses UUID primary keys. The SQL must:
        - Use external_id instead of guideline_id
        - Use source_type instead of source
        - Include publication_year column
        - Use ON CONFLICT (external_id) for upsert
        """
        # Setup mock — id is now a UUID string, not an integer
        mock_connection.fetchrow.return_value = {
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        }
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        # Execute
        record_id = await store_guideline(
            sample_guideline_with_embedding, pool=mock_pool
        )

        # Return type is now str (UUID), not int
        assert record_id == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        mock_connection.fetchrow.assert_called_once()

        # Check the SQL query contains Supabase column names
        call_args = mock_connection.fetchrow.call_args
        query = call_args[0][0]
        assert "INSERT INTO guidelines" in query
        # New column name: external_id (not guideline_id)
        assert "external_id" in query
        assert "embedding" in query
        assert "ON CONFLICT" in query
        # New columns required by Supabase schema
        assert "publication_year" in query
        assert "source_type" in query

    @pytest.mark.asyncio
    async def test_missing_embedding_raises_error(
        self,
        sample_guideline_without_embedding: GuidelineSection,
        mock_pool: MagicMock,
    ) -> None:
        """Test that missing embedding raises EmbeddingMissingError."""
        with pytest.raises(EmbeddingMissingError) as exc_info:
            await store_guideline(sample_guideline_without_embedding, pool=mock_pool)

        assert "missing embedding" in str(exc_info.value).lower()
        assert sample_guideline_without_embedding.guideline_id in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_embedding_dimensions(
        self,
        sample_guideline_without_embedding: GuidelineSection,
        mock_pool: MagicMock,
    ) -> None:
        """Test that wrong embedding dimensions raises error."""
        sample_guideline_without_embedding.metadata["embedding"] = [
            0.1
        ] * 100  # Wrong dim

        with pytest.raises(EmbeddingMissingError) as exc_info:
            await store_guideline(sample_guideline_without_embedding, pool=mock_pool)

        assert "1536" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_database_error_raises_insert_error(
        self,
        sample_guideline_with_embedding: GuidelineSection,
        mock_pool: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test that database errors are wrapped in GuidelineInsertError."""
        import asyncpg

        # Setup mock to raise PostgresError
        mock_connection.fetchrow.side_effect = asyncpg.PostgresError(
            "Connection failed"
        )
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        with pytest.raises(GuidelineInsertError) as exc_info:
            await store_guideline(sample_guideline_with_embedding, pool=mock_pool)

        assert "Failed to insert" in str(exc_info.value)
        assert sample_guideline_with_embedding.guideline_id in str(exc_info.value)


# =============================================================================
# search_guidelines Tests
# =============================================================================


class TestSearchGuidelines:
    """Tests for search_guidelines function."""

    @pytest.mark.asyncio
    async def test_successful_search_returns_ranked_results(
        self,
        sample_embedding: list[float],
        mock_pool: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test successful search returns results ordered by similarity.

        Mock rows use the new Supabase column names. The returned Python dicts
        use backward-compatible keys (guideline_id, section_name, content, source).
        """
        # Mock rows use new Supabase column names
        mock_rows = [
            {
                "id": "uuid-1",
                "external_id": "CLS-JEP-2024-001",
                "title": "Hypertenze",
                "organization": "ČLS JEP",
                "full_content": "ACE inhibitory...",
                "publication_date": date(2024, 1, 15),
                "source_type": "guidelines",
                "url": "https://example.com/1",
                "keywords": None,
                "icd10_codes": None,
                "similarity_score": 0.95,
            },
            {
                "id": "uuid-2",
                "external_id": "CLS-JEP-2024-002",
                "title": "Diabetes",
                "organization": "ČLS JEP",
                "full_content": "Diabetes mellitus...",
                "publication_date": date(2024, 2, 20),
                "source_type": "guidelines",
                "url": "https://example.com/2",
                "keywords": None,
                "icd10_codes": None,
                "similarity_score": 0.85,
            },
        ]
        mock_connection.fetch.return_value = mock_rows
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        # Execute
        results = await search_guidelines(
            query=sample_embedding, limit=5, pool=mock_pool
        )

        # Verify ranking
        assert len(results) == 2
        assert results[0]["similarity_score"] == 0.95
        assert results[1]["similarity_score"] == 0.85

        # Returned dicts must use backward-compatible keys
        assert results[0]["guideline_id"] == "CLS-JEP-2024-001"
        assert results[0]["section_name"] == "ČLS JEP"
        assert results[0]["content"] == "ACE inhibitory..."

    @pytest.mark.asyncio
    async def test_search_with_source_filter(
        self,
        sample_embedding: list[float],
        mock_pool: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test that source filter uses source_type column with ::source_type cast.

        In the Supabase schema, all guideline sources map to source_type='guidelines',
        so the param value is 'guidelines', not the enum value 'cls_jep'.
        """
        mock_connection.fetch.return_value = []
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        # Execute with source filter
        await search_guidelines(
            query=sample_embedding,
            limit=10,
            source_filter=GuidelineSource.CLS_JEP,
            pool=mock_pool,
        )

        # Verify filter uses new column name with enum cast
        call_args = mock_connection.fetch.call_args
        query = call_args[0][0]
        assert "source_type = $" in query

        # The param value should be "guidelines" (not "cls_jep")
        params = call_args[0][1:]
        assert "guidelines" in params

    @pytest.mark.asyncio
    async def test_search_with_date_filters(
        self,
        sample_embedding: list[float],
        mock_pool: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test search with publication date filters."""
        mock_connection.fetch.return_value = []
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        # Execute with date filters
        await search_guidelines(
            query=sample_embedding,
            limit=10,
            publication_date_from="2024-01-01",
            publication_date_to="2024-12-31",
            pool=mock_pool,
        )

        # Verify filters were applied
        call_args = mock_connection.fetch.call_args
        query = call_args[0][0]
        assert "publication_date >=" in query
        assert "publication_date <=" in query

    @pytest.mark.asyncio
    async def test_search_invalid_query_type_raises_error(
        self,
        mock_pool: MagicMock,
    ) -> None:
        """Test that string query raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            await search_guidelines(query="hypertenze", limit=5, pool=mock_pool)

        assert "pre-computed embedding" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_invalid_embedding_dimensions(
        self,
        mock_pool: MagicMock,
    ) -> None:
        """Test that wrong embedding dimensions raises error."""
        with pytest.raises(ValueError) as exc_info:
            await search_guidelines(query=[0.1] * 100, limit=5, pool=mock_pool)

        assert "1536" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_invalid_limit(
        self,
        sample_embedding: list[float],
        mock_pool: MagicMock,
    ) -> None:
        """Test that invalid limit raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            await search_guidelines(query=sample_embedding, limit=0, pool=mock_pool)
        assert "between 1 and 100" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            await search_guidelines(query=sample_embedding, limit=101, pool=mock_pool)
        assert "between 1 and 100" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_database_error(
        self,
        sample_embedding: list[float],
        mock_pool: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test that database errors are wrapped in GuidelineSearchError."""
        import asyncpg

        mock_connection.fetch.side_effect = asyncpg.PostgresError("Query failed")
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        with pytest.raises(GuidelineSearchError) as exc_info:
            await search_guidelines(query=sample_embedding, limit=5, pool=mock_pool)

        assert "Failed to search" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_handles_string_metadata(
        self,
        sample_embedding: list[float],
        mock_pool: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test that search reconstructs metadata from keywords and icd10_codes columns.

        Supabase schema has no metadata column. The metadata dict is reconstructed
        from the keywords (text[]) and icd10_codes (text[]) columns.
        """
        mock_rows = [
            {
                "id": "uuid-1",
                "external_id": "CLS-JEP-2024-001",
                "title": "Hypertenze",
                "organization": "ČLS JEP",
                "full_content": "ACE inhibitory...",
                "publication_date": date(2024, 1, 15),
                "source_type": "guidelines",
                "url": "https://example.com/1",
                "keywords": ["hypertenze"],
                "icd10_codes": None,
                "similarity_score": 0.90,
            },
        ]
        mock_connection.fetch.return_value = mock_rows
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        results = await search_guidelines(
            query=sample_embedding, limit=5, pool=mock_pool
        )

        # Should reconstruct metadata from keywords/icd10_codes without error
        assert len(results) == 1
        assert results[0]["metadata"] == {"keywords": ["hypertenze"]}

    @pytest.mark.asyncio
    async def test_search_handles_null_full_content(
        self,
        sample_embedding: list[float],
        mock_pool: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test that NULL full_content is mapped to empty string in results.

        The Supabase full_content column can be NULL. The backward-compatible
        'content' key must be an empty string (not None) when full_content is NULL.
        """
        mock_rows = [
            {
                "id": "uuid-null-content",
                "external_id": "CLS-JEP-2024-003",
                "title": "Bez obsahu",
                "organization": "ČLS JEP",
                "full_content": None,  # NULL in Supabase
                "publication_date": date(2024, 3, 1),
                "source_type": "guidelines",
                "url": "https://example.com/3",
                "keywords": None,
                "icd10_codes": None,
                "similarity_score": 0.70,
            },
        ]
        mock_connection.fetch.return_value = mock_rows
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        results = await search_guidelines(
            query=sample_embedding, limit=5, pool=mock_pool
        )

        assert len(results) == 1
        # NULL full_content must map to empty string, not None
        assert results[0]["content"] == ""


# =============================================================================
# get_guideline_section Tests
# =============================================================================


class TestGetGuidelineSection:
    """Tests for get_guideline_section function."""

    @pytest.mark.asyncio
    async def test_lookup_by_guideline_id_and_section_name(
        self,
        mock_pool: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test successful lookup by guideline_id alone (external_id is unique).

        In the Supabase schema, external_id is unique so section_name is no
        longer needed for lookup. The WHERE clause should be:
            WHERE external_id = $1
        Returned dict uses backward-compatible keys.
        """
        mock_row = {
            "id": "uuid-42",
            "external_id": "CLS-JEP-2024-001",
            "title": "Hypertenze",
            "organization": "ČLS JEP",
            "full_content": "ACE inhibitory...",
            "publication_date": date(2024, 1, 15),
            "source_type": "guidelines",
            "url": "https://example.com/1",
            "keywords": None,
            "icd10_codes": None,
        }
        mock_connection.fetchrow.return_value = mock_row
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        # Can look up with guideline_id alone — no section_name required
        result = await get_guideline_section(
            guideline_id="CLS-JEP-2024-001",
            pool=mock_pool,
        )

        # Verify SQL uses external_id column
        call_args = mock_connection.fetchrow.call_args
        query = call_args[0][0]
        assert "WHERE external_id = $1" in query

        # Verify backward-compatible keys in result
        assert result["id"] == "uuid-42"
        assert result["guideline_id"] == "CLS-JEP-2024-001"
        assert result["section_name"] == "ČLS JEP"
        assert result["content"] == "ACE inhibitory..."
        assert result["publication_date"] == "2024-01-15"

    @pytest.mark.asyncio
    async def test_lookup_by_section_id(
        self,
        mock_pool: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test successful lookup by UUID section_id."""
        mock_row = {
            "id": "uuid-42",
            "external_id": "CLS-JEP-2024-001",
            "title": "Hypertenze",
            "organization": "ČLS JEP",
            "full_content": "ACE inhibitory...",
            "publication_date": date(2024, 1, 15),
            "source_type": "guidelines",
            "url": "https://example.com/1",
            "keywords": None,
            "icd10_codes": None,
        }
        mock_connection.fetchrow.return_value = mock_row
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        # section_id is now a UUID string, not an integer
        result = await get_guideline_section(
            guideline_id="",
            section_id="uuid-42",
            pool=mock_pool,
        )

        # Verify lookup was by UUID id
        call_args = mock_connection.fetchrow.call_args
        query = call_args[0][0]
        assert "WHERE id = $1" in query
        assert result["id"] == "uuid-42"

    @pytest.mark.asyncio
    async def test_not_found_raises_error(
        self,
        mock_pool: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test that not found raises GuidelineNotFoundError."""
        mock_connection.fetchrow.return_value = None
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        # Lookup by guideline_id alone is now valid (no section_name required)
        with pytest.raises(GuidelineNotFoundError) as exc_info:
            await get_guideline_section(
                guideline_id="CLS-JEP-2024-999",
                pool=mock_pool,
            )

        assert "not found" in str(exc_info.value).lower()
        assert "CLS-JEP-2024-999" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_missing_arguments_raises_error(
        self,
        mock_pool: MagicMock,
    ) -> None:
        """Test that empty guideline_id without section_id raises ValueError.

        With Supabase, lookup by guideline_id alone is valid (external_id is
        unique). A ValueError must only be raised when guideline_id is empty
        (or falsy) AND section_id is None — i.e., there is truly no identifier.
        """
        with pytest.raises(ValueError) as exc_info:
            await get_guideline_section(
                guideline_id="",  # Empty — no usable identifier
                section_id=None,
                pool=mock_pool,
            )

        # Error message should indicate that some identifier is required
        assert "guideline_id" in str(exc_info.value) or "section_id" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_database_error(
        self,
        mock_pool: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test that database errors are wrapped."""
        import asyncpg

        mock_connection.fetchrow.side_effect = asyncpg.PostgresError("Connection lost")
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        with pytest.raises(GuidelinesStorageError) as exc_info:
            await get_guideline_section(
                guideline_id="CLS-JEP-2024-001",
                pool=mock_pool,
            )

        assert "Failed to get" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_handles_string_metadata(
        self,
        mock_pool: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test that get reconstructs metadata from keywords and icd10_codes columns.

        Supabase schema has no metadata column. keywords/icd10_codes are separate
        text[] columns that are reconstructed into a metadata dict in Python.
        """
        mock_row = {
            "id": "uuid-42",
            "external_id": "CLS-JEP-2024-001",
            "title": "Hypertenze",
            "organization": "ČLS JEP",
            "full_content": "ACE inhibitory...",
            "publication_date": date(2024, 1, 15),
            "source_type": "guidelines",
            "url": "https://example.com/1",
            "keywords": ["hypertenze", "ACE"],
            "icd10_codes": ["I10"],
        }
        mock_connection.fetchrow.return_value = mock_row
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await get_guideline_section(
            guideline_id="CLS-JEP-2024-001",
            pool=mock_pool,
        )

        # Metadata reconstructed from keywords and icd10_codes
        assert result["metadata"] == {
            "keywords": ["hypertenze", "ACE"],
            "icd10_codes": ["I10"],
        }


# =============================================================================
# delete_guideline_section Tests
# =============================================================================


class TestDeleteGuidelineSection:
    """Tests for delete_guideline_section function."""

    @pytest.mark.asyncio
    async def test_successful_delete(
        self,
        mock_pool: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test successful deletion using external_id column.

        In the Supabase schema, external_id is unique, so deletion by
        guideline_id alone (no section_name needed) targets the correct row.
        The SQL should be: DELETE FROM guidelines WHERE external_id = $1
        """
        mock_connection.execute.return_value = "DELETE 1"
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        # No section_name required — external_id is unique
        result = await delete_guideline_section(
            guideline_id="CLS-JEP-2024-001",
            pool=mock_pool,
        )

        assert result is True

        # Verify the SQL targets external_id, not (guideline_id, section_name)
        call_args = mock_connection.execute.call_args
        query = call_args[0][0]
        assert "WHERE external_id = $1" in query

    @pytest.mark.asyncio
    async def test_delete_not_found(
        self,
        mock_pool: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test delete returns False when not found."""
        mock_connection.execute.return_value = "DELETE 0"
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await delete_guideline_section(
            guideline_id="CLS-JEP-2024-999",
            pool=mock_pool,
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_by_id(
        self,
        mock_pool: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test delete by UUID section_id."""
        mock_connection.execute.return_value = "DELETE 1"
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        # section_id is now a UUID string, not an integer
        result = await delete_guideline_section(
            guideline_id="",
            section_id="uuid-42",
            pool=mock_pool,
        )

        assert result is True
        # Verify SQL used id
        call_args = mock_connection.execute.call_args
        query = call_args[0][0]
        assert "WHERE id = $1" in query
