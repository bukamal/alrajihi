# -*- coding: utf-8 -*-
"""Legacy DAO public API with lazy imports.

The DAO package used to import and instantiate every DAO singleton at package
load time.  That is unnecessary for most startup paths and can pull optional
services into settings/bootstrap code.  Names remain backward-compatible and are
resolved on first access.
"""
from __future__ import annotations

from importlib import import_module
from typing import Any, Dict, Tuple

_EXPORTS: Dict[str, Tuple[str, str]] = {
    'ReportingDAO': ('database.dao.reporting_dao', 'ReportingDAO'),
    'ExpenseDAO': ('database.dao.expense_dao', 'ExpenseDAO'),
    'VoucherDAO': ('database.dao.voucher_dao', 'VoucherDAO'),
    'InvoiceDAO': ('database.dao.invoice_dao', 'InvoiceDAO'),
    'ItemDAO': ('database.dao.item_dao', 'ItemDAO'),
    'CategoryDAO': ('database.dao.category_dao', 'CategoryDAO'),
    'ManufacturingDAO': ('database.dao.manufacturing_dao', 'ManufacturingDAO'),
    'WarehouseDAO': ('database.dao.warehouse_dao', 'WarehouseDAO'),
    'BranchDAO': ('database.dao.branch_dao', 'BranchDAO'),
    'CashboxDAO': ('database.dao.cashbox_dao', 'CashboxDAO'),

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
    'warehouse_dao': ('database.dao.warehouse_dao', 'warehouse_dao'),
    'branch_dao': ('database.dao.branch_dao', 'branch_dao'),
    'cashbox_dao': ('database.dao.cashbox_dao', 'cashbox_dao'),
}

__all__ = list(_EXPORTS.keys())


def __getattr__(name: str) -> Any:
    try:
        module_name, attr_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module 'database.dao' has no attribute {name!r}") from exc
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
