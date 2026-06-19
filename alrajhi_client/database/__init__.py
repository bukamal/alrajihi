# -*- coding: utf-8 -*-
"""Database package public API with lazy imports.

Historically this package imported every repository and DAO at module load time.
That made unrelated startup paths expensive and fragile.  In particular,
``settings_service`` creates a local settings gateway which imports
``database.repositories.settings_repo``.  Python initializes the parent
``database`` package before importing that submodule; eager imports here then
pulled in expense/currency code while ``settings_service`` was still only
partially initialized.

Keep the public names for backward compatibility, but resolve them only when a
caller actually asks for them.
"""
from __future__ import annotations

from importlib import import_module
from typing import Any, Dict, Tuple

_EXPORTS: Dict[str, Tuple[str, str]] = {
    # Database setup / connection
    'ensure_db': ('database.migrations', 'ensure_db'),
    'init_database': ('database.migrations', 'init_database'),
    'DatabaseConnection': ('database.connection', 'DatabaseConnection'),

    # Repositories
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
    'CashboxRepository': ('database.repositories.cashbox_repo', 'CashboxRepository'),

    # Legacy DAO singletons
    # Legacy DAO singletons.  Point directly to the concrete submodule rather
    # than the ``database.dao`` package: importing a DAO submodule causes Python
    # to set e.g. ``database.dao.expense_dao`` to the *module* object on the
    # package, which can shadow the lazy package attribute and leak a module
    # where callers expect a singleton instance.
    'reporting_dao': ('database.dao.reporting_dao', 'reporting_dao'),
    'expense_dao': ('database.dao.expense_dao', 'expense_dao'),
    'voucher_dao': ('database.dao.voucher_dao', 'voucher_dao'),
    'invoice_dao': ('database.dao.invoice_dao', 'invoice_dao'),
    'item_dao': ('database.dao.item_dao', 'item_dao'),
    'category_dao': ('database.dao.category_dao', 'category_dao'),
    'inventory_dao': ('database.dao.inventory_dao', 'inventory_dao'),
    'customer_dao': ('database.dao.customer_dao', 'customer_dao'),
    'supplier_dao': ('database.dao.supplier_dao', 'supplier_dao'),
    'manufacturing_dao': ('database.dao.manufacturing_dao', 'manufacturing_dao'),
}

__all__ = list(_EXPORTS.keys())


def __getattr__(name: str) -> Any:
    try:
        module_name, attr_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module 'database' has no attribute {name!r}") from exc
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
