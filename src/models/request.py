"""
Inbound request models.
"""

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Incoming query from the user."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The user's health information query",
        examples=["What is ibuprofen used for?"],
    )
    session_id: str | None = Field(
        default=None,
        description="Optional session ID for audit logging. Does NOT enable conversation memory.",
    )