# AGENT COMMUNICATION DIAGRAM (A2A)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AGENT-TO-AGENT (A2A) COMMUNICATION                       │
│                                                                            │
│  Message Format:                                                           │
│  {                                                                         │
│    "message_id": "uuid",                                                   │
│    "from": "agent_name",                                                   │
│    "to": "agent_name",                                                     │
│    "type": "task | response | error | status",                             │
│    "task": "task_name",                                                    │
│    "payload": {},                                                          │
│    "timestamp": "ISO8601",                                                 │
│    "status": "sent | delivered | processed | failed"                       │
│  }                                                                         │
│                                                                            │
│  ┌──────────┐        ┌──────────┐        ┌──────────┐                     │
│  │SUPERVISOR│◀──────▶│ PLANNER  │◀──────▶│RETRIEVER │                     │
│  │          │        │          │        │          │                     │
│  │Routes    │        │Research  │        │Semantic  │                     │
│  │Orchestr. │        │Planning  │        │Search    │                     │
│  └────┬─────┘        └────┬─────┘        └────┬─────┘                     │
│       │                   │                    │                           │
│       ▼                   ▼                    ▼                           │
│  ┌──────────┐        ┌──────────┐        ┌──────────┐                     │
│  │ MEMORY   │◀──────▶│ WRITER   │◀──────▶│ CRITIC   │                     │
│  │          │        │          │        │          │                     │
│  │Store/Ret │        │Reports   │        │Verify    │                     │
│  └────┬─────┘        └────┬─────┘        └────┬─────┘                     │
│       │                   │                    │                           │
│       ▼                   ▼                    ▼                           │
│  ┌──────────┐        ┌──────────┐        ┌──────────┐                     │
│  │CITATION  │◀──────▶│REFLECTION│        │          │                     │
│  │          │        │          │        │          │                     │
│  │Refs/Links│        │Review    │        │          │                     │
│  └──────────┘        └──────────┘        └──────────┘                     │
│                                                                            │
│  A2A Message Flow:                                                         │
│  ──────────────────                                                        │
│                                                                             │
│  Step 1: Supervisor → Planner: {"type":"task","task":"plan_research",      │
│           "payload":{"topic":"Quantum Computing"}}                          │
│                                                                             │
│  Step 2: Planner → Supervisor: {"type":"response","task":"plan_research",  │
│           "payload":{"subtopics":[...],"plan":[...]}}                       │
│                                                                             │
│  Step 3: Supervisor → Retriever: {"type":"task","task":"search_docs",      │
│           "payload":{"query":"quantum computing", "subtopics":[...]}}       │
│                                                                             │
│  Step 4: Retriever → Memory: {"type":"task","task":"store",                │
│           "payload":{"documents":[...]}}                                    │
│                                                                             │
│  Step 5: Memory → Retriever: {"type":"response","task":"store",            │
│           "payload":{"status":"stored","memory_ids":[...]}}                 │
│                                                                             │
│  Step 6: Retriever → Supervisor: {"type":"response","task":"search_docs",  │
│           "payload":{"documents":[...]}}                                    │
│                                                                             │
│  All messages stored in MongoDB A2A collection                              │
└─────────────────────────────────────────────────────────────────────────────┘
```