"""MCP resource definitions – matching the architecture diagram."""

RESOURCE_DEFINITIONS = [
    {
        "uri": "memories://research/{id}",
        "name": "Research Memory Entry",
        "description": "Retrieve a specific memory entry for a research run.",
        "mimeType": "application/json",
    },
    {
        "uri": "documents://research/{id}",
        "name": "Research Document",
        "description": "Retrieve a stored document by ID.",
        "mimeType": "application/json",
    },
    {
        "uri": "reports://research/{id}",
        "name": "Research Report",
        "description": "Retrieve a generated report by run ID.",
        "mimeType": "text/markdown",
    },
    {
        "uri": "citations://research/{id}",
        "name": "Research Citations",
        "description": "Retrieve citation data for a research run.",
        "mimeType": "application/json",
    },
    {
        "uri": "agents://{agent_id}/state",
        "name": "Agent State",
        "description": "Current state of a specific agent.",
        "mimeType": "application/json",
    },
]