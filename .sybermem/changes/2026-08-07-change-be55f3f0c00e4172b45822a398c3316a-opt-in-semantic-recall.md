---
type: change
record_id: change-be55f3f0c00e4172b45822a398c3316a
date: 2026-08-07
title: Opt-in zero-dependency semantic recall supplement
key_conclusion: Added an opt-in pure-Python char n-gram vector recall supplement so project search can recover synonym/rephrased/typo misses that exact-term lexical scoring drops, without new dependencies, without changing default behavior, and without ever auto-injecting on the hot path
topics: [recall, search, quality]
status: implemented
related: [change-72be196fdec34faf93c9fee00ce26881]
---

## Change Content

Added `semantic_recall.py`: a zero-dependency, offline "semantic-ish" recall built from char n-grams (3-4) over normalized tokens, mapped to a fixed-dim vector via a deterministic FNV hashing trick, L2-normalized, compared by cosine. It is not a transformer embedding — it captures lexical/morphological overlap (shared substrings, word-order-insensitive, robust to inflection/typos/CJK).

`compact_project_search` gained `_add_semantic_supplement`, active only when `SYBERMEM_SEMANTIC_RECALL=1`. It appends records that lexical scoring missed and that clear a high cosine floor (0.30), tagged `match="semantic"` with a bounded score in [5, 10).

## Reason for Change

E2: project-scope recall was purely lexical, so inflected/synonym/rephrased queries (e.g. "authenticating" vs a record's "authentication") silently missed. A local char n-gram vector recovers many such misses. Per the chosen direction, it uses no torch/onnx/model download — consistent with "Markdown is truth, derived indexes are cheap, offline, no heavy third-party deps."

## Impact Scope

- `packages/core/sybermem_core/semantic_recall.py`: new module (build_vector/cosine/semantic_scores).
- `packages/core/sybermem_core/search.py`: opt-in supplement + `SEMANTIC_RECALL_ENV`/floor constants; `_compact_match_allowed` admits `semantic`.
- Safety/economy: OFF by default (hot-path economy unchanged); semantic score always < the high-signal floor (12) so it never auto-injects via the recall hook; lowest specificity in the E5 sort so it never outranks precise lexical hits.
- README recall section documents the opt-in flag.
- Verified: 4 new tests; core suite 137 passed.
