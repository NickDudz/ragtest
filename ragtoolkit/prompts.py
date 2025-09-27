
from __future__ import annotations
from typing import List, Dict

def render_context(chunks: List[Dict]) -> str:
    # Build context text with inline citation markers that map to a source list
    lines = []
    for idx, ch in enumerate(chunks, 1):
        lines.append(f"[S{idx}] {ch['text']}")
    return "\n\n".join(lines[:10])  # cap context size

def compose_prompt(system: str, template: str, question: str, context: str) -> Dict[str, str]:
    user = template.format(question=question, context=context)
    return {
        "system": system.strip(),
        "user": user.strip()
    }
