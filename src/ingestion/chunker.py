"""
Token-aware document chunker.

Splits parsed documents into overlapping chunks of approximately
CHUNK_SIZE tokens with CHUNK_OVERLAP token overlap. Preserves section
metadata so retrieved chunks carry their document context.
"""

import logging
import uuid
from datetime import datetime, timezone

import tiktoken

from src.config import get_settings
from src.ingestion.parser import ParsedDocument
from src.models.retrieval import DocumentChunk

logger = logging.getLogger(__name__)


class DocumentChunker:
    """
    Chunks parsed documents into embeddings-ready pieces.

    Uses tiktoken (cl100k_base — used by GPT-4) for accurate token counting.
    Splits happen at sentence boundaries when possible to preserve semantic
    coherence.
    """

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        min_chunk_size: int | None = None,
    ) -> None:
        settings = get_settings()
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self.min_chunk_size = min_chunk_size or settings.min_chunk_size

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                f"chunk_overlap ({self.chunk_overlap}) must be less than "
                f"chunk_size ({self.chunk_size})"
            )

        self.encoder = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in a string."""
        return len(self.encoder.encode(text))

    def _split_into_sentences(self, text: str) -> list[str]:
        """
        Rough sentence splitter.

        Not perfect (doesn't handle abbreviations like "Dr." or "e.g."
        elegantly), but sufficient for medical prose which is mostly
        well-structured. Preserves the period at sentence end.
        """
        # Split on . ! ? followed by whitespace and capital letter
        import re
        parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
        return [p.strip() for p in parts if p.strip()]

    def _chunk_text(self, text: str) -> list[str]:
        """
        Split text into token-bounded chunks with overlap.

        Strategy: pack sentences into a chunk until adding the next would
        exceed chunk_size. Then start a new chunk with the last few
        sentences (for overlap).
        """
        sentences = self._split_into_sentences(text)
        if not sentences:
            return []

        chunks: list[str] = []
        current_sentences: list[str] = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)

            # If a single sentence exceeds chunk_size, we still emit it
            # rather than dropping content
            if sentence_tokens > self.chunk_size:
                if current_sentences:
                    chunks.append(" ".join(current_sentences))
                    current_sentences = []
                    current_tokens = 0
                chunks.append(sentence)
                continue

            if current_tokens + sentence_tokens > self.chunk_size:
                # Finalize current chunk
                chunks.append(" ".join(current_sentences))

                # Start new chunk with overlap (last N sentences that fit)
                overlap_sentences = self._build_overlap(current_sentences)
                current_sentences = overlap_sentences
                current_tokens = sum(self.count_tokens(s) for s in overlap_sentences)

            current_sentences.append(sentence)
            current_tokens += sentence_tokens

        # Flush remainder
        if current_sentences:
            chunks.append(" ".join(current_sentences))

        return chunks

    def _build_overlap(self, sentences: list[str]) -> list[str]:
        """
        Build the overlap prefix for the next chunk.

        Selects trailing sentences up to chunk_overlap tokens.
        """
        overlap: list[str] = []
        tokens = 0
        for sentence in reversed(sentences):
            s_tokens = self.count_tokens(sentence)
            if tokens + s_tokens > self.chunk_overlap:
                break
            overlap.insert(0, sentence)
            tokens += s_tokens
        return overlap

    def chunk_document(self, document: ParsedDocument) -> list[DocumentChunk]:
        """
        Chunk a parsed document, preserving section metadata per chunk.
        """
        chunks: list[DocumentChunk] = []
        chunk_index = 0

        for section in document.sections:
            text_chunks = self._chunk_text(section.text)

            for text in text_chunks:
                token_count = self.count_tokens(text)
                if token_count < self.min_chunk_size:
                    continue

                chunk_id = (
                    f"{document.source}-"
                    f"{section.normalized_section}-"
                    f"{uuid.uuid4().hex[:8]}"
                )

                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        text=text,
                        source=document.source,
                        source_url=document.url,
                        document_title=document.title,
                        section=section.normalized_section,
                        chunk_index=chunk_index,
                        token_count=token_count,
                    )
                )
                chunk_index += 1

        logger.info(
            "Chunked '%s' into %d chunks",
            document.title, len(chunks),
        )
        return chunks