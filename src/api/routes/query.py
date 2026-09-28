"""
Query endpoint — the main entry point for medical information queries.

Currently returns a placeholder response. The full pipeline will be
wired in Phase 7 (Pipeline Orchestration).
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from src.config import get_settings
from src.models.intent import IntentCategory, RiskLevel
from src.models.policy import PolicyAction
from src.models.request import QueryRequest
from src.models.response import GuardLog, PolicyLog, QueryResponse

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    """
    Process a medical information query through the safety pipeline.

    Pipeline stages (to be implemented):
    1. Input Guard — prompt injection and PII detection
    2. Intent Classification — what does the user want?
    3. Policy Evaluation — is this query allowed?
    4. Retrieval — find relevant documents (if allowed)
    5. Reranking — reorder by relevance
    6. Generation — produce grounded, cited answer
    7. Output Guard — verify response safety
    8. Response Assembly — package with citations and disclaimers
    """
    settings = get_settings()

    if len(request.query) > settings.max_query_length:
        raise HTTPException(
            status_code=400,
            detail=f"Query exceeds maximum length of {settings.max_query_length} characters",
        )

    # Placeholder response until pipeline is implemented
    return QueryResponse(
        answer=(
            "The MedGuard RAG pipeline is not yet fully implemented. "
            "This is a placeholder response from Phase 1 (Foundation). "
            "The full retrieval and generation pipeline will be available "
            "after Phase 7."
        ),
        risk_level=RiskLevel.LOW,
        policy_log=PolicyLog(
            intent_detected=IntentCategory.GENERAL_INFORMATION,
            risk_level=RiskLevel.LOW,
            classification_confidence=0.0,
            matched_policies=[],
            action_taken=PolicyAction.ALLOW,
            reasoning="Placeholder — pipeline not yet implemented",
        ),
        guard_log=GuardLog(),
        query_id=f"q-{uuid.uuid4().hex[:12]}",
        timestamp=datetime.now(timezone.utc),
    )