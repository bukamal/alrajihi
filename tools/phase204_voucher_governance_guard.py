# -*- coding: utf-8 -*-
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def text(rel):
    return (ROOT / rel).read_text(encoding='utf-8')

def require(cond, msg):
    if not cond:
        raise SystemExit(msg)

fin = text('alrajhi_client/core/services/finance_operation_policy.py')
for token in ['OP_VOUCHER_CREATE', 'OP_VOUCHER_EDIT', 'OP_VOUCHER_DELETE', 'OP_VOUCHER_PRINT', 'OP_VOUCHER_VIEW']:
    require(token in fin, f'missing {token} in finance_operation_policy')
for setting in ['allow_voucher_create', 'allow_voucher_edit', 'allow_voucher_delete', 'allow_voucher_print', 'allow_voucher_view']:
    require(setting in fin, f'missing {setting} in finance_operation_policy')

perm = text('alrajhi_client/core/services/permission_service.py')
for action in ['ACTION_VOUCHER_CREATE', 'ACTION_VOUCHER_EDIT', 'ACTION_VOUCHER_DELETE', 'ACTION_VOUCHER_PRINT', 'ACTION_VOUCHER_VIEW']:
    require(action in perm, f'missing {action}')
for code in ['finance.voucher.create', 'finance.voucher.edit', 'finance.voucher.delete', 'finance.voucher.print', 'finance.voucher.view']:
    require(code in perm, f'missing permission mapping {code}')

svc = text('alrajhi_client/core/services/voucher_service.py')
for op in ['voucher_create', 'voucher_edit', 'voucher_delete', 'voucher_view']:
    require(op in svc, f'VoucherService does not require {op}')
require('finance_operation_policy' not in svc.split('\n')[:15], 'VoucherService should not import policy eagerly at module top')

widget = text('alrajhi_client/views/widgets/vouchers_widget.py')
require('finance_operation_policy.require(finance_operation_policy.OP_VOUCHER_DELETE' in widget, 'delete action is not policy guarded')
require('finance_operation_policy.require(finance_operation_policy.OP_VOUCHER_PRINT' in widget, 'print action is not policy guarded')
require('finance_operation_policy.require(finance_operation_policy.OP_VOUCHER_CREATE' in widget, 'add action is not policy guarded')
require('current_source_row' in widget, 'voucher selection must use current_source_row')
require('self.model.get_id(rows[0].row())' not in widget, 'legacy proxy-unsafe voucher selection remains')

tab = text('alrajhi_client/features/vouchers/voucher_editor_tab.py')
require('finance_operation_policy.require(self._operation_for_save()' in tab, 'VoucherEditorTab save not policy guarded')
require('OP_VOUCHER_PRINT' in tab, 'VoucherEditorTab print/export not policy guarded')
require('_apply_operation_state' in tab, 'VoucherEditorTab lacks read-only operation state')

print('phase204 voucher governance guard passed')
