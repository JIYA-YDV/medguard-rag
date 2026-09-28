"""
Sentence-transformer based embedder for document chunks.

Uses a small, fast model (all-MiniLM-L6-v2, 384-dim) that runs on CPU.
This model has strong retrieval performance for its size and is widely
adopted as the default choice for RAG systems.
"""

import logging

from sentence_transformers import SentenceTransformer

from src.config import get_settings
from src.models.retrieval import DocumentChunk

logger = logging.getLogger(__name__)


class ChunkEmbedder:
    """
    Encodes document chunks into dense vector embeddings.

    The model is loaded lazily on first use to avoid slow startup
    when embedding is not needed (e.g., in tests that don't touch it).
    """

    def __init__(self, model_name: str | None = None) -> None:
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy-load the embedding model."""
        if self._model is None:
            logger.info("Loading embedding model: %s", self.model_name)
            self._model = SentenceTransformer(self.model_name)
        return self._model

    @property
    def embedding_dimension(self) -> int:
        """The output dimensionality of the model."""
        return self.model.get_sentence_embedding_dimension()

    def embed_text(self, text: str) -> list[float]:
        """Embed a single string."""
        vector = self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        return vector.tolist()

    def embed_texts(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Embed a batch of strings efficiently."""
        if not texts:
            return []

        vectors = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return [v.tolist() for v in vectors]

    def embed_chunks(
        self, chunks: list[DocumentChunk], batch_size: int = 32
    ) -> list[tuple[DocumentChunk, list[float]]]:
        """
        Embed a batch of DocumentChunk objects.

        Returns a list of (chunk, embedding) tuples, preserving order.
        """
        if not chunks:
            return []

        texts = [c.text for c in chunks]
        embeddings = self.embed_texts(texts, batch_size=batch_size)

        logger.info("Embedded %d chunks", len(chunks))
        return list(zip(chunks, embeddings))