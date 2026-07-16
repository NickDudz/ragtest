# Local RAG Toolkit and Evaluation Lab

Local RAG Toolkit is an Ollama-first retrieval-augmented generation project for
Windows. It can ingest PDF, Markdown, and text files into Chroma, answer
questions with `[S#]` citations, serve a small FastAPI web interface, and run a
reproducible evaluation that keeps retrieval quality separate from generated
answer checks.

The evaluation lab is the main demonstration: a version-controlled corpus,
manually authored ground truth, two controlled retrieval configurations,
deterministic metrics, stage-level timing, and auditable run artifacts. It does
not require a paid API or an LLM judge.

## Results status

Reference run `meridian-v1-20260716T175543Z-c3a8dabf` completed all 60 measured
responses on an NVIDIA GeForce RTX 4080 with Python 3.12.13, Ollama 0.11.5,
`nomic-embed-text:latest`, and `qwen2.5:7b-instruct-q4_K_M`.

| Configuration | Recall@1 | Recall@5 | MRR | Citation source recall | Fact coverage | End-to-end p50 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `baseline_900_150` | 0.60 | 0.88 | 0.775 | 0.72 | 0.523 | 6122 ms |
| `focused_500_80` | 0.76 | 0.94 | 0.920 | 0.80 | 0.543 | 5435 ms |

The focused configuration improved source retrieval and measured generation
latency in this small controlled run, while evidence Recall@5 improved only from
0.753 to 0.787 and citation presence decreased from 0.92 to 0.88. These results
do not establish general superiority outside this corpus and hardware context.

Evidence: [full measured report](artifacts/evaluation/meridian-v1-20260716T175543Z-c3a8dabf/report.md),
[machine-readable summary](artifacts/evaluation/meridian-v1-20260716T175543Z-c3a8dabf/summary.json),
[run manifest](artifacts/evaluation/meridian-v1-20260716T175543Z-c3a8dabf/run_manifest.json),
and [reviewed failures](artifacts/evaluation/meridian-v1-20260716T175543Z-c3a8dabf/error_analysis.md).

An experiment configuration is not itself a result. Report a metric only when
its manifest has `"status": "completed"` and keep the hardware, model digests,
input hashes, and per-question output attached. This reference run was made from
a dirty worktree whose complete tracked diff and untracked-file hashes are
captured by `workspace_state_sha256`; rerun from a committed checkout before
claiming commit-level provenance.

## Requirements

- Windows with PowerShell
- Python 3.12
- [Ollama](https://ollama.com/) running at `http://localhost:11434`
- Enough local memory and storage for the selected Ollama models and two small
  temporary Chroma indexes

Direct Python dependencies are pinned in `requirements.txt`; the fully resolved
Windows reference environment is captured in `requirements-lock.txt`.

## Setup

```powershell
git clone https://github.com/NickDudz/Local-RAG-Toolkit.git
cd Local-RAG-Toolkit

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt

ollama pull nomic-embed-text:latest
ollama pull qwen2.5:7b-instruct-q4_K_M
```

Those exact model tags are required by `evaluation/experiments.yaml`. The
interactive toolkit instead reads its model names from `rag.yaml`; if that file
names a different tag, pull that tag or update the configuration before using
`ingest` and `ask`. Model tags are convenient names, not immutable version
identifiers, so each evaluation run also records Ollama's resolved model digest.

If PowerShell blocks activation, invoke the environment directly, for example
`.\.venv\Scripts\python.exe -m pytest`.

## Reproduce the evaluation

With Ollama running and the two exact model tags installed, run this command
from the repository root:

```powershell
python rag.py eval --config evaluation/experiments.yaml
```

The command validates the corpus manifest, file hashes, golden-data schema, and
verbatim evidence anchors before indexing. It then creates a fresh isolated
Chroma index for each configuration, runs one excluded warm-up query, evaluates
all 30 questions, and writes a new timestamped directory under
`artifacts/evaluation/`. A failed or partial run is not a benchmark result.

Run the automated checks independently with:

```powershell
python -m pytest
```

## Evaluation design

The fixed `meridian-v1` dataset contains eight original, fictional operations
documents under the MIT License and exactly 30 manually authored questions:

- 20 answerable single-source questions
- 5 answerable questions requiring two sources amid overlapping distractors
- 5 unanswerable questions about plausible but absent details

Each answerable record identifies expected source documents, exact contiguous
evidence text, and required fact phrases. Unanswerable records have no expected
source, evidence, or required facts. Stable source IDs are independent of chunk
boundaries.

Only chunk geometry changes between the two experiments:

| Configuration | Chunk size | Overlap | Top-k |
| --- | ---: | ---: | ---: |
| `baseline_900_150` | 900 words | 150 words | 6 |
| `focused_500_80` | 500 words | 80 words | 6 |

Both configurations use the same corpus, questions, cosine distance, prompt,
retrieval depth, local embedding model, local generation model, temperature 0,
seed 7, 8,192-token context window, 256-token response cap, and no reranker or
score threshold. Each receives a separate run-local index under
`.eval_cache/<run-id>/`, preventing cross-configuration state from contaminating
the comparison.

See [the evaluation asset guide](evaluation/README.md) for the dataset schema
and [the architecture note](docs/evaluation/ARCHITECTURE.md) for execution and
trust boundaries.

## Metrics

Retrieval metrics are aggregated over the 25 answerable questions. Citation and
answer checks are deterministic signals, not model-judge scores.

| Metric | Definition |
| --- | --- |
| Recall@1, @3, @5 | Fraction of unique expected source documents present in the first `k` retrieved chunks. |
| Evidence Recall@1, @3, @5 | Fraction of gold evidence anchors contained in a same-source top-`k` chunk after whitespace normalization. |
| MRR | Mean reciprocal rank of the first chunk from an expected source. |
| Citation valid-ID rate | Fraction of generated `[S#]` mentions whose one-based index maps to an available retrieved chunk. |
| Citation presence | Fraction of answerable responses containing at least one parsed citation. |
| Citation source precision | Fraction of unique valid cited targets that belong to an expected source document. |
| Citation source recall | Fraction of expected source documents reached by at least one valid citation. |
| Required-fact coverage | Fraction of authored facts matched by a case-insensitive, whitespace-normalized `any_of` phrase. This is only a lexical answer-quality proxy. |
| Abstention accuracy | Fraction of the five unanswerable questions whose response matches the documented deterministic abstention patterns. |

Wall-clock latency is captured separately for query embedding, vector search,
combined retrieval, generation, and end to end. Aggregates include count, mean,
minimum, p50, p95, and maximum. Index creation separately records embedding,
upsert, and total ingestion time. Because V1 performs one measured generation
per question and configuration, its latency distribution is descriptive of the
recorded run, not a capacity benchmark.

Citation checks establish that a citation identifier is valid and points to an
expected source. They do not prove that the cited passage entails every nearby
claim. Required-fact matching can miss a correct paraphrase or reward a phrase
used in the wrong context; per-question review remains necessary.

## Evaluation artifacts

Each successful run writes this shape:

```text
artifacts/evaluation/<run-id>/
├── experiments.yaml
├── run_manifest.json
├── per_question.jsonl
├── summary.json
├── summary.csv
├── report.md
├── error_analysis.md
└── charts/
    ├── retrieval-quality.png
    ├── citation-answer-quality.png
    └── latency.png
```

`run_manifest.json` records run status and timestamps; the reproduction command;
git state; Python and direct dependency versions; hardware context; Ollama
version, model details, and digests; the complete resolved configuration; and
hashes for the config, prompt, corpus, manifest, golden set, and completed
results. `per_question.jsonl` contains ranked chunks, generated answers,
per-question metrics, timings, and model response metadata. `summary.json` and
`summary.csv` are aggregate machine-readable views, while `report.md` and the
PNG charts are compact presentation artifacts.

A representative `error_analysis.md` is a reviewed reference-run deliverable,
not an automatically fabricated runner output. It should be written only after
examining real `per_question.jsonl` failures.

## Use the interactive toolkit

Place `.pdf`, `.md`, or `.txt` files in `data/`, then use the model and paths
configured in `rag.yaml`:

```powershell
python rag.py ingest --config rag.yaml
python rag.py ask "What does the corpus say about recovery?" --config rag.yaml
```

`ingest` loads and word-window chunks the files, creates embeddings through the
local Ollama HTTP API, and upserts them into the persistent `rag` collection in
`storage/`. `ask` embeds the question, retrieves the configured top-k chunks,
renders them as `[S#]` context, calls Ollama for generation, prints the source
mapping, and saves Markdown and JSON responses under `outputs/` by default.

Start the web interface with a loopback-only bind when remote access is not
needed:

```powershell
python rag.py web --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000`. The FastAPI service exposes `POST /api/ingest`,
`POST /api/ask`, and `GET /api/health`. The current HTML template loads React,
ReactDOM, and Babel from `unpkg.com`, so the browser UI itself is not fully
offline even though documents, indexes, embeddings, and generation remain
local. The CLI and evaluation runner do not need those browser assets.

## Repository layout

```text
Local-RAG-Toolkit/
├── data/                         # Interactive corpus supplied by the user
├── evaluation/
│   ├── corpus/                   # Fixed MIT-licensed evaluation corpus
│   ├── corpus_manifest.yaml      # Stable IDs, provenance, and SHA-256 hashes
│   ├── golden.jsonl              # 30 authored questions and evidence labels
│   └── experiments.yaml          # Two-variable controlled experiment matrix
├── docs/evaluation/              # Architecture and evaluation documentation
├── ragtoolkit/
│   ├── evaluation/               # Validation, metrics, runner, and reporting
│   └── ...                       # Interactive ingestion and RAG components
├── tests/                        # Dataset, metric, adapter, and runner tests
├── artifacts/evaluation/         # Generated measured run artifacts
├── storage/                       # Interactive Chroma database; ignored
├── outputs/                       # Interactive answer exports; ignored
├── templates/                     # FastAPI browser UI
├── rag.py                         # Typer CLI
├── rag.yaml                       # Interactive toolkit configuration
├── requirements.txt               # Direct pinned Python dependencies
└── requirements-lock.txt          # Fully resolved Windows reference environment
```

## Limitations

- The corpus is small, fictional, English-only, and designed to contain useful
  distractors. Results do not generalize to arbitrary private collections.
- V1 compares only two word-window chunk geometries. It does not evaluate
  semantic chunking, reranking, hybrid search, or alternate embedding models.
- A seed and temperature 0 improve repeatability but do not guarantee identical
  generation across Ollama, model, driver, or hardware versions.
- Lexical fact coverage and citation-source attribution are transparent proxies,
  not semantic correctness or entailment judgments.
- One measured response per question is insufficient for strong tail-latency or
  throughput claims.
- Evaluation latency includes local service and hardware effects. Comparisons
  are meaningful only with their recorded run context.
- The interactive collection is shared and uses upsert semantics; the evaluation
  runner avoids that state by creating fresh isolated indexes.

## License

Toolkit code is licensed under the repository [MIT License](LICENSE). The
project-authored evaluation corpus carries its own [MIT License](evaluation/corpus/LICENSE).
