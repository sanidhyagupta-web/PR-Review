---
feat_id: Feat-0002
feature: chunking-embedding-indexing
type: backend-service
domain: retrieval-indexing
criticality: high
touched_paths:
  - ingestion/chunking/
  - workers/chunking_worker.py
  - workers/embedding_worker.py
  - workers/keyword_index_worker.py
  - indexing/
depends_on: [Feat-0003]
consumed_by: [Feat-0004, Feat-0005, Feat-0007]
implements: []
tags: [chunking, embeddings, vector-search, keyword-search]
---

## Overview

| Type | Package | Path | Domain | Last updated |
|---|---|---|---|---|
| backend-service | (none) | `ingestion/chunking/`, `workers/{chunking,embedding,keyword_index}_worker.py`, `indexing/` | retrieval-indexing | 2026-09-05 |

## Domain Purpose

Turns markdown-formatted document text into retrievable chunks: splits text so medical entities
(medication + dosage + frequency) are never separated, deduplicates identical chunks, embeds
them for vector search, and indexes them for keyword (BM25) search — the two retrieval paths
that Feat-0005's search pipeline queries.

## Entities Owned

| Entity | Represents |
|---|---|
| [`chunk_registry`](../../Schemas/schemas.md#chunk_registry) | Chunk identity and dedup registry |
| [`chunk_metadata`](../../Schemas/schemas.md#chunk_metadata-non-relational--chroma--keyword-index-document-metadata) | The metadata dict attached to every indexed chunk (`allowed_roles` populated by Feat-0004) |
| `index_metadata_schema` | `indexing/index_schema.py`'s `REQUIRED_METADATA_FIELDS` — defined but its `validate_metadata()` has no found call site (open question) |

## Invariants

- Chunk hash (`chunk_hash`, SHA-256 of normalized text) is globally unique — enforced by the
  `UNIQUE` constraint on `chunk_registry.chunk_hash`, the sole dedup mechanism.
- No entity group (medication + dosage + frequency) is ever split across two chunks, even if
  that pushes a chunk over the configured `chunk_size` (`entity_preserving_chunker.py:228`).
- Chunks under 30 words are merged into a neighbor rather than left standalone
  (`entity_preserving_chunker.py:272-322`).
- Indexing workers never re-run PII detection — they read already-redacted text from
  `redacted_chunks.json` and trust it (`indexing/opensearch_index.py:22`, `chroma_store.py:32`).

## Access Control

**Model**: None directly enforced here — this feature stores the `allowed_roles` metadata
Feat-0004 stamps, but the actual filtering happens at query time in Feat-0005. Chroma's metadata
sanitizer (`indexing/chroma_store.py:_sanitise_metadata()`) only allows `str`/`int`/`float`/`bool`
values, so `allowed_roles` (a list) is coerced to a comma-delimited string before storage.

## Business Rules

| ID | Rule | Enforced In | Severity |
|---|---|---|---|
| BR-01 | Chunk size defaults to 500 words; entity groups may exceed it but are never split | `app/config.py:chunk_size`, `entity_preserving_chunker.py:228` | HIGH |
| BR-02 | Duplicate chunk (same hash) is skipped, but the document is still marked `CHUNKED` | `workers/chunking_worker.py:36-48` | MEDIUM |
| BR-03 | If *every* chunk in a document is a duplicate, the document is marked `DUPLICATE` instead of `CHUNKED` | `workers/chunking_worker.py:54-56` | MEDIUM |
| BR-04 | Chunks under 30 words are merged with a neighbor | `entity_preserving_chunker.py:272-322` | LOW |
| BR-05 | Embedding model is `sentence-transformers`, default `all-MiniLM-L6-v2` (env-overridable) | `indexing/embeddings.py:39` | MEDIUM |
| BR-06 | Reranking uses `cross-encoder/ms-marco-MiniLM-L-6-v2` over (query, chunk) pairs | `indexing/reranker.py:11-48` | MEDIUM |
| BR-07 | BM25 keyword index is in-process, rebuilt after every chunk upsert, persisted to `bm25_index.json` | `indexing/opensearch_index.py:50-118` | MEDIUM |
| BR-08 | Chroma metadata values are coerced to primitive types before storage (lists → comma string, `None` → `""`) | `indexing/chroma_store.py:_sanitise_metadata()` | LOW |

## External Integrations

| System | Trigger | What Happens |
|---|---|---|
| ChromaDB | `EmbeddingWorker` message | Upserts embedded chunks into a module-level singleton collection |
| BM25 (rank-bm25) | `KeywordIndexWorker` message | Rebuilds in-memory index, persists to `bm25_index.json`; if `rank-bm25` isn't installed, keyword search silently returns `[]` (`opensearch_index.py:30-32`) |
| ChunkingWorker (async) | `chunking_queue` message (from Feat-0003's MarkdownWorker) | Chunks markdown → dedups → registers hashes → pushes to `pii_queue` (Feat-0004) |
| EmbeddingWorker (async) | `embedding_queue` message (from Feat-0006's ExtractionWorker) | Embeds redacted chunk text → Chroma upsert → `DocStatus: INDEXED` |
| KeywordIndexWorker (async) | `keyword_queue` message (fan-out alongside `embedding_queue`) | BM25 index upsert |

## Safe vs Dangerous Changes

### Safe
- Tuning `chunk_size`/`chunk_overlap` in `app/config.py`.
- Swapping the embedding model via the `EMBEDDING_MODEL` env var (same interface).

### Dangerous — Requires Review
| Change | Risk | Why |
|---|---|---|
| Editing `entity_preserving_chunker.py`'s entity regex patterns | Silent chunk-boundary regressions | These patterns are what keeps medication/dosage/frequency atomic — a regression here is invisible until a query returns a truncated drug instruction |
| Changing `chunk_hash` computation | Breaks dedup silently | Existing rows in `chunk_registry` would no longer match newly computed hashes for the same text |

### Human Escalation Required
- None specific to this feature beyond the general RBAC/PHI concerns owned by Feat-0004/Feat-0005.

## Known Error Scenarios

| Scenario | Error Returned | Root Cause |
|---|---|---|
| All chunks in a doc are duplicates | Document → `DUPLICATE` status | dedup loop finds zero new chunks |
| `rank-bm25` not installed | Keyword search returns `[]`, warning logged | `opensearch_index.py:30-32` |
| Empty redacted-chunks file | `EMBEDDED` status set anyway, with a warning logged | `workers/embedding_worker.py:27-30` |

## Testing Expectations

- No dedicated test files found for chunking, embedding, or indexing logic in `tests/unit/`.
  *(Open question: is this covered by an integration/eval harness under `AiHarness/evals/` instead
  of `pytest`?)*

## Architectural Decisions

| Decision | Reason | Do Not Change Without |
|---|---|---|
| Entity-preserving chunking over pure semantic/section chunking | Keeps medication+dosage+frequency atomic for clinical accuracy | Confirming the alternate `semantic_chunker.py` strategy isn't silently expected elsewhere (see open question) |

## Forbidden Patterns

- Never re-detect or re-redact PII inside an indexing worker — trust the already-redacted input.
- Never bypass `chunk_hash` dedup by writing directly to the vector/keyword store.

## Key Files

- `ingestion/chunking/entity_preserving_chunker.py` — the active chunking strategy (entity tagging, greedy packing, min-chunk merge)
- `ingestion/chunking/chunk_hasher.py` — SHA-256 hash + text normalization for dedup
- `ingestion/chunking/semantic_chunker.py` — an alternate chunker, **not imported by `ChunkingWorker`** (see open question)
- `workers/chunking_worker.py`, `workers/embedding_worker.py`, `workers/keyword_index_worker.py`
- `indexing/embeddings.py`, `indexing/chroma_store.py`, `indexing/opensearch_index.py`, `indexing/reranker.py`, `indexing/index_schema.py`, `indexing/pii_entity_index.py`

## Context Routing

| Feature | Load when |
|---|---|
| Feat-0002 (this file) | Touching chunking strategy, embeddings, vector/keyword indexing, reranking |

| Workflow | Sections to load |
|---|---|
| Changing chunk strategy | Business Rules, Architectural Decisions, Key Files |
| Debugging a missing search result | External Integrations, Known Error Scenarios |

## Open Questions

- *Open question: `ingestion/chunking/semantic_chunker.py` defines a chunk strategy that
  `workers/chunking_worker.py` never imports — is it dead code, an alternate strategy awaiting
  wiring, or used by something outside this target's scope (e.g. `hierarchy_builder.py`, which
  does import it)?*
- *Open question: `indexing/index_schema.py:validate_metadata()` has no found call site — is
  metadata validation intentionally unenforced, or a missed wiring?*
