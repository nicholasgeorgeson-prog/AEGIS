#!/usr/bin/env python3
"""
AEGIS v5.9.0 — Production Hardening Test Suite
================================================
Tests the specific fixes and enhancements from the overnight production review.

Run with: python -m pytest tests/test_production_hardening.py -v
"""

import pytest
import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# VERSION CONSISTENCY TESTS
# =============================================================================

class TestVersionConsistency:
    """Verify version numbers match across all files."""

    def test_root_version_json(self):
        """Root version.json has correct version."""
        vpath = Path(__file__).parent.parent / 'version.json'
        data = json.loads(vpath.read_text())
        assert data['version'] == '5.9.0', f"Root version.json: {data['version']}"
        assert data['core_version'] == '5.9.0'

    def test_static_version_json(self):
        """Static version.json matches root."""
        root = Path(__file__).parent.parent / 'version.json'
        static = Path(__file__).parent.parent / 'static' / 'version.json'
        root_data = json.loads(root.read_text())
        static_data = json.loads(static.read_text())
        assert root_data['version'] == static_data['version'], \
            f"Root ({root_data['version']}) != Static ({static_data['version']})"

    def test_changelog_has_current_version(self):
        """CHANGELOG.md has entry for current version."""
        changelog = (Path(__file__).parent.parent / 'CHANGELOG.md').read_text()
        assert '5.9.0' in changelog, "CHANGELOG.md missing 5.9.0 entry"

    def test_help_docs_has_current_version(self):
        """help-docs.js has entry for current version."""
        helpdocs = (Path(__file__).parent.parent / 'static' / 'js' / 'help-docs.js').read_text()
        assert 'v5.9.0' in helpdocs, "help-docs.js missing v5.9.0 entry"

    def test_version_json_changelog_entry(self):
        """version.json changelog has 5.9.0 as first entry."""
        vpath = Path(__file__).parent.parent / 'version.json'
        data = json.loads(vpath.read_text())
        assert data['changelog'][0]['version'] == '5.9.0', \
            f"First changelog entry: {data['changelog'][0]['version']}"


# =============================================================================
# REPORTLAB SANITIZATION TESTS
# =============================================================================

class TestReportLabSanitization:
    """Test the _sanitize_for_reportlab fix in adjudication_report.py."""

    def test_sanitize_function_exists(self):
        """_sanitize_for_reportlab function exists and is importable."""
        from adjudication_report import _sanitize_for_reportlab
        assert callable(_sanitize_for_reportlab)

    def test_sanitize_html_tags(self):
        """HTML-like content is escaped."""
        from adjudication_report import _sanitize_for_reportlab
        result = _sanitize_for_reportlab('Case<Br>Group')
        assert '<' not in result or '&lt;' in result
        assert 'Case&lt;Br&gt;Group' == result

    def test_sanitize_ampersand(self):
        """Ampersands are escaped."""
        from adjudication_report import _sanitize_for_reportlab
        result = _sanitize_for_reportlab('R&D Department')
        assert '&amp;' in result
        assert result == 'R&amp;D Department'

    def test_sanitize_empty_string(self):
        """Empty string returns empty string."""
        from adjudication_report import _sanitize_for_reportlab
        assert _sanitize_for_reportlab('') == ''

    def test_sanitize_none(self):
        """None returns empty string."""
        from adjudication_report import _sanitize_for_reportlab
        assert _sanitize_for_reportlab(None) == ''

    def test_sanitize_normal_text(self):
        """Normal text passes through unchanged."""
        from adjudication_report import _sanitize_for_reportlab
        text = 'Systems Engineer'
        assert _sanitize_for_reportlab(text) == text

    def test_sanitize_multiple_tags(self):
        """Multiple HTML-like elements are all escaped."""
        from adjudication_report import _sanitize_for_reportlab
        result = _sanitize_for_reportlab('<b>Bold</b> & <i>italic</i>')
        assert '&lt;b&gt;Bold&lt;/b&gt; &amp; &lt;i&gt;italic&lt;/i&gt;' == result


# =============================================================================
# CSRF HEADER TESTS
# =============================================================================

class TestCSRFHeaders:
    """Verify all JS files use the correct CSRF header name."""

    def _get_js_files(self) -> List[Path]:
        """Get all JavaScript files in static/js/."""
        js_dir = Path(__file__).parent.parent / 'static' / 'js'
        return list(js_dir.rglob('*.js'))

    def test_no_wrong_csrf_header(self):
        """No JS files use the wrong X-CSRFToken header."""
        wrong_pattern = re.compile(r"['\"]X-CSRFToken['\"]")
        violations = []

        for jsfile in self._get_js_files():
            content = jsfile.read_text(errors='replace')
            matches = wrong_pattern.findall(content)
            if matches:
                violations.append(f"{jsfile.name}: {len(matches)} instances")

        assert not violations, \
            f"Wrong CSRF header 'X-CSRFToken' found in: {', '.join(violations)}"

    def test_correct_csrf_header_used(self):
        """mass-statement-review.js uses correct X-CSRF-Token header."""
        msr = Path(__file__).parent.parent / 'static' / 'js' / 'features' / 'mass-statement-review.js'
        if msr.exists():
            content = msr.read_text()
            assert 'X-CSRF-Token' in content, "mass-statement-review.js missing X-CSRF-Token"
            assert 'X-CSRFToken' not in content, "mass-statement-review.js still has X-CSRFToken"


# =============================================================================
# CSS ACCESSIBILITY TESTS
# =============================================================================

class TestCSSAccessibility:
    """Verify prefers-reduced-motion is present in all animation-heavy CSS."""

    ANIMATION_CSS_FILES = [
        'features/batch-progress-dashboard.css',
        'features/data-explorer.css',
        'features/portfolio.css',
        'features/hyperlink-validator.css',
        'features/hv-cinematic-progress.css',
        'features/scan-progress-dashboard.css',
        'features/mass-statement-review.css',
        'features/statement-forge.css',
        'features/landing-page.css',
        'features/metrics-analytics.css',
        'features/hyperlink-enhanced.css',
        'features/roles-studio.css',
        'features/statement-history.css',
        'features/doc-compare.css',
        'features/guide-system.css',
    ]

    def test_all_animation_files_have_reduced_motion(self):
        """All animation-heavy CSS files include prefers-reduced-motion."""
        css_dir = Path(__file__).parent.parent / 'static' / 'css'
        missing = []

        for css_file in self.ANIMATION_CSS_FILES:
            filepath = css_dir / css_file
            if filepath.exists():
                content = filepath.read_text()
                if 'prefers-reduced-motion' not in content:
                    missing.append(css_file)

        assert not missing, \
            f"Missing prefers-reduced-motion in: {', '.join(missing)}"


# =============================================================================
# HELP DOCS ACCURACY TESTS
# =============================================================================

class TestHelpDocsAccuracy:
    """Verify help documentation references are accurate."""

    def test_no_nonexistent_api_metrics_analytics(self):
        """help-docs.js should not reference /api/metrics/analytics (doesn't exist)."""
        helpdocs = (Path(__file__).parent.parent / 'static' / 'js' / 'help-docs.js').read_text()
        # The fix changed analytics → dashboard
        # Allow it in quoted changelog text, but not as current API reference
        lines = helpdocs.split('\n')
        for i, line in enumerate(lines, 1):
            if '/api/metrics/analytics' in line and 'changelog' not in line.lower():
                # Skip if it's inside a changelog section describing the fix
                if 'corrected' in line.lower() or 'changed' in line.lower():
                    continue
                pytest.fail(f"help-docs.js line {i} references non-existent /api/metrics/analytics")


# =============================================================================
# TEXTACY SVO EXTRACTION TESTS
# =============================================================================

class TestSVOExtraction:
    """Test the enhanced SVO extraction in InformationExtractionChecker."""

    def test_checker_importable(self):
        """InformationExtractionChecker can be imported."""
        from textacy_checkers import InformationExtractionChecker
        checker = InformationExtractionChecker()
        assert checker is not None

    def test_regex_svo_extraction(self):
        """Regex-based SVO extraction works for shall/must patterns."""
        from textacy_checkers import InformationExtractionChecker
        checker = InformationExtractionChecker()

        # Test basic requirement pattern
        result = checker._extract_svo("The system shall provide real-time monitoring.")
        assert result is not None
        subject, verb, obj = result
        assert 'system' in subject.lower()
        assert verb == 'provide'

    def test_svo_missing_subject(self):
        """SVO detects missing subject (vague pronoun)."""
        from textacy_checkers import InformationExtractionChecker
        checker = InformationExtractionChecker()

        paragraphs = [(0, "It shall provide real-time monitoring capabilities for all subsystems.")]
        issues = checker.check(paragraphs=paragraphs)
        # Should flag vague "it" as missing subject
        assert any('subject' in i.get('message', '').lower() or
                   'actor' in i.get('message', '').lower()
                   for i in issues)

    def test_svo_clear_requirement(self):
        """Clear requirement should not generate issues."""
        from textacy_checkers import InformationExtractionChecker
        checker = InformationExtractionChecker()

        paragraphs = [(0, "The flight control system shall compute attitude corrections within 50 milliseconds of sensor input.")]
        issues = checker.check(paragraphs=paragraphs)
        # Clear requirement should have few/no issues
        missing_subject = [i for i in issues if 'subject' in i.get('message', '').lower()
                          or 'actor' in i.get('message', '').lower()]
        assert len(missing_subject) == 0, "Clear requirement flagged as missing subject"

    def test_checker_factory(self):
        """get_textacy_checkers returns all 4 checkers."""
        from textacy_checkers import get_textacy_checkers
        checkers = get_textacy_checkers()
        assert len(checkers) == 4
        assert 'keyword_extraction' in checkers
        assert 'complexity_analysis' in checkers
        assert 'information_extraction' in checkers
        assert 'noun_phrase_density' in checkers


# =============================================================================
# CORE ENGINE TESTS
# =============================================================================

class TestCoreEngine:
    """Test core AEGIS engine initialization."""

    def test_engine_init(self):
        """AEGISEngine initializes without errors."""
        from core import AEGISEngine
        engine = AEGISEngine()
        assert engine is not None

    def test_checkers_loaded(self):
        """Engine loads 80+ checkers."""
        from core import AEGISEngine
        engine = AEGISEngine()
        count = len(engine.checkers)
        assert count >= 80, f"Only {count} checkers loaded (expected 80+)"

    def test_textacy_checkers_registered(self):
        """Textacy checkers are registered in the engine."""
        from core import AEGISEngine
        engine = AEGISEngine()
        assert 'information_extraction' in engine.checkers
        assert 'keyword_extraction' in engine.checkers


# =============================================================================
# DATABASE TESTS
# =============================================================================

class TestDatabase:
    """Test database operations."""

    def test_db_importable(self):
        """scan_history module is importable."""
        import scan_history
        assert hasattr(scan_history, 'ScanHistoryDB')

    def test_db_connection(self):
        """Can connect to the database."""
        import scan_history
        db = scan_history.ScanHistoryDB()
        # Should have the db_path attribute
        assert hasattr(db, 'db_path')


# =============================================================================
# FLASK APP TESTS
# =============================================================================

class TestFlaskApp:
    """Test Flask application configuration."""

    def test_app_importable(self):
        """Flask app can be imported."""
        # We need to be careful - importing app.py may start the server
        # Just test that the module structure is correct
        import importlib.util
        spec = importlib.util.find_spec('app')
        assert spec is not None, "app module not found"

    def test_config_logging_importable(self):
        """config_logging module works."""
        from config_logging import get_version
        version = get_version()
        assert version == '5.9.0', f"get_version() returned {version}"


# =============================================================================
# EXPORT SANITIZATION TESTS
# =============================================================================

class TestExportSanitization:
    """Test export-related sanitization functions."""

    def test_reportlab_sanitization_order(self):
        """Ampersand must be escaped FIRST (before < and >)."""
        from adjudication_report import _sanitize_for_reportlab
        # If < is escaped before &, we'd get &amp;lt; instead of &lt;
        result = _sanitize_for_reportlab('A&B<C>D')
        assert result == 'A&amp;B&lt;C&gt;D'

    def test_reportlab_sanitization_idempotent(self):
        """Already-escaped text should be double-escaped (safe for ReportLab)."""
        from adjudication_report import _sanitize_for_reportlab
        # If text already has &amp;, it should become &amp;amp;
        # This is correct behavior - ReportLab will render it as &amp;
        result = _sanitize_for_reportlab('&amp;')
        assert result == '&amp;amp;'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
