---
title: "Streaming vs. post-validation wait"
date: 2026-09-02
id: DEC-0008
feature: clinician-search-answers
source_meeting: "Harmony Product Sync — Clinician Search & Answers (2026-09-02)"
recording_id: 1mzUHFjWDrGKYmESQM5TC-ZV75BaVdoRvp4C1I2BP1h4
transcript_id: 1mzUHFjWDrGKYmESQM5TC-ZV75BaVdoRvp4C1I2BP1h4
type: unresolved
evidence_quote: "Then measure it before we choose. Leave it open — and if the honest answer turns out to be twelve seconds we'll have a different conversation about the pipeline, not about streaming."
reconciliation:
  existed_before: false
  previously_rejected: false
  contradicts: []
  on_roadmap: false
  dependencies: []
  changes_plan: false
supersedes: []
linear_issue: https://linear.app/flightdecktest-2/issue/RYT-9/dec-0008-streaming-vs-post-validation-wait
---

## Statement
Whether the answer streams token-by-token or waits for post-generation leakage/citation-integrity
validation to complete is left open until real pipeline latency (embed, retrieval, merge,
rerank, generation) is measured.

## Reconciliation Notes
This is the first decision recorded for this project's wiki — `decisions/` was empty at
processing time, so there is nothing to duplicate, contradict, or supersede. Engineering's stated
preference for waiting was explicitly noted as an opinion, not a decision.
