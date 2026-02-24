#!/usr/bin/env python3
"""
AEGIS Cinema Video Fix — Copies downloaded video to app static folder
and updates Start_AEGIS.bat to fix duplicate tab issue.

Run from the AEGIS install directory.
"""
import os
import sys
import shutil
import ssl
import urllib.request


REPO = "nicholasgeorgeson-prog/AEGIS"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"


def get_ssl_context():
    """Get SSL context with fallback."""
    try:
        ctx = ssl.create_default_context()
        return ctx, "default"
    except Exception:
        pass
    try:
        ctx = ssl._create_unverified_context()
        return ctx, "unverified"
    except Exception:
        return None, "none"


def download_file(url, dest, ctx):
    """Download a file from URL."""
    req = urllib.request.Request(url, headers={"User-Agent": "AEGIS-Updater/6.0.2"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            data = resp.read()
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
        return len(data)
    except Exception as e:
        print(f"  [FAIL] {e}")
        return 0


def main():
    print("")
    print("  ==========================================================")
    print("    AEGIS Cinema Video Fix + Dual-Tab Fix")
    print("  ==========================================================")
    print("")

    # Find AEGIS directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_py = os.path.join(script_dir, "app.py")
    static_video = os.path.join(script_dir, "static", "video")

    if not os.path.exists(app_py):
        print("  [ERROR] app.py not found. Run this from the AEGIS directory.")
        input("\n  Press Enter to exit...")
        return

    ctx, method = get_ssl_context()
    print(f"  AEGIS dir: {script_dir}")
    print(f"  SSL:       {method}")
    print("")

    # ── Fix 1: Copy cinema video to static/video/ ──────────────────
    print("  [1/3] Checking cinema video...")

    home = os.path.expanduser("~")
    video_sources = [
        os.path.join(home, "OneDrive - NGC", "Desktop", "AEGIS_Video", "AEGIS_Cinema_Final_v5.mp4"),
        os.path.join(home, "Desktop", "AEGIS_Video", "AEGIS_Cinema_Final_v5.mp4"),
    ]

    source_video = None
    for vs in video_sources:
        if os.path.exists(vs):
            size_mb = os.path.getsize(vs) / 1048576
            if size_mb > 400:  # Must be >400MB to be the real v5
                source_video = vs
                print(f"  Found v5 video: {vs} ({size_mb:.0f} MB)")
                break

    if source_video:
        os.makedirs(static_video, exist_ok=True)
        dest = os.path.join(static_video, "aegis-showcase.mp4")
        print(f"  Copying to: {dest}")
        print(f"  This may take a moment (571 MB)...", flush=True)
        shutil.copy2(source_video, dest)
        dest_mb = os.path.getsize(dest) / 1048576
        print(f"  [OK] Video installed ({dest_mb:.0f} MB)")
    else:
        print("  [SKIP] v5 video not found in AEGIS_Video folder.")
        print("         Run apply_cinema_v5.py first to download it.")

    # ── Fix 2: Update Start_AEGIS.bat ──────────────────────────────
    print("")
    print("  [2/3] Updating Start_AEGIS.bat (fix duplicate tabs)...")

    bat_url = f"{BASE_URL}/Start_AEGIS.bat"
    bat_dest = os.path.join(script_dir, "Start_AEGIS.bat")

    # Backup existing
    if os.path.exists(bat_dest):
        backup = bat_dest + ".bak"
        shutil.copy2(bat_dest, backup)

    size = download_file(bat_url, bat_dest, ctx)
    if size > 0:
        print(f"  [OK] Start_AEGIS.bat updated ({size} bytes)")
    else:
        print("  [FAIL] Could not download updated Start_AEGIS.bat")

    # ── Fix 3: Update technology-showcase.js (cache-busting) ──────
    print("")
    print("  [3/3] Updating technology-showcase.js (video cache-busting)...")

    js_url = f"{BASE_URL}/static/js/features/technology-showcase.js"
    js_dest = os.path.join(script_dir, "static", "js", "features", "technology-showcase.js")

    if os.path.exists(js_dest):
        backup = js_dest + ".bak"
        shutil.copy2(js_dest, backup)

    size = download_file(js_url, js_dest, ctx)
    if size > 0:
        print(f"  [OK] technology-showcase.js updated ({size} bytes)")
    else:
        print("  [FAIL] Could not download updated technology-showcase.js")

    # ── Summary ───────────────────────────────────────────────────
    print("")
    print("  ==========================================================")
    print("  Done! Changes:")
    print("    1. Cinema video v5 → static/video/aegis-showcase.mp4")
    print("    2. Start_AEGIS.bat → no more duplicate browser tabs")
    print("    3. technology-showcase.js → cache-busted video URL")
    print("")
    print("  Next steps:")
    print("    - Restart AEGIS (double-click Start_AEGIS.bat)")
    print("    - Hard-refresh browser (Ctrl+Shift+R) on first load")
    print("  ==========================================================")
    print("")

    input("  Press Enter to exit...")


if __name__ == "__main__":
    main()
