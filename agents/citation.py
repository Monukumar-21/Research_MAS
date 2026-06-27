"""Citation Agent: organizes and formats references."""

import json
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import BaseAgent


CITATION_PROMPT = """You are a Citation Agent. Organize and format all references used in the research report.

Topic: {topic}

Research Findings with Sources:
{findings}

Report Draft (to extract inline references):
{report}

Generate a properly formatted reference list. For each source:
1. Extract the title, authors (if available), URL, and year
2. Format in a consistent academic style

Respond with a JSON object:
{{
    "citations": [
        {{
            "index": 1,
            "title": "...",
            "authors": "...",
            "url": "...",
            "year": "...",
            "accessed": "2024"
        }}
    ],
    "formatted_references": "A markdown-formatted reference section ready to append to the report"
}}

Respond with ONLY valid JSON."""


class CitationAgent(BaseAgent):
    """Organizes and formats research citations."""

    def __init__(self, mcp_client=None, api_key: str | None = None, provider: str = "gemini") -> None:
        super().__init__("citation", mcp_client, api_key=api_key, provider=provider)

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """Generate formatted citations and append to report."""
        topic = state.get("topic", "")
        findings = state.get("findings", [])
        report = state.get("report_draft", "")
        run_id = state.get("run_id", "default")

        self.logger.info("Generating citations for %d findings", len(findings))

        findings_text = ""
        for i, f in enumerate(findings):
            findings_text += f"[{i+1}] Summary: {f.get('summary', '')[:200]}\n    Source: {f.get('source', 'N/A')}\n\n"

        prompt = self._format_prompt(
            CITATION_PROMPT,
            topic=topic,
            findings=findings_text,
            report=report[:4000],
        )

        messages = [
            SystemMessage(content="You are a precise citation formatting assistant. Always respond with valid JSON."),
            HumanMessage(content=prompt),
        ]

        response = await self.llm.ainvoke(messages)
        raw = response.content.strip()

        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()

        try:
            citation_data = json.loads(raw)
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse citation output, creating basic citations")
            citation_data = {
                "citations": [
                    {"index": i + 1, "title": f.get("source", "Unknown"), "url": f.get("source", ""), "authors": "", "year": "2024"}
                    for i, f in enumerate(findings) if f.get("source")
                ],
                "formatted_references": "## References\n\nSee inline citations above.",
            }

        citations = citation_data.get("citations", [])
        formatted_refs = citation_data.get("formatted_references", "")

        # Store citations via MCP
        for cit in citations:
            await self.call_mcp_tool("citation_add", {
                "title": cit.get("title", ""),
                "url": cit.get("url", ""),
                "authors": cit.get("authors", ""),
                "year": cit.get("year", ""),
                "summary": "",
            })

        # Append references to report
        final_report = report
        if formatted_refs:
            final_report = report + "\n\n---\n\n" + formatted_refs

        # Save final report via MCP
        await self.call_mcp_tool("report_storage", {
            "run_id": run_id,
            "topic": topic,
            "report": final_report,
            "citations": json.dumps(citations),
        })

        activity = state.get("agent_activity", [])
        activity.append({
            "agent": "citation",
            "action": f"Added {len(citations)} citations and saved final report",
            "step": len(activity) + 1,
        })

        return {
            **state,
            "citations": citations,
            "formatted_references": formatted_refs,
            "final_report": final_report,
            "citations_done": True,
            "agent_activity": activity,
        }
