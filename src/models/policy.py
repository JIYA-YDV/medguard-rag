"""
Policy definition and decision models.

Policies are defined in YAML files and loaded at startup.
Policy decisions are deterministic — no LLM involvement.
"""

from enum import Enum

from pydantic import BaseModel, Field


class PolicyAction(str, Enum):
    """Actions a policy can mandate."""

    ALLOW = "allow"
    DENY = "deny"
    ESCALATE = "escalate"
    MODIFY = "modify"


class PolicyDefinition(BaseModel):
    """A single safety policy loaded from YAML."""

    policy_id: str = Field(..., pattern=r"^(MED|SEC)-\d{3}$", examples=["MED-001"])
    name: str
    description: str
    version: str = "1.0"

    # Matching criteria
    triggered_by: list[str] = Field(
        ...,
        description="List of IntentCategory values that trigger this policy",
    )
    min_risk_level: str = Field(
        ...,
        description="Minimum RiskLevel required to trigger",
    )

    # Actions
    action: PolicyAction
    response_template: str | None = Field(
        default=None,
        description="Pre-built response for DENY/ESCALATE actions",
    )
    required_disclaimers: list[str] = Field(default_factory=list)
    constraints: dict[str, bool] = Field(
        default_factory=dict,
        description="Constraints applied to LLM generation when action is ALLOW or MODIFY",
    )

    # Metadata
    rationale: str = Field(
        default="",
        description="Why this policy exists — for audit and documentation",
    )
    severity: str = Field(default="standard", pattern="^(standard|elevated|critical)$")


class PolicyDecision(BaseModel):
    """The result of evaluating a query against all applicable policies."""

    is_allowed: bool
    action: PolicyAction
    matched_policies: list[str] = Field(
        default_factory=list,
        description="List of policy IDs that matched",
    )
    applied_policy: str | None = Field(
        default=None,
        description="The highest-priority policy that determined the final action",
    )
    response_template: str | None = Field(
        default=None,
        description="Pre-built response if action is DENY or ESCALATE",
    )
    required_disclaimers: list[str] = Field(default_factory=list)
    constraints: dict[str, bool] = Field(default_factory=dict)
    reasoning: str = Field(
        default="",
        description="Explanation of why this decision was made",
    )