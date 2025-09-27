
from __future__ import annotations
import os, json, time
from typing import List, Dict, Tuple
from pydantic import BaseModel
from .utils import ensure_dir, Timer
from .loaders import load_documents
from .chunkers import chunk_text
from .embeddings import OllamaEmbedder
from .vectordb import get_or_create_collection, upsert_chunks
from .retriever import retrieve
from .prompts import render_context, compose_prompt
from .llm import OllamaLLM

class Config(BaseModel):
    paths: Dict[str, str]
    embedder: Dict[str, object]
    llm: Dict[str, object]
    chunking: Dict[str, object]
    retrieval: Dict[str, object]
    prompting: Dict[str, str]

def read_config(path: str) -> Config:
    import yaml
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return Config(**cfg)

def ingest_corpus(cfg: Config) -> Dict[str, int]:
    data_dir = cfg.paths["data_dir"]
    storage_dir = cfg.paths["storage_dir"]
    ensure_dir(storage_dir)

    docs = load_documents(data_dir)
    profile = cfg.chunking.get("profile", "paper")
    size = int(cfg.chunking.get("size", 900))
    overlap = int(cfg.chunking.get("overlap", 150))

    all_chunks: List[Dict] = []
    for d in docs:
        chunks = chunk_text(d["text"], profile, size, overlap)
        for j, ch in enumerate(chunks):
            all_chunks.append({
                "id": f"{d['doc_id']}@{ch['span'][0]}-{ch['span'][1]}",
                "text": ch["content"],
                "meta": {
                    "path": d["path"],
                    "page": d["page"],
                    "source": d["doc_id"],
                    "span": ch["span"],
                }
            })

    # Embed and upsert in batches
    embedder = OllamaEmbedder(cfg.embedder["model"])
    batch = int(cfg.embedder.get("batch_size", 64))
    with Timer("embed+upsert") as t:
        collection = get_or_create_collection(storage_dir, "rag")
        for i in range(0, len(all_chunks), batch):
            window = all_chunks[i:i+batch]
            vecs = embedder.embed([c["text"] for c in window])
            upsert_chunks(collection, [
                {"id": window[k]["id"], "text": window[k]["text"], "meta": window[k]["meta"], "embedding": vecs[k]}
                for k in range(len(window))
            ])

    return {"documents": len(docs), "chunks": len(all_chunks)}

def ask_question(cfg: Config, question: str) -> Tuple[str, List[Dict]]:
    storage_dir = cfg.paths["storage_dir"]
    top_k = int(cfg.retrieval.get("top_k", 6))
    min_score = float(cfg.retrieval.get("min_score", 0.0))

    embedder = OllamaEmbedder(cfg.embedder["model"])
    hits = retrieve(storage_dir, embedder, question, top_k=top_k, min_score=min_score)

    system = cfg.prompting["system"]
    template = cfg.prompting["template"]

    context = render_context(hits)
    prompt = compose_prompt(system, template, question, context)

    llm = OllamaLLM(cfg.llm["model"], cfg.llm.get("temperature", 0.2), cfg.llm.get("max_tokens", 1024))
    answer = llm.generate(prompt["system"], prompt["user"])

    return answer, hits

def save_answer(cfg: Config, question: str, answer: str, hits: List[Dict]) -> str:
    outputs_dir = cfg.paths["outputs_dir"]
    ensure_dir(outputs_dir)
    ts = time.strftime("%Y%m%d-%H%M%S")
    md_path = os.path.join(outputs_dir, f"answer-{ts}.md")
    # Build sources section
    lines = [f"# Q: {question}", "", answer, "", "## Sources"]
    for i, h in enumerate(hits, 1):
        src = h["meta"].get("source")
        path = h["meta"].get("path")
        page = h["meta"].get("page")
        lines.append(f"[S{i}] {src} — {path}" + (f" (p.{page})" if page else ""))
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    # also persist a machine-readable JSON
    json_path = os.path.join(outputs_dir, f"answer-{ts}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "question": question,
            "answer": answer,
            "sources": hits,
        }, f, ensure_ascii=False, indent=2)
    return md_path
