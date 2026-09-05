---
feat_id: Feat-0005
feature: search-rag-query
type: backend-service
domain: rag-query
criticality: high
touched_paths:
  - search/pipeline.py
  - llm/claude_client.py
  - security/guardrails.py
  - security/access_control.py
depends_on: [Feat-0004]
consumed_by: [Feat-0007]
implements: []
tags: [rag, llm, guardrails, access-control]
---

## Overview

| Type | Package | Path | Domain | Last updated |
|---|---|---|---|---|
| backend-service | (none) | `search/pipeline.py`, `llm/claude_client.py`, `security/guardrails.py`, `security/access_control.py` | rag-query | 2026-09-05 |

## Domain Purpose

The query-time security and answer-generation path: block malicious queries, filter retrieval
results to what the caller's role may see, mask PHI further based on role, generate an answer
with Claude, and scrub any residual PII from the LLM's output before it reaches the user.

**This feature's own module, `search/pipeline.py`, documents a mandatory call order —
`filter_results_by_role → apply_role_mask → generate_answer` — but is not the code path
actually used.** See the Known Error Scenarios section; this is the single most important thing
to know before touching this feature.

## Invariants

- A chunk must pass `filter_results_by_role()` before it is eligible to reach the LLM.
- `apply_role_mask()` is defined to run after that filter and before the LLM sees the chunk — **in
  the code that is actually invoked (`ui/search_page.py`), it never runs** (see below).
- Every query passes through `check_input()` before retrieval and `sanitise_output()` after
  generation.

## Access Control

**Model**: Role-based — the same `allowed_roles` chunk metadata and `role` string used
throughout the pipeline (see Feat-0004).

| Action | Access Condition | Enforced In |
|---|---|---|
| Chunk visible in results | `role` ∈ chunk's `allowed_roles`, or `role == "admin"` | `security/access_control.py:filter_results_by_role()` (lines 14-37) — the **sole** enforcement point |
| Entity-level masking of visible chunks | role-specific mask tier (see Feat-0004) | `ingestion/pii/role_based_masking.py:apply_role_mask()` — defined, **not called from the live query path** |
| Prompt-injection blocking | 16 regex patterns (system-prompt extraction, jailbreak phrasing, etc.) | `security/guardrails.py:check_input()` (lines 34-43) |
| Output PII scrub | re-runs PII detection on the LLM's own answer text | `security/guardrails.py:sanitise_output()` (lines 46-60) |

## Business Rules

| ID | Rule | Enforced In | Severity |
|---|---|---|---|
| BR-01 | Query blocked if it matches a prompt-injection/jailbreak pattern | `security/guardrails.py:check_input()` | HIGH |
| BR-02 | Retrieved chunks filtered to the caller's role before reaching the LLM | `security/access_control.py:filter_results_by_role()` | CRITICAL |
| BR-03 | If the query itself contains PII (e.g. a patient name), retrieval is pre-filtered to only chunks matching that entity hash (Top-D expansion for PERSON/PATIENT_NAME — see Feat-0004) | `indexing/pii_entity_index.py:get_chunk_ids_for_entities()` | MEDIUM |
| BR-04 | LLM's own output is re-scanned for residual PII and masked | `security/guardrails.py:sanitise_output()` | HIGH |
| BR-05 | Empty retrieval → a fixed "no relevant medical records were found" answer, not a hallucinated one | `llm/claude_client.py` (empty `context_chunks` branch) | MEDIUM |
| BR-06 | System prompt instructs the model to never reconstruct redacted placeholders | `llm/claude_client.py:12-24` | MEDIUM *(a prompt-level mitigation, not an access-control boundary — an LLM can be jailbroken past a system prompt)* |

## Safe vs Dangerous Changes

### Safe
- Tuning the 16 `check_input()` regex patterns to catch new injection phrasing.
- Adjusting the Claude system prompt wording (`llm/claude_client.py`), provided the PHI-handling instructions are preserved.

### Dangerous — Requires Review
| Change | Risk | Why |
|---|---|---|
| Any change to `security/access_control.py:filter_results_by_role()` | PHI over-exposure | Sole enforcement point for query-time RBAC — see also Feat-0004 |
| Wiring `ui/search_page.py` to call `search/pipeline.py:secure_results()` instead of `filter_results_by_role()` directly | Behavior change (chunks would newly be masked before reaching the LLM) | Read this whole file's Known Error Scenarios section first — this fixes a real gap, but changes what every role currently sees |

### Human Escalation Required
- **Deciding whether to wire `apply_role_mask()` into the live query path.** This is a
  product/security decision (does un-masked-but-role-filtered content reaching the LLM/user
  violate the compliance model this system claims?), not a routine bug fix.

## Known Error Scenarios

| Scenario | Error Returned | Root Cause |
|---|---|---|
| Query fails `check_input()` | Error shown, `GUARDRAIL_BLOCKED` audit event logged | Regex match |
| Rate limit exceeded (10/min) | Error shown, `RATE_LIMITED` audit event logged | `app/dependencies.py:RateLimiter` |
| **`apply_role_mask()` never invoked in the live query path** | *(no error — silent)* | `ui/search_page.py:45,63` calls `filter_results_by_role()` directly and calls `generate_answer()` immediately after, at line 183, **without** ever calling `apply_role_mask()` or importing `search/pipeline.py`. `search/pipeline.py:secure_results()` — which correctly chains `filter_results_by_role → apply_role_mask` — exists but has no caller anywhere in the repo. **Practical effect**: a researcher (whose mask tier should hide `[PATIENT_NAME]`/`[MRN]` tokens) currently sees them, because the only masking pass that would strip them is dead code. `sanitise_output()` afterwards catches residual *unredacted* PII in the LLM's own generated text, but does nothing about ingest-time redaction placeholders that were already present in the chunks it was given. |

## Testing Expectations

- No test found that exercises the full search pipeline end-to-end (retrieval → RBAC filter →
  masking → generation). `tests/unit/test_researcher_role.py` tests `apply_role_mask()` in
  isolation, which is exactly why this gap wasn't caught by that test — the test never had to
  go through `ui/search_page.py`'s actual call sequence.

## Architectural Decisions

| Decision | Reason | Do Not Change Without |
|---|---|---|
| Two-stage masking (ingest-time redaction + query-time role masking) | Different roles should see different levels of de-identification from the same underlying redacted chunk | Confirming whether query-time masking is meant to be mandatory (see Human Escalation above) |

## Forbidden Patterns

- Never call `generate_answer()` with chunks that haven't been through `filter_results_by_role()` first.
- Never treat `sanitise_output()` as a substitute for role-based masking — it only catches PII the LLM itself leaked into new text, not placeholders already present in the input chunks.

## Key Files

- `search/pipeline.py` — defines the correct `secure_results()` call order; **currently has no caller**
- `security/access_control.py` — `filter_results_by_role()`, the only RBAC enforcement point actually exercised
- `security/guardrails.py` — `check_input()` / `sanitise_output()`
- `llm/claude_client.py` — Claude API call, system prompt, empty-context fallback

## Context Routing

| Feature | Load when |
|---|---|
| Feat-0005 (this file) | Touching query-time security, RBAC filtering, guardrails, or answer generation |

| Workflow | Sections to load |
|---|---|
| Investigating a PHI-exposure complaint from a specific role | Known Error Scenarios, Access Control, Business Rules |
| Adding a new guardrail pattern | Business Rules (BR-01), Safe vs Dangerous Changes |

## Open Questions

- *Open question: is `apply_role_mask()` not being called in `ui/search_page.py` a missed
  refactor (the code was meant to route through `search/pipeline.py:secure_results()` and
  doesn't), or is `sanitise_output()` considered sufficient on its own? This determines whether
  it's a bug to fix or a design decision to document.*
