"""Common helper functions."""

import uuid
from datetime import datetime, timezone


def generate_id() -> str:
    """Generate a unique identifier."""
    return uuid.uuid4().hex[:16]


def timestamp_now() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def truncate_text(text: str, max_chars: int = 5000) -> str:
    """Truncate text to a maximum character count."""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks."""
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks
