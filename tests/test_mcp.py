"""Tests for MCP HTTP client."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from mcp_layer.client import MCPClient


@pytest.fixture
def client():
    """Return an MCPClient instance with a mocked HTTP client."""
    c = MCPClient(base_url="http://testserver/mcp")
    c._client = AsyncMock(spec=httpx.AsyncClient)
    return c


@pytest.mark.asyncio
async def test_list_tools(client):
    """list_tools should fetch tools from the server."""
    expected_tools = [
        {"name": "search_docs", "description": "..."},
        {"name": "store_memory", "description": "..."},
    ]
    mock_response = MagicMock()
    mock_response.json.return_value = {"tools": expected_tools}
    client._client.get.return_value = mock_response

    tools = await client.list_tools()
    assert tools == expected_tools
    client._client.get.assert_called_once_with("http://testserver/mcp/tools/list")


@pytest.mark.asyncio
async def test_call_tool_success(client):
    """call_tool should send a JSON-RPC request and return the result."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"jsonrpc": "2.0", "result": {"status": "ok"}, "id": 1}
    client._client.post.return_value = mock_response

    result = await client.call_tool("search_docs", {"query": "quantum"})
    assert result == {"status": "ok"}
    client._client.post.assert_called_once_with(
        "http://testserver/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "search_docs", "arguments": {"query": "quantum"}},
            "id": 1,
        },
    )


@pytest.mark.asyncio
async def test_call_tool_error(client):
    """call_tool should raise RuntimeError on MCP error."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Unknown tool"}}
    client._client.post.return_value = mock_response

    with pytest.raises(RuntimeError, match="MCP error"):
        await client.call_tool("nonexistent", {})


@pytest.mark.asyncio
async def test_ping_success(client):
    """ping should return True on 200 OK."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    client._client.get.return_value = mock_response

    assert await client.ping() is True
    client._client.get.assert_called_once_with("http://testserver/mcp/ping")


@pytest.mark.asyncio
async def test_ping_failure(client):
    """ping should return False on network error."""
    client._client.get.side_effect = httpx.HTTPError("Connection refused")
    assert await client.ping() is False


def test_initialization_flag(client):
    """Client should start with no HTTP client until initialize."""
    c = MCPClient()
    assert c._client is None