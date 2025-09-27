
from __future__ import annotations
import requests
from typing import Dict

class OllamaLLM:
    def __init__(self, model: str, temperature: float = 0.2, max_tokens: int = 1024, url: str = "http://localhost:11434"):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.url = url.rstrip("/")

    def generate(self, system: str, user: str) -> str:
        # Use /api/generate in non-streaming mode by default
        payload = {
            "model": self.model,
            "prompt": f"<<SYS>>\n{system}\n<</SYS>>\n\n{user}",
            "options": {
                "temperature": self.temperature,
            },
            "max_tokens": self.max_tokens,
            "stream": False
        }
        resp = requests.post(f"{self.url}/api/generate", json=payload, timeout=600)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()
