---
title: "Per-search feedback (thumbs + optional reason)"
date: 2026-09-02
id: DEC-0007
feature: clinician-search-answers
source_meeting: "Harmony Product Sync — Clinician Search & Answers (2026-09-02)"
recording_id: 1mzUHFjWDrGKYmESQM5TC-ZV75BaVdoRvp4C1I2BP1h4
transcript_id: 1mzUHFjWDrGKYmESQM5TC-ZV75BaVdoRvp4C1I2BP1h4
type: decided
evidence_quote: "Decided. Thumbs, optional free-text reason on a thumbs-down."
reconciliation:
  existed_before: false
  previously_rejected: false
  contradicts: []
  on_roadmap: false
  dependencies: ["DEC-0005"]
  changes_plan: false
supersedes: []
linear_issue: https://linear.app/flightdecktest-2/issue/RYT-8/dec-0007-per-search-feedback-thumbs-optional-reason
---

## Statement
Each search gets a minted search id, and per-search feedback is captured as thumbs up/down with
an optional free-text reason attached on a thumbs-down.

## Reconciliation Notes
This is the first decision recorded for this project's wiki — `decisions/` was empty at
processing time, so there is nothing to duplicate, contradict, or supersede. Depends on
[DEC-0005](DEC-0005_audit-event-query-text-logging.md): the free-text thumbs-down reason box
carries the same raw-text PHI question as the audit query-logging decision and should be
resolved alongside it, not separately.
