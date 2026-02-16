"""
AEGIS Adjudication Report - PDF Generation
v4.0.4: Generates formatted PDF reports of adjudication state.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from datetime import datetime
from typing import Dict, List, Optional
import io


# AEGIS brand colors
AEGIS_GOLD = '#D6A84A'
AEGIS_BRONZE = '#B8743A'

STATUS_COLORS = {
    'deliverable': '#D6A84A',
    'confirmed': '#10b981',
    'rejected': '#ef4444',
    'pending': '#6b7280'
}

STATUS_LABELS = {
    'deliverable': 'Deliverable',
    'confirmed': 'Confirmed',
    'rejected': 'Rejected',
    'pending': 'Pending'
}


class AdjudicationReportGenerator:
    """Generate PDF adjudication reports for AEGIS."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Create custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='ReportTitle', parent=self.styles['Heading1'],
            fontSize=18, alignment=TA_CENTER, spaceAfter=4,
            textColor=colors.HexColor(AEGIS_BRONZE)
        ))
        self.styles.add(ParagraphStyle(
            name='ReportSubtitle', parent=self.styles['Normal'],
            fontSize=10, alignment=TA_CENTER, spaceAfter=16,
            textColor=colors.HexColor('#64748b')
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader', parent=self.styles['Heading2'],
            fontSize=12, spaceBefore=16, spaceAfter=6,
            textColor=colors.HexColor('#1e293b'), fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='StatusHeader', parent=self.styles['Heading3'],
            fontSize=11, spaceBefore=12, spaceAfter=4,
            fontName='Helvetica-Bold'
        ))
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
            name='Footer', parent=self.styles['Normal'],
            fontSize=7, alignment=TA_CENTER,
            textColor=colors.HexColor('#9ca3af')
        ))

    def generate(self, roles: List[Dict], summary: Dict,
                 function_categories: Optional[List[Dict]] = None,
                 metadata: Optional[Dict] = None) -> bytes:
        """
        Generate PDF bytes for the adjudication report.

        Args:
            roles: List of role dicts with role_name, status, category, etc.
            summary: Dict with counts per status
            function_categories: Optional list of function category dicts
            metadata: Optional dict with version, export_date, hostname
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
        meta = metadata or {}

        # Header
        story.extend(self._build_header(meta))

        # Summary statistics
        story.extend(self._build_summary(summary, len(roles)))

        # Roles grouped by status
        for status in ['deliverable', 'confirmed', 'rejected', 'pending']:
            filtered = [r for r in roles if r.get('status') == status]
            if filtered:
                story.extend(self._build_status_section(status, filtered,
                                                        function_categories))

        # Function tag distribution
        if function_categories:
            story.extend(self._build_tag_summary(roles, function_categories))

        # Footer
        story.extend(self._build_footer(meta))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def _build_header(self, metadata: Dict) -> list:
        """Build report header section."""
        story = []

        # Gold rule
        story.append(HRFlowable(
            width="100%", thickness=2,
            color=colors.HexColor(AEGIS_GOLD),
            spaceAfter=8
        ))

        story.append(Paragraph("AEGIS Adjudication Report", self.styles['ReportTitle']))

        version = metadata.get('version', '')
        hostname = metadata.get('hostname', '')
        export_date = metadata.get('export_date', '')
        if export_date:
            try:
                dt = datetime.fromisoformat(export_date.replace('Z', '+00:00'))
                date_str = dt.strftime('%B %d, %Y at %H:%M UTC')
            except Exception:
                date_str = export_date[:19]
        else:
            date_str = datetime.now().strftime('%B %d, %Y')

        subtitle_parts = []
        if version:
            subtitle_parts.append(f"AEGIS v{version}")
        if hostname:
            subtitle_parts.append(hostname)
        subtitle_parts.append(date_str)

        story.append(Paragraph(' &bull; '.join(subtitle_parts), self.styles['ReportSubtitle']))

        story.append(HRFlowable(
            width="100%", thickness=1,
            color=colors.HexColor('#e5e7eb'),
            spaceAfter=12
        ))

        return story

    def _build_summary(self, summary: Dict, total: int) -> list:
        """Build summary statistics table."""
        story = []
        story.append(Paragraph("Summary", self.styles['SectionHeader']))

        data = [
            ['Total Roles', 'Deliverable', 'Confirmed', 'Rejected', 'Pending'],
            [
                str(total),
                str(summary.get('deliverable', 0)),
                str(summary.get('confirmed', 0)),
                str(summary.get('rejected', 0)),
                str(summary.get('pending', 0))
            ]
        ]

        col_width = (letter[0] - 1.4 * inch) / 5
        table = Table(data, colWidths=[col_width] * 5)

        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, 1), 14),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#6b7280')),
            ('TEXTCOLOR', (0, 1), (0, 1), colors.HexColor('#1f2937')),
            ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor(STATUS_COLORS['deliverable'])),
            ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor(STATUS_COLORS['confirmed'])),
            ('TEXTCOLOR', (3, 1), (3, 1), colors.HexColor(STATUS_COLORS['rejected'])),
            ('TEXTCOLOR', (4, 1), (4, 1), colors.HexColor(STATUS_COLORS['pending'])),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 1), (-1, 1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 10),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor('#e5e7eb')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fafafa')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ]))

        story.append(table)
        story.append(Spacer(1, 8))
        return story

    def _build_status_section(self, status: str, roles: List[Dict],
                               function_categories: Optional[List[Dict]] = None) -> list:
        """Build a section for roles of a given status."""
        story = []

        label = STATUS_LABELS.get(status, status.title())
        color = STATUS_COLORS.get(status, '#6b7280')

        # Section header with status dot
        header_style = ParagraphStyle(
            'StatusHeader_' + status,
            parent=self.styles['StatusHeader'],
            textColor=colors.HexColor(color)
        )
        story.append(Paragraph(
            f"{label} ({len(roles)})",
            header_style
        ))

        # Build function category lookup for tag names
        cat_lookup = {}
        if function_categories:
            for cat in function_categories:
                cat_lookup[cat.get('code', '')] = cat.get('name', cat.get('code', ''))

        # Table data
        header = ['Role Name', 'Category', 'Function Tags', 'Notes']
        data = [header]

        for role in sorted(roles, key=lambda r: r.get('role_name', '').lower()):
            name = role.get('role_name', '')
            category = role.get('category', 'Role')
            tags = role.get('function_tags', [])
            tag_names = [cat_lookup.get(t, t) for t in tags] if tags else []
            notes = role.get('notes', '') or ''

            # Truncate long notes for table display
            if len(notes) > 80:
                notes = notes[:77] + '...'

            data.append([
                Paragraph(name, self.styles['CellBold']),
                Paragraph(category, self.styles['CellText']),
                Paragraph(', '.join(tag_names) if tag_names else '-', self.styles['CellText']),
                Paragraph(notes if notes else '-', self.styles['CellText'])
            ])

        available_width = letter[0] - 1.4 * inch
        col_widths = [
            available_width * 0.30,
            available_width * 0.15,
            available_width * 0.25,
            available_width * 0.30
        ]
        table = Table(data, colWidths=col_widths, repeatRows=1)

        status_bg = colors.HexColor(color)
        status_bg_light = colors.Color(
            status_bg.red, status_bg.green, status_bg.blue, alpha=0.08
        )

        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(color)),
            ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('LINEBELOW', (0, 0), (-1, -2), 0.25, colors.HexColor('#e5e7eb')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ]))

        story.append(table)
        story.append(Spacer(1, 8))
        return story

    def _build_tag_summary(self, roles: List[Dict],
                            function_categories: List[Dict]) -> list:
        """Build function tag distribution summary."""
        # Count tag usage
        tag_counts = {}
        for role in roles:
            for tag in role.get('function_tags', []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        if not tag_counts:
            return []

        story = []
        story.append(Paragraph("Function Tag Distribution", self.styles['SectionHeader']))

        cat_lookup = {}
        for cat in function_categories:
            cat_lookup[cat.get('code', '')] = {
                'name': cat.get('name', cat.get('code', '')),
                'color': cat.get('color', '#3b82f6')
            }

        # Sort by count descending
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

        data = [['Function Tag', 'Code', 'Roles Tagged']]
        for code, count in sorted_tags:
            info = cat_lookup.get(code, {'name': code, 'color': '#6b7280'})
            data.append([
                Paragraph(info['name'], self.styles['CellText']),
                Paragraph(code, self.styles['CellText']),
                Paragraph(str(count), self.styles['CellText'])
            ])

        available_width = letter[0] - 1.4 * inch
        col_widths = [available_width * 0.50, available_width * 0.25, available_width * 0.25]
        table = Table(data, colWidths=col_widths, repeatRows=1)

        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(AEGIS_BRONZE)),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
            ('LINEBELOW', (0, 0), (-1, -2), 0.25, colors.HexColor('#e5e7eb')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ]))

        story.append(table)
        story.append(Spacer(1, 8))
        return story

    def _build_footer(self, metadata: Dict) -> list:
        """Build report footer."""
        story = []
        story.append(Spacer(1, 20))
        story.append(HRFlowable(
            width="100%", thickness=1,
            color=colors.HexColor(AEGIS_GOLD),
            spaceAfter=6
        ))

        version = metadata.get('version', '')
        footer_text = f"Generated by AEGIS v{version}" if version else "Generated by AEGIS"
        footer_text += f" &bull; {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        story.append(Paragraph(footer_text, self.styles['Footer']))
        return story
