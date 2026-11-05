---
title: "Log how many stuck documents run.py re-queued at startup"
slug: eng-36
status: active
last_updated: 2026-11-05
linear_issue: "https://linear.app/flightdecktest-2/issue/ENG-36/log-how-many-stuck-documents-runpy-re-queued-at-startup"
proposed_by: agent
identity_confirmed: false
---

## Current State

Requested in [ENG-36](https://linear.app/flightdecktest-2/issue/ENG-36/log-how-many-stuck-documents-runpy-re-queued-at-startup). Alignment agreed the spec under Requirements, as the ticket said when alignment agreed it.

## Key Facts

Nothing recorded yet.

## Requirements

When `python run.py` starts, `recover_stuck_docs()` re-queues the documents left in `PII_PROCESSED` or `EXTRACTED`. It logs how many it found, one line for each document it re-queues, and a warning for each one it skips because its redacted file is missing. It never logs a total of what it actually re-queued, and it logs nothing at all when no document was stuck. So you can't tell at a glance what recovery did.

After recovery, log one INFO line from the `run` logger, worded exactly as in this screenshot: the total, then the count for each status.

![a1-recovery-summary.png](https://uploads.linear.app/d402bfdb-a36b-4c11-ac08-a21a9725b10f/4c542718-8a0a-45d4-93bc-f0c44c694361/f8048c1d-bc5a-4771-8c5b-4594878c4ee9)

The line for when nothing is stuck is in the comments.

Decisions:

* Keep every existing recovery line: the found count, the line for each document and the missing-file warning. The summary is added after them, as the last recovery line, and replaces nothing.
* Count only the documents that were actually re-queued. A document skipped because its redacted file is missing is not counted. Each document counts once, under its status, even when it goes to two queues.
* When no document was re-queued, log the line from the comment's screenshot. That covers both cases: nothing was stuck, or every stuck document was skipped.

Test ticket for RHYTHM-248 (screenshots reaching the stations): the exact wording is only in the screenshots, on purpose.

### Summary

Work-Type: Feature

Add one recovery-summary INFO record from the `run` logger when startup recovery completes, reporting actual re-queued document counts or explicitly reporting that nothing was re-queued.

### Context

Operators cannot currently determine the aggregate recovery outcome at a glance. This is an additive logging change, not a change to which documents recovery finds, skips, or queues.

### User Flow

An operator starts `python run.py`, with its existing command-line options. Startup runs `recover_stuck_docs()`. After existing recovery messages, the operator sees exactly one summary record before startup proceeds to optional seeding.

### Error Paths

Documents with missing redacted files retain their existing warning and are excluded from all summary counts. If every candidate is skipped, use the same zero-result message as when no candidates exist. Existing exception propagation and session cleanup are unchanged; this change does not introduce recovery from database or queue exceptions.

### Acceptance Criteria

1. GIVEN recovery completes with at least one document actually re-queued, WHEN its summary is emitted, THEN exactly one INFO record from logger `run` has message `Recovery summary: {total} re-queued (PII_PROCESSED: {pii_count}, EXTRACTED: {extracted_count})`, with integer counts substituted and statuses in that order.
2. GIVEN two `PII_PROCESSED` documents and one `EXTRACTED` document are successfully re-queued, THEN the exact message is `Recovery summary: 3 re-queued (PII_PROCESSED: 2, EXTRACTED: 1)`.
3. GIVEN a document is skipped because its redacted file is missing, THEN it contributes to neither the total nor either status count, and its existing warning remains.
4. GIVEN an `EXTRACTED` document is re-queued to both embedding and keyword queues, THEN it contributes exactly one to `EXTRACTED` and exactly one to the total. Counts use the status under which recovery routes the document, not subsequent worker status changes.
5. GIVEN recovery completes with zero documents actually re-queued, THEN emit exactly `Recovery summary: nothing to re-queue`. Cover both an empty candidate set and a nonempty candidate set where all documents are skipped.
6. GIVEN a positive total with one status count equal to zero, THEN retain both status fields in the positive-result format, including the zero count.
7. Preserve all existing found-count, per-document re-queue, and missing-file-warning messages. Emit the summary after them as the last recovery record; do not replace any existing message.
8. Verify positive mixed counts, single-status counts, mixed successful/skipped documents, all-skipped documents, and no candidates. Recovery queue destinations and payloads remain unchanged.

### Existing System Behaviour

`run.py:33` creates logger `run`. `recover_stuck_docs()` queries `PII_PROCESSED` and `EXTRACTED` documents, returns without logging when the query is empty, logs the found count otherwise, and skips documents whose local redacted file is absent. It routes `PII_PROCESSED` to extraction and `EXTRACTED` to embedding plus keyword indexing, logging each successful document. It has no aggregate re-queued count. `main()` calls recovery after starting workers and before optional seeding.

### Scope Boundaries

Only add the recovery summary, its counting, and tests. Preserve recovery selection, queue destinations, payloads, existing messages, logging configuration, exception behavior, and startup sequencing. The screenshots' surrounding startup/seeding lines provide context, not requirements to rename existing messages or change timestamp formatting. No schema, storage, worker, UI, or recovery-policy changes are required.

### Reference Documents

* Description image, `a1-recovery-summary.png`: the original embedded link above. Successfully viewed. A dark terminal-style panel titled `python run.py (expected output)` has three timestamped rows: `run INFO Starting workers...`, a green `run INFO Recovery summary: 3 re-queued (PII_PROCESSED: 2, EXTRACTED: 1)`, and `run INFO Seeding 20 records`. The summary demonstrates a positive total and both status counts; it is expected output, not evidence of existing behavior.
* Comment \[2\] by [sanidhya.gupta@kickdrumtech.com](<mailto:sanidhya.gupta@kickdrumtech.com>), `a2-recovery-nothing.png`: [https://uploads.linear.app/d402bfdb-a36b-4c11-ac08-a21a9725b10f/f89d2381-558d-45a8-80bf-c619125f689f/fd3f8dc6-e567-403e-8e17-1a6652765f13](<https://uploads.linear.app/d402bfdb-a36b-4c11-ac08-a21a9725b10f/f89d2381-558d-45a8-80bf-c619125f689f/fd3f8dc6-e567-403e-8e17-1a6652765f13>). Successfully viewed. A dark terminal-style panel titled `python run.py (expected output when nothing is stuck)` has two timestamped rows: `run INFO Starting workers...` and a green `run INFO Recovery summary: nothing to re-queue`. This fixes the exact zero-result wording.
* `run.py:36–91` — current recovery implementation; `run.py:117–123` — startup placement.
* `code-wiki/healthcare-ingestion-pipeline/Architecture/Overview.md` — process-local queues and startup recovery purpose.

### Round log

* Round 1, rejected: prior judgment identified a contradiction in the earlier silent-recovery premise, as recorded in comment \[7\].
* Round 2, aligned: verified the corrected description against source, read both screenshots, and recorded exact message wording, actual-document counting, zero-result behavior, preservation of existing logs, and scope boundaries.

## Business Rules

Nothing recorded yet.

## Decisions

| Date | Title | Type | Ticket |
|---|---|---|---|

## Evidence

Nothing recorded yet.

## Open Questions

- Is this the right name and boundary for this work? Keep the folder name `eng-36`: a later alignment of ENG-36 updates the page there. Set `identity_confirmed: true` once a person has answered this, and delete the question only after it is answered.

**Resolved:**

Nothing recorded yet.

## Risks / Rejected Approaches

Nothing recorded yet.

## Relationships

**Depends On:** Nothing recorded yet.

**Related:** Nothing recorded yet.
