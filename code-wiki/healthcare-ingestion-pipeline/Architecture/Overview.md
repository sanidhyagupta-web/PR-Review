# Architecture Overview — Healthcare Ingestion Pipeline

Last updated: 2026-09-05

## System Topology

A single-process (per deployment) Python monorepo — not a set of independently deployed
microservices. Two runnable entry points share the same codebase and SQLite database:

- **`run.py`** — starts six background worker threads (`ParserWorker` → `MarkdownWorker` →
  `ChunkingWorker` → `PiiWorker` → `ExtractionWorker` → `EmbeddingWorker` + `KeywordIndexWorker`)
  and recovers documents stuck mid-pipeline from a prior crash.
- **`ui/streamlit_app.py`** — the Streamlit web app (`streamlit run ui/streamlit_app.py`); also
  lazily starts the same worker threads on first upload (`_ensure_workers()`), so a single
  Streamlit process can run the whole pipeline standalone.
- **`app/main.py`**'s FastAPI app (`uvicorn app.main:app`) exposes `POST /ingest/bulk` as an
  independent HTTP entry point into the same pipeline.
- **`llm/ade_api.py`**'s FastAPI app (separate `uvicorn` process, port 8001) hosts the local
  MLX-quantized extraction model that `workers/extraction_worker.py` calls over HTTP.

Everything else — parsing, PII redaction, chunking, embedding, indexing, search — runs
in-process as plain function/class calls, connected by six named in-memory queues
(`queues/queue_client.py`), not a message broker. **Queues are process-scoped and lost on
restart**; `run.py:recover_stuck_docs()` exists specifically to re-enqueue documents whose
status shows in-flight work when the last queue state was lost.

## Pipeline Stages (Coupling Graph)

Rendered from the `depends_on`/`consumed_by` frontmatter on each feature — see `Features/index.md`
for the generated table form.

```
Feat-0003 (Document Ingestion & Parsing)
    │  parsing_queue → markdown_queue → chunking_queue
    ▼
Feat-0002 (Chunking, Embedding & Indexing)  ──chunking──┐
    │  pii_queue                                        │
    ▼                                                    │
Feat-0004 (PII Detection, Redaction & RBAC Tagging)      │
    │  extraction_queue                                  │
    ▼                                                    │
Feat-0006 (Structured Data Extraction / ADE)             │
    │  embedding_queue + keyword_queue (fan-out)         │
    └────────────────────────────────────────────────────┘
    ▼
Feat-0002 (embedding/indexing side, same feature as the chunking side above)

Feat-0005 (Search & RAG Query)  ← reads from Feat-0002's indexes, applies Feat-0004's RBAC data
Feat-0001 (Auth, Encryption & Audit)  — consumed by Feat-0003, Feat-0004, Feat-0007 (no dependencies of its own)
Feat-0007 (Healthcare Search UI)  — the only consumer of every other feature; nothing consumes it
```

`Feat-0002` appears at both ends of the pipeline because chunking (fed by Feat-0003) and
embedding/indexing (fed by Feat-0006) are one feature page — see its Index.md.

## Tech Stack Per Layer

| Layer | Technology |
|---|---|
| Ingestion / parsing | PyMuPDF (typed PDF), pydicom-style DICOM header parsing, Tesseract + Claude Vision (OCR fallback), Presidio + regex (PII) |
| Storage | AWS S3 (raw/markdown/redacted files), KMS or SSE-S3 encryption; SQLite (`db/`) for document/chunk/audit registries |
| Chunking | Custom entity-preserving chunker (medical entity regex + greedy packing); a second, unused `semantic_chunker.py` exists (see Feat-0002's open question) |
| Embeddings | `sentence-transformers` (default `all-MiniLM-L6-v2`) → ChromaDB |
| Keyword search | `rank-bm25`, in-memory index persisted to a JSON file |
| Reranking | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| Structured extraction | Local MLX-quantized `Qwen2.5-7B-Instruct` + QLoRA adapter, served over a separate FastAPI/uvicorn process on Apple Silicon (no CUDA) |
| Answer generation | Anthropic Claude (`llm/claude_client.py`) |
| Web UI | Streamlit (plain Python, no separate JS/TS frontend) |
| Ingest HTTP API | FastAPI (`POST /ingest/bulk`) |
| Concurrency | Python `threading` + in-memory queues — no Celery, no SQS/RabbitMQ, no distributed task queue |

## Cross-Cutting Architectural Decisions

These recur across multiple features and are recorded once here rather than duplicated in each
feature's own Architectural Decisions table.

| Decision | Reason | Recurs In |
|---|---|---|
| In-memory `queue.Queue`-based pipeline instead of a durable broker | Simplicity for a single-process prototype | Feat-0002, Feat-0003, Feat-0004, Feat-0006 |
| Retry-then-DLQ pattern (`workers/base_worker.py`, max 3 retries) is the uniform failure-handling strategy for every worker | One shared base class, one shared failure semantics | Feat-0002, Feat-0003, Feat-0004, Feat-0006 |
| Role-string RBAC (`allowed_roles` chunk metadata + a `role` string) instead of per-user or per-patient ownership | Matches a department-based hospital access model | Feat-0004, Feat-0005, Feat-0007 |
| No database migration tool — SQLAlchemy `create_all()` is the entire schema-management story | Prototype-stage simplicity | Feat-0002 (schema), Feat-0003 (schema), `Schemas/schemas.md` |
| Two unrelated authentication mechanisms for two entry points into the same pipeline: session login (Streamlit) vs. an unauthenticated, self-reported `role` header (FastAPI `/ingest/bulk`) | Historical/prototype — the HTTP endpoint was likely added for programmatic/service use without an auth story | Feat-0001, Feat-0003, Feat-0007 |
| Ingest-time PII redaction (one pass, permanent) *plus* a second, role-tiered query-time masking pass intended to further restrict what non-clinical roles see | Defense in depth for a HIPAA-relevant system | Feat-0004, Feat-0005 — **note the second pass is not actually wired into the live query path, see Feat-0005** |

## Known System-Wide Gaps

(Recorded once here since each surfaced independently from more than one feature's scan — see
the individual feature pages for full detail and file:line citations.)

- **`POST /ingest/bulk`'s `role` header is unauthenticated caller input** — any network-reachable
  caller can claim any role. The Streamlit UI's session-based login provides no equivalent
  guarantee for this HTTP path. (Feat-0001, Feat-0003)
- **Query-time role masking (`apply_role_mask()`) is defined but never invoked** in the actual
  search flow (`ui/search_page.py` calls `filter_results_by_role()` directly and skips
  `search/pipeline.py:secure_results()` entirely). (Feat-0004, Feat-0005, Feat-0007)
- **No database constraints enforce referential integrity** between `document_registry`,
  `chunk_registry`, and `audit_log` — all foreign-key-shaped relationships are
  application-level only. (`Schemas/schemas.md`)
- **The password hash in `security/auth.py` is unsalted SHA-256**, and the entire user store is
  five hardcoded accounts with no persistence layer. (Feat-0001)

## Last Updated

2026-09-05, by the initial `/init-code-wiki` scan (7 codebase-scanner + 1 schema-scanner + 1
dependency-mapper agent run).
