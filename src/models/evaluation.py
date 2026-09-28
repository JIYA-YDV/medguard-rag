"""
Evaluation framework data models.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class EvalTestCase(BaseModel):
    """A single evaluation test case."""

    test_id: str
    query: str
    expected_intent: str
    expected_risk_level: str
    expected_action: str  # allow, deny, escalate
    expected_keywords: list[str] = Field(default_factory=list)
    category: str = Field(
        default="general",
        description="Test category: safe, blocked, emergency, injection, ambiguous",
    )


class EvalResult(BaseModel):
    """Result of running a single evaluation test case."""

    test_id: str
    passed: bool
    actual_intent: str | None = None
    actual_risk_level: str | None = None
    actual_action: str | None = None
    intent_match: bool = False
    risk_match: bool = False
    action_match: bool = False
    response_snippet: str = ""
    error: str | None = None
    latency_ms: int | None = None


class EvalSummary(BaseModel):
    """Summary of an evaluation run."""

    run_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_tests: int
    passed: int
    failed: int
    pass_rate: float = Field(..., ge=0.0, le=1.0)

    # Category breakdowns
    safety_compliance_rate: float = Field(
        ..., ge=0.0, le=1.0,
        description="Percentage of unsafe queries correctly blocked",
    )
    retrieval_relevance: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Average retrieval relevance score",
    )
    emergency_escalation_rate: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Percentage of emergency queries correctly escalated",
    )
    injection_resistance_rate: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Percentage of injection attempts correctly blocked",
    )

    results: list[EvalResult] = Field(default_factory=list)