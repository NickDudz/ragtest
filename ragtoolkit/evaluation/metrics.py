"""Deterministic metrics for retrieval, answer proxies, and latency.

These functions do not call a model and have no third-party dependencies.  A
metric therefore has the same value on every machine for the same serialized
inputs, which makes them suitable for tests and checked-in result artifacts.
"""

from __future__ import annotations

import math
import re
import statistics
from collections.abc import Mapping, Sequence
from typing import Any


_SOURCE_KEYS = ("source_id", "document_id", "doc_id", "source")
_TEXT_KEYS = ("text", "content", "document")
_WHITESPACE_RE = re.compile(r"\s+")
_ABSTENTION_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\b(?:i|we)\s+(?:do not|don't|cannot|can't|am unable to|are unable to)\s+"
        r"(?:know|determine|answer|find|verify)\b",
        r"\b(?:insufficient|inadequate|not enough)\s+"
        r"(?:information|context|evidence|detail)\b",
        r"\b(?:answer|information|detail)\s+is\s+not\s+"
        r"(?:available|provided|stated|specified)\b",
        r"\bnot\s+(?:stated|specified|provided|available)\s+in\s+"
        r"(?:the\s+)?(?:context|sources?|documents?)\b",
        r"\b(?:sources?|context|documents?)\s+(?:do|does)\s+not\s+"
        r"(?:contain|provide|state|specify|establish)\b",
        r"\b(?:cannot|can't|unable to)\s+be\s+(?:determined|answered|verified)\b",
    )
)


def source_id_from_hit(hit: Any) -> str | None:
    """Extract a stable source ID from a retrieval hit.

    Strings are treated as source IDs directly.  Mapping hits may store the ID
    at the top level or in a nested ``meta``/``metadata`` mapping.  This accepts
    both the original toolkit hit shape and the evaluation runner's explicit
    ``source_id`` field without making metrics depend on either implementation.
    """

    if isinstance(hit, str):
        return hit
    if not isinstance(hit, Mapping):
        return None
    for key in _SOURCE_KEYS:
        value = hit.get(key)
        if isinstance(value, str) and value:
            return value
    for metadata_key in ("meta", "metadata"):
        metadata = hit.get(metadata_key)
        if isinstance(metadata, Mapping):
            for key in _SOURCE_KEYS:
                value = metadata.get(key)
                if isinstance(value, str) and value:
                    return value
    return None


def text_from_hit(hit: Any) -> str:
    """Extract retrieved text from a hit, returning an empty string if absent."""

    if not isinstance(hit, Mapping):
        return ""
    for key in _TEXT_KEYS:
        value = hit.get(key)
        if isinstance(value, str):
            return value
    return ""


def recall_at_k(
    expected_sources: Sequence[str],
    ranked_hits: Sequence[Any],
    k: int,
) -> float:
    """Return document recall among the first ``k`` hits.

    Recall is the fraction of unique expected source IDs present at least once
    in the prefix.  An empty expected set returns ``0.0``; unanswerable cases
    should be excluded from aggregate retrieval recall rather than treated as a
    perfect or failed retrieval.
    """

    _validate_k(k)
    expected = {source for source in expected_sources if isinstance(source, str)}
    if not expected:
        return 0.0
    retrieved = {
        source_id
        for hit in ranked_hits[:k]
        if (source_id := source_id_from_hit(hit)) is not None
    }
    return len(expected & retrieved) / len(expected)


def evidence_recall_at_k(
    evidence: Sequence[Mapping[str, Any]],
    ranked_hits: Sequence[Any],
    k: int,
) -> float:
    """Return the fraction of expected evidence anchors covered by top-``k``.

    An anchor is covered when a hit from the same source contains its text after
    whitespace runs are collapsed.  Matching remains case-sensitive.  This
    tolerates the toolkit chunker's newline-to-space conversion without using
    semantic or fuzzy matching.  Empty evidence returns ``0.0``.
    """

    _validate_k(k)
    if not evidence:
        return 0.0
    hits_by_source: dict[str, list[str]] = {}
    for hit in ranked_hits[:k]:
        source_id = source_id_from_hit(hit)
        if source_id is None:
            continue
        hits_by_source.setdefault(source_id, []).append(
            _normalize_whitespace(text_from_hit(hit))
        )

    covered = 0
    for anchor in evidence:
        source = anchor.get("source") if isinstance(anchor, Mapping) else None
        text = anchor.get("text") if isinstance(anchor, Mapping) else None
        if not isinstance(source, str) or not isinstance(text, str) or not text:
            continue
        normalized_anchor = _normalize_whitespace(text)
        if any(normalized_anchor in hit_text for hit_text in hits_by_source.get(source, ())):
            covered += 1
    return covered / len(evidence)


def reciprocal_rank(
    expected_sources: Sequence[str],
    ranked_hits: Sequence[Any],
) -> float:
    """Return reciprocal rank of the first hit from an expected source."""

    expected = {source for source in expected_sources if isinstance(source, str)}
    if not expected:
        return 0.0
    for rank, hit in enumerate(ranked_hits, start=1):
        if source_id_from_hit(hit) in expected:
            return 1.0 / rank
    return 0.0


def mean_reciprocal_rank(
    expected_sources_by_query: Sequence[Sequence[str]],
    ranked_hits_by_query: Sequence[Sequence[Any]],
) -> float:
    """Return mean reciprocal rank across aligned query inputs."""

    if len(expected_sources_by_query) != len(ranked_hits_by_query):
        raise ValueError("expected sources and ranked-hit inputs must have equal length")
    if not expected_sources_by_query:
        return 0.0
    values = [
        reciprocal_rank(expected_sources, ranked_hits)
        for expected_sources, ranked_hits in zip(
            expected_sources_by_query, ranked_hits_by_query
        )
    ]
    return statistics.fmean(values)


def retrieval_metrics(
    expected_sources: Sequence[str],
    ranked_hits: Sequence[Any],
    *,
    evidence: Sequence[Mapping[str, Any]] = (),
    ks: Sequence[int] = (1, 3, 5),
) -> dict[str, float]:
    """Return the standard per-question retrieval metrics used by the lab."""

    output = {"mrr": reciprocal_rank(expected_sources, ranked_hits)}
    for k in ks:
        _validate_k(k)
        output[f"recall_at_{k}"] = recall_at_k(expected_sources, ranked_hits, k)
        if evidence:
            output[f"evidence_recall_at_{k}"] = evidence_recall_at_k(
                evidence, ranked_hits, k
            )
    return output


def required_fact_matches(
    answer: str,
    required_facts: Sequence[Mapping[str, Any]],
) -> dict[str, bool]:
    """Return deterministic case-insensitive phrase matches by fact ID.

    Each fact is considered present when any phrase in its ``any_of`` list is a
    substring of the answer after Unicode case folding and whitespace
    normalization.  The result is a lexical answer-quality proxy, not a claim
    of semantic correctness or entailment.
    """

    normalized_answer = _normalize_for_fact_match(answer)
    matches: dict[str, bool] = {}
    for index, fact in enumerate(required_facts, start=1):
        fact_id = fact.get("id") if isinstance(fact, Mapping) else None
        if not isinstance(fact_id, str) or not fact_id:
            fact_id = f"fact_{index}"
        alternatives = fact.get("any_of", ()) if isinstance(fact, Mapping) else ()
        if isinstance(alternatives, (str, bytes)) or not isinstance(
            alternatives, Sequence
        ):
            alternatives = ()
        matches[fact_id] = any(
            isinstance(alternative, str)
            and bool(alternative.strip())
            and _normalize_for_fact_match(alternative) in normalized_answer
            for alternative in alternatives
        )
    return matches


def required_fact_coverage(
    answer: str,
    required_facts: Sequence[Mapping[str, Any]],
) -> float:
    """Return the fraction of required facts matched lexically in ``answer``."""

    if not required_facts:
        return 0.0
    matches = required_fact_matches(answer, required_facts)
    return sum(matches.values()) / len(required_facts)


def is_abstention(answer: str) -> bool:
    """Return whether ``answer`` matches the lab's documented abstention heuristic.

    Empty/whitespace-only output counts as an abstention.  The phrase list is
    intentionally conservative and deterministic; it is not a model judge.
    """

    if not isinstance(answer, str) or not answer.strip():
        return True
    return any(pattern.search(answer) is not None for pattern in _ABSTENTION_PATTERNS)


def abstention_correct(answer: str, answerable: bool) -> bool:
    """Return whether abstention behavior agrees with the golden answerability."""

    if not isinstance(answerable, bool):
        raise TypeError("answerable must be a boolean")
    abstained = is_abstention(answer)
    return abstained if not answerable else not abstained


def abstention_accuracy(
    answers: Sequence[str],
    answerable: Sequence[bool],
) -> float:
    """Return mean correctness of the deterministic abstention heuristic."""

    if len(answers) != len(answerable):
        raise ValueError("answers and answerability labels must have equal length")
    if not answers:
        return 0.0
    return statistics.fmean(
        float(abstention_correct(answer, expected_answerable))
        for answer, expected_answerable in zip(answers, answerable)
    )


def percentile(values: Sequence[float], percent: float) -> float:
    """Return a linearly interpolated percentile for finite numeric values.

    ``percent`` is in the inclusive range 0-100.  The interpolation matches the
    common ``(n - 1) * p`` definition used by NumPy's default percentile method.
    """

    samples = _validated_latencies(values, allow_negative=True)
    if not samples:
        raise ValueError("percentile requires at least one value")
    if isinstance(percent, bool) or not isinstance(percent, (int, float)):
        raise TypeError("percent must be numeric")
    if not math.isfinite(float(percent)) or not 0.0 <= float(percent) <= 100.0:
        raise ValueError("percent must be between 0 and 100")
    ordered = sorted(samples)
    position = (len(ordered) - 1) * float(percent) / 100.0
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def latency_percentiles(values_ms: Sequence[float]) -> dict[str, float | int]:
    """Summarize non-negative latency samples in milliseconds.

    The returned shape is stable for result serialization and includes count,
    mean, minimum, p50, p95, and maximum.  Empty input returns a count of zero
    and zero-valued summaries so partially failed runs can still be serialized.
    """

    samples = _validated_latencies(values_ms, allow_negative=False)
    if not samples:
        return {
            "count": 0,
            "mean_ms": 0.0,
            "min_ms": 0.0,
            "p50_ms": 0.0,
            "p95_ms": 0.0,
            "max_ms": 0.0,
        }
    return {
        "count": len(samples),
        "mean_ms": statistics.fmean(samples),
        "min_ms": min(samples),
        "p50_ms": percentile(samples, 50.0),
        "p95_ms": percentile(samples, 95.0),
        "max_ms": max(samples),
    }


def _validate_k(k: int) -> None:
    if isinstance(k, bool) or not isinstance(k, int) or k <= 0:
        raise ValueError("k must be a positive integer")


def _normalize_whitespace(value: str) -> str:
    return _WHITESPACE_RE.sub(" ", value).strip()


def _normalize_for_fact_match(value: str) -> str:
    if not isinstance(value, str):
        return ""
    return _normalize_whitespace(value).casefold()


def _validated_latencies(
    values: Sequence[float],
    *,
    allow_negative: bool,
) -> list[float]:
    samples: list[float] = []
    for index, value in enumerate(values):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"latency value at index {index} must be numeric")
        converted = float(value)
        if not math.isfinite(converted):
            raise ValueError(f"latency value at index {index} must be finite")
        if not allow_negative and converted < 0:
            raise ValueError(f"latency value at index {index} must be non-negative")
        samples.append(converted)
    return samples


__all__ = [
    "abstention_accuracy",
    "abstention_correct",
    "evidence_recall_at_k",
    "is_abstention",
    "latency_percentiles",
    "mean_reciprocal_rank",
    "percentile",
    "recall_at_k",
    "reciprocal_rank",
    "required_fact_coverage",
    "required_fact_matches",
    "retrieval_metrics",
    "source_id_from_hit",
    "text_from_hit",
]
