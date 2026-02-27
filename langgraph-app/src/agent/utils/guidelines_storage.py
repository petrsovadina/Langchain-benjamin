"""Async storage utilities for guidelines with pgvector support.

This module provides async functions for storing and retrieving clinical
guideline sections with vector embeddings for semantic search.

Requires:
    - PostgreSQL 15+ with pgvector extension
    - asyncpg for async database access
    - Environment variables: SUPABASE_URL or DATABASE_URL, SUPABASE_KEY (optional)

Example:
    >>> from agent.utils.guidelines_storage import (
    ...     store_guideline,
    ...     search_guidelines,
    ...     get_guideline_section,
    ... )
    >>> # Store a guideline section
    >>> section = GuidelineSection(...)
    >>> section.metadata["embedding"] = [0.1, 0.2, ...]
    >>> await store_guideline(section)
    >>>
    >>> # Search guidelines by query vector
    >>> results = await search_guidelines(
    ...     query=[0.1, 0.2, ...],
    ...     limit=5,
    ...     source_filter="cls_jep"
    ... )
"""

from __future__ import annotations

import logging
import os
import ssl
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Sequence
from urllib.parse import parse_qs, urlparse

import asyncpg

from agent.models.guideline_models import GuidelineSection, GuidelineSource

logger = logging.getLogger(__name__)

# Embedding dimension for text-embedding-ada-002 model.
# Change this if switching to a different embedding model.
EMBEDDING_DIMENSIONS = 1536

# Mapping from GuidelineSource to organization display name
SOURCE_TO_ORG: dict[GuidelineSource, str] = {
    GuidelineSource.CLS_JEP: "ČLS JEP",
    GuidelineSource.ESC: "ESC",
    GuidelineSource.ERS: "ERS",
}

# Reverse mapping from organization to GuidelineSource
ORG_TO_SOURCE: dict[str, GuidelineSource] = {
    "ČLS JEP": GuidelineSource.CLS_JEP,
    "ESC": GuidelineSource.ESC,
    "ERS": GuidelineSource.ERS,
}


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class DatabaseConfig:
    """Database connection configuration.

    Attributes:
        host: Database host.
        port: Database port.
        database: Database name.
        user: Database user.
        password: Database password.
        ssl: SSL configuration for connection. Can be:
            - ssl.SSLContext: Full SSL context for secure connections
            - True: Enable SSL with default settings
            - False/None: Disable SSL
    """

    host: str
    port: int
    database: str
    user: str
    password: str
    ssl: ssl.SSLContext | bool | None = None

    @classmethod
    def from_env(cls) -> DatabaseConfig:
        """Create config from environment variables.

        Supports both Supabase-style and standard PostgreSQL connection strings.

        Environment Variables:
            DATABASE_URL: Full connection string (postgresql://user:pass@host:port/db)
            SUPABASE_URL: Supabase project URL (extracts host from URL)
            SUPABASE_KEY: Supabase service role key (used as password)

        Returns:
            DatabaseConfig instance.

        Raises:
            ValueError: If no database configuration is found.

        Note:
            SSL is configured based on sslmode in DATABASE_URL query string:
            - 'require', 'verify-ca', 'verify-full': Creates ssl.SSLContext
            - 'prefer': Uses ssl=True (enables with default settings)
            - 'disable', 'allow': Uses ssl=False
            Supabase always uses ssl.SSLContext as it mandates SSL.
        """
        # Option 1: Standard DATABASE_URL
        database_url = os.environ.get("DATABASE_URL")
        if database_url:
            parsed = urlparse(database_url)

            # Parse sslmode from query string
            query_params = parse_qs(parsed.query)
            sslmode = query_params.get("sslmode", ["prefer"])[0]

            # Convert sslmode string to valid asyncpg ssl parameter
            ssl_config: ssl.SSLContext | bool | None
            if sslmode in ("require", "verify-ca", "verify-full"):
                ssl_config = ssl.create_default_context()
            elif sslmode == "prefer":
                ssl_config = True
            else:  # 'disable', 'allow', or unknown
                ssl_config = False

            return cls(
                host=parsed.hostname or "localhost",
                port=parsed.port or 5432,
                database=parsed.path.lstrip("/") or "postgres",
                user=parsed.username or "postgres",
                password=parsed.password or "",
                ssl=ssl_config,
            )

        # Option 2: Supabase configuration
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        if supabase_url and supabase_key:
            # Extract host from Supabase URL (https://xxx.supabase.co -> xxx.supabase.co)
            parsed = urlparse(supabase_url)
            host = parsed.hostname or ""
            # Convert to database host (db.xxx.supabase.co)
            if host.endswith(".supabase.co"):
                db_host = f"db.{host}"
            else:
                db_host = host

            # Supabase mandates SSL
            return cls(
                host=db_host,
                port=5432,
                database="postgres",
                user="postgres",
                password=supabase_key,
                ssl=ssl.create_default_context(),
            )

        raise ValueError(
            "No database configuration found. Set DATABASE_URL or "
            "SUPABASE_URL + SUPABASE_KEY environment variables."
        )


# =============================================================================
# Exceptions
# =============================================================================


class GuidelinesStorageError(Exception):
    """Base exception for guidelines storage operations."""


class GuidelineNotFoundError(GuidelinesStorageError):
    """Raised when a guideline section is not found."""


class GuidelineInsertError(GuidelinesStorageError):
    """Raised when a guideline section cannot be inserted."""


class GuidelineSearchError(GuidelinesStorageError):
    """Raised when a guideline search fails."""


class EmbeddingMissingError(GuidelinesStorageError):
    """Raised when a guideline section is missing embedding."""


# =============================================================================
# Connection Pool
# =============================================================================

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Get or create the connection pool.

    Returns:
        asyncpg.Pool: Database connection pool.

    Raises:
        GuidelinesStorageError: If connection fails.
    """
    global _pool
    if _pool is None:
        try:
            config = DatabaseConfig.from_env()
            _pool = await asyncpg.create_pool(
                host=config.host,
                port=config.port,
                database=config.database,
                user=config.user,
                password=config.password,
                ssl=config.ssl,
                min_size=2,
                max_size=10,
                command_timeout=30,
            )
            logger.info("Database connection pool created")
        except Exception as e:
            raise GuidelinesStorageError(
                f"Failed to create connection pool: {e}"
            ) from e
    return _pool


async def close_pool() -> None:
    """Close the connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Database connection pool closed")


# =============================================================================
# Storage Operations
# =============================================================================


async def store_guideline(
    guideline_section: GuidelineSection,
    *,
    pool: asyncpg.Pool | None = None,
) -> str:
    """Store a guideline section with embedding in the database.

    Args:
        guideline_section: GuidelineSection with embedding in metadata.
        pool: Optional connection pool (uses global pool if not provided).

    Returns:
        str: UUID of the inserted/updated record.

    Raises:
        EmbeddingMissingError: If guideline_section.metadata["embedding"] is missing.
        GuidelineInsertError: If insertion fails.

    Example:
        >>> section = GuidelineSection(
        ...     guideline_id="CLS-JEP-2024-001",
        ...     title="Hypertenze",
        ...     section_name="Léčba",
        ...     content="ACE inhibitory jsou...",
        ...     publication_date="2024-01-15",
        ...     source=GuidelineSource.CLS_JEP,
        ...     url="https://www.cls.cz/guidelines/hypertenze-2024.pdf",
        ...     metadata={"embedding": [0.1, 0.2, ...]}
        ... )
        >>> record_id = await store_guideline(section)
    """
    # Validate embedding exists
    embedding = guideline_section.metadata.get("embedding")
    if embedding is None:
        raise EmbeddingMissingError(
            f"Guideline section {guideline_section.guideline_id}/{guideline_section.section_name} "
            "is missing embedding in metadata"
        )

    # Validate embedding dimensions
    if (
        not isinstance(embedding, (list, tuple))
        or len(embedding) != EMBEDDING_DIMENSIONS
    ):
        raise EmbeddingMissingError(
            f"Embedding must be a list/tuple of {EMBEDDING_DIMENSIONS} floats, got {type(embedding)} "
            f"with length {len(embedding) if hasattr(embedding, '__len__') else 'N/A'}"
        )

    if pool is None:
        pool = await get_pool()

    # Convert embedding to pgvector format (string representation)
    embedding_str = f"[{','.join(str(v) for v in embedding)}]"

    # Derive Supabase columns from GuidelineSection fields
    pub_date = datetime.strptime(
        guideline_section.publication_date, "%Y-%m-%d"
    ).date()
    organization = SOURCE_TO_ORG[guideline_section.source]
    keywords = guideline_section.metadata.get("keywords")
    icd10_codes = guideline_section.metadata.get("icd10_codes")

    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO guidelines (
                    external_id,
                    title,
                    organization,
                    full_content,
                    publication_year,
                    publication_date,
                    source_type,
                    url,
                    embedding,
                    keywords,
                    icd10_codes
                ) VALUES ($1, $2, $3, $4, $5, $6, $7::source_type, $8, $9::vector, $10, $11)
                ON CONFLICT (external_id)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    organization = EXCLUDED.organization,
                    full_content = EXCLUDED.full_content,
                    publication_year = EXCLUDED.publication_year,
                    publication_date = EXCLUDED.publication_date,
                    source_type = EXCLUDED.source_type,
                    url = EXCLUDED.url,
                    embedding = EXCLUDED.embedding,
                    keywords = EXCLUDED.keywords,
                    icd10_codes = EXCLUDED.icd10_codes
                RETURNING id
                """,
                guideline_section.guideline_id,
                guideline_section.title,
                organization,
                guideline_section.content,
                pub_date.year,
                pub_date,
                "guidelines",
                guideline_section.url,
                embedding_str,
                keywords,
                icd10_codes,
            )
            record_id = str(row["id"])
            logger.debug(
                "Stored guideline section %s with id=%s",
                guideline_section.guideline_id,
                record_id,
            )
            return record_id

    except asyncpg.PostgresError as e:
        raise GuidelineInsertError(
            f"Failed to insert guideline section {guideline_section.guideline_id}: {e}"
        ) from e


async def search_guidelines(
    query: str | Sequence[float],
    limit: int = 10,
    *,
    source_filter: str | GuidelineSource | None = None,
    publication_date_from: str | date | None = None,
    publication_date_to: str | date | None = None,
    pool: asyncpg.Pool | None = None,
) -> list[dict[str, Any]]:
    """Search guidelines using vector similarity (cosine distance).

    Args:
        query: Query embedding vector (1536 dimensions) or query text.
            If string is provided, it must be pre-embedded before calling.
        limit: Maximum number of results (1-100).
        source_filter: Filter by source (cls_jep, esc, ers).
        publication_date_from: Filter by publication date (inclusive).
        publication_date_to: Filter by publication date (inclusive).
        pool: Optional connection pool.

    Returns:
        List of guideline sections with similarity scores, ordered by relevance.
        Each dict uses backward-compatible keys: id, guideline_id, title,
        section_name, content, publication_date, source, url, metadata,
        similarity_score.

    Raises:
        GuidelineSearchError: If search fails.
        ValueError: If query is invalid.

    Example:
        >>> results = await search_guidelines(
        ...     query=[0.1, 0.2, ...],  # 1536-dim embedding
        ...     limit=5,
        ...     source_filter=GuidelineSource.CLS_JEP,
        ... )
        >>> for r in results:
        ...     print(f"{r['title']}: {r['similarity_score']:.3f}")
    """
    # Validate query
    if isinstance(query, str):
        raise ValueError(
            f"Query must be a pre-computed embedding vector ({EMBEDDING_DIMENSIONS} dimensions). "
            "Use create_embeddings() to convert text to embedding first."
        )

    if not isinstance(query, (list, tuple)) or len(query) != EMBEDDING_DIMENSIONS:
        raise ValueError(
            f"Query embedding must be a list/tuple of {EMBEDDING_DIMENSIONS} floats, "
            f"got {type(query)} with length {len(query) if hasattr(query, '__len__') else 'N/A'}"
        )

    # Validate limit
    if not 1 <= limit <= 100:
        raise ValueError(f"Limit must be between 1 and 100, got {limit}")

    if pool is None:
        pool = await get_pool()

    # Build query with optional filters
    query_parts = [
        """
        SELECT
            id,
            external_id,
            title,
            organization,
            full_content,
            publication_date,
            source_type,
            url,
            keywords,
            icd10_codes,
            1 - (embedding <=> $1::vector) as similarity_score
        FROM guidelines
        WHERE embedding IS NOT NULL
        """
    ]
    params: list[Any] = [f"[{','.join(str(v) for v in query)}]"]
    param_idx = 2

    # Add source filter — all GuidelineSource values map to "guidelines"
    if source_filter is not None:
        query_parts.append(f"AND source_type = ${param_idx}::source_type")
        params.append("guidelines")
        param_idx += 1

    # Add publication date filters
    if publication_date_from is not None:
        date_from = (
            datetime.strptime(publication_date_from, "%Y-%m-%d").date()
            if isinstance(publication_date_from, str)
            else publication_date_from
        )
        query_parts.append(f"AND publication_date >= ${param_idx}")
        params.append(date_from)
        param_idx += 1

    if publication_date_to is not None:
        date_to = (
            datetime.strptime(publication_date_to, "%Y-%m-%d").date()
            if isinstance(publication_date_to, str)
            else publication_date_to
        )
        query_parts.append(f"AND publication_date <= ${param_idx}")
        params.append(date_to)
        param_idx += 1

    # Order by similarity (cosine distance, lower is more similar)
    query_parts.append(f"ORDER BY embedding <=> $1::vector LIMIT ${param_idx}")
    params.append(limit)

    full_query = "\n".join(query_parts)

    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(full_query, *params)

            results = []
            for row in rows:
                # Reconstruct metadata from keywords/icd10_codes columns
                metadata: dict[str, Any] = {}
                if row["keywords"] is not None:
                    metadata["keywords"] = row["keywords"]
                if row["icd10_codes"] is not None:
                    metadata["icd10_codes"] = row["icd10_codes"]

                results.append(
                    {
                        "id": str(row["id"]),
                        "guideline_id": row["external_id"],
                        "title": row["title"],
                        "section_name": row["organization"],
                        "content": row["full_content"] or "",
                        "publication_date": row["publication_date"].isoformat(),
                        "source": row["source_type"],
                        "url": row["url"],
                        "metadata": metadata,
                        "similarity_score": float(row["similarity_score"]),
                    }
                )

            logger.debug(
                "Search returned %d results (limit=%d, source=%s)",
                len(results),
                limit,
                source_filter,
            )
            return results

    except asyncpg.PostgresError as e:
        raise GuidelineSearchError(f"Failed to search guidelines: {e}") from e


async def get_guideline_section(
    guideline_id: str,
    section_name: str | None = None,
    *,
    section_id: str | None = None,
    pool: asyncpg.Pool | None = None,
) -> dict[str, Any]:
    """Get a specific guideline section by external_id or UUID.

    Args:
        guideline_id: Guideline identifier (maps to external_id, unique).
        section_name: Ignored in Supabase schema (kept for backward compat).
        section_id: UUID string (alternative to guideline_id).
        pool: Optional connection pool.

    Returns:
        Dict with backward-compatible keys: id, guideline_id, title,
        section_name, content, publication_date, source, url, metadata.

    Raises:
        GuidelineNotFoundError: If section is not found.
        ValueError: If no usable identifier is provided.

    Example:
        >>> section = await get_guideline_section(
        ...     guideline_id="CLS-JEP-2024-001",
        ... )
        >>> section = await get_guideline_section(
        ...     guideline_id="",
        ...     section_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        ... )
    """
    if section_id is None and not guideline_id:
        raise ValueError(
            "Either guideline_id or section_id must be provided"
        )

    if pool is None:
        pool = await get_pool()

    try:
        async with pool.acquire() as conn:
            if section_id is not None:
                row = await conn.fetchrow(
                    """
                    SELECT
                        id, external_id, title, organization, full_content,
                        publication_date, source_type, url, keywords, icd10_codes
                    FROM guidelines
                    WHERE id = $1::uuid
                    """,
                    section_id,
                )
            else:
                row = await conn.fetchrow(
                    """
                    SELECT
                        id, external_id, title, organization, full_content,
                        publication_date, source_type, url, keywords, icd10_codes
                    FROM guidelines
                    WHERE external_id = $1
                    """,
                    guideline_id,
                )

            if row is None:
                if section_id is not None:
                    raise GuidelineNotFoundError(
                        f"Guideline section with id={section_id} not found"
                    )
                else:
                    raise GuidelineNotFoundError(
                        f"Guideline section {guideline_id} not found"
                    )

            # Reconstruct metadata from keywords/icd10_codes columns
            metadata: dict[str, Any] = {}
            if row["keywords"] is not None:
                metadata["keywords"] = row["keywords"]
            if row["icd10_codes"] is not None:
                metadata["icd10_codes"] = row["icd10_codes"]

            return {
                "id": str(row["id"]),
                "guideline_id": row["external_id"],
                "title": row["title"],
                "section_name": row["organization"],
                "content": row["full_content"] or "",
                "publication_date": row["publication_date"].isoformat(),
                "source": row["source_type"],
                "url": row["url"],
                "metadata": metadata,
            }

    except asyncpg.PostgresError as e:
        raise GuidelinesStorageError(f"Failed to get guideline section: {e}") from e


async def delete_guideline_section(
    guideline_id: str,
    section_name: str | None = None,
    *,
    section_id: str | None = None,
    pool: asyncpg.Pool | None = None,
) -> bool:
    """Delete a guideline section from the database.

    Args:
        guideline_id: Guideline identifier (maps to external_id).
        section_name: Ignored in Supabase schema (kept for backward compat).
        section_id: UUID string (alternative to guideline_id).
        pool: Optional connection pool.

    Returns:
        True if deleted, False if not found.
    """
    if section_id is None and not guideline_id:
        raise ValueError(
            "Either guideline_id or section_id must be provided"
        )

    if pool is None:
        pool = await get_pool()

    try:
        async with pool.acquire() as conn:
            if section_id is not None:
                result = await conn.execute(
                    "DELETE FROM guidelines WHERE id = $1::uuid",
                    section_id,
                )
            else:
                result = await conn.execute(
                    "DELETE FROM guidelines WHERE external_id = $1",
                    guideline_id,
                )

            # Result format: "DELETE N"
            deleted_count = int(result.split()[-1])
            return deleted_count > 0

    except asyncpg.PostgresError as e:
        raise GuidelinesStorageError(f"Failed to delete guideline section: {e}") from e
