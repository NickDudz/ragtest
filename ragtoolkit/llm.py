
from __future__ import annotations
import requests
from typing import Dict, Optional, Tuple

class OllamaLLM:
    def __init__(
        self,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        url: str = "http://localhost:11434",
        *,
        base_url: Optional[str] = None,
        seed: Optional[int] = None,
        context_window: Optional[int] = None,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.seed = seed
        self.context_window = context_window
        self.base_url = (base_url or url).rstrip("/")
        # Keep the existing attribute for callers that inspect it directly.
        self.url = self.base_url

    def generate(self, system: str, user: str) -> str:
        response, _ = self.generate_with_metadata(system, user)
        return response

    def generate_with_metadata(self, system: str, user: str) -> Tuple[str, Dict[str, object]]:
        # Use /api/generate in non-streaming mode by default
        options = {
            "temperature": self.temperature,
            "num_predict": self.max_tokens,
        }
        if self.seed is not None:
            options["seed"] = self.seed
        if self.context_window is not None:
            options["num_ctx"] = self.context_window

        payload = {
            "model": self.model,
            "system": system,
            "prompt": user,
            "options": options,
            "stream": False
        }
        resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=600)
        resp.raise_for_status()
        try:
            data = resp.json()
        except ValueError as exc:
            raise ValueError("Ollama generate response was not valid JSON") from exc
        if not isinstance(data, dict):
            raise ValueError("Ollama generate response must be a JSON object")

        response = data.get("response", "")
        if not isinstance(response, str):
            raise ValueError("Ollama generate response has a non-string 'response' field")

        metadata: Dict[str, object] = {
            "model": data.get("model", self.model),
            "created_at": data.get("created_at"),
            "done": data.get("done"),
            "done_reason": data.get("done_reason"),
            "total_duration": data.get("total_duration"),
            "load_duration": data.get("load_duration"),
            "prompt_eval_count": data.get("prompt_eval_count"),
            "prompt_eval_duration": data.get("prompt_eval_duration"),
            "eval_count": data.get("eval_count"),
            "eval_duration": data.get("eval_duration"),
        }
        return response.strip(), metadata
