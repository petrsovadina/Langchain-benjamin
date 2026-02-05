"""PDF processing utilities for Guidelines Agent (Feature 006).

Provides semantic chunking and embedding creation for ČLS JEP guidelines.

Functions:
    load_pdf: Extract text from PDF file.
    chunk_text: Semantic chunking with header preservation.
    create_embeddings: Create OpenAI embeddings for text chunks.
    detect_section_headers: Find section headers in text.
    split_on_headers: Split text on detected headers.
    count_tokens: Count tokens using tiktoken.
"""

from __future__ import annotations

import asyncio
import os
import re
from typing import Any

import tiktoken

# Import AsyncOpenAI for type hints - imported at runtime in create_embeddings
# when client is None
try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = Any  # type: ignore[misc,assignment]


class PDFReadError(Exception):
    """Raised when PDF cannot be read or parsed."""

    pass


def load_pdf(pdf_path: str) -> str:
    """Load PDF and extract text content.

    Uses pdfplumber library for layout-aware text extraction.
    Provides robust handling of complex documents and good support
    for Czech text with diacritics. See https://github.com/jsvine/pdfplumber

    Args:
        pdf_path: Path to PDF file.

    Returns:
        Raw text extracted from all PDF pages.

    Raises:
        FileNotFoundError: If PDF file does not exist.
        PDFReadError: If PDF cannot be parsed.

    Example:
        >>> text = load_pdf("guidelines/hypertenze-2024.pdf")
        >>> len(text) > 0
        True
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        import pdfplumber

        text_parts: list[str] = []

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        return "\n\n".join(text_parts)

    except Exception as e:
        raise PDFReadError(f"Failed to read PDF {pdf_path}: {e}") from e


def detect_section_headers(text: str) -> list[tuple[int, str]]:
    r"""Detect section headers in text.

    Supports multiple header formats:
    - Markdown headers: # Header, ## Header
    - Numbered headers: 1. Header, 1.1 Header
    - Colon headers: HEADER:

    Args:
        text: Raw text to analyze.

    Returns:
        List of (position, header_text) tuples sorted by position.

    Example:
        >>> headers = detect_section_headers("# Main\nText\n## Sub")
        >>> len(headers)
        2
    """
    headers: list[tuple[int, str]] = []

    # Pattern for markdown headers (# Header, ## Header, etc.)
    markdown_pattern = r"^(#{1,4})\s+(.+)$"

    # Pattern for numbered headers (1. Header, 1.1 Header, 2.3.1 Header)
    numbered_pattern = r"^(\d+(?:\.\d+)*\.?)\s+([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][^\n]+)$"

    # Pattern for colon headers (HEADER:)
    colon_pattern = r"^([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ\s]{2,}):$"

    for pattern in [markdown_pattern, numbered_pattern, colon_pattern]:
        for match in re.finditer(pattern, text, re.MULTILINE):
            header_text = match.group(0).strip()
            headers.append((match.start(), header_text))

    # Sort by position
    headers.sort(key=lambda x: x[0])

    return headers


def split_on_headers(text: str, headers: list[tuple[int, str]]) -> list[str]:
    r"""Split text into sections based on detected headers.

    Each section includes its header at the beginning.

    Args:
        text: Raw text to split.
        headers: List of (position, header_text) from detect_section_headers.

    Returns:
        List of text sections, each starting with its header.

    Example:
        >>> text = "# Intro\nText 1\n# Next\nText 2"
        >>> headers = detect_section_headers(text)
        >>> sections = split_on_headers(text, headers)
        >>> len(sections)
        2
    """
    if not headers:
        return [text] if text.strip() else []

    sections: list[str] = []

    # Handle text before first header
    first_pos = headers[0][0]
    if first_pos > 0:
        preamble = text[:first_pos].strip()
        if preamble:
            sections.append(preamble)

    # Split on headers
    for i, (pos, _header) in enumerate(headers):
        if i < len(headers) - 1:
            next_pos = headers[i + 1][0]
            section = text[pos:next_pos].strip()
        else:
            section = text[pos:].strip()

        if section:
            sections.append(section)

    return sections


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """Count tokens in text using tiktoken.

    Args:
        text: Text to count tokens for.
        model: Tiktoken encoding model (default: cl100k_base for GPT-4/ada-002).

    Returns:
        Number of tokens in text.

    Example:
        >>> count_tokens("Hello world")
        2
    """
    try:
        encoding = tiktoken.get_encoding(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback: rough estimate (4 chars per token)
        return len(text) // 4


def chunk_text(
    text: str,
    chunk_size: int = 800,
    overlap: int = 100,
    min_chunk_size: int = 100,
    max_chunk_size: int = 1500,
) -> list[str]:
    r"""Perform semantic chunking with header preservation.

    Strategy:
    1. Detect section headers in text
    2. Split text on headers (each section gets its header)
    3. If section > chunk_size, split into sub-chunks with overlap
    4. Preserve header in each sub-chunk

    Args:
        text: Raw text to chunk.
        chunk_size: Target chunk size in characters (default: 800).
        overlap: Overlap between chunks in characters (default: 100).
        min_chunk_size: Minimum chunk size (default: 100).
        max_chunk_size: Maximum chunk size (default: 1500).

    Returns:
        List of text chunks with preserved headers.

    Raises:
        ValueError: If text is empty.

    Example:
        >>> text = "# Header\n" + "Content. " * 200
        >>> chunks = chunk_text(text, chunk_size=500)
        >>> all("# Header" in c for c in chunks)
        True
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    # Detect headers and split into sections
    headers = detect_section_headers(text)
    sections = split_on_headers(text, headers)

    if not sections:
        sections = [text]

    chunks: list[str] = []

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Extract header from section (first line if it's a header)
        lines = section.split("\n", 1)
        first_line = lines[0].strip()

        # Check if first line is a header
        # Include Czech uppercase letters with diacritics (ÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ)
        # to match detect_section_headers() colon pattern
        header = ""
        content = section
        czech_upper = r"A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ"
        header_pattern = (
            rf"^(#{{1,4}}|\d+\.|\d+\.\d+|[{czech_upper}][{czech_upper}\s]+:)"
        )
        if re.match(header_pattern, first_line):
            header = first_line
            content = lines[1].strip() if len(lines) > 1 else ""

        # If section fits in chunk_size, add as-is
        if len(section) <= chunk_size:
            if len(section) >= min_chunk_size:
                chunks.append(section)
            elif section:  # Small but non-empty - merge with previous if possible
                if chunks:
                    combined = chunks[-1] + "\n\n" + section
                    if len(combined) <= max_chunk_size:
                        chunks[-1] = combined
                    else:
                        chunks.append(section)
                else:
                    chunks.append(section)
            continue

        # Section too large - split with overlap
        if not content:
            content = section

        # Split content into sub-chunks
        words = content.split()
        current_chunk: list[str] = []
        current_length = 0

        for word in words:
            word_len = len(word) + 1  # +1 for space

            if current_length + word_len > chunk_size - len(header) - 2:
                # Finish current chunk
                chunk_content = " ".join(current_chunk)
                if header:
                    chunk_text_final = f"{header}\n\n{chunk_content}"
                else:
                    chunk_text_final = chunk_content

                if len(chunk_text_final) >= min_chunk_size:
                    chunks.append(chunk_text_final)

                # Start new chunk with overlap
                overlap_words = current_chunk[-(overlap // 5) :] if overlap > 0 else []
                current_chunk = overlap_words + [word]
                current_length = sum(len(w) + 1 for w in current_chunk)
            else:
                current_chunk.append(word)
                current_length += word_len

        # Add final chunk
        if current_chunk:
            chunk_content = " ".join(current_chunk)
            if header:
                chunk_text_final = f"{header}\n\n{chunk_content}"
            else:
                chunk_text_final = chunk_content

            if len(chunk_text_final) >= min_chunk_size:
                chunks.append(chunk_text_final)
            elif chunks:
                # Merge with previous if too small
                combined = chunks[-1] + " " + chunk_content
                if len(combined) <= max_chunk_size:
                    chunks[-1] = combined

    # Ensure all chunks are within bounds with header-aware splitting
    # Also handle sub-min chunks by prepending to next chunk (not dropping)
    final_chunks: list[str] = []
    pending_small_chunk: str | None = None  # Buffer for sub-min chunks
    czech_upper = r"A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ"
    header_re = rf"^(#{{1,4}}|\d+\.|\d+\.\d+|[{czech_upper}][{czech_upper}\s]+:)"

    for chunk in chunks:
        # Prepend any pending small chunk to current chunk
        if pending_small_chunk:
            chunk = pending_small_chunk + "\n\n" + chunk
            pending_small_chunk = None

        if len(chunk) > max_chunk_size:
            # Extract header from oversized chunk if present
            chunk_lines = chunk.split("\n", 1)
            first_line = chunk_lines[0].strip()
            chunk_header = ""
            chunk_content = chunk

            if re.match(header_re, first_line):
                chunk_header = first_line
                chunk_content = chunk_lines[1].strip() if len(chunk_lines) > 1 else ""

            # Calculate available space for content in each sub-chunk
            header_overhead = (
                len(chunk_header) + 2 if chunk_header else 0
            )  # +2 for "\n\n"
            content_max = max_chunk_size - header_overhead

            # Split content on word boundaries
            words = chunk_content.split()
            current_words: list[str] = []
            current_len = 0

            for word in words:
                word_len = len(word) + (1 if current_words else 0)  # +1 for space

                if current_len + word_len > content_max and current_words:
                    # Finish current sub-chunk
                    sub_content = " ".join(current_words)
                    if chunk_header:
                        sub_chunk = f"{chunk_header}\n\n{sub_content}"
                    else:
                        sub_chunk = sub_content

                    if len(sub_chunk) >= min_chunk_size:
                        final_chunks.append(sub_chunk)

                    # Start new sub-chunk with overlap (word-based)
                    overlap_word_count = max(1, overlap // 5)
                    overlap_words = current_words[-overlap_word_count:]
                    current_words = overlap_words + [word]
                    current_len = sum(len(w) + 1 for w in current_words) - 1
                else:
                    current_words.append(word)
                    current_len += word_len

            # Add final sub-chunk
            if current_words:
                sub_content = " ".join(current_words)
                if chunk_header:
                    sub_chunk = f"{chunk_header}\n\n{sub_content}"
                else:
                    sub_chunk = sub_content

                if len(sub_chunk) >= min_chunk_size:
                    final_chunks.append(sub_chunk)
                elif final_chunks:
                    # Merge with previous if too small
                    combined = final_chunks[-1] + " " + sub_content
                    if len(combined) <= max_chunk_size:
                        final_chunks[-1] = combined
                    else:
                        # Can't merge with previous, buffer for next
                        pending_small_chunk = sub_chunk
                else:
                    # No previous chunk, buffer for next
                    pending_small_chunk = sub_chunk

        elif len(chunk) >= min_chunk_size:
            final_chunks.append(chunk)
        else:
            # Chunk below min_chunk_size - try to merge or buffer
            if final_chunks:
                combined = final_chunks[-1] + "\n\n" + chunk
                if len(combined) <= max_chunk_size:
                    final_chunks[-1] = combined
                else:
                    # Can't merge with previous, buffer for next chunk
                    pending_small_chunk = chunk
            else:
                # No previous chunk exists, buffer for next
                pending_small_chunk = chunk

    # Handle any remaining pending small chunk at the end
    if pending_small_chunk:
        if final_chunks:
            # Try to merge with last chunk
            combined = final_chunks[-1] + "\n\n" + pending_small_chunk
            if len(combined) <= max_chunk_size:
                final_chunks[-1] = combined
            else:
                # Can't merge, add as-is (don't drop content)
                final_chunks.append(pending_small_chunk)
        else:
            # No chunks at all, add as-is (don't drop content)
            final_chunks.append(pending_small_chunk)

    return final_chunks


async def create_embeddings(
    texts: list[str],
    model: str = "text-embedding-ada-002",
    batch_size: int = 100,
    client: AsyncOpenAI | None = None,
) -> list[list[float]]:
    """Create OpenAI embeddings for text chunks.

    Args:
        texts: List of text chunks to embed. All chunks must be non-empty.
        model: OpenAI embedding model name (default: text-embedding-ada-002).
        batch_size: Max chunks per API call (default: 100, OpenAI limit).
        client: Optional AsyncOpenAI client (created if not provided).

    Returns:
        List of embedding vectors (1536 dimensions each for ada-002).
        Output list has same length as input with 1:1 positional correspondence.

    Raises:
        ValueError: If texts is empty or any chunk is empty/whitespace.
        OpenAIError: If API call fails after retries.

    Example:
        >>> chunks = ["Section 1: Hypertenze...", "Section 2: Diabetes..."]
        >>> embeddings = await create_embeddings(chunks)
        >>> len(embeddings) == len(chunks)
        True
        >>> len(embeddings[0])
        1536
    """
    if not texts:
        raise ValueError("Texts list cannot be empty")

    # Validate all chunks are non-empty to preserve positional alignment
    for i, text in enumerate(texts):
        if not text or not text.strip():
            raise ValueError(
                f"Text at index {i} is empty or whitespace. "
                "All chunks must contain content to preserve positional alignment."
            )

    # Create client if not provided
    if client is None:
        from openai import AsyncOpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        client = AsyncOpenAI(api_key=api_key)

    all_embeddings: list[list[float]] = []

    # Process in batches
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]

        # Retry logic
        max_retries = 3
        last_error: Exception | None = None

        for attempt in range(max_retries):
            try:
                response = await client.embeddings.create(
                    input=batch,
                    model=model,
                )

                # Extract embeddings
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                break

            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Exponential backoff
                    await asyncio.sleep(0.1 * (2**attempt))
                else:
                    raise RuntimeError(
                        f"Failed to create embeddings after {max_retries} attempts: {e}"
                    ) from last_error

        # Rate limiting between batches
        if i + batch_size < len(texts):
            await asyncio.sleep(0.1)

    return all_embeddings
