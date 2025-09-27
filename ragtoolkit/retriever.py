
from __future__ import annotations
from typing import List, Dict
from .embeddings import OllamaEmbedder
from . import vectordb

def retrieve(storage_dir: str, embedder: OllamaEmbedder, question: str, top_k: int = 6, min_score: float = 0.0):
    collection = vectordb.get_or_create_collection(storage_dir, "rag")
    qvec = embedder.embed([question])
    res = vectordb.query(collection, qvec, top_k=top_k)
    # Chroma doesn't return distances by default when querying with embeddings.
    # If using similarity scores, one can store and compute externally. Here we only return texts + metadatas.
    docs = []
    for i in range(len(res.get("ids", [[]])[0])):
        docs.append({
            "id": res["ids"][0][i],
            "text": res["documents"][0][i],
            "meta": res["metadatas"][0][i],
            "score": None,
        })
    return docs
