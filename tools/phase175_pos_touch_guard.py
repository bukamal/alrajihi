# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


pos_widget = read('alrajhi_client/views/widgets/pos_widget.py')
pos_service = read('alrajhi_client/core/services/pos_service.py')
settings_service = read('alrajhi_client/core/services/settings_service.py')
translator = read('alrajhi_client/i18n/translator.py')
preferences = read('alrajhi_client/features/pos/pos_preferences.py')

assert_true('QSettings' not in pos_widget, 'POSWidget must not use QSettings directly')
assert_true('settings_service.set(' in preferences, 'POS preferences must persist through settings_service')
assert_true('UserSession.get_current_user_id' in preferences, 'POS preferences must be scoped per user')
assert_true('get_current_branch_id' in preferences, 'POS preferences must be scoped per branch')
assert_true('get_active_profile' in preferences, 'POS preferences must be scoped per active settings profile')

assert_true('barcode_input_service.lookup_entry' in pos_service, 'POSService must use unified barcode input service')
assert_true('product_service.items(search=code' not in pos_service, 'POS scan must not fall back to first text-search result')
assert_true('matched_unit' in pos_service, 'POSService must support matched unit barcodes')
assert_true('conversion_factor' in pos_service and 'base_qty' in pos_service, 'POS lines must carry conversion_factor/base_qty')
assert_true('remove_line_at' in pos_service, 'POS must support removing a specific row, not all item units')

assert_true('get_pos_settings' in settings_service, 'SettingsService must expose POS settings contract')
assert_true('ACTION_USE_POS' in read('alrajhi_client/core/services/permission_service.py'), 'PermissionService must expose ACTION_USE_POS')
assert_true("'use_pos': 'pos.use'" in read('alrajhi_client/core/services/rbac_service.py'), 'RBAC must map POS use permission')

for key in (
    'pos_density', 'pos_density_touch', 'pos_barcode_not_found', 'pos_search_ambiguous',
    'pos_insufficient_stock', 'pos_cannot_checkout_empty'
):
    assert_true(key in translator, f'Missing POS translation key: {key}')

print('phase175_pos_touch_guard: OK')
