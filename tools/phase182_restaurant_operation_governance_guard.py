# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')

checks = []

policy = read('alrajhi_client/core/services/restaurant_operation_policy.py')
checks.append(('RestaurantOperationPolicy class exists', 'class RestaurantOperationPolicy' in policy))
for key in ['OP_ADD_LINE', 'OP_SEND_KITCHEN', 'OP_ADJUST_BILL', 'OP_RECORD_PAYMENT', 'OP_CHECKOUT']:
    checks.append((f'{key} exists', key in policy))
checks.append(('policy uses settings_service', 'settings_service.get_bool' in policy and 'get_restaurant_settings' in policy))
checks.append(('policy uses permission_service', 'permission_service.can' in policy))
checks.append(('policy audits operations', 'audit_service.log' in policy))

service = read('alrajhi_client/core/services/restaurant_service.py')
checks.append(('RestaurantService imports policy', 'restaurant_operation_policy' in service))
for call in ['OP_ADD_LINE', 'OP_SEND_KITCHEN', 'OP_ADJUST_BILL', 'OP_RECORD_PAYMENT', 'OP_CHECKOUT']:
    checks.append((f'RestaurantService requires {call}', f'require(restaurant_operation_policy.{call})' in service))

widget = read('alrajhi_client/views/restaurant/restaurant_pos_widget.py')
checks.append(('RestaurantPOSWidget imports policy', 'restaurant_operation_policy' in widget))
checks.append(('RestaurantPOSWidget has operation state', '_apply_restaurant_operation_state' in widget))
checks.append(('RestaurantPOSWidget has require helper', '_require_restaurant_operation' in widget))

settings = read('alrajhi_client/core/services/settings_service.py')
checks.append(('SettingsService has get_restaurant_settings', 'def get_restaurant_settings' in settings))
for key in ['restaurant/operations/allow_add_line', 'restaurant/operations/allow_send_kitchen', 'restaurant/operations/allow_checkout']:
    checks.append((f'settings key {key}', key in settings))

perm = read('alrajhi_client/core/services/permission_service.py')
for action in ['ACTION_USE_RESTAURANT', 'ACTION_RESTAURANT_ADD_LINE', 'ACTION_RESTAURANT_CHECKOUT']:
    checks.append((f'permission constant {action}', action in perm))
for perm_key in ['restaurant.use', 'restaurant.line.add', 'restaurant.checkout']:
    checks.append((f'permission map {perm_key}', perm_key in perm))

rbac = read('alrajhi_client/core/services/rbac_service.py')
for perm_key in ['restaurant.use', 'restaurant.kitchen.send', 'restaurant.payment.record', 'restaurant.checkout']:
    checks.append((f'RBAC default/map {perm_key}', perm_key in rbac))

for rel in ['alrajhi_client/database/migrations.py', 'alrajhi_server/database/migrations.py']:
    mig = read(rel)
    checks.append((f'{rel} has restaurant permissions', 'Phase182: Restaurant operation-level permissions' in mig and 'restaurant.checkout' in mig))

tr = read('alrajhi_client/i18n/translator.py')
checks.append(('Phase182 translations exist', '_PHASE182_TRANSLATIONS' in tr and 'restaurant_operation_denied' in tr))

failed = [name for name, ok in checks if not ok]
if failed:
    print('Phase182 restaurant operation governance guard failed:')
    for name in failed:
        print(' -', name)
    raise SystemExit(1)
print('Phase182 restaurant operation governance guard passed.')
