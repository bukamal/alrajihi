# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase319_apparel_contract_exposes_matrix_and_bulk_builder():
    contract = text("alrajhi_client/features/apparel/apparel_workspace_contract.py")
    assert 'APPAREL_MATRIX_SCOPE = "color_size_matrix"' in contract
    assert 'APPAREL_BULK_BUILDER = "product_service_create_missing_variants"' in contract
    assert '"matrix_scope": APPAREL_MATRIX_SCOPE' in contract
    assert '"bulk_builder": APPAREL_BULK_BUILDER' in contract


def test_phase319_apparel_workspace_has_color_size_matrix_and_bulk_creator():
    widget = text("alrajhi_client/views/apparel/apparel_workspace_widget.py")
    assert "QTableWidget" in widget
    assert 'self.matrix_table = QTableWidget(self)' in widget
    assert 'setObjectName("apparelColorSizeMatrix")' in widget
    assert "def _render_color_size_matrix" in widget
    assert "qty_by_cell" in widget
    assert "apparel.bulk_builder_title" in widget
    assert "self.bulk_colors_edit" in widget
    assert "self.bulk_sizes_edit" in widget
    assert "self.create_bulk_btn" in widget
    assert "def create_missing_variants" in widget
    assert "product_service.create_missing_variants" in widget


def test_phase319_bulk_creation_stays_behind_product_service_gateway_boundary():
    service = text("alrajhi_client/core/services/product_service.py")
    widget = text("alrajhi_client/views/apparel/apparel_workspace_widget.py")
    assert "def create_missing_variants" in service
    assert "self.add_variant(int(item_id), payload)" in service
    assert "self.generate_barcode('CODE128', prefix='APP')" in service
    assert "item_gateway" in service
    forbidden_widget_markers = ["DatabaseConnection", "database.dao", "database.repositories", ".execute(", "SELECT "]
    for marker in forbidden_widget_markers:
        assert marker not in widget


def test_phase319_visible_i18n_uses_variant_code_not_sku_term():
    i18n = text("alrajhi_client/i18n/translator.py")
    assert "رمز المتغير" in i18n
    assert "Variant code" in i18n
    assert "Variantencode" in i18n
    assert "apparel.bulk_builder_title" in i18n
    assert "apparel.matrix_title" in i18n
    assert "SKU" not in i18n


def test_phase319_release_gate_registered_and_documented():
    gate = text("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert '(319, "APPAREL_MATRIX_BULK_VARIANT_BUILDER")' in gate
    assert '(319, "apparel_matrix_bulk_variant_builder")' in gate
    assert "tests/test_phase319_apparel_matrix_bulk_variant_builder.py" in gate
    assert (ROOT / "PHASE319_APPAREL_MATRIX_BULK_VARIANT_BUILDER.md").exists()
