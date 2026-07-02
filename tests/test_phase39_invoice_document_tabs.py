import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_invoice_dialog_supports_embedded_workspace_document_mode():
    source = _read("alrajhi_client/views/dialogs/invoice_dialog.py")
    ast.parse(source)
    assert "embedded=False" in source
    assert "Qt.Widget" in source
    assert "workspace_save" in source
    assert "workspace_print" in source
    assert "workspace_export" in source
    assert "dirtyChanged" in source
    assert "saved = pyqtSignal" in source


def test_main_window_opens_quick_invoices_as_document_tabs():
    source = _read("alrajhi_client/views/main_window.py")
    ast.parse(source)
    assert "from features.transactions.documents.purchase_invoice_tab import PurchaseInvoiceTab" in source
    assert "from features.transactions.documents.sales_invoice_tab import SalesInvoiceTab" in source
    assert "widget = PurchaseInvoiceTab(self, invoice_id=invoice_id)" in source
    assert "widget = SalesInvoiceTab(self, invoice_id=invoice_id)" in source
    assert "self._open_document_tab(tab_id" in source
    assert "singleton=False" in source
    assert "save_current_tab" in source
    assert "print_current_tab" in source
    assert "workspace.mark_dirty" in source


def test_phase39_workspace_command_translations_exist():
    from alrajhi_client.i18n import translator

    for lang in ("ar", "de", "en"):
        translator.set_language(lang)
        assert translator.translate("workspace.no_save_action") != "workspace.no_save_action"
        assert translator.translate("workspace.no_print_action") != "workspace.no_print_action"
        assert translator.translate("workspace.no_export_action") != "workspace.no_export_action"
