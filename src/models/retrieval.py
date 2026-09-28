"""
Retrieval pipeline data models.
"""

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """A chunk of a medical document stored in the vector database."""

    chunk_id: str
    text: str
    source: str = Field(
        ...,
        description="Source database: medlineplus, nhs, dailymed, who",
    )
    source_url: str
    document_title: str
    section: str = Field(
        default="general",
        description="Document section: overview, symptoms, treatment, side_effects, dosage",
    )
    chunk_index: int = Field(..., ge=0)
    token_count: int = Field(..., ge=1)


class RetrievedChunk(BaseModel):
    """A chunk returned by the retrieval pipeline with relevance scores."""

    chunk: DocumentChunk
    vector_score: float | None = Field(default=None, ge=0.0, le=1.0)
    bm25_score: float | None = Field(default=None, ge=0.0)
    rrf_score: float | None = Field(default=None, ge=0.0)
    reranker_score: float | None = Field(default=None)
    final_rank: int = Field(..., ge=1)