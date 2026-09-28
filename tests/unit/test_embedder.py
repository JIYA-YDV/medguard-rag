"""
Tests for the chunk embedder.

These tests are marked slow because they download the model on first run.
"""

import pytest

from src.ingestion.embedder import ChunkEmbedder
from src.models.retrieval import DocumentChunk


@pytest.fixture(scope="module")
def embedder() -> ChunkEmbedder:
    """Module-scoped embedder to avoid reloading the model per test."""
    return ChunkEmbedder()


@pytest.fixture
def sample_chunks() -> list[DocumentChunk]:
    return [
        DocumentChunk(
            chunk_id="test-1",
            text="Ibuprofen is a pain reliever used to treat headaches.",
            source="test",
            source_url="http://test.com",
            document_title="Ibuprofen",
            section="overview",
            chunk_index=0,
            token_count=15,
        ),
        DocumentChunk(
            chunk_id="test-2",
            text="Take with food to reduce stomach irritation and discomfort.",
            source="test",
            source_url="http://test.com",
            document_title="Ibuprofen",
            section="dosage",
            chunk_index=1,
            token_count=12,
        ),
    ]


@pytest.mark.slow
class TestEmbedder:
    """Tests that require loading the sentence-transformer model."""

    def test_embedding_dimension_is_384(self, embedder):
        """all-MiniLM-L6-v2 produces 384-dim vectors."""
        assert embedder.embedding_dimension == 384

    def test_embed_single_text(self, embedder):
        vector = embedder.embed_text("Ibuprofen relieves pain.")
        assert len(vector) == 384
        assert all(isinstance(v, float) for v in vector)

    def test_embed_empty_text_list(self, embedder):
        assert embedder.embed_texts([]) == []

    def test_embed_batch(self, embedder):
        texts = ["hello world", "goodbye world", "medical text"]
        vectors = embedder.embed_texts(texts)
        assert len(vectors) == 3
        assert all(len(v) == 384 for v in vectors)

    def test_embed_chunks_preserves_order(self, embedder, sample_chunks):
        results = embedder.embed_chunks(sample_chunks)
        assert len(results) == 2
        assert results[0][0].chunk_id == "test-1"
        assert results[1][0].chunk_id == "test-2"

    def test_similar_texts_have_similar_embeddings(self, embedder):
        """Sanity check: semantically similar text → similar vectors."""
        import numpy as np

        v1 = np.array(embedder.embed_text("Ibuprofen treats pain and inflammation."))
        v2 = np.array(embedder.embed_text("Ibuprofen is used for pain relief."))
        v3 = np.array(embedder.embed_text("The weather today is sunny and warm."))

        def cosine(a, b):
            return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

        similar_score = cosine(v1, v2)
        different_score = cosine(v1, v3)

        assert similar_score > different_score
        assert similar_score > 0.5