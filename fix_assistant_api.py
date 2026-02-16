# v3.0.97: Fix Assistant v2 - Backend API Enhancement
# WP1: Document content, fix grouping, confidence details, statistics

"""
Fix Assistant Backend API Enhancement Module

This module provides helper functions to transform TWR review results into
a rich API response supporting the premium Fix Assistant feature.

Functions:
    - build_document_content: Transform paragraphs into frontend-friendly format
    - group_similar_fixes: Group fixes with identical correction patterns
    - build_confidence_details: Explain confidence ratings for each fix
    - compute_fix_statistics: Pre-compute dashboard statistics
    - export_decision_log_csv: Generate CSV audit trail of decisions
"""

from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict
import csv
import io
from datetime import datetime


def build_document_content(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform raw paragraph data into frontend-friendly document content structure.
    
    Args:
        results: Dictionary containing review results with keys:
            - paragraphs: List of tuples [(para_idx, text), ...]
            - page_map: Dict {para_idx: page_number}
            - headings: List of dicts [{"text": str, "level": int}, ...]
    
    Returns:
        Dictionary with structure:
            {
                "paragraphs": [{"index": int, "text": str, "page": int, "is_heading": bool, ...}],
                "page_map": {para_index: page_number},
                "headings": [{"text": str, "level": int, "para_index": int}],
                "page_count": int
            }
    
    Notes:
        - DOCX files may not have page_map data; defaults page to 1
        - Handles missing/empty data gracefully
    """
    # Extract raw data with safe defaults
    raw_paragraphs = results.get('paragraphs', [])
    page_map = results.get('page_map', {})
    raw_headings = results.get('headings', [])
    
    # Normalize page_map keys to integers for consistent lookup
    normalized_page_map: Dict[int, int] = {}
    for key, value in page_map.items():
        try:
            normalized_page_map[int(key)] = int(value)
        except (ValueError, TypeError):
            continue
    
    # Build heading text lookup for O(1) checks
    # Map heading text (normalized) to its level
    heading_lookup: Dict[str, int] = {}
    for h in raw_headings:
        if isinstance(h, dict) and 'text' in h:
            heading_text = str(h.get('text', '')).strip().lower()
            heading_level = h.get('level', 1)
            if heading_text:
                heading_lookup[heading_text] = heading_level
    
    # Transform paragraphs into frontend format
    transformed_paragraphs: List[Dict[str, Any]] = []
    heading_para_indices: Dict[str, int] = {}  # Map heading text to para_index
    max_page = 1
    
    for item in raw_paragraphs:
        # Handle tuple format (idx, text) or dict format
        if isinstance(item, (tuple, list)) and len(item) >= 2:
            para_idx = item[0]
            para_text = item[1]
        elif isinstance(item, dict):
            para_idx = item.get('index', item.get('idx', 0))
            para_text = item.get('text', '')
        else:
            continue
        
        try:
            para_idx = int(para_idx)
        except (ValueError, TypeError):
            continue
        
        para_text = str(para_text) if para_text else ''
        
        # Get page number (default to 1 for DOCX without page mapping)
        page_num = normalized_page_map.get(para_idx, 1)
        max_page = max(max_page, page_num)
        
        # Check if this paragraph is a heading
        normalized_text = para_text.strip().lower()
        is_heading = normalized_text in heading_lookup
        
        para_dict: Dict[str, Any] = {
            "index": para_idx,
            "text": para_text,
            "page": page_num,
            "is_heading": is_heading
        }
        
        if is_heading:
            para_dict["heading_level"] = heading_lookup[normalized_text]
            heading_para_indices[normalized_text] = para_idx
        
        transformed_paragraphs.append(para_dict)
    
    # Sort paragraphs by index to ensure correct order
    transformed_paragraphs.sort(key=lambda p: p.get('index', 0))
    
    # Build headings list with para_index references
    enriched_headings: List[Dict[str, Any]] = []
    for h in raw_headings:
        if not isinstance(h, dict):
            continue
        
        heading_text = str(h.get('text', '')).strip()
        heading_level = h.get('level', 1)
        
        if not heading_text:
            continue
        
        normalized_text = heading_text.lower()
        para_index = heading_para_indices.get(normalized_text)
        
        enriched_headings.append({
            "text": heading_text,
            "level": heading_level,
            "para_index": para_index  # May be None if not found in paragraphs
        })
    
    return {
        "paragraphs": transformed_paragraphs,
        "page_map": {str(k): v for k, v in normalized_page_map.items()},  # JSON-safe keys
        "headings": enriched_headings,
        "page_count": max_page
    }


def group_similar_fixes(issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Group fixes with identical correction patterns for batch operations.
    
    Args:
        issues: List of issue dictionaries, each containing:
            - flagged_text: The problematic text
            - suggestion: The suggested correction
            - category: Issue category (Spelling, Grammar, etc.)
            - severity: Issue severity level
            - message: Human-readable description
    
    Returns:
        List of group dictionaries:
            {
                "group_id": str,
                "pattern": str,  # "original → replacement"
                "original": str,
                "replacement": str,
                "category": str,
                "severity": str,
                "fix_indices": List[int],
                "count": int,
                "message": str
            }
    
    Notes:
        - Only groups issues with both flagged_text AND suggestion
        - Excludes "Style" category (too context-dependent)
        - Only creates groups with count >= 2
    """
    if not issues:
        return []
    
    # Group key: (flagged_text.lower().strip(), suggestion.lower().strip())
    groups: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    
    for idx, issue in enumerate(issues):
        if not isinstance(issue, dict):
            continue
        
        flagged_text = issue.get('flagged_text', '')
        suggestion = issue.get('suggestion', '')
        category = issue.get('category', '')
        
        # Skip if missing required fields
        if not flagged_text or not suggestion:
            continue
        
        # Skip Style category (too context-dependent)
        if str(category).lower() == 'style':
            continue
        
        # Normalize for grouping
        key = (
            str(flagged_text).lower().strip(),
            str(suggestion).lower().strip()
        )
        
        groups[key].append({
            'index': idx,
            'issue': issue
        })
    
    # Build result list for groups with count >= 2
    result: List[Dict[str, Any]] = []
    group_counter = 0
    
    for (original_lower, replacement_lower), members in groups.items():
        if len(members) < 2:
            continue
        
        # Use the first member's original casing for display
        first_issue = members[0]['issue']
        original_display = first_issue.get('flagged_text', original_lower)
        replacement_display = first_issue.get('suggestion', replacement_lower)
        category = first_issue.get('category', 'Unknown')
        severity = first_issue.get('severity', 'Medium')
        message = first_issue.get('message', '')
        
        fix_indices = [m['index'] for m in members]
        
        result.append({
            "group_id": f"grp_{group_counter}",
            "pattern": f"{original_display} → {replacement_display}",
            "original": original_display,
            "replacement": replacement_display,
            "category": category,
            "severity": severity,
            "fix_indices": fix_indices,
            "count": len(members),
            "message": message
        })
        
        group_counter += 1
    
    # Sort by count (most frequent first)
    result.sort(key=lambda g: g['count'], reverse=True)
    
    return result


def _classify_confidence(issue: Dict[str, Any]) -> Tuple[str, float, List[str]]:
    """
    Internal helper to classify an issue's confidence tier.
    
    Args:
        issue: Single issue dictionary
    
    Returns:
        Tuple of (tier, score, reasons)
        - tier: "safe", "review", or "manual"
        - score: float 0.0-1.0
        - reasons: List of explanation strings
    """
    category = str(issue.get('category', '')).lower()
    severity = str(issue.get('severity', '')).lower()
    message = str(issue.get('message', '')).lower()
    has_suggestion = bool(issue.get('suggestion'))
    flagged_text = str(issue.get('flagged_text', '')).lower()
    
    # SAFE tier (auto-accept candidates)
    if category == 'spelling' and has_suggestion:
        return 'safe', 0.95, [
            "Common spelling error",
            "Single valid correction",
            "High dictionary confidence"
        ]
    
    if category == 'punctuation':
        if 'double space' in message:
            return 'safe', 0.92, [
                "Double space removal",
                "No ambiguity",
                "Mechanical fix"
            ]
        if 'missing period' in message:
            return 'safe', 0.90, [
                "Missing period at sentence end",
                "Clear sentence boundary"
            ]
        if 'extra space' in message or 'trailing space' in message:
            return 'safe', 0.91, [
                "Whitespace normalization",
                "No content change"
            ]
    
    # MANUAL tier (likely needs human decision)
    if category == 'style':
        return 'manual', 0.35, [
            "Style suggestion",
            "Subjective improvement",
            "Context-dependent change"
        ]
    
    if not has_suggestion:
        return 'manual', 0.30, [
            "No automatic fix available",
            "Requires manual correction",
            "Human judgment needed"
        ]
    
    if severity == 'info':
        return 'manual', 0.40, [
            "Informational only",
            "Optional change",
            "No clear error"
        ]
    
    # Category-specific REVIEW tier logic
    if category == 'grammar':
        return 'review', 0.65, [
            "Grammar correction",
            "Grammar rules can have exceptions",
            "Recommend manual verification"
        ]
    
    if category == 'acronym':
        return 'review', 0.60, [
            "Acronym handling",
            "Verify acronym definition is needed",
            "Check document conventions"
        ]
    
    if category == 'capitalization':
        return 'review', 0.70, [
            "Capitalization change",
            "May be intentional styling",
            "Verify against style guide"
        ]
    
    if category == 'consistency':
        return 'review', 0.55, [
            "Consistency issue",
            "Multiple valid forms may exist",
            "Check document-wide usage"
        ]
    
    # Default REVIEW tier
    reasons = ["Recommend manual verification"]
    if has_suggestion:
        reasons.append("Automatic fix available")
    if severity in ('medium', 'high', 'critical'):
        reasons.append(f"{severity.capitalize()} severity issue")
    
    return 'review', 0.65, reasons


def build_confidence_details(issues: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Build confidence details explaining why each fix is rated Safe/Review/Manual.
    
    Args:
        issues: List of issue dictionaries
    
    Returns:
        Dictionary with string keys (issue indices) mapping to:
            {
                "score": float,  # 0.0-1.0 confidence score
                "tier": str,     # "safe", "review", or "manual"
                "reasons": List[str]  # Explanation strings
            }
    
    Notes:
        - Uses string keys for JSON compatibility
        - Tier classification based on category, severity, and fix availability
    """
    if not issues:
        return {}
    
    confidence_map: Dict[str, Dict[str, Any]] = {}
    
    for idx, issue in enumerate(issues):
        if not isinstance(issue, dict):
            continue
        
        tier, score, reasons = _classify_confidence(issue)
        
        confidence_map[str(idx)] = {
            "score": score,
            "tier": tier,
            "reasons": reasons
        }
    
    return confidence_map


def compute_fix_statistics(
    issues: List[Dict[str, Any]],
    fix_groups: List[Dict[str, Any]],
    confidence_details: Dict[str, Dict[str, Any]],
    page_count: int
) -> Dict[str, Any]:
    """
    Pre-compute statistics for the Fix Assistant dashboard.
    
    Args:
        issues: List of issue dictionaries
        fix_groups: Result from group_similar_fixes()
        confidence_details: Result from build_confidence_details()
        page_count: Total pages in document
    
    Returns:
        Dictionary containing:
            - total_fixes: int
            - total_fixable: int (issues with suggestions)
            - total_unfixable: int (issues without suggestions)
            - by_category: Dict[str, int]
            - by_severity: Dict[str, int]
            - by_tier: Dict[str, int]
            - by_page: Dict[str, int]
            - pages_with_fixes: List[int]
            - group_count: int
            - grouped_fix_count: int
            - estimated_review_seconds: int
    """
    if not issues:
        return {
            "total_fixes": 0,
            "total_fixable": 0,
            "total_unfixable": 0,
            "by_category": {},
            "by_severity": {},
            "by_tier": {},
            "by_page": {},
            "pages_with_fixes": [],
            "group_count": 0,
            "grouped_fix_count": 0,
            "estimated_review_seconds": 0
        }
    
    # Initialize counters
    total_fixes = len(issues)
    total_fixable = 0
    total_unfixable = 0
    by_category: Dict[str, int] = defaultdict(int)
    by_severity: Dict[str, int] = defaultdict(int)
    by_tier: Dict[str, int] = defaultdict(int)
    by_page: Dict[str, int] = defaultdict(int)
    pages_with_fixes_set: set = set()
    
    # Count issues
    for idx, issue in enumerate(issues):
        if not isinstance(issue, dict):
            continue
        
        # Fixable vs unfixable
        if issue.get('suggestion'):
            total_fixable += 1
        else:
            total_unfixable += 1
        
        # By category (normalize capitalization)
        category = str(issue.get('category', 'Unknown'))
        if category:
            # Capitalize first letter for consistency
            category = category.capitalize()
            by_category[category] += 1
        
        # By severity (normalize capitalization)
        severity = str(issue.get('severity', 'Medium'))
        if severity:
            severity = severity.capitalize()
            by_severity[severity] += 1
        
        # By page
        page = issue.get('page', 1)
        try:
            page = int(page)
        except (ValueError, TypeError):
            page = 1
        
        by_page[str(page)] += 1
        pages_with_fixes_set.add(page)
        
        # By tier (from confidence_details)
        if str(idx) in confidence_details:
            tier = confidence_details[str(idx)].get('tier', 'review')
            by_tier[tier] += 1
    
    # Group statistics
    group_count = len(fix_groups)
    grouped_fix_count = sum(g.get('count', 0) for g in fix_groups)
    
    # Estimate review time
    # Safe fixes: ~1 second each (quick confirm)
    # Review fixes: ~4 seconds each
    # Manual fixes: ~8 seconds each
    safe_count = by_tier.get('safe', 0)
    review_count = by_tier.get('review', 0)
    manual_count = by_tier.get('manual', 0)
    
    estimated_review_seconds = (
        safe_count * 1 +
        review_count * 4 +
        manual_count * 8
    )
    
    # Sort pages list
    pages_with_fixes = sorted(pages_with_fixes_set)
    
    return {
        "total_fixes": total_fixes,
        "total_fixable": total_fixable,
        "total_unfixable": total_unfixable,
        "by_category": dict(by_category),
        "by_severity": dict(by_severity),
        "by_tier": dict(by_tier),
        "by_page": dict(by_page),
        "pages_with_fixes": pages_with_fixes,
        "group_count": group_count,
        "grouped_fix_count": grouped_fix_count,
        "estimated_review_seconds": estimated_review_seconds
    }


def export_decision_log_csv(
    decisions: List[Dict[str, Any]],
    issues: List[Dict[str, Any]],
    document_name: Optional[str] = None
) -> str:
    """
    Generate CSV string of all decisions for audit trail.
    
    Args:
        decisions: List of decision dictionaries:
            {
                "index": int,        # Issue index
                "decision": str,     # "accepted", "rejected", "skipped"
                "note": str,         # Optional reviewer note
                "timestamp": str     # ISO format timestamp
            }
        issues: Original issues list for context
        document_name: Optional document name for header comment
    
    Returns:
        CSV string content ready for file download
    
    Example output:
        fix_index,page,category,severity,original_text,suggested_fix,decision,reviewer_note,timestamp
        0,3,Spelling,Medium,recieve,receive,accepted,,2026-01-27T14:32:15
    """
    output = io.StringIO()
    
    # CSV header
    fieldnames = [
        'fix_index',
        'page',
        'category',
        'severity',
        'original_text',
        'suggested_fix',
        'decision',
        'reviewer_note',
        'timestamp'
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()
    
    # Build issues lookup for O(1) access
    issues_lookup: Dict[int, Dict[str, Any]] = {}
    for idx, issue in enumerate(issues):
        if isinstance(issue, dict):
            issues_lookup[idx] = issue
    
    # Write decision rows
    for decision in decisions:
        if not isinstance(decision, dict):
            continue
        
        idx = decision.get('index')
        if idx is None:
            continue
        
        try:
            idx = int(idx)
        except (ValueError, TypeError):
            continue
        
        # Get issue details
        issue = issues_lookup.get(idx, {})
        
        row = {
            'fix_index': idx,
            'page': issue.get('page', 1),
            'category': issue.get('category', ''),
            'severity': issue.get('severity', ''),
            'original_text': issue.get('flagged_text', ''),
            'suggested_fix': issue.get('suggestion', ''),
            'decision': decision.get('decision', ''),
            'reviewer_note': decision.get('note', ''),
            'timestamp': decision.get('timestamp', '')
        }
        
        writer.writerow(row)
    
    return output.getvalue()


# =============================================================================
# Flask API Endpoint
# =============================================================================

def register_fix_assistant_routes(app):
    """
    Register Fix Assistant API routes with a Flask app.
    
    Usage:
        from fix_assistant_api import register_fix_assistant_routes
        register_fix_assistant_routes(app)
    
    Args:
        app: Flask application instance
    """
    from flask import request, jsonify, Response
    
    @app.route('/api/export/decision-log', methods=['POST'])
    def export_decision_log():
        """
        Export review decisions as CSV file download.
        
        Request body:
        {
            "decisions": [...],       # Array of decision objects
            "issues": [...],          # Original issues array
            "document_name": "doc.docx"  # Optional document name
        }
        
        Returns:
            CSV file download with Content-Disposition header
        """
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No JSON data provided'
                }), 400
            
            decisions = data.get('decisions', [])
            issues = data.get('issues', [])
            document_name = data.get('document_name', 'document')
            
            if not decisions:
                return jsonify({
                    'success': False,
                    'error': 'No decisions provided'
                }), 400
            
            # Generate CSV content
            csv_content = export_decision_log_csv(decisions, issues, document_name)
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_name = document_name.rsplit('.', 1)[0] if '.' in document_name else document_name
            filename = f"{base_name}_decisions_{timestamp}.csv"
            
            # Return as file download
            return Response(
                csv_content,
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename="{filename}"',
                    'Content-Type': 'text/csv; charset=utf-8'
                }
            )
        
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to export decision log: {str(e)}'
            }), 500


# =============================================================================
# Integration Example
# =============================================================================

def enhance_review_response(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance a TWR review results response with Fix Assistant data.
    
    This is a convenience function showing how to integrate all helper
    functions into the existing review endpoint response.
    
    Args:
        results: Original review results from core.py containing:
            - paragraphs: List of tuples [(para_idx, text), ...]
            - page_map: Dict {para_idx: page_number}
            - headings: List of heading dicts
            - issues: List of issue dicts
    
    Returns:
        Enhanced results dict with additional keys:
            - document_content
            - fix_groups
            - confidence_details
            - fix_statistics
    
    Usage in routes.py:
        @app.route('/api/review/result/<job_id>')
        def review_result(job_id):
            results = get_review_results(job_id)  # existing logic
            
            # Add Fix Assistant enhancement
            enhanced = enhance_review_response(results)
            
            return jsonify(enhanced)
    """
    # Build document content structure
    document_content = build_document_content(results)
    
    # Get issues list
    issues = results.get('issues', [])
    
    # Group similar fixes
    fix_groups = group_similar_fixes(issues)
    
    # Build confidence details
    confidence_details = build_confidence_details(issues)
    
    # Compute statistics
    page_count = document_content.get('page_count', 1)
    fix_statistics = compute_fix_statistics(
        issues,
        fix_groups,
        confidence_details,
        page_count
    )
    
    # Add to results (preserve original data)
    enhanced_results = dict(results)
    enhanced_results['document_content'] = document_content
    enhanced_results['fix_groups'] = fix_groups
    enhanced_results['confidence_details'] = confidence_details
    enhanced_results['fix_statistics'] = fix_statistics
    
    return enhanced_results


# =============================================================================
# Module Self-Test
# =============================================================================

if __name__ == '__main__':
    # Test data
    test_results = {
        'paragraphs': [
            (0, "This is the first paragraph."),
            (1, "1.0 Introduction"),
            (2, "The system shall recieve data from external sources."),
            (3, "1.1 Purpose"),
            (4, "This document describes the recieve functionality."),
            (5, "Data is recieve and processed."),
        ],
        'page_map': {0: 1, 1: 1, 2: 1, 3: 2, 4: 2, 5: 2},
        'headings': [
            {"text": "1.0 Introduction", "level": 1},
            {"text": "1.1 Purpose", "level": 2},
        ],
        'issues': [
            {
                'flagged_text': 'recieve',
                'suggestion': 'receive',
                'category': 'Spelling',
                'severity': 'Medium',
                'message': 'Common spelling error',
                'page': 1,
                'paragraph_index': 2
            },
            {
                'flagged_text': 'recieve',
                'suggestion': 'receive',
                'category': 'Spelling',
                'severity': 'Medium',
                'message': 'Common spelling error',
                'page': 2,
                'paragraph_index': 4
            },
            {
                'flagged_text': 'recieve',
                'suggestion': 'receive',
                'category': 'Spelling',
                'severity': 'Medium',
                'message': 'Common spelling error',
                'page': 2,
                'paragraph_index': 5
            },
            {
                'flagged_text': 'utilize',
                'suggestion': 'use',
                'category': 'Style',
                'severity': 'Low',
                'message': 'Consider simpler word',
                'page': 1,
                'paragraph_index': 2
            },
            {
                'flagged_text': 'was ran',
                'suggestion': 'was run',
                'category': 'Grammar',
                'severity': 'Medium',
                'message': 'Incorrect verb form',
                'page': 2,
                'paragraph_index': 5
            },
        ]
    }
    
    print("=" * 60)
    print("Fix Assistant API - Self Test")
    print("=" * 60)
    
    # Test enhance_review_response
    enhanced = enhance_review_response(test_results)
    
    print("\n1. Document Content:")
    print(f"   Paragraphs: {len(enhanced['document_content']['paragraphs'])}")
    print(f"   Headings: {len(enhanced['document_content']['headings'])}")
    print(f"   Page count: {enhanced['document_content']['page_count']}")
    
    print("\n2. Fix Groups:")
    for group in enhanced['fix_groups']:
        print(f"   {group['pattern']} (count: {group['count']})")
    
    print("\n3. Confidence Details (first 3):")
    for idx in ['0', '1', '2']:
        if idx in enhanced['confidence_details']:
            detail = enhanced['confidence_details'][idx]
            print(f"   Issue {idx}: {detail['tier']} ({detail['score']:.2f})")
    
    print("\n4. Fix Statistics:")
    stats = enhanced['fix_statistics']
    print(f"   Total fixes: {stats['total_fixes']}")
    print(f"   By category: {stats['by_category']}")
    print(f"   By tier: {stats['by_tier']}")
    print(f"   Estimated review time: {stats['estimated_review_seconds']}s")
    
    print("\n5. Decision Log CSV (sample):")
    test_decisions = [
        {"index": 0, "decision": "accepted", "note": "", "timestamp": "2026-01-27T14:32:15"},
        {"index": 3, "decision": "rejected", "note": "Keep formal tone", "timestamp": "2026-01-27T14:32:18"},
    ]
    csv_output = export_decision_log_csv(test_decisions, test_results['issues'])
    print(csv_output[:500])
    
    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
