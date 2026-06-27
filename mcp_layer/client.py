"""MCP HTTP client that agents use to call tools via the API's /mcp endpoint."""

import json
from typing import Any
import httpx
from configs.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class MCPClient:
    """Thin HTTP client for MCP server (FastAPI /mcp)."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or settings.mcp_server_url
        self._client: httpx.AsyncClient | None = None

    async def initialize(self) -> None:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """Call an MCP tool by name."""
        await self.initialize()
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
            "id": 1,
        }
        logger.info("MCP tool call: %s(%s)", tool_name, list(arguments.keys()))
        try:
            response = await self._client.post(self.base_url, json=payload)
            response.raise_for_status()
            data = response.json()
            if "error" in data:
                raise RuntimeError(f"MCP error: {data['error']}")
            return data.get("result")
        except httpx.HTTPError as e:
            raise RuntimeError(f"MCP HTTP error: {e}")

    async def list_tools(self) -> list[dict]:
        await self.initialize()
        resp = await self._client.get(f"{self.base_url}/tools/list")
        resp.raise_for_status()
        return resp.json().get("tools", [])

    async def list_resources(self) -> list[dict]:
        await self.initialize()
        resp = await self._client.get(f"{self.base_url}/resources/list")
        resp.raise_for_status()
        return resp.json().get("resources", [])

    async def read_resource(self, uri: str) -> Any:
        await self.initialize()
        payload = {
            "jsonrpc": "2.0",
            "method": "resources/read",
            "params": {"uri": uri},
            "id": 1,
        }
        resp = await self._client.post(self.base_url, json=payload)
        resp.raise_for_status()
        return resp.json().get("result")

    async def ping(self) -> bool:
        await self.initialize()
        try:
            resp = await self._client.get(f"{self.base_url}/ping")
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None