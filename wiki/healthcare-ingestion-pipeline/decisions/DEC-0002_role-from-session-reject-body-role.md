---
title: "Role from session; reject role in request body"
date: 2026-09-02
id: DEC-0002
feature: clinician-search-answers
source_meeting: "Harmony Product Sync — Clinician Search & Answers (2026-09-02)"
recording_id: 1mzUHFjWDrGKYmESQM5TC-ZV75BaVdoRvp4C1I2BP1h4
transcript_id: 1mzUHFjWDrGKYmESQM5TC-ZV75BaVdoRvp4C1I2BP1h4
type: decided
evidence_quote: "The role is derived from the authenticated session server-side and it is never read off the request."
reconciliation:
  existed_before: false
  previously_rejected: false
  contradicts: []
  on_roadmap: false
  dependencies: []
  changes_plan: false
supersedes: []
linear_issue: https://linear.app/flightdecktest-2/issue/RYT-3/dec-0002-role-from-session-reject-role-in-request-body
---

## Statement
The caller's role for search requests is derived server-side from the authenticated session,
never from the request body, and a role field submitted in the request body causes the request
to be rejected rather than silently ignored.

## Reconciliation Notes
This is the first decision recorded for this project's wiki — `decisions/` was empty at
processing time, so there is nothing to duplicate, contradict, or supersede.
