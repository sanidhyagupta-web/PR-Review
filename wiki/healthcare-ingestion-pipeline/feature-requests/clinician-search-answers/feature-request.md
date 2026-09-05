---
title: "Clinician Search & Answers"
slug: clinician-search-answers
owners:
  - Rhea (Product)
  - Arjun (Engineering)
  - Meera (Clinical Lead)
status: active
last_updated: 2026-09-05
proposed_by: agent
identity_confirmed: false
---

## Current State
A query path already exists in `ui/search_page.py` — rate limiting, input guardrail, PII-aware
retrieval, rerank, a Claude-generated answer with citations, output guardrail, and audit logging
— including citations rendered as expandable source cards. It does not yet satisfy DEC-0001: the
UI calls retrieval modules directly instead of going through an API endpoint. It is also missing
DEC-0007 (no search id or feedback mechanism) and shows a page number instead of a date on
citation cards, short of DEC-0003's literal requirement — [DEC-0011](../../decisions/DEC-0011_existing-search-ui-violates-dec-0001-and-dec-0007.md).

## Key Facts
- Every claim in a generated answer already carries an inline citation marker mapping back to
  chunk metadata — [DEC-0003](../../decisions/DEC-0003_citations-as-expandable-source-cards.md).
- The reranker returns five chunks to the model, but the model may cite only some of them —
  how many the UI surfaces is open, see Open Questions —
  [DEC-0009](../../decisions/DEC-0009_source-display-breadth.md).
- Answer generation runs a post-generation leakage/citation-integrity check; this is why
  streaming is contested, see Open Questions —
  [DEC-0008](../../decisions/DEC-0008_streaming-vs-post-validation-wait.md).

## Requirements
- The client-facing search capability must be a real API endpoint; the UI is a client of that
  endpoint, never a direct caller of retrieval modules —
  [DEC-0001](../../decisions/DEC-0001_search-endpoint-before-ui.md).
- The caller's role must be derived server-side from the authenticated session; a `role` field
  submitted in the request body is rejected outright, not silently dropped —
  [DEC-0002](../../decisions/DEC-0002_role-from-session-reject-body-role.md).
- Citations render as expandable source cards showing document, department, and date, with
  redaction placeholders (e.g. `[PATIENT_NAME]`) preserved intact —
  [DEC-0003](../../decisions/DEC-0003_citations-as-expandable-source-cards.md).
- An insufficient-context result ("no relevant records found") renders as its own distinct UI
  state — never an empty-looking answer, never an error —
  [DEC-0004](../../decisions/DEC-0004_insufficient-context-is-its-own-state.md).
- Every search gets a minted search id; per-search feedback is thumbs up/down with an optional
  free-text reason on a thumbs-down, attached to that search id —
  [DEC-0007](../../decisions/DEC-0007_per-search-feedback.md).

## Business Rules
- No search history, no saved searches, no cross-patient analytics in this pass; single-patient
  filtering is acknowledged as coming but explicitly out of scope for now; no changes to the
  ingestion pipeline (no new workers, no chunk schema changes, no touching merge weighting) —
  [DEC-0010](../../decisions/DEC-0010_scope-boundaries-search-v1.md).

## Decisions
| Date | Title | Type | Ticket |
|---|---|---|---|
| 2026-09-02 | [Search endpoint before UI](../../decisions/DEC-0001_search-endpoint-before-ui.md) | decided | |
| 2026-09-02 | [Role from session; reject role in request body](../../decisions/DEC-0002_role-from-session-reject-body-role.md) | decided | |
| 2026-09-02 | [Citations as expandable source cards](../../decisions/DEC-0003_citations-as-expandable-source-cards.md) | decided | |
| 2026-09-02 | [Insufficient context is its own state](../../decisions/DEC-0004_insufficient-context-is-its-own-state.md) | decided | |
| 2026-09-02 | [Audit event query-text logging](../../decisions/DEC-0005_audit-event-query-text-logging.md) | unresolved | |
| 2026-09-02 | [Disclosing role-filtered result counts](../../decisions/DEC-0006_disclose-role-filtered-result-counts.md) | unresolved | |
| 2026-09-02 | [Per-search feedback](../../decisions/DEC-0007_per-search-feedback.md) | decided | |
| 2026-09-02 | [Streaming vs. post-validation wait](../../decisions/DEC-0008_streaming-vs-post-validation-wait.md) | unresolved | |
| 2026-09-02 | [Source display breadth](../../decisions/DEC-0009_source-display-breadth.md) | unresolved | |
| 2026-09-02 | [Scope boundaries for search v1](../../decisions/DEC-0010_scope-boundaries-search-v1.md) | rejected | |
| 2026-09-05 | [Existing search UI violates DEC-0001 and DEC-0007](../../decisions/DEC-0011_existing-search-ui-violates-dec-0001-and-dec-0007.md) | rejected | [Linear](https://linear.app/flightdecktest-2/issue/RYT-4/dec-0003-citations-as-expandable-source-cards) |

## Evidence
- [DEC-0001](../../decisions/DEC-0001_search-endpoint-before-ui.md)
- [DEC-0002](../../decisions/DEC-0002_role-from-session-reject-body-role.md)
- [DEC-0003](../../decisions/DEC-0003_citations-as-expandable-source-cards.md)
- [DEC-0004](../../decisions/DEC-0004_insufficient-context-is-its-own-state.md)
- [DEC-0005](../../decisions/DEC-0005_audit-event-query-text-logging.md)
- [DEC-0006](../../decisions/DEC-0006_disclose-role-filtered-result-counts.md)
- [DEC-0007](../../decisions/DEC-0007_per-search-feedback.md)
- [DEC-0008](../../decisions/DEC-0008_streaming-vs-post-validation-wait.md)
- [DEC-0009](../../decisions/DEC-0009_source-display-breadth.md)
- [DEC-0010](../../decisions/DEC-0010_scope-boundaries-search-v1.md)
- [DEC-0011](../../decisions/DEC-0011_existing-search-ui-violates-dec-0001-and-dec-0007.md)

## Open Questions
- Whether to re-scope RYT-4 as "bring the existing citation/search UI into compliance with
  DEC-0001 and DEC-0007, plus add the missing date field" rather than "build citation rendering
  from scratch" — raised by the round-1 codebase reality check —
  [DEC-0011](../../decisions/DEC-0011_existing-search-ui-violates-dec-0001-and-dec-0007.md).
- Is `clinician-search-answers` the right feature request for this work, or does it belong to an
  existing one? Created by an agent from ticket
  `meeting-1mzUHFjWDrGKYmESQM5TC-ZV75BaVdoRvp4C1I2BP1h4-2026-09-05T08-35-54-082Z`; rename or merge
  if wrong.
- Whether the raw query text (and the thumbs-down feedback reason box, which carries the same
  risk) is stored in the audit/feedback event, and in what form — verbatim, masked like chunks,
  or encrypted with break-glass access —
  [DEC-0005](../../decisions/DEC-0005_audit-event-query-text-logging.md).
- Whether a clinician is told that results were withheld by role, including as a bare count —
  clinical-safety argument for disclosure vs. minimum-necessary argument against — needs both
  Clinical Lead and Security & Compliance, not a unilateral build decision —
  [DEC-0006](../../decisions/DEC-0006_disclose-role-filtered-result-counts.md).
- Whether the answer streams token-by-token or waits for post-generation validation
  (leakage/citation-integrity checks) to complete — pending a real latency measurement of the
  retrieval-to-generation pipeline —
  [DEC-0008](../../decisions/DEC-0008_streaming-vs-post-validation-wait.md).
- Whether the UI shows only the sources the model actually cited, all five chunks the model was
  given, or a browsable superset — a design question to be mocked, not argued —
  [DEC-0009](../../decisions/DEC-0009_source-display-breadth.md).

**Resolved:**
- Nothing recorded yet.

## Risks / Rejected Approaches
- Rendering role-filtered-out results with no disclosure risks a clinician believing they have
  the full picture when records exist outside their access — flagged as a genuine
  safety/compliance tension, not resolved —
  [DEC-0006](../../decisions/DEC-0006_disclose-role-filtered-result-counts.md).
- Streaming the answer before post-generation leakage/citation checks complete risks rendering
  and then retracting a PHI leak — considered and left open pending latency data, not adopted
  as-is — [DEC-0008](../../decisions/DEC-0008_streaming-vs-post-validation-wait.md).
- Search history, saved searches, cross-patient analytics, single-patient filtering, and any
  ingestion-pipeline change were explicitly rejected as in scope for this pass —
  [DEC-0010](../../decisions/DEC-0010_scope-boundaries-search-v1.md).
- RYT-4 assumed a clean slate for citation UI; codebase reality check found `ui/search_page.py`
  already implements it but out of compliance with DEC-0001 and DEC-0007 — rejected as scoped,
  needs re-scoping as a compliance fix rather than a net-new build —
  [DEC-0011](../../decisions/DEC-0011_existing-search-ui-violates-dec-0001-and-dec-0007.md).

## Relationships
**Depends On:** Nothing recorded yet.
**Related:** Nothing recorded yet.
