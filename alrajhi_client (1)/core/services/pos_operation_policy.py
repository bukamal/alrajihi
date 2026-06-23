# -*- coding: utf-8 -*-
from __future__ import annotations

"""Central POS operation policy and audit helper (Phase 178).

POS is a high-risk touch workflow.  UI buttons, shortcuts, and service calls
must not make independent authorization decisions.  This helper keeps operation
names stable and routes checks through the project's permission/settings/audit
layers.
"""

from dataclasses import dataclass
from typing import Dict

from core.services.audit_service import audit_service
from core.services.permission_service import permission_service
from core.services.settings_service import settings_service
from i18n import translate


@dataclass(frozen=True)
class POSOperation:
    key: str
    permission_action: str
    enabled_setting: str = ""
    enabled_default: bool = True
    label_key: str = ""


class POSOperationPolicy:
    OP_CHECKOUT = "checkout"
    OP_SUSPEND = "suspend"
    OP_RESUME = "resume"
    OP_REMOVE_LINE = "remove_line"
    OP_CLEAR_CART = "clear_cart"
    OP_OPEN_SHIFT = "open_shift"
    OP_CLOSE_SHIFT = "close_shift"
    OP_PRINT_RECEIPT = "print_receipt"

    OPERATIONS: Dict[str, POSOperation] = {
        OP_CHECKOUT: POSOperation(OP_CHECKOUT, "use_pos", "pos/operations/allow_checkout", True, "pos_operation_checkout"),
        OP_SUSPEND: POSOperation(OP_SUSPEND, "pos_suspend", "pos/operations/allow_suspend", True, "pos_operation_suspend"),
        OP_RESUME: POSOperation(OP_RESUME, "pos_resume", "pos/operations/allow_resume", True, "pos_operation_resume"),
        OP_REMOVE_LINE: POSOperation(OP_REMOVE_LINE, "pos_remove_line", "pos/operations/allow_remove_line", True, "pos_operation_remove_line"),
        OP_CLEAR_CART: POSOperation(OP_CLEAR_CART, "pos_clear_cart", "pos/operations/allow_clear_cart", True, "pos_operation_clear_cart"),
        OP_OPEN_SHIFT: POSOperation(OP_OPEN_SHIFT, "pos_open_shift", "pos/operations/allow_open_shift", True, "pos_operation_open_shift"),
        OP_CLOSE_SHIFT: POSOperation(OP_CLOSE_SHIFT, "pos_close_shift", "pos/operations/allow_close_shift", True, "pos_operation_close_shift"),
        OP_PRINT_RECEIPT: POSOperation(OP_PRINT_RECEIPT, "pos_print_receipt", "pos/operations/allow_print_receipt", True, "pos_operation_print_receipt"),
    }

    def operation(self, key: str) -> POSOperation:
        return self.OPERATIONS.get(str(key or ""), self.OPERATIONS[self.OP_CHECKOUT])

    def is_shift_operation(self, key: str) -> bool:
        return str(key or "") in (self.OP_OPEN_SHIFT, self.OP_CLOSE_SHIFT)

    def shifts_enabled(self) -> bool:
        try:
            return bool(settings_service.pos_shifts_enabled())
        except Exception:
            return False

    def label(self, key: str) -> str:
        op = self.operation(key)
        return translate(op.label_key or "pos_operation_unknown")

    def is_enabled_by_settings(self, key: str) -> bool:
        if self.is_shift_operation(key) and not self.shifts_enabled():
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
        if self.is_shift_operation(key) and not self.shifts_enabled():
            return translate("shifts_disabled_direct_cashbox")
        if not self.is_enabled_by_settings(key):
            return translate("pos_operation_disabled_by_settings", operation=self.label(key))
        try:
            message = permission_service.denied_message(op.permission_action)
            if message:
                return message
        except Exception:
            pass
        return translate("pos_operation_denied", operation=self.label(key))

    def require(self, key: str) -> None:
        if not self.can(key):
            raise PermissionError(self.denial_message(key))

    def log(self, key: str, *, allowed: bool, context: str = "", values=None) -> None:
        try:
            audit_service.log(
                "POS_OPERATION_ALLOWED" if allowed else "POS_OPERATION_DENIED",
                "POS_OPERATION",
                None,
                new_values={"operation": key, "context": context, "values": values or {}},
                details=self.label(key),
            )
        except Exception:
            pass


pos_operation_policy = POSOperationPolicy()
