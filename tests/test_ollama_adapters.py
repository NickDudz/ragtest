from __future__ import annotations

from typing import Any

import pytest

from ragtoolkit.embeddings import OllamaEmbedder
from ragtoolkit.llm import OllamaLLM


class FakeResponse:
    def __init__(self, payload: Any):
        self.payload = payload
        self.raise_for_status_called = False

    def raise_for_status(self) -> None:
        self.raise_for_status_called = True

    def json(self) -> Any:
        if isinstance(self.payload, BaseException):
            raise self.payload
        return self.payload


def test_embedder_posts_batched_api_embed_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []
    response = FakeResponse({"embeddings": [[1, 2.5], [3.0, 4]]})

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        calls.append({"url": url, **kwargs})
        return response

    monkeypatch.setattr("ragtoolkit.embeddings.requests.post", fake_post)
    embedder = OllamaEmbedder("embed-model", base_url="http://ollama.test/")

    assert embedder.embed(["first", "second"]) == [[1.0, 2.5], [3.0, 4.0]]
    assert calls == [
        {
            "url": "http://ollama.test/api/embed",
            "json": {"model": "embed-model", "input": ["first", "second"]},
            "timeout": 120,
        }
    ]
    assert response.raise_for_status_called


def test_embedder_empty_batch_does_not_call_ollama(monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected_post(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("empty embedding input should not make an HTTP request")

    monkeypatch.setattr("ragtoolkit.embeddings.requests.post", unexpected_post)
    assert OllamaEmbedder("embed-model").embed([]) == []


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"embeddings": [[1.0, 2.0]]}, "response count mismatch"),
        ({"embeddings": [[1.0], [1.0, 2.0]]}, "dimension"),
        ({"embeddings": [[1.0], [True]]}, "non-numeric"),
        ({"embedding": [[1.0], [2.0]]}, "missing an 'embeddings' list"),
    ],
)
def test_embedder_rejects_malformed_responses(
    monkeypatch: pytest.MonkeyPatch,
    payload: dict[str, Any],
    message: str,
) -> None:
    monkeypatch.setattr(
        "ragtoolkit.embeddings.requests.post", lambda *args, **kwargs: FakeResponse(payload)
    )

    with pytest.raises(ValueError, match=message):
        OllamaEmbedder("embed-model").embed(["first", "second"])


def test_generate_posts_options_and_returns_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []
    response = FakeResponse(
        {
            "model": "generation-model@digest",
            "created_at": "2026-07-16T12:00:00Z",
            "response": "  Supported answer [S1].  ",
            "done": True,
            "done_reason": "stop",
            "total_duration": 1_000,
            "load_duration": 100,
            "prompt_eval_count": 40,
            "prompt_eval_duration": 200,
            "eval_count": 8,
            "eval_duration": 700,
        }
    )

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        calls.append({"url": url, **kwargs})
        return response

    monkeypatch.setattr("ragtoolkit.llm.requests.post", fake_post)
    llm = OllamaLLM(
        "generation-model",
        temperature=0.0,
        max_tokens=256,
        base_url="http://ollama.test/",
        seed=7,
        context_window=8192,
    )

    answer, metadata = llm.generate_with_metadata("System prompt", "User prompt")

    assert answer == "Supported answer [S1]."
    assert calls == [
        {
            "url": "http://ollama.test/api/generate",
            "json": {
                "model": "generation-model",
                "system": "System prompt",
                "prompt": "User prompt",
                "options": {
                    "temperature": 0.0,
                    "num_predict": 256,
                    "seed": 7,
                    "num_ctx": 8192,
                },
                "stream": False,
            },
            "timeout": 600,
        }
    ]
    assert response.raise_for_status_called
    assert metadata == {
        "model": "generation-model@digest",
        "created_at": "2026-07-16T12:00:00Z",
        "done": True,
        "done_reason": "stop",
        "total_duration": 1_000,
        "load_duration": 100,
        "prompt_eval_count": 40,
        "prompt_eval_duration": 200,
        "eval_count": 8,
        "eval_duration": 700,
    }


def test_generate_keeps_string_api_and_omits_unset_seed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_payload: dict[str, Any] = {}

    def fake_post(url: str, **kwargs: Any) -> FakeResponse:
        captured_payload.update(kwargs["json"])
        return FakeResponse({"response": " answer ", "done": True})

    monkeypatch.setattr("ragtoolkit.llm.requests.post", fake_post)
    llm = OllamaLLM("generation-model", temperature=0.2, max_tokens=64)

    assert llm.generate("system", "user") == "answer"
    assert captured_payload["options"] == {"temperature": 0.2, "num_predict": 64}


def test_generate_rejects_non_string_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "ragtoolkit.llm.requests.post",
        lambda *args, **kwargs: FakeResponse({"response": ["not", "text"]}),
    )

    with pytest.raises(ValueError, match="non-string"):
        OllamaLLM("generation-model").generate("system", "user")
