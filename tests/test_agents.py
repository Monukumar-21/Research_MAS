"""Unit tests for agents."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from agents.supervisor import SupervisorAgent
from agents.planner import PlannerAgent


class TestSupervisorAgent:
    """Tests for the Supervisor Agent."""

    def test_rule_based_routing_no_subtopics(self):
        agent = SupervisorAgent.__new__(SupervisorAgent)
        agent.name = "supervisor"
        state = {"topic": "test", "subtopics": [], "findings": []}
        assert agent._rule_based_routing(state) == "planner"

    def test_rule_based_routing_no_findings(self):
        agent = SupervisorAgent.__new__(SupervisorAgent)
        agent.name = "supervisor"
        state = {"subtopics": ["a"], "findings": []}
        assert agent._rule_based_routing(state) == "retrieval"

    def test_rule_based_routing_no_memory(self):
        agent = SupervisorAgent.__new__(SupervisorAgent)
        agent.name = "supervisor"
        state = {"subtopics": ["a"], "findings": [{"x": 1}], "memory_stored": False}
        assert agent._rule_based_routing(state) == "memory_agent"

    def test_rule_based_routing_no_draft(self):
        agent = SupervisorAgent.__new__(SupervisorAgent)
        agent.name = "supervisor"
        state = {"subtopics": ["a"], "findings": [{"x": 1}], "memory_stored": True, "report_draft": ""}
        assert agent._rule_based_routing(state) == "writer"

    def test_rule_based_routing_no_review(self):
        agent = SupervisorAgent.__new__(SupervisorAgent)
        agent.name = "supervisor"
        state = {"subtopics": ["a"], "findings": [{"x": 1}], "memory_stored": True, "report_draft": "draft", "critic_review": None}
        assert agent._rule_based_routing(state) == "critic"

    def test_rule_based_routing_finish(self):
        agent = SupervisorAgent.__new__(SupervisorAgent)
        agent.name = "supervisor"
        state = {
            "subtopics": ["a"], "findings": [{"x": 1}], "memory_stored": True,
            "report_draft": "draft", "critic_review": {"verdict": "approve"},
            "citations_done": True, "revision_count": 0, "max_revisions": 2,
        }
        assert agent._rule_based_routing(state) == "finish"

    def test_rule_based_routing_revision(self):
        agent = SupervisorAgent.__new__(SupervisorAgent)
        agent.name = "supervisor"
        state = {
            "subtopics": ["a"], "findings": [{"x": 1}], "memory_stored": True,
            "report_draft": "draft", "critic_review": {"verdict": "reject"},
            "citations_done": False, "revision_count": 0, "max_revisions": 2,
        }
        assert agent._rule_based_routing(state) == "writer"

    def test_build_state_summary(self):
        agent = SupervisorAgent.__new__(SupervisorAgent)
        agent.name = "supervisor"
        state = {
            "topic": "AI", "subtopics": ["ML"], "findings": [],
            "memory_stored": False, "report_draft": "", "critic_review": None,
            "revision_count": 0, "citations_done": False,
        }
        summary = agent._build_state_summary(state)
        assert "AI" in summary
        assert "1 generated" in summary
