from __future__ import annotations

from ragtoolkit.vectordb import upsert_chunks


class RecordingCollection:
    def __init__(self) -> None:
        self.payload = None

    def upsert(self, **kwargs) -> None:
        self.payload = kwargs


def test_upsert_omits_none_and_non_scalar_metadata() -> None:
    collection = RecordingCollection()

    upsert_chunks(
        collection,
        [
            {
                "id": "doc@0-4",
                "text": "text",
                "meta": {
                    "source": "doc",
                    "page": None,
                    "span_start": 0,
                    "nested": {"unsupported": True},
                },
                "embedding": [0.1, 0.2],
            }
        ],
    )

    assert collection.payload is not None
    assert collection.payload["metadatas"] == [{"source": "doc", "span_start": 0}]


def test_upsert_supplies_valid_metadata_when_input_is_empty() -> None:
    collection = RecordingCollection()

    upsert_chunks(
        collection,
        [{"id": "doc", "text": "text", "meta": {}, "embedding": [0.1]}],
    )

    assert collection.payload is not None
    assert collection.payload["metadatas"] == [{"source": "unknown"}]
