
from __future__ import annotations
import os, hashlib, time, re
from dataclasses import dataclass
from typing import Iterable, List

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def file_sha1(path: str) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

@dataclass
class Timer:
    label: str
    start: float = None
    elapsed: float = 0.0
    def __enter__(self):
        self.start = time.time()
        return self
    def __exit__(self, *exc):
        self.elapsed = time.time() - self.start

def md_escape(text: str) -> str:
    return re.sub(r'([*_`])', r'\\\1', text)

def chunks_iter(seq: List, n: int) -> Iterable[List]:
    for i in range(0, len(seq), n):
        yield seq[i:i+n]
