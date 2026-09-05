---
title: "Insufficient-context detection: real-failure carve-out and heuristic validation (Q6/Q7)"
date: 2026-09-05
id: DEC-0011
feature: clinician-search-answers
source_meeting: "Linear ticket RYT-5"
recording_id: RYT-5
transcript_id: https://linear.app/flightdecktest-2/issue/RYT-5/dec-0004-insufficient-context-is-its-own-ui-state
type: unresolved
evidence_quote: "GIVEN a real failure (missing API key, an LLM exception, or the search backend being unavailable), THEN it must NOT be routed into the insufficient-context state. *Open — Q7: no structural signal in today's return contract distinguishes this from criterion 1(b).*"
reconciliation:
  existed_before: true
  previously_rejected: false
  contradicts: []
  on_roadmap: true
  dependencies: ["RYT-2"]
  changes_plan: false
supersedes: []
linear_issue: https://linear.app/flightdecktest-2/issue/RYT-5/dec-0004-insufficient-context-is-its-own-ui-state
---

## Statement
Whether validating the `cited_indices == []` detection heuristic against `evaluation/test_dataset.json`
blocks this ticket's completion (Q6), and whether `generate_answer`'s return contract must change
to structurally distinguish a real failure from genuine insufficient-context (Q7), remain
unresolved.

## Reconciliation Notes
This ticket elaborates DEC-0004's already-decided core statement (insufficient context is its own
UI state) into a concrete contract — ownership split with RYT-2, the audit `outcome` field, and
feedback attachment were all resolved in Round 2 and don't reopen DEC-0004. Only Q6 and Q7 remain
open, so this round is recorded as `unresolved` rather than duplicating DEC-0004's `decided` type;
it does not contradict or supersede it, since the resolved portions are already reflected in the
feature request's Requirements.
