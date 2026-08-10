from __future__ import annotations

import math
import re
from typing import Mapping, Sequence, TypeAlias


# E2: zero-dependency semantic-ish recall. Pure-Python char n-gram vectors via the
# hashing trick + cosine similarity — no torch/onnx/model download, fully offline,
# consistent with SyberMem's "Markdown is truth, derived indexes are cheap and local"
# stance. This is NOT a transformer embedding; it captures lexical/morphological
# overlap (shared substrings, word-order-insensitive, robust to small edits and CJK),
# which recovers many synonym-ish / rephrased / typo'd misses that exact-term lexical
# scoring drops, without pretending to be full semantic understanding.
#
# It is an OPT-IN *supplement* to lexical recall, never a replacement: semantic-only
# hits are surfaced as a weak signal and still pass the same authority/freshness gates.

Vector: TypeAlias = dict[int, float]

_DIM: int = 1024  # hashing-trick dimensionality; small, dense enough for short records.
_TOKEN_RE = re.compile(r"[0-9a-zA-Z\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+")


def _char_ngrams(text: str, lo: int = 3, hi: int = 4) -> list[str]:
    """Return char n-grams over normalized tokens (word boundaries marked)."""
    grams: list[str] = []
    for token in _TOKEN_RE.findall(text.lower()):
        padded = f"^{token}$"
        for size in range(lo, hi + 1):
            if len(padded) < size:
                if token:
                    grams.append(padded)
                continue
            for i in range(len(padded) - size + 1):
                grams.append(padded[i : i + size])
    return grams


def _hash_bucket(gram: str) -> int:
    # Deterministic, stdlib-only, process-independent hash (Python's hash() is salted).
    h = 2166136261
    for ch in gram:
        h = (h ^ ord(ch)) * 16777619 & 0xFFFFFFFF
    return h % _DIM


def build_vector(text: str) -> Vector:
    """Build an L2-normalized sparse hashing-trick vector for the given text."""
    counts: Vector = {}
    for gram in _char_ngrams(text):
        bucket = _hash_bucket(gram)
        counts[bucket] = counts.get(bucket, 0.0) + 1.0
    norm = math.sqrt(sum(value * value for value in counts.values()))
    if norm == 0.0:
        return {}
    return {bucket: value / norm for bucket, value in counts.items()}


def cosine(a: Vector, b: Vector) -> float:
    """Cosine similarity of two L2-normalized sparse vectors (0.0 when either empty)."""
    if not a or not b:
        return 0.0
    # Iterate the smaller vector for speed.
    if len(a) > len(b):
        a, b = b, a
    return sum(value * b.get(bucket, 0.0) for bucket, value in a.items())


def semantic_scores(query: str, rows: Sequence[Mapping[str, str]]) -> list[tuple[int, float]]:
    """Return (row_index, similarity) for rows above no threshold, sorted desc.

    Caller applies its own threshold/gating. Each row's searchable text is its title,
    topics, and body-ish content — the same surface lexical scoring reads.
    """
    query_vec = build_vector(query)
    if not query_vec:
        return []
    scored: list[tuple[int, float]] = []
    for index, row in enumerate(rows):
        text = f"{row.get('title', '')} {row.get('topics', '')} {row.get('content', '')}"
        sim = cosine(query_vec, build_vector(text))
        if sim > 0.0:
            scored.append((index, sim))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored
