from __future__ import annotations
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from ragtoolkit.pipeline import read_config, ask_question, ingest_corpus
from typing import List, Dict, Optional

app = FastAPI(title="RAG Toolkit Web UI", version="1.0.0")

# Pydantic models for API
class QuestionRequest(BaseModel):
    question: str
    config_path: str = "rag.yaml"

class IngestRequest(BaseModel):
    config_path: str = "rag.yaml"

class QuestionResponse(BaseModel):
    answer: str
    sources: List[Dict]
    question: str

class IngestResponse(BaseModel):
    documents: int
    chunks: int
    message: str

# Load the HTML template
def load_template():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface."""
    return HTMLResponse(content=load_template())

@app.post("/api/ask", response_model=QuestionResponse)
async def ask_question_api(request: QuestionRequest):
    """Ask a question using the RAG system."""
    try:
        cfg = read_config(request.config_path)
        answer, hits = ask_question(cfg, request.question)
        
        # Format sources for the API
        sources = []
        for i, hit in enumerate(hits, 1):
            sources.append({
                "id": f"S{i}",
                "source": hit['meta'].get('source', ''),
                "path": hit['meta'].get('path', ''),
                "page": hit['meta'].get('page', ''),
                "text": hit['text'][:200] + "..." if len(hit['text']) > 200 else hit['text']
            })
        
        return QuestionResponse(
            answer=answer,
            sources=sources,
            question=request.question
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ingest", response_model=IngestResponse)
async def ingest_documents_api(request: IngestRequest):
    """Ingest documents into the vector database."""
    try:
        cfg = read_config(request.config_path)
        stats = ingest_corpus(cfg)
        
        return IngestResponse(
            documents=stats['documents'],
            chunks=stats['chunks'],
            message=f"Successfully ingested {stats['documents']} documents with {stats['chunks']} chunks"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "rag-toolkit-web"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
