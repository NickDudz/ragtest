
from __future__ import annotations
import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict

def get_or_create_collection(storage_dir: str, name: str = "rag") -> "chromadb.api.models.Collection.Collection":
    os.makedirs(storage_dir, exist_ok=True)
    client = chromadb.PersistentClient(path=storage_dir, settings=Settings(allow_reset=True))
    try:
        col = client.get_collection(name)
    except Exception:
        col = client.create_collection(name)
    return col

def upsert_chunks(collection, chunks: List[Dict]) -> None:
    if not chunks:
        return
    collection.upsert(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[c["meta"] for c in chunks],
        embeddings=[c["embedding"] for c in chunks],
    )

def query(collection, query_embeddings: List[List[float]], top_k: int = 6):
    return collection.query(query_embeddings=query_embeddings, n_results=top_k)
