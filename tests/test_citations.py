from __future__ import annotations

import pytest

from ragtoolkit.evaluation.citations import (
    citation_metrics,
    citation_validity_rate,
    cited_hits,
    parse_citation_numbers,
    parse_citations,
)


def test_parse_citations_preserves_mentions_and_canonicalizes_numbers() -> None:
    text = "Supported [S2], repeated [S2], padded [S01], ignored [s3] and [Sx]."

    assert parse_citations(text) == ["S2", "S2", "S1"]
    assert parse_citation_numbers(text) == [2, 2, 1]
    with pytest.raises(TypeError, match="must be a string"):
        parse_citations(None)  # type: ignore[arg-type]


def test_citation_validity_rate_is_mention_weighted() -> None:
    assert citation_validity_rate("[S1] [S3] [S0]", hit_count=2) == pytest.approx(1 / 3)
    assert citation_validity_rate("No citations.", hit_count=2) == 0.0
    with pytest.raises(ValueError, match="non-negative integer"):
        citation_validity_rate("[S1]", hit_count=-1)


def test_citation_metrics_separate_validity_from_source_attribution() -> None:
    hits = [
        {"text": "noise", "meta": {"source_id": "noise"}},
        {"text": "alpha evidence", "meta": {"source_id": "alpha"}},
        {"text": "distractor", "source_id": "distractor"},
        {"text": "beta evidence", "metadata": {"document_id": "beta"}},
    ]
    answer = "Alpha claim [S2], repeated [S2], distractor [S3], invalid [S9]."

    metrics = citation_metrics(answer, hits, ["alpha", "beta"])

    assert metrics["citation_count"] == 4
    assert metrics["unique_citation_count"] == 3
    assert metrics["valid_citation_count"] == 3
    assert metrics["invalid_citation_count"] == 1
    assert metrics["valid_citation_rate"] == 0.75
    assert metrics["attributable_citation_rate"] == 1.0
    assert metrics["expected_source_precision"] == 0.5
    assert metrics["expected_source_recall"] == 0.5
    assert metrics["valid_citations"] == ["S2", "S3"]
    assert metrics["invalid_citations"] == ["S9"]
    assert metrics["cited_source_ids"] == ["alpha", "distractor"]


def test_source_precision_counts_valid_target_without_metadata_as_incorrect() -> None:
    hits = [{"text": "missing source"}, {"source_id": "alpha", "text": "evidence"}]
    metrics = citation_metrics("Claims [S1] [S2].", hits, ["alpha"])

    assert metrics["valid_citation_rate"] == 1.0
    assert metrics["attributable_citation_rate"] == 0.5
    assert metrics["expected_source_precision"] == 0.5
    assert metrics["expected_source_recall"] == 1.0


def test_no_citations_produces_zero_rates() -> None:
    metrics = citation_metrics("A bare answer.", [{"source_id": "alpha"}], ["alpha"])

    assert metrics["citation_count"] == 0
    assert metrics["valid_citation_rate"] == 0.0
    assert metrics["expected_source_precision"] == 0.0
    assert metrics["expected_source_recall"] == 0.0
    assert metrics["citations"] == []


def test_cited_hits_are_unique_in_first_mention_order() -> None:
    hits = [
        {"id": "one", "source_id": "alpha"},
        {"id": "two", "source_id": "beta"},
    ]

    assert cited_hits("[S2] [S2] [S9] [S1]", hits) == [hits[1], hits[0]]
