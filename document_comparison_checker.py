#!/usr/bin/env python3
"""
Document Comparison Checker v1.0.0
==================================
Compares two DOCX files and generates a detailed change report.

FEATURES:
- Paragraph-level comparison
- Addition/deletion/modification tracking
- Side-by-side diff generation
- Change statistics
- Integration with review workflow

USAGE:
- Compare document versions
- Track changes between drafts
- Generate redline reports

Author: AEGIS
Version: reads from version.json (module v1.0)
"""

import os
import re
import zipfile
import difflib
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
from xml.etree import ElementTree as ET

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

# XML namespaces
NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
}


class ChangeType(Enum):
    ADDED = "added"
    DELETED = "deleted"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


@dataclass
class DocumentChange:
    """Represents a change between document versions."""
    change_type: ChangeType
    paragraph_index: int
    old_text: str
    new_text: str
    similarity: float = 1.0
    context: str = ""


class DocumentComparer:
    """
    Compare two DOCX documents and generate change report.
    """
    
    def __init__(self, similarity_threshold: float = 0.6):
        """
        Args:
            similarity_threshold: Minimum similarity ratio to consider texts as modified
                                  vs added/deleted (0.0 to 1.0)
        """
        self.similarity_threshold = similarity_threshold
        self._errors = []
    
    def compare(
        self,
        old_filepath: str,
        new_filepath: str
    ) -> List[DocumentChange]:
        """
        Compare two DOCX files and return list of changes.
        
        Args:
            old_filepath: Path to original document
            new_filepath: Path to modified document
        
        Returns:
            List of DocumentChange objects
        """
        # Extract paragraphs from both documents
        old_paragraphs = self._extract_paragraphs(old_filepath)
        new_paragraphs = self._extract_paragraphs(new_filepath)
        
        if old_paragraphs is None or new_paragraphs is None:
            return []
        
        # Perform comparison
        changes = self._compare_paragraphs(old_paragraphs, new_paragraphs)
        
        return changes
    
    def _extract_paragraphs(self, filepath: str) -> Optional[List[str]]:
        """Extract paragraph texts from a DOCX file."""
        paragraphs = []
        
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                if 'word/document.xml' not in zf.namelist():
                    self._errors.append(f"Not a valid DOCX: {filepath}")
                    return None
                
                with zf.open('word/document.xml') as f:
                    tree = ET.parse(f)
                    
                    for para in tree.iter('{%s}p' % NAMESPACES['w']):
                        text_parts = []
                        for t in para.iter('{%s}t' % NAMESPACES['w']):
                            if t.text:
                                text_parts.append(t.text)
                        
                        para_text = ''.join(text_parts).strip()
                        if para_text:  # Only include non-empty paragraphs
                            paragraphs.append(para_text)
        
        except Exception as e:
            self._errors.append(f"Error reading {filepath}: {e}")
            return None
        
        return paragraphs
    
    def _compare_paragraphs(
        self,
        old_paras: List[str],
        new_paras: List[str]
    ) -> List[DocumentChange]:
        """Compare two lists of paragraphs using sequence matching."""
        changes = []
        
        # Use difflib for intelligent sequence matching
        matcher = difflib.SequenceMatcher(None, old_paras, new_paras)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Unchanged paragraphs
                for idx, para in enumerate(old_paras[i1:i2]):
                    changes.append(DocumentChange(
                        change_type=ChangeType.UNCHANGED,
                        paragraph_index=i1 + idx,
                        old_text=para,
                        new_text=para,
                        similarity=1.0
                    ))
            
            elif tag == 'delete':
                # Paragraphs removed in new version
                for idx, para in enumerate(old_paras[i1:i2]):
                    changes.append(DocumentChange(
                        change_type=ChangeType.DELETED,
                        paragraph_index=i1 + idx,
                        old_text=para,
                        new_text='',
                        similarity=0.0
                    ))
            
            elif tag == 'insert':
                # Paragraphs added in new version
                for idx, para in enumerate(new_paras[j1:j2]):
                    changes.append(DocumentChange(
                        change_type=ChangeType.ADDED,
                        paragraph_index=j1 + idx,
                        old_text='',
                        new_text=para,
                        similarity=0.0
                    ))
            
            elif tag == 'replace':
                # Paragraphs modified - need to match them
                old_section = old_paras[i1:i2]
                new_section = new_paras[j1:j2]
                
                # Try to find best matches
                matched_changes = self._match_modified_paragraphs(
                    old_section, new_section, i1, j1
                )
                changes.extend(matched_changes)
        
        return changes
    
    def _match_modified_paragraphs(
        self,
        old_section: List[str],
        new_section: List[str],
        old_start: int,
        new_start: int
    ) -> List[DocumentChange]:
        """Match modified paragraphs between sections."""
        changes = []
        matched_new = set()
        
        # For each old paragraph, find best matching new paragraph
        for old_idx, old_para in enumerate(old_section):
            best_match = None
            best_ratio = 0.0
            best_new_idx = -1
            
            for new_idx, new_para in enumerate(new_section):
                if new_idx in matched_new:
                    continue
                
                ratio = difflib.SequenceMatcher(None, old_para, new_para).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = new_para
                    best_new_idx = new_idx
            
            if best_ratio >= self.similarity_threshold:
                # Found a match - it's a modification
                matched_new.add(best_new_idx)
                changes.append(DocumentChange(
                    change_type=ChangeType.MODIFIED,
                    paragraph_index=old_start + old_idx,
                    old_text=old_para,
                    new_text=best_match,
                    similarity=best_ratio
                ))
            else:
                # No good match - it's a deletion
                changes.append(DocumentChange(
                    change_type=ChangeType.DELETED,
                    paragraph_index=old_start + old_idx,
                    old_text=old_para,
                    new_text='',
                    similarity=0.0
                ))
        
        # Any unmatched new paragraphs are additions
        for new_idx, new_para in enumerate(new_section):
            if new_idx not in matched_new:
                changes.append(DocumentChange(
                    change_type=ChangeType.ADDED,
                    paragraph_index=new_start + new_idx,
                    old_text='',
                    new_text=new_para,
                    similarity=0.0
                ))
        
        return changes
    
    def generate_report(self, changes: List[DocumentChange]) -> Dict:
        """Generate a summary report of changes."""
        added = [c for c in changes if c.change_type == ChangeType.ADDED]
        deleted = [c for c in changes if c.change_type == ChangeType.DELETED]
        modified = [c for c in changes if c.change_type == ChangeType.MODIFIED]
        unchanged = [c for c in changes if c.change_type == ChangeType.UNCHANGED]
        
        return {
            'total_changes': len(added) + len(deleted) + len(modified),
            'paragraphs_added': len(added),
            'paragraphs_deleted': len(deleted),
            'paragraphs_modified': len(modified),
            'paragraphs_unchanged': len(unchanged),
            'change_percentage': (len(added) + len(deleted) + len(modified)) / 
                                max(1, len(changes)) * 100,
            'additions': [{'text': c.new_text[:100], 'index': c.paragraph_index} for c in added],
            'deletions': [{'text': c.old_text[:100], 'index': c.paragraph_index} for c in deleted],
            'modifications': [
                {
                    'old': c.old_text[:100],
                    'new': c.new_text[:100],
                    'index': c.paragraph_index,
                    'similarity': c.similarity
                }
                for c in modified
            ]
        }
    
    def generate_diff_text(self, changes: List[DocumentChange]) -> str:
        """Generate a text-based diff representation."""
        lines = []
        
        for change in changes:
            if change.change_type == ChangeType.ADDED:
                lines.append(f"+ [{change.paragraph_index}] {change.new_text}")
            elif change.change_type == ChangeType.DELETED:
                lines.append(f"- [{change.paragraph_index}] {change.old_text}")
            elif change.change_type == ChangeType.MODIFIED:
                lines.append(f"~ [{change.paragraph_index}] OLD: {change.old_text[:80]}...")
                lines.append(f"  [{change.paragraph_index}] NEW: {change.new_text[:80]}...")
        
        return '\n'.join(lines)


class DocumentComparisonChecker(BaseChecker):
    """
    Checker wrapper for document comparison.
    Reports significant changes as issues for review.
    """
    
    CHECKER_NAME = "Document Comparison"
    CHECKER_VERSION = "1.0.0"
    
    def __init__(
        self,
        enabled: bool = True,
        comparison_filepath: Optional[str] = None,
        report_additions: bool = True,
        report_deletions: bool = True,
        report_modifications: bool = True
    ):
        super().__init__(enabled)
        self.comparison_filepath = comparison_filepath
        self.report_additions = report_additions
        self.report_deletions = report_deletions
        self.report_modifications = report_modifications
        self.comparer = DocumentComparer()
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        """
        Compare current document with comparison document.
        
        Args:
            paragraphs: Current document paragraphs (not used directly)
            **kwargs:
                - filepath: Current document path
                - comparison_filepath: Document to compare against
        
        Returns:
            List of change issues
        """
        if not self.enabled:
            return []
        
        current_filepath = kwargs.get('filepath', '')
        compare_filepath = kwargs.get('comparison_filepath', self.comparison_filepath)
        
        if not current_filepath or not compare_filepath:
            return []
        
        if not os.path.exists(current_filepath) or not os.path.exists(compare_filepath):
            return []
        
        issues = []
        
        # Perform comparison
        changes = self.comparer.compare(compare_filepath, current_filepath)
        
        for change in changes:
            if change.change_type == ChangeType.ADDED and self.report_additions:
                issues.append(self.create_issue(
                    severity='Info',
                    message=f'New paragraph added',
                    context=change.new_text[:80],
                    paragraph_index=change.paragraph_index,
                    suggestion='Review new content',
                    rule_id='DC001',
                    flagged_text=change.new_text[:50]
                ))
            
            elif change.change_type == ChangeType.DELETED and self.report_deletions:
                issues.append(self.create_issue(
                    severity='Medium',
                    message=f'Paragraph deleted from previous version',
                    context=change.old_text[:80],
                    paragraph_index=change.paragraph_index,
                    suggestion='Verify deletion is intentional',
                    rule_id='DC002',
                    flagged_text=change.old_text[:50]
                ))
            
            elif change.change_type == ChangeType.MODIFIED and self.report_modifications:
                similarity_pct = int(change.similarity * 100)
                issues.append(self.create_issue(
                    severity='Low',
                    message=f'Paragraph modified ({similarity_pct}% similar)',
                    context=f'Was: {change.old_text[:40]}... Now: {change.new_text[:40]}...',
                    paragraph_index=change.paragraph_index,
                    suggestion='Review modification',
                    rule_id='DC003',
                    flagged_text=change.new_text[:50]
                ))
        
        return issues


if __name__ == '__main__':
    print(f"Document Comparison Checker v{__version__}")
    print("=" * 50)
    
    # Demo
    comparer = DocumentComparer()
    
    # Simulate comparison
    old_paras = [
        "1.0 INTRODUCTION",
        "This document describes the system.",
        "The system shall meet all requirements.",
        "2.0 SCOPE",
        "The scope includes all subsystems."
    ]
    
    new_paras = [
        "1.0 INTRODUCTION",
        "This document describes the system architecture.",  # Modified
        "The system shall meet all requirements.",
        # Deleted: "2.0 SCOPE"
        "The scope includes all subsystems and interfaces.",  # Modified
        "3.0 NEW SECTION"  # Added
    ]
    
    changes = comparer._compare_paragraphs(old_paras, new_paras)
    report = comparer.generate_report(changes)
    
    print(f"\nChange Summary:")
    print(f"  Added: {report['paragraphs_added']}")
    print(f"  Deleted: {report['paragraphs_deleted']}")
    print(f"  Modified: {report['paragraphs_modified']}")
    print(f"  Unchanged: {report['paragraphs_unchanged']}")
    print(f"  Change %: {report['change_percentage']:.1f}%")
    
    print(f"\nDetailed Changes:")
    print(comparer.generate_diff_text(changes))
