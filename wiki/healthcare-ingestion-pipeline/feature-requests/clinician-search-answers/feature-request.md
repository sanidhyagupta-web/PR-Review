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
No query path exists yet: documents are parsed, chunked, masked, embedded, and indexed, but
there is currently no way for a clinician to ask a question and get an answer. This feature
request defines that query/answer layer — a search endpoint the UI calls (never the reverse),
role-scoped retrieval, and an answer with sourced citations — [DEC-0001](../../decisions/DEC-0001_search-endpoint-before-ui.md).

## Key Facts
- Every claim in a generated answer already carries an inline citation marker mapping back to
  chunk metadata — [DEC-0003](../../decisions/DEC-0003_citations-as-expandable-source-cards.md).
- The reranker returns five chunks to the model, but the model may cite only some of them —
  how many the UI surfaces is open, see Open Questions —
  [DEC-0009](../../decisions/DEC-0009_source-display-breadth.md).
- No post-generation leakage/citation-integrity check exists yet — only a regex at
  `llm/claude_client.py:80-81` checks for well-formed, in-range citation markers; a real
  integrity check is planned but not built, which affects DEC-0008's streaming-vs-wait latency
  premise —
  [DEC-0014](../../decisions/DEC-0014_insufficient-context-contract-finalized.md).

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
- `generate_answer` returns a typed `AnswerResult` (`outcome`, `text`, `cited_indices`, `error`)
  instead of a tuple; infra failures raise a typed `LLMUnavailable(RuntimeError)` rather than
  returning failure text through the answer channel, and the audit `log_event("SEARCH", ...)`
  call gains a `details.outcome` field now, interim, until RYT-2 relocates emission into the
  endpoint —
  [DEC-0014](../../decisions/DEC-0014_insufficient-context-contract-finalized.md).

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
| 2026-09-05 | [Insufficient-context detection: real-failure carve-out and heuristic validation (Q6/Q7)](../../decisions/DEC-0011_insufficient-context-detection-open-questions.md) | unresolved | [Linear](https://linear.app/flightdecktest-2/issue/RYT-5/dec-0004-insufficient-context-is-its-own-ui-state) |
| 2026-09-05 | [Citation-validity check and generate_answer contract-change ownership (Q8/Q9)](../../decisions/DEC-0012_citation-validity-and-contract-change-ownership.md) | unresolved | [Linear](https://linear.app/flightdecktest-2/issue/RYT-5/dec-0004-insufficient-context-is-its-own-ui-state) |
| 2026-09-05 | [Failure-exception typing and audit-event ownership (Q10/Q11)](../../decisions/DEC-0013_failure-exception-typing-and-audit-event-ownership.md) | unresolved | [Linear](https://linear.app/flightdecktest-2/issue/RYT-5/dec-0004-insufficient-context-is-its-own-ui-state) |
| 2026-09-05 | [Insufficient-context contract finalized: LLMUnavailable typing and audit outcome ownership (Q10/Q11)](../../decisions/DEC-0014_insufficient-context-contract-finalized.md) | decided | [Linear](https://linear.app/flightdecktest-2/issue/RYT-5/dec-0004-insufficient-context-is-its-own-ui-state) |

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
- [DEC-0011](../../decisions/DEC-0011_insufficient-context-detection-open-questions.md)
- [DEC-0012](../../decisions/DEC-0012_citation-validity-and-contract-change-ownership.md)
- [DEC-0013](../../decisions/DEC-0013_failure-exception-typing-and-audit-event-ownership.md)
- [DEC-0014](../../decisions/DEC-0014_insufficient-context-contract-finalized.md)

## Open Questions
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
- ~~Whether `generate_answer`'s infra-failure path should raise the bare underlying exception or a
  typed exception class RYT-2 can catch specifically, and whether RYT-5 updates the existing
  `log_event` call at `ui/search_page.py:189` with the new `outcome` field now or defers that
  entirely to RYT-2's endpoint.~~ → resolved by
  [DEC-0014](../../decisions/DEC-0014_insufficient-context-contract-finalized.md): a typed
  `LLMUnavailable(RuntimeError)`, and RYT-5 adds `details.outcome` at the current call site now,
  interim.
- ~~Whether validating the `cited_indices == []` insufficient-context heuristic against
  `evaluation/test_dataset.json` blocks ticket completion, and whether `generate_answer`'s return
  contract needs to change to structurally distinguish a real failure from genuine
  insufficient-context.~~ → resolved by
  [DEC-0012](../../decisions/DEC-0012_citation-validity-and-contract-change-ownership.md): not
  blocking (replaced with a unit-test AC), and yes, the contract must change.
- ~~Whether this ticket's classifier or a future DEC-0008 leakage/citation-integrity check owns
  citation-validity determination, and whether this ticket or RYT-2 implements the
  `generate_answer` → `AnswerResult` contract change that acceptance criterion 4 depends on.~~ →
  resolved by
  [DEC-0013](../../decisions/DEC-0013_failure-exception-typing-and-audit-event-ownership.md): the
  future DEC-0008 integrity check owns citation validity, and RYT-5 (not RYT-2) implements the
  contract change.

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

## Relationships
**Depends On:** Nothing recorded yet.
**Related:** Nothing recorded yet.
