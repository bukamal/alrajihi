# -*- coding: utf-8 -*-
"""Repository package public API with lazy imports.

Importing a single repository submodule must not import all repositories.  This
keeps settings bootstrap isolated from optional accounting/expense/currency
paths.
"""
from __future__ import annotations

from importlib import import_module
from typing import Any, Dict, Tuple

_EXPORTS: Dict[str, Tuple[str, str]] = {
    'UserRepository': ('database.repositories.user_repo', 'UserRepository'),
    'ItemRepository': ('database.repositories.item_repo', 'ItemRepository'),
    'InvoiceRepository': ('database.repositories.invoice_repo', 'InvoiceRepository'),
    'ManufacturingRepository': ('database.repositories.manufacturing_repo', 'ManufacturingRepository'),
    'CustomerRepository': ('database.repositories.customer_repo', 'CustomerRepository'),
    'SupplierRepository': ('database.repositories.supplier_repo', 'SupplierRepository'),
    'VoucherRepository': ('database.repositories.voucher_repo', 'VoucherRepository'),
    'ExpenseRepository': ('database.repositories.expense_repo', 'ExpenseRepository'),
    'InventoryMovementRepository': ('database.repositories.inventory_movement_repo', 'InventoryMovementRepository'),
    'ReportingRepository': ('database.repositories.reporting_repo', 'ReportingRepository'),
    'SettingsRepository': ('database.repositories.settings_repo', 'SettingsRepository'),
    'AuditRepository': ('database.repositories.audit_repo', 'AuditRepository'),
    'WarehouseRepository': ('database.repositories.warehouse_repo', 'WarehouseRepository'),
    'BranchRepository': ('database.repositories.branch_repo', 'BranchRepository'),
}

__all__ = list(_EXPORTS.keys())


def __getattr__(name: str) -> Any:
    try:
        module_name, attr_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module 'database.repositories' has no attribute {name!r}") from exc
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
