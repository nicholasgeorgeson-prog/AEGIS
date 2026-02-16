#!/usr/bin/env python3
"""
Load Test Documents Script
==========================
Loads test documents into AEGIS and opens the browser.
Run this script while the server is running.

Usage: python3 load_test_docs.py
"""

import requests
import webbrowser
import time
import re
from pathlib import Path

BASE_URL = "http://localhost:5050"
TEST_DOCS_DIR = Path(__file__).parent / "test_documents"

def get_csrf_token(session):
    """Get CSRF token from the main page."""
    response = session.get(BASE_URL)
    match = re.search(r'csrf-token" content="([^"]+)"', response.text)
    if match:
        return match.group(1)
    return None

def upload_and_review(session, filepath, csrf_token, session_cookie):
    """Upload a file and run review."""
    print(f"\n📄 Processing: {filepath.name}")

    # Build headers with explicit cookie (requests.Session has issues with cookies on some systems)
    base_headers = {
        'X-CSRF-Token': csrf_token,
        'Cookie': f'session={session_cookie}'
    }

    # Upload
    with open(filepath, 'rb') as f:
        files = {'file': (filepath.name, f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
        response = requests.post(f"{BASE_URL}/api/upload", files=files, headers=base_headers)

    if not response.ok:
        print(f"   ❌ Upload failed: {response.status_code}")
        return None

    result = response.json()
    if not result.get('success'):
        print(f"   ❌ Upload error: {result.get('error')}")
        return None

    print(f"   ✅ Uploaded successfully")

    # Review
    review_headers = {**base_headers, 'Content-Type': 'application/json'}
    response = requests.post(f"{BASE_URL}/api/review", json={}, headers=review_headers)

    if not response.ok:
        print(f"   ❌ Review failed: {response.status_code}")
        return None

    # Handle potential control characters in response
    try:
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', response.text)
        result = requests.compat.json.loads(text)
    except Exception as e:
        print(f"   ❌ Parse error: {e}")
        return None

    if result.get('success'):
        issues = result.get('data', {}).get('issues', [])
        print(f"   ✅ Review complete: {len(issues)} issues found")
        return result
    else:
        print(f"   ❌ Review error: {result.get('error')}")
        return None

def main():
    print("=" * 60)
    print("AEGIS - Test Document Loader")
    print("=" * 60)

    # Find test documents
    docx_files = list(TEST_DOCS_DIR.glob("*.docx"))
    pdf_files = list(TEST_DOCS_DIR.glob("*.pdf"))

    if not docx_files and not pdf_files:
        print(f"\n❌ No test documents found in: {TEST_DOCS_DIR}")
        print("   Run the download script first or add .docx/.pdf files to test_documents/")
        return

    print(f"\n📁 Found {len(docx_files)} DOCX and {len(pdf_files)} PDF files")

    # Create session
    session = requests.Session()

    # Get CSRF token
    csrf_token = get_csrf_token(session)
    if not csrf_token:
        print("\n❌ Could not get CSRF token. Is the server running?")
        return

    # Get session cookie
    session_cookie = session.cookies.get('session')
    if not session_cookie:
        print("\n❌ Could not get session cookie. Is the server running?")
        return

    print(f"🔑 Got CSRF token and session")

    # Process first DOCX file to load into current session
    if docx_files:
        result = upload_and_review(session, docx_files[0], csrf_token, session_cookie)
        if result:
            print(f"\n🎉 Document loaded successfully!")
            print(f"   Opening browser...")

            # Open browser with the session cookie
            # The session is server-side, so we need to pass session info
            # For now, just open the browser - user will see the document
            webbrowser.open(BASE_URL)

            print(f"\n📋 Summary:")
            print(f"   Document: {docx_files[0].name}")
            data = result.get('data', {})
            print(f"   Issues: {len(data.get('issues', []))}")
            print(f"   Roles: {len(data.get('roles', {}))}")

            # List other available documents
            if len(docx_files) > 1:
                print(f"\n📚 Other available test documents:")
                for f in docx_files[1:]:
                    print(f"   - {f.name}")
    else:
        print("\n⚠️  No DOCX files found. Only DOCX files can be auto-loaded.")

if __name__ == "__main__":
    main()
