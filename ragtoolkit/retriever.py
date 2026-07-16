
from __future__ import annotations
from typing import List, Dict
from .embeddings import OllamaEmbedder
from . import vectordb

def retrieve(storage_dir: str, embedder: OllamaEmbedder, question: str, top_k: int = 6, min_score: float = 0.0):
    collection = vectordb.get_or_create_collection(storage_dir, "rag")
    qvec = embedder.embed([question])
    res = vectordb.query(collection, qvec, top_k=top_k)
    # Keep min_score for API compatibility. Chroma returns a distance whose scale
    # depends on the collection metric, so it is not treated as a similarity score.
    _ = min_score

    ids = (res.get("ids") or [[]])[0]
    documents = (res.get("documents") or [[]])[0]
    metadatas = (res.get("metadatas") or [[]])[0]
    distances = (res.get("distances") or [[]])[0]
    docs = []
    for i, chunk_id in enumerate(ids):
        distance = distances[i] if i < len(distances) else None
        docs.append({
            "id": chunk_id,
            "text": documents[i] if i < len(documents) else "",
            "meta": metadatas[i] if i < len(metadatas) and metadatas[i] is not None else {},
            "distance": float(distance) if distance is not None else None,
            "score": None,
        })
    return docs
