"""Writer Agent: generates structured research reports."""

from typing import Any
import json
from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import BaseAgent


WRITER_PROMPT = """You are an Academic Research Writer Agent. Generate a comprehensive, well-structured
research report based on the provided findings.

Topic: {topic}
Research Plan: {research_plan}
Subtopics: {subtopics}

Research Findings:
{findings}

{revision_feedback}

Write a professional academic research report with the following structure:
1. **Title** - A clear, descriptive title
2. **Abstract** - 150-200 word summary
3. **Introduction** - Background and motivation
4. **Literature Review** - Key findings organized by subtopic
5. **Analysis** - Critical analysis of the findings
6. **Key Insights** - Numbered list of important takeaways
7. **Future Directions** - Open questions and research opportunities
8. **Conclusion** - Summary of the report

Use markdown formatting. Be thorough, analytical, and cite sources where available.
Target length: 2000-3000 words."""


class WriterAgent(BaseAgent):
    """Generates structured academic research reports."""

    def __init__(self, mcp_client=None, api_key: str | None = None, provider: str = "gemini") -> None:
        super().__init__("writer", mcp_client, api_key=api_key, provider=provider)

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """Generate or revise a research report."""
        topic = state.get("topic", "")
        findings = state.get("findings", [])
        subtopics = state.get("subtopics", [])
        research_plan = state.get("research_plan", "")
        revision_count = state.get("revision_count", 0)

        # Check for critic feedback
        revision_feedback = ""
        critic_review = state.get("critic_review")
        if critic_review and critic_review.get("verdict") == "reject":
            revision_feedback = f"""
REVISION REQUIRED (Attempt {revision_count + 1}):
Previous feedback from the Critic Agent:
{critic_review.get('feedback', '')}

Issues to address:
{json.dumps(critic_review.get('issues', []), indent=2)}

Please revise the report to address these issues while maintaining the overall structure.
Previous draft for reference:
{state.get('report_draft', '')[:3000]}
"""

        findings_text = ""
        for i, f in enumerate(findings):
            findings_text += f"\n[{i+1}] {f.get('summary', '')}\n    Source: {f.get('source', 'N/A')}\n    Subtopic: {f.get('subtopic', 'General')}\n"

        prompt = self._format_prompt(
            WRITER_PROMPT,
            topic=topic,
            research_plan=research_plan,
            subtopics=json.dumps(subtopics),
            findings=findings_text or "No specific findings available. Write based on general knowledge.",
            revision_feedback=revision_feedback,
        )

        self.logger.info("Generating report draft (revision %d)", revision_count)

        messages = [
            SystemMessage(content="You are an expert academic writer producing high-quality research reports."),
            HumanMessage(content=prompt),
        ]

        response = await self.llm.ainvoke(messages)
        report_draft = response.content.strip()

        activity = state.get("agent_activity", [])
        action = "Generated initial report draft" if revision_count == 0 else f"Revised report (revision {revision_count})"
        activity.append({
            "agent": "writer",
            "action": action,
            "step": len(activity) + 1,
        })

        return {
            **state,
            "report_draft": report_draft,
            "revision_count": revision_count + (1 if revision_feedback else 0),
            "critic_review": None,  # Reset for new review
            "agent_activity": activity,
        }
