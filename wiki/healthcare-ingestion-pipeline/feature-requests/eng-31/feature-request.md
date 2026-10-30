---
title: "Accept Markdown (.md) uploads as plain text"
slug: eng-31
status: active
last_updated: 2026-10-30
linear_issue: "https://linear.app/flightdecktest-2/issue/ENG-31/accept-markdown-md-uploads-as-plain-text"
proposed_by: agent
identity_confirmed: false
---

## Current State

Requested in [ENG-31](https://linear.app/flightdecktest-2/issue/ENG-31/accept-markdown-md-uploads-as-plain-text). Alignment agreed the spec under Requirements, as the ticket said when alignment agreed it.

## Key Facts

Nothing recorded yet.

## Requirements

Clinicians export their notes as `.md` files. Today the pipeline refuses them. `detect_doc_type` in `ingestion/parsers/doc_type_detector.py` raises for `.md`, and `DocumentValidator` in `ingestion/validator.py` rejects the extension, so bulk ingest turns the file away.

A Markdown file should be ingested the same way a `.txt` file is.

### Out of scope

* Rendering or parsing the Markdown structure. It is read as plain text.
* The `.markdown` extension.

### Summary

Work-Type: Feature

Add case-insensitive `.md` support using the existing plain-text ingestion path. Enable Markdown selection in the single-upload UI only; retain bulk backend support without changing the bulk-upload UI.

### Context

Clinicians export notes as Markdown files, but the detector and bulk validator currently reject that extension. The existing text parser can handle the content without a Markdown-specific parser.

The reply to round 1 selected single-upload UI support only and delegated the unsupported-extension error-message scope. Use the minimal existing-message change: add `.md` to the detector's accepted-extension list and preserve the validator's rejection wording.

### User Flow

A clinician selects a `.md` document on the single-upload page (`ui/upload_page.py`) and submits it through the existing upload action. Subject to the same validation and ingestion rules as a `.txt` document on that path, it is accepted and routed to the existing text parser.

A caller can also submit `.md` through bulk backend ingestion. Subject to the same bulk validation and ingestion rules as `.txt`, it is accepted and routed to the existing text parser. The bulk-upload UI file picker remains unchanged and does not offer `.md` selection.

### Error Paths

The rule that `.md` behaves like `.txt` preserves the existing validation safeguards of each ingestion path, including empty-file, size-limit, executable-header, and applicable MIME checks. Non-empty content alone does not bypass these checks.

Unsupported extensions remain rejected, including `.markdown` in the detector and bulk validator. The detector's unsupported-extension exception lists `.md` among accepted extensions. The validator's unsupported-type rejection reason retains its existing wording and need not list accepted extensions.

### Acceptance Criteria

* `detect_doc_type("notes.md")` returns `"text"`, and so does `detect_doc_type("NOTES.MD")`.
* `DocumentValidator().validate("notes.md", <non-empty bytes>)` returns `(True, "")` when the bytes pass the existing `.txt` safety and size checks. The same applies to an uppercase `.MD` suffix.
* The detector's unsupported-extension exception names `.md` among accepted extensions. The validator's unsupported-type rejection wording remains unchanged.
* The single-upload UI (`ui/upload_page.py`) allows `.md` selection and submission through its existing ingestion flow, including uppercase `.MD` consistently with case-insensitive support.
* The bulk-upload UI (`ui/bulk_upload_page.py`) file-picker filter remains unchanged and excludes `.md`; bulk backend validation nevertheless accepts `.md` as specified above.
* Markdown content uses the existing plain-text parsing behavior rather than Markdown-aware rendering or parsing. Existing downstream processing remains unchanged.
* Empty, oversized, or executable-header `.md` files receive the same rejection treatment as equivalent `.txt` files on the applicable ingestion path.
* `.markdown` remains unsupported by the detector and bulk validator.
* Unit tests cover detector routing, validator acceptance, and the detector's accepted-extension error list. Verify the stated UI behavior and regression boundaries.

### Existing System Behaviour

* `ingestion/parsers/doc_type_detector.py:detect_doc_type` lowercases the suffix, returns `"text"` for `.txt` and `.text`, and raises `ValueError` for `.md`. Its unsupported-extension exception lists accepted extensions.
* `ingestion/validator.py:DocumentValidator.validate` lowercases the suffix and rejects `.md` through `SUPPORTED_EXTENSIONS`. Its unsupported-type reason does not currently list accepted extensions.
* `app/main.py:_process_single_upload_bytes` calls `DocumentValidator.validate` before uploading and enqueueing a document.
* The single-upload UI calls `app/main.py:ingest_document`, which uses `ingestion/validator.py:validate_file` for size, executable-header, and MIME checks rather than the bulk extension allow-list.
* `workers/parser_worker.py:ParserWorker.process` routes text documents to `parse_text_file`, which reads UTF-8 with replacement for decoding errors and strips surrounding whitespace.
* `ui/upload_page.py` and `ui/bulk_upload_page.py` have file-picker extension filters that currently exclude `.md`.

### Scope Boundaries

Include case-insensitive `.md` detection, bulk validation support, single-upload UI selection, and coverage for the stated acceptance criteria. Reuse the `.txt` parsing path and retain the existing safeguards and downstream processing of each entry point.

Do not enable `.md` in the bulk-upload UI. Do not change the validator's unsupported-type rejection wording. Update the detector's existing accepted-extension error list to include `.md`.

Rendering or parsing Markdown structure and supporting `.markdown` are out of scope. Existing downstream Markdown formatting is not changed by this work.

Migration and rollback: *Not applicable: this adds an extension to ingestion handling and a UI file-picker filter without changing a schema or transforming stored data.*

### Reference Documents

* `code-wiki/healthcare-ingestion-pipeline/Features/Feat-0003-document-ingestion-parsing/Index.md`
* `ingestion/parsers/doc_type_detector.py`
* `ingestion/validator.py`
* `app/main.py`
* `workers/parser_worker.py`
* `ingestion/parsers/text_parser.py`
* `tests/unit/test_dicom_parser.py`
* `tests/unit/test_bulk_ingestion.py`
* `ui/upload_page.py`
* `ui/bulk_upload_page.py`

### Round log

* Round 1, questions: verified both rejection points and the existing text-parser path; clarified inherited validation safeguards; UI coverage and error-message scope remain open.
* Round 2, aligned: incorporated single-upload-only UI support while retaining bulk backend support; resolved delegated error-message scope to the detector's accepted-extension list only; confirmed the distinct single and bulk validation paths.

## Business Rules

Nothing recorded yet.

## Decisions

| Date | Title | Type | Ticket |
|---|---|---|---|

## Evidence

Nothing recorded yet.

## Open Questions

- Is this the right name and boundary for this work? Keep the folder name `eng-31`: a later alignment of ENG-31 updates the page there. Set `identity_confirmed: true` once a person has answered this, and delete the question only after it is answered.

**Resolved:**

Nothing recorded yet.

## Risks / Rejected Approaches

Nothing recorded yet.

## Relationships

**Depends On:** Nothing recorded yet.

**Related:** Nothing recorded yet.
