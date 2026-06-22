# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Optional

from .document_contract import DocumentDescriptor, descriptor_for


DOCUMENT_ACTIONS = ("view", "create", "update", "save", "delete", "print", "export", "approve", "cancel")


@dataclass(frozen=True)
class DocumentPermissionDecision:
    action: str
    permission_key: str
    allowed: bool
    reason: str = ""


# Bridge canonical DocumentDescriptor permission keys to the project's older
# settings-driven permission actions. Exact RBAC keys are always tried first.
_LEGACY_ACTION_ALIASES: Mapping[str, str] = {
    # Transactions
    "sales_invoices.create": "edit_invoices",
    "sales_invoices.update": "edit_invoices",
    "sales_invoices.delete": "delete_records",
    "purchase_invoices.create": "edit_invoices",
    "purchase_invoices.update": "edit_invoices",
    "purchase_invoices.delete": "delete_records",
    "sales_returns.create": "edit_returns",
    "sales_returns.update": "edit_returns",
    "sales_returns.delete": "delete_records",
    "purchase_returns.create": "edit_returns",
    "purchase_returns.update": "edit_returns",
    "purchase_returns.delete": "delete_records",
    # Materials and parties
    "items.create": "edit_items",
    "items.update": "edit_items",
    "items.delete": "delete_records",
    "items.print": "print_barcodes",
    "categories.view": "category_view",
    "categories.create": "category_create",
    "categories.update": "category_edit",
    "categories.delete": "category_archive",
    "customers.view": "customer_view",
    "customers.create": "customer_create",
    "customers.update": "customer_edit",
    "customers.delete": "customer_delete",
    "suppliers.view": "supplier_view",
    "suppliers.create": "supplier_create",
    "suppliers.update": "supplier_edit",
    "suppliers.delete": "supplier_delete",
    # Finance
    "vouchers.view": "finance_voucher_view",
    "vouchers.create": "finance_voucher_create",
    "vouchers.update": "finance_voucher_edit",
    "vouchers.delete": "finance_voucher_delete",
    "vouchers.print": "finance_voucher_print",
    "expenses.view": "finance_expense_view",
    "expenses.create": "finance_expense_create",
    "expenses.update": "finance_expense_edit",
    "expenses.delete": "finance_expense_delete",
    "expenses.print": "finance_expense_print",
    "cashboxes.create": "finance_cashbox_create",
    "cashboxes.update": "finance_cashbox_edit",
    "cashboxes.delete": "finance_cashbox_archive",
    "bank_accounts.create": "finance_bank_create",
    "bank_accounts.update": "finance_bank_edit",
    "bank_accounts.delete": "finance_bank_archive",
    # Inventory
    "warehouses.create": "inventory_warehouse_create",
    "warehouses.update": "inventory_warehouse_edit",
    "warehouses.delete": "inventory_warehouse_archive",
    "warehouses.print": "inventory_print",
    "warehouse_transfers.create": "inventory_transfer_create",
    "warehouse_transfers.update": "inventory_transfer_create",
    "warehouse_transfers.cancel": "inventory_transfer_cancel",
    "warehouse_transfers.print": "inventory_print",
    # Manufacturing
    "manufacturing.bom.create": "manufacturing_bom_create",
    "manufacturing.bom.update": "manufacturing_bom_edit",
    "manufacturing.bom.delete": "manufacturing_bom_delete",
    "manufacturing.bom.print": "manufacturing_print",
    "manufacturing.bom.approve": "manufacturing_bom_edit",
    "manufacturing.bom.cancel": "manufacturing_bom_edit",
    "manufacturing.production_orders.create": "manufacturing_order_create",
    "manufacturing.production_orders.update": "manufacturing_order_start",
    "manufacturing.production_orders.print": "manufacturing_print",
    "manufacturing.production_orders.approve": "manufacturing_order_start",
    "manufacturing.production_orders.cancel": "manufacturing_order_cancel",
    # Users, settings, reports, operational shells
    "users.view": "users_manage",
    "users.create": "users_manage",
    "users.update": "users_manage",
    "users.delete": "users_manage",
    "settings.update": "users_manage",
    "settings.export": "users_manage",
    "reports.view": "view_reports",
    "reports.print": "view_reports",
    "reports.export": "export_reports",
    "pos.view": "use_pos",
    "pos.checkout": "use_pos",
    "pos.print": "pos_print_receipt",
    "pos.void": "pos_clear_cart",
    "restaurant.view": "restaurant_use",
    "restaurant.order": "restaurant_add_line",
    "restaurant.order.update": "restaurant_adjust_bill",
    "restaurant.print": "restaurant_print_receipt",
    "restaurant.cancel": "restaurant_adjust_bill",
    "cafe.view": "restaurant_use",
    "cafe.order": "restaurant_add_line",
    "cafe.payment": "restaurant_record_payment",
    "cafe.print": "restaurant_print_receipt",
    "cafe.report": "restaurant_view_analytics",
}


def document_permission_allowed(permission_key: str, *, checker: Optional[Callable[[str], bool]] = None) -> bool:
    """Return whether the current user may use a canonical document permission.

    Resolution order:
      1. Empty permission keys are allowed because the action may be unsupported.
      2. An injected checker, used by tests and future remote policy providers.
      3. Exact RBAC permission key, when database-backed roles exist.
      4. Legacy settings-driven PermissionService action alias.
      5. Backward-compatible allow for unknown keys while contract coverage matures.
    """
    key = str(permission_key or "").strip()
    if not key:
        return True
    if checker is not None:
        return bool(checker(key))
    try:
        from core.services.permission_service import permission_service
        if permission_service.is_admin():
            return True
    except Exception:
        permission_service = None  # type: ignore[assignment]
    try:
        from core.services.rbac_service import rbac_service
        if rbac_service.list_roles():
            return bool(rbac_service.has_permission(key))
    except Exception:
        pass
    alias = _LEGACY_ACTION_ALIASES.get(key)
    if alias:
        try:
            from core.services.permission_service import permission_service
            return bool(permission_service.can(alias))
        except Exception:
            return True
    return True


class DocumentPermissionBinder:
    """Bind a DocumentDescriptor permission surface to UI commands/buttons.

    The binder is intentionally small and non-invasive. It can be used by
    MainWindow, BaseDocumentTab, feature-specific tabs, or tests without forcing
    a specific visual layout. The action contract is canonical; widgets remain
    free to render their own buttons.
    """

    def __init__(self, descriptor_or_document_type: DocumentDescriptor | str | None, *, checker: Optional[Callable[[str], bool]] = None) -> None:
        if isinstance(descriptor_or_document_type, DocumentDescriptor):
            descriptor = descriptor_or_document_type
        else:
            descriptor = descriptor_for(str(descriptor_or_document_type or ""))
        self.descriptor = descriptor
        self.checker = checker

    def permission_key_for(self, action: str, *, document_id: object | None = None) -> str:
        if self.descriptor is None:
            return ""
        action = str(action or "").strip().lower()
        if action == "save":
            # New documents need create; existing documents need update. If a
            # descriptor only declares one of both, keep backward compatibility.
            if document_id in (None, "", 0, "0"):
                return self.descriptor.permissions.create or self.descriptor.permissions.update
            return self.descriptor.permissions.update or self.descriptor.permissions.create
        return self.descriptor.permission_for(action)

    def can(self, action: str, *, document_id: object | None = None) -> bool:
        key = self.permission_key_for(action, document_id=document_id)
        return document_permission_allowed(key, checker=self.checker)

    def decision(self, action: str, *, document_id: object | None = None) -> DocumentPermissionDecision:
        key = self.permission_key_for(action, document_id=document_id)
        allowed = document_permission_allowed(key, checker=self.checker)
        reason = "" if allowed else "permission_denied"
        return DocumentPermissionDecision(action=str(action), permission_key=key, allowed=allowed, reason=reason)

    def matrix(self, *, document_id: object | None = None) -> dict[str, DocumentPermissionDecision]:
        return {action: self.decision(action, document_id=document_id) for action in DOCUMENT_ACTIONS}

    def apply_to_action_bar(self, action_bar, *, document_id: object | None = None) -> None:
        """Apply save/print/export enablement to UnifiedActionBar-like objects."""
        if action_bar is None or self.descriptor is None:
            return
        for action in ("save", "print", "export"):
            if not hasattr(action_bar, "set_action_enabled"):
                continue
            capability = getattr(self.descriptor.capabilities, action if action != "save" else "save", True)
            enabled = bool(capability) and self.can(action, document_id=document_id)
            try:
                action_bar.set_action_enabled(action, enabled)
            except Exception:
                pass

    def apply_to_widget_buttons(self, widget, *, document_id: object | None = None) -> dict[str, bool]:
        """Best-effort button binding for existing document tabs.

        This intentionally supports the current heterogeneous UI while the
        project migrates toward one shell. Feature-specific code can still apply
        richer policies, but these common attributes get protected uniformly.
        """
        states: dict[str, bool] = {}
        if widget is None or self.descriptor is None:
            return states
        candidates = {
            "save": ("save_btn", "bottom_save_btn", "header_save_btn"),
            "print": ("print_btn", "bottom_print_btn", "print_label_btn", "header_print_btn"),
            "export": ("export_btn", "bottom_export_btn", "header_export_btn"),
            "delete": ("delete_btn", "bottom_delete_btn", "remove_btn", "archive_btn"),
            "approve": ("approve_btn", "bottom_approve_btn"),
            "cancel": ("cancel_btn", "bottom_cancel_btn", "void_btn"),
        }
        for action, names in candidates.items():
            if action == "save":
                capability = self.descriptor.capabilities.save
            else:
                capability = bool(getattr(self.descriptor.capabilities, action, False))
            enabled = bool(capability) and self.can(action, document_id=document_id)
            states[action] = enabled
            for name in names:
                button = getattr(widget, name, None)
                if button is not None and hasattr(button, "setEnabled"):
                    try:
                        button.setEnabled(enabled)
                        permission_key = self.permission_key_for(action, document_id=document_id)
                        if not enabled and hasattr(button, "setToolTip"):
                            button.setToolTip(permission_key or "permission_denied")
                    except Exception:
                        pass
        # TransactionBottomActions added in this phase exposes set_action_enabled.
        bottom_actions = getattr(widget, "bottom_actions", None)
        if bottom_actions is not None and hasattr(bottom_actions, "set_action_enabled"):
            for action, enabled in states.items():
                try:
                    bottom_actions.set_action_enabled(action, enabled)
                except Exception:
                    pass
        return states


__all__ = [
    "DOCUMENT_ACTIONS",
    "DocumentPermissionBinder",
    "DocumentPermissionDecision",
    "document_permission_allowed",
]
