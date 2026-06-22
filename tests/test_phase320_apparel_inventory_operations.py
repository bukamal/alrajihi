# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase320_variant_warehouse_balance_schema_exists_on_client_and_server():
    client_schema = text("alrajhi_client/database/schema_manager.py")
    server_schema = text("alrajhi_server/database/schema_manager.py")
    client_migrations = text("alrajhi_client/database/migrations.py")
    server_migrations = text("alrajhi_server/database/migrations.py")
    for source in (client_schema, server_schema, client_migrations, server_migrations):
        assert "item_warehouse_variant_balances" in source
        assert "UNIQUE(user_id, item_id, variant_id, warehouse_id)" in source
        assert "variant_id INTEGER" in source
        assert "variant_color TEXT" in source
        assert "variant_size TEXT" in source
        assert "variant_sku TEXT" in source
        assert "idx_wh_variant_balances_variant" in source or "item_warehouse_variant_balances(variant_id)" in source


def test_phase320_local_warehouse_repository_records_variant_warehouse_movements():
    repo = text("alrajhi_client/database/repositories/warehouse_repo.py")
    assert "def _variant_payload" in repo
    assert "def _ensure_variant_balance_row" in repo
    assert "def _available_variant_qty" in repo
    assert "def available_qty(self, item_id: int, warehouse_id: int | None = None, variant_id" in repo
    assert "item_warehouse_variant_balances" in repo
    assert "variant_id, variant_color, variant_size, variant_sku, barcode_scope, matched_barcode" in repo
    assert "الرصيد غير كافٍ لهذا اللون/المقاس" in repo
    assert "self.record_movement(item_id, from_wh, 'transfer_out'" in repo and "**vp" in repo
    assert "warehouse_transfers" in repo and "variant_id, variant_color" in repo


def test_phase320_gateway_and_remote_api_support_variant_warehouse_quantity():
    gateway = text("alrajhi_client/gateways/warehouse_gateway.py")
    local_gateway = text("alrajhi_client/gateways/local/warehouse_gateway.py")
    remote_gateway = text("alrajhi_client/gateways/remote/warehouse_gateway.py")
    rest_client = text("alrajhi_client/database/connection_rest.py")
    server = text("alrajhi_server/repositories/http_route_sql/warehouses.py")
    for source in (gateway, local_gateway, remote_gateway):
        assert "variant_id: int | None = None" in source
        assert "**variant_data" in source
    assert "if variant_id: params['variant_id'] = variant_id" in rest_client
    assert "def _ensure_variant_warehouse_schema" in server
    assert "variant_id = request.args.get('variant_id', type=int)" in server
    assert "_available_qty(db, uid, item_id, warehouse_id, variant_id=variant_id)" in server
    assert "**vp" in server


def test_phase320_invoice_warehouse_operations_check_variant_stock_and_post_variant_identity():
    service = text("alrajhi_client/core/services/warehouse_service.py")
    assert "required_by_variant" in service
    assert "self.available_qty(item_id, wh_id, variant_id=variant_id)" in service
    assert "المخزون غير كافٍ للون/المقاس" in service
    assert "variant_id=line.get('variant_id')" in service
    assert "variant_color=line.get('variant_color'" in service
    assert "matched_barcode=line.get('matched_barcode'" in service


def test_phase320_release_gate_registered_and_documented():
    gate = text("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert '(320, "APPAREL_INVENTORY_OPERATIONS")' in gate
    assert '(320, "apparel_inventory_operations")' in gate
    assert "tests/test_phase320_apparel_inventory_operations.py" in gate
    assert (ROOT / "PHASE320_APPAREL_INVENTORY_OPERATIONS.md").exists()
