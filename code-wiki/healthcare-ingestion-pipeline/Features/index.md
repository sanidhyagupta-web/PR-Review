# Features — Healthcare Ingestion Pipeline

Last updated: 2026-09-05

**Generated from frontmatter — never hand-edit.** If this disagrees with a feature's own
`Index.md` frontmatter, the frontmatter wins; regenerate this file instead of editing it directly.

## Feature Catalog

### backend-service

| Feat ID | Feature | Domain | Criticality | Path |
|---|---|---|---|---|
| Feat-0001 | auth-encryption-audit *(shared-library)* | security-infrastructure | high | `security/{auth,encryption,audit_logger}.py` |
| Feat-0002 | chunking-embedding-indexing | retrieval-indexing | high | `ingestion/chunking/`, `workers/{chunking,embedding,keyword_index}_worker.py`, `indexing/` |
| Feat-0003 | document-ingestion-parsing | document-ingestion | high | `app/`, `ingestion/{validator,registry,state_machine,watcher}.py`, `ingestion/{parsers,markdown,ocr}/`, `workers/{base,parser,markdown}_worker.py`, `storage/`, `queues/` |
| Feat-0004 | pii-detection-redaction-rbac | pii-compliance | high | `ingestion/pii/`, `ingestion/metadata/`, `workers/pii_worker.py` |
| Feat-0005 | search-rag-query | rag-query | high | `search/pipeline.py`, `llm/claude_client.py`, `security/{guardrails,access_control}.py` |
| Feat-0006 | structured-data-extraction-ade | structured-extraction | medium | `workers/extraction_worker.py`, `llm/{ade_model,ade_api}.py`, `mlx_adapter/` |

### frontend-feature

| Feat ID | Feature | Domain | Criticality | Path |
|---|---|---|---|---|
| Feat-0007 | healthcare-search-ui | user-interface | high | `ui/` |

*(Feat-0001 is listed under backend-service above per its `type: shared-library` — noted inline
since this project has only one shared-library-typed feature.)*

## Workflow Routing Rules

Keyword → feature file, so a consumer doesn't have to load the whole tree:

| Keyword / Symptom | Load |
|---|---|
| upload, ingest, parse, OCR, DICOM, S3, validation, state machine, DocStatus | [Feat-0003](Feat-0003-document-ingestion-parsing/Index.md) |
| PII, PHI, redaction, RBAC, department, role policy, HIPAA masking | [Feat-0004](Feat-0004-pii-detection-redaction-rbac/Index.md) |
| chunk, chunking, embedding, Chroma, BM25, keyword index, rerank | [Feat-0002](Feat-0002-chunking-embedding-indexing/Index.md) |
| drug, adverse effect, ADE, extraction, MLX, QLoRA | [Feat-0006](Feat-0006-structured-data-extraction-ade/Index.md) |
| search, query, guardrail, prompt injection, RAG answer, Claude | [Feat-0005](Feat-0005-search-rag-query/Index.md) |
| login, session, password, encryption key, audit log | [Feat-0001](Feat-0001-auth-encryption-audit/Index.md) |
| Streamlit, page, sidebar, upload form, audit page | [Feat-0007](Feat-0007-healthcare-search-ui/Index.md) |

Per-workflow section loading:

| Workflow | Sections to Load |
|---|---|
| "Why did this document get stuck?" | Feat-0003 Status/State Machine, Known Error Scenarios |
| "Is this PHI exposure a real bug?" | Feat-0004 + Feat-0005 Access Control and Known Error Scenarios, `Architecture/Overview.md`'s Known System-Wide Gaps |
| "Add a new file type / department / role" | The owning feature's Business Rules + Safe vs Dangerous Changes |
| "Security review of ingest auth" | Feat-0001 + Feat-0003 Access Control, `Architecture/Overview.md`'s auth-mechanism decision row |

## Dependency Graph

Derived from each feature's `depends_on`/`consumed_by` frontmatter — see
`Architecture/Overview.md` for the rendered pipeline diagram.

| Feature | Depends On | Consumed By |
|---|---|---|
| Feat-0001 (auth-encryption-audit) | *(none)* | Feat-0003, Feat-0004, Feat-0007 |
| Feat-0002 (chunking-embedding-indexing) | Feat-0003 | Feat-0004, Feat-0005, Feat-0007 |
| Feat-0003 (document-ingestion-parsing) | Feat-0004, Feat-0001 | Feat-0002, Feat-0007 |
| Feat-0004 (pii-detection-redaction-rbac) | Feat-0002, Feat-0001 | Feat-0006, Feat-0003, Feat-0005 |
| Feat-0005 (search-rag-query) | Feat-0004 | Feat-0007 |
| Feat-0006 (structured-data-extraction-ade) | Feat-0004, Feat-0003 | Feat-0002 |
| Feat-0007 (healthcare-search-ui) | Feat-0001, Feat-0002, Feat-0003, Feat-0004, Feat-0005 | *(none — top of the stack)* |

**Downstream impact**: a breaking change to Feat-0004 (PII/RBAC) has the widest blast radius —
it's depended on by Feat-0003, Feat-0005, and Feat-0006, and feeds the `allowed_roles` data every
other feature's access control ultimately relies on. Feat-0001 (auth/encryption/audit) is the
most heavily *shared* leaf dependency (three consumers, no dependencies of its own).
