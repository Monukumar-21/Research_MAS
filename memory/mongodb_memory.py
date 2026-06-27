"""MongoDB Atlas long-term memory for research history and agent memory."""

from typing import Any
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, OperationFailure

from memory.base import BaseMemory
from configs.config import settings
from utils.logger import get_logger
from utils.helpers import generate_id, timestamp_now

logger = get_logger(__name__)


class MongoDBMemory(BaseMemory):
    """Long-term persistent memory backed by MongoDB Atlas."""

    def __init__(self) -> None:
        self.client: AsyncIOMotorClient | None = None
        self.db = None

    async def initialize(self) -> None:
        """Initialize MongoDB connection and indexes. Raises on failure."""
        try:
            self.client = AsyncIOMotorClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS=5000,  # Fail fast if unreachable
            )
            # Verify connection — this will raise if URI is wrong or server down
            await self.client.admin.command("ping")
            self.db = self.client[settings.mongodb_db_name]

            # Build indexes safely
            await self._ensure_indexes()
            logger.info("MongoDB memory initialized: %s", settings.mongodb_db_name)

        except (ConnectionFailure, OperationFailure) as e:
            logger.error("MongoDB initialization failed: %s", e)
            self.client = None
            self.db = None
            raise  # CRITICAL: Don't swallow — let caller know connection failed

    async def _ensure_indexes(self) -> None:
        """Idempotent index creation."""
        # Research history indexes
        await self.db.research_history.create_index("run_id", unique=True)
        await self.db.research_history.create_index("topic")
        # Only create text index if results field is a string; skip if nested
        try:
            await self.db.research_history.create_index(
                [("topic", "text"), ("results", "text")]
            )
        except OperationFailure:
            logger.warning("Could not create text index on 'results' — field may not be a string")

        # Agent memory compound index
        await self.db.agents_memory.create_index(
            [("agent_name", 1), ("key", 1)], unique=True
        )

        # User & A2A indexes
        await self.db.users.create_index("user_id", unique=True)
        await self.db.a2a_messages.create_index("message_id", unique=True)
        await self.db.a2a_messages.create_index("timestamp")

    async def save_research_run(self, run_data: dict) -> str:
        if self.db is None:
            raise RuntimeError("MongoDB not initialized. Call initialize() first.")
        run_id = run_data.get("run_id", generate_id())
        run_data["run_id"] = run_id
        run_data["timestamp"] = timestamp_now()
        await self.db.research_history.update_one(
            {"run_id": run_id}, {"$set": run_data}, upsert=True
        )
        return run_id

    async def get_research_run(self, run_id: str) -> dict | None:
        if self.db is None:
            raise RuntimeError("MongoDB not initialized. Call initialize() first.")
        return await self.db.research_history.find_one({"run_id": run_id}, {"_id": 0})

    async def list_research_runs(self, limit: int = 20) -> list[dict]:
        if self.db is None:
            raise RuntimeError("MongoDB not initialized. Call initialize() first.")
        cursor = (
            self.db.research_history.find(
                {}, {"_id": 0, "run_id": 1, "topic": 1, "timestamp": 1}
            )
            .sort("timestamp", -1)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def save_agent_memory(self, agent_name: str, key: str, value: Any) -> None:
        if self.db is None:
            raise RuntimeError("MongoDB not initialized. Call initialize() first.")
        await self.db.agents_memory.update_one(
            {"agent_name": agent_name, "key": key},
            {
                "$set": {
                    "value": value,
                    "updated_at": timestamp_now(),
                    "agent_name": agent_name,
                    "key": key,
                }
            },
            upsert=True,
        )

    async def get_agent_memory(self, agent_name: str, key: str) -> Any:
        if self.db is None:
            raise RuntimeError("MongoDB not initialized. Call initialize() first.")
        doc = await self.db.agents_memory.find_one(
            {"agent_name": agent_name, "key": key}, {"_id": 0}
        )
        return doc.get("value") if doc else None

    async def save_user_prefs(self, user_id: str, prefs: dict) -> None:
        if self.db is None:
            raise RuntimeError("MongoDB not initialized. Call initialize() first.")
        await self.db.users.update_one(
            {"user_id": user_id},
            {"$set": {"preferences": prefs, "updated_at": timestamp_now()}},
            upsert=True,
        )

    async def get_user_prefs(self, user_id: str) -> dict:
        if self.db is None:
            raise RuntimeError("MongoDB not initialized. Call initialize() first.")
        doc = await self.db.users.find_one({"user_id": user_id}, {"_id": 0})
        return doc.get("preferences", {}) if doc else {}

    async def save_a2a_message(self, message: dict) -> str:
        if self.db is None:
            raise RuntimeError("MongoDB not initialized. Call initialize() first.")
        if not message.get("message_id"):
            message["message_id"] = generate_id()
        message.setdefault("timestamp", timestamp_now())
        await self.db.a2a_messages.insert_one(message)
        return message["message_id"]

    async def get_a2a_messages(
        self, session_id: str = None, limit: int = 100
    ) -> list[dict]:
        if self.db is None:
            raise RuntimeError("MongoDB not initialized. Call initialize() first.")
        query = {"session_id": session_id} if session_id else {}
        cursor = (
            self.db.a2a_messages.find(query, {"_id": 0})
            .sort("timestamp", 1)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    # ── BaseMemory Interface ──

    async def store(
        self, key: str, value: Any, metadata: dict | None = None
    ) -> None:
        agent = (metadata or {}).get("agent_name", "system")
        await self.save_agent_memory(agent, key, value)

    async def retrieve(
        self, key: str, agent_name: str = "system", metadata: dict | None = None
    ) -> Any:
        """Retrieve agent memory. Accepts agent_name directly or via metadata."""
        if metadata and "agent_name" in metadata:
            agent_name = metadata["agent_name"]
        if self.db is None:
            raise RuntimeError("MongoDB not initialized. Call initialize() first.")
        doc = await self.db.agents_memory.find_one(
            {"agent_name": agent_name, "key": key}, {"_id": 0}
        )
        return doc.get("value") if doc else None

    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        if self.db is None:
            raise RuntimeError("MongoDB not initialized. Call initialize() first.")
        try:
            cursor = (
                self.db.research_history.find(
                    {"$text": {"$search": query}}, {"_id": 0}
                )
                .limit(top_k)
            )
            return await cursor.to_list(length=top_k)
        except Exception:
            # Fallback to regex search if text index unavailable
            cursor = (
                self.db.research_history.find(
                    {"topic": {"$regex": query, "$options": "i"}}, {"_id": 0}
                )
                .limit(top_k)
            )
            return await cursor.to_list(length=top_k)

    async def close(self) -> None:
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")