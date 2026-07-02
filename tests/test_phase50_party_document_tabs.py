from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_party_document_tab_exists_and_uses_services():
    source = (ROOT / 'alrajhi_client/features/parties/party_editor_tab.py').read_text(encoding='utf-8')
    assert 'class PartyEditorTab(BaseDocumentTab)' in source
    assert 'entity_service.add_customer' in source
    assert 'entity_service.add_supplier' in source
    assert 'entity_service.update_customer' in source
    assert 'entity_service.update_supplier' in source
    assert 'DatabaseConnection' not in source
    assert '.execute(' not in source


def test_main_window_routes_customer_supplier_to_document_tabs():
    source = (ROOT / 'alrajhi_client/views/main_window.py').read_text(encoding='utf-8')
    assert 'def open_party_document' in source
    # Phase378/458: parties open through the unified inline editor host,
    # not by eager PartyEditorTab imports in MainWindow.
    host = (ROOT / 'alrajhi_client/views/widgets/party_inline_editor_host.py').read_text(encoding='utf-8')
    assert 'from features.parties import PartyEditorTab' in host
    assert "_open_page_inline_action(page_id, method_name" in source
    assert "open_party_document('customer')" in source
    assert "open_party_document('supplier')" in source


def test_customer_supplier_widgets_use_document_tabs_with_fallbacks():
    customers = (ROOT / 'alrajhi_client/views/widgets/customers_widget.py').read_text(encoding='utf-8')
    suppliers = (ROOT / 'alrajhi_client/views/widgets/suppliers_widget.py').read_text(encoding='utf-8')
    assert "main.open_party_document('customer'" in customers
    assert "main.open_party_document('supplier'" in suppliers
    assert 'AddEntityDialog' in customers
    assert 'AddEntityDialog' in suppliers
