# -*- coding: utf-8 -*-
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.registry import PAGE_MANIFESTS
from workspace.runtime.table_contract_sweep import (
    manifest_table_contract_rows,
    identity_contract_rows,
    validate_runtime_table_contract_sweep,
)
from workspace.tables.table_column_registry import (
    TABLE_COLUMN_CONTRACTS,
    TABLE_IDENTITY_CONTRACTS,
    table_column_contract_by_id,
)


def test_phase343_manifest_tables_have_contracts():
    rows = manifest_table_contract_rows()
    assert rows
    assert all(row.ok for row in rows), [row for row in rows if not row.ok]
    registered_table_count = sum(len(m.table_specs) for m in PAGE_MANIFESTS.values())
    assert len(rows) == registered_table_count


def test_phase343_legacy_smart_table_identities_resolve():
    rows = identity_contract_rows()
    assert rows
    assert all(row.ok for row in rows), [row for row in rows if not row.ok]
    assert TABLE_IDENTITY_CONTRACTS["materials.workspace.items_grid"] == "items.materials"
    assert TABLE_IDENTITY_CONTRACTS["InvoicesWidget.sales"] == "sales_invoices.list"
    assert TABLE_IDENTITY_CONTRACTS["cashboxes.cashboxes"] == "cashboxes.cashboxes"


def test_phase343_required_runtime_contracts_exist():
    required = {
        "items.materials",
        "categories.categories",
        "customers.customers",
        "suppliers.suppliers",
        "warehouses.warehouses",
        "cashboxes.cashboxes",
        "cashboxes.banks",
        "sales_invoices.list",
        "purchase_invoices.list",
        "returns.list",
        "purchase_returns.list",
        "manufacturing.bom",
        "manufacturing.orders",
        "reports.result",
        "audit_log.events",
        "batch_print.labels",
    }
    assert required.issubset(set(TABLE_COLUMN_CONTRACTS)), sorted(required - set(TABLE_COLUMN_CONTRACTS))
    for cid in required:
        contract = table_column_contract_by_id(cid)
        assert contract is not None
        assert contract.default_visible_keys()
        assert contract.default_printable_keys()
        assert contract.default_exportable_keys()


def test_phase343_runtime_sweep_has_no_issues():
    assert validate_runtime_table_contract_sweep() == {}
