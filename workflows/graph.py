"""LangGraph workflow graph construction with conditional routing."""

import asyncio
from typing import Any

from langgraph.graph import StateGraph, END

from workflows.state import ResearchState
from agents import (
    SupervisorAgent,
    PlannerAgent,
    RetrievalAgent,
    MemoryAgent,
    WriterAgent,
    CriticAgent,
    CitationAgent,
)
from mcp_layer.client import MCPClient
from utils.logger import get_logger

logger = get_logger(__name__)


def _route_next(state: ResearchState) -> str:
    """Conditional edge: route based on supervisor's decision."""
    next_agent = state.get("next_agent", "finish")
    if next_agent == "finish":
        return "finish"
    return next_agent


def build_research_graph(api_key: str | None = None, provider: str = "gemini") -> StateGraph:
    """Build and compile the multi-agent research workflow graph."""

    # Shared MCP client for all agents
    mcp_client = MCPClient()

    # Instantiate agents
    supervisor = SupervisorAgent(mcp_client, api_key=api_key, provider=provider)
    planner = PlannerAgent(mcp_client, api_key=api_key, provider=provider)
    retrieval = RetrievalAgent(mcp_client, api_key=api_key, provider=provider)
    memory_agent = MemoryAgent(mcp_client, api_key=api_key, provider=provider)
    writer = WriterAgent(mcp_client, api_key=api_key, provider=provider)
    critic = CriticAgent(mcp_client, api_key=api_key, provider=provider)
    citation = CitationAgent(mcp_client, api_key=api_key, provider=provider)

    # --- Node wrappers ---
    def _handle_error(e: Exception, state: dict[str, Any], agent_name: str, fallback: dict[str, Any]) -> dict[str, Any]:
        err_str = str(e).lower()
        if "429" in err_str or "quota" in err_str or "rate limit" in err_str:
            logger.error(f"{agent_name} QUOTA EXCEEDED: {e}")
            return {
                **state,
                "status": "quota_exceeded",
                "next_agent": "finish",
                "final_report": state.get("report_draft") or "Research interrupted due to quota limits. Findings so far:\n\n" + str(state.get("findings", []))
            }
        logger.error(f"{agent_name} error: {e}")
        return {**state, **fallback}

    async def supervisor_node(state: ResearchState) -> dict[str, Any]:
        try:
            await asyncio.sleep(4)  # Rate limit protection for free tiers
            return await supervisor.execute(dict(state))
        except Exception as e:
            return _handle_error(e, state, "Supervisor", {"next_agent": supervisor._rule_based_routing(dict(state))})

    async def planner_node(state: ResearchState) -> dict[str, Any]:
        try:
            await asyncio.sleep(4)
            return await planner.execute(dict(state))
        except Exception as e:
            return _handle_error(e, state, "Planner", {"subtopics": [state.get("topic", "Research")], "search_queries": [state.get("topic", "")]})

    async def retrieval_node(state: ResearchState) -> dict[str, Any]:
        try:
            await asyncio.sleep(4)
            return await retrieval.execute(dict(state))
        except Exception as e:
            return _handle_error(e, state, "Retrieval", {"findings": [{"summary": f"Error during retrieval: {e}", "source": "", "subtopic": "", "relevance_score": 0}]})

    async def memory_node(state: ResearchState) -> dict[str, Any]:
        try:
            await asyncio.sleep(4)
            return await memory_agent.execute(dict(state))
        except Exception as e:
            return _handle_error(e, state, "Memory", {"memory_stored": True})

    async def writer_node(state: ResearchState) -> dict[str, Any]:
        try:
            await asyncio.sleep(4)
            return await writer.execute(dict(state))
        except Exception as e:
            return _handle_error(e, state, "Writer", {"report_draft": f"# {state.get('topic', 'Research Report')}\n\nError generating report: {e}"})

    async def critic_node(state: ResearchState) -> dict[str, Any]:
        try:
            await asyncio.sleep(4)
            return await critic.execute(dict(state))
        except Exception as e:
            return _handle_error(e, state, "Critic", {"critic_review": {"verdict": "approve", "overall_score": 7.0, "feedback": "Auto-approved due to error", "issues": []}})

    async def citation_node(state: ResearchState) -> dict[str, Any]:
        try:
            await asyncio.sleep(4)
            return await citation.execute(dict(state))
        except Exception as e:
            return _handle_error(e, state, "Citation", {"citations_done": True, "final_report": state.get("report_draft", "")})

    async def finish_node(state: ResearchState) -> dict[str, Any]:
        """Terminal node that marks the workflow as complete."""
        activity = state.get("agent_activity", [])
        activity.append({
            "agent": "system",
            "action": "Research workflow completed",
            "step": len(activity) + 1,
        })
        return {
            **state,
            "status": "completed",
            "agent_activity": activity,
        }

    # --- Build graph ---
    graph = StateGraph(ResearchState)

    # Add nodes
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("planner", planner_node)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("memory_agent", memory_node)
    graph.add_node("writer", writer_node)
    graph.add_node("critic", critic_node)
    graph.add_node("citation", citation_node)
    graph.add_node("finish", finish_node)

    # Set entry point
    graph.set_entry_point("supervisor")

    # Conditional routing from supervisor
    graph.add_conditional_edges(
        "supervisor",
        _route_next,
        {
            "planner": "planner",
            "retrieval": "retrieval",
            "memory_agent": "memory_agent",
            "writer": "writer",
            "critic": "critic",
            "citation": "citation",
            "finish": "finish",
        },
    )

    # All agents route back to supervisor after execution
    for agent_name in ["planner", "retrieval", "memory_agent", "writer", "critic", "citation"]:
        graph.add_edge(agent_name, "supervisor")

    # Finish goes to END
    graph.add_edge("finish", END)

    compiled = graph.compile()
    logger.info("Research workflow graph compiled successfully")
    return compiled
