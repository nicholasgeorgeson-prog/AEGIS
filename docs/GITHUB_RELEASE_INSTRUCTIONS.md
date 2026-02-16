# How to Create a GitHub Release with NLP Offline Package

This guide walks you through uploading the NLP offline package to GitHub so Windows users can download it.

## What You Have

After running the setup, you should have:
```
AEGIS/
├── nlp_offline_windows.zip     ← 124MB file to upload
├── install_nlp_offline.py      ← Script for Windows users
├── install_nlp.py              ← Script for online install
└── nlp_offline/                ← Source folder (don't commit this)
```

## Step-by-Step Instructions

### 1. Push Your Code to GitHub (without the large files)

First, make sure the large files are NOT committed to git:

```bash
# Add to .gitignore
echo "nlp_offline_windows.zip" >> .gitignore
echo "nlp_offline/" >> .gitignore

# Commit your code changes
git add .
git commit -m "Add NLP offline installer scripts"
git push
```

### 2. Go to Your GitHub Repository

1. Open your web browser
2. Go to: `https://github.com/YOUR_USERNAME/AEGIS`

### 3. Create a New Release

1. On your repo page, look at the right sidebar
2. Click **"Releases"** (or "Create a new release" if no releases exist)
3. Click the green **"Draft a new release"** button

### 4. Fill Out the Release Form

**Tag version:** `v3.1.0` (or your current version)

**Release title:** `v3.1.0 - NLP Enhancement Release`

**Description:** (copy this)
```markdown
## What's New in v3.1.0

### NLP Enhancement Features
- spaCy integration for linguistic analysis
- Enhanced spelling with domain dictionaries
- Readability metrics (8 industry formulas)
- Professional style checking (Proselint)
- Verb tense consistency checking
- Semantic analysis with WordNet

### Offline Installation (Windows)
For air-gapped Windows environments:
1. Download `nlp_offline_windows.zip` below
2. Extract to your AEGIS folder
3. Run: `python install_nlp_offline.py`

**Requirements:** Windows 10/11 (64-bit), Python 3.10

### Online Installation
For environments with internet access:
```
python install_nlp.py
```
```

### 5. Attach the ZIP File

1. Scroll down to **"Attach binaries by dropping them here"**
2. **Drag and drop** `nlp_offline_windows.zip` onto that area
   - OR click "Attach binaries" and browse to select the file
3. Wait for upload to complete (may take a minute for 124MB)

### 6. Publish the Release

1. Make sure "Set as the latest release" is checked
2. Click the green **"Publish release"** button

## What Users Will See

After publishing, users visiting your GitHub repo will see:

```
Releases
─────────
v3.1.0 - NLP Enhancement Release
   Latest

   Assets (1)
   └── nlp_offline_windows.zip (124 MB)
```

## Instructions for Windows Users

Tell your Windows users to:

1. **Download** from GitHub:
   - Go to Releases → v3.1.0
   - Download `nlp_offline_windows.zip`

2. **Extract** to AEGIS folder:
   - Right-click → Extract All
   - Should create `nlp_offline/` folder

3. **Install** (one time):
   ```cmd
   cd AEGIS
   python install_nlp_offline.py
   ```

4. **Done!** NLP features now work offline.

## Troubleshooting

### "File too large" error
GitHub Releases allow up to 2GB per file. If you see this error:
- Make sure you're in Releases, not trying to commit to the repo
- The repo itself has a 100MB limit per file

### Upload keeps failing
- Try a different browser
- Check your internet connection
- Try uploading during off-peak hours

### Users report Python version error
- They need Python 3.10 specifically (not 3.11 or 3.9)
- Download from: https://www.python.org/downloads/release/python-3100/
