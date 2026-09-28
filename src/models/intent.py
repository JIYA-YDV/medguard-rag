"""
Intent classification and risk assessment models.
"""

from enum import Enum

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Risk levels for medical queries, ordered by severity."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IntentCategory(str, Enum):
    """
    Possible intent categories for medical queries.

    Each maps to one or more safety policies.
    """

    GENERAL_INFORMATION = "general_information"
    MEDICATION_INFORMATION = "medication_information"
    SYMPTOM_INQUIRY = "symptom_inquiry"
    DOSAGE_REQUEST = "dosage_request"
    DIAGNOSIS_REQUEST = "diagnosis_request"
    TREATMENT_RECOMMENDATION = "treatment_recommendation"
    DRUG_INTERACTION = "drug_interaction"
    EMERGENCY = "emergency"
    MENTAL_HEALTH_CRISIS = "mental_health_crisis"
    PEDIATRIC = "pediatric"
    PREGNANCY = "pregnancy"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    OFF_TOPIC = "off_topic"
    PROMPT_INJECTION = "prompt_injection"


class IntentResult(BaseModel):
    """Result of intent classification and risk assessment."""

    intent: IntentCategory
    risk_level: RiskLevel
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(
        ...,
        description="Brief explanation of why this intent and risk were assigned",
    )
    requires_escalation: bool = Field(
        default=False,
        description="Whether this query requires immediate escalation (emergency/crisis)",
    )