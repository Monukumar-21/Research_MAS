"""Pinecone vector memory for semantic retrieval."""

import asyncio
import warnings
from typing import Any, Optional

with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=FutureWarning)
    import google.generativeai as genai

from pinecone import Pinecone, ServerlessSpec

from memory.base import BaseMemory
from configs.config import settings
from utils.logger import get_logger
from utils.helpers import generate_id, chunk_text

logger = get_logger(__name__)

class PineconeMemory(BaseMemory):
    """Semantic vector memory backed by Pinecone."""

    def __init__(self) -> None:
        self.pc: Optional[Pinecone] = None
        self.index = None

    async def initialize(self) -> None:
        if not settings.pinecone_api_key:
            logger.warning("Pinecone API key not set.")
            return

        genai.configure(api_key=settings.gemini_api_key)

        try:
            # FIX: Async thread offloading for blocking connections
            self.pc = await asyncio.to_thread(Pinecone, api_key=settings.pinecone_api_key)
            existing = await asyncio.to_thread(lambda: [idx.name for idx in self.pc.list_indexes()])
            
            if settings.pinecone_index_name not in existing:
                await asyncio.to_thread(
                    self.pc.create_index,
                    name=settings.pinecone_index_name,
                    dimension=settings.pinecone_dimension,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region=settings.pinecone_environment),
                )
            
            self.index = self.pc.Index(settings.pinecone_index_name)
            logger.info("Pinecone initialized: %s", settings.pinecone_index_name)
        except Exception as e:
            logger.error("Pinecone initialization failed: %s", e)
            self.index = None

    def _embed_batch(self, texts: list[str], task_type: str) -> list[list[float]]:
        """Sync helper for batch embedding."""
        try:
            result = genai.embed_content(
                model=settings.gemini_embedding_model,
                content=texts,
                task_type=task_type,
                output_dimensionality=settings.pinecone_dimension,
            )
            # Handle single string return type vs batch return type from Gemini API
            return result["embedding"] if isinstance(result["embedding"][0], list) else [result["embedding"]]
        except Exception as e:
            logger.error("Failed to generate Gemini embeddings (Check your GEMINI_API_KEY in .env): %s", e)
            # Return zero embeddings so the workflow doesn't completely crash
            return [[0.0] * settings.pinecone_dimension for _ in texts]

    async def upsert_document(self, doc_id: str, text: str, metadata: dict | None = None) -> int:
        if self.index is None: return 0

        chunks = chunk_text(text, chunk_size=800, overlap=150)
        
        # FIX: Batch embedding in a separate thread
        embeddings = await asyncio.to_thread(self._embed_batch, chunks, "retrieval_document")

        vectors = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vec_id = f"{doc_id}_chunk_{i}"
            meta = {**(metadata or {}), "text": chunk, "chunk_index": i, "doc_id": doc_id}
            vectors.append({"id": vec_id, "values": embedding, "metadata": meta})

        if vectors:
            await asyncio.to_thread(self.index.upsert, vectors=vectors)
        
        return len(vectors)

    async def query_similar(self, query: str, top_k: int = 5, filter_dict: dict | None = None) -> list[dict]:
        if self.index is None: return []

        # Thread offloading
        embedding = await asyncio.to_thread(self._embed_batch, [query], "retrieval_query")
        
        results = await asyncio.to_thread(
            self.index.query,
            vector=embedding[0],
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict,
        )

        return [
            {
                "id": m["id"],
                "score": m["score"],
                "text": m.get("metadata", {}).get("text", ""),
                "metadata": m.get("metadata", {}),
            }
            for m in results.get("matches", [])
        ]

    async def store(self, key: str, value: Any, metadata: dict | None = None) -> None:
        if isinstance(value, str):
            await self.upsert_document(key, value, metadata)

    async def retrieve(self, key: str) -> Any:
        if self.index is None: return None
        
        results = await asyncio.to_thread(
            self.index.query,
            vector=[0.0] * settings.pinecone_dimension,
            filter={"doc_id": key},
            top_k=100,
            include_metadata=True,
        )
        
        chunks = sorted(
            [m for m in results.get("matches", []) if m.get("metadata", {}).get("doc_id") == key],
            key=lambda x: x.get("metadata", {}).get("chunk_index", 0)
        )
        return "".join([m["metadata"]["text"] for m in chunks]) if chunks else None

    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        return await self.query_similar(query, top_k)

    async def close(self) -> None:
        logger.info("Pinecone memory closed")