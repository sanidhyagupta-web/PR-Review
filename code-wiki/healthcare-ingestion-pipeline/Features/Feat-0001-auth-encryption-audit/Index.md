---
feat_id: Feat-0001
feature: auth-encryption-audit
type: shared-library
domain: security-infrastructure
criticality: high
touched_paths:
  - security/auth.py
  - security/encryption.py
  - security/audit_logger.py
depends_on: []
consumed_by: [Feat-0003, Feat-0004, Feat-0007]
implements: []
tags: [auth, encryption, audit, hipaa]
---

## Overview

| Type | Package | Path | Domain | Last updated |
|---|---|---|---|---|
| shared-library | (none) | `security/auth.py`, `security/encryption.py`, `security/audit_logger.py` | security-infrastructure | 2026-09-05 |

## Domain Purpose

Provides the three security primitives every other feature builds on: session login for the
Streamlit UI, field-level PHI encryption, and the audit trail every ingest/query/redaction event
is logged to. **Explicitly labeled a prototype in its own source** (`security/auth.py:6`), and
its weaknesses are load-bearing facts for anyone reviewing this system's HIPAA posture, not
incidental cleanup items.

## Entities Owned

| Entity | Represents |
|---|---|
| [`audit_log`](../../Schemas/schemas.md#audit_log) | Every logged event, read via `get_audit_trail()`; **written into** by three other features, this one only owns the read/write API |
| `_USERS` (in-memory dict, `security/auth.py:7-38`) | The entire user store — 5 hardcoded accounts, no persistence, no admin UI to add more |

## Invariants

- `is_authenticated()` is the sole gate for every Streamlit page — nothing renders before it
  returns `True` (enforced at `ui/streamlit_app.py:19-22`, owned by Feat-0007).
- Every `log_event()` call writes to *both* a JSON-lines file and the `audit_log` DB table; a DB
  failure is caught and logged as a warning, never raised (`security/audit_logger.py:48-49`) —
  so audit writes are effectively best-effort against the DB, guaranteed against the file.
- PHI values are encrypted before persistence (`workers/pii_worker.py`, owned by Feat-0004) —
  but **the decrypt path defined in `security/encryption.py:53-62` has no call site anywhere in
  the repo.** Encryption here is write-only in practice.

## Access Control

**Model**: Session-based, in-memory, role-carrying. `login()` checks a SHA-256 hash against the
hardcoded `_USERS` dict and, on success, populates `st.session_state` with `role`/`department`/
`username`/`display_name` — no token, no explicit expiry beyond the Streamlit server's own
session lifetime.

| Action | Access Condition | Enforced In |
|---|---|---|
| Any Streamlit page | `st.session_state["authenticated"] == True` | `security/auth.py:is_authenticated()`, gated at `ui/streamlit_app.py:19-22` |

## Business Rules

| ID | Rule | Enforced In | Severity |
|---|---|---|---|
| BR-01 | Login requires a username/password match against the hardcoded `_USERS` dict | `security/auth.py:45-56` | CRITICAL |
| BR-02 | Passwords are hashed with plain SHA-256, **no salt** | `security/auth.py:9,41-42` | CRITICAL |
| BR-03 | No session expiry beyond the Streamlit server's own lifetime | `security/auth.py:49-55` | HIGH |
| BR-04 | Every ingest/search/redaction event is logged with `event_type`, `user_id`, and free-form `details` | `security/audit_logger.py:log_event()` | HIGH |
| BR-05 | Audit log DB write failures degrade to a warning, never block the caller | `security/audit_logger.py:48-49` | MEDIUM |
| BR-06 | Encryption key loads from `ENCRYPTION_KEY` env var, or falls back to a `.encryption_key` file written on first run | `app/config.py`, `security/encryption.py` | HIGH |
| BR-07 | If `cryptography` is unavailable, encryption silently degrades to plaintext passthrough | `security/encryption.py:42-50` | CRITICAL |

## Known Error Scenarios

| Scenario | Error Returned | Root Cause |
|---|---|---|
| Wrong username/password | "Invalid username or password" | Hash mismatch against `_USERS` |
| Audit DB unavailable | Silent — file write still succeeds | `security/audit_logger.py:48-49` |
| `cryptography` package missing | Silent plaintext passthrough | `security/encryption.py:42-50` |

## Testing Expectations

- No tests found exercising `security/auth.py`, `security/encryption.py`, or
  `security/audit_logger.py` directly in `tests/unit/`.

## Safe vs Dangerous Changes

### Safe
- Adding a new hardcoded demo user for local testing.
- Adding a new `event_type` value to the audit logger.

### Dangerous — Requires Review
| Change | Risk | Why |
|---|---|---|
| Removing or weakening the SHA-256 check without replacing it | Removes the only auth check that exists, however weak | No other layer verifies identity for the Streamlit UI |
| Changing `.encryption_key` handling | Data loss or exposure | Rotating/losing this key makes previously-encrypted PHI unrecoverable; the file has no documented permission hardening |

### Human Escalation Required
- **Replacing the prototype auth store with a real identity provider.** This is explicitly
  flagged as a prototype in the source; treat any request to "harden" it as a real
  security-design task, not a quick patch — see the gaps below for the specific list of what's
  missing (salting, lockout, session TTL, MFA, etc.).

## Forbidden Patterns

- Never add a new hardcoded credential to `_USERS` for anything other than local/demo use.
- Never log a query's raw text somewhere it wasn't already being logged — `audit_log.query` is
  already a known PHI-exposure risk (see Gaps); don't create a second copy of the problem.

## Key Files

- `security/auth.py` — login/logout, session population, hardcoded user store
- `security/encryption.py` — Fernet encrypt (used) / decrypt (unused — see Gaps)
- `security/audit_logger.py` — `log_event()`, `get_audit_trail()`, dual file+DB write

## Context Routing

| Feature | Load when |
|---|---|
| Feat-0001 (this file) | Touching login, session handling, encryption, or audit logging |

| Workflow | Sections to load |
|---|---|
| Security review / HIPAA audit | Business Rules, Known Error Scenarios, Gaps (below) |
| Adding a new audited event type | Business Rules (BR-04), Key Files |

## Gaps

*(Carried forward verbatim from the scan — these are documented findings, not opinions, and
should not be quietly "cleaned up" without a human decision per Human Escalation above.)*

- No authentication at all on `POST /ingest/bulk` (owned by Feat-0003) — this feature's auth
  mechanism only covers the Streamlit UI, not the FastAPI endpoint.
- SHA-256 without salt is not a password-hashing algorithm; identical passwords produce
  identical hashes.
- No account lockout after repeated failed logins.
- No session expiry — sessions live as long as the Streamlit server process's session state does.
- No audit events for login/logout/failed-login themselves — only document/query events are logged.
- `security/encryption.py`'s `decrypt()` function is defined but never called anywhere in the repo.
- `.encryption_key` (written to disk if `ENCRYPTION_KEY` isn't set) has no documented file
  permission or rotation policy.
- `audit_log.query` stores the caller's raw search text in plaintext — may itself contain PHI
  (patient names, conditions) inside what's meant to be a compliance record.
- The in-memory rate limiter (`app/dependencies.py`, consumed by Feat-0007) resets on restart
  and is not shared across processes.
