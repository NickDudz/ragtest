
# Local RAG Toolkit

A self-contained **Retrieval-Augmented Generation** stack for Windows.
Drop documents into `data/`, run `ingest`, then `ask` questions with grounded citations.

---

## Features
- **One-command ingest:** `python rag.py ingest` parses PDFs/MD/TXT and builds a local index.
- **RAG querying:** `python rag.py ask "question"` → answer with **[S1]**-style citations.
- **Web interface:** `python web_server.py` → modern React UI at http://localhost:8000.
- **Local embeddings + vector DB:** Defaults to **ChromaDB**.
- **Model-agnostic:** Works with **Ollama** (Qwen/Llama/Phi). Swap models via `rag.yaml`.
- **Chunking profiles:** `paper`, `notes`, `legal` tuned for different formats.
- **Config-driven:** Single `rag.yaml` controls paths, chunking, retrieval, and LLMs.

---

## Quick Start (Windows)
```powershell
# Clone the repository
git clone https://github.com/yourusername/ragtest.git
cd ragtest

py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# Install Ollama, then pull models:
ollama pull qwen2.5:7b-instruct
ollama pull nomic-embed-text

# Add docs into .\data\
python rag.py ingest
python rag.py ask "Summarize Paper X in 5 bullets with citations."

# Or use the web interface:
python rag.py web
# Open http://localhost:8000
```

### Project Layout
```
RAGtest/
├─ data/                     # your PDFs/MD/TXT
├─ storage/                  # vector DB + metadata (gitignored)
├─ outputs/                  # answers, logs, exports
├─ templates/                # web UI templates
├─ rag.yaml                  # configuration
├─ rag.py                    # CLI (ingest, ask, eval, clear)
├─ web_server.py             # FastAPI web server
└─ ragtoolkit/
   ├─ loaders.py             # file loaders & text cleaning
   ├─ chunkers.py            # chunk strategies & profiles
   ├─ embeddings.py          # embedder adapters (Ollama)
   ├─ vectordb.py            # chroma wrapper
   ├─ retriever.py           # retrieval logic + scoring
   ├─ prompts.py             # prompt templates
   ├─ llm.py                 # LLM adapter (Ollama)
   ├─ pipeline.py            # glue: ingest(), ask(), eval()
   └─ utils.py               # helpers (timers, hashing, paths)
```

---

## Demo Script (2 minutes)
1. Add PDFs/notes to `data/`.
2. `python rag.py ingest` → watch counts.
3. `python rag.py ask "Key findings of Paper X?"` → answer + citations.
4. Or `python rag.py web` → open http://localhost:8000 for web UI.


**License:** MIT 
