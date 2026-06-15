from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
client = (ROOT / 'alrajhi_client/database/connection.py').read_text(encoding='utf-8')
server = (ROOT / 'alrajhi_server/api/invoices.py').read_text(encoding='utf-8')

errors = []

# Local hard guards: لا تعتمد فقط على طبقة UI/service.
for marker in [
    'لا يمكن تعديل فاتورة مرتبطة بمرتجعات',
    'لا يمكن حذف فاتورة مرتبطة بمرتجعات',
]:
    if marker not in client:
        errors.append(f'missing local returns guard: {marker}')

if 'if self._invoice_has_returns(invoice_id):' not in client:
    errors.append('local update/delete does not call _invoice_has_returns')

# Server payment metadata persistence.
required_insert = 'cashbox_id, bank_account_id, payment_method, shift_id'
if required_insert not in server:
    errors.append('server invoice INSERT does not persist cashbox/bank/payment/shift metadata')

required_update = 'cashbox_id=?, bank_account_id=?, payment_method=?, shift_id=?'
if required_update not in server:
    errors.append('server invoice UPDATE does not persist cashbox/bank/payment/shift metadata')

for field in ["data.get('cashbox_id')", "data.get('bank_account_id')", "data.get('payment_method', 'cash')", "data.get('shift_id')"]:
    if field not in server:
        errors.append(f'server missing invoice payment field mapping: {field}')

# Server stock guard for sale invoices.
if 'def _assert_sale_stock_available' not in server:
    errors.append('server missing stock availability helper')
if "if data.get('type') == 'sale':" not in server or '_assert_sale_stock_available(db, user_id, data.get(\'lines\', []))' not in server:
    errors.append('server sale invoice stock guard is not called')
if 'المطلوب {required_qty} والمتاح {available}' not in server:
    errors.append('server stock error does not include required/available quantities')
if 'except ValueError as e:' not in server:
    errors.append('server stock validation errors are not returned as 400')

# Ensure update stock validation occurs after reversing old movements, not before.
update_section = server[server.find('def update_invoice'):server.find("@invoices_bp.route('/invoices/<int:invoice_id>', methods=['DELETE'])")]
if update_section:
    pos_delete_mov = update_section.find("DELETE FROM inventory_movements")
    pos_assert = update_section.find("_assert_sale_stock_available")
    if pos_delete_mov == -1 or pos_assert == -1 or pos_assert < pos_delete_mov:
        errors.append('server update stock guard must run after reversing the old invoice movements')
else:
    errors.append('server update_invoice section not found')

if errors:
    print('invoice_phase108_integrity_guard: FAIL')
    for e in errors:
        print('-', e)
    raise SystemExit(1)
print('invoice_phase108_integrity_guard: PASS')
