# Multi-Agent Academic Research Platform 🤖🔬

> **A production-grade AI platform where 8 specialized AI agents collaborate to conduct academic research end-to-end.**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-✧-orange)](https://langchain-ai.github.io/langgraph/)
[![LLMs](https://img.shields.io/badge/LLMs-Gemini%20%7C%20OpenAI%20%7C%20Claude%20%7C%20Grok-yellow)]()
[![Streamlit](https://img.shields.io/badge/Streamlit-1.31-red)](https://streamlit.io)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green)](https://www.mongodb.com/atlas)
[![Pinecone](https://img.shields.io/badge/Pinecone-Free-blueviolet)](https://www.pinecone.io)

---

## 🎯 Overview

The **Multi-Agent Academic Research Platform** is a production-grade system where **8 specialized AI agents** collaborate to perform complete academic research. Built with modern AI engineering practices, it demonstrates how to build scalable, observable multi-agent systems.

### ✨ Key Capabilities

| Capability | Description |
|------------|-------------|
| **🤖 Multi-Agent Orchestration** | 8 agents collaborate through LangGraph workflows |
| **📚 RAG Pipeline** | Semantic search via Pinecone + Gemini embeddings |
| **🧠 Three-Tier Memory** | SQLite (short-term), MongoDB (long-term), Pinecone (vector) |
| **🔗 MCP Protocol** | Model Context Protocol for standardized tool access |
| **📝 Academic Report Generation** | Structured reports with citations and references |
| **✅ Hallucination Detection** | Critic agent verifies accuracy and confidence |
| **🔬 Citation Management** | Automatic citation generation in APA/MLA/Chicago |
| **🌐 Multi-LLM Support** | Choose between Gemini, OpenAI (ChatGPT), Anthropic (Claude), xAI (Grok), and Groq dynamically |
| **🛡️ Quota Protection** | Gracefully handles rate limits mid-research by saving & returning the current progress |
| **📊 Full Observability** | Metrics, tracing, logging for every agent action |
| **🔌 A2A Communication** | Agent-to-Agent messaging via MongoDB |

### 🧠 Agent Architecture

```
User Query → Supervisor → Planner → Retriever → Memory → Writer → Citation → Critic → Reflection → Final Output
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- API Keys (free tiers):
  - [Google Gemini](https://aistudio.google.com/app/apikey)
  - [MongoDB Atlas](https://www.mongodb.com/atlas)
  - [Pinecone](https://www.pinecone.io)

### 1. Setup
```bash
git clone https://github.com/yourusername/multi-agent-research-platform.git
cd multi-agent-research-platform
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Configure
Edit `.env` with your database keys (LLM API keys are now handled securely in the frontend):
```env
# Optional fallback, usually provided via Streamlit UI
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
XAI_API_KEY=your_xai_key
GROQ_API_KEY=your_groq_key

MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
PINECONE_API_KEY=your_pinecone_key
```

### 3. Launch
```bash
# Terminal 1: API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
streamlit run frontend/app.py --server.port 8501
```

### 4. Use
1. Open the **Frontend** at http://localhost:8501
2. **Select your LLM Provider** (Gemini, ChatGPT, Claude, Grok, Groq) and enter your API Key in the sidebar settings.
3. Type a research topic and click "Research"! 
*(Note: If you hit a rate limit or run out of quota mid-research, the platform will automatically pause, save the partial report, and ask for a new key!)*

- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/api/v1/health

## 🏗️ Architecture

### Multi-Agent Workflow
```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│Supervisor│──▶│ Planner  │──▶│Retriever │──▶│  Memory  │
│ (Routes) │   │ (Plans)  │   │(Searches)│   │ (Stores) │
└─────┬────┘   └──────────┘   └──────────┘   └──────────┘
      │                                                  │
      ▼                                                  ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Writer   │──▶│ Citation │──▶│  Critic  │──▶│Reflection│──▶ Done
│(Reports) │   │ (Refs)   │   │(Verifies)│   │(Reviews) │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
```

### Memory Architecture
```
┌─────────────────────────────────────────────┐
│           Three-Tier Memory System           │
├──────────────┬────────────────┬──────────────┤
│   SQLite     │    MongoDB     │   Pinecone   │
│ (Short-Term) │  (Long-Term)   │  (Vector)    │
│              │                │              │
│ • Chat Hist  │ • Research     │ • Embeddings │
│ • Sessions   │ • Agent Memory │ • Semantic   │
│ • Workflow   │ • Reports      │   Search     │
│   Progress   │ • Citations    │ • Documents  │
│              │ • A2A Messages │              │
└──────────────┴────────────────┴──────────────┘
```

## 🧩 Agents

| Agent | Responsibility | Tools |
|-------|---------------|-------|
| **Supervisor** | Task routing, workflow orchestration, retry logic | All MCP tools |
| **Planner** | Topic decomposition, search queries, research planning | search_docs, retrieve_memory |
| **Retriever** | Semantic search, document ranking, context expansion | search_docs, summarize |
| **Writer** | Report generation, formatting, summaries | retrieve_memory, save_report |
| **Critic** | Hallucination detection, confidence scoring, verification | load_report, retrieve_memory |
| **Citation** | Reference generation, citation formatting | generate_citations, search_docs |
| **Reflection** | Quality review, improvement suggestions | load_report, research_history |
| **Memory** | Cross-tier memory management, summarization | All memory tools |

## 📡 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | System health check |
| `/api/v1/chat` | POST | Conversational chat |
| `/api/v1/research` | POST | Full research workflow |
| `/api/v1/agent/run` | POST | Execute single agent |
| `/api/v1/memory` | POST | Memory operations |
| `/api/v1/history` | GET | Research history |
| `/api/v1/citations/{id}` | GET | Report citations |
| `/api/v1/logs` | GET | Execution logs |
| `/api/v1/metrics` | GET | System metrics |
| `/api/v1/workflow/runs` | GET | Workflow runs |

## 📁 Project Structure

```
├── agents/          # 8 specialized AI agents
├── memory/          # Three-tier memory system
├── mcp/             # Model Context Protocol
├── workflow/        # LangGraph orchestration
├── api/             # FastAPI backend
├── frontend/        # Streamlit UI
├── utils/           # Logging, config, helpers
├── tests/           # Complete test suite
├── deployment/      # Docker & deployment configs
└── scripts/         # Setup & seed scripts
```

## 🐳 Docker Deployment

```bash
docker-compose -f deployment/docker-compose.yml up --build
```

## 📊 Observability

Every agent action is logged with:
- **Trace ID** for request tracking
- **Execution time** per agent
- **Token usage** for cost monitoring
- **Success/failure** status
- **Agent-to-agent messages** stored in MongoDB

## 🧪 Testing

```bash
pytest tests/ --cov --cov-report=html
```

## 🌐 Deployment Options

| Platform | Service | Cost |
|----------|---------|------|
| Render | API + Frontend | Free tier |
| Streamlit Cloud | Frontend only | Free tier |
| Docker | Self-hosted | Your infrastructure |

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **LLMs** | Gemini, OpenAI, Anthropic, xAI, Groq (Mixtral) |
| **Agent Framework** | LangGraph + LangChain |
| **Backend** | FastAPI + Uvicorn |
| **Frontend** | Streamlit |
| **Short-Term Memory** | SQLite |
| **Long-Term Memory** | MongoDB Atlas |
| **Vector Store** | Pinecone |
| **Embeddings** | Gemini text-embedding-004 |
| **Protocols** | MCP, A2A |
| **Deployment** | Docker, Render, Streamlit Cloud |

## 📄 License

MIT License

---

**Built with ❤️ for the AI Engineering Community**
