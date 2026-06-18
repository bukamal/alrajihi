# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')

def assert_contains(rel, text):
    content = read(rel)
    if text not in content:
        raise AssertionError(f"Missing {text!r} in {rel}")

def assert_not_contains(rel, text):
    content = read(rel)
    if text in content:
        raise AssertionError(f"Forbidden {text!r} in {rel}")

assert_contains('alrajhi_client/core/services/party_operation_policy.py', 'class PartyOperationPolicy')
assert_contains('alrajhi_client/core/services/settings_service.py', 'def get_party_settings')
assert_contains('alrajhi_client/core/services/entity_service.py', 'OP_CUSTOMER_CREATE')
assert_contains('alrajhi_client/core/services/entity_service.py', 'OP_SUPPLIER_EDIT')
assert_contains('alrajhi_client/features/parties/party_editor_tab.py', 'party_operation_policy')
assert_contains('alrajhi_client/views/widgets/customers_widget.py', 'current_source_row')
assert_contains('alrajhi_client/views/widgets/suppliers_widget.py', 'current_source_row')
assert_not_contains('alrajhi_client/views/widgets/customers_widget.py', 'AddEntityDialog')
assert_not_contains('alrajhi_client/views/widgets/suppliers_widget.py', 'AddEntityDialog')
assert_contains('alrajhi_client/core/services/permission_service.py', 'ACTION_CUSTOMER_CREATE')
assert_contains('alrajhi_client/core/services/rbac_service.py', 'customers.create')
assert_contains('alrajhi_client/i18n/translator.py', 'Phase207 party governance translations')
print('phase207_party_governance_guard passed')
