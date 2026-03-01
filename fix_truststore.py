#!/usr/bin/env python3
"""Fix truststore installation on Windows embedded Python."""
import os, sys, subprocess

print("=" * 50)
print("  AEGIS — Fix truststore")
print("=" * 50)

# Find embedded Python
python_exe = sys.executable
if os.path.exists("python/python.exe"):
    python_exe = os.path.join(os.getcwd(), "python", "python.exe")
print(f"\n  Python: {python_exe}")

# Step 1: Check current state via subprocess (clean process)
print("\n  Step 1: Checking current state...")
r = subprocess.run(
    [python_exe, "-c", "import truststore; print('OK:', truststore.__file__)"],
    capture_output=True, text=True
)
if r.returncode == 0:
    print(f"  Already working: {r.stdout.strip()}")
    input("\nPress Enter to exit...")
    sys.exit(0)
else:
    print(f"  Import fails: {r.stderr.strip()[:300]}")

# Step 2: Show where pip puts packages
print("\n  Step 2: Checking site-packages...")
r = subprocess.run(
    [python_exe, "-c", "import site; print('\\n'.join(site.getsitepackages()))"],
    capture_output=True, text=True
)
site_dirs = r.stdout.strip().split('\n') if r.returncode == 0 else []
for d in site_dirs:
    print(f"    {d}")
    ts_path = os.path.join(d.strip(), "truststore")
    if os.path.isdir(ts_path):
        print(f"    ^ truststore found here!")

# Step 3: Install from wheel
wheel = os.path.join("wheels", "truststore-0.10.4-py3-none-any.whl")
if not os.path.isfile(wheel):
    print(f"\n  [ERROR] Wheel not found: {wheel}")
    input("\nPress Enter to exit...")
    sys.exit(1)

print(f"\n  Step 3: Installing from {wheel} ({os.path.getsize(wheel):,} bytes)...")
r = subprocess.run(
    [python_exe, "-m", "pip", "install", "--force-reinstall", "--no-deps", wheel],
    capture_output=True, text=True, timeout=120
)
print(f"    pip exit code: {r.returncode}")
if r.stdout.strip():
    print(f"    stdout: {r.stdout.strip()}")
if r.stderr.strip():
    print(f"    stderr: {r.stderr.strip()[:300]}")

# Step 4: Verify in a FRESH subprocess (avoids import cache)
print("\n  Step 4: Verifying import in fresh process...")
r = subprocess.run(
    [python_exe, "-c",
     "import truststore; print('SUCCESS:', truststore.__file__); "
     "truststore.inject_into_ssl(); print('inject_into_ssl() works')"],
    capture_output=True, text=True
)
if r.returncode == 0:
    print(f"  {r.stdout.strip()}")
    print("\n  [OK] truststore is installed and working!")
else:
    print(f"  STILL FAILING: {r.stderr.strip()[:500]}")

    # Step 5: Diagnostic — check what's actually in site-packages
    print("\n  Step 5: Diagnostics...")
    r2 = subprocess.run(
        [python_exe, "-m", "pip", "show", "truststore"],
        capture_output=True, text=True
    )
    print(f"    pip show:\n{r2.stdout.strip()}")

    r3 = subprocess.run(
        [python_exe, "-c",
         "import importlib.util; "
         "spec = importlib.util.find_spec('truststore'); "
         "print('find_spec:', spec)"],
        capture_output=True, text=True
    )
    print(f"    find_spec: {r3.stdout.strip()}")
    if r3.stderr.strip():
        print(f"    find_spec err: {r3.stderr.strip()[:200]}")

    # Check Python version compatibility
    r4 = subprocess.run(
        [python_exe, "-c", "import sys; print(f'Python {sys.version}')"],
        capture_output=True, text=True
    )
    print(f"    {r4.stdout.strip()}")

    print("\n  [FAIL] Could not resolve. Please share this output.")

input("\nPress Enter to exit...")
