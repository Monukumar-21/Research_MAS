"""Research Planner Agent: decomposes topics into subtopics and queries."""

import json
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import BaseAgent


PLANNER_PROMPT = """You are a Research Planner Agent. Your job is to break down a research topic into
well-defined subtopics and generate effective search queries.

Given the research topic, produce a JSON object with:
1. "subtopics": A list of 3-5 specific subtopics to investigate
2. "search_queries": A list of 5-8 search queries to find relevant papers and articles
3. "research_plan": A brief paragraph describing the research approach

Topic: {topic}

Respond with ONLY valid JSON. No markdown, no code fences."""


class PlannerAgent(BaseAgent):
    """Breaks research topics into actionable subtopics and queries."""

    def __init__(self, mcp_client=None, api_key: str | None = None, provider: str = "gemini") -> None:
        super().__init__("planner", mcp_client, api_key=api_key, provider=provider)

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """Generate subtopics and search queries for the research topic."""
        topic = state.get("topic", "")
        self.logger.info("Planning research for: %s", topic)

        prompt = self._format_prompt(PLANNER_PROMPT, topic=topic)
        messages = [
            SystemMessage(content="You are a precise research planning assistant. Always respond with valid JSON."),
            HumanMessage(content=prompt),
        ]

        response = await self.llm.ainvoke(messages)
        raw = response.content.strip()

        # Clean potential markdown fences
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()

        try:
            plan = json.loads(raw)
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse planner output, using fallback")
            plan = {
                "subtopics": [
                    f"Overview of {topic}",
                    f"Recent developments in {topic}",
                    f"Key challenges in {topic}",
                    f"Future directions for {topic}",
                ],
                "search_queries": [
                    f"{topic} recent advances 2024",
                    f"{topic} survey paper",
                    f"{topic} key challenges",
                    f"{topic} state of the art",
                    f"{topic} future research directions",
                ],
                "research_plan": f"Systematic investigation of {topic} covering recent advances, challenges, and future directions.",
            }

        # Store plan in memory via MCP
        await self.call_mcp_tool("research_memory_store", {
            "agent_name": "planner",
            "key": f"plan_{state.get('run_id', 'default')}",
            "value": json.dumps(plan),
        })

        activity = state.get("agent_activity", [])
        activity.append({
            "agent": "planner",
            "action": f"Generated {len(plan.get('subtopics', []))} subtopics and {len(plan.get('search_queries', []))} queries",
            "step": len(activity) + 1,
        })

        return {
            **state,
            "subtopics": plan.get("subtopics", []),
            "search_queries": plan.get("search_queries", []),
            "research_plan": plan.get("research_plan", ""),
            "agent_activity": activity,
        }
