#!/usr/bin/env python3
"""
Image and Figure Checker v1.0.0
===============================
Analyzes images and figures in DOCX documents.

FEATURES:
- Extract images from DOCX
- Check image resolution/quality
- Verify alt-text presence (accessibility)
- Check figure captions
- Validate figure numbering sequence
- Image format validation

Author: AEGIS
Version: reads from version.json (module v1.0)
"""

import os
import re
import zipfile
import struct
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from xml.etree import ElementTree as ET
from io import BytesIO

try:
    from base_checker import BaseChecker
except ImportError:
    class BaseChecker:
        CHECKER_NAME = "Unknown"
        CHECKER_VERSION = "1.0.0"
        def __init__(self, enabled=True):
            self.enabled = enabled
            self._errors = []
        def create_issue(self, **kwargs):
            kwargs['category'] = getattr(self, 'CHECKER_NAME', 'Unknown')
            return kwargs
        def safe_check(self, *args, **kwargs):
            try:
                return self.check(*args, **kwargs)
            except Exception as e:
                self._errors.append(str(e))
                return []

__version__ = "2.5.0"

# XML namespaces for DOCX
NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
    'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
}

# EMU (English Metric Units) to pixels conversion (96 DPI assumed)
EMU_PER_INCH = 914400
DEFAULT_DPI = 96


@dataclass
class ImageInfo:
    """Information about an image in the document."""
    filename: str
    rel_id: str
    format: str
    width_px: int = 0
    height_px: int = 0
    width_emu: int = 0
    height_emu: int = 0
    alt_text: str = ""
    title: str = ""
    paragraph_index: int = 0
    has_caption: bool = False
    caption_text: str = ""
    caption_number: str = ""
    file_size: int = 0


@dataclass
class FigureCaption:
    """Information about a figure caption."""
    number: str
    text: str
    paragraph_index: int
    full_text: str


class ImageFigureChecker(BaseChecker):
    """
    Analyze images and figures in DOCX documents.
    """
    
    CHECKER_NAME = "Images"
    CHECKER_VERSION = "1.0.0"
    
    # Minimum recommended resolution
    MIN_WIDTH = 100
    MIN_HEIGHT = 50
    
    # Figure caption pattern
    FIGURE_CAPTION_PATTERN = re.compile(
        r'^(?:Figure|Fig\.?)\s+(\d+(?:[.-]\d+)?|[A-Z](?:\.\d+)?)[.:\s—–-]\s*(.*)$',
        re.IGNORECASE
    )
    
    def __init__(
        self,
        enabled: bool = True,
        check_alt_text: bool = True,
        check_resolution: bool = True,
        check_captions: bool = True,
        check_numbering: bool = True,
        min_width: int = 100,
        min_height: int = 50
    ):
        super().__init__(enabled)
        self.check_alt_text = check_alt_text
        self.check_resolution = check_resolution
        self.check_captions = check_captions
        self.check_numbering = check_numbering
        self.min_width = min_width
        self.min_height = min_height
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        """Check images and figures in document."""
        if not self.enabled:
            return []
        
        filepath = kwargs.get('filepath', '')
        if not filepath or not os.path.exists(filepath):
            return []
        
        issues = []
        
        # Extract images from DOCX
        images = self._extract_images(filepath)
        
        # Find figure captions in paragraphs
        captions = self._find_captions(paragraphs)
        
        # Associate images with captions
        self._associate_captions(images, captions, paragraphs)
        
        # Run checks on images
        for img in images:
            if self.check_alt_text:
                issues.extend(self._check_alt_text(img))
            
            if self.check_resolution:
                issues.extend(self._check_resolution(img))
            
            if self.check_captions:
                issues.extend(self._check_caption(img))
        
        # Check figure numbering sequence
        if self.check_numbering and captions:
            issues.extend(self._check_figure_numbering(captions))
        
        return issues
    
    def _extract_images(self, filepath: str) -> List[ImageInfo]:
        """Extract all images from a DOCX file."""
        images = []
        
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                # Get relationships for image targets
                rels = {}
                rels_file = 'word/_rels/document.xml.rels'
                if rels_file in zf.namelist():
                    with zf.open(rels_file) as f:
                        rels_tree = ET.parse(f)
                        for rel in rels_tree.findall('.//{%s}Relationship' % NAMESPACES['rel']):
                            rel_id = rel.get('Id', '')
                            target = rel.get('Target', '')
                            rel_type = rel.get('Type', '')
                            if 'image' in rel_type.lower():
                                rels[rel_id] = target
                
                # Parse document.xml for images
                if 'word/document.xml' in zf.namelist():
                    with zf.open('word/document.xml') as f:
                        doc_tree = ET.parse(f)
                        
                        para_idx = 0
                        for para in doc_tree.iter('{%s}p' % NAMESPACES['w']):
                            # Check for drawings in this paragraph
                            for drawing in para.iter('{%s}drawing' % NAMESPACES['w']):
                                img_info = self._parse_drawing(drawing, rels, para_idx, zf)
                                if img_info:
                                    images.append(img_info)
                            
                            para_idx += 1
        
        except Exception as e:
            self._errors.append(f"Error extracting images: {e}")
        
        return images
    
    def _parse_drawing(
        self,
        drawing: ET.Element,
        rels: Dict[str, str],
        para_idx: int,
        zf: zipfile.ZipFile
    ) -> Optional[ImageInfo]:
        """Parse a drawing element to extract image info."""
        try:
            # Find the blip (image reference)
            blip = None
            for b in drawing.iter('{%s}blip' % NAMESPACES['a']):
                blip = b
                break
            
            if blip is None:
                return None
            
            embed = blip.get('{%s}embed' % NAMESPACES['r'], '')
            if not embed or embed not in rels:
                return None
            
            target = rels[embed]
            filename = os.path.basename(target)
            ext = os.path.splitext(filename)[1].lower().lstrip('.')
            
            # Get alt text and title from docPr
            alt_text = ""
            title = ""
            for docPr in drawing.iter('{%s}docPr' % NAMESPACES['wp']):
                alt_text = docPr.get('descr', '') or ''
                title = docPr.get('title', '') or ''
                break
            
            # Get dimensions from extent
            width_emu = 0
            height_emu = 0
            for extent in drawing.iter('{%s}extent' % NAMESPACES['wp']):
                try:
                    width_emu = int(extent.get('cx', 0))
                    height_emu = int(extent.get('cy', 0))
                except (ValueError, TypeError):
                    pass
                break
            
            # Convert EMU to pixels (assuming 96 DPI)
            width_px = int(width_emu / EMU_PER_INCH * DEFAULT_DPI) if width_emu else 0
            height_px = int(height_emu / EMU_PER_INCH * DEFAULT_DPI) if height_emu else 0
            
            # Get file size
            file_size = 0
            img_path = f'word/{target}' if not target.startswith('word/') else target
            if img_path in zf.namelist():
                file_size = zf.getinfo(img_path).file_size
            
            return ImageInfo(
                filename=filename,
                rel_id=embed,
                format=ext,
                width_px=width_px,
                height_px=height_px,
                width_emu=width_emu,
                height_emu=height_emu,
                alt_text=alt_text.strip(),
                title=title.strip(),
                paragraph_index=para_idx,
                file_size=file_size
            )
        
        except Exception as e:
            self._errors.append(f"Error parsing drawing: {e}")
            return None
    
    def _find_captions(self, paragraphs: List[Tuple[int, str]]) -> List[FigureCaption]:
        """Find figure captions in paragraphs."""
        captions = []
        
        for idx, text in paragraphs:
            match = self.FIGURE_CAPTION_PATTERN.match(text.strip())
            if match:
                captions.append(FigureCaption(
                    number=match.group(1),
                    text=match.group(2).strip() if match.group(2) else '',
                    paragraph_index=idx,
                    full_text=text.strip()
                ))
        
        return captions
    
    def _associate_captions(
        self,
        images: List[ImageInfo],
        captions: List[FigureCaption],
        paragraphs: List[Tuple[int, str]]
    ):
        """Associate images with their nearest captions."""
        for img in images:
            # Look for caption within 2 paragraphs before or after
            best_caption = None
            best_distance = 999
            
            for cap in captions:
                distance = abs(cap.paragraph_index - img.paragraph_index)
                if distance <= 2 and distance < best_distance:
                    best_distance = distance
                    best_caption = cap
            
            if best_caption:
                img.has_caption = True
                img.caption_text = best_caption.text
                img.caption_number = best_caption.number
    
    def _check_alt_text(self, img: ImageInfo) -> List[Dict]:
        """Check for missing alt-text (accessibility)."""
        issues = []
        
        if not img.alt_text and not img.title:
            issues.append(self.create_issue(
                severity='Medium',
                message=f'Image missing alt-text (accessibility issue): {img.filename}',
                context=f'Image at paragraph {img.paragraph_index}',
                paragraph_index=img.paragraph_index,
                suggestion='Add descriptive alt-text for screen readers',
                rule_id='IMG001',
                flagged_text=img.filename
            ))
        elif img.alt_text and len(img.alt_text) < 10:
            issues.append(self.create_issue(
                severity='Low',
                message=f'Image alt-text may be too brief: "{img.alt_text}"',
                context=f'Image: {img.filename}',
                paragraph_index=img.paragraph_index,
                suggestion='Consider adding more descriptive alt-text',
                rule_id='IMG002',
                flagged_text=img.alt_text
            ))
        
        return issues
    
    def _check_resolution(self, img: ImageInfo) -> List[Dict]:
        """Check image resolution."""
        issues = []
        
        if img.width_px > 0 and img.height_px > 0:
            if img.width_px < self.min_width or img.height_px < self.min_height:
                issues.append(self.create_issue(
                    severity='Low',
                    message=f'Low resolution image: {img.width_px}x{img.height_px} pixels',
                    context=f'Image: {img.filename}',
                    paragraph_index=img.paragraph_index,
                    suggestion=f'Consider using higher resolution (min {self.min_width}x{self.min_height})',
                    rule_id='IMG010',
                    flagged_text=img.filename
                ))
        
        return issues
    
    def _check_caption(self, img: ImageInfo) -> List[Dict]:
        """Check for missing figure caption."""
        issues = []
        
        if not img.has_caption:
            issues.append(self.create_issue(
                severity='Medium',
                message=f'Image may be missing a figure caption: {img.filename}',
                context=f'Image at paragraph {img.paragraph_index}',
                paragraph_index=img.paragraph_index,
                suggestion='Add a caption like "Figure X. Description"',
                rule_id='IMG020',
                flagged_text=img.filename
            ))
        elif not img.caption_text:
            issues.append(self.create_issue(
                severity='Low',
                message=f'Figure {img.caption_number} caption has no description',
                context=f'Image: {img.filename}',
                paragraph_index=img.paragraph_index,
                suggestion='Add a descriptive caption after the figure number',
                rule_id='IMG021',
                flagged_text=f'Figure {img.caption_number}'
            ))
        
        return issues
    
    def _check_figure_numbering(self, captions: List[FigureCaption]) -> List[Dict]:
        """Check figure numbering sequence."""
        issues = []
        
        if not captions:
            return issues
        
        # Group by prefix (for numbered like 1, 2, 3 vs A.1, A.2)
        simple_numbers = []
        
        for cap in captions:
            # Try to parse as simple integer
            try:
                num = int(cap.number)
                simple_numbers.append((num, cap))
            except ValueError:
                pass  # Complex numbering like "A.1" - skip sequence check
        
        # Check sequence for simple numbers
        if simple_numbers:
            simple_numbers.sort(key=lambda x: x[0])
            
            expected = 1
            for num, cap in simple_numbers:
                if num != expected:
                    if num < expected:
                        issues.append(self.create_issue(
                            severity='Medium',
                            message=f'Duplicate figure number: Figure {num}',
                            context=cap.full_text[:60],
                            paragraph_index=cap.paragraph_index,
                            suggestion='Check figure numbering sequence',
                            rule_id='IMG030',
                            flagged_text=f'Figure {num}'
                        ))
                    else:
                        issues.append(self.create_issue(
                            severity='Medium',
                            message=f'Missing figure number(s) before Figure {num} (expected {expected})',
                            context=cap.full_text[:60],
                            paragraph_index=cap.paragraph_index,
                            suggestion=f'Add missing Figure {expected} or renumber',
                            rule_id='IMG031',
                            flagged_text=f'Figure {num}'
                        ))
                expected = num + 1
        
        return issues


if __name__ == '__main__':
    print(f"Image and Figure Checker v{__version__}")
    print("=" * 50)
    
    checker = ImageFigureChecker()
    
    # Test caption parsing
    test_paragraphs = [
        (0, "1.0 INTRODUCTION"),
        (1, "This section introduces the system."),
        (2, "Figure 1. System Architecture Overview"),
        (3, "The architecture shows the main components."),
        (4, "Figure 3. Detailed Component View"),  # Missing Figure 2
        (5, "Figure 3. Duplicate Caption"),  # Duplicate
    ]
    
    captions = checker._find_captions(test_paragraphs)
    print(f"\nFound {len(captions)} figure captions:")
    for cap in captions:
        print(f"  Figure {cap.number}: {cap.text[:40] if cap.text else '(no description)'}")
    
    numbering_issues = checker._check_figure_numbering(captions)
    print(f"\nNumbering issues: {len(numbering_issues)}")
    for issue in numbering_issues:
        print(f"  [{issue['severity']}] {issue['message']}")
