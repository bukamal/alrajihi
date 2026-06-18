import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_global_search_service_exists_and_has_no_sql_literals():
    source = read('alrajhi_client/core/services/global_search_service.py')
    ast.parse(source)
    upper = source.upper()
    for word in ('SELECT ', 'INSERT ', 'UPDATE ', 'DELETE ', 'CREATE ', 'ALTER ', 'DROP '):
        assert word not in upper
    assert 'class GlobalSearchService' in source
    assert 'global_search_service = GlobalSearchService()' in source
    assert 'product_service.items' in source
    assert 'entity_service.customers' in source
    assert 'invoice_service.list_records' in source


def test_quick_open_supports_dynamic_search_results():
    source = read('alrajhi_client/shell/quick_open_dialog.py')
    ast.parse(source)
    assert 'search_provider' in source
    assert 'payload' in source
    assert 'self._search_provider' in source


def test_main_window_opens_global_search_results_as_document_tabs():
    source = read('alrajhi_client/views/main_window.py')
    ast.parse(source)
    assert '_global_search_items' in source
    assert '_open_quick_open_item' in source
    assert 'global_search_service.search' in source
    assert 'open_item_document' in source
    assert "open_party_document('customer'" in source
    assert 'open_quick_invoice' in source
    assert 'open_quick_voucher' in source
