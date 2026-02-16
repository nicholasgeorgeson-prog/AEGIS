#!/usr/bin/env python3
"""
OCR Extractor for AEGIS
==================================
Version: reads from version.json (module v1.0)
Date: 2026-01-27

Handles scanned PDFs and images using Tesseract OCR.
Pytesseract is already installed - this module integrates it.

Requirements:
- pytesseract (Python package) - ALREADY INSTALLED
- Tesseract OCR engine - NEEDS TO BE INSTALLED SEPARATELY
  Windows: https://github.com/UB-Mannheim/tesseract/wiki
  Mac: brew install tesseract
  Linux: apt install tesseract-ocr

Author: Nick / SAIC Systems Engineering
"""

import os
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
import logging

__version__ = "1.0.0"

logger = logging.getLogger(__name__)

# Check for required libraries
PYTESSERACT_AVAILABLE = False
PDF2IMAGE_AVAILABLE = False
PIL_AVAILABLE = False

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    pass

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    pass

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    pass


@dataclass
class OCRResult:
    """Result from OCR extraction."""
    text: str
    confidence: float  # Average confidence (0-100)
    pages: int
    method: str  # 'tesseract', 'easyocr', etc.
    warnings: List[str] = field(default_factory=list)
    page_texts: List[str] = field(default_factory=list)
    word_confidences: List[float] = field(default_factory=list)


class OCRExtractor:
    """
    Extract text from scanned PDFs and images using OCR.
    
    Features:
    - Automatic detection of scanned vs native text PDFs
    - Multi-page PDF support
    - Confidence scoring
    - Preprocessing for better accuracy
    """
    
    def __init__(self, tesseract_path: str = None, lang: str = 'eng'):
        """
        Initialize OCR extractor.
        
        Args:
            tesseract_path: Path to Tesseract executable (auto-detected if None)
            lang: OCR language (default: English)
        """
        self.lang = lang
        self._tesseract_available = False
        
        if PYTESSERACT_AVAILABLE:
            # Try to configure Tesseract path
            if tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
            else:
                # Common paths
                possible_paths = [
                    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                    '/usr/bin/tesseract',
                    '/usr/local/bin/tesseract',
                    '/opt/homebrew/bin/tesseract',
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        break
            
            # Verify Tesseract is working
            try:
                pytesseract.get_tesseract_version()
                self._tesseract_available = True
                logger.info("Tesseract OCR initialized successfully")
            except Exception as e:
                logger.warning(f"Tesseract not available: {e}")
    
    @property
    def is_available(self) -> bool:
        """Check if OCR is available."""
        return self._tesseract_available and PIL_AVAILABLE
    
    def extract_from_pdf(self, filepath: str, dpi: int = 300) -> OCRResult:
        """
        Extract text from a PDF using OCR.
        
        Args:
            filepath: Path to PDF file
            dpi: Resolution for PDF to image conversion (higher = better quality, slower)
            
        Returns:
            OCRResult with extracted text and metadata
        """
        result = OCRResult(
            text="",
            confidence=0.0,
            pages=0,
            method="tesseract"
        )
        
        if not self.is_available:
            result.warnings.append("OCR not available - Tesseract not installed")
            return result
        
        if not PDF2IMAGE_AVAILABLE:
            result.warnings.append("pdf2image not installed - cannot convert PDF to images")
            return result
        
        try:
            # Convert PDF pages to images
            images = convert_from_path(filepath, dpi=dpi)
            result.pages = len(images)
            
            all_text = []
            all_confidences = []
            
            for i, image in enumerate(images):
                # Preprocess image for better OCR
                processed_image = self._preprocess_image(image)
                
                # Extract text with confidence data
                page_data = pytesseract.image_to_data(
                    processed_image, 
                    lang=self.lang,
                    output_type=pytesseract.Output.DICT
                )
                
                # Build page text
                page_text = []
                page_confidences = []
                
                for j, word in enumerate(page_data['text']):
                    if word.strip():
                        page_text.append(word)
                        conf = page_data['conf'][j]
                        if conf > 0:  # -1 means no confidence
                            page_confidences.append(conf)
                
                page_text_str = ' '.join(page_text)
                result.page_texts.append(page_text_str)
                all_text.append(page_text_str)
                all_confidences.extend(page_confidences)
            
            result.text = '\n\n'.join(all_text)
            result.word_confidences = all_confidences
            
            if all_confidences:
                result.confidence = sum(all_confidences) / len(all_confidences)
            
            logger.debug(f"OCR extracted {len(result.text)} chars with {result.confidence:.1f}% confidence")
            
        except Exception as e:
            result.warnings.append(f"OCR extraction failed: {e}")
            logger.error(f"OCR extraction error: {e}")
        
        return result
    
    def extract_from_image(self, filepath: str) -> OCRResult:
        """
        Extract text from an image file.
        
        Args:
            filepath: Path to image file (PNG, JPG, TIFF, etc.)
            
        Returns:
            OCRResult with extracted text
        """
        result = OCRResult(
            text="",
            confidence=0.0,
            pages=1,
            method="tesseract"
        )
        
        if not self.is_available:
            result.warnings.append("OCR not available")
            return result
        
        try:
            image = Image.open(filepath)
            processed = self._preprocess_image(image)
            
            # Get detailed data
            data = pytesseract.image_to_data(
                processed,
                lang=self.lang,
                output_type=pytesseract.Output.DICT
            )
            
            words = []
            confidences = []
            
            for i, word in enumerate(data['text']):
                if word.strip():
                    words.append(word)
                    conf = data['conf'][i]
                    if conf > 0:
                        confidences.append(conf)
            
            result.text = ' '.join(words)
            result.word_confidences = confidences
            result.page_texts = [result.text]
            
            if confidences:
                result.confidence = sum(confidences) / len(confidences)
                
        except Exception as e:
            result.warnings.append(f"Image OCR failed: {e}")
        
        return result
    
    def _preprocess_image(self, image: 'Image.Image') -> 'Image.Image':
        """
        Preprocess image for better OCR accuracy.
        
        Applies:
        - Grayscale conversion
        - Contrast enhancement
        - Noise reduction (if needed)
        """
        try:
            from PIL import ImageEnhance, ImageFilter
            
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Slight sharpening
            image = image.filter(ImageFilter.SHARPEN)
            
            return image
            
        except Exception:
            # Return original if preprocessing fails
            return image
    
    def detect_if_scanned(self, filepath: str) -> Tuple[bool, float]:
        """
        Detect if a PDF is scanned (image-based) vs native text.
        
        Returns:
            (is_scanned, confidence) tuple
        """
        try:
            import pdfplumber
            
            with pdfplumber.open(filepath) as pdf:
                total_text = 0
                total_pages = len(pdf.pages)
                
                for page in pdf.pages[:5]:  # Check first 5 pages
                    text = page.extract_text() or ""
                    total_text += len(text.strip())
                
                # If very little text extracted, likely scanned
                chars_per_page = total_text / max(total_pages, 1)
                
                if chars_per_page < 100:
                    return True, 0.9  # High confidence it's scanned
                elif chars_per_page < 500:
                    return True, 0.6  # Might be partially scanned
                else:
                    return False, 0.9  # Likely native text
                    
        except Exception:
            return False, 0.0


def get_ocr_capabilities() -> Dict[str, Any]:
    """Report OCR capabilities."""
    tesseract_version = None
    if PYTESSERACT_AVAILABLE:
        try:
            tesseract_version = pytesseract.get_tesseract_version()
        except:
            pass
    
    return {
        'pytesseract': PYTESSERACT_AVAILABLE,
        'pdf2image': PDF2IMAGE_AVAILABLE,
        'pil': PIL_AVAILABLE,
        'tesseract_version': str(tesseract_version) if tesseract_version else None,
        'ocr_available': PYTESSERACT_AVAILABLE and PIL_AVAILABLE,
        'pdf_ocr_available': PYTESSERACT_AVAILABLE and PIL_AVAILABLE and PDF2IMAGE_AVAILABLE,
    }


# Convenience function
def extract_text_ocr(filepath: str) -> str:
    """
    Extract text from a file using OCR.
    
    Args:
        filepath: Path to PDF or image file
        
    Returns:
        Extracted text string
    """
    extractor = OCRExtractor()
    
    if not extractor.is_available:
        return ""
    
    ext = Path(filepath).suffix.lower()
    
    if ext == '.pdf':
        result = extractor.extract_from_pdf(filepath)
    elif ext in ('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'):
        result = extractor.extract_from_image(filepath)
    else:
        return ""
    
    return result.text
