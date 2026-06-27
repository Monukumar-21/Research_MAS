"""Retrieval Agent: searches the web and knowledge base for relevant information."""

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base import BaseAgent
from utils.helpers import generate_id, truncate_text

try:
    from duckduckgo_search import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False


SYNTHESIS_PROMPT = """You are a Research Retrieval Agent. Synthesize the following search results
into structured research findings.

Topic: {topic}
Subtopics: {subtopics}

Search Results:
{search_results}

For each relevant finding, provide:
1. A clear summary of the key information
2. The source URL if available
3. How it relates to the research subtopics

Format your response as a JSON array of objects with keys: "summary", "source", "subtopic", "relevance_score" (0-1).
Respond with ONLY valid JSON. No markdown fences."""


class RetrievalAgent(BaseAgent):
    """Searches web and vector store for relevant research material."""

    def __init__(self, mcp_client=None, api_key: str | None = None, provider: str = "gemini") -> None:
        super().__init__("retrieval", mcp_client, api_key=api_key, provider=provider)

    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """Search for and retrieve relevant documents."""
        topic = state.get("topic", "")
        queries = state.get("search_queries", [])
        subtopics = state.get("subtopics", [])

        self.logger.info("Retrieving documents for %d queries", len(queries))

        # Step 1: Search the existing knowledge base via MCP
        kb_results = []
        for query in queries[:3]:
            result = await self.call_mcp_tool("document_retrieval", {"query": query, "top_k": 3})
            kb_results.extend(result.get("results", []))

        # Step 2: Web search using DuckDuckGo
        web_results = []
        if HAS_DDGS:
            ddgs = DDGS()
            for query in queries:
                try:
                    results = ddgs.text(query, max_results=3)
                    for r in results:
                        web_results.append({
                            "title": r.get("title", ""),
                            "body": r.get("body", ""),
                            "href": r.get("href", ""),
                        })
                except Exception as e:
                    self.logger.warning("DuckDuckGo search failed for '%s': %s", query, e)

        # Step 3: Combine and deduplicate results
        all_results_text = ""
        for i, r in enumerate(web_results[:15]):
            all_results_text += f"\n[{i+1}] Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n"

        for i, r in enumerate(kb_results[:5]):
            idx = len(web_results) + i + 1
            all_results_text += f"\n[{idx}] [Knowledge Base] Score: {r.get('score', 'N/A')}\nContent: {truncate_text(r.get('text', ''), 500)}\n"

        if not all_results_text.strip():
            all_results_text = "No search results found. Generate findings based on your knowledge."

        # Step 4: LLM synthesizes findings
        prompt = self._format_prompt(
            SYNTHESIS_PROMPT,
            topic=topic,
            subtopics=json.dumps(subtopics),
            search_results=truncate_text(all_results_text, 6000),
        )

        messages = [
            SystemMessage(content="You synthesize search results into structured research findings. Always respond with valid JSON."),
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
            findings = json.loads(raw)
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse retrieval output, creating basic findings")
            findings = [
                {
                    "summary": r.get("body", r.get("text", "")),
                    "source": r.get("href", r.get("metadata", {}).get("source", "")),
                    "subtopic": subtopics[0] if subtopics else topic,
                    "relevance_score": 0.7,
                }
                for r in (web_results[:5] + kb_results[:3])
                if r.get("body") or r.get("text")
            ]

        # Step 5: Store documents in vector DB via MCP for future retrieval
        for finding in findings[:10]:
            if finding.get("summary"):
                await self.call_mcp_tool("document_store", {
                    "doc_id": generate_id(),
                    "text": finding["summary"],
                    "source": finding.get("source", ""),
                    "topic": topic,
                })

        activity = state.get("agent_activity", [])
        activity.append({
            "agent": "retrieval",
            "action": f"Found {len(findings)} research findings from {len(web_results)} web + {len(kb_results)} KB results",
            "step": len(activity) + 1,
        })

        return {
            **state,
            "findings": findings,
            "raw_web_results": web_results[:10],
            "agent_activity": activity,
        }
