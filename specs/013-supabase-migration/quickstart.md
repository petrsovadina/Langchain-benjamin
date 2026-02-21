# Quickstart: Supabase Migration (013)

**Date**: 2026-02-18
**Feature**: [spec.md](./spec.md)
**Prerequisites**: Supabase project with pgvector, Python 3.10+, asyncpg

## 1. Environment Setup

### Copy and fill .env

```bash
cd langgraph-app
cp .env.example .env
```

Add to `.env`:
```bash
# Option A: Direct connection string (RECOMMENDED)
DATABASE_URL=postgresql://postgres:zOr3gt60kbKourMJ@db.higziqzcjmtmkzxbbzik.supabase.co:5432/postgres?sslmode=require

# Option B: Supabase-style (alternative)
# SUPABASE_URL=https://higziqzcjmtmkzxbbzik.supabase.co
# SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  (service role key)
```

### Verify connection

```bash
cd langgraph-app
PYTHONPATH=src python -c "
from agent.utils.guidelines_storage import get_pool
import asyncio
pool = asyncio.run(get_pool())
print(f'Connected! Pool size: {pool.get_size()}')
asyncio.run(pool.close())
"
```

Expected output: `Connected! Pool size: 2`

## 2. Verify Schema

```bash
PYTHONPATH=src python -c "
from agent.utils.guidelines_storage import get_pool
import asyncio

async def check():
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(\"\"\"
            SELECT count(*) as cnt
            FROM information_schema.columns
            WHERE table_name = 'guidelines'
        \"\"\")
        print(f'Guidelines table has {row[\"cnt\"]} columns')

        row = await conn.fetchrow(\"\"\"
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'guidelines' AND indexname = 'idx_guidelines_embedding'
        \"\"\")
        print(f'HNSW index: {\"EXISTS\" if row else \"MISSING\"}'
        )
    await pool.close()

asyncio.run(check())
"
```

Expected:
```
Guidelines table has 24 columns
HNSW index: EXISTS
```

## 3. Run Tests

### Unit tests (no database needed)

```bash
cd langgraph-app
PYTHONPATH=src uv run pytest tests/unit_tests/utils/test_guidelines_storage.py -v
```

### Integration tests (requires DATABASE_URL or SUPABASE_URL)

```bash
cd langgraph-app
PYTHONPATH=src uv run pytest tests/integration_tests/test_guidelines_storage_integration.py -v
```

### Full test suite

```bash
cd langgraph-app
PYTHONPATH=src uv run pytest tests/ -v
```

Expected: All 442+ tests pass (integration tests run only when DB configured).

## 4. Verify InsForge Removal

```bash
# Should return 0 matches (only spec docs reference it)
grep -ri "insforge" --include="*.py" --include="*.json" --include="*.md" \
  --exclude-dir=specs --exclude-dir=.git .
```

Expected: No output (zero matches).

## 5. Quick Smoke Test

```bash
cd langgraph-app
PYTHONPATH=src python -c "
from agent.utils.guidelines_storage import store_guideline, search_guidelines, delete_guideline_section, get_pool, close_pool
from agent.models.guideline_models import GuidelineSection, GuidelineSource
import asyncio

async def smoke_test():
    # Create test guideline with dummy embedding
    section = GuidelineSection(
        guideline_id='CLS-JEP-2024-999',
        title='Smoke Test Guideline',
        section_name='Test Section',
        content='Testovací obsah pro ověření migrace na Supabase.',
        publication_date='2024-06-15',
        source=GuidelineSource.CLS_JEP,
        url='https://example.com/test',
        metadata={'embedding': [0.1] * 1536}
    )

    # Store
    record_id = await store_guideline(section)
    print(f'Stored: {record_id} (UUID)')

    # Retrieve
    result = await get_guideline_section(guideline_id='CLS-JEP-2024-999')
    print(f'Retrieved: {result[\"title\"]}')

    # Search
    results = await search_guidelines(query=[0.1] * 1536, limit=1)
    print(f'Search results: {len(results)}, top score: {results[0][\"similarity_score\"]:.3f}')

    # Cleanup
    deleted = await delete_guideline_section(guideline_id='CLS-JEP-2024-999')
    print(f'Deleted: {deleted}')

    await close_pool()
    print('Smoke test PASSED')

asyncio.run(smoke_test())
"
```

## Troubleshooting

| Problem | Solution |
|---|---|
| `connection refused` | Check DATABASE_URL host/port, ensure Supabase allows direct connections |
| `SSL required` | Add `?sslmode=require` to DATABASE_URL |
| `relation "guidelines" does not exist` | Check Supabase project has the guidelines table |
| `permission denied` | Use service_role key, not anon key, for INSERT/UPDATE/DELETE |
| `invalid input for enum source_type` | Ensure using valid enum value: `'guidelines'` |
| `column "guideline_id" does not exist` | Migration not applied — old column names in SQL |
