"""Real Integration Tests for all memory backends."""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator

from memory.sqlite_memory import SQLiteMemory
from memory.mongodb_memory import MongoDBMemory
from memory.pinecone_memory import PineconeMemory
from utils.helpers import generate_id
from configs.config import settings

# ---------------------------------------------------------------------------
# SQLite fixture (100% Isolated using in-memory database)
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def sqlite_memory() -> AsyncGenerator[SQLiteMemory, None]:
    mem = SQLiteMemory(db_path=":memory:") # CRITICAL: Forces RAM DB
    await mem.initialize()
    yield mem
    await mem.close()

# ---------------------------------------------------------------------------
# MongoDB fixture (Real connection with Auto-Cleanup)
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def mongo_memory() -> AsyncGenerator[MongoDBMemory, None]:
    if not settings.mongodb_uri:
        pytest.skip("MongoDB URI not set in .env")
        
    mem = MongoDBMemory()
    await mem.initialize()
    
    yield mem
    
    # TEARDOWN: Clean up tests so we don't pollute the real database
    if mem.db is not None:
        await mem.db.research_history.delete_many({"topic": {"$regex": "^TEST_.*"}})
        await mem.db.agents_memory.delete_many({"agent_name": "TestAgent"})
    await mem.close()

# ---------------------------------------------------------------------------
# Pinecone fixture (Real connection)
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def pinecone_memory() -> AsyncGenerator[PineconeMemory, None]:
    if not settings.pinecone_api_key or not settings.gemini_api_key:
        pytest.skip("Pinecone or Gemini API keys not set in .env")
        
    mem = PineconeMemory()
    await mem.initialize()
    yield mem
    
    # Optional Teardown: If you want to delete the test vectors to save space
    # if mem.index:
    #     mem.index.delete(filter={"doc_id": "TEST_DOC_ID"})
    await mem.close()


# ---------------------------------------------------------------------------
# SQLite Tests (Real logic, isolated to RAM)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_sqlite_create_session(sqlite_memory):
    session_id = await sqlite_memory.create_session("Test Topic")
    assert session_id is not None

@pytest.mark.asyncio
async def test_sqlite_messages(sqlite_memory):
    session_id = await sqlite_memory.create_session("Test")
    await sqlite_memory.add_message(session_id, "user", "Hello")
    messages = await sqlite_memory.get_messages(session_id)
    assert len(messages) == 1
    assert messages[0]["role"] == "user"

@pytest.mark.asyncio
async def test_sqlite_workflow_state(sqlite_memory):
    session_id = await sqlite_memory.create_session("Test")
    await sqlite_memory.save_workflow_state(session_id, "planner", {"steps": 3})
    states = await sqlite_memory.get_workflow_states(session_id)
    assert states[0]["data"]["steps"] == 3


# ---------------------------------------------------------------------------
# MongoDB Tests (Real Network Connection)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_mongo_save_and_get_research_run(mongo_memory):
    test_run_id = f"TEST_RUN_{generate_id()}"
    run_data = {"run_id": test_run_id, "topic": "TEST_MongoDB_Integration"}
    
    await mongo_memory.save_research_run(run_data)
    fetched = await mongo_memory.get_research_run(test_run_id)
    
    assert fetched is not None
    assert fetched["topic"] == "TEST_MongoDB_Integration"

@pytest.mark.asyncio
async def test_mongo_agent_memory_scoping(mongo_memory):
    """Ensure Agent A cannot read Agent B's memory."""
    await mongo_memory.save_agent_memory("TestAgent", "goal", "Find Data")
    
    # Should find it for TestAgent
    val1 = await mongo_memory.retrieve("goal", agent_name="TestAgent")
    assert val1 == "Find Data"
    
    # Should NOT find it for OtherAgent
    val2 = await mongo_memory.retrieve("goal", agent_name="OtherAgent")
    assert val2 is None


# ---------------------------------------------------------------------------
# Pinecone Tests (Real Network Connection & Embeddings)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_pinecone_upsert_and_query(pinecone_memory):
    test_doc_id = f"TEST_DOC_{generate_id()}"
    test_text = "The quick brown fox jumps over the lazy dog."
    
    # 1. Upsert
    count = await pinecone_memory.upsert_document(test_doc_id, test_text, {"source": "test"})
    assert count > 0
    
    # 2. Wait for Pinecone to index the new vector (Eventually Consistent)
    await asyncio.sleep(4) 
    
    # 3. Query
    results = await pinecone_memory.query_similar("brown fox", top_k=1, filter_dict={"doc_id": test_doc_id})
    
    assert len(results) > 0
    assert "fox" in results[0]["text"]