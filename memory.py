"""
Omniscient Agent - Long-Term Memory (The Hippocampus)
ChromaDB-backed vector store for persistent context retrieval.
"""

from __future__ import annotations

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import uuid
import hashlib
import math
import re
from datetime import datetime, timezone
from typing import Any, Dict, List

from config import (
    EMBEDDING_MODEL,
    MEMORY_COLLECTION_NAME,
    MEMORY_PERSIST_DIR,
    OFFLINE_EMBEDDING_DIMENSIONS,
)

COLLECTION_NAME = MEMORY_COLLECTION_NAME
PERSIST_DIR = MEMORY_PERSIST_DIR


class LocalHashEmbeddingFunction(EmbeddingFunction[Documents]):
    """
    Lightweight offline embedding fallback.
    Uses token hashing into a fixed-size vector to keep memory features available
    when remote model download is unavailable.
    """

    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions

    def __call__(self, input: Documents) -> Embeddings:
        embeddings: List[List[float]] = []
        for text in input:
            vec = [0.0] * self.dimensions
            tokens = re.findall(r"[A-Za-z0-9_]+", (text or "").lower())
            if not tokens:
                embeddings.append(vec)
                continue
            for token in tokens:
                digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
                bucket = int.from_bytes(digest, "big") % self.dimensions
                vec[bucket] += 1.0
            norm = math.sqrt(sum(v * v for v in vec))
            if norm > 0:
                vec = [v / norm for v in vec]
            embeddings.append(vec)
        return embeddings

    @staticmethod
    def name() -> str:
        return "local_hash"

    def get_config(self) -> Dict[str, Any]:
        return {"dimensions": self.dimensions}

    @staticmethod
    def build_from_config(config: Dict[str, Any]) -> "LocalHashEmbeddingFunction":
        return LocalHashEmbeddingFunction(
            dimensions=int(config.get("dimensions", OFFLINE_EMBEDDING_DIMENSIONS))
        )

    def is_legacy(self) -> bool:
        return False


def get_memory_client() -> chromadb.PersistentClient:
    """Initialize and return a persistent ChromaDB client with optimized settings."""
    return chromadb.PersistentClient(
        path=PERSIST_DIR,
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True,
            is_persistent=True,
        ),
    )


def get_collection(client: chromadb.PersistentClient):
    """Get or create the main memory collection with cached embedding function."""
    # Cache embedding function to avoid reloading model.
    # Prefer sentence-transformers semantic embeddings; fallback to local hash embeddings
    # so the app keeps working in offline/restricted environments.
    if not hasattr(get_collection, "_ef_cache"):
        try:
            get_collection._ef_cache = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=EMBEDDING_MODEL,
            )
            get_collection._ef_backend = f"sentence-transformers/{EMBEDDING_MODEL}"
        except Exception as exc:
            print(
                f"[Memory] Falling back to local hash embeddings (semantic quality reduced): {exc}"
            )
            get_collection._ef_cache = LocalHashEmbeddingFunction(
                dimensions=OFFLINE_EMBEDDING_DIMENSIONS
            )
            get_collection._ef_backend = f"local-hash-{OFFLINE_EMBEDDING_DIMENSIONS}"
    
    collection_name = COLLECTION_NAME
    if getattr(get_collection, "_ef_backend", "").startswith("local-hash"):
        collection_name = f"{COLLECTION_NAME}_offline"

    return client.get_or_create_collection(
        name=collection_name,
        embedding_function=get_collection._ef_cache,
        metadata={
            "description": "Omniscient agent long-term memory",
            "embedding_backend": getattr(get_collection, "_ef_backend", "unknown"),
        },
    )


def save_memory(fact: str, collection=None) -> str:
    """
    Save a fact into ChromaDB.
    Returns the ID of the stored document.
    """
    if collection is None:
        client = get_memory_client()
        collection = get_collection(client)

    doc_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    metadata = {"timestamp": timestamp, "type": "fact"}

    collection.add(
        ids=[doc_id],
        documents=[fact],
        metadatas=[metadata],
    )
    return doc_id


def search_memory(query: str, n_results: int = 5, collection=None) -> List[dict]:
    """
    Search ChromaDB for relevant past context.
    Returns list of dicts with 'document', 'metadata', 'distance'.
    """
    if collection is None:
        client = get_memory_client()
        collection = get_collection(client)

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    output = []
    if results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            output.append({
                "document": doc,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else None,
            })
    return output


def init_memory() -> chromadb.Collection:
    """Initialize memory and return the collection. Call at daemon startup."""
    client = get_memory_client()
    return get_collection(client)
