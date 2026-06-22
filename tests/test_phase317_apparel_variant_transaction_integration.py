# -*- coding: utf-8 -*-
from decimal import Decimal
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase317_transaction_and_inventory_tables_track_variant_identity():
    schema = text("alrajhi_client/database/schema_manager.py")
    client_migrations = text("alrajhi_client/database/migrations.py")
    server_migrations = text("alrajhi_server/database/migrations.py")
    for source in (schema, client_migrations, server_migrations):
        assert "variant_id" in source
        assert "variant_color" in source
        assert "variant_size" in source
        assert "variant_sku" in source
        assert "barcode_scope" in source
        assert "matched_barcode" in source


def test_phase317_transaction_model_preserves_variant_from_barcode_lookup_payload():
    model = text("alrajhi_client/features/transactions/grids/transaction_line_model.py")
    schema = text("alrajhi_client/features/transactions/grids/transaction_column_schema.py")
    assert 'TransactionColumn("variant", "transaction_column_variant"' in schema
    assert "def _variant_info" in model
    assert '"variant_id": variant_info.get("variant_id")' in model
    assert '"variant_color": variant_info.get("variant_color")' in model
    assert '"variant_size": variant_info.get("variant_size")' in model
    assert '"variant_sku": variant_info.get("variant_sku")' in model
    assert '"barcode_scope": row.get("barcode_scope", "")' in model
    assert '"matched_barcode": row.get("matched_barcode") or row.get("barcode", "")' in model
    assert "def _variant_label" in model


def test_phase317_pos_lines_keep_variant_identity_through_invoice_checkout_payload():
    pos_service = text("alrajhi_client/core/services/pos_service.py")
    pos_model = text("alrajhi_client/features/pos/pos_line_model.py")
    pos_schema = text("alrajhi_client/features/pos/pos_line_schema.py")
    assert "variant_id: Optional[int] = None" in pos_service
    assert "variant_color: str = ''" in pos_service
    assert "variant_size: str = ''" in pos_service
    assert "variant_sku: str = ''" in pos_service
    assert "variant_id': self.variant_id" in pos_service
    assert "matched_barcode': self.barcode" in pos_service
    assert "variant_info = self._variant_info(item)" in pos_service
    assert 'TransactionColumn("variant", "transaction_column_variant"' in pos_schema
    assert "if key == 'variant'" in pos_model
    assert "pos_barcode_scope_variant" in pos_model


def test_phase317_local_and_remote_invoice_persistence_write_variant_columns():
    client_db = text("alrajhi_client/database/connection.py")
    server_invoices = text("alrajhi_server/repositories/http_route_sql/invoices.py")
    for source in (client_db, server_invoices):
        assert "def _variant_payload_from_line" in source
        assert "variant_id, variant_color" in source
        assert "barcode_scope, matched_barcode" in source
        assert "_update_item_variant_quantity" in source
        assert "WHERE variant_id=?" in source
        assert "_insert_inventory_movement" in source or "def _record_inventory_movement" in source


def test_phase317_variant_barcode_lookup_reports_variant_specific_availability():
    client_db = text("alrajhi_client/database/connection.py")
    server_items = text("alrajhi_server/repositories/http_route_sql/items.py")
    for source in (client_db, server_items):
        assert "WHERE variant_id = v.id" in source
        assert "CAST(COALESCE(v.quantity, '0') AS REAL)) AS available" in source
        assert "barcode_scope': 'variant'" in source
        assert "matched_variant" in source


def test_phase317_release_gate_registered_and_documented():
    gate = text("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert '(317, "APPAREL_VARIANT_TRANSACTION_INTEGRATION")' in gate
    assert '(317, "apparel_variant_transaction_integration")' in gate
    assert "tests/test_phase317_apparel_variant_transaction_integration.py" in gate
    assert (ROOT / "PHASE317_APPAREL_VARIANT_TRANSACTION_INTEGRATION.md").exists()
