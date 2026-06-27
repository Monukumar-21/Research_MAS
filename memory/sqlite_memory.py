"""SQLite-backed session, chat history, and workflow state memory."""

import json
import aiosqlite
from typing import Any, Optional

from memory.base import BaseMemory
from configs.config import settings
from utils.logger import get_logger
from utils.helpers import generate_id, timestamp_now

logger = get_logger(__name__)

class SQLiteMemory(BaseMemory):
    """Short-term memory: sessions, messages, workflow state."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or str(settings.get_sqlite_path())
        self.db: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """Create tables if they don't exist and establish a persistent connection."""
        self.db = await aiosqlite.connect(self.db_path)
        
        # CRITICAL: Enable foreign key enforcement
        await self.db.execute("PRAGMA foreign_keys = ON;")
        
        await self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS workflow_states (
                state_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                node_name TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                data_json TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            );
            """
        )
        await self.db.commit()
        logger.info("SQLite memory initialized at %s", self.db_path)

    async def create_session(self, topic: str) -> str:
        session_id = generate_id()
        now = timestamp_now()
        await self.db.execute(
            "INSERT INTO sessions (session_id, topic, status, created_at, updated_at) VALUES (?, ?, 'active', ?, ?)",
            (session_id, topic, now, now),
        )
        await self.db.commit()
        return session_id

    async def update_session_status(self, session_id: str, status: str) -> None:
        await self.db.execute(
            "UPDATE sessions SET status = ?, updated_at = ? WHERE session_id = ?",
            (status, timestamp_now(), session_id),
        )
        await self.db.commit()

    async def get_session(self, session_id: str) -> dict | None:
        self.db.row_factory = aiosqlite.Row
        async with self.db.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def add_message(self, session_id: str, role: str, content: str) -> str:
        msg_id = generate_id()
        await self.db.execute(
            "INSERT INTO messages (message_id, session_id, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
            (msg_id, session_id, role, content, timestamp_now()),
        )
        await self.db.commit()
        return msg_id

    async def get_messages(self, session_id: str, limit: int = 50) -> list[dict]:
        self.db.row_factory = aiosqlite.Row
        async with self.db.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp ASC LIMIT ?",
            (session_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def save_workflow_state(self, session_id: str, node_name: str, data: dict, status: str = "pending") -> str:
        state_id = generate_id()
        await self.db.execute(
            "INSERT INTO workflow_states (state_id, session_id, node_name, status, data_json, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (state_id, session_id, node_name, status, json.dumps(data), timestamp_now()),
        )
        await self.db.commit()
        return state_id

    async def get_workflow_states(self, session_id: str) -> list[dict]:
        self.db.row_factory = aiosqlite.Row
        async with self.db.execute("SELECT * FROM workflow_states WHERE session_id = ? ORDER BY timestamp ASC", (session_id,)) as cursor:
            rows = await cursor.fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["data"] = json.loads(d.pop("data_json"))
                result.append(d)
            return result

    async def store(self, key: str, value: Any, metadata: dict | None = None) -> None:
        session_id = (metadata or {}).get("session_id", "default")
        await self.add_message(session_id, "system", json.dumps({"key": key, "value": value}))

    async def retrieve(self, key: str) -> Any:
        return None

    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        return []

    async def close(self) -> None:
        if self.db:
            await self.db.close()
            logger.info("SQLite memory closed")