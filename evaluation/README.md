# Evaluation assets

This directory contains the fixed inputs for the Local RAG Toolkit's first
evaluation suite. It intentionally separates authored ground truth from runner
code and generated results.

## Corpus and provenance

`corpus/` contains eight fictional Meridian Research Cooperative operations
documents written specifically for this project. No external text or factual
organizational policy was copied into the corpus. The documents are available
under the MIT License in `corpus/LICENSE`.

The topics overlap on purpose. Terms such as *incident*, *legal hold*,
*quarantine*, *sensor*, *offline*, *retention*, *recovery*, and *maintenance*
appear in several documents with distinct rules. Each document is longer than
1,100 words so the two chunk geometries produce meaningfully different passage
boundaries.

`corpus_manifest.yaml` is the corpus inventory. Paths in the manifest are
relative to the manifest file. The stable `id` is used by `golden.jsonl`; it is
not derived from a future chunk boundary. SHA-256 values cover the files exactly
as committed. If a corpus file changes, its manifest entry and any affected
evidence text must be updated together.

## Golden dataset

`golden.jsonl` has exactly 30 manually authored records:

- 20 answerable questions whose expected evidence is in one source
- 5 answerable questions that require two sources amid overlapping distractors
- 5 unanswerable questions about plausible but absent policy details

Every line is one JSON object with this schema:

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | string | Unique, stable question ID. |
| `question` | string | The question given to retrieval and generation. |
| `answerable` | boolean | Whether the fixed corpus contains an answer. |
| `expected_sources` | string array | Corpus source IDs needed for a supported answer. Empty for unanswerable records. |
| `evidence` | object array | Gold passages with `source` and `text`. Each `text` value is an exact contiguous substring of that source document. |
| `required_facts` | object array | Deterministic answer-quality proxies. Each object has a stable `id` and an `any_of` list of acceptable case-insensitive phrases. |
| `tags` | string array | Slices such as `single_source`, `multi_source`, `distractor`, and `unanswerable`. |

The source-level labels support document recall and reciprocal rank without
depending on implementation-specific chunk IDs. Evidence strings support a
stricter passage-level check: a retrieved chunk receives evidence credit when
it contains the gold text after whitespace runs are normalized. Required-fact
phrase coverage is a transparent proxy, not a claim of semantic equivalence or
general answer correctness.

For an unanswerable record, `expected_sources`, `evidence`, and
`required_facts` are all empty. These records test abstention separately from
retrieval recall. A top-ranked chunk for an unanswerable question is not called
relevant merely because the vector store always returns a neighbor.

## Experiment matrix

`experiments.yaml` compares only two word-window chunking configurations:

| Experiment | Chunk size | Overlap | Top-k |
| --- | ---: | ---: | ---: |
| `baseline_900_150` | 900 | 150 | 6 |
| `focused_500_80` | 500 | 80 | 6 |

Embedding model, generation model, prompt, retrieval depth, temperature, seed,
8,192-token context window, 256-token response cap, reranking setting, and run
count are shared at the top level. This keeps the comparison interpretable:
only chunk size and overlap change. V1 does not use a model judge.

The configured models are local Ollama tags:

- `nomic-embed-text:latest`
- `qwen2.5:7b-instruct-q4_K_M`

The evaluation runner records the resolved model metadata and environment in
each run manifest. Model tags alone are not treated as immutable version proof.

## Validation rules

Dataset validation should fail when any of these conditions is true:

- a question ID or source ID is duplicated;
- the number or declared composition of records changes unexpectedly;
- an expected source does not exist in the manifest;
- an evidence source is not expected by that question;
- evidence text is not an exact contiguous substring of its source;
- an answerable record has no expected source, evidence, or required fact;
- an unanswerable record has any expected source, evidence, or required fact;
- a manifest hash differs from the corpus file.

## Reproduction

From the repository root, with Ollama running and the configured models
available, the documented evaluation entry point is:

```powershell
python rag.py eval --config evaluation/experiments.yaml
```

The command validates these inputs before creating an index or reporting
metrics. Generated results belong under `artifacts/evaluation/`, not in this
directory. Do not add measured values to these source assets by hand.
