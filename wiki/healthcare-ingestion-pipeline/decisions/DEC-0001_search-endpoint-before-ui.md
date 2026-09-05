---
title: "Search endpoint before UI"
date: 2026-09-02
id: DEC-0001
feature: clinician-search-answers
source_meeting: "Harmony Product Sync — Clinician Search & Answers (2026-09-02)"
recording_id: 1mzUHFjWDrGKYmESQM5TC-ZV75BaVdoRvp4C1I2BP1h4
transcript_id: 1mzUHFjWDrGKYmESQM5TC-ZV75BaVdoRvp4C1I2BP1h4
type: decided
evidence_quote: "I want to build a real search endpoint first, and have the UI be a client of that endpoint. Not a Streamlit app that imports the retrieval modules directly."
reconciliation:
  existed_before: false
  previously_rejected: false
  contradicts: []
  on_roadmap: false
  dependencies: []
  changes_plan: false
supersedes: []
linear_issue: https://linear.app/flightdecktest-2/issue/RYT-2/dec-0001-search-endpoint-before-ui
---

## Statement
The clinician search/answers capability will be built as a real search API endpoint first, with
the UI as a client of that endpoint rather than a caller of retrieval modules directly, so that
pipeline-enforced audit logging and role filtering can't be bypassed.

## Reconciliation Notes
This is the first decision recorded for this project's wiki — `decisions/` was empty at
processing time, so there is nothing to duplicate, contradict, or supersede.
