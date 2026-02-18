"""
AEGIS Review Report - PDF Generation
v5.9.4: Generates professional PDF review reports with AEGIS branding.

Features:
- Cover page with document info and score
- Executive summary with severity breakdown
- Issue detail pages grouped by category
- Checker coverage table
- AEGIS gold/bronze branding throughout
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict, Counter
import io
import logging

logger = logging.getLogger(__name__)

# AEGIS brand colors
AEGIS_GOLD = '#D6A84A'
AEGIS_BRONZE = '#B8743A'
AEGIS_DARK = '#1a1a2e'
AEGIS_LIGHT_BG = '#f8f9fa'

SEVERITY_COLORS = {
    'Critical': '#ef4444',
    'High': '#ea580c',
    'Medium': '#ca8a04',
    'Low': '#16a34a',
    'Info': '#3b82f6'
}

SEVERITY_ORDER = ['Critical', 'High', 'Medium', 'Low', 'Info']

GRADE_COLORS = {
    'A+': '#059669', 'A': '#10b981', 'A-': '#34d399',
    'B+': '#84cc16', 'B': '#a3e635', 'B-': '#bef264',
    'C+': '#eab308', 'C': '#facc15', 'C-': '#fde047',
    'D+': '#f97316', 'D': '#fb923c', 'D-': '#fdba74',
    'F': '#ef4444'
}


def _sanitize(text):
    """Sanitize text for ReportLab XML paragraph parser."""
    if not text or not isinstance(text, str):
        return text or ''
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def _truncate(text, max_len=120):
    """Truncate text to max length with ellipsis."""
    if not text:
        return ''
    text = str(text)
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + '...'


class ReviewReportGenerator:
    """Generate professional PDF review reports for AEGIS document scans."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Create custom paragraph styles for the report."""
        # Cover page styles
        self.styles.add(ParagraphStyle(
            name='CoverTitle', parent=self.styles['Heading1'],
            fontSize=28, alignment=TA_CENTER, spaceAfter=4,
            textColor=colors.HexColor(AEGIS_BRONZE),
            fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='CoverSubtitle', parent=self.styles['Normal'],
            fontSize=14, alignment=TA_CENTER, spaceAfter=8,
            textColor=colors.HexColor(AEGIS_GOLD),
            fontName='Helvetica'
        ))
        self.styles.add(ParagraphStyle(
            name='CoverMeta', parent=self.styles['Normal'],
            fontSize=10, alignment=TA_CENTER, spaceAfter=4,
            textColor=colors.HexColor('#64748b')
        ))
        # Section headers
        self.styles.add(ParagraphStyle(
            name='SectionTitle', parent=self.styles['Heading2'],
            fontSize=14, spaceBefore=16, spaceAfter=8,
            textColor=colors.HexColor(AEGIS_DARK),
            fontName='Helvetica-Bold',
            borderWidth=0, borderColor=colors.HexColor(AEGIS_GOLD),
            borderPadding=0
        ))
        self.styles.add(ParagraphStyle(
            name='SubSection', parent=self.styles['Heading3'],
            fontSize=11, spaceBefore=10, spaceAfter=4,
            textColor=colors.HexColor('#374151'),
            fontName='Helvetica-Bold'
        ))
        # Content styles — override existing BodyText (already in getSampleStyleSheet)
        self.styles['BodyText'].fontSize = 9
        self.styles['BodyText'].textColor = colors.HexColor('#374151')
        self.styles['BodyText'].leading = 12
        self.styles['BodyText'].spaceAfter = 4
        self.styles.add(ParagraphStyle(
            name='CellText', parent=self.styles['Normal'],
            fontSize=8, textColor=colors.HexColor('#374151'),
            leading=10
        ))
        self.styles.add(ParagraphStyle(
            name='CellBold', parent=self.styles['Normal'],
            fontSize=8, textColor=colors.HexColor('#1f2937'),
            fontName='Helvetica-Bold', leading=10
        ))
        self.styles.add(ParagraphStyle(
            name='CellSmall', parent=self.styles['Normal'],
            fontSize=7, textColor=colors.HexColor('#6b7280'),
            leading=9
        ))
        self.styles.add(ParagraphStyle(
            name='FlaggedText', parent=self.styles['Normal'],
            fontSize=8, textColor=colors.HexColor('#991b1b'),
            fontName='Courier', leading=10,
            backColor=colors.HexColor('#fef2f2')
        ))
        self.styles.add(ParagraphStyle(
            name='SuggestionText', parent=self.styles['Normal'],
            fontSize=8, textColor=colors.HexColor('#065f46'),
            fontName='Courier', leading=10,
            backColor=colors.HexColor('#f0fdf4')
        ))
        self.styles.add(ParagraphStyle(
            name='Footer', parent=self.styles['Normal'],
            fontSize=7, alignment=TA_CENTER,
            textColor=colors.HexColor('#9ca3af')
        ))

    def generate(self, issues: List[Dict], document_info: Dict = None,
                 score: float = None, grade: str = None,
                 reviewer_name: str = 'AEGIS',
                 filters_applied: Dict = None,
                 metadata: Dict = None) -> bytes:
        """
        Generate PDF bytes for the review report.

        Args:
            issues: List of issue dicts with severity, category, message, flagged_text, suggestion
            document_info: Dict with filename, word_count, paragraph_count, etc.
            score: Quality score (0-100)
            grade: Letter grade
            reviewer_name: Name of reviewer
            filters_applied: Dict describing any filters used (categories, severities, checkers)
            metadata: Optional dict with version, export_date
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=0.6 * inch,
            bottomMargin=0.6 * inch,
            leftMargin=0.7 * inch,
            rightMargin=0.7 * inch
        )

        story = []
        doc_info = document_info or {}
        meta = metadata or {}

        # Cover page
        story.extend(self._build_cover_page(doc_info, score, grade,
                                             reviewer_name, len(issues), meta))

        # Filter notice (if filters were applied)
        if filters_applied:
            story.extend(self._build_filter_notice(filters_applied))

        # Executive summary
        story.extend(self._build_executive_summary(issues, score, doc_info))

        # Severity breakdown table
        story.extend(self._build_severity_breakdown(issues))

        # Category breakdown table
        story.extend(self._build_category_breakdown(issues))

        # Issue details by category
        story.append(PageBreak())
        story.extend(self._build_issue_details(issues))

        # Footer
        story.extend(self._build_footer(meta, reviewer_name))

        try:
            doc.build(story)
        except Exception as e:
            logger.error(f"PDF build failed: {e}")
            raise

        buffer.seek(0)
        return buffer.getvalue()

    def _build_cover_page(self, doc_info, score, grade, reviewer_name,
                           issue_count, metadata) -> list:
        """Build the cover page."""
        story = []

        # Top spacer
        story.append(Spacer(1, 60))

        # AEGIS branding line
        story.append(HRFlowable(
            width="40%", thickness=2, lineCap='round',
            color=colors.HexColor(AEGIS_GOLD), spaceAfter=12
        ))

        # Title
        story.append(Paragraph('AEGIS', self.styles['CoverTitle']))
        story.append(Paragraph(
            'Document Review Report',
            self.styles['CoverSubtitle']
        ))

        story.append(HRFlowable(
            width="40%", thickness=2, lineCap='round',
            color=colors.HexColor(AEGIS_GOLD), spaceBefore=12, spaceAfter=24
        ))

        # Document info card
        filename = doc_info.get('filename', doc_info.get('name', 'Unknown Document'))
        story.append(Paragraph(
            f'<b>{_sanitize(filename)}</b>',
            ParagraphStyle('DocName', parent=self.styles['Normal'],
                          fontSize=14, alignment=TA_CENTER, spaceAfter=6,
                          textColor=colors.HexColor(AEGIS_DARK))
        ))

        # Metadata line
        date_str = metadata.get('export_date', datetime.now().strftime('%B %d, %Y'))
        story.append(Paragraph(
            f'{date_str} &bull; Reviewed by {_sanitize(reviewer_name)}',
            self.styles['CoverMeta']
        ))

        story.append(Spacer(1, 30))

        # Score card
        score_val = f"{score:.0f}%" if score is not None else 'N/A'
        grade_val = grade or 'N/A'
        grade_color = GRADE_COLORS.get(grade_val, '#6b7280')
        word_count = doc_info.get('word_count', 'N/A')
        if isinstance(word_count, (int, float)):
            word_count = f"{int(word_count):,}"

        score_data = [
            ['Quality Score', 'Grade', 'Issues Found', 'Word Count'],
            [score_val, grade_val, str(issue_count), str(word_count)]
        ]

        score_table = Table(score_data, colWidths=[1.65 * inch] * 4)
        score_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(AEGIS_DARK)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            # Values row
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor(AEGIS_LIGHT_BG)),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 18),
            ('TOPPADDING', (0, 1), (-1, 1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 10),
            # Grade color
            ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor(grade_color)),
            # Border
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(AEGIS_GOLD)),
        ]))
        story.append(score_table)

        story.append(Spacer(1, 40))

        # Version info
        version = metadata.get('version', 'AEGIS')
        story.append(Paragraph(
            f'Generated by {_sanitize(version)} &bull; Aerospace Engineering Governance &amp; Inspection System',
            self.styles['CoverMeta']
        ))

        story.append(PageBreak())
        return story

    def _build_filter_notice(self, filters_applied) -> list:
        """Build a notice showing what filters were applied."""
        story = []
        parts = []

        if filters_applied.get('severities'):
            parts.append(f"Severities: {', '.join(filters_applied['severities'])}")
        if filters_applied.get('categories'):
            parts.append(f"Categories: {', '.join(filters_applied['categories'][:5])}")
            if len(filters_applied.get('categories', [])) > 5:
                parts[-1] += f" (+{len(filters_applied['categories']) - 5} more)"
        if filters_applied.get('checkers'):
            parts.append(f"Checkers: {', '.join(filters_applied['checkers'][:5])}")

        if parts:
            notice_text = 'Filtered Report: ' + ' | '.join(parts)
            story.append(Paragraph(
                f'<i>{_sanitize(notice_text)}</i>',
                ParagraphStyle('FilterNotice', parent=self.styles['Normal'],
                              fontSize=8, textColor=colors.HexColor('#92400e'),
                              backColor=colors.HexColor('#fffbeb'),
                              borderWidth=1, borderColor=colors.HexColor('#fbbf24'),
                              borderPadding=6, spaceBefore=8, spaceAfter=12)
            ))

        return story

    def _build_executive_summary(self, issues, score, doc_info) -> list:
        """Build the executive summary section."""
        story = []

        story.append(Paragraph('Executive Summary', self.styles['SectionTitle']))
        story.append(HRFlowable(
            width="100%", thickness=1, color=colors.HexColor(AEGIS_GOLD),
            spaceAfter=10
        ))

        # Summary paragraph
        total = len(issues)
        severity_counts = Counter(
            (i.get('severity', 'Info') for i in issues)
        )
        critical = severity_counts.get('Critical', 0)
        high = severity_counts.get('High', 0)

        score_desc = ''
        if score is not None:
            if score >= 90:
                score_desc = 'The document demonstrates excellent quality'
            elif score >= 80:
                score_desc = 'The document shows good quality with minor issues'
            elif score >= 70:
                score_desc = 'The document requires attention in several areas'
            elif score >= 60:
                score_desc = 'The document has significant quality concerns'
            else:
                score_desc = 'The document requires substantial revision'

        summary_parts = []
        if score_desc:
            summary_parts.append(f'{score_desc} with a score of {score:.0f}%.')
        summary_parts.append(
            f'A total of {total} issue{"s" if total != 1 else ""} '
            f'{"were" if total != 1 else "was"} identified across the document.'
        )
        if critical > 0 or high > 0:
            urgent_parts = []
            if critical > 0:
                urgent_parts.append(f'{critical} critical')
            if high > 0:
                urgent_parts.append(f'{high} high-severity')
            summary_parts.append(
                f'Of these, {" and ".join(urgent_parts)} '
                f'issue{"s" if critical + high != 1 else ""} require immediate attention.'
            )

        story.append(Paragraph(
            ' '.join(summary_parts),
            self.styles['BodyText']
        ))
        story.append(Spacer(1, 12))

        return story

    def _build_severity_breakdown(self, issues) -> list:
        """Build severity breakdown table."""
        story = []

        story.append(Paragraph('Severity Distribution', self.styles['SubSection']))

        severity_counts = Counter(
            (i.get('severity', 'Info') for i in issues)
        )
        total = len(issues)

        header = ['Severity', 'Count', 'Percentage', 'Bar']
        rows = [header]

        for sev in SEVERITY_ORDER:
            count = severity_counts.get(sev, 0)
            pct = (count / total * 100) if total > 0 else 0
            bar = '#' * int(pct / 2.5) if pct > 0 else ''
            rows.append([sev, str(count), f'{pct:.1f}%', bar])

        rows.append(['TOTAL', str(total), '100%', ''])

        table = Table(rows, colWidths=[1.2 * inch, 0.8 * inch, 1.0 * inch, 3.5 * inch])

        style_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(AEGIS_DARK)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (2, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            # Total row
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f1f5f9')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.HexColor(AEGIS_DARK)),
        ]

        # Color-code severity rows
        for i, sev in enumerate(SEVERITY_ORDER):
            row_idx = i + 1
            sev_color = SEVERITY_COLORS.get(sev, '#6b7280')
            style_cmds.append(
                ('TEXTCOLOR', (0, row_idx), (0, row_idx), colors.HexColor(sev_color))
            )
            style_cmds.append(
                ('FONTNAME', (0, row_idx), (0, row_idx), 'Helvetica-Bold')
            )
            # Bar color
            style_cmds.append(
                ('TEXTCOLOR', (3, row_idx), (3, row_idx), colors.HexColor(sev_color))
            )
            # Alternating row backgrounds
            if row_idx % 2 == 0:
                style_cmds.append(
                    ('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor('#fafafa'))
                )

        table.setStyle(TableStyle(style_cmds))
        story.append(table)
        story.append(Spacer(1, 16))

        return story

    def _build_category_breakdown(self, issues) -> list:
        """Build category breakdown table."""
        story = []

        story.append(Paragraph('Category Distribution', self.styles['SubSection']))

        category_counts = Counter(
            (i.get('category', 'Uncategorized') for i in issues)
        )

        # Sort by count descending
        sorted_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        total = len(issues)

        header = ['Category', 'Count', '%', 'Top Severity']
        rows = [header]

        for cat, count in sorted_cats[:15]:  # Top 15 categories
            pct = (count / total * 100) if total > 0 else 0
            # Find the highest severity for this category
            cat_issues = [i for i in issues if i.get('category') == cat]
            top_sev = 'Info'
            for sev in SEVERITY_ORDER:
                if any(i.get('severity') == sev for i in cat_issues):
                    top_sev = sev
                    break
            rows.append([cat, str(count), f'{pct:.0f}%', top_sev])

        if len(sorted_cats) > 15:
            remaining = sum(c for _, c in sorted_cats[15:])
            rows.append([f'({len(sorted_cats) - 15} more categories)',
                        str(remaining), '', ''])

        table = Table(rows, colWidths=[2.8 * inch, 0.7 * inch, 0.6 * inch, 2.4 * inch])

        style_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(AEGIS_DARK)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (2, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.HexColor('#fafafa')]),
        ]

        # Color the top severity column
        for i in range(1, len(rows)):
            sev = rows[i][3] if i < len(rows) else ''
            if sev in SEVERITY_COLORS:
                style_cmds.append(
                    ('TEXTCOLOR', (3, i), (3, i), colors.HexColor(SEVERITY_COLORS[sev]))
                )
                style_cmds.append(
                    ('FONTNAME', (3, i), (3, i), 'Helvetica-Bold')
                )

        table.setStyle(TableStyle(style_cmds))
        story.append(table)
        story.append(Spacer(1, 16))

        return story

    def _build_issue_details(self, issues) -> list:
        """Build detailed issue listings grouped by category."""
        story = []

        story.append(Paragraph('Issue Details', self.styles['SectionTitle']))
        story.append(HRFlowable(
            width="100%", thickness=1, color=colors.HexColor(AEGIS_GOLD),
            spaceAfter=12
        ))

        # Group by category
        by_category = defaultdict(list)
        for issue in issues:
            cat = issue.get('category', 'Uncategorized')
            by_category[cat].append(issue)

        # Sort categories by total issues descending
        sorted_categories = sorted(by_category.items(),
                                    key=lambda x: len(x[1]), reverse=True)

        for cat_idx, (category, cat_issues) in enumerate(sorted_categories):
            # Category header
            story.append(Paragraph(
                f'{_sanitize(category)} ({len(cat_issues)} issue{"s" if len(cat_issues) != 1 else ""})',
                self.styles['SubSection']
            ))

            # Build issues table for this category
            header = ['#', 'Sev', 'Message', 'Flagged Text', 'Suggestion']
            rows = [header]

            for i, issue in enumerate(cat_issues):
                sev = issue.get('severity', 'Info')
                msg = _truncate(_sanitize(issue.get('message', '')), 80)
                flagged = _truncate(_sanitize(issue.get('flagged_text', '')), 60)
                suggestion = _truncate(_sanitize(issue.get('suggestion', '')), 60)

                rows.append([
                    str(i + 1),
                    sev[:4],  # Abbreviated
                    Paragraph(msg, self.styles['CellText']),
                    Paragraph(flagged, self.styles['CellSmall']),
                    Paragraph(suggestion, self.styles['CellSmall'])
                ])

            col_widths = [0.3 * inch, 0.4 * inch, 2.6 * inch, 1.8 * inch, 1.6 * inch]
            table = Table(rows, colWidths=col_widths, repeatRows=1)

            style_cmds = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(AEGIS_DARK)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 7),
                ('FONTSIZE', (0, 1), (1, -1), 7),
                ('ALIGN', (0, 0), (1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                 [colors.white, colors.HexColor('#fafafa')]),
            ]

            # Color-code severity abbreviations
            for row_idx in range(1, len(rows)):
                sev_text = rows[row_idx][1]
                for sev_name, sev_color in SEVERITY_COLORS.items():
                    if sev_name.startswith(sev_text):
                        style_cmds.append(
                            ('TEXTCOLOR', (1, row_idx), (1, row_idx),
                             colors.HexColor(sev_color))
                        )
                        style_cmds.append(
                            ('FONTNAME', (1, row_idx), (1, row_idx), 'Helvetica-Bold')
                        )
                        break

            table.setStyle(TableStyle(style_cmds))
            story.append(table)
            story.append(Spacer(1, 12))

        return story

    def _build_footer(self, metadata, reviewer_name) -> list:
        """Build report footer."""
        story = []

        story.append(Spacer(1, 20))
        story.append(HRFlowable(
            width="100%", thickness=0.5, color=colors.HexColor('#d1d5db'),
            spaceAfter=8
        ))

        version = metadata.get('version', 'AEGIS')
        story.append(Paragraph(
            f'Report generated by {_sanitize(version)} on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} '
            f'&bull; Reviewer: {_sanitize(reviewer_name)} '
            f'&bull; Aerospace Engineering Governance &amp; Inspection System',
            self.styles['Footer']
        ))

        return story


def generate_review_report(issues: List[Dict],
                           document_info: Dict = None,
                           score: float = None,
                           grade: str = None,
                           reviewer_name: str = 'AEGIS',
                           filters_applied: Dict = None,
                           metadata: Dict = None) -> bytes:
    """
    Convenience function to generate a review report PDF.

    Returns PDF content as bytes.
    """
    generator = ReviewReportGenerator()
    return generator.generate(
        issues=issues,
        document_info=document_info,
        score=score,
        grade=grade,
        reviewer_name=reviewer_name,
        filters_applied=filters_applied,
        metadata=metadata
    )
