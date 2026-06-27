"""Pydantic models for API request/response validation."""

from pydantic import BaseModel, Field
from typing import Any


class ResearchRequest(BaseModel):
    """Request to start a new research workflow."""
    topic: str = Field(..., min_length=3, max_length=500, description="Research topic")
    max_revisions: int = Field(default=2, ge=0, le=5, description="Max revision rounds")
    api_key: str | None = Field(default=None, description="User provided API key")
    provider: str = Field(default="gemini", description="LLM Provider (gemini, openai, anthropic, grok, groq)")


class ResearchResponse(BaseModel):
    """Response containing the research results."""
    run_id: str
    session_id: str
    topic: str
    status: str
    final_report: str = ""
    citations: list[dict[str, Any]] = []
    agent_activity: list[dict[str, Any]] = []
    critic_review: dict[str, Any] | None = None


class ResearchStatusResponse(BaseModel):
    """Status of a research run."""
    run_id: str
    status: str
    current_agent: str = ""
    progress_pct: float = 0.0


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    services: dict[str, str]


class ResearchHistoryItem(BaseModel):
    """Summary of a past research run."""
    run_id: str
    topic: str
    timestamp: str
