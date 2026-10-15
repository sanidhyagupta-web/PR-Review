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

Add focused unit coverage for `ingestion.chunking.chunk_hasher.compute_hash` so its current normalization and SHA-256 behavior are protected against regressions.

### Context

[`ingestion/chunking/chunk_hasher.py`](<https://github.com/sanidhyagupta-web/PR-Review/blob/main/ingestion/chunking/chunk_hasher.py>) has one public function, `compute_hash(text)`. It collapses whitespace runs to one space, trims, lower-cases, and returns the SHA-256 hex digest. Both chunkers use it to detect duplicate chunks (`semantic_chunker.py`, `entity_preserving_chunker.py`), so a change to the normalisation silently changes which chunks count as duplicates. It has no tests.

The impact is regression risk in duplicate-chunk identification: an untested normalization change can silently alter which chunks share a hash.

### User Flow

*Not applicable: this is a unit-test-only change and does not alter any runtime user flow.*

### Error Paths

No production error behavior is being added or changed. The test suite must cover the edge cases specified below, including empty, whitespace-only, and non-ASCII string input.

### Acceptance Criteria

* Given the same text on repeated calls, when `compute_hash` is called, then it returns the same digest each time.
* Given a string input, when `compute_hash` returns, then the result is the SHA-256 digest represented as exactly 64 lower-case hexadecimal characters.
* Given two texts differing only in letter case, when each is hashed, then their hashes are equal.
* Given two texts differing only in leading or trailing whitespace, when each is hashed, then their hashes are equal.
* Given two texts differing only in the amount or kind of whitespace between words—including spaces, tabs, and newlines—when each is hashed, then their hashes are equal.
* Given two texts differing in a word, when each is hashed, then their hashes are different.
* Given two texts differing in punctuation, when each is hashed, then their hashes are different.
* Given an empty string and a whitespace-only string, when each is hashed, then both return the SHA-256 hex digest of the empty string.
* Given non-ASCII text such as `"Café"`, when it is hashed, then hashing succeeds and the returned value matches the SHA-256 digest of its normalized UTF-8 text.
* `pytest tests/unit/test_chunk_hasher.py` passes.
* The new tests import nothing outside the standard library, `pytest`, and `ingestion.chunking.chunk_hasher`.

### Existing System Behaviour

`ingestion/chunking/chunk_hasher.py` currently normalizes with `re.sub(r"\s+", " ", text).strip().lower()`, UTF-8 encodes the normalized text, and returns `hashlib.sha256(...).hexdigest()`.

`ingestion/chunking/semantic_chunker.py` and `ingestion/chunking/entity_preserving_chunker.py` both call `compute_hash` when creating chunks. No existing test file targets `chunk_hasher`.

### Scope Boundaries

* Add `tests/unit/test_chunk_hasher.py` in the style of the existing Python tests under `tests/unit/`.
* Do not change `ingestion/chunking/chunk_hasher.py` or either consuming chunker.
* Test the public `compute_hash(text: str)` contract; unsupported non-string inputs are outside scope.
* Do not add dependencies beyond the standard library, `pytest`, and the module under test.
* *Migration and data rollback are not applicable: this change adds tests only and touches no runtime state or schema. Reverting the added test file restores the prior repository state.*

### Reference Documents

* `ingestion/chunking/chunk_hasher.py`
* `ingestion/chunking/semantic_chunker.py`
* `ingestion/chunking/entity_preserving_chunker.py`
* `tests/unit/test_bulk_ingestion.py`
* `tests/unit/test_researcher_role.py`
* `tests/unit/test_dicom_parser.py`
* `.claude/rules/testing-standards.md`
* `.claude/rules/backend-testing.md`

No relevant `code-wiki` feature page or project-wiki request/decision was found in the checkout.

### Round log

* Round 1, aligned: classified as test-focused tech debt; verified the implementation, consumers, missing direct tests, and existing unit-test conventions; made the test-only scope, impact, non-ASCII assertion, and non-applicable migration explicit.

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
