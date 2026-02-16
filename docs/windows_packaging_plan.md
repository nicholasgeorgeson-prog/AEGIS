# AEGIS Windows Standalone Packaging Plan

**Document Version**: 1.0
**Date**: February 2026
**Project**: AEGIS v4.7.0 (Aerospace Engineering Governance & Inspection System)
**Objective**: Package AEGIS as a standalone Windows EXE/installer without requiring Python installation

---

## Executive Summary

AEGIS is a Flask-based Python application with NLP capabilities (spaCy, scikit-learn, etc.) and a web frontend served on localhost:5050. This document provides a detailed plan to package AEGIS as a single-file Windows executable or installer that runs on any Windows 10/11 system without requiring Python, dependencies, or user configuration.

**Recommendation**: Use **PyInstaller** + **Inno Setup** for maximum compatibility and user experience.

- **PyInstaller**: Bundles Python interpreter + all dependencies into EXE/directory
- **Inno Setup**: Creates user-friendly installer with Start Menu shortcuts, desktop launcher, and uninstaller
- **Auto-launch browser**: Opens http://localhost:5050 automatically after app starts
- **System tray** (optional): Run as background service with tray icon

---

## 1. Packaging Options Analysis

### 1.1 PyInstaller

**Pros:**
- Industry standard for Python→EXE conversion
- Excellent support for Flask applications
- Can hide intermediate Python files from users
- Handles C-extension dependencies (numpy, spaCy) well
- Works with PyDLL hooks for complex packages
- Good documentation and active community

**Cons:**
- Large file size for NLP-heavy apps (500MB+ for one-file with spaCy models)
- Antivirus software sometimes flags bundled interpreters
- First startup slower (unpacking binaries on first run)
- Debugging requires running unwrapped EXE

**Best For**: AEGIS (recommended)

---

### 1.2 cx_Freeze

**Pros:**
- Cross-platform (works on Windows, Mac, Linux)
- Smaller bundle size than PyInstaller in some cases
- Good documentation

**Cons:**
- Less mature than PyInstaller
- More complex configuration for Flask apps
- Fewer examples in community for NLP apps
- Weaker support for complex C extensions (spaCy, numpy)

**Best For**: Not recommended for AEGIS

---

### 1.3 Nuitka

**Pros:**
- Compiles Python to C, potentially faster startup
- Minimal dependency overhead if done correctly

**Cons:**
- Early stage for package bundling (2024)
- Weak support for Flask and dynamic imports
- Complex setup for NLP packages
- Long compilation times

**Best For**: Not recommended for AEGIS

---

### 1.4 NSIS + Embedded Python

**Pros:**
- Lightweight installer (~40MB)
- User can see what's being installed
- Easy to maintain across versions

**Cons:**
- Requires manual Python embedding and dependency management
- User must accept Python runtime in installer
- Higher support burden (troubleshooting Python PATH issues)
- Slower to develop and iterate

**Best For**: If maximizing installer size is critical priority

---

### 1.5 WiX (Windows Installer XML)

**Pros:**
- Professional, industry-standard Windows installer
- Excellent versioning and upgrade support
- Can create MSI packages

**Cons:**
- Steep learning curve
- Verbose XML syntax
- Overkill for a single-file embedded app
- Slower development cycle

**Best For**: Large enterprise deployments (not needed for AEGIS)

---

## Recommendation Summary

| Option | Bundle Size | Ease | Maintenance | Support | Verdict |
|--------|------------|------|------------|---------|---------|
| **PyInstaller** | 500-800MB | Easy | Low | Excellent | ✅ CHOOSE THIS |
| cx_Freeze | 450-700MB | Moderate | Medium | Moderate | ⚠️ Consider |
| Nuitka | 400-600MB | Hard | High | Weak | ❌ Not ready |
| NSIS+Python | 40MB installer | Hard | High | Weak | ❌ Too manual |
| WiX | 600-900MB | Very Hard | High | Good | ❌ Overkill |

**FINAL RECOMMENDATION: PyInstaller + Inno Setup**

---

## 2. PyInstaller Implementation Details

### 2.1 Dependencies Summary (from requirements.txt)

**Core dependencies:**
- Flask 2.0+ (web framework)
- waitress 2.0+ (WSGI server)
- python-docx, lxml (Word documents)
- PyMuPDF, pdfplumber, PyPDF2, camelot-py, tabula-py (PDF extraction)
- pytesseract, pdf2image, Pillow (OCR support)
- spacy 3.7+ (NLP, includes large language models ~40MB each)
- scikit-learn 1.3+ (ML clustering and similarity)
- nltk, TextBlob, textstat (NLP utilities)
- sentence-transformers 2.2+ (semantic similarity, models ~80MB)
- rapidfuzz (fuzzy matching)
- language-tool-python (grammar checking, requires Java)
- reportlab (PDF generation)
- diff-match-patch (document comparison)
- bokeh (interactive visualizations)
- pandas, numpy (data handling)
- passivepy (passive voice detection)
- pymupdf4llm (structured PDF extraction)

**Total native dependencies**: ~50 packages + C extensions

**Data files needed:**
- `templates/` directory (HTML templates)
- `static/` directory (CSS, JavaScript, fonts, images)
- `config.json` (configuration)
- `version.json` (version info)
- `routes/` directory (Flask blueprints)
- All NLP model files (spacy models, sentence-transformer models)

### 2.2 PyInstaller Spec File Configuration

Create `build/aegis.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for AEGIS standalone Windows executable.
Usage: pyinstaller build/aegis.spec
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import os

block_cipher = None

# Collect data files from packages
datas = []

# Flask templates and static files
datas += [('templates', 'templates')]
datas += [('static', 'static')]

# Config files
datas += [('config.json', '.')]
datas += [('version.json', '.')]

# spaCy models (download via: python -m spacy download en_core_web_sm)
datas += [('models/en_core_web_sm', 'models/en_core_web_sm')]

# Sentence-transformers cached models
datas += [('.cache/huggingface', '.cache/huggingface')]

# NLTK data
datas += [('nltk_data', 'nltk_data')]

# Bokeh resources
datas += collect_data_files('bokeh')

# Collect hidden imports (modules imported dynamically)
hiddenimports = [
    # Flask extensions
    'flask',
    'werkzeug',

    # NLP and ML
    'spacy',
    'spacy.cli',
    'sklearn',
    'sklearn.feature_extraction',
    'sklearn.metrics',
    'sklearn.cluster',
    'nltk',
    'nltk.tokenize',
    'nltk.corpus',
    'textblob',
    'textstat',
    'sentence_transformers',
    'rapidfuzz',

    # PDF and document processing
    'fitz',  # PyMuPDF
    'pdfplumber',
    'PyPDF2',
    'camelot',
    'tabula',
    'pdf2image',
    'PIL',
    'docx',
    'lxml',
    'mammoth',
    'openpyxl',

    # Grammar checking (optional, requires Java)
    'language_tool_python',

    # Reporting and visualization
    'reportlab',
    'bokeh.server',
    'bokeh.plotting',

    # Document analysis
    'passivepy',
    'pymupdf4llm',
    'py_readability_metrics',

    # Diff matching
    'diff_match_patch',

    # Utilities
    'pandas',
    'numpy',
    'requests',
    'dateutil',
    'jsonschema',

    # AEGIS custom modules (ensure all are included)
    'config_logging',
    'core',
    'routes',
    'routes._shared',
    'routes.core_routes',
    'routes.review_routes',
    'routes.config_routes',
    'routes.roles_routes',
    'routes.scan_routes',
    'routes.jobs_routes',
    'routes.data_routes',
    'scan_history',
    'diagnostic_export',
    'api_extensions',
    'update_manager',
    'statement_forge',
    'statement_forge.routes',
    'document_compare',
    'portfolio',
    'hyperlink_validator',
    'hyperlink_validator.routes',
    'hyperlink_health',
    'job_manager',
    'fix_assistant_api',
    'decision_learner',
    'report_generator',
]

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[
        # Exclude testing frameworks
        'pytest',
        'unittest',
        'nose',
        # Exclude development tools
        'ipython',
        'jupyter',
        'black',
        'flake8',
        'mypy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AEGIS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Hide console window (set True for debugging)
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='build/aegis.ico',  # Optional: Windows EXE icon
)
```

### 2.3 NLP Model Handling

**Problem**: spaCy models and sentence-transformer models are large (40-80MB each) and typically cached dynamically.

**Solution A: Pre-download models (Recommended)**

```bash
# Before running PyInstaller, download models:
python -m spacy download en_core_web_sm
python -m spacy download en_core_web_md  # Optional, larger model

# Download sentence-transformers model
python -c "from sentence_transformers import SentenceTransformer; \
           SentenceTransformer('all-MiniLM-L6-v2')"

# Copy to build directory:
mkdir -p models/en_core_web_sm
cp -r ~/.cache/spacy/en_core_web_sm/* models/en_core_web_sm/
mkdir -p .cache/huggingface
cp -r ~/.cache/huggingface/hub .cache/huggingface/
```

This adds ~150MB to bundle but ensures all NLP features work offline.

**Solution B: Lazy loading (Alternative)**

Modify `core.py` to cache models on first run:

```python
def _ensure_spacy_model(model_name='en_core_web_sm'):
    """Download spaCy model if not already cached."""
    import spacy
    try:
        nlp = spacy.load(model_name)
        logger.info(f'spaCy model {model_name} loaded from cache')
        return nlp
    except OSError:
        logger.info(f'Downloading spaCy model {model_name}...')
        os.system(f'python -m spacy download {model_name}')
        nlp = spacy.load(model_name)
        return nlp
```

This reduces initial bundle but requires internet on first run.

**Recommendation**: Use Solution A (pre-download) for maximum user convenience.

### 2.4 One-File vs One-Directory

**One-File (`--onefile`):**
- Creates single `AEGIS.exe` (~700-900MB)
- Cleaner for end users
- Slower first startup (unpacks binaries to temp directory)
- File extraction adds 5-10 seconds to startup

**One-Directory (`--onedir`):**
- Creates folder with EXE + dependencies (~700-900MB total)
- Slightly faster startup (no unpacking)
- Less professional appearance
- Harder for users to move/organize

**Recommendation**: Use `--onedir` for production, as startup time is critical for user experience.

### 2.5 Hidden Imports for Dynamic Loading

AEGIS loads modules dynamically (checkers, blueprints). Ensure PyInstaller discovers them:

```python
# In app.py, add explicit imports for dynamic modules:
import statement_forge.routes  # Ensures blueprint is included
import document_compare  # Ensure available
import job_manager  # Ensure available
```

Or use `--collect-all` flag:
```bash
pyinstaller aegis.spec --collect-all statement_forge --collect-all document_compare
```

---

## 3. Installer Options: Inno Setup (Recommended)

### 3.1 Why Inno Setup?

| Feature | Inno | NSIS | WiX |
|---------|------|------|-----|
| Learning curve | Easy | Easy | Hard |
| Installer size | Small | Small | Large |
| Uninstall | Full | Full | Full |
| Start Menu | Yes | Yes | Yes |
| Desktop shortcut | Yes | Yes | Yes |
| Code-signing support | Yes | Yes | Yes |
| Modern UI | Excellent | Good | Professional |
| Active community | Very | Good | Good |

### 3.2 Inno Setup Script

Create `build/aegis_installer.iss`:

```ini
; ============================================================================
; AEGIS Installer Script for Inno Setup 6.2+
; ============================================================================
; This script creates an installer for AEGIS standalone application.
;
; Build command:
;   "C:\Program Files (x86)\Inno Setup 6\iscc.exe" build/aegis_installer.iss
; ============================================================================

#define MyAppName "AEGIS"
#define MyAppVersion "4.7.0"
#define MyAppPublisher "AEGIS Development Team"
#define MyAppURL "https://github.com/your-org/aegis"
#define MyAppExeName "AEGIS.exe"
#define SourceDir "dist"  ; PyInstaller output directory

[Setup]
; Basic installer settings
AppId={{3F7A8B2C-E1D4-4F9B-A1B2-8D4E5C6A7B8F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={localappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=dist/installers
OutputBaseFilename=AEGIS-{#MyAppVersion}-Setup
Compression=lz4
SolidCompression=yes
WizardStyle=modern
AlwaysShowDirOnReadyPage=yes
ChangesAssociations=yes
ChangesEnvironment=yes

; Windows-specific settings
MinVersion=10.0.10240
Uninstallable=yes
CreateUninstaller=yes
ShowLanguageDialog=no

; Install to user's AppData (no admin needed)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
; Optional tasks for user selection
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "Start AEGIS when Windows starts"; GroupDescription: "Startup options"

[Files]
; Copy PyInstaller output (one-directory structure)
Source: "{#SourceDir}\AEGIS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Copy additional resources
Source: "{#SourceDir}\..\..\config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\..\..\version.json"; DestDir: "{app}"; Flags: ignoreversion

; Copy uninstaller (will be auto-created)
Source: "{code:InstallPath}\unins*.exe"; DestDir: "{app}"; Flags: external

[Icons]
; Desktop shortcut
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\AEGIS.exe"; \
    Tasks: desktopicon; Comment: "Technical Writing Review Tool"; \
    IconFilename: "{app}\aegis.ico"; WorkingDir: "{app}"

; Start Menu group
Name: "{group}\{#MyAppName}"; Filename: "{app}\AEGIS.exe"; \
    Comment: "Launch AEGIS"; WorkingDir: "{app}"

Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

; Quick launch
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; \
    Filename: "{app}\AEGIS.exe"; Tasks: quicklaunchicon; Comment: "AEGIS"; \
    WorkingDir: "{app}"

; Startup folder for auto-start
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\AEGIS.exe"; \
    Parameters: "--no-browser"; Tasks: autostart; WorkingDir: "{app}"; \
    Comment: "Start AEGIS in background"

[Run]
; Uncheck by default - let user decide
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; \
    Flags: nowait postinstall skipifsilent; WorkingDir: "{app}"

[UninstallDelete]
; Clean up application-created files
Type: filesandordirs; Name: "{app}\database"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\temp"
Type: filesandordirs; Name: "{localappdata}\AEGIS"  ; Remove user config

[Code]
{ Helper function to determine install path }
function InstallPath(Param: String): String;
begin
  Result := ExpandConstant('{app}');
end;

{ Modify Path environment variable to allow running AEGIS from any directory }
procedure ModifyPath(Add: Boolean);
var
  Path: String;
  RegPath: String;
begin
  RegPath := 'HKCU\Environment';
  if RegQueryStringValue(RegPath, 'PATH', Path) then
    begin
      if Add then
        begin
          if Pos(ExpandConstant('{app}'), Path) = 0 then
            SetEnvironmentVariable('PATH', Path + ';' + ExpandConstant('{app}'));
        end
      else
        begin
          Path := StringReplace(Path, ';' + ExpandConstant('{app}'), '', True, False);
          Path := StringReplace(Path, ExpandConstant('{app}') + ';', '', True, False);
        end;
      RegWriteStringValue(RegPath, 'PATH', Path);
    end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  { Run this after installation completes }
  if CurStep = ssPostInstall then
    begin
      { Optionally modify PATH to allow "aegis" command from any terminal }
      { ModifyPath(True); }
    end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  { Clean up when uninstalling }
  if CurUninstallStep = usPostUninstall then
    begin
      { ModifyPath(False); }
    end;
end;
```

### 3.3 Installation Flow

1. User downloads `AEGIS-4.7.0-Setup.exe`
2. Windows SmartScreen verification (sign EXE with certificate for best UX)
3. Installer prompts for install location (default: `%LOCALAPPDATA%\AEGIS`)
4. No elevation required (installs to user profile)
5. Creates shortcuts:
   - Desktop icon
   - Start Menu entry
   - (Optional) Startup folder for auto-launch
6. User clicks "Finish" → AEGIS launches automatically
7. Browser opens to http://localhost:5050

---

## 4. Auto-Launch Browser on App Startup

### 4.1 Implementation in app.py

The current code already has `open_browser()` function. Verify it's used:

```python
def open_browser():
    """Open browser after short delay."""
    time.sleep(1.5)
    webbrowser.open(f'http://{config.host}:{config.port}')

def main():
    # ... setup ...
    if not no_browser and not use_debug:
        threading.Thread(target=open_browser, daemon=True).start()
```

**For standalone EXE**, ensure this runs:
- Add `--no-browser` flag support (already exists)
- Default behavior: launch browser unless `--no-browser` is passed
- Delay 1.5s to ensure Flask is ready before opening

### 4.2 Windows-Specific Tweaks

For Windows exe bundled by PyInstaller:

```python
import webbrowser
import subprocess
import sys

def open_browser_windows():
    """Windows-specific browser launch with fallback."""
    time.sleep(2.0)  # Longer delay for bundled app

    url = f'http://{config.host}:{config.port}'

    try:
        # Try system default browser
        webbrowser.open(url)
    except Exception:
        # Fallback: try Edge or Chrome directly
        try:
            subprocess.Popen(
                [r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe', url]
            )
        except Exception:
            logger.warning(f'Could not open browser. Navigate to {url} manually.')
```

---

## 5. Optional: System Tray Icon and Background Service

### 5.1 System Tray Implementation

For advanced users, AEGIS can run as a background Windows Service with tray icon.

**Libraries**:
- `pystray` - System tray icon
- `pywin32` - Windows service integration (optional)

### 5.2 Tray Icon Script

Create `tray_launcher.py`:

```python
"""
AEGIS System Tray Launcher
Runs AEGIS in background with system tray control.
"""

import sys
import subprocess
import threading
import time
from pathlib import Path
from PIL import Image, ImageDraw
import pystray

# Global reference to Flask process
flask_process = None

def create_image(color):
    """Create a simple icon image."""
    width = 64
    height = 64
    image = Image.new('RGB', (width, height), color)
    dc = ImageDraw.Draw(image)

    # Draw "A" for AEGIS
    dc.text((15, 15), "A", fill=(255, 255, 255))
    return image

def start_flask():
    """Start Flask app in background."""
    global flask_process
    if flask_process is None or flask_process.poll() is not None:
        app_dir = Path(__file__).parent
        flask_process = subprocess.Popen(
            [sys.executable, str(app_dir / 'app.py'), '--no-browser'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(app_dir)
        )

def stop_flask():
    """Stop Flask app."""
    global flask_process
    if flask_process:
        flask_process.terminate()
        flask_process.wait(timeout=5)
        flask_process = None

def open_browser(icon, item):
    """Open web browser."""
    import webbrowser
    webbrowser.open('http://localhost:5050')

def exit_app(icon, item):
    """Exit tray app and stop Flask."""
    stop_flask()
    icon.stop()

def setup(icon):
    """Setup tray icon on startup."""
    start_flask()
    # Wait for Flask to start before opening browser
    time.sleep(2)
    threading.Thread(target=open_browser, args=(icon, None), daemon=True).start()

if __name__ == '__main__':
    icon = pystray.Icon(
        'AEGIS',
        create_image((52, 152, 219)),  # Blue icon
        menu=pystray.Menu(
            pystray.MenuItem('Open', open_browser),
            pystray.MenuItem('Exit', exit_app),
        ),
        title='AEGIS - Technical Writing Review'
    )
    icon.setup(setup)
    icon.run()
```

### 5.3 Tray Launcher Inclusion

To include tray launcher in installer:

1. PyInstaller spec: Add `tray_launcher.py` as separate entry point:
   ```python
   exe_tray = EXE(
       pyz_tray,
       a_tray.scripts,
       [],
       name='AEGIS-Tray',
       icon='build/aegis.ico',
   )
   ```

2. Inno Setup: Create two Start Menu entries:
   ```ini
   Name: "{group}\AEGIS (Normal)"; Filename: "{app}\AEGIS.exe"
   Name: "{group}\AEGIS (Background)"; Filename: "{app}\AEGIS-Tray.exe"
   ```

**Recommendation**: Include tray launcher as an optional advanced feature, not default.

---

## 6. Detailed Implementation Roadmap

### Phase 1: Prepare (Week 1)

**Tasks:**
1. Download spaCy and sentence-transformer models locally
2. Create `build/` directory structure
3. Write PyInstaller spec file
4. Test hidden imports and data file inclusion
5. Create icon files (aegis.ico, aegis.png)

**Deliverables:**
- `build/aegis.spec` (PyInstaller spec)
- `build/aegis.ico` (Windows icon)
- Models cached in project directory
- Test script to validate imports

**Testing:**
```bash
# Test PyInstaller build without Inno Setup
pyinstaller build/aegis.spec
./dist/AEGIS/AEGIS.exe  # Should launch app and open browser
```

---

### Phase 2: Build System (Week 2)

**Tasks:**
1. Create `build.py` script to orchestrate full build
2. Implement version synchronization
3. Clean build artifacts
4. Create code-signing infrastructure (optional)

**Deliverables:**
- `build.py` (main build script)
- `build_config.json` (build settings)
- Updated `version.json` process

**Build script pseudocode:**

```python
#!/usr/bin/env python
"""
AEGIS Build System
Packages AEGIS as standalone Windows EXE/installer.
"""

import subprocess
import sys
import json
from pathlib import Path

class AEGISBuilder:
    def __init__(self):
        self.root = Path(__file__).parent
        self.dist = self.root / 'dist'
        self.build = self.root / 'build'
        self.version = self._read_version()

    def _read_version(self):
        with open(self.root / 'version.json') as f:
            return json.load(f)['version']

    def clean(self):
        """Remove old build artifacts."""
        print('[*] Cleaning old builds...')
        subprocess.run(['rm', '-rf', str(self.dist)], check=False)

    def prepare_models(self):
        """Download NLP models if not present."""
        print('[*] Checking NLP models...')
        # Download spacy models
        # Download sentence-transformer models

    def build_pyinstaller(self):
        """Run PyInstaller."""
        print(f'[*] Building EXE with PyInstaller (v{self.version})...')
        cmd = [
            'pyinstaller',
            str(self.build / 'aegis.spec'),
            '--distpath', str(self.dist),
            '--buildpath', str(self.build / 'pyinstaller'),
        ]
        subprocess.run(cmd, check=True)

    def build_installer(self):
        """Run Inno Setup."""
        print(f'[*] Building installer (v{self.version})...')
        # Inno Setup command
        iscc_path = r'C:\Program Files (x86)\Inno Setup 6\iscc.exe'
        cmd = [iscc_path, str(self.build / 'aegis_installer.iss')]
        subprocess.run(cmd, check=True)

    def sign(self):
        """Code-sign EXE and installer (optional)."""
        print('[*] Code-signing binaries...')
        # signtool commands

    def build(self):
        """Full build pipeline."""
        self.clean()
        self.prepare_models()
        self.build_pyinstaller()
        self.build_installer()
        # self.sign()  # Uncomment to enable signing
        print(f'\n[✓] Build complete!')
        print(f'  EXE: {self.dist}/AEGIS-{self.version}-Setup.exe')

if __name__ == '__main__':
    builder = AEGISBuilder()
    builder.build()
```

---

### Phase 3: Inno Setup Configuration (Week 2)

**Tasks:**
1. Write Inno Setup script
2. Create installer graphics (banner, welcome screen)
3. Test installer on clean Windows VM
4. Document uninstall behavior

**Deliverables:**
- `build/aegis_installer.iss` (Inno Setup script)
- Installer graphics assets
- Installation guide for users
- Test results on Windows 10/11

**Testing:**
```bash
iscc build/aegis_installer.iss
# Test installer on clean Windows 10/11 VM
```

---

### Phase 4: Testing & Hardening (Week 3)

**Tasks:**
1. Test on bare Windows 10/11 (no Python, no dependencies)
2. Verify all features work (document upload, review, export)
3. Test antivirus/SmartScreen detection
4. Performance benchmarking
5. Error handling and logging

**Test Matrix:**
| OS | Python | Deps | Result |
|----|--------|------|--------|
| Win 10 | None | None | ✓ Must work |
| Win 11 | None | None | ✓ Must work |
| Win Server 2019 | None | None | ✓ Should work |
| Win Server 2022 | None | None | ✓ Should work |

**Testing Checklist:**
- [ ] App launches without errors
- [ ] Browser opens automatically
- [ ] All menu items functional
- [ ] Document upload/analysis works
- [ ] Reports generate correctly
- [ ] Database operations work
- [ ] No Python console visible
- [ ] App closes cleanly
- [ ] Uninstaller works
- [ ] No artifacts left after uninstall

---

### Phase 5: CI/CD Integration (Week 3)

**Tasks:**
1. Add build pipeline to GitHub Actions (or similar)
2. Automatic version increment
3. Release automation

**GitHub Actions Workflow** (`.github/workflows/build-windows.yml`):

```yaml
name: Build Windows Executable

on:
  push:
    tags:
      - 'v*'  # Trigger on version tags

jobs:
  build:
    runs-on: windows-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install build dependencies
      run: |
        pip install -r requirements.txt
        pip install pyinstaller innosetup

    - name: Download NLP models
      run: |
        python -m spacy download en_core_web_sm

    - name: Build with PyInstaller
      run: |
        python build/build.py

    - name: Create Installer with Inno Setup
      run: |
        & 'C:\Program Files (x86)\Inno Setup 6\iscc.exe' build/aegis_installer.iss

    - name: Upload Release
      uses: softprops/action-gh-release@v1
      with:
        files: dist/installers/AEGIS-*-Setup.exe
```

---

## 7. Handling External Dependencies

### 7.1 Tesseract OCR (Optional)

Tesseract requires external binary. For standalone:

**Option A: Don't include (Recommended)**
- Keep Tesseract optional
- Show friendly error if user tries OCR without Tesseract
- Link to installation guide: https://github.com/UB-Mannheim/tesseract/wiki

**Option B: Include Tesseract binary**
- Add ~100MB Tesseract binary to bundle
- Extract to temp directory on first run
- Update `pytesseract` config to point to bundled version

```python
import pytesseract
import tempfile
import shutil

def setup_tesseract():
    """Setup bundled Tesseract."""
    temp_dir = Path(tempfile.gettempdir()) / 'aegis_tesseract'
    tesseract_exe = temp_dir / 'tesseract.exe'

    if not tesseract_exe.exists():
        # Extract from bundle
        bundled = Path(sys._MEIPASS) / 'tesseract.exe'
        temp_dir.mkdir(exist_ok=True)
        shutil.copy(bundled, tesseract_exe)

    pytesseract.pytesseract.pytesseract_cmd = str(tesseract_exe)
```

**Recommendation**: Use Option A (user installs Tesseract separately if needed). Most AEGIS users won't use OCR.

### 7.2 Language Tool (Grammar Checking)

Requires Java runtime. Two options:

**Option A: Require user to install Java**
- Simpler distribution
- Many Windows users already have Java
- Graceful error if missing

**Option B: Bundle JRE**
- Adds ~200MB
- No user configuration needed
- Heavier installer

**Recommendation**: Option A - document that Language Tool requires Java 8+.

### 7.3 Poppler (PDF utility)

Required by `pdf2image` for OCR. Same approach as Tesseract:

**Option A: User installs separately**
- Keep bundle small
- Clear error message if missing

**Option B: Bundle Poppler**
- Adds ~50MB
- Seamless experience

**Recommendation**: Option A - most PDFs work fine without pdf2image.

---

## 8. Code-Signing and Distribution

### 8.1 Windows Code-Signing

**Why sign?**
- Removes SmartScreen "unknown publisher" warnings
- Proves authenticity to users
- Better adoption rate

**How to sign:**

1. Obtain certificate:
   - Self-signed (free, for testing)
   - EV Code-Signing (paid, $200-400/year, removes most warnings)

2. Sign EXE and installer:
   ```bash
   # Install Windows SDK (includes signtool.exe)
   signtool sign /f cert.pfx /p password /t http://timestamp.digicert.com \
     dist/AEGIS/AEGIS.exe
   signtool sign /f cert.pfx /p password /t http://timestamp.digicert.com \
     dist/installers/AEGIS-*.exe
   ```

3. Verify signature:
   ```bash
   signtool verify /pa dist/AEGIS/AEGIS.exe
   ```

**Recommendation**: Get proper EV certificate for production releases. For internal testing, self-signed is fine.

### 8.2 Distribution Channels

**Option 1: GitHub Releases** (Recommended)
```bash
gh release create v4.7.0 \
  dist/installers/AEGIS-4.7.0-Setup.exe \
  --title "AEGIS v4.7.0 - Windows Standalone"
```

**Option 2: Custom Website**
- Host on company server
- Track downloads
- Add changelog

**Option 3: Windows Package Manager**
- Submit to `winget` for easy install
- Users can: `winget install aegis`
- Requires proper versioning

---

## 9. Post-Installation Configuration

### 9.1 First-Run Setup

When user launches AEGIS for first time:

1. **Database initialization** (auto, happens in app.py)
2. **Config wizard** (optional - provide web UI for settings)
3. **NLP model download** (only if lazy-loading - not needed with pre-download)

### 9.2 User Configuration

Create `%LOCALAPPDATA%\AEGIS\config.json` with defaults:

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 5050
  },
  "security": {
    "csrf_enabled": true,
    "rate_limit_enabled": true,
    "auth_enabled": false
  },
  "features": {
    "statement_forge": true,
    "document_compare": true,
    "hyperlink_validator": true,
    "job_manager": true,
    "fix_assistant": true
  },
  "performance": {
    "max_upload_mb": 500,
    "timeout_seconds": 300
  }
}
```

Users can edit this file to customize behavior.

### 9.3 Database Location

Store databases in:
```
%LOCALAPPDATA%\AEGIS\data\
  ├── scan_history.db
  └── review_history.db (if exists)
```

This ensures:
- User data persists across app updates
- Different Windows users have separate databases
- Easy backup: just copy folder

---

## 10. Troubleshooting & Support

### 10.1 Common Issues

**Issue: "AEGIS.exe is not a valid Win32 application"**
- Cause: PyInstaller extraction failed
- Solution: Reinstall, clear temp directory, try again

**Issue: "The application failed to start because no Qt platform plugin could be found"**
- Cause: Bokeh visualization conflict
- Solution: Ensure bokeh data files included in spec

**Issue: Port 5050 already in use**
- Cause: Previous instance running or other app using port
- Solution: Add port fallback in config, document in installer

**Issue: Slow startup (30+ seconds)**
- Cause: First-run unpacking with many dependencies
- Solution: Document expected delay, add progress indicator

### 10.2 Support Resources

Create `docs/WINDOWS_INSTALLATION.md`:
- System requirements (Windows 10/11, 1GB RAM, 2GB disk)
- Installation step-by-step
- Troubleshooting section
- How to uninstall cleanly
- How to re-install

---

## 11. Build Performance & Size Optimization

### 11.1 Expected Sizes

| Component | Size |
|-----------|------|
| Python 3.11 + stdlib | ~150MB |
| Flask + dependencies | ~80MB |
| spaCy + en_core_web_sm model | ~50MB |
| sentence-transformers + models | ~100MB |
| scikit-learn + dependencies | ~80MB |
| Other NLP + utilities | ~120MB |
| **Total EXE/OneDir** | **~580MB** |
| **Installer (compressed)** | **~200MB** |

### 11.2 Size Reduction Strategies

**If size is too large:**

1. **Exclude unused models**:
   - Use smaller spaCy model: `en_core_web_sm` (50MB) vs `en_core_web_md` (100MB)
   - Skip sentence-transformers if not using semantic similarity

2. **Upx compression**:
   ```python
   # In spec: upx=True
   # Reduces binary size by ~40% at cost of first-run extraction time
   ```

3. **Lazy-load heavy packages**:
   ```python
   # Don't import spacy at module level
   def _load_nlp():
       import spacy
       return spacy.load('en_core_web_sm')
   ```

4. **Exclude test/docs directories**:
   ```python
   # In spec: excludedimports=['pytest', 'doctest']
   ```

**Current estimate: 580MB one-dir is acceptable for enterprise application.**

---

## 12. Future Enhancements

### 12.1 Auto-Update System

Implement update checking:

```python
# In app.py
def check_for_updates():
    """Check GitHub releases for newer version."""
    import requests
    try:
        response = requests.get(
            'https://api.github.com/repos/org/aegis/releases/latest',
            timeout=5
        )
        latest = response.json()['tag_name']
        current = VERSION
        if latest > current:
            # Notify user
            logger.info(f'Update available: {latest}')
            # Could trigger updater
    except Exception:
        pass  # Silently fail if no internet
```

### 12.2 Auto-Update Installer

Create `updater.exe` that:
- Downloads new installer
- Stops current app
- Runs installer with `/SILENT` flag
- Restarts app

### 12.3 Multi-User Support

- Store shared data in `%ProgramData%\AEGIS\` (all users)
- Store personal data in `%LOCALAPPDATA%\AEGIS\` (per user)
- Support Windows-level security groups for access control

---

## 13. Checklist for Production Release

### Pre-Release

- [ ] All tests passing on Windows 10/11
- [ ] No Python interpreter visible to end user
- [ ] Browser auto-opens on startup
- [ ] Database initializes correctly
- [ ] All core features tested
- [ ] Documentation updated
- [ ] Code signed with valid certificate
- [ ] Version number incremented in `version.json`
- [ ] Changelog prepared
- [ ] Release notes written

### Release Day

- [ ] Create GitHub release with changelog
- [ ] Upload signed `AEGIS-*.exe` installer
- [ ] Test download and run on clean Windows VM
- [ ] Announce update to users
- [ ] Monitor for issues/bug reports

### Post-Release

- [ ] Monitor crash reports
- [ ] Track uninstall rate
- [ ] Gather user feedback
- [ ] Plan next version

---

## 14. Summary: PyInstaller + Inno Setup Strategy

### Why This Stack?

| Requirement | Solution |
|-------------|----------|
| **No Python required** | PyInstaller bundles interpreter |
| **No dependencies to install** | PyInstaller includes all packages |
| **Professional installer** | Inno Setup handles UI/uninstall |
| **User-friendly experience** | Auto-launch browser, shortcuts |
| **Easy updates** | Installer replaces old version |
| **Small learning curve** | Both tools well-documented |
| **Active community** | Stack widely used for Python apps |

### Timeline

- **Week 1**: Prepare PyInstaller configuration, test local build
- **Week 2**: Create Inno Setup installer, test on Windows VM
- **Week 3**: Full testing, integrate into CI/CD, document
- **Total**: 2-3 weeks for production-ready build system

### Effort Estimate

- **Initial setup**: 40 hours
- **Per release**: 4 hours (build, test, upload)
- **Maintenance**: Low (PyInstaller specs are stable)

### Expected User Experience

1. User downloads `AEGIS-4.7.0-Setup.exe`
2. Double-clicks installer
3. Accepts default location (`%LOCALAPPDATA%\AEGIS`)
4. Clicks "Install"
5. App automatically launches
6. Browser opens to http://localhost:5050
7. **Total time: ~30 seconds**

---

## Appendix A: Required Tools

### Development Machine

- Windows 10/11 (for testing)
- Python 3.11+ (development)
- PyInstaller: `pip install pyinstaller`
- Inno Setup 6.2+: https://jrsoftware.org/isdl.php

### Optional

- WiX (if choosing WiX path): https://wixtoolset.org
- Signtool (included in Windows SDK)
- GitHub CLI: For releasing

---

## Appendix B: File Structure After Build

```
project_root/
├── build/
│   ├── build.py              (main build orchestrator)
│   ├── aegis.spec            (PyInstaller spec)
│   ├── aegis_installer.iss   (Inno Setup script)
│   ├── aegis.ico             (icon file)
│   └── build_config.json
│
├── dist/
│   ├── AEGIS/                (PyInstaller output one-dir)
│   │   ├── AEGIS.exe
│   │   ├── api_extensions.py
│   │   ├── config_logging.py
│   │   ├── core.py
│   │   ├── routes/
│   │   ├── static/
│   │   ├── templates/
│   │   └── ... (all bundled files)
│   │
│   └── installers/
│       └── AEGIS-4.7.0-Setup.exe  (final deliverable)
│
└── ... (rest of source)
```

---

## Appendix C: PyInstaller Hooks for Complex Packages

For packages that don't auto-detect hidden imports, create hooks:

**File: `build/hook-spacy.py`**:
```python
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = collect_data_files('spacy')
hiddenimports = collect_submodules('spacy')
```

**Usage in spec:**:
```python
hookspath=[Path(__file__).parent]
```

---

## Appendix D: Testing Checklist Template

Create `build/TEST_CHECKLIST.md`:

```markdown
# AEGIS v4.7.0 Testing Checklist

**Date**: ____
**Tester**: ____
**OS**: Windows __ (10/11) __
**Python Installed**: Yes/No

## Installation

- [ ] Installer downloads without issues
- [ ] No antivirus warnings on download
- [ ] Installer runs without admin prompt
- [ ] Can choose install location
- [ ] Desktop shortcut created
- [ ] Start Menu entry created
- [ ] Installation completes in <2 min

## First Launch

- [ ] AEGIS.exe exists in install folder
- [ ] App launches without errors
- [ ] Browser opens automatically
- [ ] No Python console visible
- [ ] UI fully responsive

## Core Features

- [ ] Can select and upload document
- [ ] Document analysis starts
- [ ] Results display without errors
- [ ] Can generate reports
- [ ] Can export results

## Cleanup

- [ ] Uninstall through Control Panel works
- [ ] All files removed from install folder
- [ ] No artifacts left in AppData
- [ ] Start Menu entry removed
- [ ] Desktop shortcut removed

## Notes

(Any issues or observations)

---
```

---

## Conclusion

This plan provides a comprehensive roadmap for packaging AEGIS as a standalone Windows application using **PyInstaller** and **Inno Setup**. The approach:

- **Eliminates Python requirement** for end users
- **Simplifies installation** to one click
- **Maintains all AEGIS features** without modification
- **Follows industry best practices** for Python app distribution
- **Requires moderate effort** (2-3 weeks) with clear milestones

Implementation can begin immediately with Phase 1 (prepare PyInstaller configuration). The build system is designed to be maintainable for future versions.

---

**Document Status**: Ready for implementation
**Next Steps**:
1. Create `build/aegis.spec` and test locally
2. Download NLP models and test bundling
3. Write Inno Setup script and test installer on Windows VM
4. Integrate into CI/CD pipeline
