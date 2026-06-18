# -*- coding: utf-8 -*-
"""Guard for Phase 184: material lookup must be case-insensitive for manual search.

Scanner/exact barcode lookup intentionally remains exact.  This guard checks the
manual material search path used by sales/purchase invoices and the server list
endpoint.
"""
from __future__ import annotations

from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def check_sql_predicate_runtime() -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA case_sensitive_like=ON")
    conn.execute("CREATE TABLE items (name TEXT, barcode TEXT)")
    conn.execute("INSERT INTO items (name, barcode) VALUES (?, ?)", ("Milk Box", "ABC128"))
    pattern = "%milk%"
    raw_like = conn.execute("SELECT COUNT(*) FROM items WHERE name LIKE ?", (pattern,)).fetchone()[0]
    folded_like = conn.execute(
        "SELECT COUNT(*) FROM items WHERE LOWER(COALESCE(name,'')) LIKE LOWER(?)",
        (pattern,),
    ).fetchone()[0]
    require(raw_like == 0, "Test setup failed: raw LIKE should be case-sensitive after PRAGMA.")
    require(folded_like == 1, "LOWER(... LIKE LOWER(?)) predicate did not match mixed-case material name.")


def main() -> int:
    connection = read("alrajhi_client/database/connection.py")
    server_items = read("alrajhi_server/repositories/http_route_sql/items.py")
    barcode_input = read("alrajhi_client/core/services/barcode_input_service.py")
    transaction_tab = read("alrajhi_client/features/transactions/transaction_document_tab.py")

    predicate = "LOWER(COALESCE(i.name,'')) LIKE LOWER(?)"
    require("LOWER(COALESCE(name,'')) LIKE LOWER(?)" in connection, "Local count query is not case-insensitive.")
    require(predicate in connection, "Local item list query is not case-insensitive.")
    require(predicate in server_items, "Server item list query is not case-insensitive.")
    require("LOWER(COALESCE(i.barcode,'')) LIKE LOWER(?)" in server_items, "Server item barcode search is not case-insensitive for manual search.")

    require("def _manual_exact_name_matches" in barcode_input, "Manual lookup lacks exact casefold name disambiguation.")
    require(".casefold()" in barcode_input, "Manual exact match must use casefold().")
    require("catalog_service.items(search=normalized, limit=10)" in barcode_input, "Manual lookup should fetch enough rows to resolve exact name matches.")

    require("QCompleter" in transaction_tab, "Transaction material search field lacks a completer.")
    require("setCaseSensitivity(Qt.CaseInsensitive)" in transaction_tab, "Transaction material completer is not case-insensitive.")
    require("setFilterMode(Qt.MatchContains)" in transaction_tab, "Transaction material completer should match inside material names.")
    require("_refresh_material_completer" in transaction_tab, "Transaction material completer is not refreshed from catalog search.")

    check_sql_predicate_runtime()
    print("phase184_case_insensitive_material_lookup_guard passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"phase184_case_insensitive_material_lookup_guard failed: {exc}", file=sys.stderr)
        raise
