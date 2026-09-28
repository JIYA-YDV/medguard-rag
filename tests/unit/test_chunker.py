"""Tests for the document chunker."""

import pytest

from src.ingestion.chunker import DocumentChunker
from src.ingestion.parser import ParsedDocument, ParsedSection


@pytest.fixture
def small_chunker() -> DocumentChunker:
    """Chunker with small chunk sizes for easy testing."""
    return DocumentChunker(chunk_size=100, chunk_overlap=20, min_chunk_size=10)


@pytest.fixture
def sample_document() -> ParsedDocument:
    """A document with two well-structured sections."""
    return ParsedDocument(
        source="test",
        title="Test Drug",
        url="http://test.com/drug",
        category="medication",
        sections=[
            ParsedSection(
                heading="Overview",
                normalized_section="overview",
                text=(
                    "Test Drug is a common medication used for pain relief. "
                    "It is available over the counter in most pharmacies. "
                    "Millions of people use it every day worldwide safely. "
                    "The active ingredient blocks certain pain receptors. "
                    "It works within thirty minutes of ingestion in most people."
                ),
            ),
            ParsedSection(
                heading="Side Effects",
                normalized_section="side_effects",
                text=(
                    "Common side effects include nausea and dizziness in some patients. "
                    "Serious side effects are rare but can occur in vulnerable groups. "
                    "Contact your doctor if symptoms persist beyond seventy two hours."
                ),
            ),
        ],
    )


class TestChunkerInit:
    """Test chunker configuration."""

    def test_uses_config_defaults(self):
        chunker = DocumentChunker()
        assert chunker.chunk_size > 0
        assert chunker.chunk_overlap >= 0
        assert chunker.chunk_overlap < chunker.chunk_size

    def test_rejects_overlap_larger_than_size(self):
        with pytest.raises(ValueError):
            DocumentChunker(chunk_size=100, chunk_overlap=100)

    def test_rejects_overlap_equal_to_size(self):
        with pytest.raises(ValueError):
            DocumentChunker(chunk_size=100, chunk_overlap=100)


class TestCountTokens:
    """Test token counting."""

    def test_counts_simple_text(self, small_chunker):
        assert small_chunker.count_tokens("hello world") > 0

    def test_empty_string_zero_tokens(self, small_chunker):
        assert small_chunker.count_tokens("") == 0

    def test_longer_text_more_tokens(self, small_chunker):
        short = small_chunker.count_tokens("hi")
        long = small_chunker.count_tokens("hello world this is a longer piece of text")
        assert long > short


class TestSentenceSplitting:
    """Test the internal sentence splitter."""

    def test_splits_on_periods(self, small_chunker):
        text = "First sentence. Second sentence. Third sentence."
        sentences = small_chunker._split_into_sentences(text)
        assert len(sentences) == 3

    def test_splits_on_question_marks(self, small_chunker):
        text = "Is this a question? Yes it is. Another one?"
        sentences = small_chunker._split_into_sentences(text)
        assert len(sentences) == 3

    def test_empty_text_no_sentences(self, small_chunker):
        assert small_chunker._split_into_sentences("") == []


class TestChunkText:
    """Test the core chunking logic."""

    def test_short_text_becomes_single_chunk(self, small_chunker):
        text = "This is short. Nothing more here."
        chunks = small_chunker._chunk_text(text)
        assert len(chunks) == 1

    def test_long_text_produces_multiple_chunks(self, small_chunker):
        # Generate enough text to exceed chunk_size=100 tokens
        sentence = "This is a medical sentence about pharmaceutical treatments. "
        text = sentence * 30
        chunks = small_chunker._chunk_text(text)
        assert len(chunks) > 1

    def test_chunks_respect_token_limit(self, small_chunker):
        sentence = "This is a medical sentence about pharmaceutical treatments. "
        text = sentence * 30
        chunks = small_chunker._chunk_text(text)

        for chunk in chunks:
            # Allow small slack for boundary sentences that would have overflowed
            assert small_chunker.count_tokens(chunk) <= small_chunker.chunk_size * 1.5


class TestChunkDocument:
    """Test full document chunking."""

    def test_chunks_all_sections(self, small_chunker, sample_document):
        chunks = small_chunker.chunk_document(sample_document)
        assert len(chunks) >= 2  # at least one per section

    def test_preserves_source_metadata(self, small_chunker, sample_document):
        chunks = small_chunker.chunk_document(sample_document)

        for chunk in chunks:
            assert chunk.source == "test"
            assert chunk.document_title == "Test Drug"
            assert chunk.source_url == "http://test.com/drug"

    def test_preserves_section_metadata(self, small_chunker, sample_document):
        chunks = small_chunker.chunk_document(sample_document)
        sections = {c.section for c in chunks}
        assert "overview" in sections
        assert "side_effects" in sections

    def test_chunk_ids_unique(self, small_chunker, sample_document):
        chunks = small_chunker.chunk_document(sample_document)
        ids = [c.chunk_index for c in chunks]
        assert len(set(ids)) == len(ids)

    def test_chunk_ids_have_source_prefix(self, small_chunker, sample_document):
        chunks = small_chunker.chunk_document(sample_document)
        for chunk in chunks:
            assert chunk.chunk_id.startswith("test-")

    def test_token_counts_populated(self, small_chunker, sample_document):
        chunks = small_chunker.chunk_document(sample_document)
        for chunk in chunks:
            assert chunk.token_count > 0
            assert chunk.token_count >= small_chunker.min_chunk_size

    def test_empty_document_produces_no_chunks(self, small_chunker):
        doc = ParsedDocument(
            source="test", title="Empty", url="http://test.com",
            category="medication", sections=[],
        )
        chunks = small_chunker.chunk_document(doc)
        assert chunks == []