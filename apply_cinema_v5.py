#!/usr/bin/env python3
"""
AEGIS Cinema Final v5 — Download from GitHub Release
Downloads AEGIS_Cinema_Final_v5.mp4 (571 MB) to Desktop/AEGIS_Video/
"""
import os, sys, ssl, urllib.request

RELEASE_TAG = "v6.0.2-cinema"
REPO = "nicholasgeorgeson-prog/AEGIS"
FILENAME = "AEGIS_Cinema_Final_v5.mp4"
ASSET_URL = f"https://github.com/{REPO}/releases/download/{RELEASE_TAG}/{FILENAME}"

def get_ssl_context():
    try:
        ctx = ssl.create_default_context()
        return ctx, "system certs"
    except Exception:
        pass
    try:
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
        return ctx, "certifi"
    except Exception:
        pass
    ctx = ssl._create_unverified_context()
    return ctx, "unverified"

def download_large(url, dest, ctx):
    """Download with progress indicator for large files."""
    req = urllib.request.Request(url, headers={"User-Agent": "AEGIS-Updater/6.0.2"})
    with urllib.request.urlopen(req, context=ctx, timeout=600) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        total_mb = total / 1048576 if total else 0
        downloaded = 0
        chunk_size = 1048576  # 1 MB chunks

        with open(dest, "wb") as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                dl_mb = downloaded / 1048576
                if total:
                    pct = downloaded * 100 / total
                    bar_len = 30
                    filled = int(bar_len * downloaded / total)
                    bar = "=" * filled + "-" * (bar_len - filled)
                    print(f"\r  [{bar}] {dl_mb:.1f}/{total_mb:.1f} MB ({pct:.0f}%)", end="", flush=True)
                else:
                    print(f"\r  Downloaded: {dl_mb:.1f} MB", end="", flush=True)

    print()
    return downloaded

def main():
    print(f"""
  ==========================================================
    AEGIS Cinema Final v5 Downloader
  ==========================================================

  File:   {FILENAME} (~571 MB)
  Source: GitHub Release {RELEASE_TAG}
""")

    # Determine output directory
    # Try Desktop/AEGIS_Video first, fall back to current dir
    home = os.path.expanduser("~")
    video_dir = os.path.join(home, "Desktop", "AEGIS_Video")
    if not os.path.isdir(video_dir):
        # Try OneDrive desktop path (NGC Windows)
        for candidate in [
            os.path.join(home, "OneDrive - NGC", "Desktop", "AEGIS_Video"),
            os.path.join(home, "Desktop", "AEGIS_Video"),
        ]:
            if os.path.isdir(os.path.dirname(candidate)):
                video_dir = candidate
                break
        else:
            video_dir = os.getcwd()

    os.makedirs(video_dir, exist_ok=True)
    dest = os.path.join(video_dir, FILENAME)

    print(f"  Output: {dest}")

    ctx, method = get_ssl_context()
    print(f"  SSL:    {method}")
    print()
    print("  Downloading...", flush=True)

    try:
        size = download_large(ASSET_URL, dest, ctx)
        print(f"\n  Done! {size/1048576:.1f} MB downloaded to:")
        print(f"  {dest}")
    except Exception as e:
        print(f"\n  FAILED: {e}")
        print()
        print("  If this fails, download manually from:")
        print(f"  https://github.com/{REPO}/releases/tag/{RELEASE_TAG}")
        return

    print()

if __name__ == "__main__":
    main()
