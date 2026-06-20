from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def test_voucher_panels_use_compact_grid_layouts_not_stacked_form_layouts():
    for rel in (
        'alrajhi_client/features/vouchers/components/voucher_header.py',
        'alrajhi_client/features/vouchers/components/voucher_link.py',
        'alrajhi_client/features/vouchers/components/voucher_payment.py',
    ):
        source = read(rel)
        ast.parse(source)
        assert 'QGridLayout' in source
        assert 'QFormLayout' not in source
        assert 'setColumnStretch' in source
        assert 'setMinimumHeight(30)' in source


def test_voucher_conditional_fields_hide_labels_and_widgets_together():
    link = read('alrajhi_client/features/vouchers/components/voucher_link.py')
    payment = read('alrajhi_client/features/vouchers/components/voucher_payment.py')
    for source in (link, payment):
        ast.parse(source)
        assert '_field_labels' in source
        assert '_set_field_visible' in source
        assert 'label.setVisible(visible)' in source
        assert 'widget.setVisible(visible)' in source

    assert "self._set_field_visible('customer'" in link
    assert "self._set_field_visible('supplier'" in link
    assert "self._set_field_visible('invoice'" in link
    assert "self._set_field_visible('bank'" in payment
    assert "self._set_field_visible('cashbox'" in payment


def test_voucher_editor_remains_document_shell_with_bottom_actions():
    source = read('alrajhi_client/features/vouchers/voucher_editor_tab.py')
    ast.parse(source)
    assert "DOCUMENT_DESCRIPTOR = descriptor_for(\"voucher\")" in source
    assert 'VoucherActionsPanel' in source
    assert "bar.setObjectName('BottomActionBar')" in source
    assert 'apply_document_permissions' in source
