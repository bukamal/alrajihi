# -*- coding: utf-8 -*-
"""Phase 172 guard: unit barcode storage/API/scan contract.

This guard protects the new material-unit barcode pipeline.  A scanner must be
able to resolve both a base material barcode and a sub-unit barcode through the
same exact lookup path, and the transaction grid must receive matched_unit
metadata so it can choose the correct unit/conversion factor.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


client_migrations = read("alrajhi_client/database/migrations.py")
server_migrations = read("alrajhi_server/database/migrations.py")
client_schema = read("alrajhi_client/database/schema_manager.py")
server_schema = read("alrajhi_server/database/schema_manager.py")
item_repo = read("alrajhi_client/database/repositories/item_repo.py")
connection = read("alrajhi_client/database/connection.py")
product_service = read("alrajhi_client/core/services/product_service.py")
server_items = read("alrajhi_server/repositories/http_route_sql/items.py")
line_model = read("alrajhi_client/features/transactions/grids/transaction_line_model.py")

for label, text in {
    "client migrations": client_migrations,
    "server migrations": server_migrations,
}.items():
    require("CREATE TABLE IF NOT EXISTS item_units" in text, f"{label} must define item_units")
    require("barcode TEXT" in text, f"{label} item_units must include barcode")
    require("notes TEXT" in text, f"{label} item_units must include notes")

for label, text in {"client schema": client_schema, "server schema": server_schema}.items():
    require('"item_units"' in text and '"barcode": "TEXT"' in text, f"{label} must add item_units.barcode to old DBs")
    require("idx_item_units_barcode" in text, f"{label} must index item_units.barcode")

require("SELECT id, item_id, unit_name, conversion_factor, barcode, notes" in item_repo, "local repository must return unit barcode/notes")
require("INSERT INTO item_units (item_id, unit_name, conversion_factor, barcode, notes)" in item_repo, "local repository must persist unit barcode/notes")
require("FROM item_units u" in connection and "u.barcode=?" in connection, "local exact barcode lookup must search unit barcodes")
require("matched_unit" in connection and "barcode_scope" in connection, "local lookup must return matched_unit metadata")

require("_validate_unit_barcodes" in product_service, "product service must validate unit barcodes")
require("_normalize_unit_barcode" in product_service, "product service must normalize unit barcodes")
require("self.add_unit(item_id, name, factor, barcode, notes)" in product_service, "replace_units must persist barcode/notes through gateway")

require("FROM item_units u" in server_items and "u.barcode=?" in server_items, "server exact barcode endpoint must search unit barcodes")
require("matched_unit" in server_items and "barcode_scope" in server_items, "server endpoint must return matched_unit metadata")
require("INSERT INTO item_units (item_id, unit_name, conversion_factor, barcode, notes)" in server_items, "server must persist unit barcode/notes")
require("_assert_unique_unit_barcode" in server_items, "server must validate unit barcode uniqueness")

require("matched_unit = item.get(\"matched_unit\")" in line_model, "transaction line model must read matched_unit")
require("base_price * factor" in line_model, "transaction line model must price scanned units by conversion factor")
require('"unit_id": unit_id' in line_model, "transaction line model must apply matched unit_id")

print("phase172_unit_barcode_api_guard passed")
