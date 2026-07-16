
from __future__ import annotations
import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional


def _chroma_metadata(metadata: Optional[Dict]) -> Dict:
    """Return metadata containing only Chroma-supported scalar values.

    Loaders use ``None`` for fields that are not applicable (for example, the
    page number of a Markdown file). Chroma rejects those values during an
    upsert, so omit them while preserving every meaningful scalar.
    """
    if not metadata:
        return {"source": "unknown"}
    cleaned = {
        key: value
        for key, value in metadata.items()
        if isinstance(value, (str, int, float, bool))
    }
    return cleaned or {"source": "unknown"}

def get_or_create_collection(
    storage_dir: str,
    name: str = "rag",
    metadata: Optional[Dict] = None,
) -> "chromadb.api.models.Collection.Collection":
    os.makedirs(storage_dir, exist_ok=True)
    client = chromadb.PersistentClient(
        path=storage_dir,
        settings=Settings(allow_reset=True, anonymized_telemetry=False),
    )
    return client.get_or_create_collection(name, metadata=metadata)

def upsert_chunks(collection, chunks: List[Dict]) -> None:
    if not chunks:
        return
    collection.upsert(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[_chroma_metadata(c.get("meta")) for c in chunks],
        embeddings=[c["embedding"] for c in chunks],
    )

def query(collection, query_embeddings: List[List[float]], top_k: int = 6):
    return collection.query(
        query_embeddings=query_embeddings,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
