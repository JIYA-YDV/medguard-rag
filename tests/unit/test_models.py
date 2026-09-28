"""Tests for Pydantic data models."""

import pytest

from src.models.intent import IntentCategory, IntentResult, RiskLevel
from src.models.policy import PolicyAction, PolicyDecision, PolicyDefinition
from src.models.request import QueryRequest
from src.models.response import Citation, GuardLog, PolicyLog, QueryResponse
from src.models.retrieval import DocumentChunk, RetrievedChunk


class TestQueryRequest:
    """Test QueryRequest validation."""

    def test_valid_query(self):
        req = QueryRequest(query="What is ibuprofen?")
        assert req.query == "What is ibuprofen?"
        assert req.session_id is None

    def test_query_with_session(self):
        req = QueryRequest(query="What is aspirin?", session_id="sess-123")
        assert req.session_id == "sess-123"

    def test_empty_query_rejected(self):
        with pytest.raises(ValueError):
            QueryRequest(query="")

    def test_query_too_long_rejected(self):
        with pytest.raises(ValueError):
            QueryRequest(query="a" * 501)


class TestIntentResult:
    """Test IntentResult validation."""

    def test_valid_intent_result(self):
        result = IntentResult(
            intent=IntentCategory.GENERAL_INFORMATION,
            risk_level=RiskLevel.LOW,
            confidence=0.95,
            reasoning="User asking general question about a medication",
        )
        assert result.intent == IntentCategory.GENERAL_INFORMATION
        assert result.risk_level == RiskLevel.LOW
        assert result.requires_escalation is False

    def test_emergency_intent(self):
        result = IntentResult(
            intent=IntentCategory.EMERGENCY,
            risk_level=RiskLevel.CRITICAL,
            confidence=0.99,
            reasoning="User describes overdose symptoms",
            requires_escalation=True,
        )
        assert result.requires_escalation is True

    def test_confidence_must_be_bounded(self):
        with pytest.raises(ValueError):
            IntentResult(
                intent=IntentCategory.GENERAL_INFORMATION,
                risk_level=RiskLevel.LOW,
                confidence=1.5,
                reasoning="test",
            )

    def test_confidence_cannot_be_negative(self):
        with pytest.raises(ValueError):
            IntentResult(
                intent=IntentCategory.GENERAL_INFORMATION,
                risk_level=RiskLevel.LOW,
                confidence=-0.1,
                reasoning="test",
            )


class TestPolicyDefinition:
    """Test PolicyDefinition validation."""

    def test_valid_policy(self):
        policy = PolicyDefinition(
            policy_id="MED-001",
            name="General Information",
            description="Allow general health information queries",
            triggered_by=["general_information", "medication_information"],
            min_risk_level="low",
            action=PolicyAction.ALLOW,
            required_disclaimers=["Consult a healthcare professional"],
        )
        assert policy.policy_id == "MED-001"
        assert policy.action == PolicyAction.ALLOW

    def test_invalid_policy_id_format(self):
        with pytest.raises(ValueError):
            PolicyDefinition(
                policy_id="INVALID-1",
                name="Test",
                description="Test",
                triggered_by=["general_information"],
                min_risk_level="low",
                action=PolicyAction.ALLOW,
            )

    def test_security_policy_id(self):
        policy = PolicyDefinition(
            policy_id="SEC-001",
            name="Prompt Injection",
            description="Block prompt injection attempts",
            triggered_by=["prompt_injection"],
            min_risk_level="low",
            action=PolicyAction.DENY,
        )
        assert policy.policy_id == "SEC-001"


class TestPolicyDecision:
    """Test PolicyDecision model."""

    def test_allowed_decision(self):
        decision = PolicyDecision(
            is_allowed=True,
            action=PolicyAction.ALLOW,
            matched_policies=["MED-001"],
            applied_policy="MED-001",
            required_disclaimers=["Consult a healthcare professional"],
            reasoning="General information query, low risk",
        )
        assert decision.is_allowed is True

    def test_denied_decision(self):
        decision = PolicyDecision(
            is_allowed=False,
            action=PolicyAction.DENY,
            matched_policies=["MED-002", "MED-004"],
            applied_policy="MED-004",
            response_template="Please consult your doctor for dosage recommendations.",
            reasoning="Dosage request requires professional guidance",
        )
        assert decision.is_allowed is False
        assert decision.response_template is not None


class TestDocumentChunk:
    """Test DocumentChunk model."""

    def test_valid_chunk(self):
        chunk = DocumentChunk(
            chunk_id="medlineplus-ibuprofen-001",
            text="Ibuprofen is used to reduce fever and treat pain...",
            source="medlineplus",
            source_url="https://medlineplus.gov/druginfo/meds/a682159.html",
            document_title="Ibuprofen",
            section="overview",
            chunk_index=0,
            token_count=128,
        )
        assert chunk.source == "medlineplus"

    def test_chunk_index_must_be_non_negative(self):
        with pytest.raises(ValueError):
            DocumentChunk(
                chunk_id="test",
                text="test",
                source="test",
                source_url="http://test.com",
                document_title="test",
                chunk_index=-1,
                token_count=10,
            )


class TestRetrievedChunk:
    """Test RetrievedChunk with scores."""

    def test_retrieved_chunk_with_all_scores(self):
        chunk = DocumentChunk(
            chunk_id="test-001",
            text="Test chunk text",
            source="nhs",
            source_url="https://nhs.uk/test",
            document_title="Test",
            chunk_index=0,
            token_count=50,
        )
        retrieved = RetrievedChunk(
            chunk=chunk,
            vector_score=0.85,
            bm25_score=12.3,
            rrf_score=0.034,
            reranker_score=0.92,
            final_rank=1,
        )
        assert retrieved.final_rank == 1
        assert retrieved.vector_score == 0.85


class TestQueryResponse:
    """Test complete response model."""

    def test_minimal_response(self):
        response = QueryResponse(
            answer="Ibuprofen is a nonsteroidal anti-inflammatory drug.",
            risk_level=RiskLevel.LOW,
            policy_log=PolicyLog(
                intent_detected=IntentCategory.GENERAL_INFORMATION,
                risk_level=RiskLevel.LOW,
                classification_confidence=0.95,
                matched_policies=["MED-001"],
                action_taken=PolicyAction.ALLOW,
                reasoning="General information query",
            ),
            guard_log=GuardLog(),
            query_id="q-12345",
        )
        assert response.answer is not None
        assert response.guard_log.input_guard_passed is True

    def test_response_with_citations(self):
        response = QueryResponse(
            answer="Ibuprofen is used to treat pain and fever.",
            citations=[
                Citation(
                    source="medlineplus",
                    title="Ibuprofen",
                    url="https://medlineplus.gov/druginfo/meds/a682159.html",
                    relevance_score=0.92,
                ),
            ],
            disclaimers=["Consult a healthcare professional"],
            risk_level=RiskLevel.LOW,
            policy_log=PolicyLog(
                intent_detected=IntentCategory.MEDICATION_INFORMATION,
                risk_level=RiskLevel.LOW,
                classification_confidence=0.93,
                matched_policies=["MED-001"],
                action_taken=PolicyAction.ALLOW,
                reasoning="Medication info query",
            ),
            guard_log=GuardLog(),
            query_id="q-12346",
        )
        assert len(response.citations) == 1
        assert len(response.disclaimers) == 1