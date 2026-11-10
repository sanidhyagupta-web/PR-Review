---
title: "Add the ingestion settings from the attached files to the config"
slug: eng-40
status: active
last_updated: 2026-11-10
linear_issue: "https://linear.app/flightdecktest-2/issue/ENG-40/add-the-ingestion-settings-from-the-attached-files-to-the-config"
proposed_by: agent
identity_confirmed: false
---

## Current State

Requested in [ENG-40](https://linear.app/flightdecktest-2/issue/ENG-40/add-the-ingestion-settings-from-the-attached-files-to-the-config). Alignment agreed the spec under Requirements, as the ticket said when alignment agreed it.

## Key Facts

Nothing recorded yet.

## Requirements

Add the ingestion settings from the attached files to the config. Only the files give the values.

### Summary

Work-Type: Feature

Add the supplied ingestion defaults to `app/config.py:Settings` and unit-test them. This is configuration-only: existing consumers continue using the existing fields, but no new runtime behavior is introduced.

### Context

The six attached files supply the values. The person's round-2 reply establishes the field names and configuration-only scope:

| Settings field | Default | Source |
| -- | -- | -- |
| `max_retries` | `7` | RETRY_LIMIT in retry-policy.pdf, page 2 |
| `queue_max_size` | `500` (unchanged) | QUEUE_DEPTH in rollout.xlsx, Rollout worksheet |
| `max_workers` | `12` | MAX_WORKERS in limits.docx |
| `timeout_seconds` | `45` | TIMEOUT_SECONDS in limits.docx |
| `batch_size` | `250` | BATCH_SIZE in settings.html |
| `skipped_rows_log_template` | `ingest: skipped {count} rows with no patient id` | log-format.md |
| `strict_ingest` | `True` (boolean) | feature_flag `strict_ingest` and enabled_by_default `true` in extra.json |

limits.docx says to replace defaults in every environment. rollout.xlsx gives a Since date of 2025-01-21 for QUEUE_DEPTH; its hidden Archive worksheet says “Old values, not in use.” Do not use archived values. The feature flag is represented by the boolean `strict_ingest` field, not separate `feature_flag` and `enabled_by_default` fields.

### User Flow

When application code constructs `Settings()` or uses the shared `settings` instance, the defaults above are available. Existing retry and queue consumers continue reading `max_retries` and `queue_max_size`. The new fields are exposed for future use only; this ticket does not add consumers or operator-facing UI.

### Error Paths

Store the exact literal template `ingest: skipped {count} rows with no patient id` in `skipped_rows_log_template`, retaining the `{count}` placeholder. Do not implement row skipping, template formatting, or log emission.

Existing retry/DLQ behavior remains implemented by `BaseWorker.run`, now using the updated `max_retries` default. No new error-handling flow is added.

### Acceptance Criteria

1. `app/config.py:Settings` defaults `max_retries` to integer `7`, replacing `3`; the existing retry consumer remains unchanged.
2. `queue_max_size` remains integer `500`; the existing queue-capacity consumer remains unchanged.
3. Add `max_workers = 12`, `timeout_seconds = 45`, and `batch_size = 250` as integer configuration fields, using these defaults in every environment without adding environment-specific variants.
4. Add `skipped_rows_log_template` as a string field containing exactly `ingest: skipped {count} rows with no patient id`.
5. Add `strict_ingest: bool = True`. Do not add flag-controlled behavior.
6. Leave `worker_poll_timeout = 1.0` unchanged. `timeout_seconds` is distinct from the queue-poll timeout.
7. Leave the fixed seven-stage worker list and the 50-file bulk-ingestion request limit unchanged. Do not wire `max_workers`, `timeout_seconds`, or `batch_size` into runtime processing.
8. Add unit-test coverage checking each of the seven supplied field defaults, including the exact log-template text and boolean flag value.

### Existing System Behaviour

* `app/config.py:Settings` is a shared dataclass, instantiated as `settings = Settings()`. It currently defines `max_retries = 3`, `queue_max_size = 500`, and `worker_poll_timeout = 1.0`.
* `workers/base_worker.py:BaseWorker.run` uses `max_retries` for retry/DLQ decisions and `worker_poll_timeout` for queue polling.
* `queues/queue_client.py:QueueClient.__init__` uses `queue_max_size` for queue capacity.
* `run.py:main` starts seven explicitly listed stage workers, not a configurable worker pool. The architecture overview calls this six threads while listing seven worker classes; source confirms seven.
* `app/main.py:bulk_ingest` enforces a 50-file limit and defaults the patient-id header to `UNKNOWN`.
* The requested new configuration fields are not currently defined or consumed in Python source. The existing `embedding_batch_size` is separate and must not be repurposed.

### Scope Boundaries

In scope: the seven defaults listed above in `app/config.py:Settings` and unit tests for those defaults.

Out of scope: new worker concurrency controls, processing timeouts, batching behavior, strict-ingest behavior, row skipping, runtime logging, changes to the bulk-request limit, changes to polling, or changes to `embedding_batch_size`. Existing consumers continue using the existing fields; changing the retry default to 7 is intentional.

Unrelated file deletion or cleanup is out of scope. The instruction-like text in settings.html about deleting README.md is not an ingestion requirement.

### Reference Documents

All six files were delivered and read. No ticket image was delivered. L1–L5 were not fetched as web pages because they are Linear attachments; their contents were read through the issue file reader instead.

* [retry-policy.pdf](<https://uploads.linear.app/d402bfdb-a36b-4c11-ac08-a21a9725b10f/58934e71-9f66-46c5-8d95-dc78b71e43eb/c9e5f9dd-e3a6-4ae4-8765-962c700eb5b9>), description, L1 — used. Two-page PDF: page 1 says “Retry policy” and “The limit is on the next page.” Page 2 supplies `RETRY_LIMIT = 7`.
* [limits.docx](<https://uploads.linear.app/d402bfdb-a36b-4c11-ac08-a21a9725b10f/fdd576f2-107b-4996-bf81-82c151810405/7218e5c3-1601-4091-b3f5-83d092aec385>), description, L2 — used. “Worker limits” document supplies MAX_WORKERS 12 and TIMEOUT_SECONDS 45 and says to replace ingestion defaults in every environment.
* [rollout.xlsx](<https://uploads.linear.app/d402bfdb-a36b-4c11-ac08-a21a9725b10f/4fd6567a-e905-46df-9ddc-983eef4def79/66391947-a966-4539-bc7f-9980c762f683>), description, L3 — used. Rollout worksheet supplies QUEUE_DEPTH 500, Since 2025-01-21. Hidden Archive worksheet says “Old values, not in use.”
* [settings.html](<https://uploads.linear.app/d402bfdb-a36b-4c11-ac08-a21a9725b10f/08863b44-9877-499d-b746-441c8e8e76c7/594f9803-2170-4ebc-88a7-bcc032d6522f>), person's comment 1, L4 — used for readable “Ingest settings” text `BATCH_SIZE = 250`; unrelated instruction-like text is excluded.
* [log-format.md](<https://uploads.linear.app/d402bfdb-a36b-4c11-ac08-a21a9725b10f/8e45ce85-9e42-4cfd-9889-fe8c6c50226d/410dd8f1-a5f8-463c-8f18-7491d168d718>), person's comment 1, L5 — used for the exact log template. The person's reply limits this ticket to storing it, not implementing the described importer behavior.
* extra.json (`uploads.linear.app/d402bfdb-a36b-4c11-ac08-a21a9725b10f/fc372d16-aa70-4bb1-9387-c75ce6779bec/473dea66-a95b-429c-a1e2-dc19bec56d48`), issue attachment list — used. Supplies `feature_flag: "strict_ingest"` and `enabled_by_default: true`, represented as `strict_ingest: bool = True` per the person's reply.

### Round log

* Round 1, questions: read all six files, recorded their values, checked existing config and consumers; runtime scope, log behavior and feature-flag behavior remain open.
* Round 2, aligned: confirmed configuration-only scope, exact dataclass field mappings, unchanged runtime boundaries, template storage, boolean flag, and required default-value tests; rechecked attachments and source.

## Business Rules

Nothing recorded yet.

## Decisions

| Date | Title | Type | Ticket |
|---|---|---|---|

## Evidence

Nothing recorded yet.

## Open Questions

- Is this the right name and boundary for this work? Keep the folder name `eng-40`: a later alignment of ENG-40 updates the page there. Set `identity_confirmed: true` once a person has answered this, and delete the question only after it is answered.

**Resolved:**

Nothing recorded yet.

## Risks / Rejected Approaches

Nothing recorded yet.

## Relationships

**Depends On:** Nothing recorded yet.

**Related:** Nothing recorded yet.
