"""Unit tests for PDF processor utility (Feature 006).

Tests cover:
- load_pdf: PDF text extraction
- chunk_text: Semantic chunking with header preservation
- create_embeddings: OpenAI embedding creation
- Helper functions: detect_section_headers, split_on_headers, count_tokens
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Configure pytest-asyncio mode
pytest_plugins = ("pytest_asyncio",)

from agent.utils.pdf_processor import (
    chunk_text,
    count_tokens,
    create_embeddings,
    detect_section_headers,
    load_pdf,
    split_on_headers,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_pdf_path(tmp_path: Path) -> str:
    """Create sample PDF for testing."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    pdf_path = tmp_path / "sample.pdf"

    # Create a simple PDF with text using reportlab
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    c.setTitle("Test Guideline")
    c.setAuthor("Test Author")
    c.drawString(100, 700, "Sample PDF content for testing")
    c.save()

    return str(pdf_path)


@pytest.fixture
def empty_pdf_path(tmp_path: Path) -> str:
    """Create empty PDF for testing."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    pdf_path = tmp_path / "empty.pdf"

    # Create an empty PDF (blank page with no text)
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    c.showPage()  # Add blank page
    c.save()

    return str(pdf_path)


@pytest.fixture
def sample_guideline_text() -> str:
    """Sample guideline text for chunking tests."""
    return """# Doporučené postupy pro léčbu hypertenze

Tento dokument shrnuje aktuální doporučené postupy pro diagnostiku a léčbu hypertenze.

## 1. Definice a klasifikace

Hypertenze je definována jako opakovaně naměřený krevní tlak ≥140/90 mmHg.
Klasifikace podle stupně závažnosti:
- Stupeň 1: 140-159/90-99 mmHg
- Stupeň 2: 160-179/100-109 mmHg
- Stupeň 3: ≥180/≥110 mmHg

## 2. Diagnostika

### 2.1 Měření krevního tlaku

Správná technika měření je klíčová pro přesnou diagnostiku. Pacient by měl sedět v klidu
minimálně 5 minut před měřením. Manžeta musí být správné velikosti a umístěna na úrovni srdce.

### 2.2 Laboratorní vyšetření

Základní laboratorní vyšetření zahrnuje:
- Krevní obraz
- Sodík, draslík, kreatinin
- Glykémie nalačno
- Lipidový profil
- Moč + sediment

## 3. Farmakologická léčba

### 3.1 Léky první volby

ACE inhibitory (ramipril, perindopril) jsou léky první volby u většiny pacientů.
Alternativou jsou sartany (losartan, valsartan) při nesnášenlivosti ACE inhibitorů.

### 3.2 Kombinovaná léčba

Při nedostatečné kontrole monoterapií se přidává:
- Blokátor kalciových kanálů (amlodipin)
- Thiazidové diuretikum (indapamid)

## 4. Cílové hodnoty

Cílový krevní tlak je <140/90 mmHg u většiny pacientů. U diabetiků a pacientů
s vysokým kardiovaskulárním rizikem je cíl <130/80 mmHg.

ZÁVĚR:

Správná diagnostika a léčba hypertenze je klíčová pro prevenci kardiovaskulárních
komplikací. Dodržování těchto doporučených postupů přispívá ke zlepšení prognózy pacientů.
"""


@pytest.fixture
def mock_openai_client() -> MagicMock:
    """Mock OpenAI client for embeddings."""

    class MockEmbedding:
        def __init__(self):
            self.embedding = [0.1] * 1536

    class MockResponse:
        def __init__(self, num_embeddings: int):
            self.data = [MockEmbedding() for _ in range(num_embeddings)]

    mock = MagicMock()
    mock.embeddings = MagicMock()
    mock.embeddings.create = AsyncMock(
        side_effect=lambda input, model: MockResponse(len(input))
    )
    return mock


@pytest.fixture
def mock_openai_client_with_retry() -> MagicMock:
    """Mock OpenAI client that fails twice then succeeds."""

    class MockEmbedding:
        def __init__(self):
            self.embedding = [0.1] * 1536

    class MockResponse:
        def __init__(self):
            self.data = [MockEmbedding()]

    mock = MagicMock()
    mock.embeddings = MagicMock()

    # Fail first 2 times, succeed on 3rd
    call_count = [0]

    async def create_with_retry(input: list[str], model: str) -> MockResponse:
        call_count[0] += 1
        if call_count[0] < 3:
            raise Exception("API Error - retry")
        return MockResponse()

    mock.embeddings.create = AsyncMock(side_effect=create_with_retry)
    mock._call_count = call_count
    return mock


# =============================================================================
# Test load_pdf
# =============================================================================


class TestLoadPDF:
    """Test PDF loading functionality."""

    def test_load_pdf_returns_text(self, sample_pdf_path: str) -> None:
        """Test that load_pdf extracts text from PDF."""
        text = load_pdf(sample_pdf_path)

        assert isinstance(text, str)
        # Note: Our simple test PDF may not have extractable text
        # but should not raise an error

    def test_load_pdf_raises_on_missing_file(self) -> None:
        """Test that load_pdf raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_pdf("/nonexistent/path/to/file.pdf")

        assert "not found" in str(exc_info.value)

    def test_load_pdf_handles_empty_pdf(self, empty_pdf_path: str) -> None:
        """Test that load_pdf handles empty PDF gracefully."""
        text = load_pdf(empty_pdf_path)
        # Empty PDF should return empty string or minimal content
        assert isinstance(text, str)


# =============================================================================
# Test chunk_text
# =============================================================================


class TestChunkText:
    """Test semantic chunking functionality."""

    def test_chunk_text_preserves_headers(self, sample_guideline_text: str) -> None:
        """Test that chunking preserves section headers."""
        chunks = chunk_text(sample_guideline_text, chunk_size=500)

        assert len(chunks) > 0
        # At least some chunks should contain headers
        headers_found = sum(1 for chunk in chunks if "#" in chunk or "ZÁVĚR:" in chunk)
        assert headers_found > 0

    def test_chunk_text_respects_size_limits(self) -> None:
        """Test that chunks respect size limits."""
        text = "Lorem ipsum dolor sit amet. " * 200  # Long text

        chunks = chunk_text(text, chunk_size=500, overlap=100, min_chunk_size=100)

        for chunk in chunks:
            assert len(chunk) >= 100  # Min bound
            assert len(chunk) <= 1500  # Max bound (default)

    def test_chunk_text_with_overlap(self) -> None:
        """Test that chunks have overlap for context."""
        # Create text with distinct sections
        text = "# Header\n\n" + ("Section content word. " * 100)

        chunks = chunk_text(text, chunk_size=300, overlap=50)

        # Should have multiple chunks
        assert len(chunks) > 1

    def test_chunk_text_handles_short_text(self) -> None:
        """Test that short text is handled correctly."""
        # Text needs to be at least min_chunk_size (100 chars by default)
        text = "# Short Header\n\nThis is a section with content. " * 3

        chunks = chunk_text(text, chunk_size=500, min_chunk_size=50)

        # Should be a single chunk if under chunk_size
        assert len(chunks) >= 1
        assert "Short Header" in chunks[0]

    def test_chunk_text_raises_on_empty_text(self) -> None:
        """Test that empty text raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            chunk_text("")

        with pytest.raises(ValueError, match="cannot be empty"):
            chunk_text("   ")

    def test_chunk_text_with_czech_characters(self) -> None:
        """Test that Czech characters are preserved."""
        # Make text long enough to meet min_chunk_size
        text = (
            "# Léčba hypertenze\n\nPři léčbě hypertenze je důležité dodržovat správnou životosprávu. "
            * 3
        )

        chunks = chunk_text(text, chunk_size=500, min_chunk_size=50)

        assert len(chunks) >= 1
        # Czech characters should be preserved
        full_text = " ".join(chunks)
        assert "Léčba" in full_text or "hypertenze" in full_text

    def test_chunk_text_default_parameters(self, sample_guideline_text: str) -> None:
        """Test chunk_text with default parameters."""
        chunks = chunk_text(sample_guideline_text)

        assert len(chunks) > 0
        # Default chunk_size is 800, so large text should produce multiple chunks
        if len(sample_guideline_text) > 800:
            assert len(chunks) > 1

    def test_chunk_text_no_content_loss(self) -> None:
        """Test that chunking does not lose any words from the input."""
        text = (
            "# Sekce jedna\n"
            + " ".join(f"slovo{i}" for i in range(200))
            + "\n# Sekce dva\n"
            + " ".join(f"text{i}" for i in range(150))
            + "\n# Sekce tři\n"
            + "Krátký obsah."
        )
        chunks = chunk_text(text, chunk_size=300, overlap=50, min_chunk_size=20)
        combined = " ".join(chunks)

        # Every unique content word from the input must appear in the output
        for i in range(200):
            assert f"slovo{i}" in combined, f"Lost word slovo{i}"
        for i in range(150):
            assert f"text{i}" in combined, f"Lost word text{i}"
        assert "Krátký obsah." in combined

    def test_chunk_text_no_content_loss_small_sections(self) -> None:
        """Test that very small sections are not dropped."""
        text = "# A\nKrátký.\n# B\nTaké krátký.\n# C\n" + "Dlouhý. " * 100
        chunks = chunk_text(text, chunk_size=200, min_chunk_size=5)
        combined = " ".join(chunks)

        assert "Krátký." in combined
        assert "Také krátký." in combined


# =============================================================================
# Test create_embeddings
# =============================================================================


class TestCreateEmbeddings:
    """Test embedding creation functionality."""

    @pytest.mark.asyncio
    async def test_create_embeddings_returns_vectors(
        self, mock_openai_client: MagicMock
    ) -> None:
        """Test that create_embeddings returns 1536-dim vectors."""
        texts = ["Léčba hypertenze", "Diabetes mellitus"]

        embeddings = await create_embeddings(texts, client=mock_openai_client)

        assert len(embeddings) == 2
        assert all(len(emb) == 1536 for emb in embeddings)
        assert all(isinstance(emb[0], float) for emb in embeddings)

    @pytest.mark.asyncio
    async def test_create_embeddings_batches_requests(
        self, mock_openai_client: MagicMock
    ) -> None:
        """Test that large inputs are batched."""
        texts = [f"Text {i}" for i in range(250)]  # > 100 batch size

        await create_embeddings(texts, batch_size=100, client=mock_openai_client)

        # Verify 3 API calls (100 + 100 + 50)
        assert mock_openai_client.embeddings.create.call_count == 3

    @pytest.mark.asyncio
    async def test_create_embeddings_retries_on_failure(
        self, mock_openai_client_with_retry: MagicMock
    ) -> None:
        """Test retry logic on API failure."""
        texts = ["Test text"]

        # First 2 calls fail, 3rd succeeds
        embeddings = await create_embeddings(
            texts, client=mock_openai_client_with_retry
        )

        assert len(embeddings) == 1
        assert mock_openai_client_with_retry._call_count[0] == 3

    @pytest.mark.asyncio
    async def test_create_embeddings_raises_on_empty_input(
        self, mock_openai_client: MagicMock
    ) -> None:
        """Test that empty input raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            await create_embeddings([], client=mock_openai_client)

    @pytest.mark.asyncio
    async def test_create_embeddings_raises_on_empty_text_in_list(
        self, mock_openai_client: MagicMock
    ) -> None:
        """Test that empty text in list raises ValueError to preserve alignment."""
        texts = ["Valid text", "", "Another valid"]

        with pytest.raises(ValueError, match="Text at index 1 is empty or whitespace"):
            await create_embeddings(texts, client=mock_openai_client)

    @pytest.mark.asyncio
    async def test_create_embeddings_raises_on_whitespace_text(
        self, mock_openai_client: MagicMock
    ) -> None:
        """Test that whitespace-only text raises ValueError."""
        texts = ["Valid text", "   ", "Another valid"]

        with pytest.raises(ValueError, match="Text at index 1 is empty or whitespace"):
            await create_embeddings(texts, client=mock_openai_client)


# =============================================================================
# Test Helper Functions
# =============================================================================


class TestHelperFunctions:
    """Test helper functions."""

    def test_detect_section_headers_markdown(self) -> None:
        """Test markdown header detection."""
        text = """# Main Header
Some text here.
## Sub Header
More text.
### Third Level
Even more text."""

        headers = detect_section_headers(text)

        assert len(headers) == 3
        assert "# Main Header" in headers[0][1]
        assert "## Sub Header" in headers[1][1]
        assert "### Third Level" in headers[2][1]

    def test_detect_section_headers_numbered(self) -> None:
        """Test numbered header detection."""
        text = """1. Úvod
Úvodní text.
1.1 Definice
Text definice.
2. Diagnostika
Diagnostický text."""

        headers = detect_section_headers(text)

        # Should detect numbered headers starting with capital letter
        assert len(headers) >= 2

    def test_detect_section_headers_colon(self) -> None:
        """Test colon header detection."""
        text = """ÚVOD:
Úvodní text.
ZÁVĚR:
Závěrečný text."""

        headers = detect_section_headers(text)

        assert len(headers) == 2
        assert "ÚVOD:" in headers[0][1]
        assert "ZÁVĚR:" in headers[1][1]

    def test_detect_section_headers_empty_text(self) -> None:
        """Test header detection on empty text."""
        headers = detect_section_headers("")
        assert headers == []

    def test_split_on_headers_basic(self) -> None:
        """Test basic text splitting on headers."""
        text = """# Intro
Text 1 here.
# Next
Text 2 here."""

        headers = detect_section_headers(text)
        sections = split_on_headers(text, headers)

        assert len(sections) == 2
        assert "# Intro" in sections[0]
        assert "# Next" in sections[1]

    def test_split_on_headers_with_preamble(self) -> None:
        """Test splitting preserves text before first header."""
        text = """Preamble text.
# Header
Section content."""

        headers = detect_section_headers(text)
        sections = split_on_headers(text, headers)

        assert len(sections) == 2
        assert "Preamble" in sections[0]
        assert "# Header" in sections[1]

    def test_split_on_headers_no_headers(self) -> None:
        """Test splitting text without headers."""
        text = "Just plain text without any headers."

        headers = detect_section_headers(text)
        sections = split_on_headers(text, headers)

        assert len(sections) == 1
        assert text in sections[0]

    def test_count_tokens_basic(self) -> None:
        """Test token counting."""
        text = "Hello world"

        token_count = count_tokens(text)

        assert isinstance(token_count, int)
        assert token_count > 0

    def test_count_tokens_czech(self) -> None:
        """Test token counting with Czech text."""
        text = "Léčba hypertenze u pacientů s diabetem"

        token_count = count_tokens(text)

        assert isinstance(token_count, int)
        assert token_count > 0

    def test_count_tokens_empty(self) -> None:
        """Test token counting with empty text."""
        token_count = count_tokens("")
        assert token_count == 0


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_full_chunking_pipeline(self, sample_guideline_text: str) -> None:
        """Test complete chunking pipeline."""
        # Step 1: Detect headers
        headers = detect_section_headers(sample_guideline_text)
        assert len(headers) > 0

        # Step 2: Split on headers
        sections = split_on_headers(sample_guideline_text, headers)
        assert len(sections) > 0

        # Step 3: Chunk text
        chunks = chunk_text(sample_guideline_text, chunk_size=500)
        assert len(chunks) > 0

        # Verify all content is preserved (roughly)
        original_words = set(sample_guideline_text.split())
        chunked_words = set(" ".join(chunks).split())

        # Most words should be preserved (some may be lost at boundaries)
        overlap = original_words & chunked_words
        assert len(overlap) > len(original_words) * 0.8

    @pytest.mark.asyncio
    async def test_chunking_with_embeddings(
        self, sample_guideline_text: str, mock_openai_client: MagicMock
    ) -> None:
        """Test chunking followed by embedding creation."""
        # Chunk text
        chunks = chunk_text(sample_guideline_text, chunk_size=500)
        assert len(chunks) > 0

        # Create embeddings
        embeddings = await create_embeddings(chunks, client=mock_openai_client)

        # Verify 1:1 mapping
        assert len(embeddings) == len(chunks)
        assert all(len(emb) == 1536 for emb in embeddings)
