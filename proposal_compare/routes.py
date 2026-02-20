"""
AEGIS Proposal Compare API Routes

Endpoints:
- POST /api/proposal-compare/upload     — Upload proposal files, extract data
- POST /api/proposal-compare/compare    — Compare extracted proposals
- GET  /api/proposal-compare/export     — Export comparison as XLSX
"""

import os
import json
import logging
import tempfile
import traceback
from flask import Blueprint, request, jsonify, send_file, current_app

logger = logging.getLogger(__name__)

pc_blueprint = Blueprint('proposal_compare', __name__)


@pc_blueprint.route('/api/proposal-compare/upload', methods=['POST'])
def upload_proposals():
    """Upload one or more proposal files and extract financial data.

    Expects multipart/form-data with 'files[]' field.
    Returns extracted data for each file.
    """
    try:
        from .parser import parse_proposal, SUPPORTED_EXTENSIONS

        if 'files[]' not in request.files:
            return jsonify({
                'success': False,
                'error': {'message': 'No files provided. Use "files[]" field.'}
            }), 400

        files = request.files.getlist('files[]')
        if not files:
            return jsonify({
                'success': False,
                'error': {'message': 'No files provided'}
            }), 400

        if len(files) > 10:
            return jsonify({
                'success': False,
                'error': {'message': 'Maximum 10 files allowed per upload'}
            }), 400

        results = []
        temp_dir = tempfile.mkdtemp(prefix='aegis_proposal_')

        for f in files:
            if not f.filename:
                continue

            ext = os.path.splitext(f.filename)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                results.append({
                    'filename': f.filename,
                    'success': False,
                    'error': f'Unsupported file type: {ext}. Supported: {", ".join(SUPPORTED_EXTENSIONS)}',
                })
                continue

            # Save temp file
            temp_path = os.path.join(temp_dir, f.filename)
            try:
                f.save(temp_path)
            except Exception as save_err:
                results.append({
                    'filename': f.filename,
                    'success': False,
                    'error': f'Failed to save file: {save_err}',
                })
                continue

            # Parse
            try:
                proposal_data = parse_proposal(temp_path)
                results.append({
                    'filename': f.filename,
                    'success': True,
                    'data': proposal_data.to_dict(),
                })
            except Exception as parse_err:
                logger.error(f'Proposal parse error for {f.filename}: {parse_err}', exc_info=True)
                results.append({
                    'filename': f.filename,
                    'success': False,
                    'error': f'Parse error: {str(parse_err)}',
                })
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass

        # Clean up temp dir
        try:
            os.rmdir(temp_dir)
        except Exception:
            pass

        successful = sum(1 for r in results if r.get('success'))

        return jsonify({
            'success': True,
            'data': {
                'results': results,
                'total_uploaded': len(files),
                'successful': successful,
                'failed': len(files) - successful,
            }
        })

    except Exception as e:
        logger.error(f'Proposal upload error: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': {'message': f'Upload error: {str(e)}', 'traceback': traceback.format_exc()}
        }), 500


@pc_blueprint.route('/api/proposal-compare/compare', methods=['POST'])
def compare_proposals_endpoint():
    """Compare extracted proposal data.

    Expects JSON body with 'proposals' array of ProposalData dicts
    (as returned by the upload endpoint).
    """
    try:
        from .parser import ProposalData, LineItem, ExtractedTable
        from .analyzer import compare_proposals

        data = request.get_json()
        if not data or 'proposals' not in data:
            return jsonify({
                'success': False,
                'error': {'message': 'Missing "proposals" array in request body'}
            }), 400

        raw_proposals = data['proposals']
        if len(raw_proposals) < 2:
            return jsonify({
                'success': False,
                'error': {'message': 'Need at least 2 proposals to compare'}
            }), 400

        if len(raw_proposals) > 10:
            return jsonify({
                'success': False,
                'error': {'message': 'Maximum 10 proposals allowed'}
            }), 400

        # Reconstruct ProposalData objects from dicts
        proposals = []
        for rp in raw_proposals:
            p = ProposalData(
                filename=rp.get('filename', ''),
                filepath=rp.get('filepath', ''),
                file_type=rp.get('file_type', ''),
                company_name=rp.get('company_name', ''),
                proposal_title=rp.get('proposal_title', ''),
                date=rp.get('date', ''),
                total_amount=rp.get('total_amount'),
                total_raw=rp.get('total_raw', ''),
                currency=rp.get('currency', 'USD'),
                page_count=rp.get('page_count', 0),
                extraction_notes=rp.get('extraction_notes', []),
            )

            # Reconstruct tables
            for td in rp.get('tables', []):
                t = ExtractedTable(
                    headers=td.get('headers', []),
                    rows=td.get('rows', []),
                    source=td.get('source', ''),
                    table_index=td.get('table_index', 0),
                    has_financial_data=td.get('has_financial_data', False),
                    total_row_index=td.get('total_row_index'),
                )
                p.tables.append(t)

            # Reconstruct line items
            for lid in rp.get('line_items', []):
                li = LineItem(
                    description=lid.get('description', ''),
                    amount=lid.get('amount'),
                    amount_raw=lid.get('amount_raw', ''),
                    quantity=lid.get('quantity'),
                    unit_price=lid.get('unit_price'),
                    unit=lid.get('unit', ''),
                    category=lid.get('category', ''),
                    row_index=lid.get('row_index', 0),
                    table_index=lid.get('table_index', 0),
                    source_sheet=lid.get('source_sheet', ''),
                    confidence=lid.get('confidence', 1.0),
                )
                p.line_items.append(li)

            proposals.append(p)

        # Run comparison
        result = compare_proposals(proposals)

        return jsonify({
            'success': True,
            'data': result.to_dict(),
        })

    except Exception as e:
        logger.error(f'Proposal compare error: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': {'message': f'Compare error: {str(e)}', 'traceback': traceback.format_exc()}
        }), 500


@pc_blueprint.route('/api/proposal-compare/export', methods=['POST'])
def export_comparison():
    """Export comparison results as XLSX.

    Expects JSON body with comparison result data.
    """
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': {'message': 'Missing comparison data'}
            }), 400

        proposals = data.get('proposals', [])
        aligned_items = data.get('aligned_items', [])
        category_summaries = data.get('category_summaries', [])
        totals = data.get('totals', {})

        # Create workbook
        wb = openpyxl.Workbook()

        # -- Sheet 1: Side-by-Side Comparison --
        ws = wb.active
        ws.title = 'Proposal Comparison'

        # Styles
        header_fill = PatternFill(start_color='1B2838', end_color='1B2838', fill_type='solid')
        header_font = Font(color='D6A84A', bold=True, size=11)
        gold_fill = PatternFill(start_color='D6A84A', end_color='D6A84A', fill_type='solid')
        gold_font = Font(color='1B2838', bold=True, size=12)
        low_fill = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
        high_fill = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')
        total_fill = PatternFill(start_color='D6A84A', end_color='D6A84A', fill_type='solid')
        total_font = Font(color='1B2838', bold=True, size=11)
        border = Border(
            left=Side(style='thin', color='555555'),
            right=Side(style='thin', color='555555'),
            top=Side(style='thin', color='555555'),
            bottom=Side(style='thin', color='555555'),
        )
        money_fmt = '$#,##0.00'
        pct_fmt = '0.0%'

        # Title row
        prop_ids = [p.get('id', p.get('filename', f'Proposal {i+1}')) for i, p in enumerate(proposals)]
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=3 + len(prop_ids))
        title_cell = ws.cell(row=1, column=1, value='AEGIS Proposal Comparison')
        title_cell.fill = gold_fill
        title_cell.font = gold_font
        title_cell.alignment = Alignment(horizontal='center')

        # Header row
        headers = ['Line Item', 'Category'] + prop_ids + ['Variance']
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=h)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', wrap_text=True)
            cell.border = border

        # Data rows
        row_num = 4
        for item in aligned_items:
            ws.cell(row=row_num, column=1, value=item.get('description', '')).border = border
            ws.cell(row=row_num, column=2, value=item.get('category', '')).border = border

            amounts = item.get('amounts', {})
            valid_amounts = [a for a in amounts.values() if a is not None and a > 0]
            min_amount = min(valid_amounts) if valid_amounts else None
            max_amount = max(valid_amounts) if valid_amounts else None

            for p_idx, pid in enumerate(prop_ids):
                col = 3 + p_idx
                amount = amounts.get(pid)
                cell = ws.cell(row=row_num, column=col)
                cell.border = border
                cell.alignment = Alignment(horizontal='right')
                if amount is not None:
                    cell.value = amount
                    cell.number_format = money_fmt
                    # Highlight lowest green, highest red
                    if len(valid_amounts) > 1:
                        if amount == min_amount:
                            cell.fill = low_fill
                        elif amount == max_amount:
                            cell.fill = high_fill
                else:
                    cell.value = '—'
                    cell.alignment = Alignment(horizontal='center')

            # Variance column
            variance_col = 3 + len(prop_ids)
            cell = ws.cell(row=row_num, column=variance_col)
            cell.border = border
            cell.alignment = Alignment(horizontal='right')
            variance_pct = item.get('variance_pct')
            if variance_pct is not None:
                cell.value = variance_pct / 100
                cell.number_format = pct_fmt
            else:
                cell.value = '—'
                cell.alignment = Alignment(horizontal='center')

            row_num += 1

        # Total row
        row_num += 1
        total_cell = ws.cell(row=row_num, column=1, value='GRAND TOTAL')
        total_cell.fill = total_fill
        total_cell.font = total_font
        total_cell.border = border
        ws.cell(row=row_num, column=2, value='').fill = total_fill
        ws.cell(row=row_num, column=2).border = border

        for p_idx, pid in enumerate(prop_ids):
            col = 3 + p_idx
            cell = ws.cell(row=row_num, column=col)
            total_val = totals.get(pid)
            if total_val is not None:
                cell.value = total_val
                cell.number_format = money_fmt
            else:
                cell.value = '—'
            cell.fill = total_fill
            cell.font = total_font
            cell.border = border
            cell.alignment = Alignment(horizontal='right')

        # Variance on total
        variance_col = 3 + len(prop_ids)
        cell = ws.cell(row=row_num, column=variance_col)
        cell.fill = total_fill
        cell.font = total_font
        cell.border = border
        total_variance = data.get('total_variance_pct')
        if total_variance is not None:
            cell.value = total_variance / 100
            cell.number_format = pct_fmt
        else:
            cell.value = '—'

        # Column widths
        ws.column_dimensions['A'].width = 40
        ws.column_dimensions['B'].width = 15
        for p_idx in range(len(prop_ids)):
            col_letter = openpyxl.utils.get_column_letter(3 + p_idx)
            ws.column_dimensions[col_letter].width = 20
        ws.column_dimensions[openpyxl.utils.get_column_letter(variance_col)].width = 12

        # -- Sheet 2: Category Summary --
        ws2 = wb.create_sheet('Category Summary')
        cat_headers = ['Category', 'Items'] + prop_ids
        for col, h in enumerate(cat_headers, 1):
            cell = ws2.cell(row=1, column=col, value=h)
            cell.fill = header_fill
            cell.font = header_font
            cell.border = border

        for row_idx, cat in enumerate(category_summaries, 2):
            ws2.cell(row=row_idx, column=1, value=cat.get('category', '')).border = border
            ws2.cell(row=row_idx, column=2, value=cat.get('item_count', 0)).border = border
            cat_totals = cat.get('totals', {})
            for p_idx, pid in enumerate(prop_ids):
                cell = ws2.cell(row=row_idx, column=3 + p_idx)
                val = cat_totals.get(pid, 0)
                cell.value = val if val else '—'
                if isinstance(val, (int, float)) and val > 0:
                    cell.number_format = money_fmt
                cell.border = border

        ws2.column_dimensions['A'].width = 20
        ws2.column_dimensions['B'].width = 10
        for p_idx in range(len(prop_ids)):
            col_letter = openpyxl.utils.get_column_letter(3 + p_idx)
            ws2.column_dimensions[col_letter].width = 20

        # -- Sheet 3: Proposal Details --
        ws3 = wb.create_sheet('Proposal Details')
        detail_headers = ['Field'] + prop_ids
        for col, h in enumerate(detail_headers, 1):
            cell = ws3.cell(row=1, column=col, value=h)
            cell.fill = header_fill
            cell.font = header_font
            cell.border = border

        detail_fields = [
            ('Company', 'company_name'),
            ('Title', 'proposal_title'),
            ('Date', 'date'),
            ('File', 'filename'),
            ('Type', 'file_type'),
            ('Tables Found', 'table_count'),
            ('Line Items', 'line_item_count'),
            ('Grand Total', 'total_raw'),
        ]

        for row_idx, (label, key) in enumerate(detail_fields, 2):
            ws3.cell(row=row_idx, column=1, value=label).border = border
            for p_idx, p in enumerate(proposals):
                cell = ws3.cell(row=row_idx, column=2 + p_idx, value=str(p.get(key, '')))
                cell.border = border

        ws3.column_dimensions['A'].width = 15
        for p_idx in range(len(prop_ids)):
            col_letter = openpyxl.utils.get_column_letter(2 + p_idx)
            ws3.column_dimensions[col_letter].width = 30

        # Save to temp file
        temp_path = os.path.join(tempfile.gettempdir(), 'aegis_proposal_comparison.xlsx')
        wb.save(temp_path)

        return send_file(
            temp_path,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='AEGIS_Proposal_Comparison.xlsx'
        )

    except Exception as e:
        logger.error(f'Proposal export error: {e}', exc_info=True)
        return jsonify({
            'success': False,
            'error': {'message': f'Export error: {str(e)}', 'traceback': traceback.format_exc()}
        }), 500
