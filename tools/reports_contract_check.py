#!/usr/bin/env python3
"""Static contract checks for ReportsWidget.

This check is intentionally PyQt-free so it can run in CI/headless servers.
It prevents regressions like calling a missing ReportsWidget method or using a
ReportingService/InventoryService method that does not exist.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "alrajhi_client" / "views" / "widgets" / "reports_widget.py"
REPORTING_SERVICE = ROOT / "alrajhi_client" / "core" / "services" / "reporting_service.py"
INVENTORY_SERVICE = ROOT / "alrajhi_client" / "core" / "services" / "inventory_service.py"
OFFLINE_QUEUE_SERVICE = ROOT / "alrajhi_client" / "core" / "services" / "offline_queue_service.py"
PRODUCT_SERVICE = ROOT / "alrajhi_client" / "core" / "services" / "product_service.py"


def _class_methods(path: Path, class_name: str) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {n.name for n in node.body if isinstance(n, ast.FunctionDef)}
    raise AssertionError(f"Class {class_name} not found in {path}")


def _self_calls(path: Path, class_name: str) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            calls = set()
            for child in ast.walk(node):
                if (
                    isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Attribute)
                    and isinstance(child.func.value, ast.Name)
                    and child.func.value.id == "self"
                ):
                    calls.add(child.func.attr)
            return calls
    raise AssertionError(f"Class {class_name} not found in {path}")


def _service_calls(path: Path, service_name: str) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    calls = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == service_name
        ):
            calls.add(node.func.attr)
    return calls


def main() -> int:
    reports_methods = _class_methods(REPORTS, "ReportsWidget")
    private_calls = {c for c in _self_calls(REPORTS, "ReportsWidget") if c.startswith("_")}
    missing = private_calls - reports_methods
    # Qt/model methods are not private calls on ReportsWidget and should not appear here.
    if missing:
        raise AssertionError(f"ReportsWidget calls missing private methods: {sorted(missing)}")

    reporting_methods = _class_methods(REPORTING_SERVICE, "ReportingService")
    inventory_methods = _class_methods(INVENTORY_SERVICE, "InventoryService")
    offline_methods = _class_methods(OFFLINE_QUEUE_SERVICE, "OfflineQueueService")
    product_methods = _class_methods(PRODUCT_SERVICE, "ProductService")

    missing_reporting = _service_calls(REPORTS, "reporting_service") - reporting_methods
    missing_inventory = _service_calls(REPORTS, "inventory_service") - inventory_methods
    missing_offline = _service_calls(REPORTS, "offline_queue_service") - offline_methods
    missing_product = _service_calls(REPORTS, "product_service") - product_methods

    failures = {
        "reporting_service": sorted(missing_reporting),
        "inventory_service": sorted(missing_inventory),
        "offline_queue_service": sorted(missing_offline),
        "product_service": sorted(missing_product),
    }
    failures = {k: v for k, v in failures.items() if v}
    if failures:
        raise AssertionError(f"ReportsWidget references missing service methods: {failures}")

    required_tables = {
        "trial_balance_table", "customer_statement_table", "supplier_statement_table",
        "customer_balances_table", "supplier_balances_table", "customer_aging_table",
        "supplier_aging_table", "ledger_reconciliation_table", "ledger_dual_read_table",
        "ledger_readiness_table", "offline_queue_table", "unit_audit_table",
    }
    text = REPORTS.read_text(encoding="utf-8")
    missing_tables = sorted(t for t in required_tables if t not in text)
    if missing_tables:
        raise AssertionError(f"ReportsWidget missing Phase36 table attributes: {missing_tables}")

    print("Reports contract check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
