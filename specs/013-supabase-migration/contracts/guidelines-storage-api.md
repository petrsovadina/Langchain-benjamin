# Internal API Contract: guidelines_storage.py

**Date**: 2026-02-18
**Type**: Python internal module API (not REST)
**Module**: `langgraph-app/src/agent/utils/guidelines_storage.py`

## Functions (Public API)

### store_guideline

```python
async def store_guideline(
    guideline_section: GuidelineSection,
    *,
    pool: asyncpg.Pool | None = None,
) -> str:
    """Store a guideline with embedding. Returns UUID string of inserted/updated record."""
```

**SQL Contract**:
```sql
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
```

**Parameter mapping**:
| $N | Python source | Value |
|---|---|---|
| $1 | `guideline_section.guideline_id` | external_id |
| $2 | `guideline_section.title` | title |
| $3 | `SOURCE_TO_ORG[guideline_section.source]` | "ČLS JEP" / "ESC" / "ERS" |
| $4 | `guideline_section.content` | full_content |
| $5 | `datetime.strptime(pub_date, "%Y-%m-%d").year` | publication_year |
| $6 | `datetime.strptime(pub_date, "%Y-%m-%d").date()` | publication_date |
| $7 | `"guidelines"` | source_type (always) |
| $8 | `guideline_section.url` | url |
| $9 | `"[0.1,0.2,...]"` | embedding vector string |
| $10 | `guideline_section.metadata.get("keywords")` | keywords array or None |
| $11 | `guideline_section.metadata.get("icd10_codes")` | icd10_codes array or None |

**Return**: `str` (UUID of inserted/updated row)

**Errors**: `EmbeddingMissingError`, `GuidelineInsertError`

---

### search_guidelines

```python
async def search_guidelines(
    query: str | Sequence[float],
    limit: int = 10,
    *,
    source_filter: str | GuidelineSource | None = None,
    publication_date_from: str | date | None = None,
    publication_date_to: str | date | None = None,
    pool: asyncpg.Pool | None = None,
) -> list[dict[str, Any]]:
    """Search by vector similarity. Returns list of dicts with similarity_score."""
```

**SQL Contract**:
```sql
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
  [AND source_type = $N::source_type]
  [AND publication_date >= $N]
  [AND publication_date <= $N]
ORDER BY embedding <=> $1::vector
LIMIT $N
```

**Return dict keys**: `id` (str/UUID), `guideline_id` (str), `title`, `section_name`, `content`, `publication_date`, `source`, `url`, `metadata`, `similarity_score`

Note: Return dict uses **backward-compatible keys** (`guideline_id`, `section_name`, `content`, `source`) that map from Supabase columns (`external_id`, `organization`, `full_content`, `source_type`).

**Errors**: `GuidelineSearchError`, `ValueError`

---

### get_guideline_section

```python
async def get_guideline_section(
    guideline_id: str,
    section_name: str | None = None,
    *,
    section_id: str | None = None,
    pool: asyncpg.Pool | None = None,
) -> dict[str, Any]:
    """Get by external_id or UUID. Returns dict with guideline data."""
```

**SQL Contract (by external_id)**:
```sql
SELECT id, external_id, title, organization, full_content,
       publication_date, source_type, url, keywords, icd10_codes
FROM guidelines
WHERE external_id = $1
```

**SQL Contract (by UUID)**:
```sql
SELECT id, external_id, title, organization, full_content,
       publication_date, source_type, url, keywords, icd10_codes
FROM guidelines
WHERE id = $1::uuid
```

**Note**: The `section_name` parameter becomes optional — lookup by `external_id` alone is sufficient (unique constraint). When `section_id` is provided, it's a UUID string, not int.

**Errors**: `GuidelineNotFoundError`, `GuidelinesStorageError`, `ValueError`

---

### delete_guideline_section

```python
async def delete_guideline_section(
    guideline_id: str,
    section_name: str | None = None,
    *,
    section_id: str | None = None,
    pool: asyncpg.Pool | None = None,
) -> bool:
    """Delete by external_id or UUID. Returns True if deleted."""
```

**SQL Contract (by external_id)**:
```sql
DELETE FROM guidelines WHERE external_id = $1
```

**SQL Contract (by UUID)**:
```sql
DELETE FROM guidelines WHERE id = $1::uuid
```

**Errors**: `GuidelinesStorageError`, `ValueError`

---

## Constants

```python
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
```
