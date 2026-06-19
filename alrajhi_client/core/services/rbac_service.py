# -*- coding: utf-8 -*-
"""Enterprise RBAC service (Phase 157).

Provides a database-backed roles/permissions layer while preserving the legacy
`users.role` field as a compatibility fallback.  All methods are defensive so
permission checks never crash the UI if a migration is still pending.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Dict, Optional

from auth.session import UserSession


DEFAULT_ROLE_PERMISSIONS = {
    'admin': None,  # all permissions
    'manager': {
        'reports.view', 'reports.export', 'invoices.edit', 'returns.edit',
        'parties.view', 'customers.view', 'customers.create', 'customers.edit', 'customers.delete', 'suppliers.view', 'suppliers.create', 'suppliers.edit', 'suppliers.delete', 'branches.view_all', 'approval.submit', 'items.edit', 'items.barcodes.print', 'categories.view', 'categories.create', 'categories.edit', 'categories.archive', 'categories.restore', 'approval.approve', 'approval.reject', 'restaurant.use', 'restaurant.session.open', 'restaurant.line.add', 'restaurant.kitchen.send', 'restaurant.bill.adjust', 'restaurant.payment.record', 'restaurant.checkout', 'restaurant.kitchen.status.update', 'restaurant.receipt.print', 'restaurant.kitchen_ticket.print', 'manufacturing.use', 'manufacturing.bom.create', 'manufacturing.bom.edit', 'manufacturing.bom.delete', 'manufacturing.order.create', 'manufacturing.order.start', 'manufacturing.material.consume', 'manufacturing.output.complete', 'manufacturing.order.cancel', 'manufacturing.order.delete', 'manufacturing.order.reverse', 'manufacturing.consumption.delete', 'manufacturing.output.delete', 'manufacturing.cost.view', 'manufacturing.print', 'inventory.use', 'inventory.warehouse.create', 'inventory.warehouse.edit', 'inventory.warehouse.archive', 'inventory.balance.view', 'inventory.movement.view', 'inventory.movement.direct', 'inventory.transfer.create', 'inventory.transfer.cancel', 'inventory.ledger.view', 'inventory.reconcile', 'inventory.print', 'finance.use', 'finance.cashbox.create', 'finance.cashbox.edit', 'finance.cashbox.archive', 'finance.bank.create', 'finance.bank.edit', 'finance.bank.archive', 'finance.movements.view', 'finance.shifts.view', 'finance.voucher.view', 'finance.voucher.create', 'finance.voucher.edit', 'finance.voucher.delete', 'finance.voucher.print', 'finance.expense.view', 'finance.expense.create', 'finance.expense.edit', 'finance.expense.delete', 'finance.expense.print'
    },
    'accountant': {
        'reports.view', 'reports.export', 'accounting.view', 'accounting.post',
        'parties.view', 'customers.view', 'customers.create', 'customers.edit', 'customers.delete', 'suppliers.view', 'suppliers.create', 'suppliers.edit', 'suppliers.delete', 'accounting.close_period', 'approval.submit', 'finance.use', 'finance.voucher.view', 'finance.voucher.create', 'finance.voucher.edit', 'finance.voucher.print', 'finance.expense.view', 'finance.expense.create', 'finance.expense.edit', 'finance.expense.print', 'manufacturing.use', 'manufacturing.cost.view', 'manufacturing.print', 'inventory.use', 'inventory.warehouse.create', 'inventory.warehouse.edit', 'inventory.warehouse.archive', 'inventory.balance.view', 'inventory.movement.view', 'inventory.movement.direct', 'inventory.transfer.create', 'inventory.transfer.cancel', 'inventory.ledger.view', 'inventory.reconcile', 'inventory.print'
    },
    'cashier': {'approval.submit', 'parties.view', 'customers.view', 'customers.create', 'customers.edit', 'finance.use', 'finance.voucher.view', 'finance.voucher.create', 'finance.voucher.print', 'finance.expense.view', 'finance.expense.create', 'finance.expense.print', 'items.barcodes.print', 'inventory.use', 'inventory.balance.view', 'inventory.transfer.create', 'pos.use', 'pos.suspend', 'pos.resume', 'pos.line.remove', 'pos.cart.clear', 'pos.shift.open', 'pos.shift.close', 'pos.receipt.print', 'restaurant.use', 'restaurant.session.open', 'restaurant.line.add', 'restaurant.kitchen.send', 'restaurant.payment.record', 'restaurant.checkout', 'restaurant.receipt.print', 'restaurant.kitchen_ticket.print'},
    'viewer': {'reports.view'},
}

ACTION_PERMISSION_MAP = {
    'hide_profit': 'reports.view',
    'delete_records': 'invoices.delete',
    'edit_invoices': 'invoices.edit',
    'edit_returns': 'returns.edit',
    'edit_items': 'items.edit',
    'print_barcodes': 'items.barcodes.print',
    'view_item_costs': 'items.cost.view',
    'edit_opening_stock': 'items.opening_stock.edit',
    'category_view': 'categories.view',
    'category_create': 'categories.create',
    'category_edit': 'categories.edit',
    'category_archive': 'categories.archive',
    'category_restore': 'categories.restore',
    'use_pos': 'pos.use',
    'pos_suspend': 'pos.suspend',
    'pos_resume': 'pos.resume',
    'pos_remove_line': 'pos.line.remove',
    'pos_clear_cart': 'pos.cart.clear',
    'pos_open_shift': 'pos.shift.open',
    'pos_close_shift': 'pos.shift.close',
    'pos_print_receipt': 'pos.receipt.print',
    'restaurant_use': 'restaurant.use',
    'restaurant_open_session': 'restaurant.session.open',
    'restaurant_add_line': 'restaurant.line.add',
    'restaurant_send_kitchen': 'restaurant.kitchen.send',
    'restaurant_adjust_bill': 'restaurant.bill.adjust',
    'restaurant_record_payment': 'restaurant.payment.record',
    'restaurant_checkout': 'restaurant.checkout',
    'restaurant_update_kitchen_status': 'restaurant.kitchen.status.update',
    'restaurant_print_receipt': 'restaurant.receipt.print',
    'restaurant_print_kitchen_ticket': 'restaurant.kitchen_ticket.print',
    'manufacturing_use': 'manufacturing.use',
    'manufacturing_bom_create': 'manufacturing.bom.create',
    'manufacturing_bom_edit': 'manufacturing.bom.edit',
    'manufacturing_bom_delete': 'manufacturing.bom.delete',
    'manufacturing_order_create': 'manufacturing.order.create',
    'manufacturing_order_start': 'manufacturing.order.start',
    'manufacturing_material_consume': 'manufacturing.material.consume',
    'manufacturing_output_complete': 'manufacturing.output.complete',
    'manufacturing_order_cancel': 'manufacturing.order.cancel',
    'manufacturing_order_delete': 'manufacturing.order.delete',
    'manufacturing_order_reverse': 'manufacturing.order.reverse',
    'manufacturing_consumption_delete': 'manufacturing.consumption.delete',
    'manufacturing_output_delete': 'manufacturing.output.delete',
    'manufacturing_cost_view': 'manufacturing.cost.view',
    'manufacturing_print': 'manufacturing.print',
    'inventory_use': 'inventory.use',
    'inventory_warehouse_create': 'inventory.warehouse.create',
    'inventory_warehouse_edit': 'inventory.warehouse.edit',
    'inventory_warehouse_archive': 'inventory.warehouse.archive',
    'inventory_balance_view': 'inventory.balance.view',
    'inventory_movement_view': 'inventory.movement.view',
    'inventory_direct_movement': 'inventory.movement.direct',
    'inventory_transfer_create': 'inventory.transfer.create',
    'inventory_transfer_cancel': 'inventory.transfer.cancel',
    'inventory_ledger_view': 'inventory.ledger.view',
    'inventory_ledger_backfill': 'inventory.ledger.backfill',
    'inventory_reconcile': 'inventory.reconcile',
    'inventory_print': 'inventory.print',
    'finance_use': 'finance.use',
    'finance_cashbox_create': 'finance.cashbox.create',
    'finance_cashbox_edit': 'finance.cashbox.edit',
    'finance_cashbox_archive': 'finance.cashbox.archive',
    'finance_bank_create': 'finance.bank.create',
    'finance_bank_edit': 'finance.bank.edit',
    'finance_bank_archive': 'finance.bank.archive',
    'finance_movements_view': 'finance.movements.view',
    'finance_shifts_view': 'finance.shifts.view',
    'finance_voucher_create': 'finance.voucher.create',
    'finance_voucher_edit': 'finance.voucher.edit',
    'finance_voucher_delete': 'finance.voucher.delete',
    'finance_voucher_print': 'finance.voucher.print',
    'finance_voucher_view': 'finance.voucher.view',
    'finance_expense_create': 'finance.expense.create',
    'finance_expense_edit': 'finance.expense.edit',
    'finance_expense_delete': 'finance.expense.delete',
    'finance_expense_print': 'finance.expense.print',
    'finance_expense_view': 'finance.expense.view',
    'view_reports': 'reports.view',
    'export_reports': 'reports.export',
    'view_all_branches': 'branches.view_all',
    'manage_all_branches': 'branches.manage_all',
    'approval.submit': 'approval.submit',
    'approval.approve': 'approval.approve',
    'approval.reject': 'approval.reject',
    'accounting.view': 'accounting.view',
    'accounting.post': 'accounting.post',
    'accounting.close_period': 'accounting.close_period',
    'settings.manage': 'settings.manage',
    'users.manage': 'users.manage',
    'users_manage': 'users.manage',
    'party_view': 'parties.view',
    'customer_view': 'customers.view',
    'customer_create': 'customers.create',
    'customer_edit': 'customers.edit',
    'customer_delete': 'customers.delete',
    'supplier_view': 'suppliers.view',
    'supplier_create': 'suppliers.create',
    'supplier_edit': 'suppliers.edit',
    'supplier_delete': 'suppliers.delete',
    'system.health.view': 'system.health.view',
    'system.validation.run': 'system.validation.run',
    'approval.matrix.manage': 'approval.matrix.manage',
    'approval.level1': 'approval.level1',
    'approval.level2': 'approval.level2',
    'approval.level3': 'approval.level3',
}


class RBACService:
    def __init__(self, gateway=None):
        self.gateway = gateway or self._create_gateway()

    def _create_gateway(self):
        from gateways.rbac_gateway import create_rbac_gateway
        return create_rbac_gateway()

    def _user_id(self, user_id: str | None = None) -> str | None:
        return str(user_id or UserSession.get_current_user_id() or '') or None

    def _legacy_role(self, user_id: str | None = None) -> str:
        current = UserSession.get_current() or {}
        if user_id is None and current.get('role'):
            return str(current.get('role')).lower()
        try:
            return self.gateway.legacy_role(user_id)
        except Exception:
            return 'admin'

    def list_roles(self) -> List[Dict]:
        try:
            return self.gateway.list_roles()
        except Exception:
            return []

    def list_permissions(self) -> List[Dict]:
        try:
            return self.gateway.list_permissions()
        except Exception:
            return []

    def user_roles(self, user_id: str | None = None) -> List[str]:
        uid = self._user_id(user_id)
        try:
            roles = self.gateway.user_roles(uid)
            if roles:
                return roles
        except Exception:
            pass
        return [self._legacy_role(user_id)]

    def role_parent_map(self) -> dict[str, str]:
        try:
            return self.gateway.role_parent_map()
        except Exception:
            return {}

    def effective_user_roles(self, user_id: str | None = None) -> List[str]:
        roles = [str(r).lower() for r in self.user_roles(user_id)]
        parent_map = self.role_parent_map()
        seen = set(roles)
        stack = list(roles)
        while stack:
            role = stack.pop()
            parent = parent_map.get(role)
            if parent and parent not in seen:
                seen.add(parent)
                stack.append(parent)
        return sorted(seen)

    def role_permissions(self, role_name: str) -> set[str]:
        try:
            perms = self.gateway.role_permissions(role_name)
            if perms:
                return perms
        except Exception:
            pass
        defaults = DEFAULT_ROLE_PERMISSIONS.get(str(role_name).lower(), set())
        return {'*'} if defaults is None else set(defaults)

    def can_access_branch(self, branch_id: int | None, user_id: str | None = None) -> bool:
        if branch_id in (None, '', 0):
            return True
        if self.has_permission('branches.view_all', user_id):
            return True
        allowed = self.allowed_branch_ids(user_id)
        try:
            return int(branch_id) in allowed
        except Exception:
            return False

    def user_permissions(self, user_id: str | None = None) -> set[str]:
        roles = self.effective_user_roles(user_id)
        if 'admin' in roles:
            return {p['key'] for p in self.list_permissions()} or {'*'}
        perms: set[str] = set()
        try:
            uid = self._user_id(user_id)
            perms.update(self.gateway.user_direct_permissions(uid))
        except Exception:
            pass
        if not perms:
            for role in roles:
                defaults = DEFAULT_ROLE_PERMISSIONS.get(role, set())
                if defaults is None:
                    return {'*'}
                perms.update(defaults)
        return perms

    def has_permission(self, permission_key: str, user_id: str | None = None) -> bool:
        key = ACTION_PERMISSION_MAP.get(permission_key, permission_key)
        perms = self.user_permissions(user_id)
        return '*' in perms or key in perms

    def can_action(self, action: str, user_id: str | None = None) -> bool:
        return self.has_permission(ACTION_PERMISSION_MAP.get(action, action), user_id)

    def assign_roles(self, user_id: str, role_names: Iterable[str]) -> bool:
        try:
            return self.gateway.assign_roles(user_id, role_names)
        except Exception:
            return False

    def set_role_permissions(self, role_name: str, permission_keys: Iterable[str]) -> bool:
        try:
            return self.gateway.set_role_permissions(role_name, permission_keys)
        except Exception:
            return False

    def set_user_branches(self, user_id: str, branch_ids: Iterable[int]) -> bool:
        try:
            return self.gateway.set_user_branches(user_id, branch_ids)
        except Exception:
            return False

    def allowed_branch_ids(self, user_id: str | None = None) -> List[int]:
        uid = self._user_id(user_id)
        try:
            return self.gateway.allowed_branch_ids(uid)
        except Exception:
            return []


rbac_service = RBACService()
