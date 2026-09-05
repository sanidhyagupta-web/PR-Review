---
paths:
  - "**/*.py"
---

# Security Rules

## Project Auth Model

Populated by `onboard.sh`. Read this section before reviewing any access control logic.

| Field | Value |
|-------|-------|
| **Model** | Role-based access control (RBAC) — a coarse role string, not per-user or per-resource ownership. There is no concept of "this record belongs to this user"; access is decided entirely by whether the caller's role appears in a chunk's `allowed_roles` list. |
| **Mechanism** | Two different, unrelated mechanisms, one per entry point: (1) **Streamlit UI** (`ui/`) — `security/auth.py:login()` checks a SHA-256 password hash against a hardcoded, in-memory `_USERS` dict (`security/auth.py:7-38`, explicitly labeled a prototype store) and, on success, sets `role`/`department`/`username` into `st.session_state`. There is no session token, cookie, or expiry beyond Streamlit's own server-side session lifetime, and no salting on the password hash. (2) **FastAPI bulk-ingest endpoint** (`POST /ingest/bulk`, `app/main.py:154-169`) — has **no authentication at all**. The caller self-reports `role` and `uploader_id` as plain HTTP headers, which are trusted as-is (`app/main.py:168`); anything reachable over the network can claim any role. |
| **Access primitive** | A `role` string. At ingest time, `ingestion/metadata/rbac_policy.py` stamps each chunk with an `allowed_roles` list derived from the uploading department (`_DEPARTMENT_ROLES`). At query time, `security/access_control.py:filter_results_by_role()` keeps only chunks where the caller's `role` is in that list (or the role is `"admin"`). Enforcement is query-time filtering, not row-level or endpoint-level authorization. |
| **Roles / scopes** | `admin`, `doctor`, `nurse`, `radiologist`, `billing`, `cardiologist`, `researcher` (see `security/auth.py:_USERS` and `ingestion/metadata/rbac_policy.py:_DEPARTMENT_ROLES`). Only `doctor`, `nurse`, `admin` may submit ingest jobs (`rbac_policy.py:get_ingest_allowed_roles()`). Departments: `general`, `cardiology`, `billing`, `radiology`, `oncology`. |

**Frontend auth note:** The Streamlit UI (`ui/streamlit_app.py:19-22`) gates every page behind `is_authenticated()` and only reaches page code once `security/auth.py:login()` has populated `st.session_state`, so a role reaching `filter_results_by_role()` from the UI can be trusted to reflect a real login. The FastAPI `/ingest/bulk` endpoint provides no equivalent guarantee — its `role` header is unauthenticated caller input, so treat any authorization decision based on it as advisory only, not a security boundary. Flag this explicitly (SEC-01/SEC-02) if new endpoints follow the same header-trust pattern instead of requiring real authentication.

## SEC-01: Authentication on endpoints <!-- severity: blocker -->
Every new API endpoint must require authentication unless explicitly intended to be public. Check for security annotations, configuration, or middleware that enforces auth. Compare with similar existing endpoints.

## SEC-02: Authorization and access control <!-- severity: blocker -->
Operations on resources must verify the requesting user has permission to access/modify that specific resource — not just that they are authenticated. Look for missing ownership checks (e.g., user A can modify user B's data). Check role-based access enforcement.

## SEC-03: Input validation <!-- severity: blocker -->
All user-supplied input (request bodies, query params, path params, headers) must be validated before use. Check for: missing validation annotations on request DTOs, missing schema validation, unbounded string lengths, negative numbers where only positive are valid, enum values not checked.

## SEC-04: SQL injection <!-- severity: blocker -->
Database queries must use parameterized queries or ORM criteria — never string concatenation with user input. Check for raw SQL queries built with string interpolation.

<!-- CUSTOMIZE: Replace examples below with your language/ORM's patterns -->
**Bad**: `@Query("SELECT * FROM users WHERE name = '" + name + "'")`
**Good**: `@Query("SELECT u FROM User u WHERE u.name = :name")`

## SEC-05: Secrets and credentials <!-- severity: blocker -->
No API keys, passwords, tokens, or secrets hardcoded in source code, committed config files, or log statements. Check for: hardcoded strings that look like keys/tokens, credentials in config that aren't environment variable references, secrets logged at any level.

## SEC-06: XSS prevention <!-- severity: blocker -->
User-supplied content rendered in the UI must be sanitized or escaped. Avoid injecting user input as raw HTML. Check that user input displayed in the UI goes through the framework's default escaping and is not injected as raw HTML.

## SEC-07: Sensitive data exposure <!-- severity: suggestion -->
API responses should not include sensitive fields unnecessarily (passwords, tokens, SSNs, internal IDs). Check that DTOs exclude sensitive entity fields. Verify that error responses don't leak stack traces, internal paths, or database details.

## SEC-08: CORS and request origin <!-- severity: suggestion -->
If the PR modifies CORS configuration, verify allowed origins are specific (not `*` in production). Check that CORS is not accidentally widened.

## SEC-09: File upload safety <!-- severity: blocker -->
If the PR handles file uploads, verify: file type validation (not just extension — check content type), file size limits, sanitized file names (no path traversal), storage in a safe location, and virus scanning if applicable.

## SEC-10: Rate limiting and abuse prevention <!-- severity: suggestion -->
Public-facing or expensive endpoints (login, search, report generation, file upload) should have rate limiting. Check if the new endpoint is a candidate for rate limiting based on its cost and exposure.
