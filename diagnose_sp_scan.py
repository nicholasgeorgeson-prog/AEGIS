#!/usr/bin/env python3
"""
AEGIS SP Scan Diagnostic Tool
Checks everything needed to diagnose why the cinematic dashboard isn't appearing.
Run from the AEGIS install directory, then paste the output.
"""

import os
import sys
import json
import hashlib
import platform
from datetime import datetime

DIVIDER = '=' * 70
MARKER = '__AEGIS_SP_CINEMATIC'

def main():
    lines = []
    def log(msg=''):
        print(msg)
        lines.append(msg)

    log(DIVIDER)
    log('AEGIS SP Scan Diagnostic Report')
    log(f'Generated: {datetime.now().isoformat()}')
    log(f'Platform: {platform.system()} {platform.release()} ({platform.machine()})')
    log(f'Python: {sys.version}')
    log(f'CWD: {os.getcwd()}')
    log(DIVIDER)

    # 1. Check we're in the right directory
    log('\n[1] DIRECTORY CHECK')
    for f in ['app.py', 'static/js/app.js', 'version.json', 'static/version.json', 'templates/index.html']:
        exists = os.path.exists(f)
        size = os.path.getsize(f) if exists else 0
        log(f'  {f}: {"EXISTS" if exists else "MISSING"} ({size:,} bytes)')

    # 2. Version files
    log('\n[2] VERSION FILES')
    for vf in ['version.json', 'static/version.json']:
        if os.path.exists(vf):
            try:
                with open(vf, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                log(f'  {vf}: version={data.get("version", "???")} release_date={data.get("release_date", "???")}')
            except Exception as e:
                log(f'  {vf}: ERROR reading - {e}')
        else:
            log(f'  {vf}: MISSING')

    # 3. app.js detailed analysis
    log('\n[3] APP.JS ANALYSIS')
    app_js = 'static/js/app.js'
    if os.path.exists(app_js):
        size = os.path.getsize(app_js)
        mtime = datetime.fromtimestamp(os.path.getmtime(app_js)).isoformat()
        log(f'  File size: {size:,} bytes')
        log(f'  Last modified: {mtime}')

        with open(app_js, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # MD5 hash (first 100KB and full file)
        log(f'  Full file MD5: {hashlib.md5(content.encode()).hexdigest()}')
        log(f'  First 100KB MD5: {hashlib.md5(content[:102400].encode()).hexdigest()}')

        # Check for diagnostic marker
        marker_found = MARKER in content
        log(f'  Diagnostic marker ({MARKER}): {"FOUND" if marker_found else "NOT FOUND"}')
        if marker_found:
            idx = content.index(MARKER)
            # Show 200 chars around the marker
            start = max(0, idx - 100)
            end = min(len(content), idx + 150)
            snippet = content[start:end].replace('\n', '\\n')
            log(f'  Marker context (pos {idx}): ...{snippet}...')

        # Check for key SP scan functions/identifiers
        log('\n  Key SP scan identifiers:')
        checks = [
            ('_startSPSelectedScan', 'SP selected scan function'),
            ('sharepoint-scan-selected', 'SP scan API endpoint'),
            ('_spScanUsingBatchDash', 'SP-uses-batch-dashboard flag'),
            ('sp-scan-dashboard', 'Old SP dashboard element ID'),
            ('batch-progress', 'Cinematic dashboard element ID'),
            ('AEGIS SP CINEMATIC', 'Cinematic diagnostic log label'),
            ('AEGIS SP', 'General SP diagnostic log label'),
            ('_renderSpFileSelector', 'File selector renderer'),
            ('btnSpScan', 'SP scan button reference'),
            ('window.__AEGIS_SP_CINEMATIC', 'Version marker assignment'),
        ]
        for term, desc in checks:
            count = content.count(term)
            log(f'    "{term}": {count} occurrence(s) — {desc}')

        # Check what happens in btnSpScan click handler area
        log('\n  btnSpScan click handler search:')
        # Find the handler
        handler_patterns = [
            "btnSpScan.addEventListener('click'",
            'btnSpScan.addEventListener("click"',
            "btnSpScan.addEventListener( 'click'",
        ]
        for pat in handler_patterns:
            idx = content.find(pat)
            if idx >= 0:
                log(f'    Found handler at char position {idx}')
                # Show 500 chars after the handler start
                snippet = content[idx:idx+500].replace('\n', '\\n')
                log(f'    Handler start: {snippet}')
                break
        else:
            log('    WARNING: btnSpScan click handler NOT FOUND')

        # Check if batch-progress is referenced in SP scan context
        log('\n  SP scan → batch-progress wiring:')
        # Search for getElementById('batch-progress') near SP scan code
        bp_refs = []
        search_start = 0
        while True:
            idx = content.find("'batch-progress'", search_start)
            if idx < 0:
                idx = content.find('"batch-progress"', search_start)
            if idx < 0:
                break
            # Get surrounding context
            ctx_start = max(0, idx - 80)
            ctx_end = min(len(content), idx + 80)
            ctx = content[ctx_start:ctx_end].replace('\n', '\\n')
            bp_refs.append((idx, ctx))
            search_start = idx + 1
        log(f'    "batch-progress" references: {len(bp_refs)}')
        for pos, ctx in bp_refs[:5]:
            log(f'      pos {pos}: ...{ctx}...')

    else:
        log('  FILE MISSING!')

    # 4. index.html checks
    log('\n[4] INDEX.HTML ANALYSIS')
    index_html = 'templates/index.html'
    if os.path.exists(index_html):
        with open(index_html, 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()

        log(f'  File size: {len(html):,} chars')

        # Check script tags for app.js
        log('\n  Script tags referencing app.js:')
        import re
        script_tags = re.findall(r'<script[^>]*src=["\'][^"\']*app\.js[^"\']*["\'][^>]*>', html)
        for tag in script_tags:
            log(f'    {tag}')
        if not script_tags:
            log('    WARNING: No script tags found for app.js!')

        # Check for SP-related elements
        log('\n  SP scan HTML elements:')
        sp_elements = [
            ('id="btn-sp-scan"', 'SP Scan button'),
            ('id="sp-scan-dashboard"', 'Old SP dashboard'),
            ('id="batch-progress"', 'Cinematic batch dashboard'),
            ('id="sp-file-selector"', 'SP file selector'),
            ('id="btn-sp-connect-scan"', 'Connect & Scan button'),
        ]
        for pattern, desc in sp_elements:
            found = pattern in html
            log(f'    {pattern}: {"FOUND" if found else "MISSING"} — {desc}')
            if found:
                idx = html.index(pattern)
                start = max(0, idx - 60)
                end = min(len(html), idx + 100)
                snippet = html[start:end].replace('\n', '\\n').replace('  ', ' ')
                log(f'      context: ...{snippet}...')

    else:
        log('  FILE MISSING!')

    # 5. guide-system.js check (robot voice fix)
    log('\n[5] GUIDE-SYSTEM.JS CHECK')
    gs_file = 'static/js/features/guide-system.js'
    if os.path.exists(gs_file):
        size = os.path.getsize(gs_file)
        mtime = datetime.fromtimestamp(os.path.getmtime(gs_file)).isoformat()
        log(f'  File size: {size:,} bytes')
        log(f'  Last modified: {mtime}')
        with open(gs_file, 'r', encoding='utf-8', errors='ignore') as f:
            gs = f.read()
        log(f'  _isIntro flag: {"FOUND" if "_isIntro" in gs else "NOT FOUND"}')
    else:
        log(f'  FILE MISSING!')

    # 6. Server check
    log('\n[6] SERVER CHECK')
    try:
        import urllib.request
        resp = urllib.request.urlopen('http://localhost:5050/api/version', timeout=5)
        data = json.loads(resp.read().decode())
        log(f'  Server responding: YES')
        log(f'  Server version: {data.get("version", data.get("data", {}).get("version", "???"))}')
    except Exception as e:
        log(f'  Server responding: NO — {e}')

    # 7. Fetch app.js from server and compare
    log('\n[7] SERVER-SERVED APP.JS vs DISK FILE')
    try:
        import urllib.request
        resp = urllib.request.urlopen('http://localhost:5050/static/js/app.js', timeout=30)
        server_content = resp.read().decode('utf-8', errors='ignore')
        log(f'  Server app.js size: {len(server_content):,} chars')
        log(f'  Server app.js MD5: {hashlib.md5(server_content.encode()).hexdigest()}')
        log(f'  Server has marker: {MARKER in server_content}')

        # Compare with disk
        if os.path.exists(app_js):
            with open(app_js, 'r', encoding='utf-8', errors='ignore') as f:
                disk_content = f.read()
            if disk_content == server_content:
                log(f'  Disk vs Server: IDENTICAL ✓')
            else:
                log(f'  Disk vs Server: DIFFERENT!')
                log(f'    Disk size:   {len(disk_content):,} chars')
                log(f'    Server size: {len(server_content):,} chars')
                # Find first difference
                for i, (a, b) in enumerate(zip(disk_content, server_content)):
                    if a != b:
                        log(f'    First diff at char {i}')
                        log(f'      Disk:   {repr(disk_content[i:i+50])}')
                        log(f'      Server: {repr(server_content[i:i+50])}')
                        break
    except Exception as e:
        log(f'  Could not fetch from server: {e}')

    # 8. Check the actual HTML page served to browser
    log('\n[8] SERVED INDEX.HTML — SCRIPT TAG CHECK')
    try:
        import urllib.request
        resp = urllib.request.urlopen('http://localhost:5050/', timeout=10)
        served_html = resp.read().decode('utf-8', errors='ignore')
        log(f'  Served HTML size: {len(served_html):,} chars')

        # Find app.js script tags
        script_tags = re.findall(r'<script[^>]*src=["\']([^"\']*app\.js[^"\']*)["\'][^>]*>', served_html)
        for src in script_tags:
            log(f'  app.js script src: {src}')

        # Check version param
        version_params = re.findall(r'app\.js\?v=([^\s"\'&]+)', served_html)
        for vp in version_params:
            log(f'  Cache-bust version param: ?v={vp}')

    except Exception as e:
        log(f'  Could not fetch index page: {e}')

    # Save report
    log('\n' + DIVIDER)
    log('END OF DIAGNOSTIC REPORT')
    log(DIVIDER)

    report_file = 'sp_scan_diagnostic.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'\nReport saved to: {os.path.abspath(report_file)}')
    print('Paste the contents of this file for analysis.')

if __name__ == '__main__':
    main()
