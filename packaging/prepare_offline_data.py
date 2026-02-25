"""
AEGIS Pre-Packaging Script: Download models and data for offline deployment.
===========================================================================
Run this on a machine WITH internet access before creating the installer package.

This script downloads and caches:
1. NLTK data (punkt, punkt_tab, stopwords, wordnet, omw-1.4,
   averaged_perceptron_tagger, averaged_perceptron_tagger_eng, cmudict)
2. Sentence-Transformers model (all-MiniLM-L6-v2, ~80MB)

The downloaded files are placed in the packaging/ directory so the installer
can copy them to the target machine.

NOTE (v6.1.9): NLTK data packages are now ALSO bundled as ZIP files in
the project root nltk_data/ directory (8 packages, ~57MB total). The apply
script (apply_v6.1.9.py) downloads these from GitHub and extracts them.
app.py sets NLTK_DATA env var to point to nltk_data/ on startup. This
packaging script is still useful for creating fresh offline bundles but
is no longer the only way to get NLTK data packages offline.

Usage:
    cd packaging
    python prepare_offline_data.py

Created by Nicholas Georgeson
"""

import os
import sys
import shutil
from pathlib import Path


def main():
    pkg_dir = Path(__file__).parent

    print("=" * 60)
    print("  AEGIS Offline Data Preparation")
    print("=" * 60)
    print()

    # ── NLTK Data ──────────────────────────────────────────────
    print("[1/2] Downloading NLTK data...")
    nltk_target = pkg_dir / 'nltk_data'
    nltk_target.mkdir(exist_ok=True)

    try:
        import nltk
        datasets = [
            'punkt', 'punkt_tab', 'stopwords', 'wordnet', 'omw-1.4',
            'averaged_perceptron_tagger', 'averaged_perceptron_tagger_eng',
            'cmudict'
        ]
        for ds in datasets:
            print(f"  Downloading {ds}...")
            nltk.download(ds, download_dir=str(nltk_target), quiet=True)
        print(f"  [OK] NLTK data saved to: {nltk_target}")
    except ImportError:
        print("  [ERROR] nltk not installed. Run: pip install nltk")
        return False
    except Exception as e:
        print(f"  [ERROR] NLTK download failed: {e}")
        return False

    # ── Sentence-Transformers Model ────────────────────────────
    print()
    print("[2/2] Downloading sentence-transformers model...")
    model_target = pkg_dir / 'models' / 'sentence_transformers' / 'all-MiniLM-L6-v2'
    model_target.parent.mkdir(parents=True, exist_ok=True)

    try:
        from sentence_transformers import SentenceTransformer
        print("  Loading all-MiniLM-L6-v2 (this may take a minute)...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        model.save(str(model_target))
        print(f"  [OK] Model saved to: {model_target}")
    except ImportError:
        print("  [ERROR] sentence-transformers not installed. Run: pip install sentence-transformers")
        return False
    except Exception as e:
        print(f"  [ERROR] Model download failed: {e}")
        return False

    print()
    print("=" * 60)
    print("  Offline data preparation complete!")
    print()
    print("  Files created:")
    print(f"    {nltk_target}/")
    print(f"    {model_target}/")
    print()
    print("  These will be included in the installer automatically.")
    print("=" * 60)
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
