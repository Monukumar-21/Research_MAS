# MCP (MODEL CONTEXT PROTOCOL) ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MCP (MODEL CONTEXT PROTOCOL) ARCHITECTURE                 │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                         MCP SERVER                                 │     │
│  │  ┌─────────────────────────────────────────────────────────────┐  │     │
│  │  │                    Tool Registry                            │  │     │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │  │     │
│  │  │  │ search_docs  │  │ store_memory  │  │ retrieve_memory  │ │  │     │
│  │  │  └──────────────┘  └──────────────┘  └──────────────────┘ │  │     │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │  │     │
│  │  │  │ save_report  │  │ load_report   │  │ gen_citations   │ │  │     │
│  │  │  └──────────────┘  └──────────────┘  └──────────────────┘ │  │     │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │  │     │
│  │  │  │ summarize    │  │ research_hist │  │ classify_content│ │  │     │
│  │  │  └──────────────┘  └──────────────┘  └──────────────────┘ │  │     │
│  │  └─────────────────────────────────────────────────────────────┘  │     │
│  │                                                                    │     │
│  │  ┌─────────────────────────────────────────────────────────────┐  │     │
│  │  │                  Resource Registry                         │  │     │
│  │  │  memories://research/{id}  - Research memory entries       │  │     │
│  │  │  documents://research/{id} - Stored documents              │  │     │
│  │  │  reports://research/{id}   - Generated reports             │  │     │
│  │  │  citations://research/{id} - Citation data                 │  │     │
│  │  │  agents://{agent_id}/state - Agent state data              │  │     │
│  │  └─────────────────────────────────────────────────────────────┘  │     │
│  │                                                                    │     │
│  │  ┌─────────────────────────────────────────────────────────────┐  │     │
│  │  │                 Request/Response Format                    │  │     │
│  │  │  Request:  { "jsonrpc": "2.0", "method": "...",           │  │     │
│  │  │             "params": {}, "id": 1 }                        │  │     │
│  │  │  Response: { "jsonrpc": "2.0", "result": {},              │  │     │
│  │  │             "error": null, "id": 1 }                       │  │     │
│  │  └─────────────────────────────────────────────────────────────┘  │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                    │                                        │
│                           HTTP/JSON-RPC                                      │
│                                    │                                        │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                         MCP CLIENT                                 │     │
│  │                                                                    │     │
│  │  ┌─────────────────────────────────────────────────────────────┐  │     │
│  │  │                     Client Methods                          │  │     │
│  │  │  call_tool(tool_name, params) → result                     │  │     │
│  │  │  list_tools() → tool_definitions                           │  │     │
│  │  │  read_resource(uri) → resource_content                     │  │     │
│  │  │  list_resources() → resource_uris                          │  │     │
│  │  │  ping() → health_check                                     │  │     │
│  │  └─────────────────────────────────────────────────────────────┘  │     │
│  │                                                                    │     │
│  │  Used by ALL agents to access tools and resources                 │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                    AGENT-TOOL MAPPING                              │     │
│  │                                                                    │     │
│  │  Agent        │ Tools Available                                   │     │
│  │  ─────────────┼──────────────────────────────────────────────────  │     │
│  │  Supervisor   │ list_tools, ping, research_history                │     │
│  │  Planner      │ search_docs, retrieve_memory, research_history    │     │
│  │  Retriever    │ search_docs, summarize                            │     │
│  │  Writer       │ retrieve_memory, save_report, load_report,        │     │
│  │               │ generate_citations, summarize                     │     │
│  │  Critic       │ load_report, retrieve_memory, research_history    │     │
│  │  Citation     │ generate_citations, search_docs                   │     │
│  │  Reflection   │ load_report, research_history                     │     │
│  │  Memory       │ store_memory, retrieve_memory, summarize          │     │
│  └────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
```depl