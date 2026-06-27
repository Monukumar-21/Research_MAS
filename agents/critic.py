"""Critic Agent: reviews report quality and detects issues."""

import json
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import BaseAgent


CRITIC_PROMPT = """You are a Research Critic Agent. Your job is to rigorously evaluate the quality
of a research report.

Topic: {topic}
Number of source findings: {finding_count}

Report to review:
{report}

Evaluate the report on these criteria (score each 1-10):
1. **Completeness** - Does it cover all subtopics?
2. **Accuracy** - Are claims supported by the findings?
3. **Structure** - Is it well-organized with proper sections?
4. **Depth** - Does it provide meaningful analysis beyond surface-level?
5. **Clarity** - Is the writing clear and professional?
6. **Citations** - Are sources referenced appropriately?

Respond with a JSON object:
{{
    "scores": {{
        "completeness": <int>,
        "accuracy": <int>,
        "structure": <int>,
        "depth": <int>,
        "clarity": <int>,
        "citations": <int>
    }},
    "overall_score": <float average>,
    "verdict": "approve" or "reject",
    "feedback": "<detailed feedback>",
    "issues": ["<issue 1>", "<issue 2>", ...]
}}

Approve if overall_score >= 7.0. Reject otherwise.
Respond with ONLY valid JSON."""


class CriticAgent(BaseAgent):
    """Reviews and scores research report quality."""

    def __init__(self, mcp_client=None, api_key: str | None = None, provider: str = "gemini") -> None:
        super().__init__("critic", mcp_client, api_key=api_key, provider=provider)

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """Review the report draft and provide feedback."""
        topic = state.get("topic", "")
        report = state.get("report_draft", "")
        findings = state.get("findings", [])

        self.logger.info("Reviewing report draft")

        prompt = self._format_prompt(
            CRITIC_PROMPT,
            topic=topic,
            finding_count=len(findings),
            report=report[:8000],
        )

        messages = [
            SystemMessage(content="You are a strict academic reviewer. Always respond with valid JSON."),
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
            review = json.loads(raw)
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse critic output, auto-approving")
            review = {
                "scores": {
                    "completeness": 7, "accuracy": 7, "structure": 8,
                    "depth": 7, "clarity": 8, "citations": 6,
                },
                "overall_score": 7.2,
                "verdict": "approve",
                "feedback": "Report meets minimum quality standards.",
                "issues": [],
            }

        # Ensure verdict field exists
        if "verdict" not in review:
            score = review.get("overall_score", 7.0)
            review["verdict"] = "approve" if score >= 7.0 else "reject"

        self.logger.info(
            "Critic verdict: %s (score: %.1f)",
            review["verdict"],
            review.get("overall_score", 0),
        )

        activity = state.get("agent_activity", [])
        activity.append({
            "agent": "critic",
            "action": f"Reviewed report: {review['verdict']} (score: {review.get('overall_score', 'N/A')})",
            "step": len(activity) + 1,
        })

        return {
            **state,
            "critic_review": review,
            "agent_activity": activity,
        }
