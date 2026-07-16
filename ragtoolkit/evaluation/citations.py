"""Deterministic parsing and source-attribution checks for ``[S#]`` citations."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from .metrics import source_id_from_hit


_CITATION_RE = re.compile(r"\[S([0-9]+)\]")


def parse_citations(text: str) -> list[str]:
    """Return citation IDs in mention order, retaining repeated mentions.

    Only the documented uppercase numeric form (for example, ``[S2]``) is
    parsed.  A parsed ID can still be invalid for a particular answer when its
    one-based index is zero or exceeds the number of retrieval hits.
    """

    if not isinstance(text, str):
        raise TypeError("citation text must be a string")
    return [f"S{int(match.group(1))}" for match in _CITATION_RE.finditer(text)]


def parse_citation_numbers(text: str) -> list[int]:
    """Return one-based citation numbers in mention order."""

    return [int(citation[1:]) for citation in parse_citations(text)]


def citation_validity_rate(text: str, hit_count: int) -> float:
    """Return the fraction of citation mentions that index an available hit.

    No citation mentions yields ``0.0``: the answer did not demonstrate
    citation reliability, even though it also made no out-of-range reference.
    """

    if isinstance(hit_count, bool) or not isinstance(hit_count, int) or hit_count < 0:
        raise ValueError("hit_count must be a non-negative integer")
    numbers = parse_citation_numbers(text)
    if not numbers:
        return 0.0
    return sum(1 <= number <= hit_count for number in numbers) / len(numbers)


def citation_metrics(
    answer: str,
    ranked_hits: Sequence[Any],
    expected_sources: Sequence[str],
) -> dict[str, Any]:
    """Measure citation ID validity and expected-source attribution.

    Validity is mention-weighted, so repeated bad IDs remain visible.  Source
    precision considers each unique valid citation target once; source recall
    considers each unique expected source once.  An answer with no applicable
    denominator receives ``0.0`` for that metric and should be excluded from
    aggregate expected-source metrics when the golden case is unanswerable.

    This check establishes that a citation points to a retrieved hit from an
    expected document.  It does not claim that the cited passage entails the
    surrounding sentence.
    """

    numbers = parse_citation_numbers(answer)
    hit_count = len(ranked_hits)
    valid_numbers = [number for number in numbers if 1 <= number <= hit_count]
    invalid_numbers = [number for number in numbers if not 1 <= number <= hit_count]
    unique_numbers = _ordered_unique(numbers)
    unique_valid_numbers = _ordered_unique(valid_numbers)
    unique_invalid_numbers = _ordered_unique(invalid_numbers)

    expected = {
        source for source in expected_sources if isinstance(source, str) and source
    }
    cited_sources: list[str] = []
    correctly_attributed_targets = 0
    attributable_targets = 0
    for number in unique_valid_numbers:
        source_id = source_id_from_hit(ranked_hits[number - 1])
        if source_id is not None:
            attributable_targets += 1
            if source_id not in cited_sources:
                cited_sources.append(source_id)
        if source_id in expected:
            correctly_attributed_targets += 1

    cited_source_set = set(cited_sources)
    source_precision = (
        correctly_attributed_targets / len(unique_valid_numbers)
        if unique_valid_numbers
        else 0.0
    )
    source_recall = len(expected & cited_source_set) / len(expected) if expected else 0.0
    validity_rate = (
        len(valid_numbers) / len(numbers)
        if numbers
        else 0.0
    )
    attributable_rate = (
        attributable_targets / len(unique_valid_numbers)
        if unique_valid_numbers
        else 0.0
    )

    return {
        "citation_count": len(numbers),
        "unique_citation_count": len(unique_numbers),
        "valid_citation_count": len(valid_numbers),
        "invalid_citation_count": len(invalid_numbers),
        "valid_citation_rate": validity_rate,
        "attributable_citation_rate": attributable_rate,
        "expected_source_precision": source_precision,
        "expected_source_recall": source_recall,
        "citations": [f"S{number}" for number in numbers],
        "valid_citations": [f"S{number}" for number in unique_valid_numbers],
        "invalid_citations": [f"S{number}" for number in unique_invalid_numbers],
        "cited_source_ids": cited_sources,
        "expected_source_ids": sorted(expected),
    }


def cited_hits(answer: str, ranked_hits: Sequence[Any]) -> list[Any]:
    """Return uniquely cited, in-range hits in first-mention order."""

    numbers = _ordered_unique(parse_citation_numbers(answer))
    return [ranked_hits[number - 1] for number in numbers if 1 <= number <= len(ranked_hits)]


def _ordered_unique(values: Sequence[int]) -> list[int]:
    seen: set[int] = set()
    output: list[int] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            output.append(value)
    return output


__all__ = [
    "citation_metrics",
    "citation_validity_rate",
    "cited_hits",
    "parse_citation_numbers",
    "parse_citations",
]
