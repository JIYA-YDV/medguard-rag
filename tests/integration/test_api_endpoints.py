"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.config import get_settings


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    get_settings.cache_clear()
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_healthy_status(self, client):
        data = client.get("/health").json()
        assert data["status"] == "healthy"

    def test_health_includes_service_name(self, client):
        data = client.get("/health").json()
        assert data["service"] == "MedGuard RAG"

    def test_health_includes_components(self, client):
        data = client.get("/health").json()
        assert "components" in data
        assert "api" in data["components"]
        assert data["components"]["api"] == "healthy"

    def test_health_includes_timestamp(self, client):
        data = client.get("/health").json()
        assert "timestamp" in data


class TestQueryEndpoint:
    """Tests for POST /api/v1/query."""

    def test_query_returns_200_for_valid_request(self, client):
        response = client.post(
            "/api/v1/query",
            json={"query": "What is ibuprofen used for?"},
        )
        assert response.status_code == 200

    def test_query_returns_response_structure(self, client):
        data = client.post(
            "/api/v1/query",
            json={"query": "What is ibuprofen?"},
        ).json()

        assert "answer" in data
        assert "citations" in data
        assert "risk_level" in data
        assert "policy_log" in data
        assert "guard_log" in data
        assert "query_id" in data

    def test_query_returns_policy_log(self, client):
        data = client.post(
            "/api/v1/query",
            json={"query": "What is aspirin?"},
        ).json()

        policy_log = data["policy_log"]
        assert "intent_detected" in policy_log
        assert "risk_level" in policy_log
        assert "action_taken" in policy_log

    def test_query_rejects_empty_body(self, client):
        response = client.post("/api/v1/query", json={})
        assert response.status_code == 422

    def test_query_rejects_empty_string(self, client):
        response = client.post("/api/v1/query", json={"query": ""})
        assert response.status_code == 422

    def test_query_rejects_too_long_string(self, client):
        response = client.post(
            "/api/v1/query",
            json={"query": "a" * 501},
        )
        assert response.status_code == 422

    def test_query_id_is_unique(self, client):
        r1 = client.post("/api/v1/query", json={"query": "test query 1"}).json()
        r2 = client.post("/api/v1/query", json={"query": "test query 2"}).json()
        assert r1["query_id"] != r2["query_id"]