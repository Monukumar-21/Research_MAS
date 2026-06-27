"""Memory Agent: manages storage and retrieval across all memory systems."""

import json
from typing import Any

from agents.base import BaseAgent


class MemoryAgent(BaseAgent):
    """Stores research findings and manages cross-memory operations."""

    def __init__(self, mcp_client=None, api_key: str | None = None, provider: str = "gemini") -> None:
        super().__init__("memory_agent", mcp_client, api_key=api_key, provider=provider)

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """Store findings in long-term memory and vector store."""
        findings = state.get("findings", [])
        topic = state.get("topic", "")
        run_id = state.get("run_id", "default")

        self.logger.info("Storing %d findings in memory", len(findings))

        # Store each finding in long-term memory via MCP
        for i, finding in enumerate(findings):
            key = f"finding_{run_id}_{i}"
            await self.call_mcp_tool("research_memory_store", {
                "agent_name": "memory_agent",
                "key": key,
                "value": json.dumps(finding),
            })

        # Store aggregated findings summary
        summary = {
            "run_id": run_id,
            "topic": topic,
            "finding_count": len(findings),
            "subtopics_covered": list({f.get("subtopic", "") for f in findings}),
        }
        await self.call_mcp_tool("research_memory_store", {
            "agent_name": "memory_agent",
            "key": f"summary_{run_id}",
            "value": json.dumps(summary),
        })

        activity = state.get("agent_activity", [])
        activity.append({
            "agent": "memory_agent",
            "action": f"Stored {len(findings)} findings and summary in long-term memory",
            "step": len(activity) + 1,
        })

        return {
            **state,
            "memory_stored": True,
            "agent_activity": activity,
        }
