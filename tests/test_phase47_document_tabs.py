from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_invoice_return_voucher_tabs_are_registered():
    main = (ROOT / 'alrajhi_client/views/main_window.py').read_text(encoding='utf-8')
    # Phase414/417/458: legacy dialog-backed transaction editors are quarantined.
    # MainWindow routes invoices/returns to the unified transaction shell;
    # vouchers are opened inline inside VouchersWidget.
    assert 'SalesInvoiceTab' in main
    assert 'PurchaseInvoiceTab' in main
    assert 'open_return_document' in main
    assert 'SalesReturnTab' in main
    assert 'PurchaseReturnTab' in main
    vouchers = (ROOT / 'alrajhi_client/views/widgets/vouchers_widget.py').read_text(encoding='utf-8')
    assert 'VoucherEditorTab' in vouchers
    assert "_open_page_inline_action('vouchers'" in main


def test_legacy_lists_delegate_to_workspace_tabs():
    invoices = (ROOT / 'alrajhi_client/views/widgets/invoices_widget.py').read_text(encoding='utf-8')
    returns = (ROOT / 'alrajhi_client/views/widgets/returns_widget.py').read_text(encoding='utf-8')
    vouchers = (ROOT / 'alrajhi_client/views/widgets/vouchers_widget.py').read_text(encoding='utf-8')
    assert 'main.open_quick_invoice(inv_type)' in invoices
    assert 'main.open_quick_invoice(inv_type, invoice_id=inv_id)' in invoices
    assert "open_return_document('sale'" in returns
    assert "open_return_document('purchase'" in returns
    assert 'open_quick_voucher' in vouchers


def test_dialog_document_adapter_exists():
    adapter = ROOT / 'alrajhi_client/features/dialog_documents/dialog_document_tab.py'
    text = adapter.read_text(encoding='utf-8')
    assert 'class DialogDocumentTab' in text
    assert 'workspace_save' in text
    assert 'workspace_print' in text
    assert 'workspace_export' in text
