# COMPLETE PROJECT FOLDER STRUCTURE

```
multi-agent-research-platform/
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py                    # Abstract base agent
│   ├── supervisor_agent.py              # Supervisor orchestrator
│   ├── planner_agent.py                 # Research planner
│   ├── retriever_agent.py               # Document retriever
│   ├── writer_agent.py                  # Report writer
│   ├── critic_agent.py                  # Output verifier
│   ├── reflection_agent.py              # Report reviewer
│   ├── citation_agent.py                # Citation generator
│   └── memory_agent.py                  # Memory manager
│
├── memory/
│   ├── __init__.py
│   ├── session_memory.py                # SQLite short-term
│   ├── long_term_memory.py              # MongoDB long-term
│   └── vector_memory.py                 # Pinecone vector store
│
├── mcp/
│   ├── __init__.py
│   ├── server.py                        # MCP Server
│   ├── client.py                        # MCP Client
│   ├── resources.py                     # MCP Resources
│   └── tools.py                         # MCP Tool definitions
│
├── workflow/
│   ├── __init__.py
│   ├── research_workflow.py             # LangGraph workflow
│   ├── graph_builder.py                 # Graph construction
│   └── state.py                         # Workflow state schema
│
├── api/
│   ├── __init__.py
│   ├── main.py                          # FastAPI application
│   ├── routes.py                        # API endpoints
│   ├── models.py                        # Pydantic models
│   └── middleware.py                     # Logging middleware
│
├── frontend/
│   ├── app.py                           # Streamlit main app
│   ├── components/
│   │   ├── __init__.py
│   │   ├── chat_interface.py            # Chat UI
│   │   ├── agent_panel.py              # Agent activity panel
│   │   ├── workflow_viz.py             # Workflow visualization
│   │   ├── memory_viewer.py            # Memory viewer
│   │   └── citations_viewer.py         # Citations display
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── api_client.py               # API client
│   │   └── state_manager.py            # Session state management
│   └── assets/
│       └── style.css                    # Custom styles
│
├── utils/
│   ├── __init__.py
│   ├── logger.py                        # Structured logging
│   ├── metrics.py                       # Performance metrics
│   ├── config.py                        # Configuration
│   └── helpers.py                       # Utility functions
│
├── tests/
│   ├── __init__.py
│   ├── test_agents.py                   # Agent tests
│   ├── test_memory.py                   # Memory tests
│   ├── test_mcp.py                      # MCP tests
│   ├── test_api.py                      # API tests
│   ├── test_workflow.py                 # Workflow tests
│   └── conftest.py                      # Test fixtures
│
├── deployment/
│   ├── Dockerfile.api                   # API Dockerfile
│   ├── Dockerfile.frontend             # Frontend Dockerfile
│   ├── docker-compose.yml              # Compose setup
│   ├── render.yaml                     # Render deployment
│   └── streamlit_config.toml           # Streamlit Cloud config
│
├── scripts/
│   ├── setup.sh                        # Setup script
│   ├── seed_data.py                    # Seed initial data
│   └── run.sh                          # Run script
│
├── docs/
│   ├── setup.md                        # Setup guide
│   ├── deployment.md                   # Deployment guide
│   └── api_reference.md               # API documentation
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```