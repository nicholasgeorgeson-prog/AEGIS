#!/usr/bin/env python3
"""
AEGIS Help Docs & Version History Auto-Sync
=============================================
Reads version.json and updates help-docs.js:
  1. Syncs the HelpDocs.version field
  2. Syncs the HelpDocs.lastUpdated field
  3. Updates the comment header version string
  4. Regenerates the Version History HTML from ALL version.json changelog entries
     (136 entries from v5.9.53 back to v3.0.92)

Usage:
    python3 sync_help_version.py              # Sync everything
    python3 sync_help_version.py --dry-run    # Show changes without writing

Run this after updating version.json to keep help docs in sync.
Also syncs root version.json -> static/version.json.
"""

import json
import re
import os
import sys
from datetime import datetime


def load_version_json(path):
    """Load and parse version.json."""
    with open(path, 'r') as f:
        return json.load(f)


def format_date(date_str):
    """Convert YYYY-MM-DD to 'February 22, 2026' format."""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%B %d, %Y').replace(' 0', ' ')
    except (ValueError, TypeError):
        return date_str


def _format_change(text):
    """Format a changelog entry with bold prefix labels (NEW/ENH/FIX)."""
    # Match patterns like "NEW: Feature name — description"
    m = re.match(r'^(NEW|ENH|FIX|BREAKING|REVERT|PERF):\s*(.+)', text)
    if m:
        prefix = m.group(1)
        rest = m.group(2)
        # Split on first em-dash or double-dash for description
        parts = re.split(r'\s*[—–]\s*|\s*--\s*', rest, maxsplit=1)
        if len(parts) == 2:
            return f'<strong>{prefix}: {_escape_html(parts[0])}</strong> &mdash; {_escape_html(parts[1])}'
        else:
            return f'<strong>{prefix}: {_escape_html(rest)}</strong>'
    return _escape_html(text)


def generate_changelog_html(changelog_entries):
    """Generate HTML for the version-history section from ALL changelog entries.

    Groups by major version (v5.x, v4.x, v3.x) with collapsible sections
    for older entries. Most recent version gets 'changelog-current' class.
    """
    lines = []
    lines.append('<div class="help-changelog">')

    for i, entry in enumerate(changelog_entries):
        version = entry.get('version', '?')
        date = entry.get('date', '')
        changes = entry.get('changes', [])
        tag = entry.get('tag', '')

        css_class = ' changelog-current' if i == 0 else ''
        lines.append(f'    <div class="changelog-version{css_class}">')
        lines.append(f'        <h3>v{version} <span class="changelog-date">{format_date(date)}</span></h3>')

        if tag:
            lines.append(f'        <p><strong>{_escape_html(tag)}</strong></p>')

        if changes:
            lines.append('        <ul>')
            for change in changes:
                lines.append(f'            <li>{_format_change(change)}</li>')
            lines.append('        </ul>')

        lines.append('    </div>')

    lines.append('</div>')
    return '\n'.join(lines)


def _escape_html(text):
    """Escape HTML special chars but preserve existing HTML entities and tags."""
    # Don't double-escape — if text already has &mdash; etc., leave it
    if '&' in text and ';' in text:
        return text
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def sync_help_docs(help_docs_path, version_data, dry_run=False):
    """Update help-docs.js with current version info and changelog."""
    with open(help_docs_path, 'r') as f:
        content = f.read()

    original = content
    changes = []

    # 1. Update version field
    version = version_data.get('version', '')
    old_match = re.search(r"version:\s*'([^']*)'", content)
    if old_match and old_match.group(1) != version:
        content = content[:old_match.start(1)] + version + content[old_match.end(1):]
        changes.append(f"  version: '{old_match.group(1)}' -> '{version}'")

    # 2. Update lastUpdated field
    release_date = version_data.get('release_date', datetime.now().strftime('%Y-%m-%d'))
    old_updated = re.search(r"lastUpdated:\s*'([^']*)'", content)
    if old_updated and old_updated.group(1) != release_date:
        content = content[:old_updated.start(1)] + release_date + content[old_updated.end(1):]
        changes.append(f"  lastUpdated: '{old_updated.group(1)}' -> '{release_date}'")

    # 2b. Update comment header " * Version: X.Y.Z"
    header_match = re.search(r'(\* Version:\s*)\S+', content)
    if header_match:
        old_header_ver = header_match.group(0).split()[-1]
        if old_header_ver != version:
            content = content[:header_match.start()] + f'* Version: {version}' + content[header_match.end():]
            changes.append(f"  header: Version {old_header_ver} -> {version}")

    # 3. Regenerate version-history changelog HTML
    changelog = version_data.get('changelog', [])
    if changelog:
        new_html = generate_changelog_html(changelog)
        # Find the existing version-history content block
        pattern = r"(HelpDocs\.content\['version-history'\]\s*=\s*\{[^}]*html:\s*`\s*\n)(.*?)(\n\s*`\s*\})"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            old_html = match.group(2)
            if old_html.strip() != new_html.strip():
                content = content[:match.start(2)] + new_html + content[match.end(2):]
                changes.append(f"  changelog: regenerated ({len(changelog)} entries)")

    if not changes:
        print("  No changes needed — help-docs.js is already in sync.")
        return False

    print("  Changes:")
    for c in changes:
        print(c)

    if dry_run:
        print("\n  [DRY RUN] No files modified.")
        return False

    with open(help_docs_path, 'w') as f:
        f.write(content)

    print(f"\n  Updated: {help_docs_path}")
    return True


def main():
    dry_run = '--dry-run' in sys.argv

    # Find project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    version_path = os.path.join(script_dir, 'version.json')
    help_docs_path = os.path.join(script_dir, 'static', 'js', 'help-docs.js')

    print("AEGIS Help Docs Version Sync")
    print("=" * 40)

    if not os.path.exists(version_path):
        print(f"  ERROR: version.json not found at {version_path}")
        return 1

    if not os.path.exists(help_docs_path):
        print(f"  ERROR: help-docs.js not found at {help_docs_path}")
        return 1

    version_data = load_version_json(version_path)
    print(f"  Source: version.json (v{version_data.get('version', '?')})")
    print(f"  Target: help-docs.js")
    print()

    changed = sync_help_docs(help_docs_path, version_data, dry_run)

    # Also sync static/version.json
    static_version_path = os.path.join(script_dir, 'static', 'version.json')
    if os.path.exists(static_version_path):
        with open(version_path, 'r') as f:
            root_content = f.read()
        with open(static_version_path, 'r') as f:
            static_content = f.read()
        if root_content != static_content:
            if not dry_run:
                with open(static_version_path, 'w') as f:
                    f.write(root_content)
                print(f"\n  Synced: static/version.json")
            else:
                print(f"\n  [DRY RUN] Would sync static/version.json")

    return 0


if __name__ == '__main__':
    sys.exit(main())
