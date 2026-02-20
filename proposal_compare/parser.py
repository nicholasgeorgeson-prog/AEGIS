"""
AEGIS Proposal Parser — Extracts financial data from DOCX, PDF, and XLSX files.

Pure extraction — NO AI/LLM involvement. Uses:
- openpyxl for Excel spreadsheets
- python-docx + lxml for DOCX tables
- pymupdf4llm / fitz for PDF tables
- Regex patterns for dollar amounts, percentages, dates

Returns structured ProposalData objects with company info, tables, and financial items.
"""

import re
import os
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Data classes
# ──────────────────────────────────────────────

@dataclass
class LineItem:
    """A single financial line item extracted from a proposal."""
    description: str = ''
    amount: Optional[float] = None
    amount_raw: str = ''        # Original string, e.g. "$1,234.56"
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    unit: str = ''
    category: str = ''          # Labor, Material, Travel, ODC, etc.
    row_index: int = 0          # Source row in the table
    table_index: int = 0        # Which table it came from
    source_sheet: str = ''      # Sheet name (Excel) or page (PDF)
    confidence: float = 1.0     # Extraction confidence (1.0 = certain)

@dataclass
class ExtractedTable:
    """A table extracted from a document."""
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)
    source: str = ''           # Sheet name, page number, etc.
    table_index: int = 0
    has_financial_data: bool = False
    total_row_index: Optional[int] = None  # Index of "Total" row if found

@dataclass
class ProposalData:
    """Complete extracted data from a single proposal document."""
    filename: str = ''
    filepath: str = ''
    file_type: str = ''        # 'xlsx', 'docx', 'pdf'
    company_name: str = ''
    proposal_title: str = ''
    date: str = ''

    # Extracted data
    tables: List[ExtractedTable] = field(default_factory=list)
    line_items: List[LineItem] = field(default_factory=list)

    # Financial summary
    total_amount: Optional[float] = None
    total_raw: str = ''
    currency: str = 'USD'

    # Metadata
    page_count: int = 0
    extraction_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            'filename': self.filename,
            'filepath': self.filepath,
            'file_type': self.file_type,
            'company_name': self.company_name,
            'proposal_title': self.proposal_title,
            'date': self.date,
            'tables': [
                {
                    'headers': t.headers,
                    'rows': t.rows,
                    'source': t.source,
                    'table_index': t.table_index,
                    'has_financial_data': t.has_financial_data,
                    'total_row_index': t.total_row_index,
                }
                for t in self.tables
            ],
            'line_items': [
                {
                    'description': li.description,
                    'amount': li.amount,
                    'amount_raw': li.amount_raw,
                    'quantity': li.quantity,
                    'unit_price': li.unit_price,
                    'unit': li.unit,
                    'category': li.category,
                    'row_index': li.row_index,
                    'table_index': li.table_index,
                    'source_sheet': li.source_sheet,
                    'confidence': li.confidence,
                }
                for li in self.line_items
            ],
            'total_amount': self.total_amount,
            'total_raw': self.total_raw,
            'currency': self.currency,
            'page_count': self.page_count,
            'extraction_notes': self.extraction_notes,
        }


# ──────────────────────────────────────────────
# Regex patterns for financial extraction
# ──────────────────────────────────────────────

# Dollar amounts: $1,234.56, $1234, $ 1,234.56, $1,234,567.89
DOLLAR_PATTERN = re.compile(
    r'\$\s*[\d,]+(?:\.\d{1,2})?'
)

# Percentage: 10%, 10.5%, 0.5%
PERCENT_PATTERN = re.compile(
    r'\d+(?:\.\d+)?\s*%'
)

# Date patterns: MM/DD/YYYY, YYYY-MM-DD, Month DD YYYY, etc.
DATE_PATTERN = re.compile(
    r'(?:\d{1,2}/\d{1,2}/\d{2,4})|'
    r'(?:\d{4}-\d{2}-\d{2})|'
    r'(?:(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})|'
    r'(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4})',
    re.IGNORECASE
)

# Numeric with optional commas: 1,234.56 or 1234.56
NUMERIC_PATTERN = re.compile(
    r'^[\d,]+(?:\.\d{1,4})?$'
)

# Total / subtotal / grand total row indicators
TOTAL_KEYWORDS = re.compile(
    r'\b(?:total|subtotal|sub-total|grand\s*total|sum|net|gross|overall)\b',
    re.IGNORECASE
)

# Category keywords for classification
CATEGORY_PATTERNS = {
    'Labor': re.compile(r'\b(?:labor|labour|personnel|staffing|hours?|FTE|man-?hours?|salaries?|wages?)\b', re.IGNORECASE),
    'Material': re.compile(r'\b(?:material|supplies|equipment|hardware|software|license|subscription)\b', re.IGNORECASE),
    'Travel': re.compile(r'\b(?:travel|per\s*diem|airfare|lodging|mileage|transportation)\b', re.IGNORECASE),
    'ODC': re.compile(r'\b(?:ODC|other\s*direct|subcontract|consultant|vendor)\b', re.IGNORECASE),
    'Overhead': re.compile(r'\b(?:overhead|indirect|G&A|general\s*(?:and|&)\s*admin|fringe|burden|wrap\s*rate)\b', re.IGNORECASE),
    'Fee': re.compile(r'\b(?:fee|profit|margin|markup)\b', re.IGNORECASE),
}

# Company name patterns (found in headers/footers/cover)
COMPANY_INDICATORS = re.compile(
    r'\b(?:LLC|Inc\.?|Corp\.?|Corporation|Company|Co\.|Ltd\.?|Group|Associates|Partners|Consulting|Technologies|Solutions|Systems|Services|International|Aerospace|Defense|Defence)\b',
    re.IGNORECASE
)


# ──────────────────────────────────────────────
# Utility functions
# ──────────────────────────────────────────────

def parse_dollar_amount(text: str) -> Optional[float]:
    """Parse a dollar string into a float. Returns None if not parseable."""
    if not text:
        return None
    # Remove $ and spaces, keep digits, commas, periods, minus
    cleaned = re.sub(r'[^\d,.\-()]', '', text)
    if not cleaned:
        return None
    # Handle parenthetical negatives: (1,234.56) -> -1234.56
    is_negative = '(' in text and ')' in text
    cleaned = cleaned.replace('(', '').replace(')', '').replace(',', '')
    try:
        val = float(cleaned)
        return -val if is_negative else val
    except ValueError:
        return None


def classify_line_item(description: str) -> str:
    """Classify a line item into a category based on description text."""
    for category, pattern in CATEGORY_PATTERNS.items():
        if pattern.search(description):
            return category
    return 'Other'


def extract_company_from_text(text: str, max_chars: int = 2000) -> str:
    """Try to extract company name from document text (first N chars)."""
    search_text = text[:max_chars]

    # Strategy 1: Look for lines with company indicators
    for line in search_text.split('\n'):
        line = line.strip()
        if not line or len(line) > 120:
            continue
        if COMPANY_INDICATORS.search(line):
            # Clean up the line
            name = re.sub(r'^\W+|\W+$', '', line)
            # Remove common prefixes
            name = re.sub(r'^(?:prepared\s+by|submitted\s+by|from|proposal\s+by)\s*:?\s*', '', name, flags=re.IGNORECASE)
            if 5 < len(name) < 100:
                return name.strip()

    # Strategy 2: Look for "Prepared by: XXX" or "Submitted by: XXX"
    match = re.search(
        r'(?:prepared|submitted|proposed|offered)\s+by\s*:?\s*(.+?)(?:\n|$)',
        search_text, re.IGNORECASE
    )
    if match:
        name = match.group(1).strip()
        if 3 < len(name) < 100:
            return name

    return ''


def extract_dates_from_text(text: str, max_chars: int = 3000) -> str:
    """Extract the most prominent date from document text."""
    search_text = text[:max_chars]
    matches = DATE_PATTERN.findall(search_text)
    if matches:
        return matches[0]
    return ''


def is_financial_table(headers: List[str], rows: List[List[str]]) -> bool:
    """Determine if a table likely contains financial data."""
    header_text = ' '.join(h.lower() for h in headers if h)

    # Check headers for financial indicators
    financial_headers = ['cost', 'price', 'amount', 'total', 'rate', 'fee',
                         'budget', 'estimate', 'value', 'subtotal', 'charge',
                         'extended', 'unit price', 'labor', 'material', 'travel']
    if any(kw in header_text for kw in financial_headers):
        return True

    # Check if rows contain dollar amounts
    dollar_count = 0
    for row in rows[:10]:  # Check first 10 rows
        for cell in row:
            if DOLLAR_PATTERN.search(str(cell)):
                dollar_count += 1

    # If more than 20% of checked cells have dollar amounts, it's financial
    total_cells = sum(len(row) for row in rows[:10])
    if total_cells > 0 and dollar_count / total_cells > 0.15:
        return True

    return False


def find_total_row(rows: List[List[str]]) -> Tuple[Optional[int], Optional[float]]:
    """Find the "Total" row in a table and extract its amount."""
    for i, row in enumerate(rows):
        for j, cell in enumerate(row):
            if TOTAL_KEYWORDS.search(str(cell)):
                # Look for dollar amount in the same row
                for k, val in enumerate(row):
                    dollar_match = DOLLAR_PATTERN.search(str(val))
                    if dollar_match:
                        amount = parse_dollar_amount(dollar_match.group())
                        if amount is not None:
                            return i, amount
    return None, None


def extract_line_items_from_table(table: ExtractedTable) -> List[LineItem]:
    """Extract financial line items from a table."""
    items = []
    if not table.rows or not table.headers:
        return items

    # Identify column roles
    headers_lower = [h.lower().strip() for h in table.headers]

    desc_col = None
    amount_col = None
    qty_col = None
    unit_price_col = None

    for i, h in enumerate(headers_lower):
        if not h:
            continue
        if any(kw in h for kw in ['description', 'item', 'task', 'clin', 'line item', 'wbs', 'name', 'service']):
            if desc_col is None:
                desc_col = i
        if any(kw in h for kw in ['total', 'amount', 'extended', 'cost', 'price', 'value', 'sum']):
            amount_col = i
        if any(kw in h for kw in ['qty', 'quantity', 'hours', 'units', 'count']):
            qty_col = i
        if any(kw in h for kw in ['rate', 'unit price', 'unit cost', 'per unit', 'hourly']):
            unit_price_col = i

    # If no description column found, use first non-empty text column
    if desc_col is None:
        for i, h in enumerate(headers_lower):
            if h and not any(kw in h for kw in ['#', 'no', 'num', 'id']):
                desc_col = i
                break

    # If no amount column found, find the column with most dollar values
    if amount_col is None:
        col_dollar_counts = {}
        for row in table.rows:
            for j, cell in enumerate(row):
                if DOLLAR_PATTERN.search(str(cell)):
                    col_dollar_counts[j] = col_dollar_counts.get(j, 0) + 1
        if col_dollar_counts:
            amount_col = max(col_dollar_counts, key=col_dollar_counts.get)

    if amount_col is None:
        return items

    for row_idx, row in enumerate(table.rows):
        # Skip if this is a total/subtotal row
        row_text = ' '.join(str(c) for c in row)
        if TOTAL_KEYWORDS.search(row_text) and row_idx > len(table.rows) * 0.5:
            continue  # Skip totals in the bottom half

        # Get description
        desc = str(row[desc_col]).strip() if desc_col is not None and desc_col < len(row) else ''
        if not desc or len(desc) < 2:
            continue

        # Get amount
        amount_str = str(row[amount_col]).strip() if amount_col < len(row) else ''
        dollar_match = DOLLAR_PATTERN.search(amount_str)
        if dollar_match:
            amount_raw = dollar_match.group()
            amount = parse_dollar_amount(amount_raw)
        elif NUMERIC_PATTERN.match(amount_str.replace(',', '').strip()):
            amount_raw = amount_str
            amount = parse_dollar_amount(amount_str)
        else:
            continue  # No financial value in this row

        if amount is None or amount == 0:
            continue

        # Get optional fields
        qty = None
        if qty_col is not None and qty_col < len(row):
            qty_str = str(row[qty_col]).strip().replace(',', '')
            try:
                qty = float(qty_str)
            except ValueError:
                pass

        unit_price = None
        if unit_price_col is not None and unit_price_col < len(row):
            up_str = str(row[unit_price_col]).strip()
            unit_price = parse_dollar_amount(up_str)

        item = LineItem(
            description=desc,
            amount=amount,
            amount_raw=amount_raw,
            quantity=qty,
            unit_price=unit_price,
            category=classify_line_item(desc),
            row_index=row_idx,
            table_index=table.table_index,
            source_sheet=table.source,
        )
        items.append(item)

    return items


# ──────────────────────────────────────────────
# Excel Parser
# ──────────────────────────────────────────────

def parse_excel(filepath: str) -> ProposalData:
    """Parse an Excel file (.xlsx/.xls) for proposal financial data."""
    import openpyxl

    proposal = ProposalData(
        filename=os.path.basename(filepath),
        filepath=filepath,
        file_type='xlsx',
    )

    try:
        wb = openpyxl.load_workbook(filepath, data_only=True, read_only=True)
    except Exception as e:
        proposal.extraction_notes.append(f'Failed to open Excel file: {e}')
        return proposal

    all_text_parts = []

    for sheet_idx, sheet_name in enumerate(wb.sheetnames):
        ws = wb[sheet_name]

        # Read all rows
        all_rows = []
        for row in ws.iter_rows(values_only=True):
            str_row = [str(cell) if cell is not None else '' for cell in row]
            all_rows.append(str_row)
            all_text_parts.append(' '.join(str_row))

        if not all_rows:
            continue

        # Find header row (first row with 3+ non-empty cells)
        header_idx = 0
        for i, row in enumerate(all_rows[:10]):
            non_empty = sum(1 for c in row if c.strip())
            if non_empty >= 3:
                header_idx = i
                break

        headers = all_rows[header_idx] if header_idx < len(all_rows) else []
        data_rows = all_rows[header_idx + 1:]

        # Filter out completely empty rows
        data_rows = [r for r in data_rows if any(c.strip() for c in r)]

        if not data_rows:
            continue

        table = ExtractedTable(
            headers=headers,
            rows=data_rows,
            source=sheet_name,
            table_index=sheet_idx,
        )

        # Check if financial
        table.has_financial_data = is_financial_table(headers, data_rows)

        # Find total row
        total_idx, total_amount = find_total_row(data_rows)
        table.total_row_index = total_idx

        proposal.tables.append(table)

        # Extract line items from financial tables
        if table.has_financial_data:
            items = extract_line_items_from_table(table)
            proposal.line_items.extend(items)

            if total_amount is not None and (proposal.total_amount is None or total_amount > (proposal.total_amount or 0)):
                proposal.total_amount = total_amount
                proposal.total_raw = f'${total_amount:,.2f}'

    wb.close()

    # Extract company name and date from all text
    full_text = '\n'.join(all_text_parts)
    if not proposal.company_name:
        proposal.company_name = extract_company_from_text(full_text)
    if not proposal.date:
        proposal.date = extract_dates_from_text(full_text)

    # If no total found from total rows, sum line items
    if proposal.total_amount is None and proposal.line_items:
        proposal.total_amount = sum(li.amount for li in proposal.line_items if li.amount)
        proposal.total_raw = f'${proposal.total_amount:,.2f}'

    proposal.extraction_notes.append(f'Found {len(proposal.tables)} sheets, {len(proposal.line_items)} line items')

    return proposal


# ──────────────────────────────────────────────
# DOCX Parser
# ──────────────────────────────────────────────

def parse_docx(filepath: str) -> ProposalData:
    """Parse a DOCX file for proposal financial data."""
    from docx import Document as DocxDocument

    proposal = ProposalData(
        filename=os.path.basename(filepath),
        filepath=filepath,
        file_type='docx',
    )

    try:
        doc = DocxDocument(filepath)
    except Exception as e:
        proposal.extraction_notes.append(f'Failed to open DOCX file: {e}')
        return proposal

    # Extract full text for company/date detection
    full_text_parts = []
    for para in doc.paragraphs:
        full_text_parts.append(para.text)

    # Extract title from first heading or large text
    for para in doc.paragraphs[:20]:
        if para.style and 'heading' in (para.style.name or '').lower():
            if not proposal.proposal_title and len(para.text.strip()) > 5:
                proposal.proposal_title = para.text.strip()
                break

    # Extract tables
    for tbl_idx, table in enumerate(doc.tables):
        headers = []
        rows = []

        for row_idx, row in enumerate(table.rows):
            cells = [cell.text.strip() for cell in row.cells]
            if row_idx == 0:
                headers = cells
            else:
                rows.append(cells)

        if not headers and not rows:
            continue

        # Filter empty rows
        rows = [r for r in rows if any(c.strip() for c in r)]

        ext_table = ExtractedTable(
            headers=headers,
            rows=rows,
            source=f'Table {tbl_idx + 1}',
            table_index=tbl_idx,
        )

        ext_table.has_financial_data = is_financial_table(headers, rows)
        total_idx, total_amount = find_total_row(rows)
        ext_table.total_row_index = total_idx

        proposal.tables.append(ext_table)

        if ext_table.has_financial_data:
            items = extract_line_items_from_table(ext_table)
            proposal.line_items.extend(items)

            if total_amount is not None and (proposal.total_amount is None or total_amount > (proposal.total_amount or 0)):
                proposal.total_amount = total_amount
                proposal.total_raw = f'${total_amount:,.2f}'

    # Also scan paragraphs for inline dollar amounts (not in tables)
    inline_amounts = []
    full_text = '\n'.join(full_text_parts)
    for match in DOLLAR_PATTERN.finditer(full_text):
        amount = parse_dollar_amount(match.group())
        if amount and amount > 1000:  # Only significant amounts
            # Get surrounding context
            start = max(0, match.start() - 80)
            end = min(len(full_text), match.end() + 40)
            context = full_text[start:end].replace('\n', ' ').strip()
            inline_amounts.append((amount, match.group(), context))

    if inline_amounts and not proposal.line_items:
        proposal.extraction_notes.append(f'Found {len(inline_amounts)} dollar amounts in body text (no tables)')
        # If no table-based items, create items from inline amounts
        for idx, (amount, raw, context) in enumerate(inline_amounts[:50]):
            proposal.line_items.append(LineItem(
                description=context,
                amount=amount,
                amount_raw=raw,
                category=classify_line_item(context),
                row_index=idx,
                source_sheet='Body Text',
                confidence=0.7,
            ))

    # Company and date
    if not proposal.company_name:
        proposal.company_name = extract_company_from_text(full_text)
    if not proposal.date:
        proposal.date = extract_dates_from_text(full_text)

    # Total
    if proposal.total_amount is None and proposal.line_items:
        proposal.total_amount = sum(li.amount for li in proposal.line_items if li.amount)
        proposal.total_raw = f'${proposal.total_amount:,.2f}'

    proposal.page_count = len(doc.paragraphs) // 30  # Rough estimate
    proposal.extraction_notes.append(f'Found {len(doc.tables)} tables, {len(proposal.line_items)} line items')

    return proposal


# ──────────────────────────────────────────────
# PDF Parser
# ──────────────────────────────────────────────

def parse_pdf(filepath: str) -> ProposalData:
    """Parse a PDF file for proposal financial data."""
    proposal = ProposalData(
        filename=os.path.basename(filepath),
        filepath=filepath,
        file_type='pdf',
    )

    # Try pymupdf4llm first (better table extraction)
    try:
        import pymupdf4llm
        import fitz

        doc = fitz.open(filepath)
        proposal.page_count = len(doc)

        # Get full text via pymupdf4llm (Markdown with tables)
        md_text = pymupdf4llm.to_markdown(filepath)

        # Extract tables from Markdown
        tables = _extract_tables_from_markdown(md_text)

        for tbl_idx, (headers, rows) in enumerate(tables):
            ext_table = ExtractedTable(
                headers=headers,
                rows=rows,
                source=f'Page (Markdown)',
                table_index=tbl_idx,
            )
            ext_table.has_financial_data = is_financial_table(headers, rows)
            total_idx, total_amount = find_total_row(rows)
            ext_table.total_row_index = total_idx

            proposal.tables.append(ext_table)

            if ext_table.has_financial_data:
                items = extract_line_items_from_table(ext_table)
                proposal.line_items.extend(items)

                if total_amount is not None and (proposal.total_amount is None or total_amount > (proposal.total_amount or 0)):
                    proposal.total_amount = total_amount
                    proposal.total_raw = f'${total_amount:,.2f}'

        # Also try fitz table extraction for better accuracy
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_tables = page.find_tables()
            if page_tables and page_tables.tables:
                for ft_idx, ft in enumerate(page_tables.tables):
                    try:
                        extracted = ft.extract()
                        if not extracted or len(extracted) < 2:
                            continue

                        headers = [str(c) if c else '' for c in extracted[0]]
                        rows = [[str(c) if c else '' for c in r] for r in extracted[1:]]
                        rows = [r for r in rows if any(c.strip() for c in r)]

                        if not rows:
                            continue

                        # Check if we already have this table (from markdown)
                        # Simple dedup: skip if headers match an existing table
                        h_key = '|'.join(h.strip().lower() for h in headers if h.strip())
                        existing_keys = set()
                        for et in proposal.tables:
                            existing_keys.add('|'.join(h.strip().lower() for h in et.headers if h.strip()))

                        if h_key in existing_keys:
                            continue

                        tbl_index = len(proposal.tables)
                        ext_table = ExtractedTable(
                            headers=headers,
                            rows=rows,
                            source=f'Page {page_num + 1}',
                            table_index=tbl_index,
                        )
                        ext_table.has_financial_data = is_financial_table(headers, rows)
                        total_idx, total_amount = find_total_row(rows)
                        ext_table.total_row_index = total_idx

                        proposal.tables.append(ext_table)

                        if ext_table.has_financial_data:
                            items = extract_line_items_from_table(ext_table)
                            proposal.line_items.extend(items)

                            if total_amount is not None and (proposal.total_amount is None or total_amount > (proposal.total_amount or 0)):
                                proposal.total_amount = total_amount
                                proposal.total_raw = f'${total_amount:,.2f}'
                    except Exception:
                        continue

        doc.close()

        # Company and date from text
        plain_text = re.sub(r'[#*|_\-]+', ' ', md_text)
        if not proposal.company_name:
            proposal.company_name = extract_company_from_text(plain_text)
        if not proposal.date:
            proposal.date = extract_dates_from_text(plain_text)

    except ImportError:
        proposal.extraction_notes.append('pymupdf4llm not available — limited PDF extraction')
        # Fallback to basic fitz text extraction
        try:
            import fitz
            doc = fitz.open(filepath)
            proposal.page_count = len(doc)

            full_text = ''
            for page in doc:
                full_text += page.get_text() + '\n'
            doc.close()

            # Extract inline dollar amounts
            for match in DOLLAR_PATTERN.finditer(full_text):
                amount = parse_dollar_amount(match.group())
                if amount and amount > 100:
                    start = max(0, match.start() - 80)
                    end = min(len(full_text), match.end() + 40)
                    context = full_text[start:end].replace('\n', ' ').strip()
                    proposal.line_items.append(LineItem(
                        description=context,
                        amount=amount,
                        amount_raw=match.group(),
                        category=classify_line_item(context),
                        source_sheet='PDF Text',
                        confidence=0.5,
                    ))

            if not proposal.company_name:
                proposal.company_name = extract_company_from_text(full_text)
            if not proposal.date:
                proposal.date = extract_dates_from_text(full_text)

        except ImportError:
            proposal.extraction_notes.append('No PDF library available')
    except Exception as e:
        proposal.extraction_notes.append(f'PDF parsing error: {e}')
        logger.error(f'PDF parsing error for {filepath}: {e}', exc_info=True)

    # Total
    if proposal.total_amount is None and proposal.line_items:
        proposal.total_amount = sum(li.amount for li in proposal.line_items if li.amount)
        proposal.total_raw = f'${proposal.total_amount:,.2f}'

    proposal.extraction_notes.append(f'Found {len(proposal.tables)} tables, {len(proposal.line_items)} line items')

    return proposal


def _extract_tables_from_markdown(md_text: str) -> List[Tuple[List[str], List[List[str]]]]:
    """Extract tables from Markdown text (pymupdf4llm output)."""
    tables = []
    lines = md_text.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Detect Markdown table: line with | separators
        if '|' in line and line.startswith('|'):
            # Potential table start
            header_cells = [c.strip() for c in line.split('|')]
            header_cells = [c for c in header_cells if c]  # Remove empty from split

            # Check for separator row (---|---|---)
            if i + 1 < len(lines) and re.match(r'\|[\s\-:|]+\|', lines[i + 1].strip()):
                i += 2  # Skip header + separator

                rows = []
                while i < len(lines) and '|' in lines[i] and lines[i].strip().startswith('|'):
                    row_cells = [c.strip() for c in lines[i].strip().split('|')]
                    row_cells = [c for c in row_cells if c or len(row_cells) > 3]
                    # Clean: remove first/last empty from | split
                    if row_cells and not row_cells[0]:
                        row_cells = row_cells[1:]
                    if row_cells and not row_cells[-1]:
                        row_cells = row_cells[:-1]
                    if row_cells:
                        rows.append(row_cells)
                    i += 1

                if rows:
                    tables.append((header_cells, rows))
                continue

        i += 1

    return tables


# ──────────────────────────────────────────────
# Main entry point
# ──────────────────────────────────────────────

SUPPORTED_EXTENSIONS = {'.xlsx', '.xls', '.docx', '.pdf'}

def parse_proposal(filepath: str) -> ProposalData:
    """Parse a proposal document and extract financial data.

    Supports: .xlsx, .xls, .docx, .pdf
    Returns a ProposalData object with extracted tables, line items, and totals.
    """
    ext = os.path.splitext(filepath)[1].lower()

    if ext in ('.xlsx', '.xls'):
        return parse_excel(filepath)
    elif ext == '.docx':
        return parse_docx(filepath)
    elif ext == '.pdf':
        return parse_pdf(filepath)
    else:
        data = ProposalData(
            filename=os.path.basename(filepath),
            filepath=filepath,
            file_type=ext.lstrip('.'),
        )
        data.extraction_notes.append(f'Unsupported file type: {ext}')
        return data
