"""
Outbound response models.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from src.models.intent import IntentCategory, RiskLevel
from src.models.policy import PolicyAction


class Citation(BaseModel):
    """A citation linking a response claim to a source document."""

    source: str
    title: str
    url: str
    section: str = "general"
    relevance_score: float = Field(..., ge=0.0, le=1.0)


class PolicyLog(BaseModel):
    """Transparency log showing which policies were evaluated and applied."""

    intent_detected: IntentCategory
    risk_level: RiskLevel
    classification_confidence: float = Field(..., ge=0.0, le=1.0)
    matched_policies: list[str] = Field(default_factory=list)
    action_taken: PolicyAction
    reasoning: str


class GuardLog(BaseModel):
    """Log of input/output guard evaluations."""

    input_guard_passed: bool = True
    input_guard_flags: list[str] = Field(default_factory=list)
    output_guard_passed: bool = True
    output_guard_flags: list[str] = Field(default_factory=list)


class QueryResponse(BaseModel):
    """Complete response returned to the user."""

    answer: str
    citations: list[Citation] = Field(default_factory=list)
    disclaimers: list[str] = Field(default_factory=list)
    risk_level: RiskLevel
    policy_log: PolicyLog
    guard_log: GuardLog
    query_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    latency_ms: int | None = None