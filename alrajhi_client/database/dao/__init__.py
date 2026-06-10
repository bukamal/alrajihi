from .reporting_dao import ReportingDAO
from .expense_dao import ExpenseDAO
from .voucher_dao import VoucherDAO, voucher_dao
from .invoice_dao import InvoiceDAO, invoice_dao
from .item_dao import ItemDAO, item_dao
from .category_dao import CategoryDAO, category_dao
from .inventory_dao import inventory_dao
from .customer_dao import customer_dao
from .supplier_dao import supplier_dao
from .manufacturing_dao import ManufacturingDAO, manufacturing_dao
from .warehouse_dao import WarehouseDAO, warehouse_dao

reporting_dao = ReportingDAO()
expense_dao = ExpenseDAO()

__all__ = [
    'reporting_dao', 'expense_dao', 'voucher_dao', 'invoice_dao',
    'item_dao', 'category_dao', 'inventory_dao',
    'customer_dao', 'supplier_dao', 'manufacturing_dao', 'warehouse_dao'
]


