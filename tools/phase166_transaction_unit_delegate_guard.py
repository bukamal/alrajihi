# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors = []

delegate = ROOT / 'alrajhi_client/features/transactions/grids/transaction_unit_delegate.py'
grid = ROOT / 'alrajhi_client/features/transactions/grids/transaction_line_grid.py'
model = ROOT / 'alrajhi_client/features/transactions/grids/transaction_line_model.py'

if not delegate.exists():
    errors.append('transaction_unit_delegate.py is missing')
else:
    text = delegate.read_text(encoding='utf-8')
    if 'class TransactionUnitDelegate(QStyledItemDelegate)' not in text:
        errors.append('TransactionUnitDelegate class is missing')
    if 'set_unit' not in text:
        errors.append('TransactionUnitDelegate must delegate changes to model.set_unit')

grid_text = grid.read_text(encoding='utf-8')
if 'setItemDelegateForColumn(unit_col, TransactionUnitDelegate(self))' not in grid_text:
    errors.append('TransactionLineGrid does not install TransactionUnitDelegate for unit column')

model_text = model.read_text(encoding='utf-8')
for token in ('def unit_options_for_row', 'def set_unit', 'returnable_qty_base', 'quantity_in_base'):
    if token not in model_text:
        errors.append(f'missing unit-aware token: {token}')

if errors:
    raise SystemExit('\n'.join(errors))
print('phase166 transaction unit delegate guard: OK')
