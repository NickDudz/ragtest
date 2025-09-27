
from __future__ import annotations
import requests
from typing import List

class OllamaEmbedder:
    def __init__(self, model: str, url: str = "http://localhost:11434"):
        self.model = model
        self.url = url.rstrip("/")

    def embed(self, texts: List[str]) -> List[List[float]]:
        # Batches are handled by caller if needed
        resp = requests.post(f"{self.url}/api/embeddings", json={
            "model": self.model,
            "input": texts,
        }, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        # Ollama returns {"embeddings": [[...], [...]]}
        return data.get("embeddings", [])
