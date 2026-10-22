"""Read STANTEX PDF or XLSX packing lists using the existing export model."""
from pathlib import Path
from decimal import Decimal
import re
import openpyxl
from extractor import Roll, ExtractionResult, combine_packages, extract_pdf

ZERO = Decimal('0')

def text(value):
    return '' if value is None else ' '.join(str(value).split())

def number(value):
    if value is None or isinstance(value, bool):
        raise ValueError('Missing or invalid numeric value')
    result = Decimal(str(value).replace(',', '').strip())
    if not result.is_finite() or result < ZERO:
        raise ValueError('Invalid negative or non-finite value')
    return result

def extract_excel(path):
    workbook = openpyxl.load_workbook(path, data_only=True, read_only=True)
    rows = []
    totals = {}
    review_notes = []
    try:
        for sheet in workbook:
            invoice = po = item = ''
            columns = None
            awaiting_item = False
            for line, values in enumerate(sheet.iter_rows(values_only=True), 1):
                cells = [text(v) for v in values]
                joined = ' '.join(cells)
                match = re.search(r'Invoice\s*(?:no\.?)?\s*:\s*(SIN[\w-]+)', joined, re.I)
                if match:
                    if invoice != match[1]:
                        po = item = ''
                        awaiting_item = False
                    invoice = match[1]

                if 'PACKAGE NO.' in cells and 'QUANTITY' in cells:
                    columns = {}
                    for key, label in [('package','PACKAGE NO.'), ('description','DESCRIPTION'), ('quantity','QUANTITY'), ('nw','N.W.'), ('gw','G.W.'), ('lot','LOT NO.')]:
                        found = [i for i,c in enumerate(cells) if c == label or c.startswith(label + ' ')]
                        if len(found) != 1:
                            raise ValueError(f'{sheet.title} row {line}: missing/ambiguous {label} column')
                        columns[key] = found[0]
                    continue
                if columns is None:
                    continue
                def get(key):
                    idx = columns[key]
                    return values[idx] if idx < len(values) else None
                desc = text(get('description'))
                match = re.search(r'CUSTOMER\s+P/O\s+NO\.\s*(\S+)', desc, re.I)
                if match:
                    po = match[1]
                    awaiting_item = True
                    continue
                if awaiting_item and desc:
                    if desc.upper().startswith('COL:'):
                        awaiting_item = False
                    elif not any(text(get(key)) for key in ('package', 'quantity', 'nw', 'gw', 'lot')):
                        if desc.upper().startswith(('CUTTABLE WIDTH', 'FABRICS', 'TOTAL')):
                            raise ValueError(f'{sheet.title} row {line}: expected item code or package row')
                        item = desc
                        awaiting_item = False
                if desc.upper().startswith('COL:'):
                    try:
                        package = text(get('package'))
                        lot = text(get('lot'))
                        color = desc.split(':', 1)[1].strip()
                        # Blank package numbers are permitted only for a matching
                        # weightless continuation of the immediately previous roll.
                        if not package and get('nw') is None and get('gw') is None and rows:
                            previous = rows[-1]
                            if (previous.invoice, previous.purchase_order, previous.item,
                                previous.color, previous.lot) == (invoice, po, item, color, lot):
                                package = previous.package
                                review_notes.append(f"{sheet.title} row {line}: blank package assigned to {package} (matching FOC continuation).")
                        if not all((invoice, po, item, package, lot, color)):
                            raise ValueError('Missing invoice, PO, item, package, LOT or color')
                        unit_idx = columns['quantity'] + 1
                        unit_area = cells[unit_idx:columns['nw']]
                        if 'YDS' not in unit_area:
                            raise ValueError('Only YDS quantities are supported')
                        qty = number(get('quantity'))
                        nw = None if get('nw') is None else number(get('nw'))
                        gw = None if get('gw') is None else number(get('gw'))
                        if (nw is None) != (gw is None):
                            raise ValueError('Only one weight is present')
                        if nw is not None and gw < nw:
                            raise ValueError('G.W is less than N.W')
                        rows.append(Roll(
                            invoice=invoice, purchase_order=po, item=item,
                            color=color, lot=lot, package=package, quantity=qty,
                            net_weight=nw, gross_weight=gw,
                            source_pages=[],
                            foc_quantity=qty if nw is None else ZERO,
                        ))
                    except Exception as error:
                        raise ValueError(f'{sheet.title} row {line}: {error}') from error
                match = re.search(r'TOTAL\s*:\s*([\d,]+)\s+ROLL\(S\)\s+([\d,.]+)\s*YDS', joined, re.I)
                if match:
                    expected = (int(match[1].replace(',', '')), number(match[2]), number(get('nw')), number(get('gw')))
                    if invoice in totals and totals[invoice] != expected:
                        raise ValueError(f'{invoice}: conflicting totals')
                    totals[invoice] = expected
    finally:
        workbook.close()
    if not rows:
        raise ValueError('No STANTEX packing-list rows found. Select the original source XLSX, not a converted output workbook.')
    raw_count = len(rows)
    rows = combine_packages(rows)
    warnings = list(review_notes)
    checked = []
    for invoice in dict.fromkeys(r.invoice for r in rows):
        subset = [r for r in rows if r.invoice == invoice]
        actual = (len(subset), sum((r.quantity for r in subset),ZERO), sum((r.net_weight or ZERO for r in subset),ZERO), sum((r.gross_weight or ZERO for r in subset),ZERO))
        if invoice not in totals:
            warnings.append(f'{invoice}: printed totals not found; review before export.')
        elif actual != totals[invoice]:
            raise ValueError(f'{invoice}: roll/quantity/weight totals mismatch. Expected {totals[invoice]}, extracted {actual}')
        else:
            checked.append(invoice)
    for row in rows:
        if row.net_weight is None:
            warnings.append(f'{row.invoice}, package {row.package}: no weighted base row found.')
    return ExtractionResult(rows=rows, page_count=0, raw_row_count=raw_count, checked_invoices=checked, warnings=warnings)

def extract_input(path):
    path = Path(path)
    if path.suffix.lower() == '.pdf':
        return extract_structural_pdf(path)
    if path.suffix.lower() == '.xlsx':
        return extract_excel(path)
    raise ValueError('Supported input formats: PDF and XLSX. Save legacy XLS files as XLSX first.')


def extract_structural_pdf(path):
    import pdfplumber
    rows = []
    totals = {}
    review_notes = []
    invoice = po = item = ''
    awaiting = False
    previous = None
    with pdfplumber.open(path) as document:
        pages = len(document.pages)
        for page_number, page in enumerate(document.pages, 1):
            content = page.extract_text() or ''
            if not content.strip() and page.images:
                raise ValueError(f'Page {page_number}: image-only content requires OCR')
            for raw in content.splitlines():
                line = text(raw)
                if not line:
                    continue
                match = re.search(r'Invoice\s*(?:no\.?)?\s*:?\s*(SIN[\w-]+)', line, re.I)
                if match:
                    if invoice != match[1]:
                        po = item = ''
                        awaiting = False
                    invoice = match[1]
                    continue
                match = re.search(r'P/I\s+NO\.\s*(\S+)\s*,\s*CUSTOMER\s+P/O\s+NO\.\s*(\S+)', line, re.I)
                if match:
                    po = match[2]
                    awaiting = True
                    previous = None
                    continue
                match = re.match(r'^(?:(\S+)\s+)?COL:\s*(.*?)\s+([\d,.]+)\s+YDS\s+(.+)$', line, re.I)
                if match:
                    awaiting = False
                    if not all((invoice, po, item)):
                        raise ValueError(f'Page {page_number}: missing invoice, PO or item')
                    package, color, qty, tail = match.groups()
                    fields = tail.split()
                    if len(fields) not in (1, 3):
                        raise ValueError(f'Page {page_number}: unrecognized weight/LOT fields')
                    nw, gw = (number(fields[0]), number(fields[1])) if len(fields)==3 else (None, None)
                    if not package:
                        base = rows[-1] if rows else None
                        if (nw is None and gw is None and base is not None
                            and (base.invoice, base.purchase_order, base.item,
                                 base.color, base.lot) == (invoice, po, item, color, fields[-1])):
                            package = base.package
                            review_notes.append(f"Page {page_number}: blank package assigned to {package} (matching FOC continuation).")
                        else:
                            raise ValueError(f'Page {page_number}: blank package has no matching weightless continuation')
                    if nw is not None and gw < nw:
                        raise ValueError(f'Page {page_number}: G.W is less than N.W')
                    quantity = number(qty)
                    previous = Roll(invoice=invoice, purchase_order=po, item=item, color=color,
                        lot=fields[-1], package=package, quantity=quantity,
                        net_weight=nw, gross_weight=gw, source_pages=[page_number],
                        foc_quantity=quantity if nw is None else ZERO)
                    rows.append(previous)
                    continue
                if 'COL:' in line.upper():
                    raise ValueError(f'Page {page_number}: unsupported package row: {line}')
                match = re.search(r'TOTAL\s*:?[ ]*([\d,]+)\s+ROLL\(S\)\s+([\d,.]+)\s*YDS', line, re.I)
                if match:
                    weight_fields = line[match.end():].strip().split()
                    weights = []
                    for token in weight_fields[:2]:
                        try:
                            weights.append(number(token))
                        except Exception:
                            weights.append(None)
                    weights += [None] * (2 - len(weights))
                    expected = (int(match[1].replace(',', '')), number(match[2]), *weights)
                    if invoice in totals and totals[invoice] != expected:
                        raise ValueError(f'Page {page_number}: conflicting totals for {invoice}')
                    totals[invoice] = expected
                    awaiting = False
                    previous = None
                    continue
                # Repeated page furniture does not change the active item/order.
                if line.upper().startswith(('PACKING LIST', 'MESSRS.', 'PACKAGE', 'NO. (KGS)', 'PAGE', 'DATE', 'STANTEX CORPORATION')):
                    continue
                if awaiting:
                    if line.upper().startswith(('FABRICS', 'CUTTABLE WIDTH')):
                        raise ValueError(f'Page {page_number}: expected item code after order heading')
                    item = line
                    awaiting = False
                    continue
                if previous and ('X-DYE' in line or line == 'DYE'):
                    if not previous.color.endswith(line):
                        previous.color += ('' if previous.color.endswith('-') else ' ') + line
    if not rows:
        raise ValueError('No supported text packing-list rows found')
    count = len(rows)
    rows = combine_packages(rows)
    checked = []
    warnings = list(review_notes)
    for inv in dict.fromkeys(r.invoice for r in rows):
        subset = [r for r in rows if r.invoice == inv]
        actual = (len(subset), sum((r.quantity for r in subset), ZERO))
        if inv not in totals:
            warnings.append(f'{inv}: printed totals not found; review before export')
        elif actual != totals[inv][:2]:
            raise ValueError(f'{inv}: totals mismatch: expected {totals[inv]}, extracted {actual}')
        else:
            for label, field, expected in zip(('N.W', 'G.W'), ('net_weight', 'gross_weight'), totals[inv][2:]):
                if expected is None:
                    warnings.append(f'{inv}: printed {label} total missing or unreadable; weight total could not be verified.')
                    continue
                if any(getattr(r, field) is None for r in subset):
                    raise ValueError(f'{inv}: {label} cannot be verified because package weights are missing')
                measured = sum((getattr(r, field) for r in subset), ZERO)
                if measured != expected:
                    raise ValueError(f'{inv}: {label} total mismatch: expected {expected}, extracted {measured}')
            checked.append(inv)
    for r in rows:
        if r.net_weight is None:
            warnings.append(f'{r.invoice}, package {r.package}: no weighted base row found')
    return ExtractionResult(rows=rows, page_count=pages, raw_row_count=count,
                            checked_invoices=checked, warnings=warnings)
