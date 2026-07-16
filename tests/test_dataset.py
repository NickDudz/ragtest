from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from ragtoolkit.evaluation.dataset import (
    DatasetValidationError,
    load_golden_dataset,
    load_manifest,
    sha256_file,
    validate_dataset,
    validate_golden_dataset,
    validate_manifest,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
EVALUATION_DIR = REPO_ROOT / "evaluation"
MANIFEST_PATH = EVALUATION_DIR / "corpus_manifest.yaml"
GOLDEN_PATH = EVALUATION_DIR / "golden.jsonl"


def test_checked_in_dataset_passes_strict_validation() -> None:
    manifest, questions = validate_dataset(MANIFEST_PATH, GOLDEN_PATH)

    assert manifest["schema_version"] == "1.0"
    assert len(manifest["documents"]) == 8
    assert len(questions) == 30
    assert sum(question["answerable"] for question in questions) == 25
    assert sum(not question["answerable"] for question in questions) == 5

    document_ids = {document["id"] for document in manifest["documents"]}
    assert len(document_ids) == 8
    for document in manifest["documents"]:
        path = EVALUATION_DIR / document["path"]
        assert path.is_file()
        assert sha256_file(path) == document["sha256"]


def test_manifest_rejects_hash_drift() -> None:
    manifest = load_manifest(MANIFEST_PATH)
    manifest["documents"][0]["sha256"] = "0" * 64

    with pytest.raises(DatasetValidationError, match="sha256 mismatch"):
        validate_manifest(manifest, EVALUATION_DIR)


def test_golden_dataset_rejects_nonexistent_exact_anchor() -> None:
    manifest = load_manifest(MANIFEST_PATH)
    questions = load_golden_dataset(GOLDEN_PATH)
    questions[0]["evidence"][0]["text"] = "This anchor is deliberately absent."

    with pytest.raises(DatasetValidationError, match="not an exact substring"):
        validate_golden_dataset(questions, manifest, EVALUATION_DIR)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda manifest: manifest.pop("license"), "missing field.*license"),
        (lambda manifest: manifest.update({"unexpected": True}), "unknown field.*unexpected"),
        (
            lambda manifest: manifest["documents"][0].pop("provenance"),
            "missing field.*provenance",
        ),
    ],
)
def test_manifest_rejects_schema_drift(mutation, message: str) -> None:
    manifest = load_manifest(MANIFEST_PATH)
    mutation(manifest)

    with pytest.raises(DatasetValidationError, match=message):
        validate_manifest(manifest, EVALUATION_DIR)


def test_golden_dataset_rejects_duplicate_question_id() -> None:
    manifest = load_manifest(MANIFEST_PATH)
    questions = load_golden_dataset(GOLDEN_PATH)
    questions[1]["id"] = questions[0]["id"]

    with pytest.raises(DatasetValidationError, match="duplicate question id"):
        validate_golden_dataset(questions, manifest, EVALUATION_DIR)


def test_golden_dataset_rejects_inconsistent_unanswerable_case() -> None:
    manifest = load_manifest(MANIFEST_PATH)
    questions = load_golden_dataset(GOLDEN_PATH)
    unanswerable = next(question for question in questions if not question["answerable"])
    unanswerable["expected_sources"] = ["access_control"]

    with pytest.raises(
        DatasetValidationError, match="unanswerable but has expected_sources"
    ):
        validate_golden_dataset(questions, manifest, EVALUATION_DIR)


def test_answerable_question_requires_evidence_for_each_expected_source() -> None:
    manifest = load_manifest(MANIFEST_PATH)
    questions = load_golden_dataset(GOLDEN_PATH)
    multi_source = next(
        question for question in questions if len(question["expected_sources"]) == 2
    )
    missing_source = multi_source["expected_sources"][1]
    multi_source["evidence"] = [
        evidence
        for evidence in multi_source["evidence"]
        if evidence["source"] != missing_source
    ]

    with pytest.raises(DatasetValidationError, match="without evidence"):
        validate_golden_dataset(questions, manifest, EVALUATION_DIR)


def test_default_question_count_bounds_are_enforced() -> None:
    manifest = load_manifest(MANIFEST_PATH)
    questions = load_golden_dataset(GOLDEN_PATH)

    with pytest.raises(DatasetValidationError, match="25-50 questions"):
        validate_golden_dataset(questions[:24], manifest, EVALUATION_DIR)


def test_loaders_return_independent_mutable_values() -> None:
    first_manifest = load_manifest(MANIFEST_PATH)
    first_questions = load_golden_dataset(GOLDEN_PATH)
    changed_manifest = deepcopy(first_manifest)
    changed_questions = deepcopy(first_questions)
    changed_manifest["documents"][0]["id"] = "changed"
    changed_questions[0]["id"] = "changed"

    assert load_manifest(MANIFEST_PATH)["documents"][0]["id"] != "changed"
    assert load_golden_dataset(GOLDEN_PATH)[0]["id"] != "changed"
