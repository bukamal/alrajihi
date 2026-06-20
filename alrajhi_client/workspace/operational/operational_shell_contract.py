# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from workspace.documents.document_contract import (
    BRANCH_REQUIRED,
    CURRENCY_DISPLAY,
    NETWORK_REMOTE_AVAILABLE,
    SHELL_OPERATIONAL,
    descriptor_for,
)

OP_CATEGORY_SALE = "sale"
OP_CATEGORY_SHIFT = "shift"
OP_CATEGORY_PRINT = "print"
OP_CATEGORY_ORDER = "order"
OP_CATEGORY_KITCHEN = "kitchen"
OP_CATEGORY_PAYMENT = "payment"
OP_CATEGORY_SESSION = "session"

POLICY_POS = "pos_operation_policy"
POLICY_RESTAURANT = "restaurant_operation_policy"

SHIFT_DISABLED = "disabled"
SHIFT_OPTIONAL = "optional"
SHIFT_REQUIRED_FOR_CHECKOUT = "required_for_checkout"

CASHBOX_REQUIRED = "required"
WAREHOUSE_REQUIRED = "required"

PRINT_PROFILE_THERMAL80 = "thermal80"
PRINT_PROFILE_RESTAURANT_RECEIPT = "restaurant_receipt"
PRINT_PROFILE_KITCHEN_TICKET = "kitchen_ticket"


@dataclass(frozen=True)
class OperationalOperationDescriptor:
    """Single operation exposed by a POS/restaurant operational shell.

    Operational screens are not edit documents.  Their security surface is a set
    of guarded actions: checkout, suspend, open shift, send kitchen ticket,
    record payment, print receipt, etc.  Each operation must declare its
    settings flag, RBAC action, and audit/category semantics so UI buttons,
    shortcuts, and service calls can stay aligned.
    """

    key: str
    policy_key: str
    permission_action: str
    enabled_setting: str
    label_key: str
    category: str
    requires_session: bool = False
    requires_shift: bool = False
    requires_cashbox: bool = False
    requires_warehouse: bool = False
    print_profile: str = ""


@dataclass(frozen=True)
class OperationalShellDescriptor:
    shell_key: str
    document_type: str
    title_key: str
    widget_class: str
    dashboard_class: str
    document_descriptor_type: str
    api_resource: str
    network_mode: str
    i18n_scope: str
    settings_scope: str
    operation_policy: str
    operations: tuple[OperationalOperationDescriptor, ...]
    currency_policy: str = CURRENCY_DISPLAY
    branch_policy: str = BRANCH_REQUIRED
    warehouse_policy: str = WAREHOUSE_REQUIRED
    cashbox_policy: str = CASHBOX_REQUIRED
    shift_policy: str = SHIFT_OPTIONAL
    default_print_profile: str = ""
    audit_scope: str = ""
    offline_queue: bool = True
    barcode_enabled: bool = True
    local_gateway: str = ""
    remote_gateway: str = ""
    server_blueprint: str = ""
    notes: str = ""

    @property
    def document_descriptor(self):
        return descriptor_for(self.document_descriptor_type or self.document_type)

    @property
    def permissions(self):
        descriptor = self.document_descriptor
        return descriptor.permissions if descriptor else None

    def operation_for(self, key: str, default: OperationalOperationDescriptor | None = None) -> OperationalOperationDescriptor | None:
        key = str(key or "")
        for op in self.operations:
            if op.key == key or op.policy_key == key:
                return op
        return default

    def operation_map(self) -> Mapping[str, OperationalOperationDescriptor]:
        return {op.key: op for op in self.operations}

    @property
    def is_network_ready(self) -> bool:
        return self.network_mode == NETWORK_REMOTE_AVAILABLE


def _op(
    key: str,
    *,
    policy_key: str | None = None,
    permission_action: str,
    enabled_setting: str,
    label_key: str,
    category: str,
    requires_session: bool = False,
    requires_shift: bool = False,
    requires_cashbox: bool = False,
    requires_warehouse: bool = False,
    print_profile: str = "",
) -> OperationalOperationDescriptor:
    return OperationalOperationDescriptor(
        key=key,
        policy_key=policy_key or key,
        permission_action=permission_action,
        enabled_setting=enabled_setting,
        label_key=label_key,
        category=category,
        requires_session=requires_session,
        requires_shift=requires_shift,
        requires_cashbox=requires_cashbox,
        requires_warehouse=requires_warehouse,
        print_profile=print_profile,
    )


POS_OPERATIONAL_SHELL = OperationalShellDescriptor(
    shell_key="pos",
    document_type="pos",
    title_key="pos",
    widget_class="views.widgets.pos_widget.POSWidget",
    dashboard_class="views.widgets.pos_widget.POSWidget",
    document_descriptor_type="pos",
    api_resource="/api/invoices",
    network_mode=NETWORK_REMOTE_AVAILABLE,
    i18n_scope="pos.shell",
    settings_scope="pos",
    operation_policy=POLICY_POS,
    default_print_profile=PRINT_PROFILE_THERMAL80,
    audit_scope="pos",
    local_gateway="gateways.local.invoice_gateway.LocalInvoiceGateway",
    remote_gateway="gateways.remote.invoice_gateway.RemoteInvoiceGateway",
    server_blueprint="invoices",
    shift_policy=SHIFT_REQUIRED_FOR_CHECKOUT,
    operations=(
        _op("checkout", permission_action="use_pos", enabled_setting="pos/operations/allow_checkout", label_key="pos_operation_checkout", category=OP_CATEGORY_SALE, requires_shift=True, requires_cashbox=True, requires_warehouse=True),
        _op("suspend", permission_action="pos_suspend", enabled_setting="pos/operations/allow_suspend", label_key="pos_operation_suspend", category=OP_CATEGORY_SALE),
        _op("resume", permission_action="pos_resume", enabled_setting="pos/operations/allow_resume", label_key="pos_operation_resume", category=OP_CATEGORY_SALE),
        _op("remove_line", permission_action="pos_remove_line", enabled_setting="pos/operations/allow_remove_line", label_key="pos_operation_remove_line", category=OP_CATEGORY_SALE),
        _op("clear_cart", permission_action="pos_clear_cart", enabled_setting="pos/operations/allow_clear_cart", label_key="pos_operation_clear_cart", category=OP_CATEGORY_SALE),
        _op("open_shift", permission_action="pos_open_shift", enabled_setting="pos/operations/allow_open_shift", label_key="pos_operation_open_shift", category=OP_CATEGORY_SHIFT, requires_cashbox=True),
        _op("close_shift", permission_action="pos_close_shift", enabled_setting="pos/operations/allow_close_shift", label_key="pos_operation_close_shift", category=OP_CATEGORY_SHIFT, requires_cashbox=True),
        _op("print_receipt", permission_action="pos_print_receipt", enabled_setting="pos/operations/allow_print_receipt", label_key="pos_operation_print_receipt", category=OP_CATEGORY_PRINT, print_profile=PRINT_PROFILE_THERMAL80),
    ),
    notes="Fast sale operational shell; checkout creates a sales invoice but the UI is governed by POS operations, not document editing actions.",
)


RESTAURANT_OPERATIONAL_SHELL = OperationalShellDescriptor(
    shell_key="restaurant",
    document_type="restaurant",
    title_key="restaurant",
    widget_class="views.restaurant.restaurant_pos_widget.RestaurantPOSWidget",
    dashboard_class="views.restaurant.restaurant_dashboard.RestaurantDashboard",
    document_descriptor_type="restaurant",
    api_resource="/api/restaurant",
    network_mode=NETWORK_REMOTE_AVAILABLE,
    i18n_scope="restaurant.shell",
    settings_scope="restaurant",
    operation_policy=POLICY_RESTAURANT,
    default_print_profile=PRINT_PROFILE_RESTAURANT_RECEIPT,
    audit_scope="restaurant",
    local_gateway="gateways.local.restaurant_gateway.LocalRestaurantGateway",
    remote_gateway="gateways.remote.restaurant_gateway.RemoteRestaurantGateway",
    server_blueprint="restaurant",
    shift_policy=SHIFT_OPTIONAL,
    operations=(
        _op("use", permission_action="restaurant_use", enabled_setting="restaurant/operations/allow_use", label_key="restaurant_operation_use", category=OP_CATEGORY_SESSION),
        _op("open_session", permission_action="restaurant_open_session", enabled_setting="restaurant/operations/allow_open_session", label_key="restaurant_operation_open_session", category=OP_CATEGORY_SESSION),
        _op("add_line", permission_action="restaurant_add_line", enabled_setting="restaurant/operations/allow_add_line", label_key="restaurant_operation_add_line", category=OP_CATEGORY_ORDER, requires_session=True),
        _op("send_kitchen", permission_action="restaurant_send_kitchen", enabled_setting="restaurant/operations/allow_send_kitchen", label_key="restaurant_operation_send_kitchen", category=OP_CATEGORY_KITCHEN, requires_session=True),
        _op("adjust_bill", permission_action="restaurant_adjust_bill", enabled_setting="restaurant/operations/allow_adjust_bill", label_key="restaurant_operation_adjust_bill", category=OP_CATEGORY_ORDER, requires_session=True),
        _op("record_payment", permission_action="restaurant_record_payment", enabled_setting="restaurant/operations/allow_record_payment", label_key="restaurant_operation_record_payment", category=OP_CATEGORY_PAYMENT, requires_session=True),
        _op("checkout", permission_action="restaurant_checkout", enabled_setting="restaurant/operations/allow_checkout", label_key="restaurant_operation_checkout", category=OP_CATEGORY_PAYMENT, requires_session=True),
        _op("update_kitchen_status", permission_action="restaurant_update_kitchen_status", enabled_setting="restaurant/operations/allow_update_kitchen_status", label_key="restaurant_operation_update_kitchen_status", category=OP_CATEGORY_KITCHEN),
        _op("print_receipt", permission_action="restaurant_print_receipt", enabled_setting="restaurant/operations/allow_print_receipt", label_key="restaurant_operation_print_receipt", category=OP_CATEGORY_PRINT, requires_session=True, print_profile=PRINT_PROFILE_RESTAURANT_RECEIPT),
        _op("print_kitchen_ticket", permission_action="restaurant_print_kitchen_ticket", enabled_setting="restaurant/operations/allow_print_kitchen_ticket", label_key="restaurant_operation_print_kitchen_ticket", category=OP_CATEGORY_PRINT, requires_session=True, print_profile=PRINT_PROFILE_KITCHEN_TICKET),
    ),
    notes="Restaurant operational shell; table sessions, kitchen tickets and split payments are operation-driven and use restaurant API routes.",
)


OPERATIONAL_SHELL_DESCRIPTORS: tuple[OperationalShellDescriptor, ...] = (
    POS_OPERATIONAL_SHELL,
    RESTAURANT_OPERATIONAL_SHELL,
)

_DESCRIPTOR_BY_KEY = {d.shell_key: d for d in OPERATIONAL_SHELL_DESCRIPTORS}
_DESCRIPTOR_BY_DOCUMENT = {d.document_type: d for d in OPERATIONAL_SHELL_DESCRIPTORS}


def operational_descriptor_for(shell_key: str, default: OperationalShellDescriptor | None = None) -> OperationalShellDescriptor | None:
    return _DESCRIPTOR_BY_KEY.get(str(shell_key or ""), default)


def operational_descriptor_for_document(document_type: str, default: OperationalShellDescriptor | None = None) -> OperationalShellDescriptor | None:
    return _DESCRIPTOR_BY_DOCUMENT.get(str(document_type or ""), default)


def operational_descriptors() -> tuple[OperationalShellDescriptor, ...]:
    return OPERATIONAL_SHELL_DESCRIPTORS


def validate_operational_descriptor(descriptor: OperationalShellDescriptor) -> list[str]:
    warnings: list[str] = []
    required = (
        "shell_key",
        "document_type",
        "title_key",
        "widget_class",
        "dashboard_class",
        "api_resource",
        "network_mode",
        "i18n_scope",
        "settings_scope",
        "operation_policy",
        "audit_scope",
    )
    for field_name in required:
        if not str(getattr(descriptor, field_name, "") or "").strip():
            warnings.append(f"{descriptor.shell_key}: missing {field_name}")
    backing = descriptor.document_descriptor
    if backing is None:
        warnings.append(f"{descriptor.shell_key}: missing backing DocumentDescriptor {descriptor.document_descriptor_type}")
    elif backing.shell_family != SHELL_OPERATIONAL:
        warnings.append(f"{descriptor.shell_key}: backing descriptor is not operational shell")
    if descriptor.network_mode == NETWORK_REMOTE_AVAILABLE and not descriptor.remote_gateway:
        warnings.append(f"{descriptor.shell_key}: remote_available without remote_gateway")
    if not descriptor.operations:
        warnings.append(f"{descriptor.shell_key}: no operations declared")
    seen: set[str] = set()
    for operation in descriptor.operations:
        if operation.key in seen:
            warnings.append(f"{descriptor.shell_key}: duplicate operation {operation.key}")
        seen.add(operation.key)
        if not operation.permission_action:
            warnings.append(f"{descriptor.shell_key}.{operation.key}: missing permission_action")
        if not operation.enabled_setting:
            warnings.append(f"{descriptor.shell_key}.{operation.key}: missing enabled_setting")
        if not operation.label_key:
            warnings.append(f"{descriptor.shell_key}.{operation.key}: missing label_key")
        if operation.category == OP_CATEGORY_PRINT and not operation.print_profile:
            warnings.append(f"{descriptor.shell_key}.{operation.key}: print operation without print_profile")
    if descriptor.currency_policy != CURRENCY_DISPLAY:
        warnings.append(f"{descriptor.shell_key}: operational shells must use display currency policy")
    if descriptor.branch_policy != BRANCH_REQUIRED:
        warnings.append(f"{descriptor.shell_key}: operational shells must declare branch required policy")
    return warnings


def validate_operational_descriptors(descriptors: tuple[OperationalShellDescriptor, ...] | None = None) -> list[str]:
    warnings: list[str] = []
    seen: set[str] = set()
    for descriptor in descriptors or OPERATIONAL_SHELL_DESCRIPTORS:
        if descriptor.shell_key in seen:
            warnings.append(f"duplicate operational shell_key {descriptor.shell_key}")
        seen.add(descriptor.shell_key)
        warnings.extend(validate_operational_descriptor(descriptor))
    return warnings


def operational_shell_matrix(descriptors: tuple[OperationalShellDescriptor, ...] | None = None) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for descriptor in descriptors or OPERATIONAL_SHELL_DESCRIPTORS:
        rows.append({
            "shell_key": descriptor.shell_key,
            "document_type": descriptor.document_type,
            "widget_class": descriptor.widget_class,
            "dashboard_class": descriptor.dashboard_class,
            "api_resource": descriptor.api_resource,
            "network_mode": descriptor.network_mode,
            "settings_scope": descriptor.settings_scope,
            "i18n_scope": descriptor.i18n_scope,
            "operation_policy": descriptor.operation_policy,
            "operations": ",".join(op.key for op in descriptor.operations),
            "currency_policy": descriptor.currency_policy,
            "branch_policy": descriptor.branch_policy,
            "warehouse_policy": descriptor.warehouse_policy,
            "cashbox_policy": descriptor.cashbox_policy,
            "shift_policy": descriptor.shift_policy,
            "default_print_profile": descriptor.default_print_profile,
            "offline_queue": descriptor.offline_queue,
            "barcode_enabled": descriptor.barcode_enabled,
            "audit_scope": descriptor.audit_scope,
        })
    return rows


class OperationalShellPermissionBinder:
    """Runtime adapter for operation policies.

    The contract is data-only.  This binder bridges it to the existing POS and
    restaurant operation policies when a real PyQt widget is instantiated.
    """

    def __init__(self, descriptor: OperationalShellDescriptor):
        self.descriptor = descriptor

    def _policy(self):
        if self.descriptor.operation_policy == POLICY_POS:
            from core.services.pos_operation_policy import pos_operation_policy
            return pos_operation_policy
        if self.descriptor.operation_policy == POLICY_RESTAURANT:
            from core.services.restaurant_operation_policy import restaurant_operation_policy
            return restaurant_operation_policy
        return None

    def can(self, operation_key: str) -> bool:
        operation = self.descriptor.operation_for(operation_key)
        policy = self._policy()
        if operation is None or policy is None:
            return True
        try:
            return bool(policy.can(operation.policy_key))
        except Exception:
            return True

    def denial_message(self, operation_key: str) -> str:
        operation = self.descriptor.operation_for(operation_key)
        policy = self._policy()
        if operation is None or policy is None:
            return ""
        try:
            return str(policy.denial_message(operation.policy_key))
        except Exception:
            return ""

    def require(self, operation_key: str) -> bool:
        operation = self.descriptor.operation_for(operation_key)
        policy = self._policy()
        if operation is None or policy is None:
            return True
        try:
            policy.require(operation.policy_key)
            return True
        except Exception:
            return False

    def operation_states(self) -> Mapping[str, bool]:
        return {operation.key: self.can(operation.key) for operation in self.descriptor.operations}

    def apply_to_widget(self, widget, button_map: Mapping[str, tuple[str, ...]] | None = None) -> Mapping[str, bool]:
        states = self.operation_states()
        button_map = button_map or {}
        for operation_key, names in button_map.items():
            enabled = bool(states.get(operation_key, True))
            for name in names:
                btn = getattr(widget, name, None)
                if btn is not None and hasattr(btn, "setEnabled"):
                    try:
                        btn.setEnabled(enabled)
                    except Exception:
                        pass
        return states


def bind_operational_shell(widget, shell_key: str) -> OperationalShellDescriptor | None:
    descriptor = operational_descriptor_for(shell_key)
    if descriptor is None:
        return None
    widget.operational_shell_descriptor = descriptor
    widget.document_descriptor = descriptor.document_descriptor
    widget.operational_permission_binder = OperationalShellPermissionBinder(descriptor)
    return descriptor
