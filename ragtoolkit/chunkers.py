
from __future__ import annotations
from typing import List, Dict

PROFILES = {
    "paper":   {"size": 900, "overlap": 150},
    "notes":   {"size": 500, "overlap": 80},
    "legal":   {"size": 1200, "overlap": 200},
}

def chunk_text(text: str, profile: str, size: int, overlap: int) -> List[Dict]:
    if not text:
        return []
    # Allow overrides but fall back to profile defaults
    base = PROFILES.get(profile, PROFILES["paper"]).copy()
    size = size or base["size"]
    overlap = overlap or base["overlap"]
    toks = text.split()
    out = []
    i = 0
    while i < len(toks):
        window = toks[i:i+size]
        out.append({
            "content": " ".join(window),
            "span": (i, min(i+size, len(toks)))
        })
        i += max(1, size - overlap)
    return out
