#!/usr/bin/env python3
"""
GitHub REST API Push Script for AEGIS v5.3.0
=============================================
Pushes 11 new checker files to GitHub via REST API (git index is stuck in VM).

USAGE:
  python3 github_push_script.py <VALID_PAT>

Where VALID_PAT is a GitHub Personal Access Token with 'repo' scope.

This script will:
1. Create blobs for each file
2. Create a tree combining all blobs with base_tree
3. Create a commit with the tree and parent
4. Update refs/heads/main to point to the new commit
"""

import os
import base64
import json
import subprocess
import sys
from pathlib import Path

# Configuration
REPO_OWNER = "nicholasgeorgeson-prog"
REPO_NAME = "AEGIS"
BRANCH = "main"

# Files to push: (source_path, target_path_in_repo)
FILES_TO_PUSH = [
    ("negation_checker.py", "negation_checker.py"),
    ("text_metrics_checker.py", "text_metrics_checker.py"),
    ("terminology_consistency_checker.py", "terminology_consistency_checker.py"),
    ("subjectivity_checker.py", "subjectivity_checker.py"),
    ("vocabulary_checker.py", "vocabulary_checker.py"),
    ("yake_checker.py", "yake_checker.py"),
    ("similarity_checker.py", "similarity_checker.py"),
    ("advanced_analysis_checkers.py", "advanced_analysis_checkers.py"),
    ("core.py", "core.py"),
    ("templates/index.html", "templates/index.html"),
    ("requirements.txt", "requirements.txt"),
]

COMMIT_MESSAGE = """feat: v5.3.0 spaCy Ecosystem & Deep Analysis Suite — 11 new checkers

New checker modules:
- negation_checker.py: negspacy-powered negation scope analysis
- text_metrics_checker.py: textdescriptives 40+ quality metrics + sentence complexity
- terminology_consistency_checker.py: spacy-wordnet synonym detection
- subjectivity_checker.py: spacytextblob tone/sentiment analysis
- vocabulary_checker.py: lexical_diversity MTLD/HD-D/TTR metrics
- yake_checker.py: YAKE keyword extraction & distribution analysis
- similarity_checker.py: sentence-transformers duplicate requirement detection
- advanced_analysis_checkers.py: coherence, defined-before-used, quantifier precision

Registration:
- 11 new option_mapping entries in core.py
- 8 factory imports with graceful error handling
- 11 UI toggles in index.html under 'spaCy Deep Analysis (v5.3.0)'
- 6 new dependencies in requirements.txt"""


def run_curl(method, url, data=None, pat=None):
    """Run curl command and return JSON response."""
    cmd = ["curl", "-s", "-X", method, "-H", "Accept: application/vnd.github+json"]
    
    if pat:
        cmd.extend(["-H", f"Authorization: token {pat}"])
    
    cmd.append(url)
    
    if data:
        cmd.extend(["-d", json.dumps(data)])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"Invalid response: {result.stdout}\nStderr: {result.stderr}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 github_push_script.py <VALID_PAT>")
        print("\nExample: python3 github_push_script.py ghp_xxxxxxxxxxxxxxxxxxxx")
        print("\nYou can generate a PAT at: https://github.com/settings/tokens")
        sys.exit(1)
    
    pat = sys.argv[1].strip()
    
    if not pat.startswith("ghp_"):
        print("ERROR: Invalid PAT format. Should start with 'ghp_'")
        sys.exit(1)
    
    base_dir = Path(__file__).parent
    
    print("GitHub REST API Push — v5.3.0 AEGIS Checkers")
    print("=" * 60)
    print(f"Target: {REPO_OWNER}/{REPO_NAME} on branch {BRANCH}")
    print()
    
    try:
        # Step 1: Get current HEAD
        print("Step 1: Getting current HEAD SHA...")
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/refs/heads/{BRANCH}"
        ref_data = run_curl("GET", url, pat=pat)
        
        if "message" in ref_data and "Bad credentials" in ref_data["message"]:
            print(f"ERROR: Authentication failed. The provided PAT is invalid or expired.")
            print(f"Response: {ref_data['message']}")
            sys.exit(1)
        
        if "sha" not in ref_data:
            print(f"ERROR: Could not get HEAD SHA")
            print(f"Response: {ref_data}")
            sys.exit(1)
        
        head_sha = ref_data["object"]["sha"]
        print(f"  HEAD SHA: {head_sha}")
        
        # Step 2: Get tree SHA
        print("\nStep 2: Getting base tree SHA...")
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/commits/{head_sha}"
        commit_data = run_curl("GET", url, pat=pat)
        
        if "tree" not in commit_data:
            print(f"ERROR: Could not get tree SHA")
            print(f"Response: {commit_data}")
            sys.exit(1)
        
        base_tree_sha = commit_data["tree"]["sha"]
        print(f"  Base tree SHA: {base_tree_sha}")
        
        # Step 3: Create blobs
        print("\nStep 3: Creating blobs for 11 files...")
        blobs = []
        
        for src_path, target_path in FILES_TO_PUSH:
            full_path = base_dir / src_path
            if not full_path.exists():
                print(f"  ERROR: File not found: {full_path}")
                sys.exit(1)
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create blob
            url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/blobs"
            content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            blob_data = run_curl("POST", url, {"content": content_b64, "encoding": "base64"}, pat=pat)
            
            if "sha" not in blob_data:
                print(f"  ERROR: Could not create blob for {target_path}")
                print(f"  Response: {blob_data}")
                sys.exit(1)
            
            blob_sha = blob_data["sha"]
            blobs.append((target_path, blob_sha))
            print(f"  ✓ {target_path:<40} {blob_sha[:10]}...")
        
        # Step 4: Create tree
        print("\nStep 4: Creating tree from blobs...")
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/trees"
        tree_items = [
            {"path": path, "mode": "100644", "type": "blob", "sha": sha}
            for path, sha in blobs
        ]
        tree_data = run_curl("POST", url, {"tree": tree_items, "base_tree": base_tree_sha}, pat=pat)
        
        if "sha" not in tree_data:
            print(f"ERROR: Could not create tree")
            print(f"Response: {tree_data}")
            sys.exit(1)
        
        new_tree_sha = tree_data["sha"]
        print(f"  New tree SHA: {new_tree_sha}")
        
        # Step 5: Create commit
        print("\nStep 5: Creating commit...")
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/commits"
        commit_data = run_curl("POST", url, {
            "tree": new_tree_sha,
            "parents": [head_sha],
            "message": COMMIT_MESSAGE
        }, pat=pat)
        
        if "sha" not in commit_data:
            print(f"ERROR: Could not create commit")
            print(f"Response: {commit_data}")
            sys.exit(1)
        
        new_commit_sha = commit_data["sha"]
        print(f"  New commit SHA: {new_commit_sha}")
        
        # Step 6: Update ref
        print("\nStep 6: Updating refs/heads/main...")
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/refs/heads/{BRANCH}"
        ref_data = run_curl("PATCH", url, {"sha": new_commit_sha}, pat=pat)
        
        if "ref" not in ref_data:
            print(f"ERROR: Could not update ref")
            print(f"Response: {ref_data}")
            sys.exit(1)
        
        print(f"  ✓ Ref updated to {new_commit_sha[:10]}...")
        
        # Success!
        print("\n" + "=" * 60)
        print("SUCCESS: All 11 files pushed to GitHub!")
        print("=" * 60)
        print(f"\nCommit SHA: {new_commit_sha}")
        print(f"View commit: https://github.com/{REPO_OWNER}/{REPO_NAME}/commit/{new_commit_sha}")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
