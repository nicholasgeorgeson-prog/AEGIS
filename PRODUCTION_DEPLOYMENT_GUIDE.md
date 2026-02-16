# AEGIS Production Deployment Guide

## PDF Extraction Capabilities Overview

AEGIS includes multiple PDF extraction backends for maximum compatibility:

| Backend | Status | Use Case |
|---------|--------|----------|
| **Docling** | ✅ Ready | AI-powered extraction (tables, structure) |
| **PyMuPDF** | ✅ Ready | Fast, reliable text extraction |
| **Tesseract OCR** | ⚠️ Needs Install | Scanned PDF support |

---

## Quick Start

### 1. Verify Current State
```bash
python3 check_pdf_capabilities.py --verbose
```

### 2. Set Up Offline Environment
```bash
# Mac/Linux
source setup_offline_env.sh

# Windows
setup_offline_env.bat
```

### 3. Install Tesseract (if needed)
```bash
python3 setup_tesseract.py --check
```

---

## Tesseract OCR Installation

### macOS

**Option 1: Homebrew (Recommended)**
```bash
# Install Homebrew first if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Tesseract
brew install tesseract

# Verify
tesseract --version
```

**Option 2: MacPorts**
```bash
sudo port install tesseract
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-eng
```

### Linux (CentOS/RHEL/Fedora)
```bash
# CentOS/RHEL
sudo yum install tesseract

# Fedora
sudo dnf install tesseract tesseract-langpack-eng
```

### Windows
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run `tesseract-ocr-w64-setup-*.exe`
3. During installation, select "English" language data
4. Add to PATH: `C:\Program Files\Tesseract-OCR`

---

## Air-Gapped Deployment

For systems without internet access, you need to pre-download all components.

### What's Already Downloaded

| Component | Location | Size |
|-----------|----------|------|
| Docling Models | `~/.cache/huggingface/hub` | ~1.7 GB |
| Tesseract Language Data | `./tesseract_package/tessdata/` | ~15 MB |

### Packaging for Air-Gap

1. **Copy the entire project directory** including:
   - All Python source files
   - `tesseract_package/` directory
   - `setup_offline_env.sh` / `setup_offline_env.bat`

2. **Copy the Docling model cache**:
   ```bash
   # On source machine
   tar -czf docling_models.tar.gz ~/.cache/huggingface/hub/models--ds4sd--docling-models

   # On target machine
   mkdir -p ~/.cache/huggingface/hub
   tar -xzf docling_models.tar.gz -C ~/.cache/huggingface/hub/
   ```

3. **Install Tesseract on target** (offline installer):
   - Windows: Use the standalone `.exe` installer
   - Linux: Use `.deb` or `.rpm` packages with `dpkg -i` or `rpm -i`

4. **Copy language data**:
   ```bash
   # Copy to Tesseract's tessdata directory
   cp tesseract_package/tessdata/* /usr/share/tesseract-ocr/4.00/tessdata/
   # or (macOS)
   cp tesseract_package/tessdata/* /opt/homebrew/share/tessdata/
   ```

5. **Set environment variables**:
   ```bash
   source setup_offline_env.sh
   ```

6. **Verify deployment**:
   ```bash
   python3 check_pdf_capabilities.py
   ```

---

## Environment Variables Reference

| Variable | Purpose | Default |
|----------|---------|---------|
| `DOCLING_ARTIFACTS_PATH` | Path to Docling models | `~/.cache/huggingface/hub` |
| `HF_HUB_OFFLINE` | Force Hugging Face offline mode | `1` (set) |
| `TRANSFORMERS_OFFLINE` | Force Transformers offline | `1` (set) |
| `TESSDATA_PREFIX` | Path to Tesseract language data | System default |

---

## Troubleshooting

### "Tesseract not found"
- Ensure Tesseract is installed and in PATH
- Set `pytesseract.pytesseract.tesseract_cmd` in code

### "Docling models not downloaded"
- Check `~/.cache/huggingface/hub` for model files
- Run with `DOCLING_ALLOW_NETWORK=1` to download models

### "OCR quality is poor"
- Increase DPI in PDF-to-image conversion (default: 300)
- Ensure proper language data is installed

---

## File Inventory

```
TechWriterReview/
├── check_pdf_capabilities.py    # Diagnostic script
├── setup_tesseract.py           # Tesseract setup helper
├── setup_offline_env.sh         # Environment setup (Mac/Linux)
├── setup_offline_env.bat        # Environment setup (Windows)
├── pdf_extractor.py             # Basic PDF extraction
├── pdf_extractor_v2.py          # Enhanced PDF extraction
├── docling_extractor.py         # AI-powered extraction
├── ocr_extractor.py             # OCR for scanned PDFs
└── tesseract_package/
    ├── tessdata/
    │   ├── eng.traineddata      # English language data
    │   └── osd.traineddata      # Orientation detection
    └── TESSERACT_PACKAGING_README.txt
```

---

## Verification Checklist

- [ ] Run `check_pdf_capabilities.py` - shows "PRODUCTION READY"
- [ ] Docling extraction works (test with a PDF)
- [ ] OCR works (test with a scanned PDF)
- [ ] All environment variables set correctly
- [ ] No network calls during operation (verify with network monitor)

---

## Support

For issues with PDF extraction:
1. Run `python3 check_pdf_capabilities.py --verbose > diagnostic.txt`
2. Include the diagnostic output in your support request
