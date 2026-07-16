from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = (
    ROOT
    / "artifacts"
    / "evaluation"
    / "meridian-v1-20260716T175543Z-c3a8dabf"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_reference_run_is_complete_and_has_expected_shape() -> None:
    manifest = json.loads((RUN / "run_manifest.json").read_text(encoding="utf-8"))
    summary = json.loads((RUN / "summary.json").read_text(encoding="utf-8"))
    rows = [
        json.loads(line)
        for line in (RUN / "per_question.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert manifest["status"] == "completed"
    assert summary["dataset"] == {
        "corpus_name": "Meridian Research Cooperative Operations Handbook",
        "documents": 8,
        "questions": 30,
        "answerable_questions": 25,
        "unanswerable_questions": 5,
    }
    assert len(rows) == 60
    assert {row["experiment_id"] for row in rows} == {
        "baseline_900_150",
        "focused_500_80",
    }
    assert all(
        sum(row["experiment_id"] == experiment for row in rows) == 30
        for experiment in ("baseline_900_150", "focused_500_80")
    )
    assert manifest["summary_sha256"] == _sha256(RUN / "summary.json")
    assert manifest["per_question_sha256"] == _sha256(RUN / "per_question.jsonl")


def test_reference_artifact_checksums() -> None:
    lines = (RUN / "artifact-checksums.sha256").read_text(encoding="utf-8").splitlines()
    assert lines
    for line in lines:
        expected, relative = line.split("  ", 1)
        assert _sha256(RUN / Path(relative)) == expected
