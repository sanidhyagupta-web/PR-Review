---
name: post-checks
description: Run post-implementation verification — tests, code quality, and build checks across affected repositories.
disable-model-invocation: true
---

# Post-Implementation Checks

Run targeted integration tests and verify the implementation across all affected repositories.

## Steps

### 1. Verify Completeness
Read `execution-state.md`. Check all tasks are complete. If any are incomplete or blocked, list them and ask the user how to proceed.

### 2. Verify New Tests Exist
Read the Testing Strategy from `implementation-plan.md`. Verify each planned test file was created. Note any missing tests.

### 3. Read Verification Commands
For each affected repository, read its CLAUDE.md for the testing and code quality commands.

### 4. Run Backend Checks
This is a single-repo Python project with no configured formatter, linter, or type-checker (no
`ruff`/`flake8`/`black`/`mypy` config present) and no compile/build step. Run only the affected
test files, not the full suite:
```bash
pytest tests/unit/test_<affected_area>.py
```

### 5. Run Frontend Checks
The "frontend" is the Streamlit app under `ui/` (plain Python, no bundler/build step, no
lint/type-check tooling). There is no separate frontend test runner — Streamlit component tests
(via `streamlit.testing.v1.AppTest`, if any exist for the affected page) run through the same
`pytest` invocation as the backend:
```bash
pytest tests/unit/test_<affected_ui_area>.py
```

### 6. Run Ops Validation (if applicable)
Validate any modified infrastructure files (Helm charts, Terraform, YAML).

### 7. Generate Verification Summary
Cover: services/apps tested, test results, code quality results, build results, warnings.

### 8. Update Execution State
- All pass: set status to `CHECKS_COMPLETE`
- Any fail: set status to `CHECKS_FAILED` and log failures

## Rules
- Only test affected services/apps — not the full suite
- Report failures clearly with file paths, test names, error messages
- Do NOT modify code in this step — only check and report
- If checks fail, inform the user and wait for instructions
