# Phase 11 — Security Readiness

## AEGIS v4.6.2 Audit — 2026-02-13

(Full scan details in security/secrets_scan_results.md)

## Secrets Scan

| ID | Severity | Finding | Location |
|----|----------|---------|----------|
| SEC-CRIT-01 | CRITICAL | GitHub Personal Access Token exposed | .claude/settings.local.json:58,60 |
| SEC-HIGH-01 | HIGH | .secret_key not in .gitignore | .secret_key (64-char hex Flask secret) |
| SEC-HIGH-02 | HIGH | 8 cookies*.txt files with session tokens | cookies.txt through cookies8.txt |
| SEC-HIGH-03 | HIGH | CSP allows unsafe-inline for scripts | app.py:722-724 |
| SEC-HIGH-04 | HIGH | Authentication disabled by default | config_logging.py:156 TWR_AUTH=false |

## Security Controls

| Control | Status | Notes |
|---------|--------|-------|
| CSRF protection | PASS | All POST/PUT/DELETE routes decorated with @require_csrf |
| CSRF token generation | PASS | secrets.token_urlsafe(32) — cryptographically strong |
| CSRF validation | PASS | hmac.compare_digest() — timing-safe comparison |
| Session management | PASS | Signed Flask sessions with secret key |
| Input validation | PARTIAL | File type checking present, but path traversal not fully guarded |
| SQL injection | PASS | Parameterized queries in scan_history.py |
| XSS protection | PARTIAL | sanitizeHTML() strips scripts/event handlers, but CSP allows unsafe-inline |
| Rate limiting | FAIL | No rate limiting on any endpoint |
| Authentication | FAIL | Disabled by default (env var TWR_AUTH=false) |
| HTTPS enforcement | FAIL | No HSTS headers, HTTP only |
| Content-Type validation | PASS | File upload validates extension |
| Error handling | PASS | Custom error handlers don't leak stack traces in production |

## .gitignore Adequacy

Current .gitignore has only 2 entries:
- nlp_offline_windows.zip
- nlp_offline/

**Missing entries (SHOULD be in .gitignore):**
- .secret_key
- cookies*.txt
- *.pyc / __pycache__/
- logs/
- temp/
- data/*.db (or at minimum scan_history.db)
- .DS_Store
- .claude/
- startup_error.log

## SBOM (Software Bill of Materials)

| Category | Count |
|----------|-------|
| Python packages installed | ~200 |
| Key runtime deps | 25 (21 importable, 4 with fallback guards) |
| JS vendor libs | 4 (PDF.js, Sortable.min.js, GSAP, Lottie) |
| Frontend charting | 2 (Chart.js, D3.js via CDN) |

## Medium/Low Findings

| ID | Severity | Finding |
|----|----------|---------|
| SEC-MED-01 | MED | f-string SQL table names in app.py (lines 9950, 9963, 10039, 10056, 10073, 10090) |
| SEC-MED-02 | MED | Debug mode potentially enabled via config |
| SEC-MED-03 | MED | No Content-Security-Policy for frame-ancestors |
| SEC-MED-04 | MED | Temp files not cleaned up on failed uploads |
| SEC-MED-05 | MED | No request size limit beyond Flask default |
| SEC-MED-06 | MED | Subprocess Docling runs without resource limits |
| SEC-LOW-01 | LOW | Version info exposed in meta tags and footer |
| SEC-LOW-02 | LOW | No security headers (X-Content-Type-Options, X-Frame-Options) |
| SEC-LOW-03 | LOW | Cookie files in project root |
| SEC-LOW-04 | LOW | Startup error log in project root |
| SEC-LOW-05 | LOW | .DS_Store files tracked |

## Phase 11 Verdict: FAIL
- 1 CRITICAL secret exposed (GitHub PAT)
- 4 HIGH findings (secret_key, cookies, CSP, auth disabled)
- 6 MEDIUM findings
- .gitignore severely inadequate (2 entries vs 10+ needed)
- No rate limiting, no HTTPS enforcement, no auth by default
