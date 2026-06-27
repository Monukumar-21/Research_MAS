"""Abstract base for memory backends."""

from abc import ABC, abstractmethod
from typing import Any


class BaseMemory(ABC):
    """Interface that every memory backend must implement."""

    @abstractmethod
    async def initialize(self) -> None:
        """Set up connections and schemas."""

    @abstractmethod
    async def store(self, key: str, value: Any, metadata: dict | None = None) -> None:
        """Persist a value."""

    @abstractmethod
    async def retrieve(self, key: str) -> Any:
        """Fetch a value by key."""

    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Semantic or keyword search."""

    @abstractmethod
    async def close(self) -> None:
        """Tear down connections."""
