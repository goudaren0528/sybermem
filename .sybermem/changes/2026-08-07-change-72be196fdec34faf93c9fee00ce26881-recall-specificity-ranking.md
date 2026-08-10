---
type: change
record_id: change-72be196fdec34faf93c9fee00ce26881
date: 2026-08-07
title: Rank compact recall by match specificity before freshness
key_conclusion: Added match-specificity (record-id>relation>topic>keyword) to the compact recall sort ahead of freshness/recency so a precisely-matched record is no longer buried under a newer, generically-matched one
topics: [recall, search, quality]
status: implemented
related: [change-a6dd46baa8994962a257a43e1a73daee]
---

## Change Content

Extracted the compact recall sort into `_compact_sort_key` and inserted a specificity tier between authority and freshness. New key: `(authority, specificity, freshness, score, created)`, where specificity = record-id(0) > relation(1) > topic(2) > keyword(3), unknown(4).

Authority still leads so low-trust evidence never floats above authoritative hits, and recency is only the final tiebreak.

## Reason for Change

E5: the previous key was `(authority, freshness, score, created)`, so a newer generic keyword match outranked an older but far more specific topic/relation match of equal authority/freshness (Oracle's change-048-over-change-037 example). Specificity is a better relevance signal than recency for recall.

## Impact Scope

- `packages/core/sybermem_core/search.py`: `_compact_sort_key` + `_MATCH_SPECIFICITY`.
- Test: a topic-matched older record now ranks above a keyword-matched newer one.
- Verified: core suite green.
