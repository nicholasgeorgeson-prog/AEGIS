#!/usr/bin/env python3
"""
AEGIS v5.9.0 — Functional Integration Test Suite
=================================================
Tests real HTTP requests against all major API endpoints using Flask's test client.
No live server needed — uses app.test_client() for in-process requests.

Run with: python -m pytest tests/test_integration.py -v
"""

import pytest
import os
import sys
import json
import re
import time
import threading
from pathlib import Path
from io import BytesIO

# Add parent directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(scope='session')
def flask_app():
    """Create the Flask application for testing."""
    from app import app
    app.config['TESTING'] = True
    # Ensure CSRF is enabled for security tests
    return app


@pytest.fixture
def client(flask_app):
    """Create a test client with CSRF token extracted from response headers."""
    with flask_app.test_client() as test_client:
        # Make a GET request to establish session and get CSRF token
        resp = test_client.get('/api/version')
        csrf = resp.headers.get('X-CSRF-Token', '')
        yield test_client, csrf


@pytest.fixture
def client_no_csrf(flask_app):
    """Create a test client WITHOUT extracting CSRF (for security tests)."""
    with flask_app.test_client() as test_client:
        yield test_client


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_json(resp):
    """Safely parse JSON response."""
    try:
        return resp.get_json()
    except Exception:
        return None


def assert_success_response(resp, expected_status=200):
    """Assert a standard successful API response."""
    assert resp.status_code == expected_status, \
        f"Expected {expected_status}, got {resp.status_code}: {resp.data[:500]}"
    data = get_json(resp)
    assert data is not None, "Response is not valid JSON"
    assert data.get('success') is True, f"Response success=False: {data.get('error', 'unknown')}"
    return data


# =============================================================================
# GET ENDPOINT TESTS — Core & Configuration
# =============================================================================

class TestGetEndpoints:
    """Test all major GET endpoints return 200 with success: true."""

    def test_api_version(self, client):
        """GET /api/version returns version string matching version.json."""
        c, _ = client
        resp = c.get('/api/version')
        assert resp.status_code == 200
        data = get_json(resp)
        assert data is not None
        # Version endpoint must include both 'version' and 'app_version' keys
        assert 'version' in data, f"Missing 'version' key in response: {list(data.keys())}"
        assert 'app_version' in data, f"Missing 'app_version' key in response: {list(data.keys())}"
        assert data['version'] == data['app_version'], \
            f"version ({data['version']}) != app_version ({data['app_version']})"

    def test_api_version_matches_file(self, client):
        """GET /api/version response matches root version.json."""
        c, _ = client
        resp = c.get('/api/version')
        data = get_json(resp)
        version_from_api = (data.get('app_version') or data.get('version')
                            or (data.get('data', {}) or {}).get('version'))

        vpath = Path(__file__).parent.parent / 'version.json'
        file_data = json.loads(vpath.read_text())
        assert version_from_api == file_data['version'], \
            f"API version ({version_from_api}) != file version ({file_data['version']})"

    def test_api_config(self, client):
        """GET /api/config returns app configuration."""
        c, _ = client
        resp = c.get('/api/config')
        data = assert_success_response(resp)
        assert 'data' in data

    def test_api_health(self, client):
        """GET /api/health returns healthy status."""
        c, _ = client
        resp = c.get('/api/health')
        assert resp.status_code == 200
        data = get_json(resp)
        assert data is not None

    def test_api_ready(self, client):
        """GET /api/ready returns readiness status."""
        c, _ = client
        resp = c.get('/api/ready')
        assert resp.status_code == 200

    def test_api_metrics_dashboard(self, client):
        """GET /api/metrics/dashboard returns metrics data."""
        c, _ = client
        resp = c.get('/api/metrics/dashboard')
        data = assert_success_response(resp)
        assert 'data' in data

    def test_api_metrics_landing(self, client):
        """GET /api/metrics/landing returns landing page metrics."""
        c, _ = client
        resp = c.get('/api/metrics/landing')
        data = assert_success_response(resp)

    def test_api_scan_history(self, client):
        """GET /api/scan-history returns scan history records."""
        c, _ = client
        resp = c.get('/api/scan-history')
        data = assert_success_response(resp)

    def test_api_documents(self, client):
        """GET /api/documents returns document list."""
        c, _ = client
        resp = c.get('/api/documents')
        data = assert_success_response(resp)

    def test_api_roles_dictionary(self, client):
        """GET /api/roles/dictionary returns roles array."""
        c, _ = client
        resp = c.get('/api/roles/dictionary')
        data = assert_success_response(resp)
        # Roles should be under data.roles
        roles_data = data.get('data', {})
        assert 'roles' in roles_data, f"Missing 'roles' key in data: {list(roles_data.keys())}"
        assert isinstance(roles_data['roles'], list)

    def test_api_roles_dictionary_stats(self, client):
        """GET /api/roles/dictionary/stats returns dictionary statistics."""
        c, _ = client
        resp = c.get('/api/roles/dictionary/stats')
        data = assert_success_response(resp)

    def test_api_roles_categories(self, client):
        """GET /api/function-categories returns function categories."""
        c, _ = client
        resp = c.get('/api/function-categories')
        data = assert_success_response(resp)

    def test_api_roles_aggregated(self, client):
        """GET /api/roles/aggregated returns aggregated role data."""
        c, _ = client
        resp = c.get('/api/roles/aggregated')
        data = assert_success_response(resp)

    def test_api_roles_adjudication_status(self, client):
        """GET /api/roles/adjudication-status requires role_name param."""
        c, _ = client
        # This endpoint requires role_name — test it returns 400 gracefully, not 500
        resp = c.get('/api/roles/adjudication-status')
        assert resp.status_code in (200, 400), \
            f"adjudication-status returned {resp.status_code} (expected 200 or 400)"

    def test_api_roles_adjudication_summary(self, client):
        """GET /api/roles/adjudication-summary returns adjudication metrics."""
        c, _ = client
        resp = c.get('/api/roles/adjudication-summary')
        data = assert_success_response(resp)
        summary = data.get('data', {})
        assert 'total_roles' in summary, f"Missing total_roles in summary: {list(summary.keys())}"
        assert 'adjudicated' in summary, f"Missing adjudicated in summary: {list(summary.keys())}"

    def test_api_roles_relationships(self, client):
        """GET /api/roles/relationships returns relationship edges."""
        c, _ = client
        resp = c.get('/api/roles/relationships')
        data = assert_success_response(resp)

    def test_api_roles_hierarchy(self, client):
        """GET /api/roles/hierarchy returns hierarchy data."""
        c, _ = client
        resp = c.get('/api/roles/hierarchy')
        data = assert_success_response(resp)

    def test_api_roles_matrix(self, client):
        """GET /api/roles/matrix returns RACI matrix."""
        c, _ = client
        resp = c.get('/api/roles/matrix')
        data = assert_success_response(resp)

    def test_api_roles_graph(self, client):
        """GET /api/roles/graph returns role relationship graph."""
        c, _ = client
        resp = c.get('/api/roles/graph')
        data = assert_success_response(resp)

    def test_api_scan_history_stats(self, client):
        """GET /api/scan-history/stats returns statistics."""
        c, _ = client
        resp = c.get('/api/scan-history/stats')
        data = assert_success_response(resp)

    def test_api_score_trend(self, client):
        """GET /api/score-trend requires filename param, returns 400 without it."""
        c, _ = client
        # Requires filename or document_id param
        resp = c.get('/api/score-trend')
        assert resp.status_code in (200, 400), \
            f"score-trend returned {resp.status_code} (expected 200 or 400)"

    def test_api_scan_profiles(self, client):
        """GET /api/scan-profiles returns scan profiles."""
        c, _ = client
        resp = c.get('/api/scan-profiles')
        data = assert_success_response(resp)

    def test_api_nlp_status(self, client):
        """GET /api/nlp/status returns NLP module status."""
        c, _ = client
        resp = c.get('/api/nlp/status')
        data = assert_success_response(resp)

    def test_api_nlp_checkers(self, client):
        """GET /api/nlp/checkers returns available NLP checkers."""
        c, _ = client
        resp = c.get('/api/nlp/checkers')
        data = assert_success_response(resp)

    def test_api_docling_status(self, client):
        """GET /api/docling/status returns Docling extractor status."""
        c, _ = client
        resp = c.get('/api/docling/status')
        assert resp.status_code == 200
        data = get_json(resp)
        assert data is not None
        # This endpoint doesn't use {success: true} wrapper — returns direct status object
        assert 'available' in data or 'backend' in data, \
            f"Docling status missing expected fields: {list(data.keys())}"

    def test_api_extraction_capabilities(self, client):
        """GET /api/extraction/capabilities returns extraction info."""
        c, _ = client
        resp = c.get('/api/extraction/capabilities')
        assert resp.status_code == 200
        data = get_json(resp)
        assert data is not None
        # This endpoint doesn't use {success: true} wrapper
        assert 'pdf' in data or 'nlp' in data or 'version' in data, \
            f"Extraction capabilities missing expected fields: {list(data.keys())}"

    def test_api_analyzers_status(self, client):
        """GET /api/analyzers/status returns analyzer status."""
        c, _ = client
        resp = c.get('/api/analyzers/status')
        data = assert_success_response(resp)

    def test_api_presets(self, client):
        """GET /api/presets returns style presets list."""
        c, _ = client
        resp = c.get('/api/presets')
        data = assert_success_response(resp)

    def test_api_role_function_tags(self, client):
        """GET /api/role-function-tags returns tag associations."""
        c, _ = client
        resp = c.get('/api/role-function-tags')
        data = assert_success_response(resp)

    def test_api_document_categories(self, client):
        """GET /api/document-categories returns document categories."""
        c, _ = client
        resp = c.get('/api/document-categories')
        data = assert_success_response(resp)

    def test_api_document_category_types(self, client):
        """GET /api/document-category-types returns category types."""
        c, _ = client
        resp = c.get('/api/document-category-types')
        data = assert_success_response(resp)

    def test_api_role_required_actions(self, client):
        """GET /api/role-required-actions returns required actions."""
        c, _ = client
        resp = c.get('/api/role-required-actions')
        data = assert_success_response(resp)

    def test_api_learner_patterns(self, client):
        """GET /api/learner/patterns returns learned patterns."""
        c, _ = client
        resp = c.get('/api/learner/patterns')
        assert resp.status_code == 200
        data = get_json(resp)
        assert data is not None
        # This endpoint may not use {success: true} wrapper
        assert 'patterns' in data or 'success' in data, \
            f"Learner patterns missing expected fields: {list(data.keys())}"

    def test_api_learner_statistics(self, client):
        """GET /api/learner/statistics returns learner stats."""
        c, _ = client
        resp = c.get('/api/learner/statistics')
        data = assert_success_response(resp)

    def test_api_job_list(self, client):
        """GET /api/job/list returns jobs."""
        c, _ = client
        resp = c.get('/api/job/list')
        data = assert_success_response(resp)


# =============================================================================
# GET ENDPOINTS — Feature Module Health Checks
# =============================================================================

class TestFeatureModuleHealth:
    """Test health/status endpoints for feature modules."""

    def test_compare_documents(self, client):
        """GET /api/compare/documents returns comparable document list."""
        c, _ = client
        resp = c.get('/api/compare/documents')
        data = assert_success_response(resp)

    def test_compare_status(self, client):
        """GET /api/compare/status returns compare module status."""
        c, _ = client
        resp = c.get('/api/compare/status')
        data = assert_success_response(resp)

    def test_compare_health(self, client):
        """GET /api/compare/health returns compare module health."""
        c, _ = client
        resp = c.get('/api/compare/health')
        data = assert_success_response(resp)

    def test_statement_forge_health(self, client):
        """GET /api/statement-forge/health returns SF module health."""
        c, _ = client
        resp = c.get('/api/statement-forge/health')
        data = assert_success_response(resp)

    def test_statement_forge_availability(self, client):
        """GET /api/statement-forge/availability returns SF availability."""
        c, _ = client
        resp = c.get('/api/statement-forge/availability')
        data = assert_success_response(resp)

    def test_statement_forge_verbs(self, client):
        """GET /api/statement-forge/verbs returns directive verbs list."""
        c, _ = client
        resp = c.get('/api/statement-forge/verbs')
        data = assert_success_response(resp)

    def test_hyperlink_validator_health(self, client):
        """GET /api/hyperlink-validator/health returns HV module health."""
        c, _ = client
        resp = c.get('/api/hyperlink-validator/health')
        data = assert_success_response(resp)

    def test_hyperlink_validator_capabilities(self, client):
        """GET /api/hyperlink-validator/capabilities returns HV capabilities."""
        c, _ = client
        resp = c.get('/api/hyperlink-validator/capabilities')
        data = assert_success_response(resp)

    def test_hyperlink_validator_exclusions(self, client):
        """GET /api/hyperlink-validator/exclusions returns exclusion list."""
        c, _ = client
        resp = c.get('/api/hyperlink-validator/exclusions')
        data = assert_success_response(resp)

    def test_hyperlink_validator_history(self, client):
        """GET /api/hyperlink-validator/history returns validation history."""
        c, _ = client
        resp = c.get('/api/hyperlink-validator/history')
        data = assert_success_response(resp)

    def test_hyperlink_validator_history_stats(self, client):
        """GET /api/hyperlink-validator/history/stats returns HV history stats."""
        c, _ = client
        resp = c.get('/api/hyperlink-validator/history/stats')
        data = assert_success_response(resp)

    def test_hyperlink_validator_rescan_capabilities(self, client):
        """GET /api/hyperlink-validator/rescan/capabilities returns rescan info."""
        c, _ = client
        resp = c.get('/api/hyperlink-validator/rescan/capabilities')
        data = assert_success_response(resp)

    def test_hyperlink_validator_excel_capabilities(self, client):
        """GET /api/hyperlink-validator/excel-capabilities returns Excel support info."""
        c, _ = client
        resp = c.get('/api/hyperlink-validator/excel-capabilities')
        data = assert_success_response(resp)

    def test_hyperlink_validator_export_highlighted_capabilities(self, client):
        """GET /api/hyperlink-validator/export-highlighted/capabilities returns export caps."""
        c, _ = client
        resp = c.get('/api/hyperlink-validator/export-highlighted/capabilities')
        data = assert_success_response(resp)

    def test_portfolio_stats(self, client):
        """GET /api/portfolio/stats returns portfolio statistics."""
        c, _ = client
        resp = c.get('/api/portfolio/stats')
        data = assert_success_response(resp)

    def test_portfolio_recent(self, client):
        """GET /api/portfolio/recent returns recent activity."""
        c, _ = client
        resp = c.get('/api/portfolio/recent')
        data = assert_success_response(resp)

    def test_portfolio_batches(self, client):
        """GET /api/portfolio/batches returns batch list."""
        c, _ = client
        resp = c.get('/api/portfolio/batches')
        data = assert_success_response(resp)


# =============================================================================
# DIAGNOSTICS ENDPOINT TESTS
# =============================================================================

class TestDiagnostics:
    """Test diagnostics endpoints — health, summary, export."""

    def test_diagnostics_health_returns_packages(self, client):
        """GET /api/diagnostics/health returns 25+ packages (was only 15 before fix)."""
        c, _ = client
        resp = c.get('/api/diagnostics/health')
        data = assert_success_response(resp)
        packages = data.get('data', {}).get('packages', {})
        pkg_count = len(packages)
        assert pkg_count >= 25, \
            f"Only {pkg_count} packages reported (expected 25+): {list(packages.keys())}"

    def test_diagnostics_health_has_key_packages(self, client):
        """Health check includes Flask, spaCy, NLTK, reportlab, mammoth."""
        c, _ = client
        resp = c.get('/api/diagnostics/health')
        data = assert_success_response(resp)
        packages = data.get('data', {}).get('packages', {})
        required = ['Flask', 'spaCy', 'NLTK', 'reportlab', 'mammoth']
        for pkg in required:
            assert pkg in packages, f"Missing required package '{pkg}' in health check"

    def test_diagnostics_health_has_summary(self, client):
        """Health check includes summary with counts."""
        c, _ = client
        resp = c.get('/api/diagnostics/health')
        data = assert_success_response(resp)
        summary = data.get('data', {}).get('summary', {})
        assert 'packages' in summary
        assert 'nlp_models' in summary

    def test_diagnostics_health_has_nlp_models(self, client):
        """Health check reports NLP model availability."""
        c, _ = client
        resp = c.get('/api/diagnostics/health')
        data = assert_success_response(resp)
        nlp_models = data.get('data', {}).get('nlp_models', {})
        assert len(nlp_models) >= 1, "No NLP models reported in health check"

    def test_diagnostics_summary(self, client):
        """GET /api/diagnostics/summary returns comprehensive summary."""
        c, _ = client
        resp = c.get('/api/diagnostics/summary')
        data = assert_success_response(resp)

    def test_diagnostics_logs(self, client):
        """GET /api/diagnostics/logs returns log entries."""
        c, _ = client
        resp = c.get('/api/diagnostics/logs')
        data = assert_success_response(resp)

    def test_diagnostics_errors(self, client):
        """GET /api/diagnostics/errors returns error list."""
        c, _ = client
        resp = c.get('/api/diagnostics/errors')
        data = assert_success_response(resp)

    def test_diagnostics_export_requires_csrf(self, client_no_csrf):
        """POST /api/diagnostics/export enforces CSRF protection."""
        c = client_no_csrf
        c.get('/api/version')  # establish session
        resp = c.post('/api/diagnostics/export',
                       data=json.dumps({'format': 'json'}),
                       content_type='application/json')
        assert resp.status_code == 403, \
            f"Diagnostics export should require CSRF, got {resp.status_code}"

    def test_diagnostics_export_with_csrf(self, client):
        """POST /api/diagnostics/export with CSRF completes within 5 seconds (RLock regression)."""
        c, csrf = client
        start = time.monotonic()
        resp = c.post('/api/diagnostics/export',
                       data=json.dumps({'format': 'json'}),
                       content_type='application/json',
                       headers={'X-CSRF-Token': csrf})
        elapsed = time.monotonic() - start
        # Must not deadlock — should complete in well under 5 seconds
        assert elapsed < 5.0, \
            f"Diagnostics export took {elapsed:.1f}s (>5s = likely RLock deadlock)"
        assert resp.status_code == 200, \
            f"Export failed with status {resp.status_code}: {resp.data[:300]}"


# =============================================================================
# CSRF SECURITY TESTS
# =============================================================================

class TestCSRFSecurity:
    """Test CSRF token enforcement on state-changing endpoints."""

    def test_csrf_token_in_response_headers(self, client):
        """Every response should include X-CSRF-Token header."""
        c, _ = client
        resp = c.get('/api/version')
        assert 'X-CSRF-Token' in resp.headers, "Missing X-CSRF-Token in response headers"
        assert len(resp.headers['X-CSRF-Token']) > 10, "CSRF token too short"

    def test_csrf_token_in_api_responses(self, client):
        """Multiple different API responses all include CSRF token."""
        c, _ = client
        endpoints = ['/api/config', '/api/health', '/api/scan-history']
        for ep in endpoints:
            resp = c.get(ep)
            assert 'X-CSRF-Token' in resp.headers, \
                f"Missing X-CSRF-Token in {ep} response"

    def test_csrf_blocks_post_without_token(self, client_no_csrf):
        """POST endpoints with @require_csrf reject requests without CSRF token."""
        c = client_no_csrf
        # Establish session first
        c.get('/api/version')

        # Only test endpoints that use @require_csrf decorator (in blueprints)
        # NOT endpoints registered via diagnostic_export.py (which lack CSRF)
        post_endpoints = [
            '/api/roles/adjudicate',
            '/api/roles/rename',
            '/api/roles/auto-adjudicate',
            '/api/upload',
        ]
        for ep in post_endpoints:
            resp = c.post(ep,
                          data=json.dumps({}),
                          content_type='application/json')
            assert resp.status_code == 403, \
                f"{ep} should return 403 without CSRF, got {resp.status_code}"

    def test_csrf_allows_post_with_token(self, client):
        """POST endpoints accept requests with valid CSRF token."""
        c, csrf = client
        # Test with an endpoint that won't cause side effects
        # /api/roles/adjudicate with empty body should return 400 (bad request), not 403
        resp = c.post('/api/roles/adjudicate',
                       data=json.dumps({}),
                       content_type='application/json',
                       headers={'X-CSRF-Token': csrf})
        # Should NOT be 403 — any other status is fine (400, 500, etc.)
        assert resp.status_code != 403, \
            f"Got 403 CSRF error even WITH valid token on /api/roles/adjudicate"

    def test_csrf_wrong_header_name_rejected(self, client):
        """Using wrong header name X-CSRFToken (no dash) should fail on @require_csrf endpoints."""
        c, csrf = client
        # Use an endpoint that has @require_csrf (not diagnostics/export which lacks it)
        resp = c.post('/api/roles/adjudicate',
                       data=json.dumps({}),
                       content_type='application/json',
                       headers={'X-CSRFToken': csrf})  # Wrong header name!
        assert resp.status_code == 403, \
            f"Wrong CSRF header name should be rejected, got {resp.status_code}"


# =============================================================================
# CSRF HEADER NAME REGRESSION (Source Code Check)
# =============================================================================

class TestCSRFHeaderNameInSource:
    """Verify no JS files use the wrong X-CSRFToken header name."""

    def test_no_wrong_csrf_header_in_js(self):
        """All JS files should use X-CSRF-Token (with dash), never X-CSRFToken."""
        js_dir = Path(__file__).parent.parent / 'static' / 'js'
        wrong_pattern = re.compile(r"['\"]X-CSRFToken['\"]")
        violations = []

        for jsfile in js_dir.rglob('*.js'):
            content = jsfile.read_text(errors='replace')
            matches = wrong_pattern.findall(content)
            if matches:
                violations.append(f"{jsfile.relative_to(js_dir)}: {len(matches)} instances")

        assert not violations, \
            f"Wrong CSRF header 'X-CSRFToken' (no dash) found in: {', '.join(violations)}"


# =============================================================================
# UPLOAD & FILE SECURITY TESTS
# =============================================================================

class TestFileUploadSecurity:
    """Test file upload security — path traversal, file types, CSRF."""

    def test_upload_requires_csrf(self, client_no_csrf):
        """POST /api/upload without CSRF is rejected."""
        c = client_no_csrf
        c.get('/api/version')  # establish session
        data = {'file': (BytesIO(b'test content'), 'test.docx')}
        resp = c.post('/api/upload', data=data, content_type='multipart/form-data')
        assert resp.status_code == 403

    def test_upload_path_traversal_blocked(self, client):
        """Upload filenames containing ../ should be rejected or sanitized."""
        c, csrf = client
        # Try uploading with a path traversal filename
        malicious_name = '../../../etc/passwd'
        data = {'file': (BytesIO(b'fake content'), malicious_name)}
        resp = c.post('/api/upload',
                       data=data,
                       content_type='multipart/form-data',
                       headers={'X-CSRF-Token': csrf})
        # Should either reject (400/403) or sanitize the filename
        if resp.status_code == 200:
            result = get_json(resp)
            # If accepted, verify the filename was sanitized (no path components)
            if result and result.get('data', {}).get('filename'):
                saved_name = result['data']['filename']
                assert '..' not in saved_name, f"Path traversal in saved filename: {saved_name}"
        # Status 400 or 415 = correctly rejected
        assert resp.status_code in (200, 400, 415, 422), \
            f"Unexpected status for path traversal upload: {resp.status_code}"

    def test_upload_invalid_extension_rejected(self, client):
        """Non-document file extensions should be rejected."""
        c, csrf = client
        bad_files = [
            ('malware.exe', b'MZ\x90\x00'),
            ('script.sh', b'#!/bin/bash\nrm -rf /'),
            ('hack.py', b'import os; os.system("whoami")'),
        ]
        for filename, content in bad_files:
            data = {'file': (BytesIO(content), filename)}
            resp = c.post('/api/upload',
                           data=data,
                           content_type='multipart/form-data',
                           headers={'X-CSRF-Token': csrf})
            # Should reject with 400 or 415 (unsupported media type)
            assert resp.status_code in (400, 415, 422), \
                f"File '{filename}' should be rejected, got status {resp.status_code}"

    def test_upload_no_file_returns_error(self, client):
        """POST /api/upload with no file returns 400, not 500."""
        c, csrf = client
        resp = c.post('/api/upload',
                       data={},
                       content_type='multipart/form-data',
                       headers={'X-CSRF-Token': csrf})
        assert resp.status_code in (400, 422), \
            f"Empty upload should return 400, got {resp.status_code}"


# =============================================================================
# POST ENDPOINTS — CSRF ENFORCEMENT
# =============================================================================

class TestPostCSRFEnforcement:
    """Verify CSRF is enforced on all state-changing POST/PUT/DELETE endpoints."""

    # Endpoints that use @require_csrf decorator
    POST_ENDPOINTS = [
        # Diagnostics (now protected via diagnostic_export.py)
        '/api/diagnostics/export',
        # Roles (use @require_csrf via blueprint)
        '/api/roles/adjudicate',
        '/api/roles/rename',
        '/api/roles/auto-adjudicate',
        '/api/roles/adjudicate/batch',
        '/api/roles/update-category',
        '/api/roles/verify',
        '/api/roles/matrix/export',
        '/api/roles/bulk-delete-statements',
        # Scan History
        '/api/scan-history/clear',
        '/api/scan-history/statements/deduplicate',
        # Data
        '/api/sow/generate',
        '/api/data/clear-roles',
        '/api/learner/record',
        '/api/learner/predict',
        '/api/learner/patterns/clear',
    ]

    def test_all_post_endpoints_require_csrf(self, client_no_csrf):
        """Every POST endpoint should return 403 without CSRF token."""
        c = client_no_csrf
        c.get('/api/version')  # establish session

        for ep in self.POST_ENDPOINTS:
            resp = c.post(ep,
                          data=json.dumps({}),
                          content_type='application/json')
            assert resp.status_code == 403, \
                f"{ep} returned {resp.status_code} without CSRF (expected 403)"


# =============================================================================
# GRACEFUL ERROR HANDLING TESTS
# =============================================================================

class TestGracefulErrors:
    """Test endpoints return graceful errors (not 500) for missing data."""

    def test_export_without_session_data(self, client):
        """POST /api/export without active scan returns error, not 500."""
        c, csrf = client
        resp = c.post('/api/export',
                       data=json.dumps({}),
                       content_type='application/json',
                       headers={'X-CSRF-Token': csrf})
        # Should be 400 (no data) or success with empty — NOT 500
        assert resp.status_code != 500, \
            f"/api/export returned 500 without session data: {resp.data[:300]}"

    def test_filter_without_session_data(self, client):
        """POST /api/filter without active scan returns error, not 500."""
        c, csrf = client
        resp = c.post('/api/filter',
                       data=json.dumps({'severity': 'high'}),
                       content_type='application/json',
                       headers={'X-CSRF-Token': csrf})
        assert resp.status_code != 500, \
            f"/api/filter returned 500 without session data: {resp.data[:300]}"

    def test_review_result_nonexistent_job(self, client):
        """GET /api/review/result/<bad_id> returns 404 or graceful error, not 500."""
        c, _ = client
        resp = c.get('/api/review/result/nonexistent-job-id-12345')
        assert resp.status_code in (200, 404), \
            f"/api/review/result returned {resp.status_code} for nonexistent job"

    def test_compare_diff_without_data(self, client):
        """POST /api/compare/diff without scan IDs returns error, not 500."""
        c, csrf = client
        resp = c.post('/api/compare/diff',
                       data=json.dumps({}),
                       content_type='application/json',
                       headers={'X-CSRF-Token': csrf})
        assert resp.status_code != 500, \
            f"/api/compare/diff returned 500 without data: {resp.data[:300]}"

    def test_scan_history_delete_nonexistent(self, client):
        """DELETE /api/scan-history/999999 returns graceful error."""
        c, csrf = client
        resp = c.delete('/api/scan-history/999999',
                         headers={'X-CSRF-Token': csrf})
        # 404 or 200 with error message — not 500
        assert resp.status_code != 500, \
            f"Delete nonexistent scan returned 500: {resp.data[:300]}"

    def test_job_status_nonexistent(self, client):
        """GET /api/job/nonexistent-id returns graceful error."""
        c, _ = client
        resp = c.get('/api/job/nonexistent-job-id-99999')
        assert resp.status_code in (200, 404), \
            f"/api/job/<bad_id> returned {resp.status_code}: {resp.data[:300]}"

    def test_folder_scan_progress_nonexistent(self, client):
        """GET /api/review/folder-scan-progress/<bad_id> returns graceful error."""
        c, _ = client
        resp = c.get('/api/review/folder-scan-progress/nonexistent-scan-id')
        assert resp.status_code in (200, 404), \
            f"Folder scan progress returned {resp.status_code} for bad ID"


# =============================================================================
# REGRESSION TESTS — SPECIFIC BUG FIXES
# =============================================================================

class TestRegressions:
    """Regression tests for specific bugs that were fixed."""

    def test_rlock_deadlock_regression(self, client):
        """
        Regression: diagnostic_export.py used threading.Lock which deadlocked
        when export_diagnostics() held lock then called methods that also acquired it.
        Fixed by switching to threading.RLock (reentrant lock).
        POST /api/diagnostics/export must complete within 5 seconds.
        """
        c, csrf = client
        start = time.monotonic()
        resp = c.post('/api/diagnostics/export',
                       data=json.dumps({'format': 'json', 'include_system_info': True}),
                       content_type='application/json',
                       headers={'X-CSRF-Token': csrf})
        elapsed = time.monotonic() - start
        assert elapsed < 5.0, \
            f"RLock deadlock regression: export took {elapsed:.1f}s (limit: 5s)"
        assert resp.status_code == 200

    def test_version_consistency(self, client):
        """
        Regression: /api/version was returning stale version due to import-time caching.
        Must match root version.json.
        """
        c, _ = client
        resp = c.get('/api/version')
        api_data = get_json(resp)
        api_version = api_data.get('app_version') or api_data.get('version') or (api_data.get('data', {}) or {}).get('version')

        root_version = json.loads(
            (Path(__file__).parent.parent / 'version.json').read_text()
        )['version']

        assert api_version == root_version, \
            f"API version ({api_version}) != file version ({root_version})"

    def test_health_check_completeness(self, client):
        """
        Regression: health check was only reporting 15 packages.
        Must report 25+ packages after fix.
        """
        c, _ = client
        resp = c.get('/api/diagnostics/health')
        data = assert_success_response(resp)
        packages = data.get('data', {}).get('packages', {})
        assert len(packages) >= 25, \
            f"Health check only reports {len(packages)} packages (expected 25+)"

    def test_reportlab_sanitization_html(self):
        """
        Regression: ReportLab PDF crashed on role names containing < > &.
        _sanitize_for_reportlab must escape these characters.
        """
        from adjudication_report import _sanitize_for_reportlab
        assert _sanitize_for_reportlab('Case<Br>Group') == 'Case&lt;Br&gt;Group'
        assert _sanitize_for_reportlab('R&D Department') == 'R&amp;D Department'
        assert _sanitize_for_reportlab('A&B<C>D') == 'A&amp;B&lt;C&gt;D'
        assert _sanitize_for_reportlab('') == ''
        assert _sanitize_for_reportlab(None) == ''

    def test_reportlab_sanitization_order(self):
        """
        Regression: Ampersand must be escaped FIRST to avoid &amp;lt; artifacts.
        """
        from adjudication_report import _sanitize_for_reportlab
        # If & is not escaped first, <tag> becomes &lt;tag&gt; then & in &lt; becomes &amp;lt;
        result = _sanitize_for_reportlab('A&B<C>D')
        assert result == 'A&amp;B&lt;C&gt;D', f"Wrong escape order: {result}"

    def test_diagnostic_export_uses_rlock(self):
        """
        Regression: diagnostic_export.py must use RLock (reentrant), not Lock.
        Source code check.
        """
        diag_path = Path(__file__).parent.parent / 'diagnostic_export.py'
        content = diag_path.read_text()
        # Should use RLock, not plain Lock for the DiagnosticCollector
        assert 'threading.RLock()' in content, \
            "diagnostic_export.py should use threading.RLock(), not threading.Lock()"


# =============================================================================
# RESPONSE FORMAT TESTS
# =============================================================================

class TestResponseFormats:
    """Verify API response structure conventions."""

    def test_success_responses_have_success_field(self, client):
        """All API JSON responses should have a 'success' boolean field."""
        c, _ = client
        endpoints = [
            '/api/config',
            '/api/scan-history',
            '/api/roles/dictionary',
            '/api/function-categories',
            '/api/metrics/dashboard',
        ]
        for ep in endpoints:
            resp = c.get(ep)
            data = get_json(resp)
            assert data is not None, f"{ep} returned non-JSON response"
            assert 'success' in data, f"{ep} missing 'success' field: {list(data.keys())}"

    def test_error_responses_have_error_object(self, client_no_csrf):
        """Error responses should include error object with code and message."""
        c = client_no_csrf
        c.get('/api/version')  # establish session
        # Trigger a CSRF error on an endpoint that enforces CSRF
        resp = c.post('/api/roles/adjudicate',
                       data=json.dumps({}),
                       content_type='application/json')
        assert resp.status_code == 403
        data = get_json(resp)
        assert data is not None
        assert 'error' in data, f"Error response missing 'error' field: {data}"
        assert 'code' in data['error'], f"Error missing 'code': {data['error']}"
        assert 'message' in data['error'], f"Error missing 'message': {data['error']}"

    def test_security_headers_present(self, client):
        """All responses should include security headers."""
        c, _ = client
        resp = c.get('/api/version')
        assert resp.headers.get('X-Content-Type-Options') == 'nosniff'
        assert resp.headers.get('X-Frame-Options') == 'SAMEORIGIN'
        assert resp.headers.get('X-XSS-Protection') == '1; mode=block'
        assert 'X-Correlation-ID' in resp.headers

    def test_api_cache_control_headers(self, client):
        """API responses should have no-cache headers."""
        c, _ = client
        resp = c.get('/api/config')
        cache_control = resp.headers.get('Cache-Control', '')
        assert 'no-cache' in cache_control or 'no-store' in cache_control, \
            f"API response missing no-cache header: {cache_control}"


# =============================================================================
# UPDATE SYSTEM TESTS
# =============================================================================

class TestUpdateSystem:
    """Test update management endpoints."""

    def test_updates_status(self, client):
        """GET /api/updates/status returns update system status."""
        c, _ = client
        resp = c.get('/api/updates/status')
        # May return 200 or 404 depending on update manager availability
        assert resp.status_code in (200, 404), \
            f"/api/updates/status returned {resp.status_code}"

    def test_updates_check(self, client):
        """GET /api/updates/check returns update availability."""
        c, _ = client
        resp = c.get('/api/updates/check')
        assert resp.status_code in (200, 404), \
            f"/api/updates/check returned {resp.status_code}"

    def test_updates_version(self, client):
        """GET /api/updates/version returns version info."""
        c, _ = client
        resp = c.get('/api/updates/version')
        assert resp.status_code in (200, 404), \
            f"/api/updates/version returned {resp.status_code}"

    def test_updates_health(self, client):
        """GET /api/updates/health returns update system health."""
        c, _ = client
        resp = c.get('/api/updates/health')
        assert resp.status_code in (200, 404), \
            f"/api/updates/health returned {resp.status_code}"


# =============================================================================
# REPORTS ENDPOINT TESTS
# =============================================================================

class TestReports:
    """Test report generation endpoints."""

    def test_reports_by_function(self, client):
        """GET /api/roles/reports/by-function returns report data."""
        c, _ = client
        resp = c.get('/api/roles/reports/by-function')
        # Should return 200 or graceful error (empty data is OK)
        assert resp.status_code == 200, \
            f"/api/roles/reports/by-function returned {resp.status_code}"

    def test_reports_by_document(self, client):
        """GET /api/roles/reports/by-document returns report data."""
        c, _ = client
        resp = c.get('/api/roles/reports/by-document')
        assert resp.status_code == 200

    def test_reports_by_owner(self, client):
        """GET /api/roles/reports/by-owner returns report data."""
        c, _ = client
        resp = c.get('/api/roles/reports/by-owner')
        assert resp.status_code == 200


# =============================================================================
# INDEX PAGE TESTS
# =============================================================================

class TestIndexPage:
    """Test the main index page serves correctly."""

    def test_index_returns_html(self, client):
        """GET / returns HTML page with 200 status."""
        c, _ = client
        resp = c.get('/')
        assert resp.status_code == 200
        assert 'text/html' in resp.content_type

    def test_index_contains_csrf_meta(self, client):
        """Index page contains CSRF meta tag."""
        c, _ = client
        resp = c.get('/')
        html = resp.data.decode('utf-8', errors='replace')
        assert 'csrf-token' in html, "Index page missing csrf-token meta tag"

    def test_index_contains_version(self, client):
        """Index page contains version information."""
        c, _ = client
        resp = c.get('/')
        html = resp.data.decode('utf-8', errors='replace')
        # Version is injected into the page by core_routes.py
        assert 'AEGIS' in html, "Index page missing AEGIS branding"

    def test_csrf_token_endpoint(self, client):
        """GET /api/csrf-token returns a fresh token."""
        c, _ = client
        resp = c.get('/api/csrf-token')
        assert resp.status_code == 200
        assert 'X-CSRF-Token' in resp.headers


# =============================================================================
# CONCURRENT REQUEST SAFETY
# =============================================================================

class TestConcurrency:
    """Test that endpoints handle concurrent requests safely."""

    def test_concurrent_get_requests(self, flask_app):
        """Multiple concurrent GET requests don't crash the app."""
        results = []
        errors = []

        def make_request(endpoint):
            try:
                with flask_app.test_client() as c:
                    resp = c.get(endpoint)
                    results.append((endpoint, resp.status_code))
            except Exception as e:
                errors.append((endpoint, str(e)))

        endpoints = [
            '/api/version', '/api/config', '/api/scan-history',
            '/api/roles/dictionary', '/api/diagnostics/health',
            '/api/metrics/dashboard', '/api/health',
        ]

        threads = [threading.Thread(target=make_request, args=(ep,)) for ep in endpoints]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert len(errors) == 0, f"Concurrent request errors: {errors}"
        assert len(results) == len(endpoints), \
            f"Only {len(results)}/{len(endpoints)} requests completed"
        for ep, status in results:
            assert status == 200, f"{ep} returned {status} under concurrent load"


# =============================================================================
# DATA INTEGRITY TESTS
# =============================================================================

class TestDataIntegrity:
    """Test that data returned by APIs is consistent and well-formed."""

    def test_roles_dictionary_has_expected_fields(self, client):
        """Role dictionary entries have required fields."""
        c, _ = client
        resp = c.get('/api/roles/dictionary')
        data = assert_success_response(resp)
        roles = data.get('data', {}).get('roles', [])
        if roles:  # Only test if roles exist
            role = roles[0]
            expected_fields = ['id', 'role_name']
            for field in expected_fields:
                assert field in role, f"Role missing '{field}' field: {list(role.keys())}"

    def test_function_categories_structure(self, client):
        """Function categories have code, name fields."""
        c, _ = client
        resp = c.get('/api/function-categories')
        data = assert_success_response(resp)
        cats = data.get('data', [])
        if isinstance(cats, dict):
            cats = cats.get('categories', [])
        if cats:
            cat = cats[0] if isinstance(cats, list) else list(cats.values())[0]
            if isinstance(cat, dict):
                assert 'code' in cat or 'name' in cat, \
                    f"Category missing expected fields: {list(cat.keys())}"

    def test_scan_history_returns_list(self, client):
        """Scan history returns a list of scan records."""
        c, _ = client
        resp = c.get('/api/scan-history')
        data = assert_success_response(resp)
        # data should contain a list of scans
        scans = data.get('data', data.get('scans', []))
        assert isinstance(scans, (list, dict)), \
            f"Scan history data is not list/dict: {type(scans)}"


# =============================================================================
# ROLES EXPORT ENDPOINTS
# =============================================================================

class TestRolesExports:
    """Test role dictionary export endpoints."""

    def test_dictionary_export_json(self, client):
        """GET /api/roles/dictionary/export returns downloadable JSON."""
        c, _ = client
        resp = c.get('/api/roles/dictionary/export')
        assert resp.status_code == 200
        # Should return JSON or file attachment
        content_type = resp.content_type or ''
        assert 'json' in content_type or 'octet' in content_type or resp.status_code == 200

    def test_dictionary_export_template(self, client):
        """GET /api/roles/dictionary/export-template returns import template."""
        c, _ = client
        resp = c.get('/api/roles/dictionary/export-template')
        assert resp.status_code == 200

    def test_hierarchy_export_html(self, client):
        """GET /api/roles/hierarchy/export-html returns standalone HTML."""
        c, _ = client
        resp = c.get('/api/roles/hierarchy/export-html')
        assert resp.status_code == 200
        # Should be HTML content
        content_type = resp.content_type or ''
        assert 'html' in content_type or 'octet' in content_type

    def test_adjudication_export_html(self, client):
        """GET /api/roles/adjudication/export-html returns kanban HTML."""
        c, _ = client
        resp = c.get('/api/roles/adjudication/export-html')
        assert resp.status_code == 200

    def test_adjudication_export_pdf(self, client):
        """GET /api/roles/adjudication/export-pdf returns PDF report."""
        c, _ = client
        resp = c.get('/api/roles/adjudication/export-pdf')
        # Might return 200 with PDF or error if no data
        assert resp.status_code in (200, 400, 404), \
            f"PDF export returned {resp.status_code}"


# =============================================================================
# HYPERLINK HEALTH ENDPOINTS
# =============================================================================

class TestHyperlinkHealth:
    """Test hyperlink health endpoints."""

    def test_hyperlink_health_status(self, client):
        """GET /api/hyperlink-health/status returns status."""
        c, _ = client
        resp = c.get('/api/hyperlink-health/status')
        assert resp.status_code == 200

    def test_hyperlink_health_validate_requires_csrf(self, client_no_csrf):
        """POST /api/hyperlink-health/validate without CSRF returns 403."""
        c = client_no_csrf
        c.get('/api/version')
        resp = c.post('/api/hyperlink-health/validate',
                       data=json.dumps({}),
                       content_type='application/json')
        assert resp.status_code == 403


# =============================================================================
# SOW (STATEMENT OF WORK) ENDPOINT
# =============================================================================

class TestSOW:
    """Test Statement of Work endpoints."""

    def test_sow_data(self, client):
        """GET /api/sow/data returns SOW data."""
        c, _ = client
        resp = c.get('/api/sow/data')
        data = assert_success_response(resp)

    def test_sow_generate_requires_csrf(self, client_no_csrf):
        """POST /api/sow/generate without CSRF returns 403."""
        c = client_no_csrf
        c.get('/api/version')
        resp = c.post('/api/sow/generate',
                       data=json.dumps({}),
                       content_type='application/json')
        assert resp.status_code == 403


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
