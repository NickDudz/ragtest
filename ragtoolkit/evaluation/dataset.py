"""Golden-dataset and corpus-manifest loading and validation.

The evaluation data is deliberately represented by ordinary dictionaries so
the files remain easy to inspect and consume outside this package.  Validation
is strict at the repository boundary: unknown fields, missing corpus files,
hash drift, and evidence anchors that no longer occur verbatim all fail before
an evaluation run starts.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml


MANIFEST_FIELDS = {
    "schema_version",
    "corpus_name",
    "description",
    "license",
    "documents",
}
DOCUMENT_FIELDS = {"id", "path", "title", "provenance", "license", "sha256"}
QUESTION_FIELDS = {
    "id",
    "question",
    "answerable",
    "expected_sources",
    "evidence",
    "required_facts",
    "tags",
}
EVIDENCE_FIELDS = {"source", "text"}
FACT_FIELDS = {"id", "any_of"}

MIN_GOLDEN_QUESTIONS = 25
MAX_GOLDEN_QUESTIONS = 50

_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class DatasetValidationError(ValueError):
    """Raised when a manifest or golden dataset violates its schema.

    ``issues`` contains every validation problem found in the current pass,
    making authoring errors fixable without repeatedly rerunning validation.
    """

    def __init__(self, issues: Sequence[str]):
        self.issues = tuple(str(issue) for issue in issues)
        summary = f"dataset validation failed with {len(self.issues)} issue(s)"
        details = "\n".join(f"- {issue}" for issue in self.issues)
        super().__init__(f"{summary}\n{details}" if details else summary)


def sha256_file(path: str | Path) -> str:
    """Return the lowercase SHA-256 digest of *path* without loading it whole."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(path: str | Path) -> dict[str, Any]:
    """Load a JSON or YAML corpus manifest.

    Known file extensions select their parser.  For an extensionless or custom
    path, content beginning with ``{`` is parsed as JSON and other content as
    YAML.  PyYAML is a pinned project dependency.
    """

    manifest_path = Path(path)
    try:
        content = manifest_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise DatasetValidationError(
            [f"could not load manifest {manifest_path}: {exc}"]
        ) from exc
    suffix = manifest_path.suffix.lower()
    try:
        if suffix == ".json" or (suffix not in {".yaml", ".yml"} and content.lstrip().startswith("{")):
            value = json.loads(content)
        else:
            value = yaml.safe_load(content)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise DatasetValidationError(
            [f"could not parse manifest {manifest_path}: {exc}"]
        ) from exc
    if not isinstance(value, dict):
        raise DatasetValidationError(["manifest root must be an object"])
    return value


def load_golden_dataset(path: str | Path) -> list[dict[str, Any]]:
    """Load golden questions from JSONL (or a JSON array for interoperability).

    Empty JSONL lines are ignored.  Each non-empty line must contain exactly one
    JSON object; validation of object fields is performed separately.
    """

    dataset_path = Path(path)
    if dataset_path.suffix.lower() == ".json":
        try:
            with dataset_path.open("r", encoding="utf-8") as handle:
                value = json.load(handle)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise DatasetValidationError(
                [f"could not load golden dataset {dataset_path}: {exc}"]
            ) from exc
        if not isinstance(value, list):
            raise DatasetValidationError(
                ["golden JSON root must be an array of question objects"]
            )
        records: list[dict[str, Any]] = []
        issues: list[str] = []
        for index, record in enumerate(value, start=1):
            if isinstance(record, dict):
                records.append(record)
            else:
                issues.append(f"golden record {index} must be an object")
        if issues:
            raise DatasetValidationError(issues)
        return records

    records = []
    issues = []
    try:
        with dataset_path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                if not raw_line.strip():
                    continue
                try:
                    record = json.loads(raw_line)
                except json.JSONDecodeError as exc:
                    issues.append(
                        f"golden JSONL line {line_number} is invalid JSON: {exc.msg}"
                    )
                    continue
                if not isinstance(record, dict):
                    issues.append(
                        f"golden JSONL line {line_number} must contain an object"
                    )
                    continue
                records.append(record)
    except (OSError, UnicodeError) as exc:
        raise DatasetValidationError(
            [f"could not load golden dataset {dataset_path}: {exc}"]
        ) from exc
    if issues:
        raise DatasetValidationError(issues)
    return records


def validate_manifest(
    manifest: Mapping[str, Any],
    base_dir: str | Path,
) -> dict[str, Path]:
    """Validate *manifest* and return resolved document paths keyed by ID.

    Document paths must be relative to ``base_dir`` and must not escape it,
    including through a symlink.  Every file's current SHA-256 digest must match
    the checked-in manifest value.
    """

    issues: list[str] = []
    document_paths = _validate_manifest(manifest, Path(base_dir), issues)
    if issues:
        raise DatasetValidationError(issues)
    return document_paths


def validate_golden_dataset(
    questions: Sequence[Mapping[str, Any]],
    manifest: Mapping[str, Any],
    corpus_dir: str | Path,
    *,
    min_questions: int = MIN_GOLDEN_QUESTIONS,
    max_questions: int = MAX_GOLDEN_QUESTIONS,
) -> None:
    """Strictly validate golden questions against a validated corpus manifest.

    Evidence text is checked as an exact, case-sensitive substring of the
    source document.  Answerable questions must name sources, evidence, and
    required facts.  Unanswerable questions must leave all three lists empty.
    The default size limit enforces the V1 brief; callers may narrow it in unit
    tests, but cannot configure an invalid negative or inverted interval.
    """

    if isinstance(questions, (str, bytes)) or not isinstance(questions, Sequence):
        raise DatasetValidationError(["golden dataset root must be a sequence"])
    if min_questions < 0 or max_questions < min_questions:
        raise ValueError("question bounds must satisfy 0 <= min_questions <= max_questions")

    issues: list[str] = []
    document_paths = _validate_manifest(manifest, Path(corpus_dir), issues)
    if issues:
        raise DatasetValidationError(issues)

    count = len(questions)
    if not min_questions <= count <= max_questions:
        issues.append(
            f"golden dataset must contain {min_questions}-{max_questions} questions; "
            f"found {count}"
        )

    manifest_documents = manifest.get("documents", [])
    source_ids = {
        document.get("id")
        for document in manifest_documents
        if isinstance(document, Mapping) and isinstance(document.get("id"), str)
    }
    document_text: dict[str, str] = {}
    for source_id, path in document_paths.items():
        try:
            document_text[source_id] = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            issues.append(f"source {source_id!r} is not valid UTF-8 text: {exc}")

    seen_question_ids: set[str] = set()
    for index, question in enumerate(questions, start=1):
        label = f"question {index}"
        if not isinstance(question, Mapping):
            issues.append(f"{label} must be an object")
            continue
        _check_exact_fields(question, QUESTION_FIELDS, label, issues)

        question_id = _nonempty_string(question.get("id"), f"{label}.id", issues)
        if question_id:
            label = f"question {question_id!r}"
            if not _ID_RE.fullmatch(question_id):
                issues.append(
                    f"{label}.id must contain only letters, numbers, '.', '_', or '-'"
                )
            if question_id in seen_question_ids:
                issues.append(f"duplicate question id {question_id!r}")
            seen_question_ids.add(question_id)

        _nonempty_string(question.get("question"), f"{label}.question", issues)
        answerable = question.get("answerable")
        if not isinstance(answerable, bool):
            issues.append(f"{label}.answerable must be a boolean")

        expected_sources = _string_list(
            question.get("expected_sources"),
            f"{label}.expected_sources",
            issues,
        )
        _report_duplicates(expected_sources, f"{label}.expected_sources", issues)
        for source in expected_sources:
            if source not in source_ids:
                issues.append(
                    f"{label}.expected_sources references unknown source {source!r}"
                )

        evidence = question.get("evidence")
        evidence_items: list[Mapping[str, Any]] = []
        if not isinstance(evidence, list):
            issues.append(f"{label}.evidence must be a list")
        else:
            evidence_items = [item for item in evidence if isinstance(item, Mapping)]
            if len(evidence_items) != len(evidence):
                issues.append(f"{label}.evidence entries must be objects")

        evidence_sources: set[str] = set()
        seen_evidence: set[tuple[str, str]] = set()
        for evidence_index, item in enumerate(evidence_items, start=1):
            evidence_label = f"{label}.evidence[{evidence_index}]"
            _check_exact_fields(item, EVIDENCE_FIELDS, evidence_label, issues)
            source = _nonempty_string(item.get("source"), f"{evidence_label}.source", issues)
            text = _nonempty_string(item.get("text"), f"{evidence_label}.text", issues)
            if source:
                evidence_sources.add(source)
                if source not in source_ids:
                    issues.append(f"{evidence_label} references unknown source {source!r}")
                elif source not in expected_sources:
                    issues.append(
                        f"{evidence_label}.source {source!r} is not in expected_sources"
                    )
            if source and text:
                pair = (source, text)
                if pair in seen_evidence:
                    issues.append(f"{evidence_label} duplicates an earlier evidence anchor")
                seen_evidence.add(pair)
                source_text = document_text.get(source)
                if source_text is not None and text not in source_text:
                    issues.append(
                        f"{evidence_label}.text is not an exact substring of source {source!r}"
                    )

        facts = question.get("required_facts")
        fact_items: list[Mapping[str, Any]] = []
        if not isinstance(facts, list):
            issues.append(f"{label}.required_facts must be a list")
        else:
            fact_items = [item for item in facts if isinstance(item, Mapping)]
            if len(fact_items) != len(facts):
                issues.append(f"{label}.required_facts entries must be objects")

        seen_fact_ids: set[str] = set()
        for fact_index, fact in enumerate(fact_items, start=1):
            fact_label = f"{label}.required_facts[{fact_index}]"
            _check_exact_fields(fact, FACT_FIELDS, fact_label, issues)
            fact_id = _nonempty_string(fact.get("id"), f"{fact_label}.id", issues)
            if fact_id:
                if not _ID_RE.fullmatch(fact_id):
                    issues.append(f"{fact_label}.id has an invalid identifier format")
                if fact_id in seen_fact_ids:
                    issues.append(f"{fact_label}.id duplicates {fact_id!r}")
                seen_fact_ids.add(fact_id)
            alternatives = _string_list(fact.get("any_of"), f"{fact_label}.any_of", issues)
            if not alternatives:
                issues.append(f"{fact_label}.any_of must contain at least one string")
            _report_duplicates(alternatives, f"{fact_label}.any_of", issues)

        tags = _string_list(question.get("tags"), f"{label}.tags", issues)
        if not tags:
            issues.append(f"{label}.tags must contain at least one tag")
        _report_duplicates(tags, f"{label}.tags", issues)

        if answerable is True:
            if not expected_sources:
                issues.append(f"{label} is answerable but has no expected_sources")
            if not evidence_items:
                issues.append(f"{label} is answerable but has no evidence")
            if not fact_items:
                issues.append(f"{label} is answerable but has no required_facts")
            missing_evidence_sources = set(expected_sources) - evidence_sources
            if missing_evidence_sources:
                issues.append(
                    f"{label} has expected source(s) without evidence: "
                    + ", ".join(sorted(missing_evidence_sources))
                )
        elif answerable is False:
            if expected_sources:
                issues.append(f"{label} is unanswerable but has expected_sources")
            if evidence_items:
                issues.append(f"{label} is unanswerable but has evidence")
            if fact_items:
                issues.append(f"{label} is unanswerable but has required_facts")

    if issues:
        raise DatasetValidationError(issues)


def validate_dataset(
    manifest_path: str | Path,
    golden_path: str | Path,
    *,
    corpus_dir: str | Path | None = None,
    min_questions: int = MIN_GOLDEN_QUESTIONS,
    max_questions: int = MAX_GOLDEN_QUESTIONS,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Load and validate a complete evaluation dataset.

    Relative document paths are resolved from the manifest's directory unless
    an explicit ``corpus_dir`` is supplied.  The loaded values are returned
    unchanged after successful validation.
    """

    manifest_file = Path(manifest_path)
    manifest = load_manifest(manifest_file)
    questions = load_golden_dataset(golden_path)
    base_dir = Path(corpus_dir) if corpus_dir is not None else manifest_file.parent
    validate_golden_dataset(
        questions,
        manifest,
        base_dir,
        min_questions=min_questions,
        max_questions=max_questions,
    )
    return manifest, questions


def _validate_manifest(
    manifest: Mapping[str, Any],
    base_dir: Path,
    issues: list[str],
) -> dict[str, Path]:
    if not isinstance(manifest, Mapping):
        issues.append("manifest root must be an object")
        return {}
    _check_exact_fields(manifest, MANIFEST_FIELDS, "manifest", issues)
    _nonempty_string(manifest.get("schema_version"), "manifest.schema_version", issues)
    _nonempty_string(manifest.get("corpus_name"), "manifest.corpus_name", issues)
    _nonempty_string(manifest.get("description"), "manifest.description", issues)
    _nonempty_string(manifest.get("license"), "manifest.license", issues)

    documents = manifest.get("documents")
    if not isinstance(documents, list):
        issues.append("manifest.documents must be a list")
        return {}
    if not documents:
        issues.append("manifest.documents must contain at least one document")

    try:
        resolved_base = base_dir.resolve(strict=True)
    except OSError as exc:
        issues.append(f"corpus base directory does not exist: {base_dir} ({exc})")
        return {}
    if not resolved_base.is_dir():
        issues.append(f"corpus base path is not a directory: {resolved_base}")
        return {}

    document_paths: dict[str, Path] = {}
    seen_document_ids: set[str] = set()
    seen_paths: set[str] = set()
    for index, document in enumerate(documents, start=1):
        label = f"manifest.documents[{index}]"
        if not isinstance(document, Mapping):
            issues.append(f"{label} must be an object")
            continue
        _check_exact_fields(document, DOCUMENT_FIELDS, label, issues)
        document_id = _nonempty_string(document.get("id"), f"{label}.id", issues)
        if document_id:
            label = f"manifest document {document_id!r}"
            if not _ID_RE.fullmatch(document_id):
                issues.append(f"{label}.id has an invalid identifier format")
            if document_id in seen_document_ids:
                issues.append(f"duplicate manifest document id {document_id!r}")
            seen_document_ids.add(document_id)

        relative_path = _nonempty_string(document.get("path"), f"{label}.path", issues)
        _nonempty_string(document.get("title"), f"{label}.title", issues)
        _nonempty_string(document.get("provenance"), f"{label}.provenance", issues)
        _nonempty_string(document.get("license"), f"{label}.license", issues)
        expected_digest = _nonempty_string(document.get("sha256"), f"{label}.sha256", issues)
        if expected_digest and not _SHA256_RE.fullmatch(expected_digest):
            issues.append(f"{label}.sha256 must be exactly 64 hexadecimal characters")

        if not document_id or not relative_path:
            continue
        path_value = Path(relative_path)
        if path_value.is_absolute():
            issues.append(f"{label}.path must be relative to the corpus directory")
            continue
        try:
            resolved_path = (resolved_base / path_value).resolve(strict=True)
        except OSError as exc:
            issues.append(f"{label}.path does not exist: {relative_path!r} ({exc})")
            continue
        try:
            resolved_path.relative_to(resolved_base)
        except ValueError:
            issues.append(f"{label}.path escapes the corpus directory: {relative_path!r}")
            continue
        if not resolved_path.is_file():
            issues.append(f"{label}.path is not a file: {relative_path!r}")
            continue

        normalized_path = resolved_path.as_posix().casefold()
        if normalized_path in seen_paths:
            issues.append(f"duplicate manifest document path {relative_path!r}")
        seen_paths.add(normalized_path)
        if document_id not in document_paths:
            document_paths[document_id] = resolved_path

        if expected_digest and _SHA256_RE.fullmatch(expected_digest):
            try:
                actual_digest = sha256_file(resolved_path)
            except OSError as exc:
                issues.append(f"could not hash {label}.path: {exc}")
            else:
                if actual_digest != expected_digest.lower():
                    issues.append(
                        f"{label}.sha256 mismatch: expected {expected_digest.lower()}, "
                        f"found {actual_digest}"
                    )
    return document_paths


def _check_exact_fields(
    value: Mapping[str, Any],
    expected: set[str],
    label: str,
    issues: list[str],
) -> None:
    keys = set(value)
    missing = sorted(expected - keys)
    unknown = sorted(keys - expected)
    if missing:
        issues.append(f"{label} is missing field(s): {', '.join(missing)}")
    if unknown:
        issues.append(f"{label} has unknown field(s): {', '.join(unknown)}")


def _nonempty_string(value: Any, label: str, issues: list[str]) -> str:
    if not isinstance(value, str) or not value.strip():
        issues.append(f"{label} must be a non-empty string")
        return ""
    if value != value.strip():
        issues.append(f"{label} must not have leading or trailing whitespace")
    return value


def _string_list(value: Any, label: str, issues: list[str]) -> list[str]:
    if not isinstance(value, list):
        issues.append(f"{label} must be a list of strings")
        return []
    output: list[str] = []
    for index, item in enumerate(value, start=1):
        parsed = _nonempty_string(item, f"{label}[{index}]", issues)
        if parsed:
            output.append(parsed)
    return output


def _report_duplicates(values: Sequence[str], label: str, issues: list[str]) -> None:
    seen: set[str] = set()
    reported: set[str] = set()
    for value in values:
        if value in seen and value not in reported:
            issues.append(f"{label} contains duplicate value {value!r}")
            reported.add(value)
        seen.add(value)


__all__ = [
    "DatasetValidationError",
    "DOCUMENT_FIELDS",
    "EVIDENCE_FIELDS",
    "FACT_FIELDS",
    "MANIFEST_FIELDS",
    "MAX_GOLDEN_QUESTIONS",
    "MIN_GOLDEN_QUESTIONS",
    "QUESTION_FIELDS",
    "load_golden_dataset",
    "load_manifest",
    "sha256_file",
    "validate_dataset",
    "validate_golden_dataset",
    "validate_manifest",
]
