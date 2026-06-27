"""MCP tool definitions matching the architecture's agent‑tool mapping."""

TOOL_DEFINITIONS = [
    {
        "name": "search_docs",
        "description": "Semantic search across the research knowledge base (Pinecone).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query."},
                "top_k": {"type": "integer", "description": "Number of results to return.", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "store_memory",
        "description": "Persist a key-value pair into long‑term agent memory (MongoDB).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_name": {"type": "string", "description": "Agent storing the memory."},
                "key": {"type": "string", "description": "Unique key."},
                "value": {"type": "string", "description": "Value to store."},
            },
            "required": ["agent_name", "key", "value"],
        },
    },
    {
        "name": "retrieve_memory",
        "description": "Retrieve a value from agent memory by agent and key.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_name": {"type": "string", "description": "Agent name."},
                "key": {"type": "string", "description": "Memory key."},
            },
            "required": ["agent_name", "key"],
        },
    },
    {
        "name": "save_report",
        "description": "Save a research report to persistent storage (MongoDB research_history).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {"type": "string", "description": "Research run ID."},
                "topic": {"type": "string", "description": "Research topic."},
                "report": {"type": "string", "description": "Full report markdown."},
                "citations": {
                    "type": "string",
                    "description": "JSON string of citations array.",
                },
            },
            "required": ["run_id", "topic", "report"],
        },
    },
    {
        "name": "load_report",
        "description": "Load a previously saved research report by run ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {"type": "string", "description": "Research run ID."},
            },
            "required": ["run_id"],
        },
    },
    {
        "name": "generate_citations",
        "description": "Format and store a list of citations; return citation data.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "citations": {
                    "type": "string",
                    "description": "JSON string of citation objects (each with title, url, authors, year, summary).",
                },
                "run_id": {"type": "string", "description": "Associated research run ID."},
            },
            "required": ["citations"],
        },
    },
    {
        "name": "summarize",
        "description": "Summarize a text or document (LLM‑based, placeholder).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to summarize."},
                "max_words": {"type": "integer", "description": "Max summary words.", "default": 200},
            },
            "required": ["text"],
        },
    },
    {
        "name": "research_history",
        "description": "List past research runs or retrieve one by run_id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {"type": "string", "description": "Optional run ID for specific run."},
                "limit": {"type": "integer", "description": "Max runs to list.", "default": 20},
            },
        },
    },
    {
        "name": "ping",
        "description": "Health check. Returns 'pong' if the server is reachable.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]