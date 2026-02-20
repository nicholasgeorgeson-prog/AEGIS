"""
Portfolio Routes - API endpoints for the Portfolio tile view
============================================================
v3.0.114 - Initial release

Provides endpoints for:
- Listing all batches with document counts
- Getting batch details with document cards
- Individual document quick-view data
- Recent activity feed
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from flask import Blueprint, jsonify, request

# Set up logging
logger = logging.getLogger('portfolio')

# Create Blueprint
portfolio_blueprint = Blueprint('portfolio', __name__)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_db_path():
    """Get the scan history database path."""
    try:
        from scan_history import get_scan_history_db
        db = get_scan_history_db()
        if hasattr(db, 'db_path'):
            return db.db_path
    except (ImportError, AttributeError):
        pass

    app_dir = Path(__file__).resolve().parent.parent
    return str(app_dir / "scan_history.db")


def _get_db_connection():
    """Get a database connection."""
    db_path = _get_db_path()
    return sqlite3.connect(db_path)


def _format_timestamp(timestamp_str):
    """Format timestamp for display."""
    if not timestamp_str:
        return 'Unknown'
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        diff = now - dt

        if diff.days == 0:
            if diff.seconds < 60:
                return 'Just now'
            elif diff.seconds < 3600:
                mins = diff.seconds // 60
                return f'{mins}m ago'
            else:
                hours = diff.seconds // 3600
                return f'{hours}h ago'
        elif diff.days == 1:
            return 'Yesterday'
        elif diff.days < 7:
            return f'{diff.days}d ago'
        else:
            return dt.strftime('%b %d, %Y')
    except:
        return timestamp_str[:10] if len(timestamp_str) > 10 else timestamp_str


def _get_grade_color(grade):
    """Get color class for grade."""
    grade_colors = {
        'A': 'success',
        'B': 'good',
        'C': 'warning',
        'D': 'caution',
        'F': 'error'
    }
    return grade_colors.get(grade, 'neutral')


# =============================================================================
# API ENDPOINTS
# =============================================================================

@portfolio_blueprint.route('/batches', methods=['GET'])
def get_batches():
    """
    Get all batch sessions with summary data.

    Batches are grouped by scan sessions (scans within 5 minutes of each other
    with multiple documents).

    Returns:
        {
            success: true,
            batches: [
                {
                    id: "batch_20260131_073400",
                    name: "Batch Upload",
                    timestamp: "2026-01-31T07:34:00",
                    formatted_time: "2h ago",
                    document_count: 5,
                    total_issues: 23,
                    avg_score: 87,
                    grades: {A: 2, B: 2, C: 1},
                    documents: [...] // Preview of first 4 docs
                }
            ],
            singles: [...] // Individual non-batch scans
        }
    """
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()

        # Get all scans with document info, ordered by time
        cursor.execute('''
            SELECT
                s.id, s.document_id, s.scan_time, s.score, s.grade,
                s.issue_count, s.word_count, s.results_json,
                d.filename, d.scan_count
            FROM scans s
            JOIN documents d ON s.document_id = d.id
            ORDER BY s.scan_time DESC
            LIMIT 200
        ''')

        scans = cursor.fetchall()
        conn.close()

        if not scans:
            return jsonify({
                'success': True,
                'batches': [],
                'singles': [],
                'stats': {'total_documents': 0, 'total_batches': 0}
            })

        # BUG-M15 FIX: Reduced from 5 minutes to 30 seconds for batch detection
        # This prevents individual scans done minutes apart from being grouped as batches
        # A true batch upload typically processes multiple files within seconds
        BATCH_TIME_WINDOW_SECONDS = 30

        batches = []
        singles = []
        current_batch = []
        batch_start_time = None

        for scan in scans:
            scan_id, doc_id, scan_time, score, grade, issue_count, word_count, results_json, filename, scan_count = scan

            scan_dt = datetime.fromisoformat(scan_time.replace('Z', '+00:00')) if scan_time else datetime.now()

            # Parse results for additional info
            try:
                results = json.loads(results_json) if results_json else {}
            except:
                results = {}

            doc_data = {
                'id': scan_id,
                'document_id': doc_id,
                'filename': filename,
                'scan_time': scan_time,
                'formatted_time': _format_timestamp(scan_time),
                'score': score or 0,
                'grade': grade or 'N/A',
                'grade_color': _get_grade_color(grade),
                'issue_count': issue_count or 0,
                'word_count': word_count or 0,
                'scan_count': scan_count or 1,
                'categories': list(results.get('by_category', {}).keys())[:3]
            }

            if batch_start_time is None:
                batch_start_time = scan_dt
                current_batch = [doc_data]
            elif abs((batch_start_time - scan_dt).total_seconds()) <= BATCH_TIME_WINDOW_SECONDS:
                current_batch.append(doc_data)
            else:
                # Save current batch
                if len(current_batch) >= 2:
                    batches.append(_create_batch_summary(current_batch))
                else:
                    singles.extend(current_batch)

                # Start new batch
                batch_start_time = scan_dt
                current_batch = [doc_data]

        # Don't forget the last batch
        if current_batch:
            if len(current_batch) >= 2:
                batches.append(_create_batch_summary(current_batch))
            else:
                singles.extend(current_batch)

        return jsonify({
            'success': True,
            'batches': batches,
            'singles': singles[:20],  # Limit singles
            'stats': {
                'total_documents': len(scans),
                'total_batches': len(batches),
                'total_singles': len(singles)
            }
        })

    except Exception as e:
        logger.error(f"Error getting batches: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _create_batch_summary(documents):
    """Create a batch summary from a list of documents."""
    if not documents:
        return None

    # Calculate aggregates
    total_issues = sum(d['issue_count'] for d in documents)
    total_score = sum(d['score'] for d in documents)
    avg_score = round(total_score / len(documents)) if documents else 0

    # Count grades
    grades = {}
    for d in documents:
        g = d['grade']
        grades[g] = grades.get(g, 0) + 1

    # Get dominant grade
    dominant_grade = max(grades.keys(), key=lambda k: grades[k]) if grades else 'N/A'

    # Create batch ID from first scan time
    # Handle both "2026-01-31T12:34:18" and "2026-01-31 12:34:18" formats
    first_time = documents[0]['scan_time']
    batch_id = f"batch_{first_time[:19].replace('-', '').replace(':', '').replace('T', '_').replace(' ', '_')}"

    return {
        'id': batch_id,
        'name': f"Batch ({len(documents)} docs)",
        'timestamp': first_time,
        'formatted_time': _format_timestamp(first_time),
        'document_count': len(documents),
        'total_issues': total_issues,
        'avg_score': avg_score,
        'dominant_grade': dominant_grade,
        'grade_color': _get_grade_color(dominant_grade),
        'grades': grades,
        'documents': documents[:6],  # Preview first 6
        'all_document_ids': [d['id'] for d in documents]
    }


@portfolio_blueprint.route('/batch/<batch_id>', methods=['GET'])
def get_batch_details(batch_id):
    """
    Get full details for a specific batch.

    Returns all documents in the batch with full metadata.
    """
    try:
        # Parse batch ID to get timestamp
        # Format: batch_YYYYMMDD_HHMMSS
        parts = batch_id.replace('batch_', '').split('_')
        if len(parts) >= 2:
            date_str = parts[0]
            time_str = parts[1]
            # Reconstruct timestamp
            timestamp = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}T{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
        else:
            return jsonify({'success': False, 'error': 'Invalid batch ID'}), 400

        conn = _get_db_connection()
        cursor = conn.cursor()

        # v5.9.39: Use 30-second window to match batch detection in list view
        # (was ±5 minutes which pulled in scans from different batches)
        cursor.execute('''
            SELECT
                s.id, s.document_id, s.scan_time, s.score, s.grade,
                s.issue_count, s.word_count, s.results_json,
                d.filename, d.filepath, d.scan_count
            FROM scans s
            JOIN documents d ON s.document_id = d.id
            WHERE datetime(s.scan_time) BETWEEN datetime(?, '-30 seconds') AND datetime(?, '+30 seconds')
            ORDER BY s.scan_time DESC
        ''', (timestamp, timestamp))

        scans = cursor.fetchall()
        conn.close()

        documents = []
        for scan in scans:
            scan_id, doc_id, scan_time, score, grade, issue_count, word_count, results_json, filename, filepath, scan_count = scan

            try:
                results = json.loads(results_json) if results_json else {}
            except:
                results = {}

            documents.append({
                'id': scan_id,
                'document_id': doc_id,
                'filename': filename,
                'filepath': filepath,
                'scan_time': scan_time,
                'formatted_time': _format_timestamp(scan_time),
                'score': score or 0,
                'grade': grade or 'N/A',
                'grade_color': _get_grade_color(grade),
                'issue_count': issue_count or 0,
                'word_count': word_count or 0,
                'scan_count': scan_count or 1,
                'by_severity': results.get('by_severity', {}),
                'by_category': results.get('by_category', {}),
                'top_issues': results.get('issues', [])[:3]
            })

        if not documents:
            return jsonify({'success': False, 'error': 'Batch not found'}), 404

        return jsonify({
            'success': True,
            'batch': _create_batch_summary(documents),
            'documents': documents
        })

    except Exception as e:
        logger.error(f"Error getting batch details: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@portfolio_blueprint.route('/document/<int:scan_id>/preview', methods=['GET'])
def get_document_preview(scan_id):
    """
    Get quick preview data for a document tile.

    Returns summary data for hovering/quick view.
    """
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                s.id, s.document_id, s.scan_time, s.score, s.grade,
                s.issue_count, s.word_count, s.results_json,
                d.filename, d.filepath
            FROM scans s
            JOIN documents d ON s.document_id = d.id
            WHERE s.id = ?
        ''', (scan_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({'success': False, 'error': 'Document not found'}), 404

        scan_id, doc_id, scan_time, score, grade, issue_count, word_count, results_json, filename, filepath = row

        try:
            results = json.loads(results_json) if results_json else {}
        except:
            results = {}

        # Get top issues for preview
        issues = results.get('issues', [])
        top_issues = []
        for issue in issues[:5]:
            top_issues.append({
                'category': issue.get('category', 'Unknown'),
                'severity': issue.get('severity', 'Low'),
                'message': issue.get('message', '')[:100]
            })

        return jsonify({
            'success': True,
            'preview': {
                'id': scan_id,
                'filename': filename,
                'filepath': filepath,
                'score': score or 0,
                'grade': grade or 'N/A',
                'grade_color': _get_grade_color(grade),
                'issue_count': issue_count or 0,
                'word_count': word_count or 0,
                'by_severity': results.get('by_severity', {}),
                'by_category': results.get('by_category', {}),
                'top_issues': top_issues,
                'full_text_preview': (results.get('full_text', '') or '')[:200] + '...'
            }
        })

    except Exception as e:
        logger.error(f"Error getting document preview: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@portfolio_blueprint.route('/recent', methods=['GET'])
def get_recent_activity():
    """
    Get recent scan activity for the activity feed.
    """
    try:
        limit = request.args.get('limit', 10, type=int)

        conn = _get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                s.id, s.scan_time, s.score, s.grade, s.issue_count,
                d.filename
            FROM scans s
            JOIN documents d ON s.document_id = d.id
            ORDER BY s.scan_time DESC
            LIMIT ?
        ''', (limit,))

        scans = cursor.fetchall()
        conn.close()

        activity = []
        for scan in scans:
            scan_id, scan_time, score, grade, issue_count, filename = scan
            activity.append({
                'id': scan_id,
                'filename': filename,
                'scan_time': scan_time,
                'formatted_time': _format_timestamp(scan_time),
                'score': score or 0,
                'grade': grade or 'N/A',
                'grade_color': _get_grade_color(grade),
                'issue_count': issue_count or 0
            })

        return jsonify({
            'success': True,
            'activity': activity
        })

    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@portfolio_blueprint.route('/stats', methods=['GET'])
def get_portfolio_stats():
    """
    Get overall portfolio statistics.
    """
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()

        # Total documents
        cursor.execute('SELECT COUNT(*) FROM documents')
        total_docs = cursor.fetchone()[0]

        # Total scans
        cursor.execute('SELECT COUNT(*) FROM scans')
        total_scans = cursor.fetchone()[0]

        # Average score
        cursor.execute('SELECT AVG(score) FROM scans WHERE score IS NOT NULL')
        avg_score = cursor.fetchone()[0] or 0

        # Grade distribution
        cursor.execute('''
            SELECT grade, COUNT(*)
            FROM scans
            WHERE grade IS NOT NULL
            GROUP BY grade
        ''')
        grade_dist = dict(cursor.fetchall())

        # Recent trend (last 7 days vs previous 7 days)
        cursor.execute('''
            SELECT AVG(score) FROM scans
            WHERE scan_time >= datetime('now', '-7 days')
        ''')
        recent_avg = cursor.fetchone()[0] or 0

        cursor.execute('''
            SELECT AVG(score) FROM scans
            WHERE scan_time >= datetime('now', '-14 days')
            AND scan_time < datetime('now', '-7 days')
        ''')
        prev_avg = cursor.fetchone()[0] or 0

        trend = 'up' if recent_avg > prev_avg else ('down' if recent_avg < prev_avg else 'stable')

        conn.close()

        return jsonify({
            'success': True,
            'stats': {
                'total_documents': total_docs,
                'total_scans': total_scans,
                'avg_score': round(avg_score, 1),
                'grade_distribution': grade_dist,
                'trend': trend,
                'trend_value': round(recent_avg - prev_avg, 1)
            }
        })

    except Exception as e:
        logger.error(f"Error getting portfolio stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
