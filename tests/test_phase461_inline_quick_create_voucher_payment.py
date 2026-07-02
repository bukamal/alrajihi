from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'alrajhi_client' / 'ui' / 'inline_quick_create_registry.py'
PANEL = ROOT / 'alrajhi_client' / 'ui' / 'inline_quick_create.py'
VOUCHER_LINK = ROOT / 'alrajhi_client' / 'features' / 'vouchers' / 'components' / 'voucher_link.py'
VOUCHER_PAYMENT = ROOT / 'alrajhi_client' / 'features' / 'vouchers' / 'components' / 'voucher_payment.py'
TRANSLATOR = ROOT / 'alrajhi_client' / 'i18n' / 'translator.py'


def test_phase461_registry_extends_inline_quick_create_to_payment_targets():
    source = REGISTRY.read_text(encoding='utf-8')
    for entity in ('cashbox', 'bank_account'):
        assert f'"{entity}": QuickCreateDefinition' in source
    assert 'permission_operation="cashbox_create"' in source
    assert 'permission_operation="bank_create"' in source
    assert 'network_boundary: str = "official_service_gateway"' in source


def test_phase461_panel_saves_payment_targets_through_official_services():
    source = PANEL.read_text(encoding='utf-8')
    assert 'finance_operation_policy.OP_CASHBOX_CREATE' in source
    assert 'finance_operation_policy.OP_BANK_CREATE' in source
    assert 'cashbox_service.add_cashbox(payload)' in source
    assert 'cashbox_service.add_bank_account(payload)' in source
    assert '_find_existing_cashbox' in source
    assert '_find_existing_bank_account' in source
    assert 'QDialog' not in source
    assert 'exec(' not in source and 'exec_(' not in source


def test_phase461_voucher_link_uses_inline_customer_supplier_create():
    source = VOUCHER_LINK.read_text(encoding='utf-8')
    assert "InlineQuickCreatePanel('customer'" in source
    assert "InlineQuickCreatePanel('supplier'" in source
    assert 'VoucherInlineQuickCustomerPanel' in source
    assert 'VoucherInlineQuickSupplierPanel' in source
    assert '_on_inline_party_created' in source
    assert '_reload_customer_options(target_id)' in source
    assert '_reload_supplier_options(target_id)' in source
    assert 'QDialog' not in source


def test_phase461_voucher_payment_uses_inline_cashbox_bank_create():
    source = VOUCHER_PAYMENT.read_text(encoding='utf-8')
    assert "InlineQuickCreatePanel('cashbox'" in source
    assert "InlineQuickCreatePanel('bank_account'" in source
    assert 'VoucherInlineQuickCashboxPanel' in source
    assert 'VoucherInlineQuickBankAccountPanel' in source
    assert '_on_inline_payment_target_created' in source
    assert '_reload_cashboxes(target_id)' in source
    assert '_reload_bank_accounts(target_id)' in source
    assert 'QDialog' not in source


def test_phase461_payment_inline_quick_create_translations_exist_for_supported_languages():
    source = TRANSLATOR.read_text(encoding='utf-8')
    for key in (
        'inline_quick_create_customer_tooltip',
        'inline_quick_create_supplier_tooltip',
        'inline_quick_create_cashbox_tooltip',
        'inline_quick_create_bank_account_tooltip',
        'inline_quick_create_cashbox_title',
        'inline_quick_create_bank_account_title',
        'cashbox_name',
        'cashbox_name_placeholder',
    ):
        assert source.count(key) >= 4
