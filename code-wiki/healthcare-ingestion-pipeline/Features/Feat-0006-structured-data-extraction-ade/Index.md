---
feat_id: Feat-0006
feature: structured-data-extraction-ade
type: backend-service
domain: structured-extraction
criticality: medium
touched_paths:
  - workers/extraction_worker.py
  - llm/ade_model.py
  - llm/ade_api.py
  - mlx_adapter/
depends_on: [Feat-0004, Feat-0003]
consumed_by: [Feat-0002]
implements: []
tags: [llm, extraction, mlx, on-device-inference]
---

## Overview

| Type | Package | Path | Domain | Last updated |
|---|---|---|---|---|
| backend-service (worker + local inference server pair) | (none) | `workers/extraction_worker.py`, `llm/ade_api.py`, `llm/ade_model.py`, `mlx_adapter/` | structured-extraction | 2026-09-05 |

## Domain Purpose

Runs a fine-tuned local LLM ("ADE" = automated document extraction) over each redacted sentence
to pull out structured drug-name / adverse-effect pairs, so downstream search can answer
questions like "which patients had an adverse reaction to X" without re-parsing free text.

**Deployment shape**: two processes, not one — `extraction_worker` (a queue consumer, part of
the same pipeline as every other worker) calls `ade_api` (a separate `uvicorn` server on
`localhost:8001`) over plain HTTP. Treat them as one feature for code changes: the worker has no
purpose without the API running, and the API has no other caller.

## Invariants

- Extraction always runs on already-redacted chunk text — it never sees raw PHI.
- The model (`Qwen2.5-7B-Instruct`, 4-bit quantized, + QLoRA rank-8/alpha-16 adapter per
  `mlx_adapter/adapter_config.json`) is loaded exactly once at `ade_api` startup, via a FastAPI
  lifespan context manager.
- If `ade_api` is unreachable, extraction is skipped for that document (not fatal) — the
  document still reaches `EXTRACTED` status, just with no drug/ADE fields populated.

## Access Control

**Model**: None — `/extract` and `/health` are internal, unauthenticated endpoints, reachable
only from `localhost:8001` in the deployed topology. This is appropriate for a same-host
service-to-service call, but it means **anything else on the same host can also call it** — no
process isolation was found.

## Business Rules

| ID | Rule | Enforced In | Severity |
|---|---|---|---|
| BR-01 | Extracted drug/ADE values of `"none"`, `"null"`, or empty are filtered out | `workers/extraction_worker.py:77-80` | MEDIUM |
| BR-02 | Extracted drugs/ADEs deduped and sorted before storage | `workers/extraction_worker.py:72-82` | LOW |
| BR-03 | Sentences under 5 characters are skipped | `workers/extraction_worker.py:40` | LOW |
| BR-04 | Model output capped at 150 tokens; non-JSON output stored raw rather than discarded | `llm/ade_model.py:60-90` | MEDIUM |
| BR-05 | `ade_api` unreachable → extraction skipped, not a pipeline failure | `workers/extraction_worker.py:61-66` | MEDIUM |
| BR-06 | Empty/whitespace sentence → HTTP 422 from `/extract` | `llm/ade_api.py:56-57` | LOW |
| BR-07 | Inference timeout: 30 seconds per sentence | `workers/extraction_worker.py` (`requests.post(timeout=...)`) | MEDIUM |

## External Integrations

| System | Trigger | What Happens |
|---|---|---|
| `ade_api` (local `uvicorn`, port 8001) | `POST /extract` per sentence | Runs MLX inference, returns `{drug, adverse_effect, sentence, raw}` |
| ExtractionWorker (async) | `extraction_queue` message (from Feat-0004's PiiWorker) | Splits chunk text into sentences (spaCy, falls back to line-splitting) → calls `/extract` per sentence → merges results into chunk metadata → `DocStatus: EXTRACTED` → pushes to `embedding_queue` **and** `keyword_queue` (Feat-0002) |

## API Endpoints

| Method | Path | Auth | Who Uses It | Description |
|---|---|---|---|---|
| POST | `/extract` | none (localhost-only in practice) | `workers/extraction_worker.py` | `{"sentence": str}` → structured drug/ADE extraction |
| GET | `/health` | none | operational monitoring | `{"status": "ok", "model_loaded": bool}` |

## Safe vs Dangerous Changes

### Safe
- Adjusting the token cap or timeout values.
- Adding a new extracted field to the JSON schema, provided `extraction_worker.py`'s merge logic is updated to match.

### Dangerous — Requires Review
| Change | Risk | Why |
|---|---|---|
| Swapping the base model or adapter | Extraction quality regression with no automated signal | No test/eval harness in `tests/unit/` validates extraction accuracy; only `AiHarness/evals/` (a separate, manual-feeling eval harness) touches this |
| Changing the `/extract` request/response shape | Breaks the worker | The two processes share an implicit contract with no shared DTO/schema file |

## Known Error Scenarios

| Scenario | Error Returned | Root Cause |
|---|---|---|
| `ade_api` down | Extraction silently skipped for the document | `ConnectionError` caught, warning logged |
| Model output isn't valid JSON | Stored in a `raw` field, `drug`/`adverse_effect` both `None` | `llm/ade_model.py` parse fallback |
| Model not loaded when `/extract` is called | `RuntimeError` | Should only happen if the server is hit before its own startup completes |

## Testing Expectations

- No unit tests found in `tests/unit/` for this feature. `AiHarness/evals/` contains
  eval-harness cases (drug/ADE extraction quality) but that's a different mechanism from
  `pytest` — see `.claude/skills/backend-test/SKILL.md` for how this project actually tests.

## Forbidden Patterns

- Never call `/extract` with unredacted text — this stage sits after Feat-0004 in the pipeline
  specifically so the model never sees raw PHI.

## Key Files

- `workers/extraction_worker.py` — queue orchestration, sentence splitting, result merging
- `llm/ade_api.py` — FastAPI server, `/extract` and `/health`
- `llm/ade_model.py` — MLX model load + inference
- `mlx_adapter/adapter_config.json` — LoRA hyperparameters (rank=8, alpha=16.0, scale=2.0)
- `scripts/convert_to_mlx.py` — one-time setup: quantizes the base model and converts the PEFT adapter to MLX format (not part of the runtime pipeline)

## Context Routing

| Feature | Load when |
|---|---|
| Feat-0006 (this file) | Touching structured extraction, the ADE model/adapter, or the extraction-worker↔ade_api contract |

| Workflow | Sections to load |
|---|---|
| Debugging missing drug/ADE data | External Integrations, Known Error Scenarios |
| Changing the model/adapter | Safe vs Dangerous Changes, Testing Expectations |

## Open Questions

- *Open question: extracted drug/ADE values themselves are never logged — only counts — making
  it hard to audit extraction accuracy in production. Is this intentional (avoiding PHI in logs)
  or an observability gap?*
- *Open question: which W&B hyperparameter-sweep version of the adapter is actually deployed?
  Nothing in the repo versions this beyond the adapter directory name
  (`qlora-adapter-happy-sweep-1_v0`, from `app/config.py`).*
