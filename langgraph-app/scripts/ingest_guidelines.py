#!/usr/bin/env python
r"""Ingestion script for ČLS JEP PDF guidelines (Feature 006).

Batch processing script for converting PDF guidelines into GuidelineSection objects
with embeddings, ready for pgvector storage.

Usage:
    # Single PDF
    python scripts/ingest_guidelines.py \
        --pdf data/guidelines/hypertenze-2024.pdf \
        --id CLS-JEP-2024-001 \
        --title "Doporučené postupy pro hypertenzi" \
        --source cls_jep \
        --date 2024-01-15 \
        --url https://www.cls.cz/guidelines/hypertenze-2024.pdf \
        --output data/processed/cls-jep-2024-001.json

    # Batch processing from CSV
    python scripts/ingest_guidelines.py \
        --batch data/guidelines/ \
        --metadata data/guidelines/metadata.csv \
        --output-dir data/processed/

CSV format:
    filename,guideline_id,title,source,publication_date,url
    hypertenze-2024.pdf,CLS-JEP-2024-001,Doporučené postupy...,cls_jep,2024-01-15,https://...
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent.models.guideline_models import GuidelineSection, GuidelineSource
from agent.utils.pdf_processor import (
    chunk_text,
    create_embeddings,
    load_pdf,
)


async def ingest_guideline_pdf(
    pdf_path: str,
    guideline_id: str,
    title: str,
    source: GuidelineSource,
    publication_date: str,
    url: str,
    chunk_size: int = 800,
    overlap: int = 100,
    create_embeddings_flag: bool = True,
    best_effort_embeddings: bool = False,
) -> list[GuidelineSection]:
    """Ingest single PDF guideline into GuidelineSection objects.

    Workflow:
        1. Load PDF → raw text
        2. Chunk text → semantic chunks (preserve headers)
        3. Create embeddings → vectors (1536 dim) [optional]
        4. Create GuidelineSection objects
        5. Return sections (ready for pgvector storage)

    Args:
        pdf_path: Path to PDF file.
        guideline_id: Unique ID (e.g., "CLS-JEP-2024-001").
        title: Guideline title.
        source: GuidelineSource enum (CLS_JEP/ESC/ERS).
        publication_date: Publication date (YYYY-MM-DD).
        url: URL to guideline document.
        chunk_size: Target chunk size in characters (default: 800).
        overlap: Overlap between chunks (default: 100).
        create_embeddings_flag: Whether to create embeddings (default: True).
        best_effort_embeddings: If True, continue without embeddings on failure.
            If False (default), raise exception on embedding failure.

    Returns:
        List of GuidelineSection objects with embeddings in metadata.

    Raises:
        FileNotFoundError: If PDF file does not exist.
        PDFReadError: If PDF cannot be parsed.
        RuntimeError: If embeddings creation fails and best_effort_embeddings=False.
    """
    print(f"Processing: {pdf_path}")

    # Step 1: Load PDF
    print("  Loading PDF...")
    raw_text = load_pdf(pdf_path)
    print(f"  Extracted {len(raw_text)} characters")

    # Step 2: Chunk text
    print("  Chunking text...")
    chunks = chunk_text(raw_text, chunk_size=chunk_size, overlap=overlap)
    print(f"  Created {len(chunks)} chunks")

    # Step 3: Create embeddings (optional)
    embeddings: list[list[float]] | None = None
    if create_embeddings_flag:
        print("  Creating embeddings...")
        try:
            embeddings = await create_embeddings(chunks)
            print(f"  Created {len(embeddings)} embeddings (1536 dim)")
        except Exception as e:
            if best_effort_embeddings:
                print(f"  Warning: Failed to create embeddings: {e}")
                print("  Continuing without embeddings (best_effort_embeddings=True)")
                embeddings = None
            else:
                print(f"  Error: Failed to create embeddings: {e}")
                raise RuntimeError(
                    f"Embedding creation failed for {pdf_path}: {e}. "
                    "Set best_effort_embeddings=True to continue without embeddings."
                ) from e

    # Step 4: Create GuidelineSection objects
    print("  Creating GuidelineSection objects...")
    sections: list[GuidelineSection] = []

    for i, chunk in enumerate(chunks):
        # Extract section name from chunk (first line or first sentence)
        lines = chunk.split("\n")
        first_line = lines[0].strip()

        # Use first line as section name if it looks like a header
        if len(first_line) < 100 and first_line:
            section_name = first_line
        else:
            # Use first sentence or truncate
            section_name = chunk[:80].replace("\n", " ").strip()
            if len(chunk) > 80:
                section_name += "..."

        section = GuidelineSection(
            guideline_id=guideline_id,
            title=title,
            section_name=f"{section_name} (Part {i + 1}/{len(chunks)})",
            content=chunk,
            publication_date=publication_date,
            source=source,
            url=url,
        )

        # Add embedding to metadata if available
        if embeddings and i < len(embeddings):
            section.metadata["embedding"] = embeddings[i]
            section.metadata["embedding_model"] = "text-embedding-ada-002"
            section.metadata["embedding_dim"] = 1536

        section.metadata["chunk_index"] = i
        section.metadata["total_chunks"] = len(chunks)
        section.metadata["ingested_at"] = datetime.now().isoformat()

        sections.append(section)

    print(f"  Created {len(sections)} GuidelineSection objects")
    return sections


async def ingest_directory(
    guidelines_dir: str,
    metadata_csv: str,
    output_dir: str,
    chunk_size: int = 800,
    overlap: int = 100,
    create_embeddings_flag: bool = True,
    best_effort_embeddings: bool = False,
) -> dict[str, list[GuidelineSection]]:
    """Batch ingest all PDFs in directory using metadata CSV.

    CSV format:
        filename,guideline_id,title,source,publication_date,url

    Args:
        guidelines_dir: Directory containing PDF files.
        metadata_csv: Path to metadata CSV file.
        output_dir: Directory to save processed JSON files.
        chunk_size: Target chunk size in characters.
        overlap: Overlap between chunks.
        create_embeddings_flag: Whether to create embeddings.
        best_effort_embeddings: If True, continue without embeddings on failure.

    Returns:
        Dictionary mapping guideline_id to list of GuidelineSection objects.
    """
    print(f"Batch processing from: {guidelines_dir}")
    print(f"Using metadata from: {metadata_csv}")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    results: dict[str, list[GuidelineSection]] = {}
    errors: list[str] = []

    # Read metadata CSV
    with open(metadata_csv, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            filename = row["filename"]
            pdf_path = os.path.join(guidelines_dir, filename)

            if not os.path.exists(pdf_path):
                errors.append(f"File not found: {pdf_path}")
                continue

            try:
                # Parse source enum
                source_str = row["source"].lower()
                source = GuidelineSource(source_str)

                sections = await ingest_guideline_pdf(
                    pdf_path=pdf_path,
                    guideline_id=row["guideline_id"],
                    title=row["title"],
                    source=source,
                    publication_date=row["publication_date"],
                    url=row["url"],
                    chunk_size=chunk_size,
                    overlap=overlap,
                    create_embeddings_flag=create_embeddings_flag,
                    best_effort_embeddings=best_effort_embeddings,
                )

                results[row["guideline_id"]] = sections

                # Save individual JSON file
                output_file = os.path.join(output_dir, f"{row['guideline_id']}.json")
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(
                        [s.model_dump() for s in sections],
                        f,
                        indent=2,
                        ensure_ascii=False,
                    )
                print(f"  Saved: {output_file}")

            except Exception as e:
                errors.append(f"Error processing {filename}: {e}")

    # Report errors
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")

    print(f"\nProcessed {len(results)} guidelines, {len(errors)} errors")
    return results


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest ČLS JEP guidelines into GuidelineSection objects"
    )

    # Single PDF mode
    parser.add_argument("--pdf", help="Path to PDF file")
    parser.add_argument(
        "--id", dest="guideline_id", help="Guideline ID (CLS-JEP-YYYY-NNN)"
    )
    parser.add_argument("--title", help="Guideline title")
    parser.add_argument(
        "--source",
        default="cls_jep",
        choices=["cls_jep", "esc", "ers"],
        help="Source (cls_jep/esc/ers)",
    )
    parser.add_argument("--date", help="Publication date (YYYY-MM-DD)")
    parser.add_argument("--url", help="URL to guideline")

    # Batch mode
    parser.add_argument(
        "--batch", help="Directory containing PDFs for batch processing"
    )
    parser.add_argument("--metadata", help="Path to metadata CSV file")
    parser.add_argument("--output-dir", help="Output directory for batch processing")

    # Output
    parser.add_argument("--output", help="Output JSON file (single PDF mode)")

    # Processing options
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=800,
        help="Target chunk size in characters (default: 800)",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=100,
        help="Overlap between chunks (default: 100)",
    )
    parser.add_argument(
        "--no-embeddings",
        action="store_true",
        help="Skip embedding creation (faster, for testing)",
    )
    parser.add_argument(
        "--best-effort-embeddings",
        action="store_true",
        help="Continue without embeddings if creation fails (default: fail on error)",
    )

    args = parser.parse_args()

    # Validate arguments
    if args.batch:
        # Batch mode
        if not args.metadata:
            parser.error("--metadata required for batch processing")
        if not args.output_dir:
            parser.error("--output-dir required for batch processing")

        asyncio.run(
            ingest_directory(
                guidelines_dir=args.batch,
                metadata_csv=args.metadata,
                output_dir=args.output_dir,
                chunk_size=args.chunk_size,
                overlap=args.overlap,
                create_embeddings_flag=not args.no_embeddings,
                best_effort_embeddings=args.best_effort_embeddings,
            )
        )

    elif args.pdf:
        # Single PDF mode
        if not all([args.guideline_id, args.title, args.date, args.url]):
            parser.error(
                "--id, --title, --date, and --url required for single PDF mode"
            )

        try:
            source = GuidelineSource(args.source.lower())
        except ValueError:
            parser.error(f"Invalid source: {args.source}")

        sections = asyncio.run(
            ingest_guideline_pdf(
                pdf_path=args.pdf,
                guideline_id=args.guideline_id,
                title=args.title,
                source=source,
                publication_date=args.date,
                url=args.url,
                chunk_size=args.chunk_size,
                overlap=args.overlap,
                create_embeddings_flag=not args.no_embeddings,
                best_effort_embeddings=args.best_effort_embeddings,
            )
        )

        # Save to JSON if output specified
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(
                    [s.model_dump() for s in sections],
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
            print(f"Saved to: {args.output}")
        else:
            # Print summary
            print("\nSummary:")
            print(f"  Guideline ID: {args.guideline_id}")
            print(f"  Title: {args.title}")
            print(f"  Sections: {len(sections)}")
            for i, section in enumerate(sections[:3]):
                print(f"  [{i + 1}] {section.section_name[:60]}...")
            if len(sections) > 3:
                print(f"  ... and {len(sections) - 3} more sections")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
