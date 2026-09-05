---
title: "Citation-validity check and generate_answer contract-change ownership (Q8/Q9)"
date: 2026-09-05
id: DEC-0012
feature: clinician-search-answers
source_meeting: "Linear ticket RYT-5"
recording_id: RYT-5
transcript_id: https://linear.app/flightdecktest-2/issue/RYT-5/dec-0004-insufficient-context-is-its-own-ui-state
type: unresolved
evidence_quote: "Open — Q9: which ticket implements this contract change to llm/claude_client.py — this ticket (it already owns the case→state mapping and this contract is that mapping made executable) or RYT-2 (which will be the caller)? Flagged as a sequencing call, not decided."
reconciliation:
  existed_before: false
  previously_rejected: false
  contradicts: []
  on_roadmap: false
  dependencies: ["DEC-0011", "RYT-2"]
  changes_plan: true
supersedes: []
linear_issue: https://linear.app/flightdecktest-2/issue/RYT-5/dec-0004-insufficient-context-is-its-own-ui-state
---

## Statement
Whether this ticket's classifier or a future DEC-0008 leakage/citation-integrity check owns
citation-validity determination (Q8), and whether this ticket or RYT-2 implements the
`generate_answer` → `AnswerResult` contract change that acceptance criterion 4 depends on (Q9),
remain unresolved.

## Reconciliation Notes
DEC-0011 recorded this ticket's prior round of open questions (Q6/Q7), both of which are now
resolved per the reply folded into Acceptance Criteria 4 and 8 — the contract-change requirement
and shape are settled, and heuristic validation was replaced with a blocking unit-test AC rather
than left open. This decision records the two new open items the same reply surfaced (Q8/Q9),
which are sequencing/ownership questions, not contradictions of anything already decided —
`dependencies` links back to DEC-0011 and to RYT-2, whose eventual scope Q9 partly hinges on.
