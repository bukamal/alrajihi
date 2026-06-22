from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_phase315_schema_creates_item_variants_without_replacing_units():
    from alrajhi_client.database.schema_manager import apply_common_schema

    conn = sqlite3.connect(":memory:")
    apply_common_schema(conn)
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "item_variants" in tables
    columns = {row[1] for row in conn.execute("PRAGMA table_info(item_variants)")}
    for column in {
        "item_id", "color", "size", "sku", "barcode", "sale_price",
        "cost_price", "quantity", "reorder_level", "is_active",
    }:
        assert column in columns
    # Variants are additive; existing item_units support remains separately indexed.
    assert "idx_item_units_barcode" in read("alrajhi_client/database/schema_manager.py")


def test_phase315_product_service_exposes_variants_behind_gateway_boundary():
    service = read("alrajhi_client/core/services/product_service.py")
    assert "def item_variants" in service
    assert "def add_variant" in service
    assert "def update_variant" in service
    assert "def delete_variant" in service
    assert "self.item_gateway.get_variants" in service
    assert "self.item_gateway.add_variant" in service
    assert "SELECT " not in service
    assert "self.item_gateway" in service


def test_phase315_gateways_and_rest_api_support_variant_barcode_lookup():
    gateway = read("alrajhi_client/gateways/product_gateway.py")
    local = read("alrajhi_client/gateways/local/product_gateway.py")
    remote = read("alrajhi_client/gateways/remote/product_gateway.py")
    rest = read("alrajhi_client/database/connection_rest.py")
    server = read("alrajhi_server/repositories/http_route_sql/items.py")
    for text in (gateway, local, remote):
        assert "get_variant_by_barcode" in text
        assert "add_variant" in text
    assert "/api/items/variants/by-barcode" in rest
    assert "@items_bp.route('/items/variants/by-barcode'" in server
    assert "barcode_scope': 'variant'" in server
    assert "matched_variant" in server


def test_phase315_barcode_uniqueness_covers_base_units_and_variants():
    client_connection = read("alrajhi_client/database/connection.py")
    server_items = read("alrajhi_server/repositories/http_route_sql/items.py")
    for text in (client_connection, server_items):
        assert "item_variants" in text
        assert "item_units" in text
        assert "JOIN items" in text
        assert "متغير المادة" in text
    assert "UNIQUE(item_id, color, size)" in read("alrajhi_client/database/schema_manager.py")


def test_phase315_release_gate_registered_and_documented():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert '(315, "PRODUCT_VARIANTS_FOUNDATION")' in gate
    assert '(315, "product_variants_foundation")' in gate
    assert "tests/test_phase315_product_variants_foundation.py" in gate
    assert (ROOT / "PHASE315_PRODUCT_VARIANTS_FOUNDATION.md").exists()
