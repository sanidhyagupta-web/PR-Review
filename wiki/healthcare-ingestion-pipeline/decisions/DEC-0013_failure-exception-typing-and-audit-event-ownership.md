---
title: "Failure-exception typing and audit-event ownership (Q10/Q11)"
date: 2026-09-05
id: DEC-0013
feature: clinician-search-answers
source_meeting: "Linear ticket RYT-5"
recording_id: RYT-5
transcript_id: https://linear.app/flightdecktest-2/issue/RYT-5/dec-0004-insufficient-context-is-its-own-ui-state
type: unresolved
evidence_quote: "Open — Q11: this round's scope-boundary answer states \"audit-event emission\" stays with RYT-2, but the already-resolved AC5/Q2 answer above has this ticket adding `details.outcome` to the existing `log_event` call at `ui/search_page.py:189`. These two statements conflict. Does RYT-5 update that existing call now (interim, since it's the only caller of `log_event` today), or does RYT-5 leave the audit call untouched and defer the `outcome` field entirely to RYT-2's endpoint?"
reconciliation:
  existed_before: true
  previously_rejected: false
  contradicts: []
  on_roadmap: false
  dependencies: ["DEC-0012", "RYT-2"]
  changes_plan: false
supersedes: []
linear_issue: https://linear.app/flightdecktest-2/issue/RYT-5/dec-0004-insufficient-context-is-its-own-ui-state
---

## Statement
Whether `generate_answer`'s infra-failure path should raise the bare underlying exception or a
typed exception class RYT-2 can catch specifically (Q10), and whether RYT-5 updates the existing
`log_event` call at `ui/search_page.py:189` with the new `outcome` field now or defers that
entirely to RYT-2's endpoint (Q11), remain unresolved.

## Reconciliation Notes
DEC-0012 recorded this ticket's prior round of open questions (Q8/Q9), both of which are now
resolved per the reply folded into Error Paths and Scope Boundaries — the future DEC-0008
integrity check owns citation validity and RYT-5 (not RYT-2) implements the contract change. This
decision records the two new open items the same reply surfaced (Q10/Q11), which are typing and
sequencing questions, not contradictions of anything already decided — `dependencies` links back
to DEC-0012 and to RYT-2, whose catch clause and audit-event ownership Q10/Q11 partly hinge on.
