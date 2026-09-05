---
title: "Scope boundaries for search v1"
date: 2026-09-02
id: DEC-0010
feature: clinician-search-answers
source_meeting: "Harmony Product Sync — Clinician Search & Answers (2026-09-02)"
recording_id: 1mzUHFjWDrGKYmESQM5TC-ZV75BaVdoRvp4C1I2BP1h4
transcript_id: 1mzUHFjWDrGKYmESQM5TC-ZV75BaVdoRvp4C1I2BP1h4
type: rejected
evidence_quote: "Scope boundaries so this doesn't sprawl. No search history. No saved searches. No cross-patient analytics."
reconciliation:
  existed_before: false
  previously_rejected: false
  contradicts: []
  on_roadmap: false
  dependencies: []
  changes_plan: false
supersedes: []
linear_issue: https://linear.app/flightdecktest-2/issue/RYT-11/dec-0010-scope-boundaries-for-search-v1
---

## Statement
For this pass, search history, saved searches, cross-patient analytics, single-patient
filtering, and any change to the ingestion pipeline (new workers, chunk schema changes,
merge-weighting changes) are explicitly out of scope.

## Reconciliation Notes
This is the first decision recorded for this project's wiki — `decisions/` was empty at
processing time, so there is nothing to duplicate, contradict, or supersede. Single-patient
filtering was explicitly acknowledged as planned future work, just not this pass; the retrieval
constants on the ingestion side were explicitly called "settled" and not being reopened.
