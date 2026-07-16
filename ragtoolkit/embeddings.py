
from __future__ import annotations
import requests
from typing import List, Optional

class OllamaEmbedder:
    def __init__(
        self,
        model: str,
        url: str = "http://localhost:11434",
        *,
        base_url: Optional[str] = None,
    ):
        self.model = model
        self.base_url = (base_url or url).rstrip("/")
        # Keep the existing attribute for callers that inspect it directly.
        self.url = self.base_url

    def embed(self, texts: List[str]) -> List[List[float]]:
        # Batches are handled by caller if needed
        if not texts:
            return []

        resp = requests.post(f"{self.base_url}/api/embed", json={
            "model": self.model,
            "input": texts,
        }, timeout=120)
        resp.raise_for_status()
        try:
            data = resp.json()
        except ValueError as exc:
            raise ValueError("Ollama embed response was not valid JSON") from exc

        if not isinstance(data, dict):
            raise ValueError("Ollama embed response must be a JSON object")
        embeddings = data.get("embeddings")
        if not isinstance(embeddings, list):
            raise ValueError("Ollama embed response is missing an 'embeddings' list")
        if len(embeddings) != len(texts):
            raise ValueError(
                "Ollama embed response count mismatch: "
                f"requested {len(texts)}, received {len(embeddings)}"
            )

        normalized: List[List[float]] = []
        dimension: Optional[int] = None
        for index, vector in enumerate(embeddings):
            if not isinstance(vector, list) or not vector:
                raise ValueError(f"Ollama embedding {index} must be a non-empty list")
            if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in vector):
                raise ValueError(f"Ollama embedding {index} contains a non-numeric value")
            if dimension is None:
                dimension = len(vector)
            elif len(vector) != dimension:
                raise ValueError(
                    f"Ollama embedding {index} has dimension {len(vector)}; expected {dimension}"
                )
            normalized.append([float(value) for value in vector])

        return normalized
