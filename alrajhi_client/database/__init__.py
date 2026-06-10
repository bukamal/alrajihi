# -*- coding: utf-8 -*-
from .migrations import ensure_db, init_database
from .connection import DatabaseConnection
from .repositories.user_repo import UserRepository
from .repositories.item_repo import ItemRepository
from .repositories.invoice_repo import InvoiceRepository
from .repositories.manufacturing_repo import ManufacturingRepository
from .repositories.customer_repo import CustomerRepository
from .repositories.supplier_repo import SupplierRepository
from .repositories.voucher_repo import VoucherRepository
from .repositories.expense_repo import ExpenseRepository
from .repositories.inventory_movement_repo import InventoryMovementRepository
from .repositories.reporting_repo import ReportingRepository
from .repositories.settings_repo import SettingsRepository
from .repositories.audit_repo import AuditRepository

# DAOs للتوافق مع الكود القديم
from .dao import (
    reporting_dao, expense_dao, voucher_dao, invoice_dao,
    item_dao, category_dao, inventory_dao,
    customer_dao, supplier_dao, manufacturing_dao
)

__all__ = [
    'ensure_db', 'init_database', 'DatabaseConnection',
    'UserRepository', 'ItemRepository', 'InvoiceRepository', 'ManufacturingRepository',
    'CustomerRepository', 'SupplierRepository', 'VoucherRepository', 'ExpenseRepository',
    'InventoryMovementRepository', 'ReportingRepository', 'SettingsRepository',
    'AuditRepository',
    'reporting_dao', 'expense_dao', 'voucher_dao', 'invoice_dao',
    'item_dao', 'category_dao', 'inventory_dao',
    'customer_dao', 'supplier_dao', 'manufacturing_dao'
]


