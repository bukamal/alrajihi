# -*- coding: utf-8 -*-
from __future__ import annotations

"""Central restaurant operation policy and audit helper (Phase 182).

Restaurant POS is a payment/kitchen workflow, not a loose set of buttons.
UI actions and service calls must use the same settings, RBAC permissions, and
audit trail so table checkout, kitchen send, payments, and manual lines cannot
be bypassed by calling the service directly.
"""

from dataclasses import dataclass
from typing import Dict

from core.services.audit_service import audit_service
from core.services.permission_service import permission_service
from core.services.settings_service import settings_service
from i18n import translate


@dataclass(frozen=True)
class RestaurantOperation:
    key: str
    permission_action: str
    enabled_setting: str = ""
    enabled_default: bool = True
    label_key: str = ""


class RestaurantOperationPolicy:
    OP_USE = "use"
    OP_OPEN_SESSION = "open_session"
    OP_ADD_LINE = "add_line"
    OP_SEND_KITCHEN = "send_kitchen"
    OP_ADJUST_BILL = "adjust_bill"
    OP_RECORD_PAYMENT = "record_payment"
    OP_CHECKOUT = "checkout"
    OP_UPDATE_KITCHEN_STATUS = "update_kitchen_status"
    OP_PRINT_RECEIPT = "print_receipt"
    OP_PRINT_KITCHEN_TICKET = "print_kitchen_ticket"
    OP_RESERVE_TABLE = "reserve_table"
    OP_CANCEL_RESERVATION = "cancel_reservation"
    OP_TRANSFER_TABLE = "transfer_table"
    OP_MERGE_TABLES = "merge_tables"
    OP_MOVE_ORDER_LINE = "move_order_line"
    OP_SPLIT_BILL = "split_bill"
    OP_WAITER_WORKFLOW = "waiter_workflow"
    OP_KITCHEN_STATION_MANAGE = "kitchen_station_manage"
    OP_MODIFIER_MANAGE = "modifier_manage"
    OP_RECIPE_MANAGE = "recipe_manage"
    OP_DELIVERY_TAKEAWAY = "delivery_takeaway"
    OP_PRINTER_MANAGE = "printer_manage"
    OP_PRINT_QUEUE = "print_queue"
    OP_VIEW_ANALYTICS = "view_analytics"

    OPERATIONS: Dict[str, RestaurantOperation] = {
        OP_USE: RestaurantOperation(OP_USE, "restaurant_use", "restaurant/operations/allow_use", True, "restaurant_operation_use"),
        OP_OPEN_SESSION: RestaurantOperation(OP_OPEN_SESSION, "restaurant_open_session", "restaurant/operations/allow_open_session", True, "restaurant_operation_open_session"),
        OP_ADD_LINE: RestaurantOperation(OP_ADD_LINE, "restaurant_add_line", "restaurant/operations/allow_add_line", True, "restaurant_operation_add_line"),
        OP_SEND_KITCHEN: RestaurantOperation(OP_SEND_KITCHEN, "restaurant_send_kitchen", "restaurant/operations/allow_send_kitchen", True, "restaurant_operation_send_kitchen"),
        OP_ADJUST_BILL: RestaurantOperation(OP_ADJUST_BILL, "restaurant_adjust_bill", "restaurant/operations/allow_adjust_bill", True, "restaurant_operation_adjust_bill"),
        OP_RECORD_PAYMENT: RestaurantOperation(OP_RECORD_PAYMENT, "restaurant_record_payment", "restaurant/operations/allow_record_payment", True, "restaurant_operation_record_payment"),
        OP_CHECKOUT: RestaurantOperation(OP_CHECKOUT, "restaurant_checkout", "restaurant/operations/allow_checkout", True, "restaurant_operation_checkout"),
        OP_UPDATE_KITCHEN_STATUS: RestaurantOperation(OP_UPDATE_KITCHEN_STATUS, "restaurant_update_kitchen_status", "restaurant/operations/allow_update_kitchen_status", True, "restaurant_operation_update_kitchen_status"),
        OP_PRINT_RECEIPT: RestaurantOperation(OP_PRINT_RECEIPT, "restaurant_print_receipt", "restaurant/operations/allow_print_receipt", True, "restaurant_operation_print_receipt"),
        OP_PRINT_KITCHEN_TICKET: RestaurantOperation(OP_PRINT_KITCHEN_TICKET, "restaurant_print_kitchen_ticket", "restaurant/operations/allow_print_kitchen_ticket", True, "restaurant_operation_print_kitchen_ticket"),
        OP_RESERVE_TABLE: RestaurantOperation(OP_RESERVE_TABLE, "restaurant_reserve_table", "restaurant/operations/allow_reserve_table", True, "restaurant_operation_reserve_table"),
        OP_CANCEL_RESERVATION: RestaurantOperation(OP_CANCEL_RESERVATION, "restaurant_cancel_reservation", "restaurant/operations/allow_cancel_reservation", True, "restaurant_operation_cancel_reservation"),
        OP_TRANSFER_TABLE: RestaurantOperation(OP_TRANSFER_TABLE, "restaurant_transfer_table", "restaurant/operations/allow_transfer_table", True, "restaurant_operation_transfer_table"),
        OP_MERGE_TABLES: RestaurantOperation(OP_MERGE_TABLES, "restaurant_merge_tables", "restaurant/operations/allow_merge_tables", True, "restaurant_operation_merge_tables"),
        OP_MOVE_ORDER_LINE: RestaurantOperation(OP_MOVE_ORDER_LINE, "restaurant_move_order_line", "restaurant/operations/allow_move_order_line", True, "restaurant_operation_move_order_line"),
        OP_SPLIT_BILL: RestaurantOperation(OP_SPLIT_BILL, "restaurant_split_bill", "restaurant/operations/allow_split_bill", True, "restaurant_operation_split_bill"),
        OP_WAITER_WORKFLOW: RestaurantOperation(OP_WAITER_WORKFLOW, "restaurant_waiter_workflow", "restaurant/operations/allow_waiter_workflow", True, "restaurant_operation_waiter_workflow"),
        OP_KITCHEN_STATION_MANAGE: RestaurantOperation(OP_KITCHEN_STATION_MANAGE, "restaurant_kitchen_station_manage", "restaurant/operations/allow_kitchen_station_manage", True, "restaurant_operation_kitchen_station_manage"),
        OP_MODIFIER_MANAGE: RestaurantOperation(OP_MODIFIER_MANAGE, "restaurant_modifier_manage", "restaurant/operations/allow_modifier_manage", True, "restaurant_operation_modifier_manage"),
        OP_RECIPE_MANAGE: RestaurantOperation(OP_RECIPE_MANAGE, "restaurant_recipe_manage", "restaurant/operations/allow_recipe_manage", True, "restaurant_operation_recipe_manage"),
        OP_DELIVERY_TAKEAWAY: RestaurantOperation(OP_DELIVERY_TAKEAWAY, "restaurant_delivery_takeaway", "restaurant/operations/allow_delivery_takeaway", True, "restaurant_operation_delivery_takeaway"),
        OP_PRINTER_MANAGE: RestaurantOperation(OP_PRINTER_MANAGE, "restaurant_printer_manage", "restaurant/operations/allow_printer_manage", True, "restaurant_operation_printer_manage"),
        OP_PRINT_QUEUE: RestaurantOperation(OP_PRINT_QUEUE, "restaurant_print_queue", "restaurant/operations/allow_print_queue", True, "restaurant_operation_print_queue"),
        OP_VIEW_ANALYTICS: RestaurantOperation(OP_VIEW_ANALYTICS, "restaurant_view_analytics", "restaurant/operations/allow_view_analytics", True, "restaurant_operation_view_analytics"),
    }

    def operation(self, key: str) -> RestaurantOperation:
        return self.OPERATIONS.get(str(key or ""), self.OPERATIONS[self.OP_USE])

    def label(self, key: str) -> str:
        op = self.operation(key)
        return translate(op.label_key or "restaurant_operation_unknown")

    def restaurant_enabled(self) -> bool:
        try:
            return bool(settings_service.get_restaurant_settings().get("enabled", True))
        except Exception:
            return True

    def is_enabled_by_settings(self, key: str) -> bool:
        if not self.restaurant_enabled():
            return False
        op = self.operation(key)
        if not op.enabled_setting:
            return True
        return settings_service.get_bool(op.enabled_setting, op.enabled_default)

    def can(self, key: str) -> bool:
        op = self.operation(key)
        if not self.is_enabled_by_settings(key):
            return False
        try:
            return bool(permission_service.can(op.permission_action))
        except Exception:
            return True

    def denial_message(self, key: str) -> str:
        op = self.operation(key)
        if not self.restaurant_enabled():
            return translate("restaurant_operation_disabled")
        if not self.is_enabled_by_settings(key):
            return translate("restaurant_operation_disabled_by_settings", operation=self.label(key))
        try:
            message = permission_service.denied_message(op.permission_action)
            if message:
                return message
        except Exception:
            pass
        return translate("restaurant_operation_denied", operation=self.label(key))

    def require(self, key: str) -> None:
        if not self.can(key):
            raise PermissionError(self.denial_message(key))

    def log(self, key: str, *, allowed: bool, context: str = "", values=None) -> None:
        try:
            audit_service.log(
                "RESTAURANT_OPERATION_ALLOWED" if allowed else "RESTAURANT_OPERATION_DENIED",
                "RESTAURANT_OPERATION",
                None,
                new_values={"operation": key, "context": context, "values": values or {}},
                details=self.label(key),
            )
        except Exception:
            pass


restaurant_operation_policy = RestaurantOperationPolicy()
