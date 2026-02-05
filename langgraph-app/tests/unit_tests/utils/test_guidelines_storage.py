"""Unit tests for guidelines storage utilities.

Tests async storage functions for guidelines with pgvector support,
including insert, search, lookup, and error handling.
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
        """Test successful guideline section insertion."""
        # Setup mock
        mock_connection.fetchrow.return_value = {"id": 42}
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        # Execute
        record_id = await store_guideline(
            sample_guideline_with_embedding, pool=mock_pool
        )

        # Verify
        assert record_id == 42
        mock_connection.fetchrow.assert_called_once()

        # Check the SQL query contains expected columns
        call_args = mock_connection.fetchrow.call_args
        query = call_args[0][0]
        assert "INSERT INTO guidelines" in query
        assert "guideline_id" in query
        assert "embedding" in query
        assert "ON CONFLICT" in query

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

        Note: asyncpg decodes JSONB to dict, so metadata should be dict in mocks
        to simulate real database behavior.
        """
        # Setup mock results (metadata as dict, as asyncpg would return)
        mock_rows = [
            {
                "id": 1,
                "guideline_id": "CLS-JEP-2024-001",
                "title": "Hypertenze",
                "section_name": "Léčba",
                "content": "ACE inhibitory...",
                "publication_date": date(2024, 1, 15),
                "source": "cls_jep",
                "url": "https://example.com/1",
                "metadata": {"chunk_index": 1},  # dict, as asyncpg returns
                "similarity_score": 0.95,
            },
            {
                "id": 2,
                "guideline_id": "CLS-JEP-2024-002",
                "title": "Diabetes",
                "section_name": "Úvod",
                "content": "Diabetes mellitus...",
                "publication_date": date(2024, 2, 20),
                "source": "cls_jep",
                "url": "https://example.com/2",
                "metadata": {},  # dict, as asyncpg returns
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

        # Verify
        assert len(results) == 2
        assert results[0]["similarity_score"] == 0.95
        assert results[1]["similarity_score"] == 0.85
        assert results[0]["guideline_id"] == "CLS-JEP-2024-001"
        assert results[0]["metadata"] == {"chunk_index": 1}

    @pytest.mark.asyncio
    async def test_search_with_source_filter(
        self,
        sample_embedding: list[float],
        mock_pool: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test search with source filter is applied."""
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

        # Verify filter was applied in query
        call_args = mock_connection.fetch.call_args
        query = call_args[0][0]
        assert "source = $" in query

        # Check that cls_jep was passed as parameter
        params = call_args[0][1:]
        assert "cls_jep" in params

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
        """Test that search handles string metadata (backward compatibility)."""
        # Some edge cases may return string metadata
        mock_rows = [
            {
                "id": 1,
                "guideline_id": "CLS-JEP-2024-001",
                "title": "Hypertenze",
                "section_name": "Léčba",
                "content": "ACE inhibitory...",
                "publication_date": date(2024, 1, 15),
                "source": "cls_jep",
                "url": "https://example.com/1",
                "metadata": '{"chunk_index": 2}',  # string metadata
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

        # Should handle string metadata without TypeError
        assert len(results) == 1
        assert results[0]["metadata"] == {"chunk_index": 2}


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
        """Test successful lookup by guideline_id and section_name.

        Note: asyncpg decodes JSONB to dict, so metadata should be dict in mocks.
        """
        mock_row = {
            "id": 42,
            "guideline_id": "CLS-JEP-2024-001",
            "title": "Hypertenze",
            "section_name": "Léčba",
            "content": "ACE inhibitory...",
            "publication_date": date(2024, 1, 15),
            "source": "cls_jep",
            "url": "https://example.com/1",
            "metadata": {"chunk_index": 1},  # dict, as asyncpg returns
        }
        mock_connection.fetchrow.return_value = mock_row
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        # Execute
        result = await get_guideline_section(
            guideline_id="CLS-JEP-2024-001",
            section_name="Léčba",
            pool=mock_pool,
        )

        # Verify
        assert result["id"] == 42
        assert result["guideline_id"] == "CLS-JEP-2024-001"
        assert result["section_name"] == "Léčba"
        assert result["publication_date"] == "2024-01-15"
        assert result["metadata"] == {"chunk_index": 1}

    @pytest.mark.asyncio
    async def test_lookup_by_section_id(
        self,
        mock_pool: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test successful lookup by database ID."""
        mock_row = {
            "id": 42,
            "guideline_id": "CLS-JEP-2024-001",
            "title": "Hypertenze",
            "section_name": "Léčba",
            "content": "ACE inhibitory...",
            "publication_date": date(2024, 1, 15),
            "source": "cls_jep",
            "url": "https://example.com/1",
            "metadata": None,
        }
        mock_connection.fetchrow.return_value = mock_row
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        # Execute
        result = await get_guideline_section(
            guideline_id="",  # Ignored
            section_id=42,
            pool=mock_pool,
        )

        # Verify lookup was by ID
        call_args = mock_connection.fetchrow.call_args
        query = call_args[0][0]
        assert "WHERE id = $1" in query
        assert result["id"] == 42
        assert result["metadata"] == {}

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

        with pytest.raises(GuidelineNotFoundError) as exc_info:
            await get_guideline_section(
                guideline_id="CLS-JEP-2024-999",
                section_name="NonExistent",
                pool=mock_pool,
            )

        assert "not found" in str(exc_info.value).lower()
        assert "CLS-JEP-2024-999" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_missing_arguments_raises_error(
        self,
        mock_pool: MagicMock,
    ) -> None:
        """Test that missing section_name and section_id raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            await get_guideline_section(
                guideline_id="CLS-JEP-2024-001",
                pool=mock_pool,
            )

        assert "section_name or section_id" in str(exc_info.value)

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
                section_name="Léčba",
                pool=mock_pool,
            )

        assert "Failed to get" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_handles_string_metadata(
        self,
        mock_pool: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test that get handles string metadata (backward compatibility)."""
        mock_row = {
            "id": 42,
            "guideline_id": "CLS-JEP-2024-001",
            "title": "Hypertenze",
            "section_name": "Léčba",
            "content": "ACE inhibitory...",
            "publication_date": date(2024, 1, 15),
            "source": "cls_jep",
            "url": "https://example.com/1",
            "metadata": '{"chunk_index": 3}',  # string metadata
        }
        mock_connection.fetchrow.return_value = mock_row
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await get_guideline_section(
            guideline_id="CLS-JEP-2024-001",
            section_name="Léčba",
            pool=mock_pool,
        )

        # Should handle string metadata without TypeError
        assert result["metadata"] == {"chunk_index": 3}


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
        """Test successful deletion."""
        mock_connection.execute.return_value = "DELETE 1"
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await delete_guideline_section(
            guideline_id="CLS-JEP-2024-001",
            section_name="Léčba",
            pool=mock_pool,
        )

        assert result is True

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
            section_name="NonExistent",
            pool=mock_pool,
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_by_id(
        self,
        mock_pool: MagicMock,
        mock_connection: MagicMock,
    ) -> None:
        """Test delete by section_id."""
        mock_connection.execute.return_value = "DELETE 1"
        mock_pool.acquire.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await delete_guideline_section(
            guideline_id="",
            section_id=42,
            pool=mock_pool,
        )

        assert result is True
        # Verify SQL used id
        call_args = mock_connection.execute.call_args
        query = call_args[0][0]
        assert "WHERE id = $1" in query
