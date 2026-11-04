---
title: "Write a README with setup, run and test instructions"
slug: eng-28
status: active
last_updated: 2026-10-15
linear_issue: "https://linear.app/flightdecktest-2/issue/ENG-28/write-a-readme-with-setup-run-and-test-instructions"
proposed_by: agent
identity_confirmed: false
---

## Current State

Requested in [ENG-28](https://linear.app/flightdecktest-2/issue/ENG-28/write-a-readme-with-setup-run-and-test-instructions). Alignment agreed the spec under Requirements, as the ticket said when alignment agreed it.

## Key Facts

Nothing recorded yet.

## Requirements

Repository: [https://github.com/sanidhyagupta-web/PR-Review](<https://github.com/sanidhyagupta-web/PR-Review>)

### Problem

`README.md` holds only two headings (`# PR-Review` and `# HealthCare`). Someone new to the repository cannot tell what it does or how to run it without reading the code.

### What to do

Replace it with a README that covers, briefly:

1. **What it is:** a healthcare document ingestion and semantic search pipeline. Uploads (PDF, scanned PDF, DICOM, text) go through parsing, OCR, Markdown conversion, chunking, PII detection and masking, embedding, and keyword indexing, and are then searchable through a Streamlit UI and a FastAPI endpoint. Take the stages from the code (`workers/`, `run.py`), not from this list.
2. **Setup:** Python version, creating a virtual environment, `pip install -r requirements.txt`, the system tools OCR needs (Tesseract, Poppler for `pdf2image`), and the optional spaCy model named in `requirements.txt`.
3. **Configuration:** that settings are read from `.env` through `app/config.py`, with a table of the environment variables `app/config.py` reads and their defaults.
4. **Running:** the `run.py` options (from its docstring), and how to start the Streamlit UI (`ui/streamlit_app.py`) and the FastAPI app (`app/main.py`).
5. **Tests:** how to run `pytest`.
6. **Layout:** one line per top-level folder.

### Summary

Work-Type: Feature

Replace the two-line `README.md` with a concise onboarding guide for the repository’s healthcare document-ingestion and semantic-search system. The guide must be grounded in current source and cover purpose, setup, configuration, running the pipeline/UI/API, tests, and repository layout.

Document Python 3.12 only, matching `.github/workflows/claude-review.yml`; do not claim support for another Python version. Provide the full setup path for macOS on Apple Silicon. For Linux and Intel Mac, provide a working path that installs every requirement except `mlx-lm`, and state that the ADE extraction server cannot run on those platforms. The rest of the pipeline can continue without ADE: `workers/extraction_worker.py` logs a warning and skips extraction when no service responds at `ADE_API_URL`, whose source default is `http://localhost:8001`.

### Context

The repository currently provides no usable onboarding documentation beyond its name. Source confirms pipeline workers for parsing/OCR, Markdown conversion, chunking, PII handling, extraction, embeddings, and keyword indexing; Streamlit and FastAPI entry points; `.env` loading; PDF/text/DICOM handling; and an Apple-Silicon-specific `mlx-lm` dependency.

A fresh-environment setup is not currently self-consistent: `requirements.txt` does not declare `python-dotenv`, `pydicom`, or `requests`, although current source/tests import them. `run.py` configures `logs/ingestion.log` before ensuring `logs/` exists. Upload and ingestion paths use S3 and therefore require applicable configuration and credentials.

### User Flow

A newcomer reads the README to understand the system, creates and activates a Python 3.12 virtual environment, installs platform prerequisites and Python dependencies, configures `.env`, launches the desired process using a repository-valid command, and runs the test suite with `pytest`.

On macOS Apple Silicon, the setup installs all of `requirements.txt`. On Linux and Intel Mac, it installs every requirement except `mlx-lm` and explains that the ADE server is unavailable there.

Immediately after `pip install -r requirements.txt`—or after the equivalent non-Apple-Silicon install excluding `mlx-lm`—the README must direct users to run:

```sh
pip install pydicom python-dotenv requests
```

Add a one-line explanation that current code imports these packages but `requirements.txt` does not list them yet.

Before first launch, direct users to create the log directory with `mkdir -p logs`, install Tesseract and Poppler for OCR, and install the spaCy model named in `requirements.txt`.

The running section is launch-focused. Each documented command must start its process and cover:

* `python run.py` and only the options supported by its source/docstring.
* The Streamlit app at `ui/streamlit_app.py`.
* The FastAPI app at `app/main.py`.
* The optional Apple-Silicon-only ADE server with `uvicorn llm.ade_api:app --port 8001`.

### Error Paths

Call out that the `mlx-lm` requirement and ADE server are Apple-Silicon-only; do not change that dependency. Linux and Intel Mac users omit `mlx-lm`, cannot run the ADE server, and can still run the remaining pipeline with extraction skipped when ADE is unavailable.

The configuration table must list every environment variable read by `app/config.py`, with its source default. For the S3/KMS settings (`S3_BUCKET`, `KMS_KEY_ID`, and `AWS_*`), `ANTHROPIC_API_KEY`, and `SAPLING_API_KEY`, explain what each setting is used for and what current code does when it is blank. Do not provide an AWS account-setup walkthrough.

Handle the current undeclared imports and absent `logs/` directory through the prerequisite steps in User Flow. Do not fix them in this ticket.

### Acceptance Criteria

 1. GIVEN the current pipeline source in `workers/` and `run.py`, WHEN the README describes the system and its stages, THEN the description matches those sources rather than assuming the supplied stage list is authoritative.
 2. GIVEN the supported environment, WHEN setup is documented, THEN the README specifies Python 3.12, virtual-environment creation and activation, Tesseract, Poppler, the spaCy model named in `requirements.txt`, and the applicable Python dependency-install path for macOS Apple Silicon or Linux/Intel Mac.
 3. GIVEN macOS Apple Silicon, WHEN dependencies are documented, THEN the README includes `pip install -r requirements.txt` followed immediately by `pip install pydicom python-dotenv requests` and explains why the supplemental line is currently required.
 4. GIVEN Linux or Intel Mac, WHEN dependencies are documented, THEN the README provides a working installation path for every `requirements.txt` entry except `mlx-lm`, includes the supplemental package line, and states that ADE cannot run on that platform.
 5. GIVEN `app/config.py`, WHEN configuration is documented, THEN the README explains root `.env` loading and lists all 12 environment variables read there with their source defaults.
 6. GIVEN the named S3/KMS and API-key settings, WHEN configuration is documented, THEN the README explains their purpose and current blank-value behavior without walking through AWS account setup.
 7. GIVEN `run.py`, WHEN pipeline setup and running are documented, THEN the README includes `mkdir -p logs`, `python run.py`, and only the runner options present in source.
 8. GIVEN `ui/streamlit_app.py`, `app/main.py`, and `llm/ade_api.py`, WHEN running instructions are documented, THEN they provide valid launch commands for Streamlit, the main FastAPI app, and the Apple-Silicon-only optional ADE server.
 9. GIVEN ADE is unavailable at `ADE_API_URL`, WHEN the fallback is documented, THEN the README states that extraction is skipped with a warning while processing continues.
10. GIVEN the current test suite, WHEN test instructions are documented, THEN they provide a repository-valid `pytest` command after all prerequisites required by this setup contract.
11. GIVEN the settled layout scope, WHEN repository layout is documented, THEN each listed checked-in top-level directory receives exactly one descriptive line, while generated or ignored directories such as `logs/` and `.venv/` are omitted.
12. Every command documented in the README must exist and work under its stated platform/setup conditions; do not document an absent option or script.
13. Only `README.md` changes.

### Existing System Behaviour

`README.md` contains only `# PR-Review` and `# HealthCare`. `run.py` documents default seeding, `--seed`, and `--workers`; it creates a `logging.FileHandler` for `logs/ingestion.log` before startup without creating the directory. `ui/streamlit_app.py`, `app/main.py`, and `llm/ade_api.py` are the requested UI, primary API, and optional ADE entry points.

`app/config.py` loads a root `.env` and reads 12 named environment variables with defaults. `workers/extraction_worker.py` separately reads `ADE_API_URL`, defaulting to `http://localhost:8001`, catches connection failures, records blank extraction values, and continues to embedding and keyword queues.

`requirements.txt` names OCR packages, `pdf2image`, the `en_core_web_lg` spaCy model command, pytest, and Apple-Silicon-specific `mlx-lm`, but it declares no supported Python version and omits `pydicom`, `python-dotenv`, and `requests`, which current source/tests import directly.

### Scope Boundaries

Only `README.md` may change. Do not modify dependencies, source, configuration, tests, directories, or platform compatibility. Do not invent commands, scripts, options, settings, or pipeline stages absent from the repository.

Layout covers these checked-in top-level directories, one line each: `.claude`, `.github`, `AiHarness`, `Dataset`, `Typed`, `app`, `code-wiki`, `data`, `db`, `evaluation`, `indexing`, `ingestion`, `llm`, `mlx_adapter`, `monitoring`, `queues`, `scripts`, `search`, `security`, `storage`, `tests`, `ui`, `wiki`, and `workers`. Leave out generated or gitignored directories such as `logs/` and `.venv/`.

End-to-end AWS account provisioning, making ingestion/search operational without valid external configuration, fixing missing requirements, creating `logs/` in source, and adding non-Apple ADE support are out of scope.

### Reference Documents

* `README.md`
* `requirements.txt`
* `.github/workflows/claude-review.yml`
* `app/config.py`
* `app/main.py`
* `run.py`
* `ui/streamlit_app.py`
* `llm/ade_api.py`
* `workers/extraction_worker.py`
* `workers/`
* `ingestion/validator.py`
* `ingestion/parsers/doc_type_detector.py`
* `tests/`
* `code-wiki/healthcare-ingestion-pipeline/Architecture/Overview.md`

### Round log

* Round 1, questions: classified as a feature and verified against source; supported runtime/platform, fresh-setup behavior, run prerequisites, and layout scope remained open.
* Round 2, aligned: incorporated the Python/platform contract, supplemental dependencies, launch-only prerequisites and commands, ADE fallback, and exact checked-in layout scope; rechecked all answered claims against source.

## Business Rules

Nothing recorded yet.

## Decisions

| Date | Title | Type | Ticket |
|---|---|---|---|

## Evidence

Nothing recorded yet.

## Open Questions

- Is this the right name and boundary for this work? Keep the folder name `eng-28`: a later alignment of ENG-28 updates the page there. Set `identity_confirmed: true` once a person has answered this, and delete the question only after it is answered.

**Resolved:**

Nothing recorded yet.

## Risks / Rejected Approaches

Nothing recorded yet.

## Relationships

**Depends On:** Nothing recorded yet.

**Related:** Nothing recorded yet.
