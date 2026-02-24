#!/usr/bin/env python3
"""
AEGIS Cinema Final v5 — Download from GitHub Release
Downloads AEGIS_Cinema_Final_v5.mp4 (571 MB) to Desktop/AEGIS_Video/
"""
import os, sys, ssl, urllib.request, urllib.error, time

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

def follow_redirects(url, ctx):
    """Manually follow redirects to get the final direct URL."""
    for _ in range(5):
        req = urllib.request.Request(url, headers={"User-Agent": "AEGIS-Updater/6.0.2"})
        req.method = "HEAD"
        try:
            resp = urllib.request.urlopen(req, context=ctx, timeout=30)
            return resp.url  # final URL after redirects
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308):
                url = e.headers.get("Location", url)
            else:
                raise
    return url

def download_large(url, dest, ctx):
    """Download with progress indicator for large files."""
    print("  Resolving download URL...", flush=True)

    # Follow redirects first (GitHub -> S3)
    try:
        final_url = follow_redirects(url, ctx)
        if final_url != url:
            print("  Redirected to CDN", flush=True)
    except Exception:
        final_url = url  # fall back to original

    req = urllib.request.Request(final_url, headers={"User-Agent": "AEGIS-Updater/6.0.2"})

    print("  Connecting...", flush=True)
    resp = urllib.request.urlopen(req, context=ctx, timeout=120)

    total = int(resp.headers.get("Content-Length", 0))
    total_mb = total / 1048576 if total else 0
    downloaded = 0
    chunk_size = 262144  # 256 KB chunks (smaller = more responsive)
    last_print = 0
    start_time = time.time()

    print(f"  Total size: {total_mb:.1f} MB", flush=True)
    print("  Downloading...", flush=True)

    with open(dest, "wb") as f:
        while True:
            try:
                chunk = resp.read(chunk_size)
            except Exception as e:
                print(f"\n  Read error at {downloaded/1048576:.1f} MB: {e}", flush=True)
                break
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            dl_mb = downloaded / 1048576

            # Print progress every 10 MB (IDLE-friendly, no \r)
            if dl_mb - last_print >= 10:
                elapsed = time.time() - start_time
                speed = dl_mb / elapsed if elapsed > 0 else 0
                if total:
                    pct = downloaded * 100 / total
                    remaining = (total - downloaded) / 1048576 / speed if speed > 0 else 0
                    print(f"    {dl_mb:.0f}/{total_mb:.0f} MB ({pct:.0f}%) - {speed:.1f} MB/s - ~{remaining:.0f}s left", flush=True)
                else:
                    print(f"    {dl_mb:.0f} MB - {speed:.1f} MB/s", flush=True)
                last_print = dl_mb

    resp.close()
    elapsed = time.time() - start_time
    print(f"  Download complete: {downloaded/1048576:.1f} MB in {elapsed:.0f}s", flush=True)
    return downloaded

def main():
    print("")
    print("  ==========================================================")
    print("    AEGIS Cinema Final v5 Downloader")
    print("  ==========================================================")
    print("")
    print(f"  File:   {FILENAME} (~571 MB)")
    print(f"  Source: GitHub Release {RELEASE_TAG}")
    print("")

    # Determine output directory
    home = os.path.expanduser("~")
    video_dir = None

    # Check common paths
    candidates = [
        os.path.join(home, "OneDrive - NGC", "Desktop", "AEGIS_Video"),
        os.path.join(home, "Desktop", "AEGIS_Video"),
    ]
    for candidate in candidates:
        parent = os.path.dirname(candidate)
        if os.path.isdir(parent):
            video_dir = candidate
            break

    if not video_dir:
        video_dir = os.path.join(home, "Desktop", "AEGIS_Video")

    os.makedirs(video_dir, exist_ok=True)
    dest = os.path.join(video_dir, FILENAME)

    print(f"  Output: {dest}")

    ctx, method = get_ssl_context()
    print(f"  SSL:    {method}")
    print("", flush=True)

    try:
        size = download_large(ASSET_URL, dest, ctx)
        if size > 0:
            print("")
            print(f"  SUCCESS! {size/1048576:.1f} MB downloaded to:")
            print(f"  {dest}")
        else:
            print("")
            print("  WARNING: Downloaded 0 bytes. Try the manual link below.")
    except Exception as e:
        print(f"\n  FAILED: {e}")
        # If partial file exists and is small, remove it
        if os.path.exists(dest) and os.path.getsize(dest) < 1048576:
            os.remove(dest)
            print("  (Removed incomplete file)")

    print("")
    print("  If download fails, download manually from:")
    print(f"  https://github.com/{REPO}/releases/tag/{RELEASE_TAG}")
    print("")

if __name__ == "__main__":
    main()
