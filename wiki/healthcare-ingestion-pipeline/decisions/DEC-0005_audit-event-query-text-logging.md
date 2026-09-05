---
title: "Audit event query-text logging"
date: 2026-09-02
id: DEC-0005
feature: clinician-search-answers
source_meeting: "Harmony Product Sync — Clinician Search & Answers (2026-09-02)"
recording_id: 1mzUHFjWDrGKYmESQM5TC-ZV75BaVdoRvp4C1I2BP1h4
transcript_id: 1mzUHFjWDrGKYmESQM5TC-ZV75BaVdoRvp4C1I2BP1h4
type: unresolved
evidence_quote: "It's open. I'll build the event with everything except the query text and leave the field to be filled in once we've decided."
reconciliation:
  existed_before: false
  previously_rejected: false
  contradicts: []
  on_roadmap: false
  dependencies: []
  changes_plan: false
supersedes: []
linear_issue: https://linear.app/flightdecktest-2/issue/RYT-6/dec-0005-audit-event-query-text-logging
---

## Statement
Every search's audit event will record user, role, timestamp, and returned chunks, but whether
and how the clinician's raw query text is captured (verbatim, masked like chunks, or encrypted
under a break-glass process) is left open pending a proper compliance write-up, with the field
reserved but unfilled in the meantime.

## Reconciliation Notes
This is the first decision recorded for this project's wiki — `decisions/` was empty at
processing time, so there is nothing to duplicate, contradict, or supersede. Explicitly flagged
by Product as a real compliance question that should not be guessed at.
