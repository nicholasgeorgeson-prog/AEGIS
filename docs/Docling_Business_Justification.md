# Business Justification: Docling AI Models for Document Processing

**Date:** February 1, 2026
**Requested By:** Nick Georgeson
**Tool:** AEGIS - Technical Documentation Quality Assurance Tool

---

## Executive Summary

This document requests approval to download and deploy IBM's Docling document processing models on our network. These models enable advanced PDF and document parsing capabilities for the AEGIS tool, which is used to ensure quality and compliance of technical documentation.

**Key Points:**
- One-time download (~358 MB), then operates 100% offline
- Open-source, Apache 2.0 licensed - free for commercial use
- Developed by IBM Research - enterprise-grade quality
- No data transmission during operation - all processing is local
- Not a generative AI/chatbot - purely document parsing

---

## What is Docling?

Docling is an open-source document processing library developed by **IBM Research**. It converts PDF, DOCX, PPTX, and other document formats into structured, machine-readable data while preserving:

- Document layout and reading order
- Table structures (rows, columns, merged cells)
- Headings and section hierarchy
- Lists and bullet points

**GitHub Repository:** https://github.com/docling-project/docling
**IBM Announcement:** https://www.ibm.com/new/announcements/granite-docling-end-to-end-document-conversion

---

## Models Requested for Download

### Required Model

| Model Name | Repository | Size | License |
|------------|------------|------|---------|
| Docling Models | `docling-project/docling-models` | 358 MB | CDLA-Permissive-2.0 + Apache-2.0 |

**Source URL:** https://huggingface.co/docling-project/docling-models

**Contents:**
- Layout Detection Model - Identifies document regions (text blocks, tables, figures, headers)
- TableFormer Model - AI-powered table structure recognition

### Optional Model (if OCR capability needed)

| Model Name | Repository | Size | License |
|------------|------------|------|---------|
| EasyOCR | `JaidedAI/EasyOCR` | ~500 MB | Apache-2.0 |

**Source URL:** https://huggingface.co/JaidedAI/EasyOCR

---

## Security Considerations

### What These Models Are

- **Static neural network weights** - binary files containing pre-trained parameters
- **Not executable code** - cannot run independently
- **Read-only at runtime** - models are loaded but never modified
- **Deterministic output** - same input always produces same output

### What These Models Are NOT

- ❌ Not a Large Language Model (LLM) or chatbot
- ❌ Not capable of generating text, code, or creative content
- ❌ Not connected to any external services
- ❌ Not capable of learning or storing new information
- ❌ Not capable of network communication

### Network Access Requirements

| Phase | Network Required | Data Transmitted |
|-------|------------------|------------------|
| Initial Download | Yes (one-time) | Download model files from HuggingFace |
| Runtime Operation | **No** | **None - 100% offline** |
| Updates | Optional | Only if manually triggered |

**Offline Enforcement:** Environment variables (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`) block all network access during operation.

### Data Privacy

- All document processing occurs locally on the workstation
- No document content is transmitted externally
- No telemetry or usage data is collected
- Compliant with air-gapped network requirements

---

## Business Benefits

### Current Limitations (Without Docling)

- Basic text extraction loses document structure
- Tables extracted as unstructured text
- Manual effort required to reconstruct layouts
- Inconsistent results across document formats

### Capabilities Enabled (With Docling)

- **95%+ table extraction accuracy** - preserves rows, columns, headers
- **Reading order preservation** - text extracted in logical sequence
- **Multi-format support** - PDF, DOCX, PPTX, XLSX, HTML
- **Batch processing** - analyze multiple documents efficiently
- **Quality metrics** - automated documentation compliance checking

### Return on Investment

- Reduces manual document review time by estimated 40-60%
- Improves consistency of technical documentation audits
- Enables automated compliance checking against standards
- Supports SAIC's quality assurance processes

---

## Technical Requirements

### Workstation Requirements

- Windows 10/11 (64-bit)
- Python 3.12
- 4 GB available disk space
- 8 GB RAM (recommended)
- No GPU required (CPU processing)

### Installation Process

1. Download model files (one-time, ~358 MB)
2. Extract to user directory (`%USERPROFILE%\.cache\docling\models`)
3. No administrator privileges required
4. No system-level changes

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Malicious code in models | Very Low | High | Models are static weights, not executable; sourced from IBM/HuggingFace with community verification |
| Data exfiltration | None | N/A | Offline operation enforced; no network capability at runtime |
| License compliance | None | N/A | Apache 2.0 permits commercial use without restrictions |
| Supply chain attack | Low | Medium | Verify checksums; models have 800K+ monthly downloads with community oversight |

---

## Approval Request

**Requested Action:** Approve one-time download of Docling models from HuggingFace to enable advanced document processing capabilities in AEGIS.

**Download URLs:**
1. https://huggingface.co/docling-project/docling-models (Required - 358 MB)
2. https://huggingface.co/JaidedAI/EasyOCR (Optional - 500 MB, for OCR)

**Alternative:** If direct download is not permitted, models can be downloaded on an approved system and transferred via secure media.

---

## Appendix A: Model File Listing

### docling-project/docling-models

```
model_artifacts/
├── layout/
│   ├── config.json
│   └── model.safetensors
├── tableformer/
│   ├── config.json
│   └── model.safetensors
├── .gitattributes
├── .gitignore
├── README.md
└── config.json

Total: ~358 MB
```

---

## Appendix B: License Information

### Apache License 2.0 (Summary)

- ✅ Commercial use permitted
- ✅ Modification permitted
- ✅ Distribution permitted
- ✅ Private use permitted
- ⚠️ License and copyright notice must be included
- ⚠️ Changes must be stated

**Full License:** https://www.apache.org/licenses/LICENSE-2.0

### CDLA-Permissive-2.0 (Summary)

- ✅ Commercial use permitted
- ✅ Designed specifically for data/model sharing
- ✅ No copyleft requirements

**Full License:** https://cdla.dev/permissive-2-0/

---

## Contact

For questions regarding this request, please contact:

**Nick Georgeson**
Systems Engineering
SAIC

---

*Document generated by AEGIS v3.1.0*
