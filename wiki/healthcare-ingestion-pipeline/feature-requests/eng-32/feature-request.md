---
title: "Reject a .pdf upload whose bytes are not a PDF"
slug: eng-32
status: active
last_updated: 2026-10-30
linear_issue: "https://linear.app/flightdecktest-2/issue/ENG-32/reject-a-pdf-upload-whose-bytes-are-not-a-pdf"
proposed_by: agent
identity_confirmed: false
---

## Current State

Requested in [ENG-32](https://linear.app/flightdecktest-2/issue/ENG-32/reject-a-pdf-upload-whose-bytes-are-not-a-pdf). Alignment agreed the spec under Requirements, as the ticket said when alignment agreed it.

## Key Facts

Nothing recorded yet.

## Requirements

`DocumentValidator.validate` in `ingestion/validator.py` checks the DICOM magic bytes of a `.dcm` file. It accepts a `.pdf` on its extension alone, though. A renamed text file therefore passes validation, reaches the PDF parser, and only fails later inside the parser worker, where the uploader never sees why.

The validator should check a `.pdf` the way it already checks a `.dcm`.

### Summary

Work-Type: Bug

Reject PDF-named uploads without the `%PDF` prefix in `DocumentValidator.validate`, returning a clear validation reason before downstream parsing. Preserve the existing empty-file, size-limit, and executable rejection precedence and reasons.

### Context

Impact: a non-PDF file renamed to `.pdf` can pass bulk-upload validation and fail asynchronously instead of providing an immediate rejection reason.

Reproduction: call `DocumentValidator().validate("report.pdf", b"ordinary text")`. The current result is `(True, "")`; the requested result is `(False, "PDF magic bytes not found")`.

### User Flow

*Not applicable: this corrects validation within the existing bulk-upload flow rather than introducing a new user flow.*

### Error Paths

For supported PDF filenames, retain this order:

1. Empty content: reject with `"File is empty"`.
2. Content exceeding the configured size limit: reject with the existing `"File exceeds {mb} MB limit"` reason, including when the content starts with `MZ` or lacks `%PDF`.
3. Dangerous executable headers: reject with `"Executable/malicious file type rejected"`.
4. Otherwise, content not starting with `%PDF`: reject with `"PDF magic bytes not found"`.

The existing unsupported-extension check remains unchanged and precedes these checks.

### Acceptance Criteria

* For a filename whose normalized extension is `.pdf`, nonempty, within-limit content that passes executable detection and does not start with the exact bytes `b"%PDF"` returns `(False, "PDF magic bytes not found")`.
* For such a filename, content starting with `b"%PDF"` returns `(True, "")` provided it passes the existing checks. This remains a prefix check, not structural PDF validation.
* Empty `.pdf` content returns `(False, "File is empty")`, not the new PDF-prefix reason.
* Oversized `.pdf` content retains the existing size-limit reason, regardless of whether it starts with `%PDF`, starts with `MZ`, or lacks a recognized prefix.
* Within-limit `MZ` content named `report.pdf` returns `(False, "Executable/malicious file type rejected")`, not the PDF-prefix reason. All existing dangerous-header checks retain precedence over the PDF-prefix check.
* Unit tests cover PDF-prefix acceptance and rejection and the retained empty-file, size-limit, and executable-rejection precedence, including oversized `MZ` content.

### Existing System Behaviour

* `ingestion/validator.py`: `DocumentValidator.validate` normalizes extension case, checks supported extensions, empty content, size, and dangerous headers, then validates DICOM magic bytes. It has no PDF-specific rejection.
* `_PDF_MAGIC = b"%PDF"` already exists in the same module for MIME detection.
* `app/main.py`: `_process_single_upload_bytes` returns validator rejection reasons before upload, registration, or parser queueing.
* `tests/unit/test_bulk_ingestion.py`: `TestDocumentValidator` already covers accepted PDFs, empty PDFs, oversized PDFs, and executable rejection with a text extension.

### Scope Boundaries

The requested change concerns `DocumentValidator.validate` and unit coverage. It is a prefix check, not proof that a PDF is structurally parseable. Preserve existing extension normalization, unsupported-extension handling, empty-file validation, size-limit validation, and dangerous-header detection. No change to DICOM validation, parser behavior, or the separate disk-based `validate_file` API is requested.

### Reference Documents

* `ingestion/validator.py`
* `app/main.py`, `_process_single_upload_bytes`
* `tests/unit/test_bulk_ingestion.py`, `TestDocumentValidator`
* `workers/parser_worker.py`, `ParserWorker.process`
* `ingestion/parsers/pdf_parser.py`, `parse_typed_pdf`
* No code wiki or intent wiki was found in this checkout.

### Round log

* Round 1, questions: verified the validation gap, documented reproduction and scope, and asked whether existing empty-file and size-limit reasons retain precedence.
* Round 2, aligned: confirmed the existing check order against the source and incorporated the reply preserving empty-file, size-limit, and executable rejection precedence; no open requirements remain.

## Business Rules

Nothing recorded yet.

## Decisions

| Date | Title | Type | Ticket |
|---|---|---|---|

## Evidence

Nothing recorded yet.

## Open Questions

- Is this the right name and boundary for this work? Keep the folder name `eng-32`: a later alignment of ENG-32 updates the page there. Set `identity_confirmed: true` once a person has answered this, and delete the question only after it is answered.

**Resolved:**

Nothing recorded yet.

## Risks / Rejected Approaches

Nothing recorded yet.

## Relationships

**Depends On:** Nothing recorded yet.

**Related:** Nothing recorded yet.
