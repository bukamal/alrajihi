from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
issues = []

invoices = (root / 'alrajhi_client/views/widgets/invoices_widget.py').read_text(encoding='utf-8')
returns = (root / 'alrajhi_client/views/widgets/returns_widget.py').read_text(encoding='utf-8')
dialog = (root / 'alrajhi_client/views/dialogs/invoice_dialog.py').read_text(encoding='utf-8')

# External management tabs must not expose line-item columns.
external_bad = {'barcode','item_name','quantity','unit','unit_price','line_total','line_notes','item_profit'}
for source_name, source in [('invoices_widget.py', invoices), ('returns_widget.py', returns)]:
    for m in re.finditer(r"data_keys=\[([^\]]+)\]", source, flags=re.S):
        keys = set(re.findall(r"'([^']+)'", m.group(1)))
        bad = sorted(keys & external_bad)
        if bad:
            issues.append(f'{source_name} external table contains line columns: {bad}')

# Invoice dialog line defaults should expose only requested logical line columns.
required_sale = {'COL_BARCODE','COL_ITEM_NAME','COL_QUANTITY','COL_UNIT','COL_PRICE','COL_TOTAL','COL_NOTES','COL_PROFIT'}
required_purchase = {'COL_BARCODE','COL_ITEM_NAME','COL_UNIT','COL_QUANTITY','COL_PRICE','COL_TOTAL','COL_NOTES'}
for label, required in [('sale', required_sale), ('purchase', required_purchase)]:
    pattern = r"if self\.inv_type == 'sale':\s*return \{([^}]+)\}" if label == 'sale' else r"return \{([^}]+)\}\s*\n\s*def _restore_lines_table_layout"
    match = re.search(pattern, dialog, flags=re.S)
    if not match:
        issues.append(f'{label} invoice dialog default columns block missing')
        continue
    cols = set(re.findall(r'LinesModel\.(COL_[A-Z_]+)', match.group(1)))
    missing = sorted(required - cols)
    if missing:
        issues.append(f'{label} invoice dialog missing logical columns: {missing}')
    hidden_by_default = {'COL_DISCOUNT','COL_TAX'} & cols
    if hidden_by_default:
        issues.append(f'{label} invoice dialog shows technical columns by default: {sorted(hidden_by_default)}')

# Return dialogs must include return-specific validation columns and no always-visible unit combobox.
for text in ['sold_qty', 'purchased_qty', 'previous_returned', 'returnable_qty', 'unit', 'return_qty', 'price', 'total', 'notes']:
    if text not in returns:
        issues.append(f'return dialogs missing {text}')
if 'setCellWidget' in returns and 'QComboBox' in returns:
    issues.append('return unit column appears to use persistent cell widget')
if 'ReturnUnitDelegate(QStyledItemDelegate)' not in returns:
    issues.append('return unit delegate missing')

if issues:
    print('PHASE137_LOGICAL_COLUMNS_GUARD: FAIL')
    for issue in issues:
        print('-', issue)
    raise SystemExit(1)
print('PHASE137_LOGICAL_COLUMNS_GUARD: PASS')
