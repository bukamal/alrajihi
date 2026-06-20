# -*- coding: utf-8 -*-
"""Canonical Report Shell contract (Phase 256).

Reports are read-only operational documents.  They are not edited like
invoices, but they still need the same governance surface: language, currency,
filters, permissions, print/export, API/network readiness, branch policy, and
table identity.  This module is intentionally data-only so CI, PyInstaller
builds, and audit tools can inspect it without importing PyQt.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from workspace.documents.document_contract import (
    BRANCH_NONE,
    BRANCH_OPTIONAL,
    CURRENCY_DISPLAY,
    NETWORK_LOCAL_ONLY,
    NETWORK_MIXED,
    NETWORK_REMOTE_AVAILABLE,
    SHELL_REPORT,
    descriptor_for,
)

REPORT_FILTER_PERIOD = "period"
REPORT_FILTER_WAREHOUSE = "warehouse"
REPORT_FILTER_CASHBOX = "cashbox"
REPORT_FILTER_BANK = "bank"
REPORT_FILTER_CUSTOMER = "customer"
REPORT_FILTER_SUPPLIER = "supplier"
REPORT_FILTER_ITEM = "item"
REPORT_FILTER_BRANCH = "branch"


@dataclass(frozen=True)
class ReportShellDescriptor:
    """Contract for one concrete report tab inside ReportsWidget."""

    report_key: str
    title_key: str
    tab_attr: str
    table_attr: str
    service_method: str
    api_resource: str
    filters: tuple[str, ...] = field(default_factory=tuple)
    network_mode: str = NETWORK_REMOTE_AVAILABLE
    permission_view: str = "reports.view"
    permission_print: str = "reports.print"
    permission_export: str = "reports.export"
    currency_policy: str = CURRENCY_DISPLAY
    branch_policy: str = BRANCH_OPTIONAL
    supports_print: bool = True
    supports_export: bool = True
    i18n_scope: str = "reports.shell"
    settings_scope: str = "reports"
    audit_scope: str = "reports"
    notes: str = ""

    @property
    def shell_family(self) -> str:
        return SHELL_REPORT

    @property
    def table_identity(self) -> str:
        return f"reports_{self.table_attr}"

    def permission_for(self, action: str) -> str:
        action = str(action or "").lower()
        if action == "view":
            return self.permission_view
        if action == "print":
            return self.permission_print
        if action == "export":
            return self.permission_export
        return ""


# Network modes are deliberately explicit.  Some reports are built locally from
# service composition (cashbox/warehouse/POS/inventory) while core accounting
# reports have server endpoints.  This prevents the UI from claiming total API
# parity where the implementation is intentionally local/mixed.
REPORT_SHELL_DESCRIPTORS: tuple[ReportShellDescriptor, ...] = (
    ReportShellDescriptor("income_statement", "report_income_statement", "income_tab", "income_table", "income_statement", "/api/reports/income_statement", (REPORT_FILTER_PERIOD,), NETWORK_REMOTE_AVAILABLE),
    ReportShellDescriptor("balance_sheet", "report_balance_sheet", "balance_tab", "balance_table", "balance_sheet", "/api/reports/balance_sheet", (REPORT_FILTER_PERIOD,), NETWORK_REMOTE_AVAILABLE),
    ReportShellDescriptor("warehouse_valuation", "report_warehouse_valuation", "wh_valuation_tab", "wh_valuation_table", "warehouse_valuation", "/api/reports/warehouse/valuation", (REPORT_FILTER_WAREHOUSE, REPORT_FILTER_BRANCH), NETWORK_MIXED, notes="Composed from warehouse balances until server endpoint parity is completed."),
    ReportShellDescriptor("warehouse_balances", "report_warehouse_balances", "wh_balances_tab", "wh_balances_table", "warehouse_balances", "/api/reports/warehouse/balances", (REPORT_FILTER_WAREHOUSE, REPORT_FILTER_BRANCH), NETWORK_MIXED),
    ReportShellDescriptor("warehouse_movements", "report_warehouse_movements", "wh_movements_tab", "wh_movements_table", "warehouse_movements", "/api/reports/warehouse/movements", (REPORT_FILTER_WAREHOUSE, REPORT_FILTER_ITEM, REPORT_FILTER_BRANCH), NETWORK_MIXED),
    ReportShellDescriptor("warehouse_transfers", "report_warehouse_transfers", "wh_transfers_tab", "wh_transfers_table", "warehouse_transfers", "/api/reports/warehouse/transfers", (REPORT_FILTER_WAREHOUSE,), NETWORK_MIXED),
    ReportShellDescriptor("cash_bank_summary", "report_cash_bank_summary", "cash_summary_tab", "cash_summary_table", "cash_bank_summary", "/api/reports/cash-bank/summary", (REPORT_FILTER_CASHBOX, REPORT_FILTER_BANK, REPORT_FILTER_BRANCH), NETWORK_MIXED),
    ReportShellDescriptor("cash_movements", "report_cash_movements", "cash_movements_tab", "cash_movements_table", "cash_bank_movements", "/api/reports/cash-bank/movements", (REPORT_FILTER_CASHBOX, REPORT_FILTER_PERIOD, REPORT_FILTER_BRANCH), NETWORK_MIXED),
    ReportShellDescriptor("bank_movements", "report_bank_movements", "bank_movements_tab", "bank_movements_table", "cash_bank_movements", "/api/reports/cash-bank/movements", (REPORT_FILTER_BANK, REPORT_FILTER_PERIOD, REPORT_FILTER_BRANCH), NETWORK_MIXED),
    ReportShellDescriptor("pos_shifts", "report_pos_shifts", "pos_shifts_tab", "pos_shifts_table", "pos_shifts_report", "/api/reports/pos-shifts", (REPORT_FILTER_PERIOD, REPORT_FILTER_CASHBOX, REPORT_FILTER_BRANCH), NETWORK_MIXED),
    ReportShellDescriptor("trial_balance", "report_trial_balance", "trial_balance_tab", "trial_balance_table", "trial_balance", "/api/reports/trial_balance", (REPORT_FILTER_PERIOD,), NETWORK_REMOTE_AVAILABLE),
    ReportShellDescriptor("customer_statement", "report_customer_statement", "customer_statement_tab", "customer_statement_table", "customer_statement", "/api/reports/customers/<id>/statement", (REPORT_FILTER_CUSTOMER, REPORT_FILTER_PERIOD), NETWORK_REMOTE_AVAILABLE),
    ReportShellDescriptor("supplier_statement", "report_supplier_statement", "supplier_statement_tab", "supplier_statement_table", "supplier_statement", "/api/reports/suppliers/<id>/statement", (REPORT_FILTER_SUPPLIER, REPORT_FILTER_PERIOD), NETWORK_REMOTE_AVAILABLE),
    ReportShellDescriptor("customer_balances", "report_customer_balances", "customer_balances_tab", "customer_balances_table", "customer_balances", "/api/reports/customers/balances", (REPORT_FILTER_CUSTOMER,), NETWORK_REMOTE_AVAILABLE),
    ReportShellDescriptor("supplier_balances", "report_supplier_balances", "supplier_balances_tab", "supplier_balances_table", "supplier_balances", "/api/reports/suppliers/balances", (REPORT_FILTER_SUPPLIER,), NETWORK_REMOTE_AVAILABLE),
    ReportShellDescriptor("customer_aging", "report_customer_aging", "customer_aging_tab", "customer_aging_table", "customer_aging", "/api/reports/customers/aging", (REPORT_FILTER_PERIOD, REPORT_FILTER_CUSTOMER), NETWORK_REMOTE_AVAILABLE),
    ReportShellDescriptor("supplier_aging", "report_supplier_aging", "supplier_aging_tab", "supplier_aging_table", "supplier_aging", "/api/reports/suppliers/aging", (REPORT_FILTER_PERIOD, REPORT_FILTER_SUPPLIER), NETWORK_REMOTE_AVAILABLE),
    ReportShellDescriptor("ledger_reconciliation", "report_ledger_reconciliation", "ledger_reconciliation_tab", "ledger_reconciliation_table", "inventory_ledger_reconciliation", "/api/inventory-ledger/reconciliation", (REPORT_FILTER_ITEM, REPORT_FILTER_WAREHOUSE), NETWORK_MIXED),
    ReportShellDescriptor("ledger_dual_read", "report_ledger_dual_read", "ledger_dual_read_tab", "ledger_dual_read_table", "inventory_ledger_dual_read", "/api/inventory-ledger/dual-read", (REPORT_FILTER_ITEM, REPORT_FILTER_WAREHOUSE), NETWORK_MIXED),
    ReportShellDescriptor("ledger_readiness", "report_ledger_readiness", "ledger_readiness_tab", "ledger_readiness_table", "inventory_ledger_readiness", "/api/inventory-ledger/readiness", (REPORT_FILTER_ITEM, REPORT_FILTER_WAREHOUSE), NETWORK_MIXED),
    ReportShellDescriptor("offline_queue", "report_offline_queue", "offline_queue_tab", "offline_queue_table", "offline_queue_report", "local://offline-queue", (), NETWORK_LOCAL_ONLY, currency_policy=CURRENCY_DISPLAY, branch_policy=BRANCH_NONE, notes="Local client diagnostics by design."),
    ReportShellDescriptor("unit_audit", "report_unit_audit", "unit_audit_tab", "unit_audit_table", "unit_audit_report", "/api/reports/unit-audit", (REPORT_FILTER_ITEM,), NETWORK_MIXED),
    ReportShellDescriptor("item_movement", "report_item_movement", "item_movement_tab", "item_movement_table", "item_movement_report", "/api/reports/item-movement", (REPORT_FILTER_ITEM, REPORT_FILTER_WAREHOUSE, REPORT_FILTER_PERIOD, REPORT_FILTER_BRANCH), NETWORK_MIXED),
    ReportShellDescriptor("invoice_profit", "report_invoice_profit", "invoice_profit_tab", "invoice_profit_table", "invoice_profit_report", "/api/reports/invoice-profit", (REPORT_FILTER_CUSTOMER, REPORT_FILTER_PERIOD, REPORT_FILTER_BRANCH), NETWORK_MIXED),
    ReportShellDescriptor("net_profit", "report_net_profit", "net_profit_tab", "net_profit_table", "net_profit_report", "/api/reports/net-profit", (REPORT_FILTER_PERIOD, REPORT_FILTER_BRANCH), NETWORK_MIXED),
    ReportShellDescriptor("manufacturing_orders", "report_manufacturing_orders", "manufacturing_orders_tab", "manufacturing_orders_table", "manufacturing_orders_report", "/api/reports/manufacturing/orders", (REPORT_FILTER_PERIOD,), NETWORK_MIXED),
    ReportShellDescriptor("product_cost", "report_product_cost", "product_cost_tab", "product_cost_table", "product_cost_report", "/api/reports/product-cost", (REPORT_FILTER_ITEM, REPORT_FILTER_BRANCH), NETWORK_MIXED),
    ReportShellDescriptor("general_ledger", "report_general_ledger", "general_ledger_tab", "general_ledger_table", "accounting_ledger", "/api/reports/accounting/ledger", (REPORT_FILTER_PERIOD,), NETWORK_REMOTE_AVAILABLE),
    ReportShellDescriptor("full_trial_balance", "report_full_trial_balance", "full_trial_balance_tab", "full_trial_balance_table", "full_trial_balance_report", "/api/reports/accounting/trial_balance", (REPORT_FILTER_PERIOD,), NETWORK_REMOTE_AVAILABLE),
    ReportShellDescriptor("slow_items", "report_slow_items", "slow_items_tab", "slow_items_table", "smart_items_report", "/api/reports/smart-items/slow", (REPORT_FILTER_WAREHOUSE, REPORT_FILTER_PERIOD, REPORT_FILTER_BRANCH), NETWORK_MIXED),
    ReportShellDescriptor("top_items", "report_top_items", "top_items_tab", "top_items_table", "smart_items_report", "/api/reports/smart-items/top", (REPORT_FILTER_WAREHOUSE, REPORT_FILTER_PERIOD, REPORT_FILTER_BRANCH), NETWORK_MIXED),
    ReportShellDescriptor("low_items", "report_low_items", "low_items_tab", "low_items_table", "smart_items_report", "/api/reports/smart-items/low", (REPORT_FILTER_WAREHOUSE, REPORT_FILTER_PERIOD, REPORT_FILTER_BRANCH), NETWORK_MIXED),
    ReportShellDescriptor("reorder_items", "report_reorder_items", "reorder_items_tab", "reorder_items_table", "smart_items_report", "/api/reports/smart-items/reorder", (REPORT_FILTER_WAREHOUSE, REPORT_FILTER_BRANCH), NETWORK_MIXED),
    ReportShellDescriptor("report_audit", "report_consistency_audit", "report_audit_tab", "report_audit_table", "report_consistency_audit", "/api/reports/consistency-audit", (REPORT_FILTER_PERIOD,), NETWORK_MIXED),
)


REPORTS_DOCUMENT_DESCRIPTOR = descriptor_for("reports")


def all_report_descriptors() -> tuple[ReportShellDescriptor, ...]:
    return REPORT_SHELL_DESCRIPTORS


def report_descriptor_for_key(report_key: str) -> ReportShellDescriptor | None:
    key = str(report_key or "").strip()
    for descriptor in REPORT_SHELL_DESCRIPTORS:
        if descriptor.report_key == key:
            return descriptor
    return None


def report_descriptor_for_tab_attr(tab_attr: str) -> ReportShellDescriptor | None:
    attr = str(tab_attr or "").strip()
    for descriptor in REPORT_SHELL_DESCRIPTORS:
        if descriptor.tab_attr == attr:
            return descriptor
    return None


def report_descriptor_for_table_attr(table_attr: str) -> ReportShellDescriptor | None:
    attr = str(table_attr or "").strip()
    for descriptor in REPORT_SHELL_DESCRIPTORS:
        if descriptor.table_attr == attr:
            return descriptor
    return None


def report_table_map() -> Mapping[str, str]:
    return {descriptor.tab_attr: descriptor.table_attr for descriptor in REPORT_SHELL_DESCRIPTORS}


def validate_report_descriptor(descriptor: ReportShellDescriptor) -> list[str]:
    warnings: list[str] = []
    for field_name in ("report_key", "title_key", "tab_attr", "table_attr", "service_method", "api_resource", "network_mode", "permission_view", "currency_policy", "audit_scope"):
        if not str(getattr(descriptor, field_name, "") or "").strip():
            warnings.append(f"{descriptor.report_key}: missing {field_name}")
    if descriptor.supports_print and not descriptor.permission_print:
        warnings.append(f"{descriptor.report_key}: supports print without permission_print")
    if descriptor.supports_export and not descriptor.permission_export:
        warnings.append(f"{descriptor.report_key}: supports export without permission_export")
    if descriptor.network_mode == NETWORK_REMOTE_AVAILABLE and not descriptor.api_resource.startswith("/api/"):
        warnings.append(f"{descriptor.report_key}: remote report without /api resource")
    return warnings


def validate_all_report_descriptors() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    seen: set[str] = set()
    for descriptor in REPORT_SHELL_DESCRIPTORS:
        warnings = validate_report_descriptor(descriptor)
        if descriptor.report_key in seen:
            warnings.append(f"{descriptor.report_key}: duplicate report_key")
        seen.add(descriptor.report_key)
        if warnings:
            result[descriptor.report_key] = warnings
    return result


def bind_report_widgets(widget) -> None:
    """Attach stable Report Shell metadata to a ReportsWidget instance.

    This is intentionally best-effort and uses Qt only through duck-typing, so
    importing this module remains PyQt-free.
    """
    if widget is None:
        return
    for descriptor in REPORT_SHELL_DESCRIPTORS:
        tab = getattr(widget, descriptor.tab_attr, None)
        table = getattr(widget, descriptor.table_attr, None)
        for obj in (tab, table):
            if obj is None or not hasattr(obj, "setProperty"):
                continue
            try:
                obj.setProperty("report_key", descriptor.report_key)
                obj.setProperty("report_shell_family", SHELL_REPORT)
                obj.setProperty("report_api_resource", descriptor.api_resource)
                obj.setProperty("report_network_mode", descriptor.network_mode)
                obj.setProperty("report_currency_policy", descriptor.currency_policy)
            except Exception:
                pass
        if table is not None:
            try:
                table.set_table_identity(descriptor.table_identity)
            except Exception:
                pass
