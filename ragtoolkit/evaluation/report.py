"""Reporting helpers for reproducible RAG evaluation artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def _flatten_experiment(experiment: Dict[str, Any]) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "experiment_id": experiment["id"],
        "chunk_size": experiment["chunking"]["size"],
        "chunk_overlap": experiment["chunking"]["overlap"],
        "documents": experiment["index"]["documents"],
        "chunks": experiment["index"]["chunks"],
        "ingest_seconds": experiment["index"]["ingest_seconds"],
    }
    row.update(experiment["metrics"])
    for stage, values in experiment["latency_ms"].items():
        for percentile, value in values.items():
            column = f"{stage}_count" if percentile == "count" else f"{stage}_{percentile}_ms"
            row[column] = value
    return row


def write_summary_csv(summary: Dict[str, Any], path: Path) -> None:
    """Write one flat, machine-readable row per experiment."""
    rows = [_flatten_experiment(item) for item in summary["experiments"]]
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: List[str] = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary_json(summary: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _metric_table(experiments: Iterable[Dict[str, Any]]) -> List[str]:
    headers = [
        "Configuration",
        "Recall@1",
        "Recall@3",
        "Recall@5",
        "MRR",
        "Citation source recall",
        "Fact coverage",
        "End-to-end p50 (ms)",
    ]
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for item in experiments:
        metrics = item["metrics"]
        latency = item["latency_ms"]["end_to_end"]
        values = [
            item["id"],
            f"{metrics['recall_at_1']:.3f}",
            f"{metrics['recall_at_3']:.3f}",
            f"{metrics['recall_at_5']:.3f}",
            f"{metrics['mrr']:.3f}",
            f"{metrics['citation_source_recall']:.3f}",
            f"{metrics['required_fact_coverage']:.3f}",
            f"{latency['p50']:.1f}",
        ]
        lines.append("| " + " | ".join(values) + " |")
    return lines


def write_results_report(summary: Dict[str, Any], manifest: Dict[str, Any], path: Path) -> None:
    """Write a compact methodology and measured-results report."""
    experiments = summary["experiments"]
    question_count = summary["dataset"]["questions"]
    answerable_count = summary["dataset"]["answerable_questions"]
    document_count = len(manifest["documents"])
    lines = [
        "# RAG Evaluation Results",
        "",
        f"Reference run `{summary['run_id']}` evaluated {question_count} golden questions "
        f"({answerable_count} answerable) over {document_count} version-controlled documents.",
        "",
        "## Summary",
        "",
        *_metric_table(experiments),
        "",
        "![Retrieval quality](charts/retrieval-quality.png)",
        "",
        "![Citation and answer checks](charts/citation-answer-quality.png)",
        "",
        "![Latency](charts/latency.png)",
        "",
        "## Methodology",
        "",
        "Both configurations used the same corpus, questions, embedding model, generation model, "
        "prompt, cosine distance, retrieval depth, temperature, and seed. Only chunk size and "
        "overlap changed. Each configuration was indexed into a fresh run-specific Chroma store.",
        "",
        "Retrieval metrics are calculated only for answerable questions. Citation metrics parse "
        "the generated `[S#]` markers and map them back to ranked retrieved chunks. Required-fact "
        "coverage is deterministic normalized phrase matching and is an answer-quality proxy, not "
        "a semantic correctness judgment. Latencies use wall-clock measurements after an excluded "
        "warm-up query for each configuration.",
        "",
        "## Artifact map",
        "",
        "- `per_question.jsonl`: ranked hits, generated answers, metrics, timings, and model metadata",
        "- `summary.json` and `summary.csv`: aggregate results",
        "- `run_manifest.json`: versions, hashes, models, hardware, and configuration",
        "- `error_analysis.md`: manually reviewed representative failures, added after the run",
        "",
        "## Limitations",
        "",
        "- The corpus is deliberately small and project-authored; results do not generalize to arbitrary domains.",
        "- One measured generation per question limits latency-distribution confidence.",
        "- Exact phrase checks under-credit valid paraphrases and can reward superficial lexical matches.",
        "- Citation-source checks verify attribution targets, not whether every generated claim is entailed.",
        "- The comparison isolates chunk geometry; it does not evaluate reranking or alternate embedding models.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def generate_charts(summary: Dict[str, Any], charts_dir: Path) -> None:
    """Generate compact PNG comparisons from measured summary values."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    charts_dir.mkdir(parents=True, exist_ok=True)
    experiments = summary["experiments"]
    names = [item["id"].replace("_", "\n") for item in experiments]
    colors = ["#0072B2", "#D55E00", "#009E73", "#CC79A7"]

    def grouped_chart(
        filename: str,
        labels: List[str],
        keys: List[str],
        ylabel: str,
        title: str,
    ) -> None:
        x = np.arange(len(labels), dtype=float)
        width = 0.8 / max(1, len(experiments))
        fig, ax = plt.subplots(figsize=(9, 5.2), constrained_layout=True)
        for index, item in enumerate(experiments):
            values = [float(item["metrics"][key]) for key in keys]
            positions = x - 0.4 + width / 2 + index * width
            bars = ax.bar(
                positions,
                values,
                width,
                label=names[index],
                color=colors[index % len(colors)],
            )
            ax.bar_label(bars, labels=[f"{value:.2f}" for value in values], padding=3, fontsize=8)
        ax.set_xticks(x, labels)
        ax.set_ylim(0, 1.12)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(axis="y", alpha=0.2)
        ax.legend(frameon=False, ncols=max(1, len(experiments)))
        fig.savefig(charts_dir / filename, dpi=180)
        plt.close(fig)

    grouped_chart(
        "retrieval-quality.png",
        ["Recall@1", "Recall@3", "Recall@5", "MRR", "Evidence R@5"],
        ["recall_at_1", "recall_at_3", "recall_at_5", "mrr", "evidence_recall_at_5"],
        "Score",
        "Retrieval quality by chunk configuration",
    )
    grouped_chart(
        "citation-answer-quality.png",
        ["Valid IDs", "Source precision", "Source recall", "Fact coverage", "Abstention"],
        [
            "citation_valid_id_rate",
            "citation_source_precision",
            "citation_source_recall",
            "required_fact_coverage",
            "abstention_accuracy",
        ],
        "Score",
        "Citation attribution and deterministic answer checks",
    )

    stages = ["retrieval", "generation", "end_to_end"]
    stage_labels = ["Retrieval", "Generation", "End to end"]
    x = np.arange(len(stages), dtype=float)
    width = 0.8 / max(1, len(experiments))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), constrained_layout=True, sharey=True)
    for axis, percentile in zip(axes, ("p50", "p95")):
        for index, item in enumerate(experiments):
            values = [float(item["latency_ms"][stage][percentile]) for stage in stages]
            positions = x - 0.4 + width / 2 + index * width
            bars = axis.bar(
                positions,
                values,
                width,
                label=names[index],
                color=colors[index % len(colors)],
            )
            axis.bar_label(bars, labels=[f"{value:.0f}" for value in values], padding=3, fontsize=8)
        axis.set_xticks(x, stage_labels)
        axis.set_title(percentile.upper())
        axis.grid(axis="y", alpha=0.2)
    axes[0].set_ylabel("Milliseconds")
    axes[1].legend(frameon=False)
    fig.suptitle("Warm-query response latency")
    fig.savefig(charts_dir / "latency.png", dpi=180)
    plt.close(fig)
