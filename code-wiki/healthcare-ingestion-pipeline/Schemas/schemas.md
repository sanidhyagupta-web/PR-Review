# Schemas — Healthcare Ingestion Pipeline

Canonical, whole-codebase entity catalog. This project has **no migration tool** (no
Alembic/Flyway) — schema is created at process startup via SQLAlchemy's
`Base.metadata.create_all()` (`db/database.py`). So **the SQLAlchemy model definitions in
`db/models.py` are the schema source of truth**, in place of the usual "the migration wins"
rule.

Three relational tables (`db/models.py`), plus four non-relational "schema-like" shapes that
this pipeline treats as persisted contracts even though they live in JSON files or vector/keyword
index metadata rather than SQL tables.

---

## `document_registry`

Owner: [Feat-0003 — Document Ingestion & Parsing](../Features/Feat-0003-document-ingestion-parsing/Index.md)

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `doc_id` | string | not null | — | **Primary key** |
| `original_filename` | string | not null | — | |
| `raw_path` | string | not null | — | `s3://…` URI |
| `file_type` | string | null | — | `typed_pdf`, `scanned_pdf`, `text` |
| `status` | string | not null | — | `DocStatus` value — see the state machine on Feat-0003. **No `CHECK` constraint**; validity is enforced only in application code (`ingestion/state_machine.py:can_transition()`) |
| `retry_count` | integer | null | `0` | |
| `error_message` | text | null | — | |
| `uploader_id` | string | null | — | |
| `created_at` | datetime | null | `utcnow` | |
| `updated_at` | datetime | null | `utcnow`, on-update `utcnow` | |
| `doc_metadata` | JSON | null | `{}` | |

Constraints: `doc_id` primary key. No `UNIQUE` on `original_filename` — duplicate detection
(`ingestion/registry.py:is_duplicate_document()`) is an application-level query filtered by
status, not a database constraint.

---

## `chunk_registry`

Owner: [Feat-0002 — Chunking, Embedding & Indexing](../Features/Feat-0002-chunking-embedding-indexing/Index.md)

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `chunk_id` | string | not null | — | **Primary key** |
| `doc_id` | string | not null | — | Logically references `document_registry.doc_id` — **no `FOREIGN KEY` constraint defined** |
| `chunk_hash` | string | not null | — | **`UNIQUE`** — the sole enforcement point for chunk deduplication |
| `chunk_index` | integer | null | — | |
| `parent_chunk_id` | string | null | — | hierarchical chunking |
| `section` | string | null | — | |
| `page_number` | integer | null | `0` | |
| `is_redacted` | integer | null | `0` | 0/1 flag, set by [Feat-0004](../Features/Feat-0004-pii-detection-redaction-rbac/Index.md)'s `PiiWorker` |
| `created_at` | datetime | null | `utcnow` | |

Constraints: `chunk_id` primary key; `chunk_hash` unique.

---

## `audit_log`

Owner: **contested** — written by [Feat-0003](../Features/Feat-0003-document-ingestion-parsing/Index.md), [Feat-0004](../Features/Feat-0004-pii-detection-redaction-rbac/Index.md), [Feat-0006](../Features/Feat-0006-structured-data-extraction-ade/Index.md), [Feat-0007](../Features/Feat-0007-healthcare-search-ui/Index.md), and read by [Feat-0001](../Features/Feat-0001-auth-encryption-audit/Index.md) (`security/audit_logger.py` owns the read/write API, but does not own the events written into it)

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | integer | not null | autoincrement | **Primary key** |
| `event_type` | string | not null | — | e.g. `DOCUMENT_INGESTED`, `VALIDATION_FAILED`, `BULK_INGEST_SUBMITTED`, `PII_PROCESSED`, `SEARCH`, `RATE_LIMITED`, `GUARDRAIL_BLOCKED` |
| `user_id` | string | null | — | defaults to `"system"` at the call site if not supplied |
| `doc_id` | string | null | — | Logically references `document_registry.doc_id` — **no `FOREIGN KEY` constraint defined** |
| `query` | text | null | — | **Stores the caller's raw search query in plaintext** — see Feat-0001's Known Error Scenarios / open questions; this is a HIPAA-relevant exposure since queries may contain patient names or conditions |
| `details` | JSON | null | — | |
| `timestamp` | datetime | null | `utcnow` | |

Constraints: `id` primary key. **No constraints of any kind on the other columns** — no
`NOT NULL` beyond `event_type`, no `CHECK`, no `FOREIGN KEY`.

---

## `chunk_metadata` (non-relational — Chroma / keyword-index document metadata)

Owner: [Feat-0002 — Chunking, Embedding & Indexing](../Features/Feat-0002-chunking-embedding-indexing/Index.md); the `allowed_roles` field is stamped by [Feat-0004](../Features/Feat-0004-pii-detection-redaction-rbac/Index.md)

Source: `ingestion/metadata/metadata_builder.py` (and a duplicated inline copy of the same
logic in `workers/pii_worker.py:62-73` — see Feat-0004's open questions).

| Field | Type | Notes |
|---|---|---|
| `patient_id` | string | |
| `doc_id` | string | |
| `chunk_id` | string | |
| `source_file` | string | |
| `source_page` | int | |
| `source_section` | string | |
| `chunk_index` | int | |
| `parent_chunk_id` | string, nullable | |
| `department` | string | one of `general`, `cardiology`, `billing`, `radiology`, `oncology` |
| `allowed_roles` | list[string] | **the access-control primitive checked by `security/access_control.py:filter_results_by_role()`** — see [Feat-0005](../Features/Feat-0005-search-rag-query/Index.md) |
| `entity_types` | list[string] | PII entity types found in the chunk at ingest time; consumed by `ingestion/pii/role_based_masking.py:apply_role_mask()` (defined but not currently called in the live query path — Feat-0005 Known Error Scenarios) |

`indexing/index_schema.py` defines `REQUIRED_METADATA_FIELDS` and a `validate_metadata()`
function for this shape, but no call site was found for `validate_metadata()` — validation is
effectively unenforced (open question, carried on Feat-0002).

---

## `pii_entity_index` / `pii_doc_index` (non-relational — JSON files)

Owner: [Feat-0004 — PII Detection, Redaction & RBAC Tagging](../Features/Feat-0004-pii-detection-redaction-rbac/Index.md)

Source: `indexing/pii_entity_index.py`. Persisted as runtime caches, not permanent schema —
regenerated as documents are ingested:

- `data/pii_entity_index.json` — `{ SHA256(entity_type:entity_value): [chunk_id, ...] }`. Hashes
  only; no plaintext PII is stored here.
- `data/pii_doc_index.json` — `{ "doc_chunks": {doc_id: [chunk_id, ...]}, "chunk_doc": {chunk_id: doc_id} }`,
  used to expand a `PERSON`/`PATIENT_NAME` hash hit to every chunk in the same document (Top-D
  candidate generation for RAG).

---

## Cross-Feature Foreign Keys

None of the relationships below are enforced by a database constraint — all are
**implicit / application-level only**. This is itself a finding, not just a gap: referential
integrity between `document_registry`, `chunk_registry`, and `audit_log` depends entirely on
every writer getting it right.

| Reference | Owners | Enforced? |
|---|---|---|
| `chunk_registry.doc_id` → `document_registry.doc_id` | Feat-0002 → Feat-0003 | **No** — no `FOREIGN KEY` |
| `audit_log.doc_id` → `document_registry.doc_id` | contested → Feat-0003 | **No** — no `FOREIGN KEY` |

## Definition Drift

- `document_registry.status` — valid values (the `DocStatus` enum) are enforced only by
  `ingestion/state_machine.py:can_transition()` in application code; the database column is a
  bare `string` with no `CHECK` constraint. A direct SQL write (or a future code path that
  bypasses `ingestion/registry.py:update_status()`) could set an invalid status with nothing
  to stop it.
- `chunk_registry.doc_id` / `audit_log.doc_id` — declared `nullable=False`/implicit in the
  SQLAlchemy model but neither is backed by a `FOREIGN KEY`, so an orphaned chunk or audit row
  (referencing a `doc_id` that was never inserted, or was later removed) is not something the
  database can reject.

## Gaps

- No migration tool of any kind is used in this project; schema evolution has no versioning
  path beyond editing `db/models.py` and relying on `create_all()`, which does not alter
  existing tables. *Open question: how would an existing SQLite file be migrated if a column
  were added or renamed?*
- `indexing/index_schema.py:validate_metadata()` is defined but no call site was found —
  *open question: is chunk-metadata validation intended to run somewhere, or is this dead code?*
