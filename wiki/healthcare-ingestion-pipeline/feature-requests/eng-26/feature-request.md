---
title: "Add missing packages to requirements.txt: pydicom, python-dotenv, requests"
slug: eng-26
status: active
last_updated: 2026-10-15
linear_issue: "https://linear.app/flightdecktest-2/issue/ENG-26/add-missing-packages-to-requirementstxt-pydicom-python-dotenv-requests"
proposed_by: agent
identity_confirmed: false
---

## Current State

Requested in [ENG-26](https://linear.app/flightdecktest-2/issue/ENG-26/add-missing-packages-to-requirementstxt-pydicom-python-dotenv-requests). Alignment agreed the spec under Requirements, as the ticket said when alignment agreed it.

## Key Facts

Nothing recorded yet.

## Requirements

Repository: [https://github.com/sanidhyagupta-web/PR-Review](<https://github.com/sanidhyagupta-web/PR-Review>)

### Problem

Three packages the code imports directly are not listed in `requirements.txt`, so `pip install -r requirements.txt` gives an environment where parts of the app and the tests cannot import:

| Package | Imported by |
| -- | -- |
| `pydicom` | `ingestion/parsers/dicom_parser.py`, `tests/unit/test_dicom_parser.py` |
| `python-dotenv` (imported as `dotenv`) | `app/config.py`, which almost every module loads through `settings` |
| `requests` | `ingestion/ocr/ocr_quality.py`, `workers/extraction_worker.py` |

`requests` may arrive today as a dependency of another package, but nothing guarantees it.

### What to do

Add the three packages to `requirements.txt` with a minimum version each, in the section that fits, in the file's existing style (one package per line, a short comment where it helps).

### Summary

Work-Type: Bug

Correct `requirements.txt` so every third-party distribution directly imported under the stated audit scope is explicitly listed rather than supplied only transitively. Add these nine requirement lines:

* `pydicom>=2.4`
* `python-dotenv>=1.0`
* `requests>=2.32.4`
* `numpy>=1.26`
* `scipy>=1.11`
* `anthropic>=0.40`
* `spacy>=3.7.2`
* `pydantic>=2.0`
* `botocore>=1.34`

### Context

The repository directly imports all nine distributions but does not list them in `requirements.txt`. `pydicom` and `anthropic` are not installed by another current requirement. The other seven may currently arrive transitively, but that does not satisfy this ticket because a transitive dependency can disappear when its provider changes.

Severity: Medium.

Material impact:

* Without `pydicom`, DICOM ingestion fails and `tests/unit/test_dicom_parser.py` cannot be collected, preventing a clean setup from collecting the unit-test suite.
* Without `anthropic`, Claude answers on the search page and the Claude Vision OCR fallback are unavailable even when `ANTHROPIC_API_KEY` is configured. The code catches the import failure, so the feature degrades rather than reporting a missing package to the user.
* The seven transitively installed packages are at risk if current providers change their dependency trees.
* The PDF and text pipeline, Streamlit UI, and FastAPI app currently work. The repository has no deployment, so no deployed environment is affected.

The repository has no `code-wiki/` or `wiki/` documentation.

### User Flow

Current reproduction on macOS Apple Silicon with Python 3.12, from a clean checkout of `main`:

```sh
python3.12 -m venv /tmp/eng26
. /tmp/eng26/bin/activate
pip install -r requirements.txt
python -c "import pydicom"
python -c "import anthropic"
pytest --collect-only -q tests/unit
```

Before the fix, both explicit imports raise `ModuleNotFoundError`, and `tests/unit/test_dicom_parser.py` fails collection because `pydicom` is unavailable.

After the fix, run the same steps in a fresh virtual environment. Both imports must succeed, and all three test files under `tests/unit` must collect without `ImportError`. Making the collected tests pass is not part of this ticket.

### Error Paths

* If package installation itself fails, retain pip's existing failure behavior; changing installation error handling is out of scope.
* The dependency audit must include imports inside functions as well as module-level imports. No additional unlisted third-party distribution was found in the stated directories beyond the nine specified above.
* A package available only as another package's transitive dependency does not satisfy the audit.

### Acceptance Criteria

1. GIVEN the existing `requirements.txt`, WHEN this ticket is implemented, THEN it gains exactly these nine lines with the stated minimum versions: `pydicom>=2.4`, `python-dotenv>=1.0`, `requests>=2.32.4`, `numpy>=1.26`, `scipy>=1.11`, `anthropic>=0.40`, `spacy>=3.7.2`, `pydantic>=2.0`, and `botocore>=1.34`.
2. GIVEN the existing requirement lines, WHEN the nine lines are added, THEN no pre-existing line in `requirements.txt` changes.
3. GIVEN Python 3.12 on macOS Apple Silicon and a clean checkout, WHEN a fresh virtual environment installs `requirements.txt`, THEN `python -c "import pydicom"` succeeds.
4. GIVEN that same clean environment, WHEN `python -c "import anthropic"` runs, THEN it succeeds.
5. GIVEN that same clean environment, WHEN `pytest --collect-only -q tests/unit` runs, THEN all three unit-test files collect without `ImportError`; passing the tests is not required by this ticket.
6. GIVEN the Python files under `app/`, `db/`, `ingestion/`, `indexing/`, `llm/`, `queues/`, `search/`, `security/`, `storage/`, `workers/`, and `tests/`, WHEN their module-level and function-local imports are audited, THEN every directly imported third-party distribution has its own line in `requirements.txt`; transitive availability does not count.
7. GIVEN import names that differ from distribution names, WHEN the audit is documented, THEN the providing distributions are identified correctly, including `dotenv` → `python-dotenv`, `fitz` → `pymupdf`, and `PIL` → `Pillow`.
8. GIVEN the completed dependency audit, WHEN the pull request is written, THEN it lists each checked third-party import name and the requirement line that provides it.

### Existing System Behaviour

`requirements.txt` has 49 lines and contains none of the nine new requirement lines.

Relevant direct imports include:

* `pydicom`: `ingestion/parsers/dicom_parser.py` and `tests/unit/test_dicom_parser.py`.
* `dotenv`: `app/config.py`.
* `requests`: `ingestion/ocr/ocr_quality.py` and `workers/extraction_worker.py`.
* `numpy`, `scipy`, and `anthropic`: function-local imports in `ingestion/ocr/tesseract_ocr.py`.
* `anthropic`: function-local import in `llm/claude_client.py`.
* `spacy`: `workers/extraction_worker.py`.
* `pydantic`: `llm/ade_api.py`.
* `botocore`: `app/main.py` and `storage/s3_client.py`.

There are three test files under `tests/unit`: `test_bulk_ingestion.py`, `test_researcher_role.py`, and `test_dicom_parser.py`.

### Scope Boundaries

In scope:

* Add exactly the nine specified direct requirement lines.
* Audit module-level and function-local third-party imports under `app/`, `db/`, `ingestion/`, `indexing/`, `llm/`, `queues/`, `search/`, `security/`, `storage/`, `workers/`, and `tests/`.
* Document each checked import name and its providing requirement line in the pull request.

Out of scope:

* Changing any pre-existing line in `requirements.txt`.
* Auditing directories outside the stated scope, including `.github/`, `AiHarness/`, and `scripts/`.
* Making unit tests pass beyond collecting them without `ImportError`.
* Changing runtime fallback or error-handling behavior.
* Adding deployment work; the repository has no deployment.

### Reference Documents

* `requirements.txt`
* `app/config.py`
* `app/main.py`
* `ingestion/parsers/dicom_parser.py`
* `ingestion/ocr/ocr_quality.py`
* `ingestion/ocr/tesseract_ocr.py`
* `llm/claude_client.py`
* `llm/ade_api.py`
* `storage/s3_client.py`
* `workers/extraction_worker.py`
* `tests/unit/test_dicom_parser.py`

No repository `code-wiki/` or `wiki/` pages are present.

### Round log

* Round 1, questions: classified as a bug; confirmed the three named omissions and imports; found additional direct imports that make the audit criterion conflict with the three-package scope; minimum versions, reproduction steps, and severity remain open.
* Round 2, aligned: fixed all nine minimum versions, broadened scope to every direct third-party import in the stated directories, defined clean-environment reproduction and collection checks, and recorded severity and affected workflows.

## Business Rules

Nothing recorded yet.

## Decisions

| Date | Title | Type | Ticket |
|---|---|---|---|

## Evidence

Nothing recorded yet.

## Open Questions

- Is this the right name and boundary for this work? Keep the folder name `eng-26`: a later alignment of ENG-26 updates the page there. Set `identity_confirmed: true` once a person has answered this, and delete the question only after it is answered.

**Resolved:**

Nothing recorded yet.

## Risks / Rejected Approaches

Nothing recorded yet.

## Relationships

**Depends On:** Nothing recorded yet.

**Related:** Nothing recorded yet.
