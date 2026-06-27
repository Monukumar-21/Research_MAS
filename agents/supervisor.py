"""Supervisor Agent: orchestrates the workflow and routes tasks."""

from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import BaseAgent


SUPERVISOR_SYSTEM_PROMPT = """You are the Supervisor Agent of a Multi-Agent Academic Research Platform.

Your role is to:
1. Analyze the current state of the research workflow
2. Decide which agent should execute next
3. Provide routing instructions

Available agents:
- planner: Breaks research topic into subtopics and search queries
- retrieval: Searches for and retrieves relevant documents
- memory_agent: Stores and retrieves information from memory systems
- writer: Generates structured research reports
- critic: Reviews report quality and detects issues
- citation: Organizes and formats references

Current workflow state will be provided. Respond with ONLY the next agent name to route to.

Rules:
- If no subtopics exist yet, route to "planner"
- If subtopics exist but no research findings, route to "retrieval"
- If findings exist but haven't been stored, route to "memory_agent"
- If findings are stored but no report draft exists, route to "writer"
- If a draft exists but hasn't been reviewed, route to "critic"
- If the critic approved OR max revisions reached, route to "citation"
- If the critic rejected and revisions remain, route to "writer"
- If citations are done, route to "FINISH"

Respond with exactly one word: the agent name or FINISH."""


class SupervisorAgent(BaseAgent):
    """Orchestrator that decides which agent runs next."""

    def __init__(self, mcp_client=None, api_key: str | None = None, provider: str = "gemini") -> None:
        super().__init__("supervisor", mcp_client, api_key=api_key, provider=provider)

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """Determine the next agent to execute."""
        self.logger.info("Supervisor evaluating workflow state")

        # Build state summary for the LLM
        state_summary = self._build_state_summary(state)

        messages = [
            SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
            HumanMessage(content=f"Current workflow state:\n{state_summary}\n\nWhich agent should execute next?"),
        ]

        response = await self.llm.ainvoke(messages)
        next_agent = response.content.strip().lower().replace('"', "").replace("'", "")

        # Validate the response
        valid_agents = {"planner", "retrieval", "memory_agent", "writer", "critic", "citation", "finish"}
        if next_agent not in valid_agents:
            # Fallback to rule-based routing
            next_agent = self._rule_based_routing(state)

        self.logger.info("Supervisor routing to: %s", next_agent)

        # Track agent activity
        activity_log = state.get("agent_activity", [])
        activity_log.append({
            "agent": "supervisor",
            "action": f"Routing to {next_agent}",
            "step": len(activity_log) + 1,
        })

        return {
            **state,
            "next_agent": next_agent,
            "agent_activity": activity_log,
        }

    def _build_state_summary(self, state: dict[str, Any]) -> str:
        """Create a concise summary of the current state."""
        parts = [f"Topic: {state.get('topic', 'Not set')}"]

        subtopics = state.get("subtopics", [])
        parts.append(f"Subtopics: {len(subtopics)} generated" if subtopics else "Subtopics: None")

        findings = state.get("findings", [])
        parts.append(f"Findings: {len(findings)} collected" if findings else "Findings: None")

        parts.append(f"Memory stored: {state.get('memory_stored', False)}")

        draft = state.get("report_draft", "")
        parts.append(f"Report draft: {'Yes' if draft else 'No'}")

        review = state.get("critic_review")
        if review:
            parts.append(f"Critic review: {review.get('verdict', 'pending')}")
        else:
            parts.append("Critic review: Not done")

        parts.append(f"Revision count: {state.get('revision_count', 0)}")
        parts.append(f"Citations done: {state.get('citations_done', False)}")

        return "\n".join(parts)

    def _rule_based_routing(self, state: dict[str, Any]) -> str:
        """Deterministic fallback routing based on state."""
        if not state.get("subtopics"):
            return "planner"
        if not state.get("findings"):
            return "retrieval"
        if not state.get("memory_stored"):
            return "memory_agent"
        if not state.get("report_draft"):
            return "writer"
        if not state.get("critic_review"):
            return "critic"

        review = state.get("critic_review", {})
        revision_count = state.get("revision_count", 0)
        max_revisions = state.get("max_revisions", 2)

        if review.get("verdict") == "reject" and revision_count < max_revisions:
            return "writer"
        if not state.get("citations_done"):
            return "citation"
        return "finish"
