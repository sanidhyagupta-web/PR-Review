---
title: "Log how many terms the OCR regex fallback corrected"
slug: eng-35
status: active
last_updated: 2026-10-30
linear_issue: "https://linear.app/flightdecktest-2/issue/ENG-35/log-how-many-terms-the-ocr-regex-fallback-corrected"
proposed_by: agent
identity_confirmed: false
---

## Current State

Requested in [ENG-35](https://linear.app/flightdecktest-2/issue/ENG-35/log-how-many-terms-the-ocr-regex-fallback-corrected). Alignment agreed the spec under Requirements, as the ticket said when alignment agreed it.

## Key Facts

Nothing recorded yet.

## Requirements

In `correct_medical_terms` (`ingestion/ocr/ocr_quality.py`), the Sapling path logs "Sapling corrected %d term(s) in OCR text" at debug level. The regex fallback logs nothing, so a log gives no way to tell whether the fallback changed anything.

### Summary

Work-Type: Feature

Add a debug-level correction count to the existing OCR regex fallback without changing the text returned or the Sapling path.

### Context

The fallback currently applies the entries in `_CORRECTIONS` without reporting how many replacements it made. The new log provides that diagnostic information. Count replacement occurrences, not distinct correction-map entries.

### User Flow

When `correct_medical_terms` runs the regex fallback, a developer or operator viewing debug logs can see the total number of replacements for that invocation if the total is positive. No new UI or caller interaction is required.

### Error Paths

Preserve the existing warning and fallback behavior when a Sapling request raises `requests.RequestException`. The zero-replacement silence requirement concerns the new correction-count log; it does not suppress the existing API-unavailable warning.

### Acceptance Criteria

* When the regex fallback replaces at least one term, it logs "Regex fallback corrected N term(s) in OCR text" at debug level. N is the total number of replacements for that invocation, including repeated occurrences of the same misspelling and replacements across different correction entries.
* Emit one aggregate correction-count message per fallback invocation with a positive replacement count.
* When it replaces nothing, it emits no regex correction-count message.
* The text it returns is the same as today, including case-insensitive matching, whole-word boundaries, and the existing replacement values.
* Unit tests check the log with `caplog` and make no network call. Cover positive counts, repeated occurrences, multiple correction entries, and zero replacements, and assert the returned text remains correct.

### Existing System Behaviour

`correct_medical_terms` attempts Sapling when an API key is configured. Successful Sapling processing returns before the fallback and logs its edit count only when edits exist. A request exception produces a warning before falling through to regex processing. With no API key, regex processing runs directly. The fallback uses case-insensitive, whole-word substitutions for `_CORRECTIONS` and currently emits no correction-count log.

### Scope Boundaries

Limit production changes to counting and logging replacements in the existing regex fallback, with supporting unit tests. Do not change the correction dictionary, matching rules, returned text, API request behavior, Sapling logging, or existing warning behavior. Do not log OCR text or individual terms as part of the new message.

### Reference Documents

* `ingestion/ocr/ocr_quality.py`: `correct_medical_terms`, `_CORRECTIONS`, and the module logger.
* `workers/parser_worker.py`: existing OCR correction callers.
* No `code-wiki/` or `wiki/` documents were found in the checkout.

### Round log

* Round 1, aligned: verified the logging gap in source; clarified occurrence counting, per-invocation aggregation, unchanged warning behavior, and network-free test coverage.

## Business Rules

Nothing recorded yet.

## Decisions

| Date | Title | Type | Ticket |
|---|---|---|---|

## Evidence

Nothing recorded yet.

## Open Questions

- Is this the right name and boundary for this work? Keep the folder name `eng-35`: a later alignment of ENG-35 updates the page there. Set `identity_confirmed: true` once a person has answered this, and delete the question only after it is answered.

**Resolved:**

Nothing recorded yet.

## Risks / Rejected Approaches

Nothing recorded yet.

## Relationships

**Depends On:** Nothing recorded yet.

**Related:** Nothing recorded yet.
