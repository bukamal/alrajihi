# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase321_product_gateway_exposes_apparel_report_boundary():
    contract = text("alrajhi_client/gateways/product_gateway.py")
    local = text("alrajhi_client/gateways/local/product_gateway.py")
    remote = text("alrajhi_client/gateways/remote/product_gateway.py")
    service = text("alrajhi_client/core/services/product_service.py")
    rest = text("alrajhi_client/database/connection_rest.py")
    assert "def apparel_report(self, item_id: int | None = None)" in contract
    assert "def apparel_report(self, item_id: int | None = None)" in local
    assert "item_dao.repo.db.get_connection()" in local
    assert "def apparel_report(self, item_id: int | None = None)" in remote
    assert "return self.rest_client.get_apparel_report(item_id=item_id)" in remote
    assert "def apparel_report(self, item_id: int | None = None)" in service
    assert "self.item_gateway.apparel_report(item_id=item_id)" in service
    assert "def get_apparel_report(self, item_id=None)" in rest
    assert "/api/items/variants/apparel-report" in rest


def test_phase321_server_api_reports_variant_stock_sales_and_low_stock():
    server = text("alrajhi_server/repositories/http_route_sql/items.py")
    assert "@items_bp.route('/items/variants/apparel-report', methods=['GET'])" in server
    assert "def get_apparel_report()" in server
    assert "item_warehouse_variant_balances" not in server or "warehouse_movements" in server
    assert "v.color" in server and "v.size" in server and "v.sku" in server
    assert "low_stock" in server
    assert "by_color" in server
    assert "by_size" in server
    assert "total_sold_quantity" in server
    assert "invoice_lines" in server
    assert "sales_return_lines" in server


def test_phase321_apparel_workspace_has_reports_card_without_visible_sku_term():
    widget = text("alrajhi_client/views/apparel/apparel_workspace_widget.py")
    translations = text("alrajhi_client/i18n/translator.py")
    assert "apparelReportsCard" in widget
    assert "apparel.reports_title" in widget
    assert "product_service.apparel_report" in widget
    assert "report_low_label" in widget
    assert "report_best_color_label" in widget
    assert "report_best_size_label" in widget
    assert "report_table" in widget
    assert "apparel.metric_sold" in translations
    assert "apparel.report_low_stock" in translations
    assert "apparel.report_top_color" in translations
    assert "apparel.report_top_size" in translations
    # Internal field names may remain technical, but visible text must not expose SKU.
    visible_translation_slice = translations[translations.index("# Phase 316: Apparel workspace shell"):]
    assert "'apparel_col_sku': 'SKU'" not in visible_translation_slice
    assert "رمز المتغير" in visible_translation_slice
    assert "Variantencode" in visible_translation_slice
    assert "Variant code" in visible_translation_slice


def test_phase321_release_gate_registered_and_documented():
    gate = text("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert '(321, "APPAREL_REPORTS")' in gate
    assert '(321, "apparel_reports")' in gate
    assert "tests/test_phase321_apparel_reports.py" in gate
    assert (ROOT / "PHASE321_APPAREL_REPORTS.md").exists()
