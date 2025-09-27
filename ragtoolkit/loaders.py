
from __future__ import annotations
import os
from typing import List, Dict
from pypdf import PdfReader

SUPPORTED_EXT = {'.pdf', '.md', '.txt'}

def _load_pdf(path: str) -> List[Dict]:
    reader = PdfReader(path)
    docs = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        docs.append({
            "doc_id": f"{os.path.basename(path)}#p{i+1}",
            "path": path,
            "page": i+1,
            "text": text.strip()
        })
    return docs

def _load_text(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        txt = f.read()
    return [{
        "doc_id": f"{os.path.basename(path)}",
        "path": path,
        "page": None,
        "text": txt.strip()
    }]

def load_documents(data_dir: str) -> List[Dict]:
    items: List[Dict] = []
    for root, _, files in os.walk(data_dir):
        for name in files:
            ext = os.path.splitext(name)[1].lower()
            if ext not in SUPPORTED_EXT:
                continue
            path = os.path.join(root, name)
            if ext == ".pdf":
                items.extend(_load_pdf(path))
            else:
                items.extend(_load_text(path))
    return [d for d in items if d.get("text")]
