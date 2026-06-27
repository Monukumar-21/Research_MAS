"""MCP Server integrated into FastAPI as an HTTP/JSON‑RPC service."""

import json
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from mcp_layer.tools import TOOL_DEFINITIONS
from mcp_layer.resources import RESOURCE_DEFINITIONS
from memory.mongodb_memory import MongoDBMemory
from memory.pinecone_memory import PineconeMemory
from utils.logger import get_logger
from utils.helpers import generate_id

logger = get_logger(__name__)

# --- JSON‑RPC Request Model ---
class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: dict = {}
    id: int = 1


# --- FastAPI Router ---
def create_mcp_router() -> APIRouter:
    """Build a FastAPI router exposing MCP functionality."""
    router = APIRouter(prefix="/mcp", tags=["MCP"])

    # Lazy backend initialisation (shared across requests)
    mongo: MongoDBMemory | None = None
    pinecone: PineconeMemory | None = None
    _initialized = False

    async def _ensure_backends():
        nonlocal mongo, pinecone, _initialized
        if not _initialized:
            mongo = MongoDBMemory()
            pinecone = PineconeMemory()
            await mongo.initialize()
            await pinecone.initialize()
            _initialized = True

    # --- Tool Listing ---
    @router.get("/tools/list")
    async def list_tools():
        return {"tools": TOOL_DEFINITIONS}

    # --- Resource Listing ---
    @router.get("/resources/list")
    async def list_resources():
        return {"resources": RESOURCE_DEFINITIONS}

    # --- Ping ---
    @router.get("/ping")
    async def ping():
        return {"status": "pong"}

    # --- Single JSON‑RPC endpoint ---
    @router.post("/")
    async def handle_jsonrpc(request: JsonRpcRequest):
        await _ensure_backends()
        method = request.method

        # Tools/call
        if method == "tools/call":
            tool_name = request.params.get("name")
            args = request.params.get("arguments", {})
            try:
                result = await _execute_tool(tool_name, args, mongo, pinecone)
                return {
                    "jsonrpc": "2.0",
                    "result": result,
                    "id": request.id,
                }
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.exception("Tool call failed: %s", tool_name)
                raise HTTPException(status_code=500, detail=f"Tool '{tool_name}' error: {e}")

        # tools/list via JSON‑RPC
        elif method == "tools/list":
            return {"jsonrpc": "2.0", "result": {"tools": TOOL_DEFINITIONS}, "id": request.id}

        # resources/list via JSON‑RPC
        elif method == "resources/list":
            return {"jsonrpc": "2.0", "result": {"resources": RESOURCE_DEFINITIONS}, "id": request.id}

        # resources/read
        elif method == "resources/read":
            uri = request.params.get("uri", "")
            content = await _read_resource(uri, mongo)
            return {"jsonrpc": "2.0", "result": {"contents": [content]}, "id": request.id}

        # Health ping via JSON‑RPC
        elif method == "ping":
            return {"jsonrpc": "2.0", "result": "pong", "id": request.id}

        else:
            raise HTTPException(status_code=404, detail=f"Unknown method: {method}")

    return router


# --- Tool Execution Logic ---
async def _execute_tool(name: str, args: dict, mongo: MongoDBMemory, pinecone: PineconeMemory) -> Any:
    """Dispatch tool call to the correct handler."""
    if mongo is None or mongo.db is None:
        raise ValueError("MongoDB unavailable – cannot execute tool.")
    if pinecone is None or pinecone.index is None and name in ("search_docs",):
        raise ValueError("Pinecone unavailable – cannot execute search tool.")

    # Validate required fields based on schema
    schema = next((t["inputSchema"] for t in TOOL_DEFINITIONS if t["name"] == name), None)
    if schema:
        required = schema.get("required", [])
        for req in required:
            if req not in args or args[req] is None:
                raise ValueError(f"Missing required argument: {req}")

    if name == "search_docs":
        results = await pinecone.query_similar(args["query"], args.get("top_k", 5))
        return {"matches": results}

    elif name == "store_memory":
        await mongo.save_agent_memory(args["agent_name"], args["key"], args["value"])
        return {"status": "stored", "key": args["key"]}

    elif name == "retrieve_memory":
        value = await mongo.get_agent_memory(args["agent_name"], args["key"])
        return {"key": args["key"], "value": value}

    elif name == "save_report":
        run_data = {
            "run_id": args["run_id"],
            "topic": args["topic"],
            "report": args["report"],
            "citations": json.loads(args.get("citations", "[]")),
        }
        await mongo.save_research_run(run_data)
        return {"status": "saved", "run_id": args["run_id"]}

    elif name == "load_report":
        doc = await mongo.get_research_run(args["run_id"])
        if doc is None:
            return {"error": "Run not found", "run_id": args["run_id"]}
        return doc

    elif name == "generate_citations":
        # Parse citations JSON string, store each, return IDs
        citations = json.loads(args["citations"])
        stored = []
        for cit in citations:
            cit_id = generate_id()
            await mongo.save_agent_memory("citations", cit_id, cit)
            stored.append(cit_id)
        return {"citation_ids": stored}

    elif name == "summarize":
        # Placeholder: could call Gemini summarization. For now return truncated.
        text = args["text"]
        max_words = args.get("max_words", 200)
        words = text.split()
        summary = " ".join(words[:max_words])
        return {"summary": summary + ("..." if len(words) > max_words else "")}

    elif name == "research_history":
        run_id = args.get("run_id")
        if run_id:
            doc = await mongo.get_research_run(run_id)
            return {"runs": [doc] if doc else []}
        else:
            runs = await mongo.list_research_runs(args.get("limit", 20))
            return {"runs": runs}

    elif name == "ping":
        return {"pong": True}

    else:
        raise ValueError(f"Unknown tool: {name}")


async def _read_resource(uri: str, mongo: MongoDBMemory) -> dict:
    """Return resource content for a given URI."""
    # Simple mapping – expand as needed
    if uri.startswith("reports://research/"):
        run_id = uri.split("/")[-1]
        doc = await mongo.get_research_run(run_id)
        return {"uri": uri, "mimeType": "text/markdown", "text": doc.get("report", "") if doc else ""}
    elif uri.startswith("memories://research/"):
        mem_id = uri.split("/")[-1]
        # For simplicity, return agent memory for 'system' with that key
        val = await mongo.get_agent_memory("system", mem_id)
        return {"uri": uri, "mimeType": "application/json", "text": json.dumps(val)}
    # Add more mappings...
    return {"uri": uri, "mimeType": "text/plain", "text": "Resource not implemented"}