# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase325_materials_list_hides_apparel_base_items_by_default():
    widget = text("alrajhi_client/views/widgets/items_widget.py")
    assert "show_apparel_base_filter = QCheckBox" in widget
    assert "show_apparel_base_materials" in widget
    assert "def _filter_apparel_base_materials" in widget
    assert "product_service.item_variants(item_id)" in widget
    assert "not self._show_apparel_base_materials()" in widget


def test_phase325_transactions_block_base_apparel_and_keep_variant_barcode():
    doc = text("alrajhi_client/features/transactions/transaction_document_tab.py")
    delegate = text("alrajhi_client/features/transactions/grids/transaction_item_delegate.py")
    assert "def _item_has_active_variants" in doc
    assert "def _transaction_item_to_display" in doc
    assert "apparel.transaction_base_item_blocked" in doc
    assert "item_transform=self._transaction_item_to_display" in doc
    assert '"barcode": barcode,' in doc
    assert "must never fall back to the base-material barcode" in doc
    assert "transformed = self.item_transform(item)" in delegate
    assert "if not transformed" in delegate


def test_phase325_variant_sale_price_fallback_and_purchase_cost_policy():
    doc = text("alrajhi_client/features/transactions/transaction_document_tab.py")
    model = text("alrajhi_client/features/transactions/grids/transaction_line_model.py")
    client_db = text("alrajhi_client/database/connection.py")
    server_inv = text("alrajhi_server/repositories/http_route_sql/invoices.py")
    assert "sale_price = first_price" in doc
    assert "variant.get(\"sale_price\")" in doc
    assert "item.get(\"selling_price\")" in doc
    assert "cost_price = first_price" in doc
    assert "variant.get(\"cost_price\")" in doc
    assert "explicit_price = item.get(\"unit_price\")" in model
    assert "else item.get(price_key)" in model
    assert "def _update_variant_last_purchase_cost" in client_db
    assert "def _update_variant_last_purchase_cost" in server_inv
    assert "UPDATE item_variants SET cost_price" in client_db
    assert "UPDATE item_variants SET cost_price" in server_inv


def test_phase325_i18n_and_release_gate_registered():
    i18n = text("alrajhi_client/i18n/translator.py")
    gate = text("alrajhi_client/workspace/quality/release_gate_contract.py")
    for key in ("show_apparel_base_materials", "show_apparel_base_materials_hint", "apparel.transaction_base_item_blocked"):
        assert key in i18n
    assert '(325, "APPAREL_CATALOG_BOUNDARY_PRICING_HARDENING")' in gate
    assert '(325, "apparel_catalog_boundary_pricing_hardening")' in gate
    assert "tests/test_phase325_apparel_catalog_boundary_pricing_hardening.py" in gate
