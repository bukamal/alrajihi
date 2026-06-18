# -*- coding: utf-8 -*-
"""Phase 178 guard: POS operation governance and permissions."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')

def require(condition, message):
    if not condition:
        print(f"FAIL: {message}")
        sys.exit(1)

policy = read('alrajhi_client/core/services/pos_operation_policy.py')
widget = read('alrajhi_client/views/widgets/pos_widget.py')
service = read('alrajhi_client/core/services/pos_service.py')
perms = read('alrajhi_client/core/services/permission_service.py')
rbacks = read('alrajhi_client/core/services/rbac_service.py')
settings = read('alrajhi_client/core/services/settings_service.py')
translations = read('alrajhi_client/i18n/translator.py')
client_migrations = read('alrajhi_client/database/migrations.py')
server_migrations = read('alrajhi_server/database/migrations.py')

require('class POSOperationPolicy' in policy, 'POSOperationPolicy missing')
for op in ['OP_CHECKOUT','OP_SUSPEND','OP_RESUME','OP_REMOVE_LINE','OP_CLEAR_CART','OP_OPEN_SHIFT','OP_CLOSE_SHIFT','OP_PRINT_RECEIPT']:
    require(op in policy, f'{op} missing in POSOperationPolicy')

require('from core.services.pos_operation_policy import pos_operation_policy' in widget, 'POSWidget must import core POS operation policy')
require('def _require_pos_operation' in widget, 'POSWidget must enforce operations through helper')
for method_guard in [
    'OP_OPEN_SHIFT', 'OP_CLOSE_SHIFT', 'OP_REMOVE_LINE', 'OP_CLEAR_CART',
    'OP_SUSPEND', 'OP_RESUME', 'OP_CHECKOUT', 'OP_PRINT_RECEIPT'
]:
    require(method_guard in widget, f'POSWidget missing guard for {method_guard}')

require('from core.services.pos_operation_policy import pos_operation_policy' in service, 'POSService must import operation policy')
require('def _require_operation' in service, 'POSService must enforce operation policy at service level')
for permission in ['ACTION_POS_SUSPEND','ACTION_POS_RESUME','ACTION_POS_REMOVE_LINE','ACTION_POS_CLEAR_CART','ACTION_POS_OPEN_SHIFT','ACTION_POS_CLOSE_SHIFT','ACTION_POS_PRINT_RECEIPT']:
    require(permission in perms, f'{permission} missing in PermissionService')
for key in ['pos.suspend','pos.resume','pos.line.remove','pos.cart.clear','pos.shift.open','pos.shift.close','pos.receipt.print']:
    require(key in rbacks, f'{key} missing in RBAC service')
    require(key in client_migrations, f'{key} missing in client migrations')
    require(key in server_migrations, f'{key} missing in server migrations')
for setting in ['allow_suspend','allow_resume','allow_remove_line','allow_clear_cart','allow_print_receipt']:
    require(setting in settings, f'{setting} missing in get_pos_settings operations contract')
for tr_key in ['pos_operation_checkout','pos_operation_disabled_by_settings','pos_operation_denied','pos_operation_governance_unified']:
    require(tr_key in translations, f'{tr_key} translation missing')
require('features.pos.pos_operation_policy' not in widget + service, 'POS operation policy must not live under features for core enforcement')
print('phase178_pos_operation_governance_guard passed')
