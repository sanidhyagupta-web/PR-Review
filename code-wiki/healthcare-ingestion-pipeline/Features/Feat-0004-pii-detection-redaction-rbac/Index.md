---
feat_id: Feat-0004
feature: pii-detection-redaction-rbac
type: backend-service
domain: pii-compliance
criticality: high
touched_paths:
  - ingestion/pii/
  - ingestion/metadata/
  - workers/pii_worker.py
depends_on: [Feat-0002, Feat-0001]
consumed_by: [Feat-0006, Feat-0003, Feat-0005]
implements: []
tags: [pii, rbac, hipaa, compliance]
---

## Overview

| Type | Package | Path | Domain | Last updated |
|---|---|---|---|---|
| backend-service | (none) | `ingestion/pii/`, `ingestion/metadata/`, `workers/pii_worker.py` | pii-compliance | 2026-09-05 |

## Domain Purpose

Detects and redacts PHI/PII in every chunk before it can reach an embedding model, a keyword
index, or an LLM, and stamps each chunk with the RBAC metadata (`allowed_roles`) that later
query-time access control depends on. This is the HIPAA-compliance chokepoint of the whole
pipeline — nothing downstream is supposed to see unredacted patient data.

## Entities Owned

| Entity | Represents |
|---|---|
| [`pii_entity_index` / `pii_doc_index`](../../Schemas/schemas.md#pii_entity_index--pii_doc_index-non-relational--json-files) | Hash-only index of detected PII entities → chunk/document ids, for query-time Top-D candidate expansion |
| `allowed_roles` field of [`chunk_metadata`](../../Schemas/schemas.md#chunk_metadata-non-relational--chroma--keyword-index-document-metadata) | Stamped here from department, consumed by Feat-0005's RBAC filter |

**`ingestion/metadata/rbac_policy.py` is the single source of truth for department↔role
policy** — its own docstring says so, and no other file in the repo hardcodes a role list.

## Invariants

- Plaintext PII never touches disk — chunks arrive inline in the queue message and are only
  ever written to disk *after* redaction (`workers/pii_worker.py:4,34-35,94`).
- Query-time masking (`apply_role_mask()`) must run *after* RBAC filtering, never before — the
  non-negotiable call order documented in `security/access_control.py:8-9` and
  `search/pipeline.py:7-9`. **See Feat-0005's Known Error Scenarios — this order is currently
  violated in the live query path.**
- A chunk's `allowed_roles` is set once at ingest from `get_allowed_roles(department)` and never
  updated — if a department's role policy changes later, already-ingested chunks keep the old
  policy (open question below).
- Masking produces a copy of a chunk, never mutates the original (`role_based_masking.py:116`).

## Access Control

**Model**: Role-based (RBAC) — department drives an `allowed_roles` list; role membership is
the only test, never per-user ownership.

| Action | Access Condition | Enforced In |
|---|---|---|
| Chunk stamped with `allowed_roles` at ingest | department ∈ known set | `ingestion/metadata/rbac_policy.py:get_allowed_roles()` (raises `ValueError` on unknown department — "fail loudly", per its own comment) |
| Query-time visibility | `role` ∈ chunk's `allowed_roles`, or `role == "admin"` | `security/access_control.py:filter_results_by_role()` — owned by Feat-0005, but the policy data originates here |
| Query-time entity masking | role-specific mask set | `ingestion/pii/role_based_masking.py:apply_role_mask()` |

Department → allowed roles (`ingestion/metadata/rbac_policy.py:_DEPARTMENT_ROLES`):

| Department | Allowed Roles |
|---|---|
| general | doctor, nurse, admin, researcher |
| cardiology | doctor, nurse, cardiologist, researcher |
| billing | billing, admin |
| radiology | doctor, nurse, radiologist, admin |
| oncology | doctor, nurse, admin |

Role masking tiers (`ingestion/pii/role_based_masking.py`):

| Role | Masked (never sees) |
|---|---|
| researcher | PATIENT_NAME, MRN, DATE, PHONE, EMAIL, SSN, PATIENT_DEMOGRAPHICS |
| admin | all of the above **plus** ICD10, LAB_VALUE, VITAL_SIGN, MEDICATION, DOSAGE_FREQ, DRUG_DOSE |
| billing | all of the above except it can see billing-relevant fields, masks clinical content |
| doctor / nurse / cardiologist | unmasked (full redacted text) |

## Business Rules

| ID | Rule | Enforced In | Severity |
|---|---|---|---|
| BR-01 | Only `doctor`/`nurse`/`admin` may submit documents for ingestion | `ingestion/metadata/rbac_policy.py:38-40`, checked at `app/main.py:168` | CRITICAL |
| BR-02 | Every chunk must carry `allowed_roles` derived from its department | `workers/pii_worker.py:72` | CRITICAL |
| BR-03 | Unknown department → ingest fails loudly, never produces a zero-access chunk | `ingestion/metadata/rbac_policy.py:30-31` | HIGH |
| BR-04 | All PII redacted (type-labeled placeholders) before embedding/indexing | `workers/pii_worker.py:58`, `ingestion/pii/pii_redactor.py:24-38` | CRITICAL |
| BR-05 | PHI values encrypted before persistence | `workers/pii_worker.py:47-56` (Feat-0001's `encrypt()`) | HIGH |
| BR-06 | PERSON/PATIENT_NAME entity hash hits expand to *every* chunk in the same document at query time; other entity types (MRN, DATE, PHONE, EMAIL, SSN) match only their own chunk | `indexing/pii_entity_index.py:71-129` | MEDIUM |
| BR-07 | Clinical false positives suppressed: ICD-10 codes, dosage frequencies ("every 6 hours"), first-name-as-city are never tagged as PII | `ingestion/pii/pii_detector.py:55-84` | MEDIUM |
| BR-08 | Researcher/admin/billing never see certain entity types at query time (see Access Control table) | `ingestion/pii/role_based_masking.py:25-75` | CRITICAL |

## External Integrations

| System | Trigger | What Happens |
|---|---|---|
| Presidio (optional) | PII detection call | Used if installed; falls back to regex-only patterns if not (`ingestion/pii/pii_detector.py:104-137`) — a silent capability downgrade |
| PiiWorker (async) | `pii_queue` message (from Feat-0002's ChunkingWorker) | Detects PII → registers entity hashes → encrypts entity values → redacts text → stamps RBAC metadata → writes `redacted_chunks.json` → `DocStatus: PII_PROCESSED` → pushes to `extraction_queue` (Feat-0006) |

## Safe vs Dangerous Changes

### Safe
- Adding a new department to `_DEPARTMENT_ROLES` with its own role list.
- Adding a new PII entity type to the detector, provided masking tiers are updated to cover it.

### Dangerous — Requires Review
| Change | Risk | Why |
|---|---|---|
| Changing `_DEPARTMENT_ROLES` for an existing department | Retroactive access change without retroactive effect | Already-ingested chunks keep their old `allowed_roles` — a policy tightening does not automatically re-restrict old data (see open question) |
| Removing a role from `_ROLE_MASK_MAP` tiers | PHI exposure | This is the only enforcement point for query-time entity masking |
| Changing queue message shape consumed from `pii_queue` or produced to `extraction_queue` | Breaks pipeline | Feat-0002 and Feat-0006 depend on the exact shape |

### Human Escalation Required
- Any relaxation of BR-01/BR-04/BR-08 — these are the core HIPAA guarantees of the whole system.

## Known Error Scenarios

| Scenario | Error Returned | Root Cause |
|---|---|---|
| Unknown department | `ValueError` | `get_allowed_roles()` — fails loudly by design |
| Presidio unavailable | Silent fallback to regex-only detection | `ImportError` caught, logged |
| Encryption unavailable | Silent fallback to plaintext (see Feat-0001) | `security/encryption.py` degradation |

## Testing Expectations

- `tests/unit/test_researcher_role.py` covers the researcher-role masking happy path.
- No test found for: empty `allowed_roles` for a department, missing/`None` `entity_types` at
  query time, or Presidio silently failing on all sentences. *(Open question, carried forward
  from the scan.)*

## Forbidden Patterns

- Never hardcode a role or department list outside `ingestion/metadata/rbac_policy.py` — it is
  the explicitly-documented single source of truth.
- Never call `apply_role_mask()` before `filter_results_by_role()` — the non-negotiable order
  exists because masking assumes the chunk has already passed the RBAC check.

## Key Files

- `ingestion/metadata/rbac_policy.py` — department↔role policy, single source of truth
- `ingestion/metadata/metadata_builder.py` — chunk metadata assembly (**duplicated inline** in
  `workers/pii_worker.py:62-73` — same logic, two places; a future edit to one and not the
  other would silently diverge)
- `workers/pii_worker.py` — orchestrates detect → encrypt → redact → stamp → persist → advance status
- `ingestion/pii/pii_detector.py` — Presidio + regex detection, false-positive suppression
- `ingestion/pii/pii_redactor.py` — span replacement with type labels
- `ingestion/pii/role_based_masking.py` — query-time role-tiered entity masking
- `indexing/pii_entity_index.py` — hash-only PII index for Top-D candidate expansion

## Context Routing

| Feature | Load when |
|---|---|
| Feat-0004 (this file) | Touching PII detection, redaction, RBAC policy, or role masking |

| Workflow | Sections to load |
|---|---|
| Adding a department/role | Access Control, Business Rules (BR-01–03) |
| Debugging a PHI-exposure report | Invariants, Access Control, Known Error Scenarios |
| Changing masking rules | Access Control (masking tiers), Forbidden Patterns |

## Open Questions

- *Open question: if a department's role policy changes (`_DEPARTMENT_ROLES` edited), are
  already-ingested chunks re-stamped, or do they silently keep the old `allowed_roles` forever?*
- *Open question: `metadata_builder.py:build_chunk_metadata()` and the inline logic in
  `workers/pii_worker.py:62-73` implement the same thing twice — is the standalone function
  dead code, or is duplication intentional for some reason not visible in this scan?*
