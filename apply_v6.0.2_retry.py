#!/usr/bin/env python3
"""
AEGIS v6.0.2 - Retry 4 failed audio files
"""
import os, sys, ssl, urllib.request

BASE_URL = "https://raw.githubusercontent.com/nicholasgeorgeson-prog/AEGIS/main/"

FILES = [
    "static/audio/demo/feature_tiles__step2.mp3",
    "static/audio/demo/forge__step2.mp3",
    "static/audio/demo/getting_started__step3.mp3",
    "static/audio/demo/graph_view__step2.mp3",
]

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

def download(url, ctx, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "AEGIS-Updater/6.0.2"})
    with urllib.request.urlopen(req, context=ctx, timeout=timeout) as r:
        return r.read()

def main():
    install_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isfile(os.path.join(install_dir, "app.py")):
        print("  ERROR: Run this from the AEGIS install directory.")
        return

    ctx, method = get_ssl_context()
    print(f"\n  AEGIS v6.0.2 — Retry 4 failed audio files")
    print(f"  SSL: {method}\n")

    ok = 0
    for i, f in enumerate(FILES, 1):
        short = os.path.basename(f)
        print(f"  [{i}/4] {short}...", end=" ", flush=True)
        path = os.path.join(install_dir, f.replace("/", os.sep))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        for attempt in range(3):
            try:
                data = download(BASE_URL + f, ctx, timeout=90)
                with open(path, "wb") as fh:
                    fh.write(data)
                print(f"OK ({len(data)/1024:.1f} KB)")
                ok += 1
                break
            except Exception as e:
                if attempt < 2:
                    print(f"retry {attempt+2}...", end=" ", flush=True)
                else:
                    print(f"FAIL — {e}")

    print(f"\n  Done: {ok}/4 applied\n")

if __name__ == "__main__":
    main()
