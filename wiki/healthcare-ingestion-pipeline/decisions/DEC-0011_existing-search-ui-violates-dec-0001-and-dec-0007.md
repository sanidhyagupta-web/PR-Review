---
title: "Existing search UI violates DEC-0001 and DEC-0007"
date: 2026-09-05
id: DEC-0011
feature: clinician-search-answers
source_meeting: "Linear ticket RYT-4"
recording_id: RYT-4
transcript_id: https://linear.app/flightdecktest-2/issue/RYT-4/dec-0003-citations-as-expandable-source-cards
type: rejected
evidence_quote: "`ui/search_page.py` already implements the full query path end-to-end — rate limiting, input guardrail, PII-aware retrieval (vector + BM25 + RRF merge), cross-encoder rerank, Claude-generated answer with citations, output guardrail, and audit logging."
reconciliation:
  existed_before: true
  previously_rejected: false
  contradicts: []
  on_roadmap: false
  dependencies:
    - DEC-0001
    - DEC-0007
  changes_plan: true
supersedes: []
linear_issue: https://linear.app/flightdecktest-2/issue/RYT-4/dec-0003-citations-as-expandable-source-cards
---

## Statement
Ticket RYT-4's premise of a clean slate is rejected: `ui/search_page.py` already implements the
full query path and already renders citations as expandable source cards, but it calls retrieval
modules directly instead of through an API endpoint (violating DEC-0001), has no search id or
feedback mechanism (missing DEC-0007), and shows a page number instead of a date (short of
DEC-0003's literal requirement).

## Reconciliation Notes
`existed_before` is true because DEC-0003 already decided this exact UI pattern; `contradicts` is
empty because this finding doesn't invalidate DEC-0003's statement, it exposes non-compliance with
DEC-0001 and DEC-0007, which are recorded as `dependencies`. `changes_plan` is true because the
feature request's Current State currently claims no query path exists, which this record
corrects.
