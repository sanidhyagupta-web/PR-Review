---
title: "Add unit tests for chunk_hasher.compute_hash"
slug: eng-27
status: active
last_updated: 2026-10-15
linear_issue: "https://linear.app/flightdecktest-2/issue/ENG-27/add-unit-tests-for-chunk-hashercompute-hash"
proposed_by: agent
identity_confirmed: false
---

## Current State

Requested in [ENG-27](https://linear.app/flightdecktest-2/issue/ENG-27/add-unit-tests-for-chunk-hashercompute-hash). Alignment agreed the spec under Requirements, as the ticket said when alignment agreed it.

## Key Facts

Nothing recorded yet.

## Requirements

Repository: [https://github.com/sanidhyagupta-web/PR-Review](<https://github.com/sanidhyagupta-web/PR-Review>)

### What to do

Add `tests/unit/test_chunk_hasher.py`, in the style of the existing files in `tests/unit/`, covering the current behaviour. Do not change `chunk_hasher.py`.

### Summary

Work-Type: Tech-Debt

Add focused unit coverage for `ingestion.chunking.chunk_hasher.compute_hash` so its current whitespace normalization, lower-casing, UTF-8 encoding, and SHA-256 behavior are protected against regressions.

### Context

[`ingestion/chunking/chunk_hasher.py`](<https://github.com/sanidhyagupta-web/PR-Review/blob/main/ingestion/chunking/chunk_hasher.py>) has one public function, `compute_hash(text)`. It collapses whitespace runs to one space, trims, lower-cases, UTF-8 encodes the result, and returns its SHA-256 hexadecimal digest.

`semantic_chunker.py` and `entity_preserving_chunker.py` assign this hash to created chunks. The active `ChunkingWorker` passes those hashes to `register_chunk`, and the unique `chunk_registry.chunk_hash` field is the sole deduplication mechanism. A normalization change can therefore silently change which chunks count as duplicates. No existing test file directly targets `chunk_hasher`.

The impact is regression risk in duplicate-chunk identification: an untested normalization change can silently alter which chunks share a hash.

### User Flow

*Not applicable: this is a unit-test-only change and does not alter any runtime user flow.*

### Error Paths

No production error behavior is being added or changed. The test suite must cover the specified edge cases, including empty, whitespace-only, and non-ASCII string input.

### Acceptance Criteria

 1. Given the same text on repeated calls, when `compute_hash` is called, then it returns the same digest each time.
 2. Given a string input, when `compute_hash` returns, then the result is exactly 64 lower-case hexadecimal characters.
 3. Given a string input, when `compute_hash` returns, then the value is the SHA-256 digest of the normalized text encoded as UTF-8.
 4. Given two texts differing only in letter case, when each is hashed, then their hashes are equal.
 5. Given two texts differing only in leading or trailing whitespace, when each is hashed, then their hashes are equal.
 6. Given two texts differing only in the amount or kind of whitespace between words—including spaces, tabs, and newlines—when each is hashed, then their hashes are equal.
 7. Given two texts differing in a word, when each is hashed, then their hashes are different.
 8. Given two texts differing in punctuation, when each is hashed, then their hashes are different.
 9. Given an empty string and a whitespace-only string, when each is hashed, then both return the SHA-256 hexadecimal digest of the empty string.
10. Given non-ASCII text such as `"Café"`, when it is hashed, then hashing succeeds and the returned value matches the SHA-256 digest of its normalized UTF-8 text.
11. `pytest tests/unit/test_chunk_hasher.py` passes.
12. The new test file imports nothing outside the standard library, `pytest`, and `ingestion.chunking.chunk_hasher`.

### Existing System Behaviour

`ingestion/chunking/chunk_hasher.py` currently normalizes with `re.sub(r"\s+", " ", text).strip().lower()`, UTF-8 encodes the normalized text, and returns `hashlib.sha256(...).hexdigest()`.

`ingestion/chunking/semantic_chunker.py` and `ingestion/chunking/entity_preserving_chunker.py` both call `compute_hash` when creating chunks. `workers/chunking_worker.py` uses each resulting `chunk_hash` when registering chunks, and `db/models.py` makes `chunk_registry.chunk_hash` unique. No existing test file targets `chunk_hasher`.

### Scope Boundaries

* Add `tests/unit/test_chunk_hasher.py` in the style of the existing Python tests under `tests/unit/`.
* Do not change `ingestion/chunking/chunk_hasher.py`, either consuming chunker, production deduplication code, or schemas.
* Test the public `compute_hash(text: str)` contract; unsupported non-string inputs are outside scope.
* Do not add dependencies beyond the standard library, `pytest`, and the module under test.
* Migration and data rollback are not applicable because this change adds tests only and touches no runtime state or schema. Reverting the added test file restores the prior repository state.

### Reference Documents

* `code-wiki/healthcare-ingestion-pipeline/Features/Feat-0002-chunking-embedding-indexing/Index.md`
* `wiki/healthcare-ingestion-pipeline/feature-requests/eng-27/feature-request.md`
* `ingestion/chunking/chunk_hasher.py`
* `ingestion/chunking/semantic_chunker.py`
* `ingestion/chunking/entity_preserving_chunker.py`
* `workers/chunking_worker.py`
* `ingestion/registry.py`
* `db/models.py`
* `tests/unit/test_bulk_ingestion.py`
* `tests/unit/test_researcher_role.py`
* `tests/unit/test_dicom_parser.py`
* `.claude/skills/backend-test/SKILL.md`
* `.claude/skills/post-checks/SKILL.md`
* `conftest.py`
* `requirements.txt`

### Round log

* Round 1, aligned: classified as test-focused tech debt; verified the implementation, consumers, actual deduplication path, missing direct tests, pytest setup, and unit-test conventions; corrected stale documentation references and clarified that chunkers assign hashes while the worker and registry perform duplicate detection.

## Business Rules

Nothing recorded yet.

## Decisions

| Date | Title | Type | Ticket |
|---|---|---|---|

## Evidence

Nothing recorded yet.

## Open Questions

- Is this the right name and boundary for this work? Keep the folder name `eng-27`: a later alignment of ENG-27 updates the page there. Set `identity_confirmed: true` once a person has answered this, and delete the question only after it is answered.

**Resolved:**

Nothing recorded yet.

## Risks / Rejected Approaches

Nothing recorded yet.

## Relationships

**Depends On:** Nothing recorded yet.

**Related:** Nothing recorded yet.
