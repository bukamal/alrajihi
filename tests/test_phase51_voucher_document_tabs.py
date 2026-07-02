from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_voucher_document_tab_is_decomposed_and_service_bound():
    source = (ROOT / 'alrajhi_client/features/vouchers/voucher_editor_tab.py').read_text(encoding='utf-8')
    assert 'class VoucherEditorTab(BaseDocumentTab)' in source
    assert 'VoucherHeaderPanel' in source
    assert 'VoucherLinkPanel' in source
    assert 'VoucherPaymentPanel' in source
    assert 'VoucherActionsPanel' in source
    assert 'voucher_service.add' in source
    assert 'voucher_service.update' in source
    assert 'printing_service.voucher_preview' in source
    assert 'printing_service.voucher_pdf' in source
    assert 'DialogDocumentTab' not in source
    assert 'VoucherDialog' not in source
    assert 'DatabaseConnection' not in source
    assert '.execute(' not in source


def test_voucher_components_exist():
    base = ROOT / 'alrajhi_client/features/vouchers/components'
    for name in ('voucher_header.py', 'voucher_link.py', 'voucher_payment.py', 'voucher_actions.py'):
        assert (base / name).exists()
    payment = (base / 'voucher_payment.py').read_text(encoding='utf-8')
    assert 'cashbox_service.cashboxes' in payment
    assert 'cashbox_service.bank_accounts' in payment
    link = (base / 'voucher_link.py').read_text(encoding='utf-8')
    assert 'catalog_service.customers' in link
    assert 'catalog_service.suppliers' in link
    assert 'invoice_service.unpaid_invoices' in link


def test_voucher_widget_still_routes_to_workspace_tabs():
    source = (ROOT / 'alrajhi_client/views/widgets/vouchers_widget.py').read_text(encoding='utf-8')
    assert 'main.open_quick_voucher' in source
    main = (ROOT / 'alrajhi_client/views/main_window.py').read_text(encoding='utf-8')
    # Phase378/458: voucher creation is inline inside VouchersWidget.
    assert 'from features.vouchers import VoucherEditorTab' in source
    assert 'def open_quick_voucher' in main
    assert "_open_page_inline_action('vouchers'" in main
