"""Base agent class with shared LLM and MCP access."""

from abc import ABC, abstractmethod
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_groq import ChatGroq

from configs.config import settings
from mcp_layer.client import MCPClient
from utils.logger import get_logger


class BaseAgent(ABC):
    """Abstract base for all agents in the platform."""

    def __init__(self, name: str, mcp_client: MCPClient | None = None, api_key: str | None = None, provider: str = "gemini") -> None:
        self.name = name
        self.logger = get_logger(f"agent.{name}")
        self.mcp = mcp_client or MCPClient()
        key = api_key or settings.gemini_api_key
        if not key:
            raise ValueError(f"{provider.capitalize()} API key is required. Please provide it in the UI or .env file.")
        
        self.provider = provider.lower()
        if self.provider == "openai":
            self.llm = ChatOpenAI(model="gpt-4o-mini", api_key=key, temperature=0.3)
        elif self.provider == "anthropic":
            self.llm = ChatAnthropic(model="claude-3-haiku-20240307", api_key=key, temperature=0.3, max_tokens=8192)
        elif self.provider == "grok":
            self.llm = ChatOpenAI(model="grok-beta", api_key=key, base_url="https://api.x.ai/v1", temperature=0.3)
        elif self.provider == "groq":
            self.llm = ChatGroq(model="mixtral-8x7b-32768", api_key=key, temperature=0.3)
        else:
            self.llm = ChatGoogleGenerativeAI(
                model=settings.gemini_model,
                google_api_key=key,
                temperature=0.3,
                max_output_tokens=8192,
            )

    @abstractmethod
    async def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """Execute the agent's task and return updated state."""

    async def call_mcp_tool(self, tool_name: str, arguments: dict) -> Any:
        """Convenience wrapper for MCP tool calls."""
        return await self.mcp.call_tool(tool_name, arguments)

    def _format_prompt(self, template: str, **kwargs: Any) -> str:
        """Format a prompt template with the given variables."""
        return template.format(**kwargs)
