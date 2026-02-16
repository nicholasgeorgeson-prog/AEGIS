# v3.0.105: Fix Assistant v2 - Summary Report Generator
# WP10: PDF report generation for review sessions
# v3.0.105: BUG-001 FIX - Made output_path optional, returns bytes when not provided

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import os
import io


class ReportGenerator:
    """Generate PDF summary reports for Fix Assistant review sessions."""
    
    VERSION = "3.0.105"
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Create custom paragraph styles for the report."""
        self.styles.add(ParagraphStyle(
            name='ReportTitle', parent=self.styles['Heading1'],
            fontSize=16, alignment=TA_CENTER, spaceAfter=6,
            textColor=colors.HexColor('#1e293b')
        ))
        self.styles.add(ParagraphStyle(
            name='ReportSubtitle', parent=self.styles['Normal'],
            fontSize=10, alignment=TA_CENTER, spaceAfter=12,
            textColor=colors.HexColor('#64748b')
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader', parent=self.styles['Heading2'],
            fontSize=11, spaceBefore=14, spaceAfter=6,
            textColor=colors.HexColor('#1e293b'), fontName='Helvetica-Bold'
        ))
        if 'BodyText' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='BodyText', parent=self.styles['Normal'],
                fontSize=9, spaceAfter=4, textColor=colors.HexColor('#374151')
            ))
        self.styles.add(ParagraphStyle(
            name='SmallText', parent=self.styles['Normal'],
            fontSize=8, textColor=colors.HexColor('#6b7280')
        ))
        self.styles.add(ParagraphStyle(
            name='Footer', parent=self.styles['Normal'],
            fontSize=8, alignment=TA_CENTER, textColor=colors.HexColor('#9ca3af')
        ))
    
    def generate(self, output_path: str = None, document_name: str = None, reviewer_name: str = None,
                 review_data: Dict[str, Any] = None, options: Optional[Dict] = None,
                 **kwargs) -> Union[bytes, Dict[str, Any]]:
        """Generate PDF report.
        
        v3.0.105: Made output_path optional. When not provided, returns PDF bytes directly.
        This allows the API to call without creating temp files.
        
        Args:
            output_path: Optional path to write PDF. If None, returns bytes.
            document_name: Name of the reviewed document.
            reviewer_name: Name of the reviewer.
            review_data: Review session data dict.
            options: Optional generation options.
            **kwargs: Additional keyword args for flexibility.
            
        Returns:
            If output_path provided: Dict with success status and path
            If output_path is None: PDF bytes directly
        """
        # Handle kwargs for backwards compatibility (options can come as kwargs)
        options = options or {}
        options.update(kwargs)
        
        # Default values
        document_name = document_name or 'Document'
        reviewer_name = reviewer_name or ''
        review_data = review_data or {}
        
        page_size = A4 if options.get('page_size') == 'a4' else letter
        
        # Determine output target - file or BytesIO buffer
        use_buffer = output_path is None
        buffer = io.BytesIO() if use_buffer else None
        target = buffer if use_buffer else output_path
        
        try:
            doc = SimpleDocTemplate(target, pagesize=page_size,
                                    leftMargin=0.75*inch, rightMargin=0.75*inch,
                                    topMargin=0.5*inch, bottomMargin=0.5*inch)
            story = []
            review_date = datetime.now()
            
            story.extend(self._build_header(document_name, reviewer_name, review_date,
                                           review_data.get('duration_seconds', 0)))
            story.extend(self._build_overview(review_data))
            story.extend(self._build_quality_section(
                review_data.get('score_before', 0), review_data.get('score_after', 0)))
            story.extend(self._build_category_table(review_data.get('by_category', {})))
            story.extend(self._build_severity_bars(review_data.get('by_severity', {})))
            
            if options.get('include_rejected_details', True) and review_data.get('rejected'):
                story.extend(self._build_rejected_section(
                    review_data['rejected'], options.get('max_rejected_shown', 10)))
            
            if options.get('include_flagged_details', True) and review_data.get('flagged'):
                story.extend(self._build_flagged_section(
                    review_data['flagged'], options.get('max_flagged_shown', 10)))
            
            if review_data.get('reviewer_notes'):
                story.extend(self._build_notes_section(review_data['reviewer_notes']))
            
            story.extend(self._build_footer(review_date))
            doc.build(story)
            
            # Return based on output mode
            if use_buffer:
                buffer.seek(0)
                return buffer.getvalue()
            else:
                return {'success': True, 'path': output_path}
        except Exception as e:
            if use_buffer:
                return None  # Signal failure for bytes mode
            return {'success': False, 'error': str(e)}
    
    def _build_header(self, doc_name: str, reviewer: str, 
                      review_date: datetime, duration_seconds: int) -> List:
        """Build report header section."""
        elements = []
        elements.append(Paragraph("TECHWRITER REVIEW", self.styles['ReportTitle']))
        elements.append(Paragraph("Session Summary Report", self.styles['ReportSubtitle']))
        elements.append(Spacer(1, 8))
        
        header_data = [
            ['Document:', doc_name, 'Reviewer:', reviewer],
            ['Date:', review_date.strftime('%B %d, %Y at %I:%M %p'),
             'Duration:', self._format_duration(duration_seconds)]
        ]
        header_table = Table(header_data, colWidths=[0.8*inch, 2.5*inch, 0.8*inch, 2.5*inch])
        header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#374151')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 6))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
        return elements
    
    def _build_overview(self, data: Dict) -> List:
        """Build overview statistics section."""
        elements = [Paragraph("OVERVIEW", self.styles['SectionHeader'])]
        
        accepted = len(data.get('accepted', []))
        rejected = len(data.get('rejected', []))
        flagged = len(data.get('flagged', []))
        total = data.get('total_issues', accepted + rejected + flagged)
        
        overview_data = [
            [f"Total issues identified: {total}"],
            [f"<font color='#16a34a'>✓</font>  {accepted} fixes ACCEPTED (applied as tracked changes)"],
            [f"<font color='#dc2626'>✗</font>  {rejected} fixes REJECTED (noted as comments)"],
            [f"<font color='#ca8a04'>○</font>  {flagged} issues FLAGGED (no automatic fix available)"]
        ]
        for row in overview_data:
            elements.append(Paragraph(row[0], self.styles['BodyText']))
        elements.append(Spacer(1, 6))
        return elements
    
    def _build_quality_section(self, before: int, after: int) -> List:
        """Build quality improvement section."""
        elements = [Paragraph("QUALITY IMPROVEMENT", self.styles['SectionHeader'])]
        
        improvement = after - before
        pct = round((improvement / before) * 100) if before > 0 else 0
        
        quality_data = [
            ['Score Before:', f"{before} (Grade: {self._score_to_grade(before)})"],
            ['Score After:', f"{after} (Grade: {self._score_to_grade(after)}) *estimated"],
            ['Improvement:', f"+{improvement} points (+{pct}%)" if improvement >= 0 
                           else f"{improvement} points ({pct}%)"]
        ]
        quality_table = Table(quality_data, colWidths=[1.2*inch, 3*inch])
        quality_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#374151')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(quality_table)
        elements.append(Spacer(1, 6))
        return elements
    
    def _build_category_table(self, by_category: Dict) -> List:
        """Build category breakdown table."""
        if not by_category:
            return []
        elements = [Paragraph("BREAKDOWN BY CATEGORY", self.styles['SectionHeader'])]
        
        table_data = [['Category', 'Total', 'Accepted', 'Rejected', 'Flagged']]
        for cat, counts in sorted(by_category.items()):
            table_data.append([
                cat, str(counts.get('total', 0)), str(counts.get('accepted', 0)),
                str(counts.get('rejected', 0)), str(counts.get('flagged', 0))
            ])
        
        cat_table = Table(table_data, colWidths=[1.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
        cat_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#374151')),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ]))
        elements.append(cat_table)
        elements.append(Spacer(1, 6))
        return elements
    
    def _build_severity_bars(self, by_severity: Dict) -> List:
        """Build severity breakdown with progress bars."""
        if not by_severity:
            return []
        elements = [Paragraph("BREAKDOWN BY SEVERITY", self.styles['SectionHeader'])]
        
        severity_order = ['Critical', 'High', 'Medium', 'Low', 'Info']
        bar_colors = {'Critical': '#dc2626', 'High': '#ea580c', 'Medium': '#ca8a04',
                      'Low': '#16a34a', 'Info': '#6b7280'}
        
        for sev in severity_order:
            if sev in by_severity:
                counts = by_severity[sev]
                total = counts.get('total', 0)
                accepted = counts.get('accepted', 0)
                pct = round((accepted / total) * 100) if total > 0 else 0
                bar = self._create_bar_string(pct)
                text = f"<b>{sev:10}</b> {bar}  {accepted}/{total}  ({pct}%)"
                elements.append(Paragraph(text, self.styles['BodyText']))
        
        elements.append(Spacer(1, 6))
        return elements
    
    def _create_bar_string(self, percent: int, width: int = 20) -> str:
        """Create text-based progress bar."""
        filled = round(percent / 100 * width)
        return '█' * filled + '░' * (width - filled)
    
    def _build_rejected_section(self, rejected: List, max_shown: int) -> List:
        """Build rejected fixes list."""
        elements = [Paragraph("REJECTED FIXES", self.styles['SectionHeader'])]
        
        for i, fix in enumerate(rejected[:max_shown]):
            page = fix.get('page', '?')
            flagged = fix.get('flagged_text', '')[:30]
            suggestion = fix.get('suggestion', '')[:30]
            note = fix.get('note', 'No reason provided')
            elements.append(Paragraph(
                f"<b>Page {page}:</b> \"{flagged}\" → \"{suggestion}\"", self.styles['BodyText']))
            elements.append(Paragraph(f"<i>Reviewer note: {note}</i>", self.styles['SmallText']))
            elements.append(Spacer(1, 4))
        
        if len(rejected) > max_shown:
            elements.append(Paragraph(
                f"... (showing {max_shown} of {len(rejected)} rejected fixes)", self.styles['SmallText']))
        elements.append(Spacer(1, 6))
        return elements
    
    def _build_flagged_section(self, flagged: List, max_shown: int) -> List:
        """Build flagged items list."""
        elements = [Paragraph("FLAGGED ITEMS (No Automatic Fix)", self.styles['SectionHeader'])]
        
        for i, item in enumerate(flagged[:max_shown]):
            page = item.get('page', '?')
            msg = item.get('message', item.get('category', 'Review required'))
            elements.append(Paragraph(f"<b>Page {page}:</b> {msg}", self.styles['BodyText']))
        
        if len(flagged) > max_shown:
            elements.append(Paragraph(
                f"... (showing {max_shown} of {len(flagged)} flagged items)", self.styles['SmallText']))
        elements.append(Spacer(1, 6))
        return elements
    
    def _build_notes_section(self, notes: List) -> List:
        """Build reviewer notes section."""
        elements = [Paragraph("REVIEWER NOTES", self.styles['SectionHeader'])]
        for note in notes:
            elements.append(Paragraph(f"• {note}", self.styles['BodyText']))
        elements.append(Spacer(1, 6))
        return elements
    
    def _build_footer(self, gen_date: datetime) -> List:
        """Build report footer."""
        return [
            Spacer(1, 12),
            HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')),
            Spacer(1, 6),
            Paragraph(f"Generated by AEGIS v{self.VERSION}", self.styles['Footer']),
            Paragraph(f"Report generated: {gen_date.strftime('%B %d, %Y at %I:%M %p')}",
                     self.styles['Footer'])
        ]
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration as 'X minutes Y seconds'."""
        minutes, secs = divmod(seconds, 60)
        if minutes == 0:
            return f"{secs} seconds"
        elif secs == 0:
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        return f"{minutes} minute{'s' if minutes != 1 else ''} {secs} seconds"
    
    def _score_to_grade(self, score: int) -> str:
        """Convert numeric score to letter grade."""
        grades = [(97,'A+'), (93,'A'), (90,'A-'), (87,'B+'), (83,'B'), (80,'B-'),
                  (77,'C+'), (73,'C'), (70,'C-'), (67,'D+'), (63,'D'), (60,'D-')]
        for threshold, grade in grades:
            if score >= threshold:
                return grade
        return 'F'
