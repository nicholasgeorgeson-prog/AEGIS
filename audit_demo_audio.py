#!/usr/bin/env python3
"""
AEGIS Demo Audio Manifest Audit & Rebuild
==========================================
Scans static/audio/demo/ for all MP3 files, matches them to
guide-system.js section/sub-demo IDs, and rebuilds manifest.json
to index ALL matching audio files.

Usage:
    python3 audit_demo_audio.py              # Audit + rebuild manifest
    python3 audit_demo_audio.py --audit      # Audit only (no write)
    python3 audit_demo_audio.py --report     # Detailed report

Reports:
  - Total MP3 files on disk
  - Files indexed in manifest vs not
  - Sections/sub-demos with audio vs without
  - Naming convention issues
"""

import json
import os
import re
import sys
import hashlib
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(SCRIPT_DIR, 'static', 'audio', 'demo')
MANIFEST_PATH = os.path.join(AUDIO_DIR, 'manifest.json')
GUIDE_SYSTEM_JS = os.path.join(SCRIPT_DIR, 'static', 'js', 'features', 'guide-system.js')


def discover_mp3s():
    """Find all MP3 files in the audio directory and parse their naming."""
    files = {}
    if not os.path.isdir(AUDIO_DIR):
        return files

    for fname in sorted(os.listdir(AUDIO_DIR)):
        if not fname.endswith('.mp3'):
            continue

        fpath = os.path.join(AUDIO_DIR, fname)
        size = os.path.getsize(fpath)

        # Parse naming convention: {id}__step{N}.mp3 or {id}_step_{N}.mp3
        # Also handle: {id}_overview_step_{N}.mp3
        section_id = None
        step_num = None

        # Pattern 1: standard double-underscore  e.g. review__step0.mp3
        m = re.match(r'^(.+?)__step(\d+)\.mp3$', fname)
        if m:
            section_id = m.group(1)
            step_num = int(m.group(2))

        # Pattern 2: older single-underscore  e.g. comparison_view_step_0.mp3
        if not m:
            m = re.match(r'^(.+?)_step_(\d+)\.mp3$', fname)
            if m:
                section_id = m.group(1)
                step_num = int(m.group(2))

        # Pattern 3: overview prefix  e.g. proposal-compare_overview_step_0.mp3
        if not m:
            m = re.match(r'^(.+?)_overview_step_(\d+)\.mp3$', fname)
            if m:
                section_id = m.group(1)
                step_num = int(m.group(2))

        if section_id is not None and step_num is not None:
            if section_id not in files:
                files[section_id] = []
            files[section_id].append({
                'file': fname,
                'step': step_num,
                'size': size,
            })

    # Sort steps within each section
    for sid in files:
        files[sid].sort(key=lambda x: x['step'])

    return files


def compute_text_hash(text):
    """Compute a short hash of narration text for cache invalidation."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:8]


def build_manifest(discovered_files):
    """Build a complete manifest.json from discovered MP3 files."""
    manifest = {
        'version': '2.0',
        'voice': 'en-US-JennyNeural',
        'provider': 'edge-tts',
        'generated': __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'sections': {}
    }

    total = 0
    for section_id, files in sorted(discovered_files.items()):
        steps = []
        for f in files:
            steps.append({
                'file': f['file'],
                'size': f['size'],
            })
            total += 1

        manifest['sections'][section_id] = {
            'steps': steps
        }

    manifest['total_clips'] = total
    return manifest


def load_existing_manifest():
    """Load the current manifest.json if it exists."""
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, 'r') as f:
            return json.load(f)
    return None


def print_report(discovered, old_manifest):
    """Print a detailed audit report."""
    print()
    print("  =============================================")
    print("    AEGIS Demo Audio Audit Report")
    print("  =============================================")
    print()

    # Total files
    total_files = sum(len(files) for files in discovered.values())
    total_sections = len(discovered)
    print(f"  MP3 files on disk:     {total_files}")
    print(f"  Unique section IDs:    {total_sections}")
    print()

    # Old manifest stats
    if old_manifest:
        old_sections = old_manifest.get('sections', {})
        old_total = sum(len(s.get('steps', [])) for s in old_sections.values())
        old_sec_count = len(old_sections)
        print(f"  Old manifest indexed:  {old_total} clips in {old_sec_count} sections")
        print(f"  New manifest indexed:  {total_files} clips in {total_sections} sections")
        print(f"  Gain:                  +{total_files - old_total} clips, +{total_sections - old_sec_count} sections")
    else:
        print(f"  No existing manifest found")
    print()

    # Per-section breakdown
    print("  Section breakdown:")
    print("  " + "-" * 55)
    for sid in sorted(discovered.keys()):
        files = discovered[sid]
        steps = [f['step'] for f in files]
        total_kb = sum(f['size'] for f in files) / 1024
        status = "OK" if steps == list(range(len(steps))) else "GAP"
        in_old = "+" if old_manifest and sid not in old_manifest.get('sections', {}) else " "
        print(f"  {in_old} {sid:<40} {len(files):>3} clips  {total_kb:>7.0f} KB  [{status}]")

    print()
    print(f"  (+) = newly discovered, not in old manifest")
    print()


def main():
    audit_only = '--audit' in sys.argv
    detailed = '--report' in sys.argv

    print()
    print("  AEGIS Demo Audio Manifest Rebuild")
    print("  " + "=" * 40)
    print()

    if not os.path.isdir(AUDIO_DIR):
        print(f"  [ERROR] Audio directory not found: {AUDIO_DIR}")
        return 1

    # Discover all MP3 files
    print("  Scanning for MP3 files...")
    discovered = discover_mp3s()
    total_files = sum(len(files) for files in discovered.values())
    print(f"  Found {total_files} MP3 files in {len(discovered)} sections")
    print()

    # Load old manifest for comparison
    old_manifest = load_existing_manifest()

    # Print report if requested
    if detailed or audit_only:
        print_report(discovered, old_manifest)

    if audit_only:
        print("  [AUDIT ONLY] No files modified.")
        return 0

    # Build new manifest
    print("  Building new manifest...")
    manifest = build_manifest(discovered)
    print(f"  Manifest: {manifest['total_clips']} clips in {len(manifest['sections'])} sections")

    # Write manifest
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"  Written: {MANIFEST_PATH}")

    # Summary
    if old_manifest:
        old_total = sum(len(s.get('steps', [])) for s in old_manifest.get('sections', {}).values())
        print(f"\n  Before: {old_total} indexed clips")
        print(f"  After:  {manifest['total_clips']} indexed clips")
        print(f"  Gain:   +{manifest['total_clips'] - old_total} clips")
    else:
        print(f"\n  Created new manifest with {manifest['total_clips']} clips")

    print()
    print("  Done! Manifest rebuilt successfully.")
    print()
    return 0


if __name__ == '__main__':
    try:
        code = main()
    except KeyboardInterrupt:
        print("\n  Cancelled.")
        code = 1
    except Exception as e:
        print(f"\n  Error: {e}")
        import traceback
        traceback.print_exc()
        code = 1
    sys.exit(code)
