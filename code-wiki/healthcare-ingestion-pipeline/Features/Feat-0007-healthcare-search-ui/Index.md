---
feat_id: Feat-0007
feature: healthcare-search-ui
type: frontend-feature
domain: user-interface
criticality: high
touched_paths:
  - ui/streamlit_app.py
  - ui/login_page.py
  - ui/search_page.py
  - ui/upload_page.py
  - ui/bulk_upload_page.py
  - ui/audit_page.py
depends_on: [Feat-0001, Feat-0002, Feat-0003, Feat-0004, Feat-0005]
consumed_by: []
implements: []
tags: [streamlit, ui, healthcare-search]
---

## Overview

| Type | Package | Path | Domain | Last updated |
|---|---|---|---|---|
| frontend-feature | (none) | `ui/` | user-interface | 2026-09-05 |

This is a **single-process Streamlit app, plain Python** — there is no separate JS/TS frontend,
no bundler, and no HTTP boundary between "frontend" and "backend": every page imports and calls
backend modules directly, in-process. Where the rest of this wiki's frontend section headings
say "API calls", read that as "direct Python function calls into the modules below."

## What This Does for the User

A role-gated web app for hospital staff to upload documents into the ingestion pipeline, search
over them in natural language with an LLM-generated answer, and (for authorized roles) review
the audit trail and dead-letter queue.

## Key User Flows

| Flow | What Happens |
|---|---|
| **Login** | Username/password form → `security.auth.login()` (Feat-0001) → on success, `st.session_state` populated and the app reruns into the authenticated shell |
| **Search** | Query text → rate-limit check → `check_input()` guardrail (Feat-0005) → PII pre-filter on the query itself (Feat-0004) → vector (Chroma) + keyword (BM25) retrieval (Feat-0002), each filtered by `filter_results_by_role()` (Feat-0005) → rerank (Feat-0002) → `generate_answer()` (Feat-0005) → `sanitise_output()` (Feat-0005) → answer + citations displayed, `SEARCH` audit event logged |
| **Single-file upload** | File + metadata form → rate-limit check → `ingest_document()` (Feat-0003) → success/failure list + recent-documents table |
| **Bulk upload** | Role check (only doctor/nurse/admin) → up to 50 files → `_process_single_upload_bytes()` per file (Feat-0003) → per-file queued/rejected results, one `BULK_INGEST_SUBMITTED` audit event for the whole batch |
| **Audit log view** | Two tabs: audit events (`get_audit_trail()`, Feat-0001) and the dead-letter queue (`queues.dlq.list_messages()`) |

## UI States

| Condition | What Renders |
|---|---|
| Not authenticated | Login form only (`ui/login_page.py`), all other pages blocked |
| Empty search query | "Enter a query" info message |
| Rate limit exceeded | Error message, `RATE_LIMITED` audit event |
| Query blocked by guardrail | Error message, `GUARDRAIL_BLOCKED` audit event |
| Query contains detected PII | A caption noting PII was detected in the query |
| No search results | "No results found" warning |
| Bulk upload, unauthorized role | Error message, page returns early before rendering the upload form |
| Bulk upload, >50 files | Error message, page returns early |
| No audit events for the filter | "No audit events found" info |
| Empty dead-letter queue | "DLQ is empty" success message |

## APIs Consumed

*("API" here means a direct in-process Python call — see the note under Overview.)*

| Function | Owning Feature | Description |
|---|---|---|
| `security.auth.login/logout/is_authenticated/current_user` | Feat-0001 | Session auth |
| `security.audit_logger.log_event/get_audit_trail` | Feat-0001 | Audit trail write/read |
| `app.main.ingest_document` / `_process_single_upload_bytes` | Feat-0003 | Document upload |
| `indexing.chroma_store.query`, `indexing.opensearch_index.keyword_search(_filtered)`, `indexing.reranker.rerank`, `indexing.pii_entity_index.get_chunk_ids_for_entities` | Feat-0002 | Retrieval + reranking |
| `ingestion.pii.pii_detector.detect_pii` | Feat-0004 | PII detection on the query text itself |
| `security.access_control.filter_results_by_role` | Feat-0005 | RBAC filter on retrieved chunks — **called directly, not via `search/pipeline.py`; see Feat-0005's Known Error Scenarios for why this matters** |
| `security.guardrails.check_input/sanitise_output` | Feat-0005 | Input/output guardrails |
| `llm.claude_client.generate_answer` | Feat-0005 | LLM answer generation |
| `ingestion.metadata.rbac_policy.get_ingest_allowed_roles` | Feat-0004 | Bulk-upload role gate |

## State

No separate state-management store — state lives entirely in Streamlit's `st.session_state`:

| Key | Set By | Holds |
|---|---|---|
| `authenticated` | `security.auth.login()` | `bool` |
| `username` | `security.auth.login()` | logged-in user's username, used for rate limiting and audit `user_id` |
| `role` | `security.auth.login()` | one of `admin`, `doctor`, `nurse`, `radiologist`, `billing`, `cardiologist`, `researcher` |
| `department` | `security.auth.login()` | one of `general`, `cardiology`, `billing`, `radiology`, `oncology` |
| `display_name` | `security.auth.login()` | shown in the sidebar |

## Business Rules

| ID | Rule | Enforced In | Severity |
|---|---|---|---|
| BR-01 | No page renders content until authenticated | `ui/streamlit_app.py:19-22` | CRITICAL |
| BR-02 | Bulk upload requires role ∈ {doctor, nurse, admin}; single-file upload has **no equivalent role gate** in the UI itself | `ui/bulk_upload_page.py:69` | HIGH |
| BR-03 | Rate limit: 10 operations/minute per user, applied independently on search and both upload pages | `app/dependencies.py:RateLimiter`, checked at each page | MEDIUM |
| BR-04 | Six pipeline worker threads (`ParserWorker` … `KeywordIndexWorker`) are started once per process, lazily, from the upload pages | `ui/upload_page.py`, `ui/bulk_upload_page.py` (`_ensure_workers()`) | HIGH |

## Safe vs Dangerous Changes

### Safe
- Adding a new page/tab that only reads existing data (e.g. a dashboard).
- Cosmetic changes to any page's layout.

### Dangerous — Requires Review
| Change | Risk | Why |
|---|---|---|
| Calling `filter_results_by_role()` without also masking (or switching to `search/pipeline.py:secure_results()`) | PHI exposure | See Feat-0005 — this is the current (gap-laden) pattern; don't copy it into new code without understanding why |
| Moving worker-thread startup logic | Pipeline stalls silently | `_ensure_workers()`'s locking pattern is what prevents duplicate worker threads across Streamlit reruns; no shutdown/health-check mechanism exists |

### Human Escalation Required
- Adding a role check to the single-file upload page to match bulk upload's — this changes
  existing behavior (currently any authenticated user can single-upload) and should be a
  deliberate decision, not a silent fix.

## Known Error Scenarios

| Scenario | What Happens | Root Cause |
|---|---|---|
| Backend call raises during retrieval | `st.warning("... unavailable: {e}")` shown, rest of page continues | try/except around vector/keyword search calls |
| Worker threads never explicitly stopped | Threads persist for the process lifetime | No shutdown mechanism found |

## Testing Expectations

- No Streamlit-specific test tooling is wired up in this repo (no `streamlit.testing.v1.AppTest`
  usage found). See `.claude/skills/frontend-test/SKILL.md` for how to add coverage if asked.

## Forbidden Patterns

- Never call a backend mutation (ingest, encryption) directly from a page without going through
  the same audit-logging call sites the existing pages use — the audit trail is the only record
  of who did what.

## Key Files

- `ui/streamlit_app.py` — shell, auth gate, page routing
- `ui/login_page.py`, `ui/search_page.py`, `ui/upload_page.py`, `ui/bulk_upload_page.py`, `ui/audit_page.py`

## Context Routing

| Feature | Load when |
|---|---|
| Feat-0007 (this file) | Touching any Streamlit page, session state, or the worker-thread startup pattern |

| Workflow | Sections to load |
|---|---|
| Adding a new page | Key User Flows, State, Business Rules |
| Debugging "search shows PHI it shouldn't" | APIs Consumed (note on `filter_results_by_role`), then Feat-0005 in full |

## Open Questions

- *Open question: single-file upload (`ui/upload_page.py`) has no role check equivalent to bulk
  upload's — is that intentional (any authenticated user may upload one file) or an oversight?*
