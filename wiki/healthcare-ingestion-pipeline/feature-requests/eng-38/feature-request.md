---
title: "Add unit tests for the RBAC policy module"
slug: eng-38
status: active
last_updated: 2026-11-06
linear_issue: "https://linear.app/flightdecktest-2/issue/ENG-38/add-unit-tests-for-the-rbac-policy-module"
proposed_by: agent
identity_confirmed: false
---

## Current State

Requested in [ENG-38](https://linear.app/flightdecktest-2/issue/ENG-38/add-unit-tests-for-the-rbac-policy-module). Alignment agreed the spec under Requirements, as the ticket said when alignment agreed it.

## Key Facts

Nothing recorded yet.

## Requirements

`ingestion/metadata/rbac_policy.py` decides which roles can read each department's chunks and which roles can submit documents.

`tests/unit/test_researcher_role.py` (lines 214–228) already checks four things about it: a researcher is allowed in `general` and `cardiology`, a researcher is not allowed in `billing`, and an unknown department raises `ValueError`. Nothing tests each department's full role list, the list of departments, the roles allowed to submit documents, or whether a caller can change the policy by editing what it gets back.

Add `tests/unit/test_rbac_policy.py` with these checks:

* `get_allowed_roles` returns exactly these roles for each department:
  * `general`: doctor, nurse, admin, researcher
  * `cardiology`: doctor, nurse, cardiologist, researcher
  * `billing`: billing, admin
  * `radiology`: doctor, nurse, radiologist, admin
  * `oncology`: doctor, nurse, admin
* For an unknown department, the `ValueError` message names that department and lists the five valid ones.
* Changing the list that `get_allowed_roles` returns does not change what the next call returns.
* `get_all_departments` returns exactly the five departments above.
* `get_ingest_allowed_roles` is exactly `doctor`, `nurse` and `admin`; `researcher`, `billing`, `cardiologist` and `radiologist` are not in it.

Only add the new test file. Do not change `rbac_policy.py` or `test_researcher_role.py`. The tests run with `pytest`.

### Summary

Work-Type: Tech-Debt

Add focused unit coverage for the existing RBAC policy without changing production behaviour.

### Context

The current tests cover researcher membership in two departments, exclusion from billing, and the unknown-department exception type. They leave the complete policy mappings, department enumeration, ingest permissions, diagnostic contents, and defensive copying without direct regression coverage. The impact is missing regression protection for access-control policy; this item does not report a production defect.

Migration: *Not applicable: only a new Python test file is added; no production code, schema, or stored data changes.* Rollback consists of removing or reverting the new test file; no data rollback is needed.

### User Flow

*Not applicable: this test-only change introduces no application user flow.* Developers run the new tests with `pytest tests/unit/test_rbac_policy.py`.

### Error Paths

An unknown department must raise `ValueError`; its message must identify the supplied department and include all five valid department names. No new production error handling is introduced.

### Acceptance Criteria

1. The new test file checks the complete allowed-role contents for each of the five departments against the explicit expectations above.
2. The unknown-department test checks both `ValueError` and the required diagnostic contents.
3. A test mutates a returned allowed-role list and verifies that a subsequent call for the same department still returns the original policy contents.
4. Department enumeration contains exactly general, cardiology, billing, radiology, and oncology.
5. Ingest permissions contain exactly doctor, nurse, and admin, excluding researcher, billing, cardiologist, and radiologist.
6. The tests pass against the existing implementation using pytest. Non-functional criterion: the tests exercise the policy module directly without requiring application services or external infrastructure.
7. The only repository change is the addition of `tests/unit/test_rbac_policy.py`.

### Existing System Behaviour

`get_allowed_roles` returns a fresh list for a known department. For an unknown department it raises `ValueError` containing the supplied name and a sorted list of valid departments. `get_all_departments` returns a list of the policy's department names. `get_ingest_allowed_roles` returns a frozenset containing doctor, nurse, and admin. All requested policy values match the source.

### Scope Boundaries

Only add the specified unit-test file. Do not modify the policy, existing tests, fixtures, configuration, documentation, or dependencies. This item does not change access permissions or add integration coverage.

### Reference Documents

* `ingestion/metadata/rbac_policy.py:9–40`
* `tests/unit/test_researcher_role.py:214–228`
* `code-wiki/healthcare-ingestion-pipeline/Features/Feat-0004-pii-detection-redaction-rbac/Index.md`

### Round log

* Round 1, rejected: the earlier coverage assertion contradicted the four existing policy tests, as recorded in the factory comment.
* Round 2, aligned: verified the corrected coverage statement and all requested checks against source; documented the test-only scope and migration/rollback applicability.

## Business Rules

Nothing recorded yet.

## Decisions

| Date | Title | Type | Ticket |
|---|---|---|---|

## Evidence

Nothing recorded yet.

## Open Questions

- Is this the right name and boundary for this work? Keep the folder name `eng-38`: a later alignment of ENG-38 updates the page there. Set `identity_confirmed: true` once a person has answered this, and delete the question only after it is answered.

**Resolved:**

Nothing recorded yet.

## Risks / Rejected Approaches

Nothing recorded yet.

## Relationships

**Depends On:** Nothing recorded yet.

**Related:** Nothing recorded yet.
