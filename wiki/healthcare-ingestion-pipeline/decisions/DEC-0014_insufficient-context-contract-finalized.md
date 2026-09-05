---
title: "Insufficient-context contract finalized: LLMUnavailable typing and audit outcome ownership (Q10/Q11)"
date: 2026-09-05
id: DEC-0014
feature: clinician-search-answers
source_meeting: "Linear ticket RYT-5"
recording_id: RYT-5
transcript_id: https://linear.app/flightdecktest-2/issue/RYT-5/dec-0004-insufficient-context-is-its-own-ui-state
type: decided
evidence_quote: "GIVEN a real failure (missing API key, an LLM exception, or the search backend being unavailable), THEN it must NOT be routed into the insufficient-context state. Achieved via the `generate_answer` contract change described in Error Paths: RYT-5 implements it, raising a typed `LLMUnavailable` exception (resolved, was Q7/Q9/Q10) rather than returning failure text through the answer channel."
reconciliation:
  existed_before: true
  previously_rejected: false
  contradicts: []
  on_roadmap: true
  dependencies: ["DEC-0004", "DEC-0011", "DEC-0012", "DEC-0013", "RYT-2"]
  changes_plan: true
supersedes: []
linear_issue: https://linear.app/flightdecktest-2/issue/RYT-5/dec-0004-insufficient-context-is-its-own-ui-state
---

## Statement
RYT-5's `generate_answer` → `AnswerResult` contract is finalized: infra failures raise a typed
`LLMUnavailable(RuntimeError)` rather than a bare exception, and RYT-5 (not RYT-2) adds the new
`details.outcome` field to the existing `log_event("SEARCH", ...)` call at
`ui/search_page.py:189` now, with RYT-2 owning only the later relocation of that emission into the
endpoint.

## Reconciliation Notes
DEC-0013 recorded this ticket's prior round of open questions (Q10/Q11); both are now resolved
per the reply, with no new open items surfaced, so the ticket has converged (marked `aligned`) and
this round is recorded as `decided` rather than another `unresolved` round. It doesn't contradict
or supersede DEC-0004/DEC-0011/DEC-0012/DEC-0013 — it completes the same contract those decisions
progressively elaborated. It does change plan: the feature request's Key Facts incorrectly states
that a post-generation leakage/citation-integrity check already runs, which this round's evidence
confirms is still false — that bullet is corrected below independently of this ticket's own scope.
