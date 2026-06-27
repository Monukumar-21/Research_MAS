"""Integration tests for the LangGraph workflow."""

import pytest
from workflows.state import ResearchState


class TestResearchState:
    """Tests for the state schema."""

    def test_state_creation(self):
        state: ResearchState = {
            "topic": "Test Topic",
            "run_id": "abc123",
            "session_id": "sess123",
            "subtopics": [],
            "search_queries": [],
            "findings": [],
            "memory_stored": False,
            "report_draft": "",
            "revision_count": 0,
            "max_revisions": 2,
            "critic_review": None,
            "citations": [],
            "citations_done": False,
            "final_report": "",
            "status": "running",
            "next_agent": "",
            "agent_activity": [],
        }
        assert state["topic"] == "Test Topic"
        assert state["status"] == "running"

    def test_state_defaults(self):
        state: ResearchState = {"topic": "Minimal"}
        assert state["topic"] == "Minimal"
