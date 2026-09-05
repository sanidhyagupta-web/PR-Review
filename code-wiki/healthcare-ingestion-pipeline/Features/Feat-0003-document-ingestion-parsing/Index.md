---
feat_id: Feat-0003
feature: document-ingestion-parsing
type: backend-service
domain: document-ingestion
criticality: high
touched_paths:
  - app/main.py
  - app/config.py
  - app/dependencies.py
  - ingestion/validator.py
  - ingestion/registry.py
  - ingestion/state_machine.py
  - ingestion/watcher.py
  - ingestion/parsers/
  - ingestion/markdown/
  - ingestion/ocr/
  - workers/base_worker.py
  - workers/parser_worker.py
  - workers/markdown_worker.py
  - storage/s3_client.py
  - queues/
depends_on: [Feat-0004, Feat-0001]
consumed_by: [Feat-0002, Feat-0007]
implements: []
tags: [ingestion, pipeline-entrypoint, pdf, dicom, ocr]
---

## Overview

| Type | Package | Path | Domain | Last updated |
|---|---|---|---|---|
| backend-service | (none — plain Python module tree) | `app/`, `ingestion/`, `workers/{base,parser,markdown}_worker.py`, `storage/`, `queues/` | document-ingestion | 2026-09-05 |

## Domain Purpose

The front door of the pipeline: accepts a healthcare document (PDF, DICOM, or plain text),
validates it's safe and well-formed, stores the raw bytes encrypted in S3, and converts it
through parsing and markdown formatting so downstream stages (PII redaction, chunking) receive
clean, structured text instead of raw file bytes.

## Entities Owned

| Entity | Represents |
|---|---|
| [`document_registry`](../../Schemas/schemas.md#document_registry) | One row per uploaded document — identity, storage location, and lifecycle status |

## Status / State Machine

`DocStatus` (`ingestion/state_machine.py`) governs every document's lifecycle across the *whole*
pipeline, not just this feature — reproduced here since this feature owns the registry and the
first several transitions:

| Status | Can Transition To | Trigger |
|---|---|---|
| UPLOADED | VALIDATED, FAILED | validator passes/fails |
| VALIDATED | PARSING, FAILED | ParserWorker picks up message |
| PARSING | PARSED, FAILED | parse succeeds/throws |
| PARSED | MARKDOWN_READY, FAILED | MarkdownWorker succeeds/throws |
| MARKDOWN_READY | CHUNKED, FAILED | (owned by Feat-0002 from here on) |
| CHUNKED | PII_PROCESSED, DUPLICATE, FAILED | — |
| PII_PROCESSED | EXTRACTED, FAILED | — |
| EXTRACTED | EMBEDDED, FAILED | — |
| EMBEDDED | INDEXED, FAILED | — |
| INDEXED | *(terminal)* | — |
| FAILED | PARSING | manual/automatic retry |
| DUPLICATE | *(terminal)* | — |

All transitions go through `ingestion/registry.py:update_status()`, which is the **sole**
enforcement point — it calls `can_transition()` and raises `RegistryError` on an invalid edge
(`ingestion/state_machine.py:36-37`).

## Invariants

- Document status changes only through `update_status()` — no other write path exists.
- No plaintext document content persists on local disk past the worker step that produced it;
  everything downloaded from S3 is processed in memory/temp and deleted after re-upload.
- S3 objects are always encrypted (KMS if `kms_key_id` configured, else SSE-S3 fallback) —
  `storage/s3_client.py:42-46`.
- After 3 failed retries, a message goes to the DLQ instead of being retried again indefinitely
  (`workers/base_worker.py:32-36`).

## Access Control

**Model**: Role-based — a coarse `role` string, not per-user ownership.

| Action | Access Condition | Enforced In |
|---|---|---|
| `POST /ingest/bulk` | `role` header ∈ {doctor, nurse, admin} | `app/main.py:168` (`ingestion/metadata/rbac_policy.py:get_ingest_allowed_roles()`, owned by Feat-0004) |
| Python `ingest_document()` | none — caller identity is only logged (`uploader_id`), never verified | *(no enforcement — relies on the Streamlit UI's own login gate, Feat-0007)* |

**Critical gap**: `POST /ingest/bulk`'s `role` header is unauthenticated caller input (see
`.claude/rules/security.md`) — the role check is a real code path but not a real security
boundary, since nothing verifies the header wasn't just made up by the caller.

## Business Rules

| ID | Rule | Enforced In | Severity |
|---|---|---|---|
| BR-01 | File extension must be one of `.pdf`, `.txt`, `.text`, `.dcm`; executables (PE/ELF/shebang magic bytes) rejected | `ingestion/validator.py:10-20,55-57,88-90` | CRITICAL |
| BR-02 | File size ≤ 50 MB | `app/config.py:30` | HIGH |
| BR-03 | `.dcm` files must have a valid DICOM preamble/magic bytes | `ingestion/validator.py:59-63`, `ingestion/parsers/doc_type_detector.py:49-58` | HIGH |
| BR-04 | Duplicate filename (non-failed, non-duplicate existing doc) is rejected | `app/main.py:116-117`, `ingestion/registry.py:70-82` | MEDIUM |
| BR-05 | OCR average confidence < 0.40 (configurable) → document FAILED, sent to DLQ | `ingestion/ocr/ocr_quality.py:26-33`, `workers/parser_worker.py:64-78` | HIGH |
| BR-06 | Department must be a known value (`general`/`cardiology`/`billing`/`radiology`/`oncology`) or ingest raises `ValueError` | `ingestion/metadata/rbac_policy.py:21-31` (owned by Feat-0004) | HIGH |
| BR-07 | Only `doctor`/`nurse`/`admin` may submit ingest jobs — see Access Control gap above | `app/main.py:168` | CRITICAL |
| BR-08 | Bulk ingest accepts at most 50 files per request | `app/main.py:171-172` | MEDIUM |

## External Integrations

| System | Trigger | What Happens |
|---|---|---|
| AWS S3 (+ KMS) | every raw/parsed/markdown file write | Encrypted upload; `TokenRetrievalError`/`NoCredentialsError` surfaces as a user-facing "run `aws sso login`" message (`app/main.py:65-69`) |
| Filesystem watcher | polls `watch_dirs` every 5s | `ingestion/watcher.py` auto-calls `ingest_document()` on new files, `uploader_id="watcher"` |
| ParserWorker (async) | `parsing_queue` message | Downloads from S3 → detects type → parses (PyMuPDF/pydicom/text) or OCRs (Claude Vision → Tesseract fallback) → uploads extracted text → `markdown_queue` |
| MarkdownWorker (async) | `markdown_queue` message | Converts extracted text to structured Markdown (heading promotion) → `chunking_queue` (Feat-0002) |

## API Endpoints

| Method | Path | Auth | Who Uses It | Description |
|---|---|---|---|---|
| POST | `/ingest/bulk` | `role` header (unauthenticated, see gap above) | `ui/bulk_upload_page.py` calls the underlying helper directly (in-process); external callers would hit this over HTTP | Accepts up to 50 files, per-file validate/upload/enqueue, returns per-file queued/rejected status |
| *(Python API)* | `ingest_document()` | none | `ui/upload_page.py` (in-process call) | Single-file validate/upload/enqueue |

## Safe vs Dangerous Changes

### Safe
- Adding a new supported file extension to `ingestion/validator.py`'s allow-list, provided a matching parser/OCR path exists.
- Raising/lowering `max_file_size_bytes` or `ocr_confidence_threshold` in `app/config.py`.

### Dangerous — Requires Review
| Change | Risk | Why |
|---|---|---|
| Adding a new `DocStatus` value or transition | Breaks recovery | `run.py:recover_stuck_docs()` hardcodes which statuses are recoverable (`PII_PROCESSED`, `EXTRACTED`) — a new in-flight status won't be recovered after a crash |
| Changing the `role` check on `/ingest/bulk` | Security | This is the *only* authorization gate on ingest — see the unauthenticated-header gap above; don't relax it further without also fixing the auth mechanism |
| Changing queue message shape (`doc_id`, `raw_s3_key`, etc.) | Breaks downstream | Every worker in the chain (Feat-0002, Feat-0004, Feat-0006) expects exact message keys |

### Human Escalation Required
- Any change to how `role` is authenticated on `POST /ingest/bulk` — this is a live security gap in a HIPAA-context system, not a routine code change.

## Known Error Scenarios

| Scenario | Error Returned | Root Cause |
|---|---|---|
| Unsupported/dangerous file | Rejected, reason string | `ingestion/validator.py` extension/magic-byte check |
| Duplicate filename | Rejected, `"Duplicate document"` | `is_duplicate_document()` |
| S3 credentials expired | `ValueError` with `aws sso login` instructions | `TokenRetrievalError`/`NoCredentialsError` (`app/main.py:65-69`) |
| OCR quality too low | Document `FAILED`, sent to DLQ | `avg_confidence < 0.40` |
| Invalid state transition | `RegistryError`, sent to DLQ | `can_transition()` rejects the edge |
| Max retries exceeded | Sent to DLQ | `workers/base_worker.py:32-36` |

## Testing Expectations

- `tests/unit/test_bulk_ingestion.py` covers RBAC (role accept/reject), batch size limits, mixed valid/invalid batches, audit event emission, and exception isolation (one bad file doesn't fail the batch).
- No test coverage found for the `ingest_document()` single-file Python API path, the file watcher, or OCR quality gating — *Open question: are these covered elsewhere or genuinely untested?*

## Forbidden Patterns

- Never write document status directly to the database — always go through `ingestion/registry.py:update_status()`, or the state machine invariant (and DLQ recovery) breaks silently.
- Never treat the `POST /ingest/bulk` `role` header as a trusted identity claim in new code — it isn't authenticated.

## Key Files

- `app/main.py` — HTTP + Python entry points, role check, S3 upload orchestration
- `ingestion/state_machine.py` — `DocStatus` enum and valid-transition graph
- `ingestion/registry.py` — registration, status updates, duplicate check
- `ingestion/validator.py` — extension/size/magic-byte validation
- `workers/base_worker.py` — retry/DLQ base class shared by every worker in the pipeline
- `workers/parser_worker.py`, `workers/markdown_worker.py` — this feature's two async stages
- `storage/s3_client.py` — the single choke-point for all file I/O
- `queues/queue_client.py`, `queues/dlq.py` — in-memory queue + dead-letter handling

## Context Routing

| Feature | Load when |
|---|---|
| Feat-0003 (this file) | Touching upload, validation, parsing, OCR, or the document status state machine |

| Workflow | Sections to load |
|---|---|
| Adding a file type | Business Rules, Safe vs Dangerous Changes, Key Files |
| Debugging a stuck/failed document | Status/State Machine, Known Error Scenarios, Key Files |
| Security review of ingest | Access Control, Business Rules (BR-07), Dangerous Changes |
