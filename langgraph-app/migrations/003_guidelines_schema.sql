-- =============================================================================
-- Migration 003: Guidelines Schema with pgvector Support
-- =============================================================================
-- Feature 006: Guidelines Agent - Creates table and indexes for storing
-- clinical guideline sections with vector embeddings for semantic search.
--
-- Prerequisites:
--   - PostgreSQL 15+ with pgvector extension available
--   - Supabase project or local PostgreSQL with pgvector installed
--
-- Usage:
--   psql -d your_database -f 003_guidelines_schema.sql
--
-- Rollback:
--   DROP INDEX IF EXISTS guidelines_embedding_idx;
--   DROP INDEX IF EXISTS guidelines_guideline_id_idx;
--   DROP INDEX IF EXISTS guidelines_source_idx;
--   DROP INDEX IF EXISTS guidelines_publication_date_idx;
--   DROP TABLE IF EXISTS guidelines;
-- =============================================================================

-- Enable pgvector extension for vector similarity search
-- This extension must be available in the PostgreSQL instance
CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================================================
-- Guidelines Table
-- =============================================================================
-- Stores clinical guideline sections from ČLS JEP, ESC, ERS sources
-- with embeddings for semantic search capabilities.
--
-- Columns:
--   - id: Auto-incrementing primary key
--   - guideline_id: Unique identifier (e.g., CLS-JEP-2024-001)
--   - title: Guideline document title
--   - section_name: Section/chapter name within the guideline
--   - content: Full text content of the section
--   - publication_date: Date the guideline was published
--   - source: Source organization (cls_jep, esc, ers)
--   - url: URL to the original guideline document
--   - embedding: 1536-dimensional vector from text-embedding-ada-002
--   - metadata: Additional metadata (chunk info, ingestion timestamp, etc.)
--   - created_at: Record creation timestamp
--   - updated_at: Record update timestamp
-- =============================================================================

CREATE TABLE IF NOT EXISTS guidelines (
    -- Primary key
    id BIGSERIAL PRIMARY KEY,

    -- Guideline identification
    guideline_id VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    section_name TEXT NOT NULL,

    -- Content
    content TEXT NOT NULL,

    -- Metadata fields
    publication_date DATE NOT NULL,
    source VARCHAR(20) NOT NULL CHECK (source IN ('cls_jep', 'esc', 'ers')),
    url TEXT NOT NULL,

    -- Vector embedding for semantic search
    -- Using 1536 dimensions for OpenAI text-embedding-ada-002 model
    embedding vector(1536),

    -- Additional metadata stored as JSONB
    -- Can include: chunk_index, total_chunks, ingestion_timestamp, specialty, etc.
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Unique constraint on guideline_id + section_name to prevent duplicates
    CONSTRAINT guidelines_unique_section UNIQUE (guideline_id, section_name)
);

-- =============================================================================
-- Indexes
-- =============================================================================

-- HNSW index on embedding for fast approximate nearest neighbor search
-- Using cosine distance (vector_cosine_ops) for semantic similarity
-- HNSW parameters:
--   - m: Maximum number of connections per layer (default: 16)
--   - ef_construction: Size of dynamic candidate list for construction (default: 64)
CREATE INDEX IF NOT EXISTS guidelines_embedding_idx
    ON guidelines
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- B-tree index on guideline_id for fast lookups
CREATE INDEX IF NOT EXISTS guidelines_guideline_id_idx
    ON guidelines (guideline_id);

-- B-tree index on source for filtering by source organization
CREATE INDEX IF NOT EXISTS guidelines_source_idx
    ON guidelines (source);

-- B-tree index on publication_date for date range queries
CREATE INDEX IF NOT EXISTS guidelines_publication_date_idx
    ON guidelines (publication_date);

-- =============================================================================
-- Comments
-- =============================================================================

COMMENT ON TABLE guidelines IS 'Clinical guideline sections with vector embeddings for semantic search';
COMMENT ON COLUMN guidelines.guideline_id IS 'Unique guideline identifier (e.g., CLS-JEP-2024-001)';
COMMENT ON COLUMN guidelines.embedding IS '1536-dimensional embedding from text-embedding-ada-002';
COMMENT ON COLUMN guidelines.source IS 'Source organization: cls_jep (Czech), esc (European Cardiology), ers (European Respiratory)';
COMMENT ON INDEX guidelines_embedding_idx IS 'HNSW index for fast approximate nearest neighbor search using cosine similarity';

-- =============================================================================
-- Trigger for updated_at timestamp
-- =============================================================================

CREATE OR REPLACE FUNCTION update_guidelines_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS guidelines_updated_at_trigger ON guidelines;

CREATE TRIGGER guidelines_updated_at_trigger
    BEFORE UPDATE ON guidelines
    FOR EACH ROW
    EXECUTE FUNCTION update_guidelines_updated_at();
