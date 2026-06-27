"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Multi-Agent Research Platform" in data["message"]


def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_research_validation():
    """Test that empty topic is rejected."""
    response = client.post("/api/v1/research", json={"topic": ""})
    assert response.status_code == 422  # Validation error


def test_research_short_topic():
    """Test that very short topic is rejected."""
    response = client.post("/api/v1/research", json={"topic": "ab"})
    assert response.status_code == 422  # min_length=3
