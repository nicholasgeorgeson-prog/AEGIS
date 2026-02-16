#!/usr/bin/env python3
"""
Markup Engine v6.0.0 (Robust COM-Based)
=======================================
Creates marked-up copies of Word documents with comments and tracked changes.

v6.0.0 FIXES:
- Primary method is now COM-based (more reliable on Windows)
- Ensures Track Changes is properly enabled and visible
- Better comment placement using flagged_text or context
- Added bulk change capability
- Fixed "unreadable content" errors
- Falls back to lxml only when COM unavailable

REQUIRES: pip install pywin32 (for Windows COM)
          pip install lxml (fallback for non-Windows)
"""

import os
import re
import shutil
import zipfile
import tempfile
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path

__version__ = "2.9.1"

# Backward compatibility alias
DocumentMarker = None  # Will be set after MarkupEngine is defined

# Check for win32com (primary method)
try:
    import win32com.client
    import pythoncom
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("[MarkupEngine] WARNING: pywin32 not available. Install with: pip install pywin32")

# Check for lxml (fallback)
try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False

# OOXML Namespaces
NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}

W_NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

# Logging
DEBUG_LOG = None
LOG_FOLDER = None  # Can be set to enable debug logging to a folder


def _log(msg: str):
    global DEBUG_LOG
    print(f"[DEBUG] {msg}")
    if DEBUG_LOG:
        try:
            with open(DEBUG_LOG, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()} - {msg}\n")
        except Exception:  # Intentionally ignored
            pass


class MarkupEngine:
    """Creates marked-up Word documents with review comments and track changes."""
    
    def __init__(self, author: str = "AEGIS"):
        self.author = author
        self.stats: Dict[str, Any] = {}
        self._errors: List[str] = []
    
    def create_marked_copy(
        self,
        source_path: str,
        output_path: str,
        issues: List[Dict],
        reviewer_name: str = None,
        enable_track_changes: bool = True
    ) -> bool:
        """
        Create a marked copy with comments.
        
        Args:
            source_path: Source document path
            output_path: Output document path  
            issues: List of issues to add as comments
            reviewer_name: Name to attribute comments to
            enable_track_changes: Whether to enable track changes mode
        
        Returns:
            True if successful
        """
        global DEBUG_LOG
        
        if LOG_FOLDER:
            DEBUG_LOG = os.path.join(LOG_FOLDER, f"markup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        else:
            DEBUG_LOG = os.path.join(tempfile.gettempdir(), f"markup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        try:
            with open(DEBUG_LOG, 'w', encoding='utf-8') as f:
                f.write(f"Markup Engine v{__version__}\n")
                f.write(f"Time: {datetime.now().isoformat()}\n\n")
        except Exception:  # Caught and handled
            DEBUG_LOG = None
        
        self.stats = {
            'comments_added': 0, 
            'comments_attempted': 0,
            'existing_comments': 0, 
            'issues_received': len(issues) if issues else 0
        }
        self._errors = []
        
        if reviewer_name:
            self.author = reviewer_name
        
        _log(f"[MarkupEngine] Source: {source_path}")
        _log(f"[MarkupEngine] Output: {output_path}")
        _log(f"[MarkupEngine] Reviewer: {self.author}, Issues: {len(issues) if issues else 0}")
        
        if not source_path or not os.path.exists(source_path):
            _log("[MarkupEngine] ERROR: Source file not found")
            self._errors.append("Source file not found")
            return False
        
        if not output_path:
            _log("[MarkupEngine] ERROR: No output path specified")
            return False
        
        # Filter valid issues
        valid_issues = [i for i in (issues or []) if isinstance(i, dict)]
        _log(f"[MarkupEngine] Valid issues: {len(valid_issues)}")
        
        if not valid_issues:
            _log("[MarkupEngine] No issues to add, copying file...")
            if source_path != output_path:
                shutil.copy2(source_path, output_path)
            return True
        
        # Use COM if available (preferred on Windows)
        if WIN32_AVAILABLE:
            return self._create_with_com(source_path, output_path, valid_issues, enable_track_changes)
        elif LXML_AVAILABLE:
            return self._create_with_lxml(source_path, output_path, valid_issues)
        else:
            _log("[MarkupEngine] ERROR: No markup method available")
            self._errors.append("Neither pywin32 nor lxml is available")
            if source_path != output_path:
                shutil.copy2(source_path, output_path)
            return False
    
    def _create_with_com(
        self, 
        source_path: str, 
        output_path: str, 
        issues: List[Dict],
        enable_track_changes: bool = True
    ) -> bool:
        """
        Add comments using Word COM automation.
        Most reliable method for Windows.
        """
        if not WIN32_AVAILABLE:
            _log("[MarkupEngine] COM not available")
            return False
        
        word_app = None
        doc = None
        comments_added = 0
        
        # Track which texts we've already added comments for to prevent duplicates
        added_comments = set()
        
        def normalize_for_search(text):
            """Normalize text for Word search - collapse multiple spaces and decode entities."""
            if not text:
                return ""
            import html
            
            # Decode HTML entities (e.g., &amp; -> &)
            text = html.unescape(text)
            
            # Remove bullet point characters that might have been extracted
            text = text.replace('•', '').replace('*', '').replace('●', '')
            
            # Collapse multiple spaces/whitespace to single space
            text = re.sub(r'\s+', ' ', text.strip())
            
            # Remove special characters that might cause issues
            text = text.replace('\r', ' ').replace('\n', ' ')
            return text[:250]  # Word Find has a limit
        
        try:
            _log("[MarkupEngine] Initializing Word COM...")
            pythoncom.CoInitialize()
            
            word_app = win32com.client.DispatchEx("Word.Application")
            word_app.Visible = False
            word_app.DisplayAlerts = 0  # wdAlertsNone
            
            # Copy source to output first
            if source_path != output_path:
                shutil.copy2(source_path, output_path)
            
            import time
            time.sleep(0.3)
            
            abs_path = os.path.abspath(output_path)
            _log(f"[MarkupEngine] Opening: {abs_path}")
            
            doc = word_app.Documents.Open(
                abs_path, 
                ReadOnly=False, 
                AddToRecentFiles=False,
                Visible=False
            )
            
            # Set reviewer name
            if self.author:
                word_app.UserName = self.author
            
            # Enable Track Changes if requested
            if enable_track_changes:
                doc.TrackRevisions = True
                # Show all markup
                try:
                    doc.ActiveWindow.View.ShowRevisionsAndComments = True
                    doc.ActiveWindow.View.RevisionsView = 0  # wdRevisionsViewFinal with markup
                except Exception:  # Intentionally ignored
                    pass
                _log("[MarkupEngine] Track Changes enabled")
            
            _log(f"[MarkupEngine] Adding {len(issues)} comments...")
            self.stats['comments_attempted'] = len(issues)
            
            # Sort issues by paragraph index to process in order
            sorted_issues = sorted(issues, key=lambda x: x.get('paragraph_index', 0))
            
            for i, issue in enumerate(sorted_issues):
                try:
                    # Get text to find for comment anchor and normalize it
                    search_text = normalize_for_search(self._get_search_text(issue))
                    
                    if not search_text or len(search_text) < 3:
                        _log(f"[MarkupEngine] Issue {i+1}: No searchable text, skipping")
                        continue
                    
                    # Create dedup key
                    para_idx = issue.get('paragraph_index', 0)
                    category = issue.get('category', '')
                    dedup_key = (para_idx, category, search_text[:30])
                    
                    if dedup_key in added_comments:
                        _log(f"[MarkupEngine] Issue {i+1}: Duplicate, skipping")
                        continue
                    
                    # Build comment text
                    comment_text = self._build_comment_text(issue)
                    
                    # Find the text in document using a fresh range
                    rng = doc.Content
                    find = rng.Find
                    find.ClearFormatting()
                    
                    found = find.Execute(
                        FindText=search_text,
                        MatchCase=False,
                        MatchWholeWord=False,
                        Forward=True,
                        Wrap=0,  # wdFindStop - don't wrap
                        MatchWildcards=False
                    )
                    
                    if found:
                        try:
                            doc.Comments.Add(Range=rng, Text=comment_text)
                            comments_added += 1
                            added_comments.add(dedup_key)
                            _log(f"[MarkupEngine] Issue {i+1}: ✓ Comment added for '{search_text[:30]}...'")
                        except Exception as ce:
                            # v2.9.4 #23: Handle specific COM error codes gracefully
                            ce_str = str(ce)
                            if "-2147352567" in ce_str:
                                # This COM error often occurs with protected ranges or special characters
                                _log(f"[MarkupEngine] Issue {i+1}: ⚠ COM restriction (skipped): Range may be protected")
                            elif "-2147024809" in ce_str:
                                # Invalid parameter error
                                _log(f"[MarkupEngine] Issue {i+1}: ⚠ Invalid range parameter (skipped)")
                            else:
                                _log(f"[MarkupEngine] Issue {i+1}: ✗ Comment add error: {ce_str[:40]}")
                    else:
                        # Try shorter text
                        short_text = search_text[:50].strip()
                        if len(short_text) >= 3:
                            rng2 = doc.Content
                            find2 = rng2.Find
                            find2.ClearFormatting()
                            found = find2.Execute(
                                FindText=short_text,
                                MatchCase=False,
                                Forward=True,
                                Wrap=0,
                                MatchWildcards=False
                            )
                            if found:
                                try:
                                    doc.Comments.Add(Range=rng2, Text=comment_text)
                                    comments_added += 1
                                    added_comments.add(dedup_key)
                                    _log(f"[MarkupEngine] Issue {i+1}: ✓ Comment added (short match)")
                                except Exception as ce:
                                    # v2.9.4 #23: Handle specific COM error codes gracefully
                                    ce_str = str(ce)
                                    if "-2147352567" in ce_str or "-2147024809" in ce_str:
                                        _log(f"[MarkupEngine] Issue {i+1}: ⚠ COM restriction on short match (skipped)")
                                    else:
                                        _log(f"[MarkupEngine] Issue {i+1}: ✗ Short comment error: {ce_str[:40]}")
                            else:
                                _log(f"[MarkupEngine] Issue {i+1}: ✗ Text not found: '{search_text[:40]}...'")
                        else:
                            _log(f"[MarkupEngine] Issue {i+1}: ✗ Text too short to search")
                    
                except Exception as e:
                    _log(f"[MarkupEngine] Issue {i+1}: ✗ Error: {str(e)[:60]}")
            
            self.stats['comments_added'] = comments_added
            _log(f"[MarkupEngine] Added {comments_added}/{len(issues)} comments")
            
            # Ensure track changes is still on
            if enable_track_changes:
                doc.TrackRevisions = True
            
            # Save and close
            doc.Save()
            _log("[MarkupEngine] Document saved")
            
            return True
            
        except Exception as e:
            _log(f"[MarkupEngine] COM ERROR: {e}")
            import traceback
            _log(traceback.format_exc())
            self._errors.append(str(e))
            return False
            
        finally:
            try:
                if doc:
                    doc.Close(SaveChanges=True)
                    doc = None
            except Exception:  # Intentionally ignored
                pass
            try:
                if word_app:
                    word_app.Quit()
                    word_app = None
            except Exception:  # Intentionally ignored
                pass
            try:
                pythoncom.CoUninitialize()
            except Exception:  # Intentionally ignored
                pass
            
            import gc
            gc.collect()
            import time
            time.sleep(0.3)
    
    def _get_search_text(self, issue: Dict) -> str:
        """Get the best text to search for from an issue."""
        # Priority order for finding anchor text:
        # 1. flagged_text - the actual problematic text
        # 2. original_text - the text before fix
        # 3. context - surrounding context
        # 4. Extract from message (quoted text)
        
        search = issue.get('flagged_text', '').strip()
        if search and len(search) >= 2:
            return search
        
        search = issue.get('original_text', '').strip()
        if search and len(search) >= 2:
            return search
        
        search = issue.get('context', '').strip()
        if search and len(search) >= 2:
            return search
        
        # Try to extract quoted text from message
        msg = issue.get('message', '')
        match = re.search(r'"([^"]+)"', msg)
        if match and len(match.group(1)) >= 2:
            return match.group(1)
        
        # Last resort: use first word from message
        words = msg.split()
        if len(words) > 3:
            return ' '.join(words[:5])
        
        return ''
    
    def _build_comment_text(self, issue: Dict) -> str:
        """
        Build the comment text from an issue.
        
        v3.0.96: Enhanced format for better readability and actionability.
        
        Format:
        ═══════════════════════════════
        CATEGORY | SEVERITY
        ═══════════════════════════════
        
        ▸ Issue: [message]
        
        ✎ Suggestion: [suggestion]
        
        📍 Location: Paragraph [index]
        ───────────────────────────────
        """
        category = issue.get('category', 'Review')
        severity = issue.get('severity', 'Info')
        message = issue.get('message', 'Review this item')
        suggestion = issue.get('suggestion', '')
        para_idx = issue.get('paragraph_index', 0)
        rule_id = issue.get('rule_id', '')
        
        # Build structured comment
        lines = []
        
        # Header with category and severity
        header = f"{category}"
        if severity:
            header += f" | {severity}"
        lines.append(header)
        
        # Separator
        lines.append("─" * 30)
        
        # Main issue message
        lines.append(f"Issue: {message}")
        
        # Suggestion (if available)
        if suggestion and suggestion != '-':
            lines.append("")
            lines.append(f"Suggestion: {suggestion}")
        
        # Rule ID for traceability (if available)
        if rule_id:
            lines.append("")
            lines.append(f"Rule: {rule_id}")
        
        return "\n".join(lines)
    
    def apply_bulk_changes(
        self,
        source_path: str,
        output_path: str,
        changes: List[Dict],
        reviewer_name: str = None
    ) -> Dict:
        """
        Apply bulk find/replace changes with track changes.
        
        Args:
            source_path: Source document path
            output_path: Output document path
            changes: List of change dicts with 'find' and 'replace' keys
                     Can also include 'match_case', 'whole_word' options
            reviewer_name: Name for track changes attribution
        
        Returns:
            Dict with 'success', 'changes_applied', 'errors' keys
        """
        result = {
            'success': False,
            'changes_applied': 0,
            'changes_attempted': len(changes) if changes else 0,
            'errors': []
        }
        
        if not WIN32_AVAILABLE:
            result['errors'].append("Word COM not available - cannot apply changes")
            if source_path != output_path:
                shutil.copy2(source_path, output_path)
            return result
        
        if not changes:
            if source_path != output_path:
                shutil.copy2(source_path, output_path)
            result['success'] = True
            return result
        
        word_app = None
        doc = None
        
        try:
            _log("[BulkChanges] Initializing Word COM...")
            pythoncom.CoInitialize()
            
            word_app = win32com.client.DispatchEx("Word.Application")
            word_app.Visible = False
            word_app.DisplayAlerts = 0
            
            # Copy source to output
            if source_path != output_path:
                shutil.copy2(source_path, output_path)
            
            import time
            time.sleep(0.3)
            
            abs_path = os.path.abspath(output_path)
            doc = word_app.Documents.Open(abs_path, ReadOnly=False, AddToRecentFiles=False)
            
            # Enable Track Changes
            doc.TrackRevisions = True
            if reviewer_name:
                word_app.UserName = reviewer_name
            elif self.author:
                word_app.UserName = self.author
            
            _log(f"[BulkChanges] Applying {len(changes)} changes...")
            
            for i, change in enumerate(changes):
                find_text = change.get('find', '').strip()
                replace_text = change.get('replace', '')
                match_case = change.get('match_case', True)
                whole_word = change.get('whole_word', False)
                replace_all = change.get('replace_all', True)
                
                if not find_text:
                    _log(f"[BulkChanges] Change {i+1}: Empty find text, skipping")
                    continue
                
                try:
                    find = doc.Content.Find
                    find.ClearFormatting()
                    find.Replacement.ClearFormatting()
                    
                    # Execute replace
                    # wdReplaceAll = 2, wdReplaceOne = 1
                    replace_type = 2 if replace_all else 1
                    
                    replaced = find.Execute(
                        FindText=find_text,
                        MatchCase=match_case,
                        MatchWholeWord=whole_word,
                        Forward=True,
                        Wrap=1,  # wdFindContinue
                        ReplaceWith=replace_text,
                        Replace=replace_type
                    )
                    
                    if replaced:
                        result['changes_applied'] += 1
                        _log(f"[BulkChanges] Change {i+1}: ✓ '{find_text[:30]}' → '{replace_text[:30]}'")
                    else:
                        _log(f"[BulkChanges] Change {i+1}: ✗ '{find_text[:30]}' not found")
                        
                except Exception as e:
                    _log(f"[BulkChanges] Change {i+1}: ✗ Error: {str(e)[:50]}")
                    result['errors'].append(f"Change '{find_text[:20]}': {str(e)[:50]}")
            
            # Save document
            doc.Save()
            _log(f"[BulkChanges] Saved. Applied {result['changes_applied']}/{result['changes_attempted']} changes")
            
            result['success'] = True
            
        except Exception as e:
            _log(f"[BulkChanges] ERROR: {e}")
            result['errors'].append(str(e))
            import traceback
            _log(traceback.format_exc())
            
        finally:
            try:
                if doc:
                    doc.Close(SaveChanges=True)
                    doc = None
            except Exception:  # Intentionally ignored
                pass
            try:
                if word_app:
                    word_app.Quit()
                    word_app = None
            except Exception:  # Intentionally ignored
                pass
            try:
                pythoncom.CoUninitialize()
            except Exception:  # Intentionally ignored
                pass
            
            import gc
            gc.collect()
            import time
            time.sleep(0.3)
        
        return result
    
    def apply_fixes_with_track_changes(
        self,
        source_path: str,
        output_path: str,
        issues: List[Dict],
        reviewer_name: str = None,
        also_add_comments: bool = True
    ) -> Dict:
        """
        Apply fixes from issues as tracked changes, optionally adding comments.
        
        Issues with 'original_text' and 'replacement_text' will be applied as fixes.
        Other issues will be added as comments if also_add_comments=True.
        
        Args:
            source_path: Source document
            output_path: Output document
            issues: List of issue dicts
            reviewer_name: Attribution name
            also_add_comments: Add non-fixable issues as comments
        
        Returns:
            Dict with results
        """
        result = {
            'success': False,
            'fixes_applied': 0,
            'fixes_attempted': 0,
            'comments_added': 0,
            'errors': []
        }
        
        if not WIN32_AVAILABLE:
            result['errors'].append("Word COM not available")
            if source_path != output_path:
                shutil.copy2(source_path, output_path)
            return result
        
        # Separate fixable issues from comment-only issues
        # v2.9.1 FIX A12: Enhanced deduplication to prevent duplicate redlines
        # The bug occurs when the same fix is applied multiple times, causing
        # "perperper..." or "beforebefore..." corruption
        fixable = []
        comment_only = []
        
        # Track unique fixes by (normalized_original, normalized_replacement)
        # This prevents the same find/replace pair from being queued multiple times
        seen_fix_pairs = set()
        
        # Also track by original text alone to limit how many times we try to fix the same text
        fix_count_by_text = {}
        MAX_FIXES_PER_TEXT = 1  # Only allow one fix per unique original text
        
        for issue in (issues or []):
            orig = issue.get('original_text', '').strip()
            repl = issue.get('replacement_text', '')
            
            if orig and repl is not None and orig != repl:
                # Normalize both for comparison
                norm_orig = orig.lower().strip()[:100]
                norm_repl = (repl or '').lower().strip()[:100]
                
                # Create dedup key based on the actual find/replace pair
                dedup_key = (norm_orig, norm_repl)
                
                # Check if we've already queued this exact fix
                if dedup_key in seen_fix_pairs:
                    _log(f"[ApplyFixes] Skipping duplicate fix: '{orig[:30]}' -> '{repl[:30]}'")
                    continue
                
                # Check if we've already queued too many fixes for this original text
                text_key = norm_orig
                current_count = fix_count_by_text.get(text_key, 0)
                if current_count >= MAX_FIXES_PER_TEXT:
                    _log(f"[ApplyFixes] Skipping excess fix for text: '{orig[:30]}' (already have {current_count})")
                    continue
                
                seen_fix_pairs.add(dedup_key)
                fix_count_by_text[text_key] = current_count + 1
                
                fixable.append({
                    'find': orig,
                    'replace': repl,
                    'match_case': True,
                    'whole_word': False,
                    'replace_all': False,  # One at a time for precision
                    '_issue': issue,
                    '_dedup_key': dedup_key  # Store for tracking
                })
            else:
                comment_only.append(issue)
        
        _log(f"[ApplyFixes] Deduplicated: {len(seen_fix_pairs)} unique fixes from {len(issues or [])} issues")
        
        result['fixes_attempted'] = len(fixable)
        _log(f"[ApplyFixes] {len(fixable)} fixable (deduplicated), {len(comment_only)} comment-only issues")
        
        word_app = None
        doc = None
        
        def normalize_for_search(text):
            """Normalize text for Word search - collapse multiple spaces and decode entities."""
            if not text:
                return ""
            import re
            import html
            
            # Decode HTML entities (e.g., &amp; -> &)
            text = html.unescape(text)
            
            # Remove bullet point characters that might have been extracted
            text = text.replace('•', '').replace('*', '').replace('●', '')
            
            # Collapse multiple spaces/tabs/newlines to single space
            text = re.sub(r'\s+', ' ', text.strip())
            
            # Remove special characters that might cause issues
            text = text.replace('\r', ' ').replace('\n', ' ')
            return text[:250]  # Word Find has a limit
        
        try:
            pythoncom.CoInitialize()
            
            word_app = win32com.client.DispatchEx("Word.Application")
            word_app.Visible = False
            word_app.DisplayAlerts = 0
            
            if source_path != output_path:
                shutil.copy2(source_path, output_path)
            
            import time
            time.sleep(0.3)
            
            abs_path = os.path.abspath(output_path)
            doc = word_app.Documents.Open(abs_path, ReadOnly=False, AddToRecentFiles=False)
            
            # Enable Track Changes BEFORE any modifications
            doc.TrackRevisions = True
            if reviewer_name:
                word_app.UserName = reviewer_name
            elif self.author:
                word_app.UserName = self.author
            
            # Show markup
            try:
                doc.ActiveWindow.View.ShowRevisionsAndComments = True
                doc.ActiveWindow.View.RevisionsView = 0  # wdRevisionsViewFinal
            except Exception:  # Intentionally ignored
                pass
            
            # Apply fixes using Range.Text replacement for proper tracked changes
            # Find.Execute Replace doesn't always create tracked changes properly
            # v2.9.1 FIX A12: Track which fixes have been applied to prevent duplicates
            skipped_noop = 0
            applied_fixes = set()  # Track (find_text, replace_text) pairs that succeeded
            
            for fix in fixable:
                find_text = normalize_for_search(fix['find'])
                replace_text = normalize_for_search(fix['replace'])
                
                if not find_text:
                    continue
                
                # Skip no-op replacements (where normalized versions are identical)
                if find_text == replace_text:
                    skipped_noop += 1
                    continue
                
                # v2.9.1 FIX A12: Check if this exact fix was already applied
                fix_key = (find_text.lower(), replace_text.lower())
                if fix_key in applied_fixes:
                    _log(f"[ApplyFixes] Skipping already-applied fix: '{find_text[:25]}'")
                    continue
                
                # Use the original (un-normalized) replace text for actual replacement
                actual_replace = fix['replace']
                
                try:
                    # Method: Find the text, then replace via Range.Text
                    # This properly creates tracked changes
                    rng = doc.Content
                    find = rng.Find
                    find.ClearFormatting()
                    
                    # Find the text (don't replace yet)
                    found = find.Execute(
                        FindText=find_text,
                        MatchCase=True,
                        MatchWholeWord=False,
                        Forward=True,
                        Wrap=0,  # wdFindStop - don't wrap
                        MatchWildcards=False
                    )
                    
                    if found:
                        # Replace via Range.Text - this creates proper tracked change
                        rng.Text = actual_replace
                        result['fixes_applied'] += 1
                        applied_fixes.add(fix_key)  # v2.9.1: Mark as applied
                        _log(f"[ApplyFixes] ✓ '{find_text[:25]}' → '{actual_replace[:25]}'")
                    else:
                        # Try case-insensitive
                        rng2 = doc.Content
                        find2 = rng2.Find
                        find2.ClearFormatting()
                        
                        found = find2.Execute(
                            FindText=find_text,
                            MatchCase=False,
                            MatchWholeWord=False,
                            Forward=True,
                            Wrap=0,
                            MatchWildcards=False
                        )
                        
                        if found:
                            rng2.Text = actual_replace
                            result['fixes_applied'] += 1
                            applied_fixes.add(fix_key)  # v2.9.1: Mark as applied
                            _log(f"[ApplyFixes] ✓ (ci) '{find_text[:25]}' → '{actual_replace[:25]}'")
                        else:
                            _log(f"[ApplyFixes] ✗ Not found: '{find_text[:25]}'")
                        
                except Exception as e:
                    _log(f"[ApplyFixes] ✗ Error: {str(e)[:50]}")
                    result['errors'].append(str(e)[:50])
            
            if skipped_noop > 0:
                _log(f"[ApplyFixes] Skipped {skipped_noop} no-op replacements (text unchanged after normalization)")
            
            _log(f"[ApplyFixes] Applied {len(applied_fixes)} unique fixes")
            
            # Add comments for non-fixable issues (with deduplication)
            if also_add_comments and comment_only:
                _log(f"[ApplyFixes] Adding {len(comment_only)} comments...")
                
                # Dedup set to prevent duplicate comments
                added_comment_keys = set()
                
                for issue in comment_only:
                    try:
                        search_text = normalize_for_search(self._get_search_text(issue))
                        if not search_text or len(search_text) < 3:
                            continue
                        
                        # Create dedup key
                        para_idx = issue.get('paragraph_index', 0)
                        category = issue.get('category', '')
                        dedup_key = (para_idx, category, search_text[:30])
                        
                        # Skip if we already added this comment
                        if dedup_key in added_comment_keys:
                            continue
                        
                        comment_text = self._build_comment_text(issue)
                        
                        # Reset find object for each search
                        rng = doc.Content
                        find = rng.Find
                        find.ClearFormatting()
                        
                        # Use wildcards=False and simpler search
                        found = find.Execute(
                            FindText=search_text,
                            MatchCase=False,
                            MatchWholeWord=False,
                            Forward=True,
                            Wrap=0,  # wdFindStop - don't wrap
                            MatchWildcards=False
                        )
                        
                        if found:
                            try:
                                # Add comment to the found range
                                doc.Comments.Add(Range=rng, Text=comment_text)
                                result['comments_added'] += 1
                                added_comment_keys.add(dedup_key)
                            except Exception as ce:
                                _log(f"[ApplyFixes] Comment add error: {str(ce)[:30]}")
                        
                    except Exception as e:
                        _log(f"[ApplyFixes] Comment error: {str(e)[:40]}")
            
            # Verify revisions exist
            try:
                rev_count = doc.Revisions.Count
                comment_count = doc.Comments.Count
                _log(f"[ApplyFixes] Document has {rev_count} revisions, {comment_count} comments")
            except Exception:  # Intentionally ignored
                pass
            
            doc.Save()
            result['success'] = True
            
            # v3.0.96: Add detailed fix report for user feedback
            result['fix_report'] = {
                'attempted': result['fixes_attempted'],
                'applied': result['fixes_applied'],
                'not_found': result['fixes_attempted'] - result['fixes_applied'] - skipped_noop,
                'skipped_noop': skipped_noop,
                'comments_added': result.get('comments_added', 0),
                'summary': f"Applied {result['fixes_applied']} of {result['fixes_attempted']} fixes. " +
                          (f"Added {result.get('comments_added', 0)} comments. " if also_add_comments else "") +
                          (f"{skipped_noop} fixes skipped (no change needed)." if skipped_noop > 0 else "")
            }
            
        except Exception as e:
            _log(f"[ApplyFixes] ERROR: {e}")
            result['errors'].append(str(e))
            
        finally:
            try:
                if doc:
                    doc.Close(SaveChanges=True)
            except Exception:  # Intentionally ignored
                pass
            try:
                if word_app:
                    word_app.Quit()
            except Exception:  # Intentionally ignored
                pass
            try:
                pythoncom.CoUninitialize()
            except Exception:  # Intentionally ignored
                pass
            
            import gc
            gc.collect()
            import time
            time.sleep(0.3)
        
        return result
    
    def add_review_comments(
        self,
        source_path: str,
        output_path: str,
        issues: List[Dict],
        reviewer_name: str = None
    ) -> Dict:
        """
        Add review comments to a document (no track changes or fixes).
        
        Args:
            source_path: Source document path
            output_path: Output document path
            issues: List of issues to add as comments
            reviewer_name: Name for comment attribution
        
        Returns:
            Dict with 'success', 'comments_added', 'errors' keys
        """
        result = {
            'success': False,
            'comments_added': 0,
            'comments_attempted': len(issues) if issues else 0,
            'errors': []
        }
        
        if reviewer_name:
            self.author = reviewer_name
        
        _log(f"[AddComments] Source: {source_path}, Issues: {len(issues) if issues else 0}")
        
        # Use create_marked_copy which handles the actual work
        try:
            success = self.create_marked_copy(
                source_path,
                output_path,
                issues,
                reviewer_name=reviewer_name,
                enable_track_changes=False
            )
            
            result['success'] = success
            result['comments_added'] = self.stats.get('comments_added', 0)
            result['errors'] = self._errors.copy()
            
        except Exception as e:
            _log(f"[AddComments] Error: {e}")
            result['errors'].append(str(e))
            if source_path != output_path:
                shutil.copy2(source_path, output_path)
        
        return result
    
    def _create_with_lxml(self, source_path: str, output_path: str, issues: List[Dict]) -> bool:
        """
        Fallback: Create marked document using lxml.
        Used when COM is not available (non-Windows).
        """
        if not LXML_AVAILABLE:
            _log("[MarkupEngine] lxml not available")
            return False
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract docx
                with zipfile.ZipFile(source_path, 'r') as zf:
                    zf.extractall(temp_dir)
                
                # Parse document.xml
                doc_path = os.path.join(temp_dir, 'word', 'document.xml')
                parser = etree.XMLParser(recover=True)
                doc_tree = etree.parse(doc_path, parser)
                doc_root = doc_tree.getroot()
                
                # Get all paragraphs and their text
                paragraphs = doc_root.findall('.//w:p', NAMESPACES)
                
                # Create/update comments.xml
                comments_path = os.path.join(temp_dir, 'word', 'comments.xml')
                
                # Start new comments XML with proper namespace declarations
                COMMENTS_NSMAP = {
                    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
                    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
                    'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
                    'w14': 'http://schemas.microsoft.com/office/word/2010/wordml',
                    'w15': 'http://schemas.microsoft.com/office/word/2012/wordml',
                }
                
                comments_root = etree.Element(
                    f'{W_NS}comments',
                    nsmap=COMMENTS_NSMAP
                )
                
                comment_id = 0
                comments_added = 0
                
                for issue in issues:
                    # Find matching paragraph
                    search_text = self._get_search_text(issue)
                    if not search_text:
                        continue
                    
                    para_idx = issue.get('paragraph_index', -1)
                    
                    # Find paragraph by index or text match
                    target_para = None
                    if 0 <= para_idx < len(paragraphs):
                        target_para = paragraphs[para_idx]
                    else:
                        # Search for text
                        for para in paragraphs:
                            para_text = ''.join(t.text or '' for t in para.findall('.//w:t', NAMESPACES))
                            if search_text in para_text:
                                target_para = para
                                break
                    
                    if target_para is None:
                        continue
                    
                    # Create comment
                    comment_text = self._build_comment_text(issue)
                    
                    comment = etree.SubElement(comments_root, f'{W_NS}comment')
                    comment.set(f'{W_NS}id', str(comment_id))
                    comment.set(f'{W_NS}author', self.author)
                    comment.set(f'{W_NS}date', datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
                    comment.set(f'{W_NS}initials', self.author[:2].upper() if self.author else 'TR')
                    
                    # Comment paragraph
                    comment_p = etree.SubElement(comment, f'{W_NS}p')
                    comment_r = etree.SubElement(comment_p, f'{W_NS}r')
                    comment_t = etree.SubElement(comment_r, f'{W_NS}t')
                    comment_t.text = comment_text
                    
                    # Add comment reference to paragraph
                    first_run = target_para.find('.//w:r', NAMESPACES)
                    if first_run is not None:
                        comment_start = etree.Element(f'{W_NS}commentRangeStart')
                        comment_start.set(f'{W_NS}id', str(comment_id))
                        first_run.insert(0, comment_start)
                        
                        comment_end = etree.Element(f'{W_NS}commentRangeEnd')
                        comment_end.set(f'{W_NS}id', str(comment_id))
                        first_run.append(comment_end)
                        
                        comment_ref = etree.Element(f'{W_NS}commentReference')
                        comment_ref.set(f'{W_NS}id', str(comment_id))
                        
                        ref_run = etree.SubElement(target_para, f'{W_NS}r')
                        ref_run.append(comment_ref)
                    
                    comment_id += 1
                    comments_added += 1
                
                self.stats['comments_added'] = comments_added
                
                # Write modified document.xml
                with open(doc_path, 'wb') as f:
                    f.write(etree.tostring(doc_tree, xml_declaration=True, encoding='UTF-8', standalone='yes'))
                
                # Write comments.xml
                with open(comments_path, 'wb') as f:
                    f.write(etree.tostring(comments_root, xml_declaration=True, encoding='UTF-8', standalone='yes'))
                
                # Update document.xml.rels to include comments reference
                rels_path = os.path.join(temp_dir, 'word', '_rels', 'document.xml.rels')
                if os.path.exists(rels_path):
                    rels_tree = etree.parse(rels_path, parser)
                    rels_root = rels_tree.getroot()
                    
                    # Check if comments relationship already exists
                    RELS_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'
                    has_comments_rel = any(
                        'comments' in (elem.get('Target') or '').lower()
                        for elem in rels_root
                    )
                    
                    if not has_comments_rel:
                        # Find next rId
                        existing_ids = [int(elem.get('Id', 'rId0').replace('rId', '')) 
                                       for elem in rels_root if elem.get('Id', '').startswith('rId')]
                        next_id = max(existing_ids, default=0) + 1
                        
                        # Add relationship
                        rel = etree.SubElement(rels_root, f'{{{RELS_NS}}}Relationship')
                        rel.set('Id', f'rId{next_id}')
                        rel.set('Type', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments')
                        rel.set('Target', 'comments.xml')
                        
                        with open(rels_path, 'wb') as f:
                            f.write(etree.tostring(rels_tree, xml_declaration=True, encoding='UTF-8', standalone='yes'))
                
                # Update [Content_Types].xml
                ct_path = os.path.join(temp_dir, '[Content_Types].xml')
                if os.path.exists(ct_path):
                    ct_tree = etree.parse(ct_path, parser)
                    ct_root = ct_tree.getroot()
                    
                    # Get the namespace for content types
                    CT_NS = ct_root.tag.replace('Types', '').strip('{}') if ct_root.tag.startswith('{') else ''
                    
                    # Check if comments content type exists
                    has_comments = any(
                        'comments.xml' in (elem.get('PartName') or '')
                        for elem in ct_root
                    )
                    
                    if not has_comments:
                        if CT_NS:
                            override = etree.SubElement(ct_root, f'{{{CT_NS}}}Override')
                        else:
                            override = etree.SubElement(ct_root, 'Override')
                        override.set('PartName', '/word/comments.xml')
                        override.set('ContentType', 'application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml')
                        
                        with open(ct_path, 'wb') as f:
                            f.write(etree.tostring(ct_tree, xml_declaration=True, encoding='UTF-8', standalone='yes'))
                
                # Repack the docx
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arc_name = os.path.relpath(file_path, temp_dir)
                            # ZIP files always use forward slashes, convert Windows backslashes
                            arc_name = arc_name.replace('\\', '/')
                            zf.write(file_path, arc_name)
                
                _log(f"[MarkupEngine] lxml: Added {comments_added} comments")
                return True
                
        except Exception as e:
            _log(f"[MarkupEngine] lxml error: {e}")
            import traceback
            _log(traceback.format_exc())
            self._errors.append(str(e))
            
            if source_path != output_path:
                shutil.copy2(source_path, output_path)
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics from last operation."""
        return self.stats.copy()
    
    def get_errors(self) -> List[str]:
        """Get errors from last operation."""
        return self._errors.copy()


# Convenience functions
def create_marked_copy(
    source_path: str, 
    output_path: str, 
    issues: List[Dict], 
    reviewer_name: str = "AEGIS"
) -> bool:
    """Create a marked copy with comments."""
    return MarkupEngine(author=reviewer_name).create_marked_copy(
        source_path, output_path, issues, reviewer_name
    )


def apply_bulk_changes(
    source_path: str,
    output_path: str,
    changes: List[Dict],
    reviewer_name: str = "AEGIS"
) -> Dict:
    """Apply bulk find/replace changes with track changes."""
    return MarkupEngine(author=reviewer_name).apply_bulk_changes(
        source_path, output_path, changes, reviewer_name
    )


# Backward compatibility alias
DocumentMarker = MarkupEngine
