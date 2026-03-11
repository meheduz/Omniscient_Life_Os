"""
Omniscient Agent - Long-Term Memory (The Hippocampus)
ChromaDB-backed vector store for persistent context retrieval.
"""

from __future__ import annotations

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import uuid
from datetime import datetime
from typing import List


COLLECTION_NAME = "omniscient_memory"
PERSIST_DIR = "./chroma_db"


def get_memory_client() -> chromadb.PersistentClient:
    """Initialize and return a persistent ChromaDB client."""
    return chromadb.PersistentClient(
        path=PERSIST_DIR,
        settings=Settings(anonymized_telemetry=False),
    )


def get_collection(client: chromadb.PersistentClient):
    """Get or create the main memory collection."""
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2",
    )
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"description": "Omniscient agent long-term memory"},
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
    timestamp = datetime.utcnow().isoformat()
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
