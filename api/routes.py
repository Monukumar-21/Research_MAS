"""FastAPI route handlers."""

from fastapi import APIRouter, HTTPException

from api.schemas import (
    ResearchRequest,
    ResearchResponse,
    HealthResponse,
    ResearchHistoryItem,
)
from workflows.graph import build_research_graph
from memory.sqlite_memory import SQLiteMemory
from memory.mongodb_memory import MongoDBMemory
from utils.logger import get_logger
from utils.helpers import generate_id

logger = get_logger(__name__)
router = APIRouter()

# Singletons
_sqlite = SQLiteMemory()
_mongo = MongoDBMemory()


@router.on_event("startup")
async def startup():
    await _sqlite.initialize()
    await _mongo.initialize()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        services={
            "sqlite": "connected",
            "mongodb": "connected" if _mongo.db is not None else "degraded",
            "api": "running",
        },
    )


@router.post("/research", response_model=ResearchResponse)
async def start_research(request: ResearchRequest):
    """Start a new research workflow."""
    run_id = generate_id()
    session_id = await _sqlite.create_session(request.topic)

    logger.info("Starting research: run=%s topic=%s", run_id, request.topic)

    # Build initial state
    initial_state = {
        "topic": request.topic,
        "run_id": run_id,
        "session_id": session_id,
        "subtopics": [],
        "search_queries": [],
        "research_plan": "",
        "findings": [],
        "raw_web_results": [],
        "memory_stored": False,
        "report_draft": "",
        "revision_count": 0,
        "max_revisions": request.max_revisions,
        "critic_review": None,
        "citations": [],
        "formatted_references": "",
        "citations_done": False,
        "final_report": "",
        "status": "running",
        "error": None,
        "next_agent": "",
        "agent_activity": [],
    }

    try:
        graph = build_research_graph(request.api_key, request.provider)
        final_state = await graph.ainvoke(initial_state)

        await _sqlite.update_session_status(session_id, "completed")
        await _sqlite.add_message(session_id, "user", request.topic)
        await _sqlite.add_message(session_id, "assistant", final_state.get("final_report", ""))

        return ResearchResponse(
            run_id=run_id,
            session_id=session_id,
            topic=request.topic,
            status=final_state.get("status", "completed"),
            final_report=final_state.get("final_report", ""),
            citations=final_state.get("citations", []),
            agent_activity=final_state.get("agent_activity", []),
            critic_review=final_state.get("critic_review"),
        )

    except Exception as e:
        logger.error("Research workflow failed: %s", e, exc_info=True)
        await _sqlite.update_session_status(session_id, "failed")
        raise HTTPException(status_code=500, detail=f"Research workflow failed: {str(e)}")


@router.get("/research/history", response_model=list[ResearchHistoryItem])
async def get_research_history():
    """Get list of past research runs."""
    runs = await _mongo.list_research_runs(limit=20)
    return [
        ResearchHistoryItem(
            run_id=r.get("run_id", ""),
            topic=r.get("topic", ""),
            timestamp=r.get("timestamp", ""),
        )
        for r in runs
    ]


@router.get("/research/{run_id}", response_model=ResearchResponse)
async def get_research_run(run_id: str):
    """Get details of a specific research run."""
    run = await _mongo.get_research_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Research run not found")

    import json
    citations = run.get("citations", "[]")
    if isinstance(citations, str):
        try:
            citations = json.loads(citations)
        except json.JSONDecodeError:
            citations = []

    return ResearchResponse(
        run_id=run.get("run_id", run_id),
        session_id=run.get("session_id", ""),
        topic=run.get("topic", ""),
        status="completed",
        final_report=run.get("report", ""),
        citations=citations,
        agent_activity=[],
    )
