# MEMORY ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MEMORY ARCHITECTURE                                 │
│                    THREE-TIER MEMORY SYSTEM                                  │
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                    LAYER 1: SHORT-TERM MEMORY                       │     │
│  │                         SQLite (session.db)                        │     │
│  │                                                                    │     │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐               │     │
│  │  │ conversations│ │  sessions    │ │ workflow     │               │     │
│  │  │              │ │              │ │ progress     │               │     │
│  │  │ id           │ │ id           │ │ id           │               │     │
│  │  │ session_id   │ │ user_id      │ │ session_id   │               │     │
│  │  │ role         │ │ status       │ │ step         │               │     │
│  │  │ content      │ │ created_at   │ │ status       │               │     │
│  │  │ timestamp    │ │ updated_at   │ │ data         │               │     │
│  │  └──────────────┘ └──────────────┘ └──────────────┘               │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                    │                                        │
│                                    ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                    LAYER 2: LONG-TERM MEMORY                       │     │
│  │                         MongoDB (research_db)                      │     │
│  │                                                                    │     │
│  │  Collections:                                                      │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐     │     │
│  │  │research  │ │agents    │ │reports   │ │a2a_messages     │     │     │
│  │  │_history  │ │_memory   │ │          │ │                  │     │     │
│  │  ├──────────┤ ├──────────┤ ├──────────┤ ├──────────────────┤     │     │
│  │  │topic     │ │agent_id  │ │id        │ │message_id       │     │     │
│  │  │subtopics │ │key       │ │title     │ │from_agent       │     │     │
│  │  │queries   │ │value     │ │content   │ │to_agent         │     │     │
│  │  │results   │ │timestamp │ │summary   │ │payload          │     │     │
│  │  │timestamp │ │type      │ │sources   │ │timestamp        │     │     │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘     │     │
│  │                                                                    │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                           │     │
│  │  │citations │ │users     │ │feedback  │                           │     │
│  │  ├──────────┤ ├──────────┤ ├──────────┤                           │     │
│  │  │id        │ │id        │ │report_id │                           │     │
│  │  │report_id │ │prefs     │ │rating    │                           │     │
│  │  │source    │ │history   │ │comments  │                           │     │
│  │  │claim     │ │created_at│ │timestamp │                           │     │
│  │  │reference │ │          │ │          │                           │     │
│  │  └──────────┘ └──────────┘ └──────────┘                           │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                    │                                        │
│                                    ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │                    LAYER 3: VECTOR MEMORY                         │     │
│  │                         Pinecone (research-index)                  │     │
│  │                                                                    │     │
│  │  ┌────────────────────────────────────────────────────────────┐    │     │
│  │  │  Namespace: documents                                      │    │     │
│  │  │  Vector Dimensions: 768 (Gemini Embeddings)                │    │     │
│  │  │  Metric: Cosine Similarity                                │    │     │
│  │  │                                                            │    │     │
│  │  │  Vector ID: doc_{hash}                                     │    │     │
│  │  │  Values: [0.123, 0.456, ...] (768 floats)                 │    │     │
│  │  │  Metadata:                                                 │    │     │
│  │  │    - text: "chunk content"                                 │    │     │
│  │  │    - source: "arxiv/url/pdf"                               │    │     │
│  │  │    - topic: "quantum computing"                            │    │     │
│  │  │    - chunk_index: 0                                        │    │     │
│  │  │    - total_chunks: 12                                      │    │     │
│  │  │    - timestamp: "ISO8601"                                  │    │     │
│  │  │    - research_session: "uuid"                              │    │     │
│  │  └────────────────────────────────────────────────────────────┘    │     │
│  └────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘

                            RAG DATA FLOW
                    User Query → Embed → Pinecone Search
                    → Top-K Results → Rerank → Gemini → Response
                                                                                
                    MEMORY RETENTION POLICY
                    SQLite: Session Duration (auto-clear)
                    MongoDB: Indefinite (user-managed)
                    Pinecone: Indefinite with TTL per document
```