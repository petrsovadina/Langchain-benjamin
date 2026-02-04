"""Agent utilities module.

Provides helper functions and utilities for agent processing.

Modules:
    translation_prompts: Translation prompt templates.
    pdf_processor: PDF processing and chunking utilities (Feature 006).
    guidelines_storage: Async storage utilities for guidelines with pgvector.
"""

from agent.utils.guidelines_storage import (
    DatabaseConfig,
    EmbeddingMissingError,
    GuidelineInsertError,
    GuidelineNotFoundError,
    GuidelineSearchError,
    GuidelinesStorageError,
    close_pool,
    delete_guideline_section,
    get_guideline_section,
    get_pool,
    search_guidelines,
    store_guideline,
)
from agent.utils.pdf_processor import (
    PDFReadError,
    chunk_text,
    count_tokens,
    create_embeddings,
    detect_section_headers,
    load_pdf,
    split_on_headers,
)

__all__ = [
    # PDF processor
    "PDFReadError",
    "load_pdf",
    "chunk_text",
    "create_embeddings",
    "detect_section_headers",
    "split_on_headers",
    "count_tokens",
    # Guidelines storage
    "DatabaseConfig",
    "GuidelinesStorageError",
    "GuidelineNotFoundError",
    "GuidelineInsertError",
    "GuidelineSearchError",
    "EmbeddingMissingError",
    "get_pool",
    "close_pool",
    "store_guideline",
    "search_guidelines",
    "get_guideline_section",
    "delete_guideline_section",
]
