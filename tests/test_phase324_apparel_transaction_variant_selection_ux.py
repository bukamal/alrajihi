# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase324_transaction_lookup_expands_apparel_variants_not_base_item_only():
    doc = text("alrajhi_client/features/transactions/transaction_document_tab.py")
    catalog = text("alrajhi_client/core/services/catalog_service.py")
    assert "def item_variants" in catalog
    assert "def _variant_row_from_item" in doc
    assert "catalog_service.item_variants" in doc
    assert '"base_item_name"' in doc
    assert '"barcode_scope": "variant"' in doc
    assert '"matched_variant": matched_variant' in doc
    assert "not offered in manual suggestions" in doc
    assert "catalog_service.items(search=None, limit=max" in doc


def test_phase324_invoice_quick_search_and_cell_delegate_resolve_selected_variant_label():
    doc = text("alrajhi_client/features/transactions/transaction_document_tab.py")
    delegate = text("alrajhi_client/features/transactions/grids/transaction_item_delegate.py")
    for source in (doc, delegate):
        assert "lookup_label" in source
        assert "search_label" in source
        assert "matched_barcode" in source
    assert "def _row_for_search_text" in doc
    assert "item = self._row_for_search_text(text)" in doc
    assert "rows = self._material_lookup_rows(text or None, 50)" in doc
    assert "def _row_for_text" in delegate
    assert "item = self._row_for_text(text)" in delegate


def test_phase324_variant_column_is_visible_in_transaction_presets():
    schema = text("alrajhi_client/features/transactions/grids/transaction_column_schema.py")
    presets = text("alrajhi_client/features/transactions/grids/transaction_column_presets.py")
    assert 'TransactionColumn("variant", "transaction_column_variant", False, True' in schema
    assert '("row", "barcode", "item", "variant", "qty"' in presets
    assert '("row", "item", "variant", "unit"' in presets
    assert '("row", "original_invoice", "barcode", "item", "variant"' in presets


def test_phase324_variant_specific_available_qty_and_base_item_display_are_preserved():
    doc = text("alrajhi_client/features/transactions/transaction_document_tab.py")
    model = text("alrajhi_client/features/transactions/grids/transaction_line_model.py")
    assert "warehouse_service.available_qty(int(item.get(\"id\")), self._selected_warehouse_id(), variant_id=variant_id)" in doc
    assert '"item": item.get("base_item_name") or item.get("item_name") or item.get("name") or ""' in model
    assert '"variant": variant_info.get("variant") or ""' in model
    assert '"variant_id": variant_info.get("variant_id")' in model
    assert '"barcode_scope": barcode_scope' in model


def test_phase324_release_gate_registered_and_documented():
    gate = text("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert '(324, "APPAREL_TRANSACTION_VARIANT_SELECTION_UX")' in gate
    assert '(324, "apparel_transaction_variant_selection_ux")' in gate
    assert "tests/test_phase324_apparel_transaction_variant_selection_ux.py" in gate
    assert (ROOT / "PHASE324_APPAREL_TRANSACTION_VARIANT_SELECTION_UX.md").exists()
