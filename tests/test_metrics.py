from __future__ import annotations

import math

import pytest

from ragtoolkit.evaluation.metrics import (
    abstention_accuracy,
    abstention_correct,
    evidence_recall_at_k,
    is_abstention,
    latency_percentiles,
    mean_reciprocal_rank,
    percentile,
    recall_at_k,
    reciprocal_rank,
    required_fact_coverage,
    required_fact_matches,
    retrieval_metrics,
    source_id_from_hit,
    text_from_hit,
)


def _runner_hit(source_id: str, text: str) -> dict:
    return {"text": text, "meta": {"source_id": source_id}}


def test_hit_accessors_accept_runner_and_independent_shapes() -> None:
    assert source_id_from_hit(_runner_hit("alpha", "passage")) == "alpha"
    assert source_id_from_hit({"metadata": {"document_id": "beta"}}) == "beta"
    assert source_id_from_hit({"source_id": "gamma"}) == "gamma"
    assert source_id_from_hit("delta") == "delta"
    assert source_id_from_hit({"text": "missing metadata"}) is None
    assert text_from_hit({"content": "passage"}) == "passage"
    assert text_from_hit({"other": "value"}) == ""


def test_recall_at_k_and_reciprocal_rank_use_ranked_unique_sources() -> None:
    hits = [
        _runner_hit("noise", "irrelevant"),
        _runner_hit("beta", "beta evidence"),
        _runner_hit("alpha", "alpha evidence"),
        _runner_hit("beta", "duplicate beta chunk"),
    ]
    expected = ["alpha", "beta"]

    assert recall_at_k(expected, hits, 1) == 0.0
    assert recall_at_k(expected, hits, 2) == 0.5
    assert recall_at_k(expected, hits, 3) == 1.0
    assert reciprocal_rank(expected, hits) == 0.5


def test_retrieval_edge_cases_are_explicit() -> None:
    hits = [{"source_id": "alpha", "text": "text"}]

    assert recall_at_k([], hits, 1) == 0.0
    assert reciprocal_rank([], hits) == 0.0
    assert reciprocal_rank(["missing"], hits) == 0.0
    assert evidence_recall_at_k([], hits, 1) == 0.0
    with pytest.raises(ValueError, match="positive integer"):
        recall_at_k(["alpha"], hits, 0)
    with pytest.raises(ValueError, match="positive integer"):
        evidence_recall_at_k([], hits, -1)


def test_evidence_recall_matches_source_and_normalized_whitespace() -> None:
    evidence = [
        {"source": "beta", "text": "line one\nline two"},
        {"source": "alpha", "text": "Exact Alpha Anchor"},
    ]
    hits = [
        _runner_hit("noise", "line one line two"),
        _runner_hit("beta", "prefix line one   line two suffix"),
        {"source_id": "alpha", "content": "Exact Alpha Anchor and details"},
    ]

    assert evidence_recall_at_k(evidence, hits, 1) == 0.0
    assert evidence_recall_at_k(evidence, hits, 2) == 0.5
    assert evidence_recall_at_k(evidence, hits, 3) == 1.0
    assert evidence_recall_at_k(
        [{"source": "alpha", "text": "exact alpha anchor"}], hits, 3
    ) == 0.0


def test_mrr_and_metric_bundle() -> None:
    expected_by_query = [["alpha"], ["beta"], ["missing"]]
    hits_by_query = [
        [{"source_id": "alpha"}],
        [{"source_id": "noise"}, {"source_id": "beta"}],
        [{"source_id": "noise"}],
    ]
    assert mean_reciprocal_rank(expected_by_query, hits_by_query) == pytest.approx(0.5)
    with pytest.raises(ValueError, match="equal length"):
        mean_reciprocal_rank(expected_by_query, hits_by_query[:1])

    bundle = retrieval_metrics(
        ["beta"],
        hits_by_query[1],
        evidence=[{"source": "beta", "text": "target"}],
        ks=(1, 2),
    )
    assert bundle == {
        "mrr": 0.5,
        "recall_at_1": 0.0,
        "evidence_recall_at_1": 0.0,
        "recall_at_2": 1.0,
        "evidence_recall_at_2": 0.0,
    }


def test_required_fact_matching_is_casefolded_and_whitespace_normalized() -> None:
    facts = [
        {"id": "frequency", "any_of": ["EVERY 24 HOURS", "daily"]},
        {"id": "deadline", "any_of": ["within 15 minutes"]},
        {"id": "owner", "any_of": ["Security Operations"]},
    ]
    answer = "The snapshot runs every   24 hours and action follows within 15 minutes."

    assert required_fact_matches(answer, facts) == {
        "frequency": True,
        "deadline": True,
        "owner": False,
    }
    assert required_fact_coverage(answer, facts) == pytest.approx(2 / 3)
    assert required_fact_coverage(answer, []) == 0.0


@pytest.mark.parametrize(
    "answer",
    [
        "",
        "I don't know based on the provided context.",
        "There is not enough information to determine that.",
        "The sources do not provide that detail.",
        "It cannot be determined from these documents.",
    ],
)
def test_abstention_heuristic_detects_documented_phrases(answer: str) -> None:
    assert is_abstention(answer)


def test_abstention_correctness_and_accuracy() -> None:
    supported = "The required interval is 15 minutes [S1]."
    abstained = "I don't know based on the provided context."

    assert not is_abstention(supported)
    assert abstention_correct(supported, answerable=True)
    assert abstention_correct(abstained, answerable=False)
    assert not abstention_correct(abstained, answerable=True)
    assert abstention_accuracy(
        [supported, abstained, abstained], [True, False, True]
    ) == pytest.approx(2 / 3)
    assert abstention_accuracy([], []) == 0.0
    with pytest.raises(ValueError, match="equal length"):
        abstention_accuracy([supported], [])


def test_percentiles_use_linear_interpolation() -> None:
    assert percentile([0, 10], 25) == 2.5
    assert percentile([10, 20, 30, 40], 50) == 25.0
    assert percentile([10, 20, 30, 40], 95) == 38.5
    with pytest.raises(ValueError, match="at least one"):
        percentile([], 50)
    with pytest.raises(ValueError, match="between 0 and 100"):
        percentile([1], 101)


def test_latency_summary_and_invalid_samples() -> None:
    assert latency_percentiles([10, 20, 30, 40]) == {
        "count": 4,
        "mean_ms": 25.0,
        "min_ms": 10.0,
        "p50_ms": 25.0,
        "p95_ms": 38.5,
        "max_ms": 40.0,
    }
    assert latency_percentiles([]) == {
        "count": 0,
        "mean_ms": 0.0,
        "min_ms": 0.0,
        "p50_ms": 0.0,
        "p95_ms": 0.0,
        "max_ms": 0.0,
    }
    with pytest.raises(ValueError, match="non-negative"):
        latency_percentiles([1, -1])
    with pytest.raises(ValueError, match="finite"):
        latency_percentiles([math.inf])
    with pytest.raises(TypeError, match="numeric"):
        latency_percentiles([True])
