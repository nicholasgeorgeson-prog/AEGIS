# AEGIS Security Audit Report

**Audit Date:** 2026-02-13
**Auditor:** Claude Opus 4.6 (automated)
**Codebase:** AEGIS v4.6.2 at `/Users/nick/Desktop/Work_Tools/TechWriterReview/`
**Scope:** Read-only audit -- no files modified

---

## Executive Summary

The audit identified **1 CRITICAL**, **4 HIGH**, **6 MEDIUM**, and **5 LOW** severity findings. The most urgent issue is an exposed GitHub Personal Access Token in `.claude/settings.local.json`. The codebase demonstrates solid security fundamentals (CSRF, CSP headers, input sanitization) but has gaps in secret management and SQL query construction.

| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | 1 | Requires immediate action |
| HIGH     | 4 | Should be remediated soon |
| MEDIUM   | 6 | Plan for remediation |
| LOW      | 5 | Informational / best practices |

---

## 1. HARDCODED SECRETS

### CRITICAL-01: GitHub Personal Access Token Exposed

**File:** `/Users/nick/Desktop/Work_Tools/TechWriterReview/.claude/settings.local.json` (lines 58, 60)
**Severity:** CRITICAL

A GitHub PAT (`ghp_REDACTED_TOKEN`) for user `nicholasgeorgeson-prog` is embedded in two `git fetch` / `git ls-remote` commands inside the Claude settings file. This token grants repository access.

```
"Bash(git fetch https://nicholasgeorgeson-prog:ghp_DCIkAX...@github.com/...)"
```

**Recommendation:**
1. **Immediately revoke this token** at https://github.com/settings/tokens
2. Generate a new token and store it in the macOS Keychain or as an environment variable
3. Add `.claude/settings.local.json` to `.gitignore` if not already excluded
4. Rotate any credentials that may have been exposed through this token

### CRITICAL-01b: CSRF Token Values in Settings

**File:** `/Users/nick/Desktop/Work_Tools/TechWriterReview/.claude/settings.local.json` (lines 88, 129)
**Severity:** LOW (localhost-only, ephemeral)

Two CSRF token literal values appear in the allowed commands list. These are session-specific and for localhost only, so the risk is minimal, but they indicate test artifacts were persisted.

---

## 2. SECRET FILES IN REPO

### HIGH-01: `.secret_key` File in Working Tree

**File:** `/Users/nick/Desktop/Work_Tools/TechWriterReview/.secret_key`
**Severity:** HIGH
**Content:** A 64-character hex string (SHA-256 derived Flask secret key)

This file contains the Flask `SECRET_KEY` used to sign session cookies. If committed to version control, any party with repo access can forge sessions.

**Current `.gitignore` contents:**
```
nlp_offline_windows.zip
nlp_offline/
```

The `.gitignore` does NOT exclude `.secret_key`.

**Recommendation:**
1. Add `.secret_key` to `.gitignore` immediately
2. Verify this file has not been committed to any remote repository
3. If committed, regenerate the key (delete `.secret_key` and restart the server)

### HIGH-02: 8 Cookie Files with Session Tokens

**Files:**
- `/Users/nick/Desktop/Work_Tools/TechWriterReview/cookies.txt`
- `/Users/nick/Desktop/Work_Tools/TechWriterReview/cookies2.txt` through `cookies8.txt`

**Severity:** HIGH
**Content:** Netscape HTTP cookie files containing Flask session JWTs with embedded CSRF tokens and session IDs.

Example from `cookies.txt`:
```
#HttpOnly_localhost FALSE / TRUE 0 session eyJjc3JmX3Rva2VuIjoi...
```

These files contain signed Flask session cookies that include CSRF tokens. While localhost-only, they should not exist in the project directory.

**Recommendation:**
1. Delete all 8 `cookies*.txt` files
2. Add `cookies*.txt` to `.gitignore`
3. These appear to be `curl` test artifacts -- use `--cookie-jar /tmp/cookies.txt` for temporary locations instead

### MEDIUM-01: Insufficient `.gitignore`

**File:** `/Users/nick/Desktop/Work_Tools/TechWriterReview/.gitignore`
**Severity:** MEDIUM

The `.gitignore` only excludes 2 entries. It should also exclude:
- `.secret_key`
- `cookies*.txt`
- `*.db` (SQLite databases contain user data)
- `*.db-shm`, `*.db-wal` (SQLite journal files)
- `__pycache__/`
- `logs/`
- `temp/`
- `*.pyc`
- `.DS_Store`
- `.claude/`
- `startup_error.log`

---

## 3. DANGEROUS CODE PATTERNS

### MEDIUM-02: SQL Injection via f-string Table Names

**File:** `/Users/nick/Desktop/Work_Tools/TechWriterReview/app.py` (lines 9950, 9963, 10039, 10056, 10073, 10090)
**Severity:** MEDIUM

Multiple `cursor.execute()` calls use f-strings to interpolate table names:

```python
cursor.execute(f'DELETE FROM {tbl}')  # app.py:9950
```

While the `tbl` values come from hardcoded lists (not user input), this pattern is fragile. If any code path allows user-controlled table names, it becomes exploitable.

**Additional locations with f-string SQL:**
- `scan_history.py:517` -- `ALTER TABLE` with f-string column definitions
- `scan_history.py:1070` -- `UPDATE` with f-string `SET` clauses (field names from allowlist)
- `scan_history.py:1499` -- `SELECT` with f-string `WHERE` clause
- `scan_history.py:3629` -- `UPDATE role_dictionary SET {sets}` with f-string
- `adaptive_learner.py:925` -- `SELECT COUNT(*)` with f-string confidence value
- `diagnostic_export.py:656` -- `SELECT COUNT(*)` with f-string table name

**Recommendation:**
- For `scan_history.py:1070` and `3629`: The column names in `set_clauses`/`sets` are constructed from an allowlist (`allowed_fields`), which is a safe pattern. However, add explicit validation that field names match `^[a-z_]+$` regex.
- For `app.py:9950` etc.: These use hardcoded table name lists, which is safe. Add a comment documenting this is intentional.
- For `adaptive_learner.py:925`: `self.HIGH_CONFIDENCE` is a class constant (safe), but should use a parameterized query for consistency: `cursor.execute('SELECT COUNT(*) FROM patterns WHERE confidence >= ?', (self.HIGH_CONFIDENCE,))`

### MEDIUM-03: `__import__()` Dynamic Imports

**Files:**
- `nlp_integration.py:770` -- `module = __import__(module_name)` with module names from a hardcoded list
- `diagnostic_export.py:612` -- `mod = __import__(module_name)` with module names from hardcoded list
- `app.py:6680-6681` -- `__import__('sqlite3')` (safe, literal string)
- `acronym_checker.py:609` -- `__import__('json')` (safe, literal string)

**Severity:** LOW

The dynamic imports in `nlp_integration.py` and `diagnostic_export.py` use module names from hardcoded lists within the function, not from user input. This is a code smell but not exploitable.

**Recommendation:** Replace `__import__()` with `importlib.import_module()` which is the recommended alternative for dynamic imports.

### LOW-01: No `eval()` or `exec()` Usage

No instances of `eval()` or `exec()` were found in any `.py` files. This is a positive finding.

### LOW-02: No `pickle.loads()` Usage

No instances of `pickle.loads()` or `pickle.load()` were found. This is a positive finding.

### MEDIUM-04: `subprocess.run()` Usage

**Files:**
- `install_nlp.py:50,85`
- `install_nlp_offline.py:93,118`
- `setup_tesseract.py:90,106`
- `hyperlink_health.py:894`

**Severity:** LOW

All `subprocess` calls use list-form arguments (no `shell=True`), which prevents command injection. The commands are for pip installs and tesseract setup. No user input flows into these commands.

### LOW-03: No `os.system()` Usage

No instances of `os.system()` were found. This is a positive finding.

### MEDIUM-05: Extensive `innerHTML` Usage in JavaScript (532 locations)

**Files:** 46 JavaScript files across `static/js/`
**Severity:** MEDIUM

There are hundreds of `innerHTML` assignments throughout the JavaScript codebase. While most dynamic content is escaped via `escapeHtml()` (defined in `static/js/utils/dom.js:24` and `static/js/ui/renderers.js:71`), not all innerHTML assignments were verified to use this function.

**Positive mitigations found:**
- `escapeHtml()` utility is defined and used extensively in renderers.js
- CSP header blocks external script loading in production mode
- Backend returns JSON (not HTML), so most XSS risk is client-side template injection

**Concerning patterns:**
- `static/js/function-tags.js:1323`: Error message rendered via innerHTML: `'Error loading documents: ' + e.message` -- if `e.message` contains HTML, it is injectable.
- Various roles/dictionary files build HTML from API data without consistent escaping.

**Recommendation:**
- Audit all `innerHTML` assignments to ensure they use `escapeHtml()` for any user-derived or API-derived content
- Consider migrating to `textContent` where HTML rendering is not needed
- The error message pattern at function-tags.js:1323 should use `escapeHtml(e.message)`

---

## 4. DEPENDENCY RISKS

### MEDIUM-06: Loose Version Pinning

**File:** `/Users/nick/Desktop/Work_Tools/TechWriterReview/requirements.txt`
**Severity:** MEDIUM

Dependencies use range constraints (e.g., `Flask>=2.0.0,<3.0.0`) rather than exact pins. While this allows flexibility, it means builds are not reproducible and could pull in a compromised minor version.

**Notable dependencies and observations:**
| Package | Constraint | Note |
|---------|-----------|------|
| Flask | >=2.0.0,<3.0.0 | Wide range; pin to specific minor |
| requests | >=2.31.0 | No upper bound |
| spacy | >=3.7.0,<4.0.0 | Large attack surface |
| sentence-transformers | >=2.2.0 | No upper bound |
| Pillow | >=10.0.0 | Frequent CVEs; needs upper bound |
| lxml | >=4.9.0,<5.0.0 | History of XML injection CVEs |
| reportlab | >=4.0.0 | No upper bound |
| bokeh | >=3.3.0 | No upper bound |

**Recommendation:**
1. Generate a `requirements-lock.txt` with exact versions: `pip freeze > requirements-lock.txt`
2. Add upper bounds to all open-ended constraints (especially `requests`, `Pillow`, `sentence-transformers`)
3. Run `pip audit` or `safety check` periodically to check for known CVEs

---

## 5. SESSION / AUTH / CSRF SECURITY

### Positive Findings

**CSRF Protection:**
- Token generation uses `secrets.token_urlsafe(32)` (cryptographically secure) -- `config_logging.py:684`
- Token verification uses `hmac.compare_digest()` (constant-time comparison) -- `config_logging.py:690`
- CSRF is required on all state-changing routes via `@require_csrf` decorator
- CSRF can be disabled via `TWR_CSRF=false` env var (needed for testing, but documented)

**Session Security:**
- `SESSION_COOKIE_HTTPONLY = True` -- prevents JavaScript access to session cookie
- `SESSION_COOKIE_SAMESITE = 'Lax'` -- prevents CSRF via cross-site POST
- `SESSION_COOKIE_SECURE = False` -- correctly disabled for localhost HTTP

**Secret Key Generation:**
- Uses `secrets.token_hex(32)` for 256-bit keys -- `config_logging.py:135`
- File permissions set to `0o600` (owner-only) -- `config_logging.py:138`
- Minimum key length validated at 32 characters -- `config_logging.py:169`

**Security Headers (in `after_request`):**
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- Content Security Policy applied

### HIGH-03: CSP Allows `unsafe-inline` for Scripts

**File:** `/Users/nick/Desktop/Work_Tools/TechWriterReview/app.py` (lines 722-724)
**Severity:** HIGH

The Content Security Policy includes `script-src 'self' 'unsafe-inline'`. This undermines CSP's XSS protection because inline scripts can still execute, which is the primary attack vector for XSS.

```python
"script-src 'self' 'unsafe-inline'"
```

**Recommendation:**
- Migrate inline scripts to external files
- Use nonce-based CSP: `script-src 'self' 'nonce-{random}'` with a per-request nonce
- At minimum, remove `'unsafe-inline'` from script-src and add nonces to the few inline script blocks in `templates/index.html`

### HIGH-04: Authentication Disabled by Default

**File:** `/Users/nick/Desktop/Work_Tools/TechWriterReview/config_logging.py` (line 156)
**Severity:** HIGH (for production deployment)

```python
auth_enabled=os.environ.get('TWR_AUTH', 'false').lower() == 'true',
```

Authentication is disabled by default. Anyone on the network can access all functionality. This is acceptable for localhost development but dangerous if the server is bound to `0.0.0.0` or deployed on a network.

**Recommendation:**
- Require authentication when `TWR_HOST` is not `127.0.0.1` or `localhost`
- Add a startup warning if auth is disabled and host is `0.0.0.0`
- Document the authentication setup prominently in deployment guides

---

## 6. FILE UPLOAD SECURITY

### Positive Findings

**File extension validation:**
- `validate_file_extension()` checks against allowlist: `.docx`, `.pdf`, `.doc` -- `config_logging.py:676`
- `sanitize_filename()` strips path separators, null bytes, leading dots, limits to 255 chars -- `config_logging.py:660-673`
- Unique filenames generated with UUID prefix: `f"{uuid.uuid4().hex[:8]}_{original_name}"` -- `app.py:1448`

**Size limits:**
- Default max upload: 50MB (`DEFAULT_MAX_UPLOAD_MB`) -- `config_logging.py:27`
- Hard cap: 500MB (`MAX_SAFE_UPLOAD_MB`) -- `config_logging.py:28`
- Flask `MAX_CONTENT_LENGTH` enforced -- `app.py:148`
- Batch upload limits enforced -- `app.py:1582`
- Per-extractor file size limits (100MB) -- `core.py:139,408,695`

**Temp file cleanup:**
- Background cleanup thread removes files older than 24 hours -- `app.py:9676-9698`
- Cleanup runs on startup and periodically -- `app.py:10255-10256`
- Session cleanup included -- `app.py:9696`

**Path traversal protection:**
- `sanitize_static_path()` blocks `..` and leading `/` -- `app.py:1222`
- `send_from_directory()` used for temp file serving with `Path(filename).name` sanitization -- `app.py:1546-1550`
- Static file paths validated against allowed extensions -- `app.py:1252-1254`

### LOW-04: File Content Not Validated

While file extensions are checked, file content (magic bytes / MIME type) is not validated. A malicious file with a `.docx` extension but non-DOCX content could potentially exploit parser vulnerabilities.

**Recommendation:** Add magic byte validation (e.g., check for ZIP header `PK` for DOCX, `%PDF` for PDF).

### LOW-05: Dev Endpoint Lacks CSRF

**File:** `/Users/nick/Desktop/Work_Tools/TechWriterReview/app.py` (line 1540)

```python
@app.route('/api/dev/temp/<filename>', methods=['GET'])
```

This endpoint serves files from the temp directory and lacks the `@require_csrf` decorator. While it is a GET endpoint (CSRF is typically only needed for state-changing methods) and uses `Path(filename).name` for sanitization, it could be used to retrieve uploaded documents without authentication.

**Recommendation:** Add authentication check or remove this endpoint in production builds.

---

## 7. ADDITIONAL OBSERVATIONS

### Diagnostic Export Sanitization (Positive)

**File:** `/Users/nick/Desktop/Work_Tools/TechWriterReview/diagnostic_export.py` (lines 88-105)

The diagnostic export module includes comprehensive redaction patterns for secrets, tokens, and sensitive data before exporting diagnostics. This is a good security practice.

### Console Logging Volume

532 `console.log/debug/trace` statements across 46 JS files. While not a security vulnerability per se, excessive logging can leak sensitive data to browser developer tools. Consider implementing log levels that can be disabled in production.

### No Open Redirect Vulnerabilities

No instances of `redirect(request.args.get(...))` or similar open redirect patterns were found.

### No Unsafe Deserialization

No `pickle.loads()`, `yaml.load()` (without SafeLoader), or `eval()` calls found on untrusted data.

---

## Remediation Priority

| # | Finding | Severity | Effort | Action |
|---|---------|----------|--------|--------|
| 1 | CRITICAL-01: Revoke GitHub PAT | CRITICAL | 5 min | Revoke token NOW at github.com/settings/tokens |
| 2 | HIGH-01: Add `.secret_key` to .gitignore | HIGH | 1 min | Update .gitignore |
| 3 | HIGH-02: Delete cookies*.txt files | HIGH | 1 min | Remove files, add to .gitignore |
| 4 | HIGH-03: Remove `unsafe-inline` from CSP | HIGH | 2-4 hrs | Refactor inline scripts to external |
| 5 | HIGH-04: Auth warning for non-localhost | HIGH | 30 min | Add startup check |
| 6 | MEDIUM-01: Expand .gitignore | MEDIUM | 10 min | Add all sensitive patterns |
| 7 | MEDIUM-02: Parameterize SQL queries | MEDIUM | 1-2 hrs | Refactor f-string queries |
| 8 | MEDIUM-05: Audit innerHTML usage | MEDIUM | 2-3 hrs | Ensure escapeHtml on all dynamic content |
| 9 | MEDIUM-06: Pin dependency versions | MEDIUM | 30 min | Generate requirements-lock.txt |
| 10 | LOW-04: Add file magic byte validation | LOW | 1 hr | Check file headers match extension |

---

*End of Security Audit Report*
