"""LangGraph state definitions for the research workflow."""

from typing import Any, TypedDict


class ResearchState(TypedDict, total=False):
    """Complete state schema for the research workflow graph."""

    # --- Input ---
    topic: str
    run_id: str
    session_id: str

    # --- Planner outputs ---
    subtopics: list[str]
    search_queries: list[str]
    research_plan: str

    # --- Retrieval outputs ---
    findings: list[dict[str, Any]]
    raw_web_results: list[dict[str, Any]]

    # --- Memory ---
    memory_stored: bool

    # --- Writer outputs ---
    report_draft: str
    revision_count: int
    max_revisions: int

    # --- Critic outputs ---
    critic_review: dict[str, Any] | None

    # --- Citation outputs ---
    citations: list[dict[str, Any]]
    formatted_references: str
    citations_done: bool

    # --- Final ---
    final_report: str
    status: str
    error: str | None

    # --- Routing ---
    next_agent: str

    # --- Observability ---
    agent_activity: list[dict[str, Any]]
