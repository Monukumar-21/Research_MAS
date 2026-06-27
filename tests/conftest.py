"""Shared test fixtures – loaded before any test code to set environment."""
import os
from dotenv import load_dotenv

# Load .env first so we use real credentials for integration tests if they exist
load_dotenv()

# Set dummy environment variables BEFORE any project imports
os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("PINECONE_API_KEY", "test-pinecone-key")
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DB_NAME", "test_research_platform")
os.environ.setdefault("SQLITE_DB_PATH", "data/test_session.db")

import pytest_asyncio
from memory.sqlite_memory import SQLiteMemory


@pytest_asyncio.fixture
async def sqlite_memory(tmp_path):
    """Provide a fresh SQLite memory instance."""
    db_path = str(tmp_path / "test.db")
    mem = SQLiteMemory(db_path=db_path)
    await mem.initialize()
    yield mem
    await mem.close()