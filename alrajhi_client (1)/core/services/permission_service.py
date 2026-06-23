# -*- coding: utf-8 -*-
"""Runtime permission policy driven by SettingsService.

Phase 146 introduces a lightweight policy layer so operational screens can ask
one stable question (can/cannot) instead of reading scattered settings keys.
It is intentionally conservative: admin is always allowed, unknown roles are
restricted by the configured global policy.
"""
from __future__ import annotations

from typing import Dict, Iterable

from auth.session import UserSession
from core.services.settings_service import settings_service
from core.services.rbac_service import rbac_service
from gateways.system_gateway import create_system_gateway


class PermissionService:
    ACTION_HIDE_PROFIT = 'hide_profit'
    ACTION_DELETE = 'delete_records'
    ACTION_EDIT_INVOICES = 'edit_invoices'
    ACTION_EDIT_RETURNS = 'edit_returns'
    ACTION_EDIT_ITEMS = 'edit_items'
    ACTION_PRINT_BARCODES = 'print_barcodes'
    ACTION_VIEW_ITEM_COSTS = 'view_item_costs'
    ACTION_EDIT_OPENING_STOCK = 'edit_opening_stock'
    ACTION_CATEGORY_VIEW = 'category_view'
    ACTION_CATEGORY_CREATE = 'category_create'
    ACTION_CATEGORY_EDIT = 'category_edit'
    ACTION_CATEGORY_ARCHIVE = 'category_archive'
    ACTION_CATEGORY_RESTORE = 'category_restore'
    ACTION_USE_POS = 'use_pos'
    ACTION_POS_SUSPEND = 'pos_suspend'
    ACTION_POS_RESUME = 'pos_resume'
    ACTION_POS_REMOVE_LINE = 'pos_remove_line'
    ACTION_POS_CLEAR_CART = 'pos_clear_cart'
    ACTION_POS_OPEN_SHIFT = 'pos_open_shift'
    ACTION_POS_CLOSE_SHIFT = 'pos_close_shift'
    ACTION_POS_PRINT_RECEIPT = 'pos_print_receipt'
    ACTION_USE_RESTAURANT = 'restaurant_use'
    ACTION_RESTAURANT_OPEN_SESSION = 'restaurant_open_session'
    ACTION_RESTAURANT_ADD_LINE = 'restaurant_add_line'
    ACTION_RESTAURANT_SEND_KITCHEN = 'restaurant_send_kitchen'
    ACTION_RESTAURANT_ADJUST_BILL = 'restaurant_adjust_bill'
    ACTION_RESTAURANT_RECORD_PAYMENT = 'restaurant_record_payment'
    ACTION_RESTAURANT_CHECKOUT = 'restaurant_checkout'
    ACTION_RESTAURANT_UPDATE_KITCHEN_STATUS = 'restaurant_update_kitchen_status'
    ACTION_RESTAURANT_PRINT_RECEIPT = 'restaurant_print_receipt'
    ACTION_RESTAURANT_PRINT_KITCHEN_TICKET = 'restaurant_print_kitchen_ticket'
    ACTION_RESTAURANT_RESERVE_TABLE = 'restaurant_reserve_table'
    ACTION_RESTAURANT_CANCEL_RESERVATION = 'restaurant_cancel_reservation'
    ACTION_RESTAURANT_TRANSFER_TABLE = 'restaurant_transfer_table'
    ACTION_RESTAURANT_MERGE_TABLES = 'restaurant_merge_tables'
    ACTION_RESTAURANT_MOVE_ORDER_LINE = 'restaurant_move_order_line'
    ACTION_RESTAURANT_SPLIT_BILL = 'restaurant_split_bill'
    ACTION_RESTAURANT_WAITER_WORKFLOW = 'restaurant_waiter_workflow'
    ACTION_RESTAURANT_KITCHEN_STATION_MANAGE = 'restaurant_kitchen_station_manage'
    ACTION_RESTAURANT_MODIFIER_MANAGE = 'restaurant_modifier_manage'
    ACTION_RESTAURANT_RECIPE_MANAGE = 'restaurant_recipe_manage'
    ACTION_RESTAURANT_DELIVERY_TAKEAWAY = 'restaurant_delivery_takeaway'
    ACTION_RESTAURANT_PRINTER_MANAGE = 'restaurant_printer_manage'
    ACTION_RESTAURANT_PRINT_QUEUE = 'restaurant_print_queue'
    ACTION_RESTAURANT_VIEW_ANALYTICS = 'restaurant_view_analytics'
    ACTION_USE_MANUFACTURING = 'manufacturing_use'
    ACTION_MANUFACTURING_BOM_CREATE = 'manufacturing_bom_create'
    ACTION_MANUFACTURING_BOM_EDIT = 'manufacturing_bom_edit'
    ACTION_MANUFACTURING_BOM_DELETE = 'manufacturing_bom_delete'
    ACTION_MANUFACTURING_ORDER_CREATE = 'manufacturing_order_create'
    ACTION_MANUFACTURING_ORDER_START = 'manufacturing_order_start'
    ACTION_MANUFACTURING_MATERIAL_CONSUME = 'manufacturing_material_consume'
    ACTION_MANUFACTURING_OUTPUT_COMPLETE = 'manufacturing_output_complete'
    ACTION_MANUFACTURING_ORDER_CANCEL = 'manufacturing_order_cancel'
    ACTION_MANUFACTURING_ORDER_DELETE = 'manufacturing_order_delete'
    ACTION_MANUFACTURING_ORDER_REVERSE = 'manufacturing_order_reverse'
    ACTION_MANUFACTURING_CONSUMPTION_DELETE = 'manufacturing_consumption_delete'
    ACTION_MANUFACTURING_OUTPUT_DELETE = 'manufacturing_output_delete'
    ACTION_MANUFACTURING_COST_VIEW = 'manufacturing_cost_view'
    ACTION_MANUFACTURING_PRINT = 'manufacturing_print'
    ACTION_USE_INVENTORY = 'inventory_use'
    ACTION_INVENTORY_WAREHOUSE_CREATE = 'inventory_warehouse_create'
    ACTION_INVENTORY_WAREHOUSE_EDIT = 'inventory_warehouse_edit'
    ACTION_INVENTORY_WAREHOUSE_ARCHIVE = 'inventory_warehouse_archive'
    ACTION_INVENTORY_BALANCE_VIEW = 'inventory_balance_view'
    ACTION_INVENTORY_MOVEMENT_VIEW = 'inventory_movement_view'
    ACTION_INVENTORY_DIRECT_MOVEMENT = 'inventory_direct_movement'
    ACTION_INVENTORY_TRANSFER_CREATE = 'inventory_transfer_create'
    ACTION_INVENTORY_TRANSFER_CANCEL = 'inventory_transfer_cancel'
    ACTION_INVENTORY_LEDGER_VIEW = 'inventory_ledger_view'
    ACTION_INVENTORY_LEDGER_BACKFILL = 'inventory_ledger_backfill'
    ACTION_INVENTORY_RECONCILE = 'inventory_reconcile'
    ACTION_INVENTORY_PRINT = 'inventory_print'
    ACTION_USE_FINANCE = 'finance_use'
    ACTION_CASHBOX_CREATE = 'finance_cashbox_create'
    ACTION_CASHBOX_EDIT = 'finance_cashbox_edit'
    ACTION_CASHBOX_ARCHIVE = 'finance_cashbox_archive'
    ACTION_BANK_CREATE = 'finance_bank_create'
    ACTION_BANK_EDIT = 'finance_bank_edit'
    ACTION_BANK_ARCHIVE = 'finance_bank_archive'
    ACTION_FINANCE_MOVEMENTS_VIEW = 'finance_movements_view'
    ACTION_FINANCE_SHIFTS_VIEW = 'finance_shifts_view'
    ACTION_VOUCHER_CREATE = 'finance_voucher_create'
    ACTION_VOUCHER_EDIT = 'finance_voucher_edit'
    ACTION_VOUCHER_DELETE = 'finance_voucher_delete'
    ACTION_VOUCHER_PRINT = 'finance_voucher_print'
    ACTION_VOUCHER_VIEW = 'finance_voucher_view'
    ACTION_EXPENSE_CREATE = 'finance_expense_create'
    ACTION_EXPENSE_EDIT = 'finance_expense_edit'
    ACTION_EXPENSE_DELETE = 'finance_expense_delete'
    ACTION_EXPENSE_PRINT = 'finance_expense_print'
    ACTION_EXPENSE_VIEW = 'finance_expense_view'
    ACTION_VIEW_REPORTS = 'view_reports'
    ACTION_EXPORT_REPORTS = 'export_reports'
    ACTION_VIEW_ALL_BRANCHES = 'view_all_branches'
    ACTION_MANAGE_ALL_BRANCHES = 'manage_all_branches'
    ACTION_USERS_MANAGE = 'users_manage'
    ACTION_PARTY_VIEW = 'party_view'
    ACTION_CUSTOMER_VIEW = 'customer_view'
    ACTION_CUSTOMER_CREATE = 'customer_create'
    ACTION_CUSTOMER_EDIT = 'customer_edit'
    ACTION_CUSTOMER_DELETE = 'customer_delete'
    ACTION_SUPPLIER_VIEW = 'supplier_view'
    ACTION_SUPPLIER_CREATE = 'supplier_create'
    ACTION_SUPPLIER_EDIT = 'supplier_edit'
    ACTION_SUPPLIER_DELETE = 'supplier_delete'

    DEFAULTS = {
        ACTION_HIDE_PROFIT: False,
        ACTION_DELETE: True,
        ACTION_EDIT_INVOICES: True,
        ACTION_EDIT_RETURNS: True,
        ACTION_EDIT_ITEMS: True,
        ACTION_PRINT_BARCODES: True,
        ACTION_VIEW_ITEM_COSTS: True,
        ACTION_EDIT_OPENING_STOCK: True,
        ACTION_CATEGORY_VIEW: True,
        ACTION_CATEGORY_CREATE: True,
        ACTION_CATEGORY_EDIT: True,
        ACTION_CATEGORY_ARCHIVE: True,
        ACTION_CATEGORY_RESTORE: True,
        ACTION_USE_POS: True,
        ACTION_POS_SUSPEND: True,
        ACTION_POS_RESUME: True,
        ACTION_POS_REMOVE_LINE: True,
        ACTION_POS_CLEAR_CART: True,
        ACTION_POS_OPEN_SHIFT: True,
        ACTION_POS_CLOSE_SHIFT: True,
        ACTION_POS_PRINT_RECEIPT: True,
        ACTION_USE_RESTAURANT: True,
        ACTION_RESTAURANT_OPEN_SESSION: True,
        ACTION_RESTAURANT_ADD_LINE: True,
        ACTION_RESTAURANT_SEND_KITCHEN: True,
        ACTION_RESTAURANT_ADJUST_BILL: True,
        ACTION_RESTAURANT_RECORD_PAYMENT: True,
        ACTION_RESTAURANT_CHECKOUT: True,
        ACTION_RESTAURANT_UPDATE_KITCHEN_STATUS: True,
        ACTION_RESTAURANT_PRINT_RECEIPT: True,
        ACTION_RESTAURANT_PRINT_KITCHEN_TICKET: True,
        ACTION_RESTAURANT_RESERVE_TABLE: True,
        ACTION_RESTAURANT_CANCEL_RESERVATION: True,
        ACTION_RESTAURANT_TRANSFER_TABLE: True,
        ACTION_RESTAURANT_MERGE_TABLES: True,
        ACTION_RESTAURANT_MOVE_ORDER_LINE: True,
        ACTION_RESTAURANT_SPLIT_BILL: True,
        ACTION_RESTAURANT_WAITER_WORKFLOW: True,
        ACTION_RESTAURANT_KITCHEN_STATION_MANAGE: True,
        ACTION_RESTAURANT_MODIFIER_MANAGE: True,
        ACTION_RESTAURANT_RECIPE_MANAGE: True,
        ACTION_RESTAURANT_DELIVERY_TAKEAWAY: True,
        ACTION_RESTAURANT_PRINTER_MANAGE: True,
        ACTION_RESTAURANT_PRINT_QUEUE: True,
        ACTION_RESTAURANT_VIEW_ANALYTICS: True,
        ACTION_USE_MANUFACTURING: True,
        ACTION_MANUFACTURING_BOM_CREATE: True,
        ACTION_MANUFACTURING_BOM_EDIT: True,
        ACTION_MANUFACTURING_BOM_DELETE: True,
        ACTION_MANUFACTURING_ORDER_CREATE: True,
        ACTION_MANUFACTURING_ORDER_START: True,
        ACTION_MANUFACTURING_MATERIAL_CONSUME: True,
        ACTION_MANUFACTURING_OUTPUT_COMPLETE: True,
        ACTION_MANUFACTURING_ORDER_CANCEL: True,
        ACTION_MANUFACTURING_ORDER_DELETE: True,
        ACTION_MANUFACTURING_ORDER_REVERSE: True,
        ACTION_MANUFACTURING_CONSUMPTION_DELETE: True,
        ACTION_MANUFACTURING_OUTPUT_DELETE: True,
        ACTION_MANUFACTURING_COST_VIEW: True,
        ACTION_MANUFACTURING_PRINT: True,
        ACTION_USE_INVENTORY: True,
        ACTION_INVENTORY_WAREHOUSE_CREATE: True,
        ACTION_INVENTORY_WAREHOUSE_EDIT: True,
        ACTION_INVENTORY_WAREHOUSE_ARCHIVE: True,
        ACTION_INVENTORY_BALANCE_VIEW: True,
        ACTION_INVENTORY_MOVEMENT_VIEW: True,
        ACTION_INVENTORY_DIRECT_MOVEMENT: True,
        ACTION_INVENTORY_TRANSFER_CREATE: True,
        ACTION_INVENTORY_TRANSFER_CANCEL: True,
        ACTION_INVENTORY_LEDGER_VIEW: True,
        ACTION_INVENTORY_LEDGER_BACKFILL: False,
        ACTION_INVENTORY_RECONCILE: True,
        ACTION_INVENTORY_PRINT: True,
        ACTION_USE_FINANCE: True,
        ACTION_CASHBOX_CREATE: True,
        ACTION_CASHBOX_EDIT: True,
        ACTION_CASHBOX_ARCHIVE: True,
        ACTION_BANK_CREATE: True,
        ACTION_BANK_EDIT: True,
        ACTION_BANK_ARCHIVE: True,
        ACTION_FINANCE_MOVEMENTS_VIEW: True,
        ACTION_FINANCE_SHIFTS_VIEW: True,
        ACTION_VOUCHER_CREATE: True,
        ACTION_VOUCHER_EDIT: True,
        ACTION_VOUCHER_DELETE: True,
        ACTION_VOUCHER_PRINT: True,
        ACTION_VOUCHER_VIEW: True,
        ACTION_EXPENSE_CREATE: True,
        ACTION_EXPENSE_EDIT: True,
        ACTION_EXPENSE_DELETE: True,
        ACTION_EXPENSE_PRINT: True,
        ACTION_EXPENSE_VIEW: True,
        ACTION_VIEW_REPORTS: True,
        ACTION_EXPORT_REPORTS: True,
        ACTION_VIEW_ALL_BRANCHES: False,
        ACTION_MANAGE_ALL_BRANCHES: False,
        ACTION_USERS_MANAGE: False,
        ACTION_PARTY_VIEW: True,
        ACTION_CUSTOMER_VIEW: True,
        ACTION_CUSTOMER_CREATE: True,
        ACTION_CUSTOMER_EDIT: True,
        ACTION_CUSTOMER_DELETE: True,
        ACTION_SUPPLIER_VIEW: True,
        ACTION_SUPPLIER_CREATE: True,
        ACTION_SUPPLIER_EDIT: True,
        ACTION_SUPPLIER_DELETE: True,
    }

    def __init__(self, system_gateway=None):
        self.system_gateway = system_gateway or create_system_gateway()

    def current_role(self) -> str:
        return (UserSession.get_current_user_role() or 'admin').strip().lower()

    def is_admin(self, role: str | None = None) -> bool:
        return (role or self.current_role()).strip().lower() == 'admin'

    def _blocked_roles(self, key: str) -> set[str]:
        raw = settings_service.get(key, '') or ''
        return {x.strip().lower() for x in str(raw).split(',') if x.strip()}

    def policy(self) -> Dict[str, object]:
        return {
            'hide_profit_for_non_admin': settings_service.get_bool('security/hide_profit_for_non_admin', False),
            'prevent_delete_for_non_admin': settings_service.get_bool('security/prevent_delete_for_non_admin', False),
            'prevent_invoice_edit_for_non_admin': settings_service.get_bool('security/prevent_invoice_edit_for_non_admin', False),
            'prevent_return_edit_for_non_admin': settings_service.get_bool('security/prevent_return_edit_for_non_admin', False),
            'restrict_reports_to_admin': settings_service.get_bool('security/restrict_reports_to_admin', False),
            'restrict_report_export_to_admin': settings_service.get_bool('security/restrict_report_export_to_admin', False),
            'blocked_report_roles': sorted(self._blocked_roles('security/blocked_report_roles')),
            'restrict_branch_scope_for_non_admin': settings_service.get_bool('security/restrict_branch_scope_for_non_admin', True),
            'allow_non_admin_view_all_branches': settings_service.get_bool('security/allow_non_admin_view_all_branches', False),
            'allow_non_admin_manage_all_branches': settings_service.get_bool('security/allow_non_admin_manage_all_branches', False),
        }

    def can(self, action: str, role: str | None = None) -> bool:
        role = (role or self.current_role()).strip().lower()
        allowed = True
        reason = ''
        if self.is_admin(role):
            return True
        try:
            # Phase157: database-backed RBAC overrides coarse legacy settings when available.
            if rbac_service.list_roles():
                mapped = {
                    self.ACTION_DELETE: 'invoices.delete',
                    self.ACTION_EDIT_INVOICES: 'invoices.edit',
                    self.ACTION_EDIT_RETURNS: 'returns.edit',
                    self.ACTION_EDIT_ITEMS: 'items.edit',
                    self.ACTION_PRINT_BARCODES: 'items.barcodes.print',
                    self.ACTION_VIEW_ITEM_COSTS: 'items.cost.view',
                    self.ACTION_EDIT_OPENING_STOCK: 'items.opening_stock.edit',
                    self.ACTION_CATEGORY_VIEW: 'categories.view',
                    self.ACTION_CATEGORY_CREATE: 'categories.create',
                    self.ACTION_CATEGORY_EDIT: 'categories.edit',
                    self.ACTION_CATEGORY_ARCHIVE: 'categories.archive',
                    self.ACTION_CATEGORY_RESTORE: 'categories.restore',
                    self.ACTION_USE_POS: 'pos.use',
                    self.ACTION_POS_SUSPEND: 'pos.suspend',
                    self.ACTION_POS_RESUME: 'pos.resume',
                    self.ACTION_POS_REMOVE_LINE: 'pos.line.remove',
                    self.ACTION_POS_CLEAR_CART: 'pos.cart.clear',
                    self.ACTION_POS_OPEN_SHIFT: 'pos.shift.open',
                    self.ACTION_POS_CLOSE_SHIFT: 'pos.shift.close',
                    self.ACTION_POS_PRINT_RECEIPT: 'pos.receipt.print',
                    self.ACTION_USE_RESTAURANT: 'restaurant.use',
                    self.ACTION_RESTAURANT_OPEN_SESSION: 'restaurant.session.open',
                    self.ACTION_RESTAURANT_ADD_LINE: 'restaurant.line.add',
                    self.ACTION_RESTAURANT_SEND_KITCHEN: 'restaurant.kitchen.send',
                    self.ACTION_RESTAURANT_ADJUST_BILL: 'restaurant.bill.adjust',
                    self.ACTION_RESTAURANT_RECORD_PAYMENT: 'restaurant.payment.record',
                    self.ACTION_RESTAURANT_CHECKOUT: 'restaurant.checkout',
                    self.ACTION_RESTAURANT_UPDATE_KITCHEN_STATUS: 'restaurant.kitchen.status.update',
                    self.ACTION_RESTAURANT_PRINT_RECEIPT: 'restaurant.receipt.print',
                    self.ACTION_RESTAURANT_PRINT_KITCHEN_TICKET: 'restaurant.kitchen_ticket.print',
                    self.ACTION_RESTAURANT_RESERVE_TABLE: 'restaurant.table.reserve',
                    self.ACTION_RESTAURANT_CANCEL_RESERVATION: 'restaurant.reservation.cancel',
                    self.ACTION_RESTAURANT_TRANSFER_TABLE: 'restaurant.table.transfer',
                    self.ACTION_RESTAURANT_MERGE_TABLES: 'restaurant.table.merge',
                    self.ACTION_RESTAURANT_MOVE_ORDER_LINE: 'restaurant.line.move',
                    self.ACTION_RESTAURANT_SPLIT_BILL: 'restaurant.bill.split',
                    self.ACTION_RESTAURANT_WAITER_WORKFLOW: 'restaurant.waiter.workflow',
                    self.ACTION_RESTAURANT_KITCHEN_STATION_MANAGE: 'restaurant.kitchen_station.manage',
                    self.ACTION_RESTAURANT_MODIFIER_MANAGE: 'restaurant.modifier.manage',
                    self.ACTION_RESTAURANT_RECIPE_MANAGE: 'restaurant.recipe.manage',
                    self.ACTION_RESTAURANT_DELIVERY_TAKEAWAY: 'restaurant.delivery_takeaway',
                    self.ACTION_RESTAURANT_PRINTER_MANAGE: 'restaurant.printer.manage',
                    self.ACTION_RESTAURANT_PRINT_QUEUE: 'restaurant.print_queue.manage',
                    self.ACTION_RESTAURANT_VIEW_ANALYTICS: 'restaurant.analytics.view',
                    self.ACTION_USE_MANUFACTURING: 'manufacturing.use',
                    self.ACTION_MANUFACTURING_BOM_CREATE: 'manufacturing.bom.create',
                    self.ACTION_MANUFACTURING_BOM_EDIT: 'manufacturing.bom.edit',
                    self.ACTION_MANUFACTURING_BOM_DELETE: 'manufacturing.bom.delete',
                    self.ACTION_MANUFACTURING_ORDER_CREATE: 'manufacturing.order.create',
                    self.ACTION_MANUFACTURING_ORDER_START: 'manufacturing.order.start',
                    self.ACTION_MANUFACTURING_MATERIAL_CONSUME: 'manufacturing.material.consume',
                    self.ACTION_MANUFACTURING_OUTPUT_COMPLETE: 'manufacturing.output.complete',
                    self.ACTION_MANUFACTURING_ORDER_CANCEL: 'manufacturing.order.cancel',
                    self.ACTION_MANUFACTURING_ORDER_DELETE: 'manufacturing.order.delete',
                    self.ACTION_MANUFACTURING_ORDER_REVERSE: 'manufacturing.order.reverse',
                    self.ACTION_MANUFACTURING_CONSUMPTION_DELETE: 'manufacturing.consumption.delete',
                    self.ACTION_MANUFACTURING_OUTPUT_DELETE: 'manufacturing.output.delete',
                    self.ACTION_MANUFACTURING_COST_VIEW: 'manufacturing.cost.view',
                    self.ACTION_MANUFACTURING_PRINT: 'manufacturing.print',
                    self.ACTION_USE_INVENTORY: 'inventory.use',
                    self.ACTION_INVENTORY_WAREHOUSE_CREATE: 'inventory.warehouse.create',
                    self.ACTION_INVENTORY_WAREHOUSE_EDIT: 'inventory.warehouse.edit',
                    self.ACTION_INVENTORY_WAREHOUSE_ARCHIVE: 'inventory.warehouse.archive',
                    self.ACTION_INVENTORY_BALANCE_VIEW: 'inventory.balance.view',
                    self.ACTION_INVENTORY_MOVEMENT_VIEW: 'inventory.movement.view',
                    self.ACTION_INVENTORY_DIRECT_MOVEMENT: 'inventory.movement.direct',
                    self.ACTION_INVENTORY_TRANSFER_CREATE: 'inventory.transfer.create',
                    self.ACTION_INVENTORY_TRANSFER_CANCEL: 'inventory.transfer.cancel',
                    self.ACTION_INVENTORY_LEDGER_VIEW: 'inventory.ledger.view',
                    self.ACTION_INVENTORY_LEDGER_BACKFILL: 'inventory.ledger.backfill',
                    self.ACTION_INVENTORY_RECONCILE: 'inventory.reconcile',
                    self.ACTION_INVENTORY_PRINT: 'inventory.print',
                    self.ACTION_USE_FINANCE: 'finance.use',
                    self.ACTION_CASHBOX_CREATE: 'finance.cashbox.create',
                    self.ACTION_CASHBOX_EDIT: 'finance.cashbox.edit',
                    self.ACTION_CASHBOX_ARCHIVE: 'finance.cashbox.archive',
                    self.ACTION_BANK_CREATE: 'finance.bank.create',
                    self.ACTION_BANK_EDIT: 'finance.bank.edit',
                    self.ACTION_BANK_ARCHIVE: 'finance.bank.archive',
                    self.ACTION_FINANCE_MOVEMENTS_VIEW: 'finance.movements.view',
                    self.ACTION_FINANCE_SHIFTS_VIEW: 'finance.shifts.view',
                    self.ACTION_VOUCHER_CREATE: 'finance.voucher.create',
                    self.ACTION_VOUCHER_EDIT: 'finance.voucher.edit',
                    self.ACTION_VOUCHER_DELETE: 'finance.voucher.delete',
                    self.ACTION_VOUCHER_PRINT: 'finance.voucher.print',
                    self.ACTION_VOUCHER_VIEW: 'finance.voucher.view',
                    self.ACTION_EXPENSE_CREATE: 'finance.expense.create',
                    self.ACTION_EXPENSE_EDIT: 'finance.expense.edit',
                    self.ACTION_EXPENSE_DELETE: 'finance.expense.delete',
                    self.ACTION_EXPENSE_PRINT: 'finance.expense.print',
                    self.ACTION_EXPENSE_VIEW: 'finance.expense.view',
                    self.ACTION_VIEW_REPORTS: 'reports.view',
                    self.ACTION_EXPORT_REPORTS: 'reports.export',
                    self.ACTION_VIEW_ALL_BRANCHES: 'branches.view_all',
                    self.ACTION_MANAGE_ALL_BRANCHES: 'branches.manage_all',
                    self.ACTION_USERS_MANAGE: 'users.manage',
                    self.ACTION_PARTY_VIEW: 'parties.view',
                    self.ACTION_CUSTOMER_VIEW: 'customers.view',
                    self.ACTION_CUSTOMER_CREATE: 'customers.create',
                    self.ACTION_CUSTOMER_EDIT: 'customers.edit',
                    self.ACTION_CUSTOMER_DELETE: 'customers.delete',
                    self.ACTION_SUPPLIER_VIEW: 'suppliers.view',
                    self.ACTION_SUPPLIER_CREATE: 'suppliers.create',
                    self.ACTION_SUPPLIER_EDIT: 'suppliers.edit',
                    self.ACTION_SUPPLIER_DELETE: 'suppliers.delete',
                }.get(action)
                if mapped:
                    allowed = rbac_service.has_permission(mapped)
                    if not allowed:
                        self.log_event('RBAC_DENIED', action=mapped, allowed=False, reason='rbac_permission_missing', role=role)
                    return allowed
        except Exception:
            pass
        if action == self.ACTION_DELETE and settings_service.get_bool('security/prevent_delete_for_non_admin', False):
            allowed, reason = False, 'prevent_delete_for_non_admin'
        elif action == self.ACTION_EDIT_INVOICES and settings_service.get_bool('security/prevent_invoice_edit_for_non_admin', False):
            allowed, reason = False, 'prevent_invoice_edit_for_non_admin'
        elif action == self.ACTION_EDIT_RETURNS and settings_service.get_bool('security/prevent_return_edit_for_non_admin', False):
            allowed, reason = False, 'prevent_return_edit_for_non_admin'
        elif action == self.ACTION_EDIT_ITEMS and settings_service.get_bool('security/prevent_item_edit_for_non_admin', False):
            allowed, reason = False, 'prevent_item_edit_for_non_admin'
        elif action == self.ACTION_PRINT_BARCODES and settings_service.get_bool('security/restrict_barcode_print_to_admin', False):
            allowed, reason = False, 'restrict_barcode_print_to_admin'
        elif action == self.ACTION_VIEW_ITEM_COSTS and settings_service.get_bool('security/hide_item_cost_for_non_admin', settings_service.get_bool('security/hide_profit_for_non_admin', False)):
            allowed, reason = False, 'hide_item_cost_for_non_admin'
        elif action == self.ACTION_EDIT_OPENING_STOCK and settings_service.get_bool('materials/security/restrict_opening_stock_edit_to_admin', False):
            allowed, reason = False, 'restrict_opening_stock_edit_to_admin'
        elif action == self.ACTION_CATEGORY_VIEW and settings_service.get_bool('security/restrict_categories_view_to_admin', False):
            allowed, reason = False, 'restrict_categories_view_to_admin'
        elif action == self.ACTION_CATEGORY_CREATE and settings_service.get_bool('security/restrict_category_create_to_admin', False):
            allowed, reason = False, 'restrict_category_create_to_admin'
        elif action == self.ACTION_CATEGORY_EDIT and settings_service.get_bool('security/restrict_category_edit_to_admin', False):
            allowed, reason = False, 'restrict_category_edit_to_admin'
        elif action == self.ACTION_CATEGORY_ARCHIVE and settings_service.get_bool('security/restrict_category_archive_to_admin', False):
            allowed, reason = False, 'restrict_category_archive_to_admin'
        elif action == self.ACTION_CATEGORY_RESTORE and settings_service.get_bool('security/restrict_category_restore_to_admin', False):
            allowed, reason = False, 'restrict_category_restore_to_admin'
        elif action == self.ACTION_USE_POS and settings_service.get_bool('security/restrict_pos_to_authorized_users', False):
            allowed, reason = False, 'restrict_pos_to_authorized_users'
        elif action == self.ACTION_POS_SUSPEND and settings_service.get_bool('security/restrict_pos_suspend_to_admin', False):
            allowed, reason = False, 'restrict_pos_suspend_to_admin'
        elif action == self.ACTION_POS_RESUME and settings_service.get_bool('security/restrict_pos_resume_to_admin', False):
            allowed, reason = False, 'restrict_pos_resume_to_admin'
        elif action == self.ACTION_POS_REMOVE_LINE and settings_service.get_bool('security/restrict_pos_remove_line_to_admin', False):
            allowed, reason = False, 'restrict_pos_remove_line_to_admin'
        elif action == self.ACTION_POS_CLEAR_CART and settings_service.get_bool('security/restrict_pos_clear_cart_to_admin', False):
            allowed, reason = False, 'restrict_pos_clear_cart_to_admin'
        elif action == self.ACTION_POS_OPEN_SHIFT and settings_service.get_bool('security/restrict_pos_open_shift_to_admin', False):
            allowed, reason = False, 'restrict_pos_open_shift_to_admin'
        elif action == self.ACTION_POS_CLOSE_SHIFT and settings_service.get_bool('security/restrict_pos_close_shift_to_admin', False):
            allowed, reason = False, 'restrict_pos_close_shift_to_admin'
        elif action == self.ACTION_POS_PRINT_RECEIPT and settings_service.get_bool('security/restrict_pos_receipt_print_to_admin', False):
            allowed, reason = False, 'restrict_pos_receipt_print_to_admin'
        elif action == self.ACTION_USE_RESTAURANT and settings_service.get_bool('security/restrict_restaurant_to_authorized_users', False):
            allowed, reason = False, 'restrict_restaurant_to_authorized_users'
        elif action == self.ACTION_RESTAURANT_OPEN_SESSION and settings_service.get_bool('security/restrict_restaurant_open_session_to_admin', False):
            allowed, reason = False, 'restrict_restaurant_open_session_to_admin'
        elif action == self.ACTION_RESTAURANT_ADD_LINE and settings_service.get_bool('security/restrict_restaurant_add_line_to_admin', False):
            allowed, reason = False, 'restrict_restaurant_add_line_to_admin'
        elif action == self.ACTION_RESTAURANT_SEND_KITCHEN and settings_service.get_bool('security/restrict_restaurant_send_kitchen_to_admin', False):
            allowed, reason = False, 'restrict_restaurant_send_kitchen_to_admin'
        elif action == self.ACTION_RESTAURANT_ADJUST_BILL and settings_service.get_bool('security/restrict_restaurant_adjust_bill_to_admin', False):
            allowed, reason = False, 'restrict_restaurant_adjust_bill_to_admin'
        elif action == self.ACTION_RESTAURANT_RECORD_PAYMENT and settings_service.get_bool('security/restrict_restaurant_payment_to_admin', False):
            allowed, reason = False, 'restrict_restaurant_payment_to_admin'
        elif action == self.ACTION_RESTAURANT_CHECKOUT and settings_service.get_bool('security/restrict_restaurant_checkout_to_admin', False):
            allowed, reason = False, 'restrict_restaurant_checkout_to_admin'
        elif action == self.ACTION_RESTAURANT_UPDATE_KITCHEN_STATUS and settings_service.get_bool('security/restrict_restaurant_kitchen_status_to_admin', False):
            allowed, reason = False, 'restrict_restaurant_kitchen_status_to_admin'
        elif action == self.ACTION_RESTAURANT_PRINT_RECEIPT and settings_service.get_bool('security/restrict_restaurant_receipt_print_to_admin', False):
            allowed, reason = False, 'restrict_restaurant_receipt_print_to_admin'
        elif action == self.ACTION_RESTAURANT_PRINT_KITCHEN_TICKET and settings_service.get_bool('security/restrict_restaurant_kitchen_ticket_print_to_admin', False):
            allowed, reason = False, 'restrict_restaurant_kitchen_ticket_print_to_admin'
        elif action == self.ACTION_RESTAURANT_RESERVE_TABLE and settings_service.get_bool('security/restrict_restaurant_reservation_to_admin', False):
            allowed, reason = False, 'restrict_restaurant_reservation_to_admin'
        elif action == self.ACTION_RESTAURANT_CANCEL_RESERVATION and settings_service.get_bool('security/restrict_restaurant_reservation_cancel_to_admin', False):
            allowed, reason = False, 'restrict_restaurant_reservation_cancel_to_admin'
        elif action == self.ACTION_RESTAURANT_TRANSFER_TABLE and settings_service.get_bool('security/restrict_restaurant_table_transfer_to_admin', False):
            allowed, reason = False, 'restrict_restaurant_table_transfer_to_admin'
        elif action == self.ACTION_RESTAURANT_MERGE_TABLES and settings_service.get_bool('security/restrict_restaurant_table_merge_to_admin', False):
            allowed, reason = False, 'restrict_restaurant_table_merge_to_admin'
        elif action == self.ACTION_RESTAURANT_MOVE_ORDER_LINE and settings_service.get_bool('security/restrict_restaurant_line_move_to_admin', False):
            allowed, reason = False, 'restrict_restaurant_line_move_to_admin'
        elif action == self.ACTION_RESTAURANT_SPLIT_BILL and settings_service.get_bool('security/restrict_restaurant_split_bill_to_admin', False):
            allowed, reason = False, 'restrict_restaurant_split_bill_to_admin'
        elif action == self.ACTION_RESTAURANT_WAITER_WORKFLOW and settings_service.get_bool('security/restrict_restaurant_waiter_workflow_to_admin', False):
            allowed, reason = False, 'restrict_restaurant_waiter_workflow_to_admin'
        elif action == self.ACTION_RESTAURANT_KITCHEN_STATION_MANAGE and settings_service.get_bool('security/restrict_restaurant_kitchen_station_manage_to_admin', False):
            allowed, reason = False, 'restrict_restaurant_kitchen_station_manage_to_admin'
        elif action == self.ACTION_RESTAURANT_MODIFIER_MANAGE and settings_service.get_bool('security/restrict_restaurant_modifier_manage_to_admin', False):
            allowed, reason = False, 'restrict_restaurant_modifier_manage_to_admin'
        elif action == self.ACTION_RESTAURANT_RECIPE_MANAGE and settings_service.get_bool('security/restrict_restaurant_recipe_manage_to_admin', False):
            allowed, reason = False, 'restrict_restaurant_recipe_manage_to_admin'
        elif action == self.ACTION_RESTAURANT_DELIVERY_TAKEAWAY and settings_service.get_bool('security/restrict_restaurant_delivery_takeaway_to_admin', False):
            allowed, reason = False, 'restrict_restaurant_delivery_takeaway_to_admin'
        elif action == self.ACTION_RESTAURANT_PRINTER_MANAGE and settings_service.get_bool('security/restrict_restaurant_printer_manage_to_admin', False):
            allowed, reason = False, 'restrict_restaurant_printer_manage_to_admin'
        elif action == self.ACTION_RESTAURANT_PRINT_QUEUE and settings_service.get_bool('security/restrict_restaurant_print_queue_to_admin', False):
            allowed, reason = False, 'restrict_restaurant_print_queue_to_admin'
        elif action == self.ACTION_RESTAURANT_VIEW_ANALYTICS and settings_service.get_bool('security/restrict_restaurant_analytics_to_admin', False):
            allowed, reason = False, 'restrict_restaurant_analytics_to_admin'
        elif action == self.ACTION_USE_MANUFACTURING and settings_service.get_bool('security/restrict_manufacturing_to_authorized_users', False):
            allowed, reason = False, 'restrict_manufacturing_to_authorized_users'
        elif action == self.ACTION_MANUFACTURING_BOM_CREATE and settings_service.get_bool('security/restrict_manufacturing_bom_create_to_admin', False):
            allowed, reason = False, 'restrict_manufacturing_bom_create_to_admin'
        elif action == self.ACTION_MANUFACTURING_BOM_EDIT and settings_service.get_bool('security/restrict_manufacturing_bom_edit_to_admin', False):
            allowed, reason = False, 'restrict_manufacturing_bom_edit_to_admin'
        elif action == self.ACTION_MANUFACTURING_BOM_DELETE and settings_service.get_bool('security/restrict_manufacturing_bom_delete_to_admin', False):
            allowed, reason = False, 'restrict_manufacturing_bom_delete_to_admin'
        elif action == self.ACTION_MANUFACTURING_ORDER_CREATE and settings_service.get_bool('security/restrict_manufacturing_order_create_to_admin', False):
            allowed, reason = False, 'restrict_manufacturing_order_create_to_admin'
        elif action == self.ACTION_MANUFACTURING_ORDER_START and settings_service.get_bool('security/restrict_manufacturing_order_start_to_admin', False):
            allowed, reason = False, 'restrict_manufacturing_order_start_to_admin'
        elif action == self.ACTION_MANUFACTURING_MATERIAL_CONSUME and settings_service.get_bool('security/restrict_manufacturing_material_consume_to_admin', False):
            allowed, reason = False, 'restrict_manufacturing_material_consume_to_admin'
        elif action == self.ACTION_MANUFACTURING_OUTPUT_COMPLETE and settings_service.get_bool('security/restrict_manufacturing_output_complete_to_admin', False):
            allowed, reason = False, 'restrict_manufacturing_output_complete_to_admin'
        elif action == self.ACTION_MANUFACTURING_ORDER_REVERSE and settings_service.get_bool('security/restrict_manufacturing_reverse_to_admin', False):
            allowed, reason = False, 'restrict_manufacturing_reverse_to_admin'
        elif action == self.ACTION_MANUFACTURING_COST_VIEW and settings_service.get_bool('security/hide_manufacturing_cost_for_non_admin', settings_service.get_bool('security/hide_item_cost_for_non_admin', False)):
            allowed, reason = False, 'hide_manufacturing_cost_for_non_admin'
        elif action == self.ACTION_MANUFACTURING_PRINT and settings_service.get_bool('security/restrict_manufacturing_print_to_admin', False):
            allowed, reason = False, 'restrict_manufacturing_print_to_admin'
        elif action == self.ACTION_USE_INVENTORY and settings_service.get_bool('security/restrict_inventory_to_authorized_users', False):
            allowed, reason = False, 'restrict_inventory_to_authorized_users'
        elif action == self.ACTION_INVENTORY_WAREHOUSE_CREATE and settings_service.get_bool('security/restrict_warehouse_create_to_admin', False):
            allowed, reason = False, 'restrict_warehouse_create_to_admin'
        elif action == self.ACTION_INVENTORY_WAREHOUSE_EDIT and settings_service.get_bool('security/restrict_warehouse_edit_to_admin', False):
            allowed, reason = False, 'restrict_warehouse_edit_to_admin'
        elif action == self.ACTION_INVENTORY_WAREHOUSE_ARCHIVE and settings_service.get_bool('security/restrict_warehouse_archive_to_admin', False):
            allowed, reason = False, 'restrict_warehouse_archive_to_admin'
        elif action == self.ACTION_INVENTORY_DIRECT_MOVEMENT and settings_service.get_bool('security/restrict_direct_inventory_movement_to_admin', False):
            allowed, reason = False, 'restrict_direct_inventory_movement_to_admin'
        elif action == self.ACTION_INVENTORY_TRANSFER_CREATE and settings_service.get_bool('security/restrict_warehouse_transfer_to_admin', False):
            allowed, reason = False, 'restrict_warehouse_transfer_to_admin'
        elif action == self.ACTION_INVENTORY_TRANSFER_CANCEL and settings_service.get_bool('security/restrict_warehouse_transfer_cancel_to_admin', False):
            allowed, reason = False, 'restrict_warehouse_transfer_cancel_to_admin'
        elif action == self.ACTION_INVENTORY_LEDGER_BACKFILL and settings_service.get_bool('security/restrict_inventory_ledger_backfill_to_admin', True):
            allowed, reason = False, 'restrict_inventory_ledger_backfill_to_admin'
        elif action == self.ACTION_INVENTORY_PRINT and settings_service.get_bool('security/restrict_inventory_print_to_admin', False):
            allowed, reason = False, 'restrict_inventory_print_to_admin'
        elif action == self.ACTION_VIEW_REPORTS:
            if settings_service.get_bool('security/restrict_reports_to_admin', False):
                allowed, reason = False, 'restrict_reports_to_admin'
            elif role in self._blocked_roles('security/blocked_report_roles'):
                allowed, reason = False, 'blocked_report_roles'
        elif action == self.ACTION_EXPORT_REPORTS and settings_service.get_bool('security/restrict_report_export_to_admin', False):
            allowed, reason = False, 'restrict_report_export_to_admin'
        elif action == self.ACTION_VIEW_ALL_BRANCHES:
            if settings_service.get_bool('security/restrict_branch_scope_for_non_admin', True) and not settings_service.get_bool('security/allow_non_admin_view_all_branches', False):
                allowed, reason = False, 'restrict_branch_scope_for_non_admin'
        elif action == self.ACTION_MANAGE_ALL_BRANCHES:
            if not settings_service.get_bool('security/allow_non_admin_manage_all_branches', False):
                allowed, reason = False, 'manage_all_branches_restricted'
        else:
            allowed = self.DEFAULTS.get(action, True)
        if not allowed:
            self.log_event('PERMISSION_DENIED', action=action, allowed=False, reason=reason, role=role)
        return allowed

    def can_view_all_branches(self, role: str | None = None) -> bool:
        role = (role or self.current_role()).strip().lower()
        if self.is_admin(role):
            return True
        try:
            if rbac_service.list_roles():
                return rbac_service.has_permission('branches.view_all')
        except Exception:
            pass
        if not settings_service.get_bool('security/restrict_branch_scope_for_non_admin', True):
            return True
        return settings_service.get_bool('security/allow_non_admin_view_all_branches', False)

    def branch_scope(self) -> dict:
        """Return the effective branch scope for the current user.

        Admins, or users allowed by policy, may see all branches. Other users
        are restricted to their session branch, falling back to the configured
        default branch. This is read-only and safe for reports.
        """
        if self.can_view_all_branches():
            return {'mode': 'all', 'branch_id': None}
        try:
            from core.services.branch_service import branch_service
            return {'mode': 'current', 'branch_id': branch_service.current_branch_id()}
        except Exception:
            return {'mode': 'current', 'branch_id': None}

    def effective_branch_id(self, requested_branch_id=None):
        if requested_branch_id not in (None, '', 0, '0') and self.can_view_all_branches():
            try:
                return int(requested_branch_id)
            except Exception:
                return None
        scope = self.branch_scope()
        return scope.get('branch_id') if scope.get('mode') != 'all' else None

    def should_hide_profit(self, role: str | None = None) -> bool:
        role = (role or self.current_role()).strip().lower()
        return (not self.is_admin(role)) and settings_service.get_bool('security/hide_profit_for_non_admin', False)

    # ========== Security event log (Phase 147) ==========
    def log_event(self, event_type: str, action: str = '', allowed: bool = False,
                  reason: str = '', context: str = '', role: str | None = None) -> None:
        try:
            username = ''
            try:
                username = UserSession.get_current_username() or ''
            except Exception:
                username = ''
            self.system_gateway.log_security_event(
                event_type=event_type, action=action, allowed=allowed,
                reason=reason, context=context, role=role or self.current_role(),
                username=username,
            )
        except Exception:
            pass

    def security_events(self, limit: int = 200):
        return self.system_gateway.security_events(limit)

    def denied_events_count(self) -> int:
        return self.system_gateway.denied_security_events_count()

    def denied_message(self, action: str) -> str:
        labels = {
            self.ACTION_DELETE: 'الحذف غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_EDIT_INVOICES: 'تعديل الفواتير غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_EDIT_RETURNS: 'تعديل المرتجعات غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_EDIT_ITEMS: 'تعديل المواد غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_PRINT_BARCODES: 'طباعة الباركود غير مسموحة لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_VIEW_ITEM_COSTS: 'عرض تكلفة المواد غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_EDIT_OPENING_STOCK: 'تعديل الكمية الافتتاحية غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_USE_POS: 'استخدام نقطة البيع غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_POS_SUSPEND: 'تعليق بيع POS غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_POS_RESUME: 'استرجاع بيع POS معلق غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_POS_REMOVE_LINE: 'حذف سطر من POS غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_POS_CLEAR_CART: 'تفريغ سلة POS غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_POS_OPEN_SHIFT: 'فتح وردية POS غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_POS_CLOSE_SHIFT: 'إغلاق وردية POS غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_POS_PRINT_RECEIPT: 'طباعة إيصال POS غير مسموحة لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_USE_RESTAURANT: 'استخدام المطعم غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_RESTAURANT_OPEN_SESSION: 'فتح جلسة مطعم غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_RESTAURANT_ADD_LINE: 'إضافة سطر طلب مطعم غير مسموحة لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_RESTAURANT_SEND_KITCHEN: 'إرسال الطلب للمطبخ غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_RESTAURANT_ADJUST_BILL: 'تعديل فاتورة المطعم غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_RESTAURANT_RECORD_PAYMENT: 'تسجيل دفعة مطعم غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_RESTAURANT_CHECKOUT: 'إغلاق طاولة المطعم غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_RESTAURANT_UPDATE_KITCHEN_STATUS: 'تحديث حالة المطبخ غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_RESTAURANT_PRINT_RECEIPT: 'طباعة إيصال المطعم غير مسموحة لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_RESTAURANT_PRINT_KITCHEN_TICKET: 'طباعة تذكرة المطبخ غير مسموحة لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_RESTAURANT_RESERVE_TABLE: 'حجز طاولة مطعم غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_RESTAURANT_CANCEL_RESERVATION: 'إلغاء حجز مطعم غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_RESTAURANT_TRANSFER_TABLE: 'نقل طاولة مطعم غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_RESTAURANT_MERGE_TABLES: 'دمج طاولات المطعم غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_RESTAURANT_MOVE_ORDER_LINE: 'نقل سطر طلب مطعم غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_RESTAURANT_SPLIT_BILL: 'تقسيم فاتورة المطعم غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_RESTAURANT_WAITER_WORKFLOW: 'تشغيل سير عمل النادل غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_RESTAURANT_KITCHEN_STATION_MANAGE: 'إدارة محطات المطبخ غير مسموحة لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_RESTAURANT_MODIFIER_MANAGE: 'إدارة إضافات المطعم غير مسموحة لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_RESTAURANT_RECIPE_MANAGE: 'إدارة وصفات المطعم غير مسموحة لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_RESTAURANT_DELIVERY_TAKEAWAY: 'تشغيل طلبات السفري/التوصيل غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_RESTAURANT_PRINTER_MANAGE: 'إدارة طابعات المطعم غير مسموحة لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_RESTAURANT_PRINT_QUEUE: 'إدارة طابور طباعة المطعم غير مسموحة لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_RESTAURANT_VIEW_ANALYTICS: 'عرض تحليلات المطعم غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_USE_MANUFACTURING: 'استخدام التصنيع غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_MANUFACTURING_BOM_CREATE: 'إنشاء تركيبة تصنيع غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_MANUFACTURING_BOM_EDIT: 'تعديل تركيبة التصنيع غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_MANUFACTURING_BOM_DELETE: 'حذف تركيبة التصنيع غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_MANUFACTURING_ORDER_CREATE: 'إنشاء أمر إنتاج غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_MANUFACTURING_ORDER_START: 'بدء أمر الإنتاج غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_MANUFACTURING_MATERIAL_CONSUME: 'استهلاك مواد الإنتاج غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_MANUFACTURING_OUTPUT_COMPLETE: 'إتمام إنتاج المخرجات غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_MANUFACTURING_ORDER_REVERSE: 'عكس أمر الإنتاج غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_MANUFACTURING_COST_VIEW: 'عرض تكلفة التصنيع غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_MANUFACTURING_PRINT: 'طباعة مستندات التصنيع غير مسموحة لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_INVENTORY_PRINT: 'طباعة مستندات المخزون والمستودعات غير مسموحة لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_VIEW_REPORTS: 'عرض التقارير غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_EXPORT_REPORTS: 'تصدير التقارير غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_VIEW_ALL_BRANCHES: 'عرض كل الفروع غير مسموح لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_MANAGE_ALL_BRANCHES: 'إدارة كل الفروع غير مسموحة لهذا المستخدم حسب إعدادات الصلاحيات.',
            self.ACTION_USERS_MANAGE: 'إدارة المستخدمين غير مسموحة لهذا المستخدم حسب إعدادات الصلاحيات.',
        }
        return labels.get(action, 'لا تملك صلاحية تنفيذ هذه العملية.')


permission_service = PermissionService()
