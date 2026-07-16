# Portfolio handoff: Local RAG Evaluation Lab

## What is verified

The completed reference run is
`meridian-v1-20260716T175543Z-c3a8dabf`. Its manifest status is `completed`,
with 60 measured responses: 30 questions across two isolated retrieval
configurations.

| Verified claim | Evidence |
| --- | --- |
| The evaluator validates source paths, SHA-256 hashes, exact evidence anchors, answerability rules, and a 25-50 question count before indexing. | [Dataset validator](ragtoolkit/evaluation/dataset.py), [tests](tests/test_dataset.py), [reproduction command](#exact-setup-and-run) |
| V1 compares only 900/150 versus 500/80 word chunks while holding corpus, models, prompt, cosine distance, top-k 6, temperature 0, seed 7, context window, and response cap constant. | [Experiment configuration](evaluation/experiments.yaml), [run manifest](artifacts/evaluation/meridian-v1-20260716T175543Z-c3a8dabf/run_manifest.json) |
| Focused 500/80 achieved Recall@1 0.76, Recall@5 0.94, and MRR 0.920 versus 0.60, 0.88, and 0.775 for baseline 900/150. | [Summary JSON](artifacts/evaluation/meridian-v1-20260716T175543Z-c3a8dabf/summary.json), [retrieval chart](artifacts/evaluation/meridian-v1-20260716T175543Z-c3a8dabf/charts/retrieval-quality.png) |
| Focused 500/80 achieved citation source precision 0.88 and recall 0.80 versus 0.76 and 0.72. Citation valid-ID rate was 1.00 for both, but citation presence was 0.88 versus 0.92. | [Summary CSV](artifacts/evaluation/meridian-v1-20260716T175543Z-c3a8dabf/summary.csv), [citation chart](artifacts/evaluation/meridian-v1-20260716T175543Z-c3a8dabf/charts/citation-answer-quality.png) |
| Deterministic required-fact coverage was 0.543 focused versus 0.523 baseline; both configurations scored 1.00 on the five-question abstention heuristic. These are proxies, not semantic accuracy. | [Measured report](artifacts/evaluation/meridian-v1-20260716T175543Z-c3a8dabf/report.md), [metric implementation](ragtoolkit/evaluation/metrics.py) |
| End-to-end p50 was 5435 ms focused versus 6122 ms baseline; p95 was 5892 ms versus 6590 ms. The measured reduction came from generation while retrieval stayed near 2063 ms p50. | [Latency chart](artifacts/evaluation/meridian-v1-20260716T175543Z-c3a8dabf/charts/latency.png), [per-question records](artifacts/evaluation/meridian-v1-20260716T175543Z-c3a8dabf/per_question.jsonl) |
| The reference environment was Python 3.12.13, Ollama 0.11.5, Chroma 0.5.23, an NVIDIA GeForce RTX 4080, `nomic-embed-text` digest `0a109f...e59f`, and Qwen digest `845dbd...697e`. | [Run manifest](artifacts/evaluation/meridian-v1-20260716T175543Z-c3a8dabf/run_manifest.json) |
| Automated validation, metric, adapter, config, storage-boundary, and reference-artifact integrity tests pass. | Command: `python -m pytest -q`; current result: 54 passed |

## Dataset and corpus provenance

- **Corpus:** Meridian Research Cooperative Operations Handbook
- **Size:** 8 original Markdown documents, 9,752 words
- **License:** MIT; see [corpus license](evaluation/corpus/LICENSE)
- **Provenance:** Fictional operations policies authored for this project; no
  external policy text was copied. Topics intentionally reuse terms such as
  incident, retention, recovery, sensor, quarantine, and maintenance.
- **Golden data:** 30 manually authored questions: 20 single-source, 5
  multi-source/distractor, and 5 unanswerable.
- **Integrity:** Stable source IDs, exact evidence text, required fact phrases,
  and corpus SHA-256 values are recorded in the [manifest](evaluation/corpus_manifest.yaml)
  and [golden JSONL](evaluation/golden.jsonl).

## Architecture and visual assets

- Architecture and trust boundaries: [ARCHITECTURE.md](docs/evaluation/ARCHITECTURE.md)
- Retrieval comparison: [retrieval-quality.png](artifacts/evaluation/meridian-v1-20260716T175543Z-c3a8dabf/charts/retrieval-quality.png)
- Citation and deterministic answer checks: [citation-answer-quality.png](artifacts/evaluation/meridian-v1-20260716T175543Z-c3a8dabf/charts/citation-answer-quality.png)
- Warm-query latency: [latency.png](artifacts/evaluation/meridian-v1-20260716T175543Z-c3a8dabf/charts/latency.png)
- Compact results narrative: [report.md](artifacts/evaluation/meridian-v1-20260716T175543Z-c3a8dabf/report.md)
- Screenshots: no dedicated results UI screenshot was captured for V1. Use the
  measured charts; do not imply that a hosted evaluation dashboard exists.

## Repository and demo status

- Repository: <https://github.com/NickDudz/Local-RAG-Toolkit>
- Hosted demo: none. V1 is a local CLI experiment and does not require a paid API.
- Optional web UI: the existing FastAPI interface is for interactive ingest/ask,
  not the evaluation report, and its browser template loads CDN assets.

## Exact setup and run

```powershell
git clone https://github.com/NickDudz/Local-RAG-Toolkit.git
cd Local-RAG-Toolkit
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
ollama pull nomic-embed-text:latest
ollama pull qwen2.5:7b-instruct-q4_K_M
python rag.py eval --config evaluation/experiments.yaml
```

Validate the deterministic components separately with `python -m pytest -q`.
Every evaluation creates a new timestamped artifact directory; do not overwrite
the checked-in reference run with results from a different environment.

## Owner contribution and engineering decisions

Portfolio wording can accurately describe this work as extending an existing
local Ollama/Chroma RAG toolkit into a reproducible evaluation lab. The work
includes the authored corpus and gold set, strict validation, controlled
experiment configuration, isolated indexing, retrieval/citation/answer proxy
metrics, stage-level timing, automated tests, machine-readable artifacts,
charts, architecture documentation, and reviewed failure analysis.

Important decisions:

- Changed one interpretable retrieval factor—chunk geometry—instead of building
  a broad evaluation framework or mixing model and reranking effects.
- Kept retrieval quality separate from generation and citation checks.
- Used transparent lexical answer checks and abstention patterns instead of
  presenting a local LLM judge as ground truth.
- Fingerprinted corpus, prompts, configuration, dependencies, model digests,
  hardware, outputs, and complete dirty-worktree state.
- Fixed the existing Ollama embedding API contract and generation options,
  including the explicit 8K context window required to avoid truncating the
  question and early retrieved passages.

## Representative failures and limitations

The full review is in [error_analysis.md](artifacts/evaluation/meridian-v1-20260716T175543Z-c3a8dabf/error_analysis.md).
Representative cases include:

- Baseline `q15` missed the cold-chain document entirely; focused chunks
  recovered it and answered correctly.
- Focused `q17` retrieved the correct document at rank 1 but missed the evidence
  passage and omitted required operational details.
- Focused `q21` returned repeated access-control chunks that crowded out the
  second source required for a complete lost-tablet answer.
- Baseline `q23` used valid `[S3]` syntax that mapped to the wrong document,
  demonstrating why valid-ID rate is not groundedness.
- Both configurations missed the incident-response half of multi-source `q24`.
- Focused `q13` had the relevant source and passage but still abstained.
- Exact phrase matching under-credited a correct `q04` paraphrase, while citation
  ranges such as `[S1-S6]` exposed a parser blind spot.

The corpus is small, fictional, English-only, and deliberately difficult. The
run has one measured generation per question/configuration, an ordered
baseline-then-focused execution, one local hardware profile, and no semantic
entailment judge. The reference manifest records a dirty worktree plus a full
workspace-state hash; rerun after committing before claiming commit-level
provenance or bit-for-bit reproducibility.

## Claims that should not appear publicly

- Do **not** call Recall@5 `0.94` “94% answer accuracy.”
- Do **not** claim all citations were correct; valid-ID rate was 1.00, but focused
  citation source precision was 0.88 and source recall was 0.80.
- Do **not** present required-fact coverage as semantic correctness or a model
  quality percentage.
- Do **not** claim 500/80 chunks are universally superior; this is one small
  corpus, one embedding model, one ordered run, and one machine.
- Do **not** claim production latency, throughput, scalability, or an SLA from
  30 measured queries per configuration.
- Do **not** claim the project is fully air-gapped; the CLI evaluation is local,
  but the optional web template loads JavaScript from `unpkg.com`.
- Do **not** claim reranking, hybrid retrieval, alternate embeddings, or an LLM
  judge were evaluated.
- Do **not** claim citations prove entailment, that hallucinations were
  eliminated, or that every answerable question was answered.
- Do **not** claim the checked-in run came from a clean commit. Its exact dirty
  workspace state is fingerprinted, but commit-level provenance requires a
  post-commit rerun.
