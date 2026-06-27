"""Centralized configuration using pydantic-settings."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Google Gemini ---
    gemini_api_key: str = os.getenv("GEMINI_API_KEY")
    gemini_model: str = "gemini-2.0-flash"          
    gemini_embedding_model: str = "models/gemini-embedding-2"

    # --- MongoDB Atlas ---
    mongodb_uri: str = os.getenv("MONGODB_URI")
    mongodb_db_name: str = os.getenv("MONGODB_DB_NAME")

    # --- Pinecone ---
    pinecone_api_key: str = os.getenv("PINECONE_API_KEY")
    pinecone_index_name: str = os.getenv("PINECONE_INDEX_NAME", "research-kb")
    pinecone_environment: str = os.getenv("PINECONE_ENVIRONMENT", "us-east-1-aws")
    pinecone_dimension: int = 1024

    # --- SQLite ---
    sqlite_db_path: str = "data/session.db"
    database_url: str = "sqlite:///data/session.db" 

    # --- API ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_base_url: str = "http://localhost:8000"

    # --- MCP ---
    mcp_server_host: str = "localhost"
    mcp_server_port: int = 8000                     # FIXED to match deployment
    mcp_server_url: str = "http://localhost:8000/mcp"  # ADDED combined URL

    # --- Logging ---
    log_level: str = "INFO"

    # --- Research Defaults ---
    max_subtopics: int = 5
    max_search_results: int = 10
    max_report_words: int = 3000
    max_revision_rounds: int = 2

    def get_sqlite_path(self) -> Path:
        """Return resolved SQLite path, creating parent dirs."""
        path = Path(self.sqlite_db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()