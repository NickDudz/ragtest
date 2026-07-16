"""End-to-end, local-first evaluation runner for the Local RAG Toolkit."""

from __future__ import annotations

import ctypes
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import requests
import yaml

from ..chunkers import chunk_text
from ..embeddings import OllamaEmbedder
from ..llm import OllamaLLM
from ..prompts import compose_prompt, render_context
from .citations import citation_metrics
from .dataset import sha256_file, validate_dataset
from .metrics import (
    abstention_correct,
    latency_percentiles,
    required_fact_coverage,
    required_fact_matches,
    retrieval_metrics,
)
from .report import (
    generate_charts,
    write_results_report,
    write_summary_csv,
    write_summary_json,
)


DIRECT_PACKAGES = (
    "chromadb",
    "pypdf",
    "markdown-it-py",
    "typer",
    "pydantic",
    "requests",
    "rich",
    "tqdm",
    "numpy",
    "fastapi",
    "uvicorn",
    "jinja2",
    "PyYAML",
    "pytest",
    "pandas",
    "matplotlib",
    "posthog",
)


class EvaluationConfigError(ValueError):
    """Raised when the intentionally small V1 experiment schema is invalid."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _jsonl_append(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False) + "\n")


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _resolve_input(repo_root: Path, config_path: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    candidates = (repo_root / path, config_path.parent / path)
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return candidates[0].resolve()


def _resolve_output(repo_root: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (repo_root / path).resolve()


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate.resolve()
    return Path.cwd().resolve()


def load_experiment_config(path: str | Path) -> Dict[str, Any]:
    """Load and validate the deliberately narrow V1 experiment configuration."""
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise EvaluationConfigError("experiment config must be a YAML object")

    required = {
        "version",
        "name",
        "dataset",
        "corpus_manifest",
        "output_dir",
        "seed",
        "runs",
        "models",
        "prompt",
        "retrieval",
        "experiments",
    }
    missing = sorted(required - set(value))
    if missing:
        raise EvaluationConfigError(f"missing experiment fields: {', '.join(missing)}")
    if value["version"] != 1:
        raise EvaluationConfigError("only experiment schema version 1 is supported")
    if not isinstance(value["experiments"], list) or len(value["experiments"]) < 2:
        raise EvaluationConfigError("at least two experiments are required")
    ids: set[str] = set()
    for item in value["experiments"]:
        if not isinstance(item, dict) or not {"id", "chunking"}.issubset(item):
            raise EvaluationConfigError("each experiment must contain id and chunking")
        extra_fields = set(item) - {"id", "description", "chunking"}
        if extra_fields:
            raise EvaluationConfigError(
                f"unsupported experiment fields: {', '.join(sorted(extra_fields))}"
            )
        experiment_id = item["id"]
        if not isinstance(experiment_id, str) or not experiment_id:
            raise EvaluationConfigError("experiment id must be a non-empty string")
        if experiment_id in ids:
            raise EvaluationConfigError(f"duplicate experiment id: {experiment_id}")
        ids.add(experiment_id)
        chunking = item["chunking"]
        if not isinstance(chunking, dict):
            raise EvaluationConfigError(f"{experiment_id}: chunking must be an object")
        size = int(chunking.get("size", 0))
        overlap = int(chunking.get("overlap", -1))
        if size <= 0 or overlap < 0 or overlap >= size:
            raise EvaluationConfigError(
                f"{experiment_id}: require size > 0 and 0 <= overlap < size"
            )

    retrieval = value["retrieval"]
    if retrieval.get("rerank") is not False:
        raise EvaluationConfigError("V1 requires rerank: false")
    if retrieval.get("min_score") is not None:
        raise EvaluationConfigError("V1 requires min_score: null because score filtering is not implemented")
    if int(retrieval.get("top_k", 0)) < 5:
        raise EvaluationConfigError("top_k must be at least 5 to report Recall@5")
    for model_key in ("embedding", "generation"):
        section = value["models"].get(model_key, {})
        if section.get("provider") != "ollama" or not section.get("model"):
            raise EvaluationConfigError(f"models.{model_key} must specify an Ollama model")
    if not value["prompt"].get("system") or not value["prompt"].get("template"):
        raise EvaluationConfigError("prompt.system and prompt.template are required")
    return value


def _run_command(args: Sequence[str], cwd: Path) -> str | None:
    try:
        result = subprocess.run(
            list(args), cwd=cwd, text=True, capture_output=True, check=False, timeout=15
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _git_snapshot(repo_root: Path) -> Dict[str, Any]:
    commit = _run_command(("git", "rev-parse", "HEAD"), repo_root)
    status = _run_command(("git", "status", "--porcelain", "-uall"), repo_root)
    diff = _run_command(("git", "diff", "HEAD", "--binary"), repo_root) or ""
    untracked_hashes: Dict[str, str] = {}
    for line in status.splitlines() if status else ():
        if not line.startswith("?? "):
            continue
        relative = line[3:].strip('"')
        candidate = repo_root / relative
        if candidate.is_file():
            untracked_hashes[Path(relative).as_posix()] = sha256_file(candidate)
    state_material = json.dumps(
        {
            "commit": commit,
            "tracked_diff_sha256": _hash_text(diff),
            "untracked_files": untracked_hashes,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "commit": commit,
        "dirty": bool(status),
        "status": status.splitlines() if status else [],
        "tracked_diff_sha256": _hash_text(diff),
        "untracked_files": untracked_hashes,
        "workspace_state_sha256": _hash_text(state_material),
    }


def _memory_bytes() -> int | None:
    if os.name != "nt":
        return None

    class MemoryStatus(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = MemoryStatus()
    status.dwLength = ctypes.sizeof(status)
    try:
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.ullTotalPhys)
    except (AttributeError, OSError):
        return None
    return None


def _hardware_snapshot(repo_root: Path) -> Dict[str, Any]:
    gpu_rows: List[Dict[str, str]] = []
    output = _run_command(
        (
            "nvidia-smi",
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader,nounits",
        ),
        repo_root,
    )
    if output:
        for line in output.splitlines():
            parts = [part.strip() for part in line.split(",")]
            if len(parts) == 3:
                gpu_rows.append(
                    {"name": parts[0], "memory_mib": parts[1], "driver": parts[2]}
                )
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER"),
        "logical_cpu_count": os.cpu_count(),
        "total_memory_bytes": _memory_bytes(),
        "gpus": gpu_rows,
    }


def _package_snapshot() -> Dict[str, str | None]:
    versions: Dict[str, str | None] = {}
    for package in DIRECT_PACKAGES:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return versions


def _ollama_snapshot(base_url: str, model_names: Sequence[str]) -> Dict[str, Any]:
    version_response = requests.get(f"{base_url.rstrip('/')}/api/version", timeout=15)
    version_response.raise_for_status()
    tags_response = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=30)
    tags_response.raise_for_status()
    tags = tags_response.json().get("models", [])
    by_name: Dict[str, Dict[str, Any]] = {}
    for item in tags:
        if isinstance(item, dict):
            name = item.get("name") or item.get("model")
            if isinstance(name, str):
                by_name[name] = item
    missing = [name for name in model_names if name not in by_name]
    if missing:
        raise RuntimeError(f"Ollama models are not installed: {', '.join(missing)}")
    return {
        "version": version_response.json().get("version"),
        "base_url": base_url,
        "models": {
            name: {
                "digest": by_name[name].get("digest"),
                "size": by_name[name].get("size"),
                "modified_at": by_name[name].get("modified_at"),
                "details": by_name[name].get("details"),
            }
            for name in model_names
        },
    }


def _corpus_hash(manifest: Mapping[str, Any]) -> str:
    material = "\n".join(
        f"{item['id']}:{item['sha256']}" for item in sorted(manifest["documents"], key=lambda d: d["id"])
    )
    return _hash_text(material)


def _create_index(
    *,
    manifest: Mapping[str, Any],
    manifest_path: Path,
    cache_path: Path,
    chunking: Mapping[str, Any],
    embedder: OllamaEmbedder,
    batch_size: int,
) -> Tuple[Any, Dict[str, Any]]:
    import chromadb
    from chromadb.config import Settings

    started = time.perf_counter()
    cache_path.mkdir(parents=True, exist_ok=False)
    client = chromadb.PersistentClient(
        path=str(cache_path), settings=Settings(anonymized_telemetry=False)
    )
    collection = client.create_collection("rag", metadata={"hnsw:space": "cosine"})
    prepared: List[Dict[str, Any]] = []
    for document in sorted(manifest["documents"], key=lambda item: item["id"]):
        relative_path = Path(document["path"])
        absolute_path = (manifest_path.parent / relative_path).resolve()
        text = absolute_path.read_text(encoding="utf-8")
        chunks = chunk_text(
            text,
            str(chunking.get("profile", "paper")),
            int(chunking["size"]),
            int(chunking["overlap"]),
        )
        for chunk in chunks:
            start, end = chunk["span"]
            prepared.append(
                {
                    "id": f"{document['id']}@{start}-{end}",
                    "text": chunk["content"],
                    "metadata": {
                        "source_id": document["id"],
                        "source": document["id"],
                        "path": relative_path.as_posix(),
                        "title": document["title"],
                        "span_start": int(start),
                        "span_end": int(end),
                    },
                }
            )
    if not prepared:
        raise RuntimeError("evaluation corpus produced no chunks")

    embed_seconds = 0.0
    upsert_seconds = 0.0
    for offset in range(0, len(prepared), batch_size):
        batch = prepared[offset : offset + batch_size]
        embed_start = time.perf_counter()
        vectors = embedder.embed([item["text"] for item in batch])
        embed_seconds += time.perf_counter() - embed_start
        upsert_start = time.perf_counter()
        collection.upsert(
            ids=[item["id"] for item in batch],
            documents=[item["text"] for item in batch],
            metadatas=[item["metadata"] for item in batch],
            embeddings=vectors,
        )
        upsert_seconds += time.perf_counter() - upsert_start
    total_seconds = time.perf_counter() - started
    stats = {
        "documents": len(manifest["documents"]),
        "chunks": len(prepared),
        "embedding_seconds": embed_seconds,
        "upsert_seconds": upsert_seconds,
        "ingest_seconds": total_seconds,
        "distance_metric": "cosine",
        "cache_path": str(cache_path),
    }
    # Retain the client alongside the collection; older Chroma clients may be
    # finalized if the owning object is collected during a run.
    return (client, collection), stats


def _hits_from_query(result: Mapping[str, Any]) -> List[Dict[str, Any]]:
    ids = (result.get("ids") or [[]])[0]
    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]
    hits: List[Dict[str, Any]] = []
    for index, chunk_id in enumerate(ids):
        hits.append(
            {
                "id": chunk_id,
                "text": documents[index],
                "meta": metadatas[index] or {},
                "distance": float(distances[index]) if distances[index] is not None else None,
                "score": None,
            }
        )
    return hits


def _execute_question(
    *,
    collection: Any,
    embedder: OllamaEmbedder,
    llm: OllamaLLM,
    question: str,
    top_k: int,
    system_prompt: str,
    prompt_template: str,
) -> Tuple[str, List[Dict[str, Any]], Dict[str, float], Dict[str, Any]]:
    end_to_end_start = time.perf_counter()
    embedding_start = time.perf_counter()
    query_vector = embedder.embed([question])
    query_embedding_ms = (time.perf_counter() - embedding_start) * 1000.0

    search_start = time.perf_counter()
    result = collection.query(
        query_embeddings=query_vector,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    vector_search_ms = (time.perf_counter() - search_start) * 1000.0
    hits = _hits_from_query(result)
    context = render_context(hits)
    rendered = compose_prompt(system_prompt, prompt_template, question, context)

    generation_start = time.perf_counter()
    answer, model_metadata = llm.generate_with_metadata(rendered["system"], rendered["user"])
    generation_ms = (time.perf_counter() - generation_start) * 1000.0
    end_to_end_ms = (time.perf_counter() - end_to_end_start) * 1000.0
    timing = {
        "query_embedding_ms": query_embedding_ms,
        "vector_search_ms": vector_search_ms,
        "retrieval_ms": query_embedding_ms + vector_search_ms,
        "generation_ms": generation_ms,
        "end_to_end_ms": end_to_end_ms,
    }
    return answer, hits, timing, model_metadata


def _mean(rows: Iterable[Mapping[str, Any]], accessor: Any) -> float:
    values = [float(accessor(row)) for row in rows]
    return fmean(values) if values else 0.0


def _latency_summary(rows: Sequence[Mapping[str, Any]], key: str) -> Dict[str, float | int]:
    raw = latency_percentiles([float(row["timing_ms"][key]) for row in rows])
    return {
        "count": int(raw["count"]),
        "mean": float(raw["mean_ms"]),
        "min": float(raw["min_ms"]),
        "p50": float(raw["p50_ms"]),
        "p95": float(raw["p95_ms"]),
        "max": float(raw["max_ms"]),
    }


def _aggregate_experiment(
    experiment: Mapping[str, Any], index_stats: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]
) -> Dict[str, Any]:
    answerable = [row for row in rows if row["answerable"]]
    unanswerable = [row for row in rows if not row["answerable"]]
    total_citations = sum(row["citation_metrics"]["citation_count"] for row in answerable)
    total_valid_citations = sum(
        row["citation_metrics"]["valid_citation_count"] for row in answerable
    )
    metrics = {
        "recall_at_1": _mean(answerable, lambda row: row["retrieval_metrics"]["recall_at_1"]),
        "recall_at_3": _mean(answerable, lambda row: row["retrieval_metrics"]["recall_at_3"]),
        "recall_at_5": _mean(answerable, lambda row: row["retrieval_metrics"]["recall_at_5"]),
        "evidence_recall_at_1": _mean(
            answerable, lambda row: row["retrieval_metrics"]["evidence_recall_at_1"]
        ),
        "evidence_recall_at_3": _mean(
            answerable, lambda row: row["retrieval_metrics"]["evidence_recall_at_3"]
        ),
        "evidence_recall_at_5": _mean(
            answerable, lambda row: row["retrieval_metrics"]["evidence_recall_at_5"]
        ),
        "mrr": _mean(answerable, lambda row: row["retrieval_metrics"]["mrr"]),
        "citation_valid_id_rate": (
            total_valid_citations / total_citations if total_citations else 0.0
        ),
        "citation_presence_rate": _mean(
            answerable, lambda row: row["citation_metrics"]["citation_count"] > 0
        ),
        "citation_source_precision": _mean(
            answerable,
            lambda row: row["citation_metrics"]["expected_source_precision"],
        ),
        "citation_source_recall": _mean(
            answerable,
            lambda row: row["citation_metrics"]["expected_source_recall"],
        ),
        "required_fact_coverage": _mean(
            answerable, lambda row: row["answer_quality"]["required_fact_coverage"]
        ),
        "abstention_accuracy": _mean(
            unanswerable, lambda row: row["answer_quality"]["abstention_correct"]
        ),
    }
    return {
        "id": experiment["id"],
        "chunking": dict(experiment["chunking"]),
        "index": dict(index_stats),
        "metrics": metrics,
        "latency_ms": {
            "query_embedding": _latency_summary(rows, "query_embedding_ms"),
            "vector_search": _latency_summary(rows, "vector_search_ms"),
            "retrieval": _latency_summary(rows, "retrieval_ms"),
            "generation": _latency_summary(rows, "generation_ms"),
            "end_to_end": _latency_summary(rows, "end_to_end_ms"),
        },
        "questions": len(rows),
        "answerable_questions": len(answerable),
        "unanswerable_questions": len(unanswerable),
    }


def run_evaluation(config_path: str | Path) -> Path:
    """Run validation, indexing, retrieval, generation, metrics, and reporting.

    Returns the newly created artifact directory. No accuracy or latency claim
    is emitted until every configured experiment has completed successfully.
    """

    config_file = Path(config_path).resolve()
    repo_root = _find_repo_root(config_file.parent)
    config = load_experiment_config(config_file)
    dataset_path = _resolve_input(repo_root, config_file, str(config["dataset"]))
    manifest_path = _resolve_input(repo_root, config_file, str(config["corpus_manifest"]))
    corpus_manifest, questions = validate_dataset(manifest_path, dataset_path)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{config['name']}-{timestamp}-{uuid.uuid4().hex[:8]}"
    output_root = _resolve_output(repo_root, str(config["output_dir"]))
    artifact_dir = output_root / run_id
    cache_root = repo_root / ".eval_cache" / run_id
    per_question_path = artifact_dir / "per_question.jsonl"

    embedding_config = config["models"]["embedding"]
    generation_config = config["models"]["generation"]
    embedding_url = str(embedding_config.get("base_url", "http://localhost:11434")).rstrip("/")
    generation_url = str(generation_config.get("base_url", "http://localhost:11434")).rstrip("/")
    if embedding_url != generation_url:
        raise EvaluationConfigError("V1 requires one shared local Ollama base URL")

    git_snapshot = _git_snapshot(repo_root)
    hardware_snapshot = _hardware_snapshot(repo_root)
    package_snapshot = _package_snapshot()
    ollama_snapshot = _ollama_snapshot(
        embedding_url,
        [str(embedding_config["model"]), str(generation_config["model"])],
    )
    try:
        config_display = config_file.relative_to(repo_root).as_posix()
    except ValueError:
        config_display = str(config_file)
    quoted_config = f'"{config_display}"' if " " in config_display else config_display

    artifact_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(config_file, artifact_dir / "experiments.yaml")

    run_manifest: Dict[str, Any] = {
        "schema_version": 1,
        "run_id": run_id,
        "status": "running",
        "started_at": _utc_now(),
        "finished_at": None,
        "reproduction_command": f"python rag.py eval --config {quoted_config}",
        "git": git_snapshot,
        "python": {
            "version": sys.version,
            "executable": sys.executable,
            "packages": package_snapshot,
        },
        "hardware": hardware_snapshot,
        "ollama": ollama_snapshot,
        "inputs": {
            "config_path": str(config_file),
            "config_sha256": sha256_file(config_file),
            "golden_path": str(dataset_path),
            "golden_sha256": sha256_file(dataset_path),
            "manifest_path": str(manifest_path),
            "manifest_sha256": sha256_file(manifest_path),
            "corpus_sha256": _corpus_hash(corpus_manifest),
            "prompt_sha256": _hash_text(
                config["prompt"]["system"] + "\n" + config["prompt"]["template"]
            ),
        },
        "configuration": config,
    }
    _json_write(artifact_dir / "run_manifest.json", run_manifest)

    embedder = OllamaEmbedder(str(embedding_config["model"]), base_url=embedding_url)
    llm = OllamaLLM(
        str(generation_config["model"]),
        temperature=float(generation_config.get("temperature", 0.0)),
        max_tokens=int(generation_config.get("max_tokens", 512)),
        base_url=generation_url,
        seed=int(config["seed"]),
        context_window=(
            int(generation_config["context_window"])
            if generation_config.get("context_window") is not None
            else None
        ),
    )
    top_k = int(config["retrieval"]["top_k"])
    batch_size = int(embedding_config.get("batch_size", 32))
    warmup_queries = int(config["runs"].get("warmup_queries", 1))
    measured_repetitions = int(config["runs"].get("measured_repetitions", 1))
    if measured_repetitions != 1:
        raise EvaluationConfigError("V1 currently requires measured_repetitions: 1")

    summaries: List[Dict[str, Any]] = []
    try:
        for experiment in config["experiments"]:
            (_, collection), index_stats = _create_index(
                manifest=corpus_manifest,
                manifest_path=manifest_path,
                cache_path=cache_root / experiment["id"],
                chunking=experiment["chunking"],
                embedder=embedder,
                batch_size=batch_size,
            )
            for warmup_index in range(warmup_queries):
                warmup_question = questions[warmup_index % len(questions)]["question"]
                _execute_question(
                    collection=collection,
                    embedder=embedder,
                    llm=llm,
                    question=warmup_question,
                    top_k=top_k,
                    system_prompt=config["prompt"]["system"],
                    prompt_template=config["prompt"]["template"],
                )

            experiment_rows: List[Dict[str, Any]] = []
            for question in questions:
                answer, hits, timing, model_metadata = _execute_question(
                    collection=collection,
                    embedder=embedder,
                    llm=llm,
                    question=question["question"],
                    top_k=top_k,
                    system_prompt=config["prompt"]["system"],
                    prompt_template=config["prompt"]["template"],
                )
                retrieval = (
                    retrieval_metrics(
                        question["expected_sources"],
                        hits,
                        evidence=question["evidence"],
                        ks=(1, 3, 5),
                    )
                    if question["answerable"]
                    else None
                )
                citations = citation_metrics(answer, hits, question["expected_sources"])
                answer_quality = {
                    "required_fact_matches": required_fact_matches(
                        answer, question["required_facts"]
                    ),
                    "required_fact_coverage": required_fact_coverage(
                        answer, question["required_facts"]
                    ),
                    "abstention_correct": abstention_correct(
                        answer, question["answerable"]
                    ),
                }
                row = {
                    "run_id": run_id,
                    "experiment_id": experiment["id"],
                    "question_id": question["id"],
                    "question": question["question"],
                    "answerable": question["answerable"],
                    "tags": question["tags"],
                    "expected_sources": question["expected_sources"],
                    "expected_evidence": question["evidence"],
                    "required_facts": question["required_facts"],
                    "hits": hits,
                    "answer": answer,
                    "retrieval_metrics": retrieval,
                    "citation_metrics": citations,
                    "answer_quality": answer_quality,
                    "timing_ms": timing,
                    "llm_metadata": model_metadata,
                }
                experiment_rows.append(row)
                _jsonl_append(per_question_path, row)
            summaries.append(_aggregate_experiment(experiment, index_stats, experiment_rows))

        summary = {
            "schema_version": 1,
            "run_id": run_id,
            "dataset": {
                "corpus_name": corpus_manifest["corpus_name"],
                "documents": len(corpus_manifest["documents"]),
                "questions": len(questions),
                "answerable_questions": sum(item["answerable"] for item in questions),
                "unanswerable_questions": sum(not item["answerable"] for item in questions),
            },
            "experiments": summaries,
        }
        write_summary_json(summary, artifact_dir / "summary.json")
        write_summary_csv(summary, artifact_dir / "summary.csv")
        generate_charts(summary, artifact_dir / "charts")
        write_results_report(summary, corpus_manifest, artifact_dir / "report.md")
        run_manifest["status"] = "completed"
        run_manifest["finished_at"] = _utc_now()
        run_manifest["summary_sha256"] = sha256_file(artifact_dir / "summary.json")
        run_manifest["per_question_sha256"] = sha256_file(per_question_path)
        _json_write(artifact_dir / "run_manifest.json", run_manifest)
    except Exception as exc:
        run_manifest["status"] = "failed"
        run_manifest["finished_at"] = _utc_now()
        run_manifest["error"] = f"{type(exc).__name__}: {exc}"
        _json_write(artifact_dir / "run_manifest.json", run_manifest)
        raise
    return artifact_dir


__all__ = ["EvaluationConfigError", "load_experiment_config", "run_evaluation"]
