# AEGIS Offline Dependencies Download Report

**Date:** 2026-02-15
**AEGIS Version:** 4.6.2
**Python Version:** 3.10+
**Platform:** Linux/macOS/Windows

---

## Executive Summary

✅ **SUCCESS** - All Python dependencies have been successfully downloaded as wheel files for offline installation.

- **Total packages in requirements.txt:** 47 direct dependencies
- **Total wheels downloaded:** 122 (including all transitive dependencies)
- **Total size:** 398 MB
- **Download status:** 100% successful

---

## Download Statistics

| Category | Count |
|----------|-------|
| Wheel files (.whl) | 121 |
| Source distributions (.tar.gz) | 1 |
| Total packages | 122 |
| Directory size | 398 MB |

### Package Categories

#### Core Framework & Web Server
- Flask 2.3.3
- Werkzeug 3.1.5
- Waitress 2.1.2
- Jinja2 3.1.6
- Click 8.3.1
- Itsdangerous 2.2.0
- Blinker 1.9.0

#### Document Processing
- python-docx 0.8.11 (Word documents)
- lxml 4.9.4 (XML/HTML processing)
- mammoth 1.11.0 (DOCX to HTML)
- openpyxl 3.1.5 (Excel)
- PyMuPDF 1.27.1 (PDF extraction)
- pdfplumber 0.11.9 (PDF extraction)
- PyPDF2 3.0.1 (PDF utilities)
- pypdf 3.17.4 (PDF tools)
- pdfminer.six 20221105 (PDF parsing)
- pdf2image 1.17.0 (PDF to images)

#### OCR & Image Processing
- pytesseract 0.3.13 (Tesseract OCR)
- Pillow 12.1.1 (Image processing)
- opencv-python-headless 4.13.0.92 (OpenCV)
- pypdfium2 5.4.0 (PDF handling)

#### Table Extraction
- camelot-py 1.0.9 (Table extraction)
- tabula-py 2.10.0 (Table extraction)

#### Natural Language Processing
- spacy 3.7.2 (Named Entity Recognition)
- NLTK 3.9.2 (Tokenization, stemming)
- TextBlob 0.19.0 (Sentiment analysis)
- textstat 0.7.12 (Readability metrics)
- sentence-transformers 5.2.2 (Semantic similarity)
- transformers 5.1.0 (Pre-trained models)
- PassivePy 0.2.23 (Passive voice detection)
- rapidfuzz 3.14.3 (Fuzzy string matching)

#### NLP & ML Infrastructure
- torch 2.10.0 (PyTorch deep learning)
- scikit-learn 1.7.2 (Machine learning)
- numpy 2.2.6 (Numerical computing)
- scipy 1.15.3 (Scientific computing)
- pandas 2.3.3 (Data analysis)
- huggingface-hub 1.4.1 (Model downloads)
- tokenizers 0.22.2 (Fast tokenization)
- safetensors 0.7.0 (Tensor I/O)

#### Analysis & Visualization
- reportlab 4.4.10 (PDF generation)
- bokeh 3.8.2 (Interactive visualizations)
- diff-match-patch 20241021 (Document comparison)
- pymupdf4llm 0.3.4 (Structured PDF output)
- py-readability-metrics 1.4.5 (Readability analysis)

#### Utilities
- requests 2.31.0 (HTTP client)
- python-dateutil 2.9.0 (Date handling)
- jsonschema 4.26.0 (JSON validation)
- psutil 7.2.2 (System monitoring)

#### Dependencies Infrastructure
- spacy-legacy 3.0.14
- spacy-loggers 1.0.5
- catalogue 2.0.10
- pydantic 2.8.0
- pydantic-core 2.27.0
- confection 0.1.5
- cymem 2.0.10
- murmurhash 1.0.10
- preshed 3.1.0
- srsly 2.5.2
- thinc 8.3.10
- wasabi 1.1.3
- weasel 0.4.3
- typer / typer-slim
- cloudpathlib 0.23.0
- smart-open 7.5.0
- filelock 3.24.0
- fsspec 2026.2.0
- regex 2026.1.15
- contourpy 1.3.2
- cryptography 46.0.5
- cffi 2.0.0
- pycparser 3.0
- narwhals 2.16.0
- networkx 3.4.2
- sympy 1.14.0
- mpmath 1.3.0
- attrs 25.4.0
- annotated-types 0.7.0
- referencing 0.37.0
- jsonschema-specifications 2025.9.1
- rpds-py 0.30.0
- et-xmlfile 2.0.0
- charset-normalizer 3.4.4
- certifi 2026.1.4
- idna 3.10
- urllib3 2.6.3
- chardet 5.2.0
- joblib 1.5.3
- threadpoolctl 3.6.0
- setuptools 82.0.0
- tqdm 4.67.3
- tornado 6.5.4
- markdown-it-py 4.0.0
- mdurl 0.1.2
- rich 14.3.2
- pygments 2.19.2
- typing-extensions 4.15.0
- typing-inspection 0.4.2
- shellingham 1.5.4
- httpx 0.28.1
- httpcore 1.0.9
- h11 0.16.0
- anyio 4.12.1
- exceptiongroup 1.3.1
- six 1.17.0
- wrapt 2.1.1
- language-tool-python 3.2.2
- pyyaml 6.0.3
- pytz 2025.2
- tzdata 2025.3
- tabulate 0.9.0
- blis 1.3.3
- xyzservices 2025.11.0
- annotated-doc 0.0.4
- distro 1.9.0
- toml 0.10.2
- termcolor 3.3.0
- pyphen 0.17.2
- hf-xet 1.2.0
- cobble 0.1.4

---

## Installation Instructions

### Option 1: Windows Users

1. **Navigate to project directory:**
   ```cmd
   cd C:\path\to\TechWriterReview
   ```

2. **Double-click `install_offline.bat`** or run from Command Prompt:
   ```cmd
   install_offline.bat
   ```

3. The script will:
   - Verify Python 3.10+ is installed
   - Install all packages from wheels directory
   - Verify installation of key dependencies
   - Display next steps

### Option 2: macOS / Linux Users

1. **Navigate to project directory:**
   ```bash
   cd /path/to/TechWriterReview
   ```

2. **Run the installation script:**
   ```bash
   bash install_offline.sh
   ```

   Or with optional virtual environment:
   ```bash
   bash install_offline.sh --venv
   ```

3. The script will:
   - Verify Python 3.10+ is installed
   - Optionally create and activate virtual environment
   - Install all packages from wheels directory
   - Verify installation of key dependencies
   - Display next steps

### Option 3: Manual Installation (All Platforms)

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install from wheels
python -m pip install --no-index --find-links=wheels -r requirements.txt
```

---

## System Requirements

### Minimum
- **Python:** 3.10.0 or higher (3.12+ recommended)
- **Disk space:** 500 MB (for wheels + installed packages)
- **Memory:** 4 GB RAM minimum

### Optional Dependencies (System-level)

These are only needed if using certain features:

1. **Tesseract OCR** (for scanned PDF documents):
   ```bash
   # macOS
   brew install tesseract

   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr

   # Windows
   # Download from: https://github.com/UB-Mannheim/tesseract/wiki
   ```

2. **Poppler** (for PDF to image conversion):
   ```bash
   # macOS
   brew install poppler

   # Ubuntu/Debian
   sudo apt-get install poppler-utils

   # Windows
   # Download from: https://github.com/osboxes/poppler-windows/releases
   ```

3. **Ghostscript** (for advanced PDF table extraction):
   ```bash
   # macOS
   brew install ghostscript

   # Ubuntu/Debian
   sudo apt-get install ghostscript

   # Windows
   # Download from: https://www.ghostscript.com/download/gsdnld.html
   ```

4. **Java 8+** (for LanguageTool grammar checking):
   ```bash
   # macOS
   brew install openjdk

   # Ubuntu/Debian
   sudo apt-get install default-jdk

   # Windows
   # Download from: https://www.oracle.com/java/technologies/downloads/
   ```

---

## Running AEGIS After Installation

### Start the server:

```bash
# Default (production mode)
python3 app.py

# Development mode with auto-reload (recommended during development)
python3 app.py --debug
```

### Access the application:

Open your browser and navigate to:
```
http://localhost:5050
```

---

## Verification Checklist

After installation, verify these core packages are installed:

```bash
# Check Flask
python3 -c "import flask; print(f'Flask {flask.__version__}')"

# Check python-docx
python3 -c "import docx; print('python-docx installed')"

# Check Pandas
python3 -c "import pandas; print(f'Pandas {pandas.__version__}')"

# Check spaCy (optional)
python3 -c "import spacy; print('spaCy installed')"

# Check PyTorch (optional)
python3 -c "import torch; print(f'PyTorch {torch.__version__}')"
```

---

## Troubleshooting

### Issue: "Python not found" or "Python 3.10+ required"

**Solution:** Install Python 3.10+ from python.org or your package manager

### Issue: "Permission denied" on Unix/Linux

**Solution:** Make script executable first:
```bash
chmod +x install_offline.sh
./install_offline.sh
```

### Issue: "wheels directory not found"

**Solution:** Ensure the `wheels/` directory exists in the project root:
```bash
ls -la wheels/
```

### Issue: Some packages fail to install

**Solution:**
1. Note which packages failed
2. Try installing individually:
   ```bash
   python -m pip install --no-index --find-links=wheels PACKAGE_NAME
   ```
3. If it still fails, the package may need to be downloaded on your Mac with internet connection

### Issue: ModuleNotFoundError after installation

**Solution:**
1. Verify package is installed:
   ```bash
   python -m pip list | grep package_name
   ```
2. If not present, reinstall:
   ```bash
   python -m pip install --no-index --find-links=wheels -r requirements.txt
   ```

---

## File Structure After Download

```
TechWriterReview/
├── wheels/                              (398 MB)
│   ├── Flask-2.3.3-py3-none-any.whl
│   ├── python-docx-0.8.11-py3-none-any.whl
│   ├── PyMuPDF-1.27.1-cp310-abi3-manylinux_2_28_aarch64.whl
│   ├── spacy-3.7.2-cp310-cp310-manylinux_2_17_aarch64.whl
│   ├── torch-2.10.0-cp310-cp310-manylinux_2_28_aarch64.whl
│   ├── ... (116 more packages)
│   └── et-xmlfile-2.0.0-py3-none-any.whl
├── requirements.txt                     (Current dependencies list)
├── install_offline.bat                  (Windows installation script)
├── install_offline.sh                   (Unix/Linux/macOS installation script)
├── WHEELS_INSTALLATION_REPORT.md        (This file)
└── ... (other project files)
```

---

## Notes

### About Platform-Specific Wheels

The downloaded wheels include binaries for:
- **Architecture:** aarch64 (ARM 64-bit) - suitable for M1/M2 Macs and Linux ARM servers
- **Python:** 3.10-3.12 compatible wheels
- **OS:** Linux wheels (works with minor adjustments on Windows/macOS for compatible packages)

If you need different architectures (e.g., Intel x86-64), download wheels on a machine with that architecture.

### Dependencies Size Breakdown

The 398 MB includes:
- **PyTorch (torch):** ~120 MB (largest package)
- **Transformers & models:** ~80 MB
- **scikit-learn & scipy:** ~60 MB
- **spaCy & dependencies:** ~40 MB
- **All other packages:** ~98 MB

### Why These Packages?

- **Document Processing:** Required for DOCX, PDF, Excel, OCR support
- **NLP:** Enables advanced role extraction, acronym detection, semantic analysis
- **ML/Deep Learning:** Powers sentence transformers for duplicate detection, semantic similarity
- **Data Analysis:** Pandas/NumPy for data aggregation and reporting
- **Visualization:** Bokeh for interactive charts and dashboards
- **Web Framework:** Flask + Werkzeug for web server

---

## Additional Resources

- [AEGIS README](./README.md)
- [Installation Guide](./Install_AEGIS.bat)
- [Production Deployment Guide](./PRODUCTION_DEPLOYMENT_GUIDE.md)
- [Project Documentation](./docs/)

---

**Generated:** 2026-02-15
**Report Version:** 1.0
