# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from workspace.documents.document_contract import all_descriptors, BRANCH_REQUIRED, BRANCH_USER_ACCESS
from workspace.lists.list_workspace_contract import list_descriptors
from workspace.operational.operational_shell_contract import operational_descriptors
from features.reports.report_shell_contract import all_report_descriptors

RBAC_API_RESOURCE = "/api/rbac"
NETWORK_REMOTE_AVAILABLE = "remote_available"

# Keep this map PyQt-free.  It mirrors core.services.rbac_service.ACTION_PERMISSION_MAP
# for operational shell actions that are still expressed as legacy action names.
OPERATION_ACTION_PERMISSION_MAP: Mapping[str, str] = {
    "use_pos": "pos.use",
    "pos_suspend": "pos.suspend",
    "pos_resume": "pos.resume",
    "pos_remove_line": "pos.line.remove",
    "pos_clear_cart": "pos.cart.clear",
    "pos_open_shift": "pos.shift.open",
    "pos_close_shift": "pos.shift.close",
    "pos_print_receipt": "pos.receipt.print",
    "restaurant_use": "restaurant.use",
    "restaurant_open_session": "restaurant.session.open",
    "restaurant_add_line": "restaurant.line.add",
    "restaurant_send_kitchen": "restaurant.kitchen.send",
    "restaurant_adjust_bill": "restaurant.bill.adjust",
    "restaurant_record_payment": "restaurant.payment.record",
    "restaurant_checkout": "restaurant.checkout",
    "restaurant_update_kitchen_status": "restaurant.kitchen.status.update",
    "restaurant_print_receipt": "restaurant.receipt.print",
    "restaurant_print_kitchen_ticket": "restaurant.kitchen_ticket.print",
}


@dataclass(frozen=True)
class RBACPermissionDescriptor:
    key: str
    module: str
    action: str
    description: str
    source: str
    shell_family: str = ""
    api_resource: str = RBAC_API_RESOURCE
    network_mode: str = NETWORK_REMOTE_AVAILABLE
    branch_scoped: bool = False
    legacy_alias: str = ""


@dataclass(frozen=True)
class RBACRoleSeed:
    role_name: str
    permission_keys: tuple[str, ...]
    mode: str = "merge"  # migration should merge; never replace admin customizations.


def _split_permission_key(key: str) -> tuple[str, str]:
    parts = str(key or "").split(".")
    if not parts:
        return "system", "use"
    module = parts[0] or "system"
    action = "_".join(parts[1:]) if len(parts) > 1 else "use"
    return module, action


def _description_for(key: str, source: str) -> str:
    module, action = _split_permission_key(key)
    return f"{source}: {module} {action.replace('_', ' ')}"


def _add(result: dict[str, RBACPermissionDescriptor], key: str, *, source: str, shell_family: str = "", branch_scoped: bool = False, legacy_alias: str = "") -> None:
    key = str(key or "").strip()
    if not key:
        return
    module, action = _split_permission_key(key)
    existing = result.get(key)
    if existing is not None:
        # Preserve the first declaration, but upgrade branch scope and alias data if later sources know more.
        if branch_scoped and not existing.branch_scoped:
            result[key] = RBACPermissionDescriptor(
                key=existing.key,
                module=existing.module,
                action=existing.action,
                description=existing.description,
                source=existing.source,
                shell_family=existing.shell_family,
                api_resource=existing.api_resource,
                network_mode=existing.network_mode,
                branch_scoped=True,
                legacy_alias=existing.legacy_alias or legacy_alias,
            )
        return
    result[key] = RBACPermissionDescriptor(
        key=key,
        module=module,
        action=action,
        description=_description_for(key, source),
        source=source,
        shell_family=shell_family,
        branch_scoped=bool(branch_scoped),
        legacy_alias=legacy_alias,
    )


def _descriptor_branch_scoped(descriptor) -> bool:
    return getattr(descriptor, "branch_policy", "") in {BRANCH_REQUIRED, BRANCH_USER_ACCESS}


def required_permission_descriptors() -> tuple[RBACPermissionDescriptor, ...]:
    """Permissions required by Document/List/Report/Operational shell contracts.

    This function intentionally imports only contract modules; it is safe in CI,
    PyInstaller analysis, and environments without PyQt5.
    """
    result: dict[str, RBACPermissionDescriptor] = {}

    for descriptor in all_descriptors():
        for action, key in descriptor.permissions.action_map().items():
            _add(
                result,
                key,
                source=f"document:{descriptor.document_type}:{action}",
                shell_family=descriptor.shell_family,
                branch_scoped=_descriptor_branch_scoped(descriptor),
            )

    for descriptor in list_descriptors():
        for action in ("view", "create", "update", "delete", "print", "export"):
            _add(
                result,
                descriptor.permission_for(action),
                source=f"list:{descriptor.list_key}:{action}",
                shell_family="list_workspace",
                branch_scoped=_descriptor_branch_scoped(descriptor),
            )

    for descriptor in all_report_descriptors():
        _add(result, descriptor.permission_view, source=f"report:{descriptor.report_key}:view", shell_family="report_shell", branch_scoped=_descriptor_branch_scoped(descriptor))
        _add(result, descriptor.permission_print, source=f"report:{descriptor.report_key}:print", shell_family="report_shell", branch_scoped=_descriptor_branch_scoped(descriptor))
        _add(result, descriptor.permission_export, source=f"report:{descriptor.report_key}:export", shell_family="report_shell", branch_scoped=_descriptor_branch_scoped(descriptor))

    for descriptor in operational_descriptors():
        backing = descriptor.document_descriptor
        if backing is not None:
            for action, key in backing.permissions.action_map().items():
                _add(result, key, source=f"operational:{descriptor.shell_key}:backing:{action}", shell_family="operational_shell", branch_scoped=_descriptor_branch_scoped(descriptor))
        for op in descriptor.operations:
            canonical = OPERATION_ACTION_PERMISSION_MAP.get(op.permission_action, op.permission_action)
            _add(
                result,
                canonical,
                source=f"operational:{descriptor.shell_key}:{op.key}",
                shell_family="operational_shell",
                branch_scoped=_descriptor_branch_scoped(descriptor),
                legacy_alias=op.permission_action,
            )

    # Cross-cutting branch administration keys used by RBACService.branch checks.
    _add(result, "branches.view_all", source="rbac:branch_scope:view_all", shell_family="security")
    _add(result, "branches.manage_all", source="rbac:branch_scope:manage_all", shell_family="security")

    return tuple(result[k] for k in sorted(result))


def required_permission_keys() -> tuple[str, ...]:
    return tuple(d.key for d in required_permission_descriptors())


def permission_descriptor_map() -> Mapping[str, RBACPermissionDescriptor]:
    return {d.key: d for d in required_permission_descriptors()}


def role_seed_descriptors() -> tuple[RBACRoleSeed, ...]:
    keys = set(required_permission_keys())
    view_keys = {k for k in keys if k.endswith(".view") or k in {"reports.view"}}
    print_export_keys = {k for k in keys if k.endswith(".print") or k.endswith(".export")}
    sales_keys = {k for k in keys if k.startswith("sales_") or k.startswith("pos.") or k.startswith("restaurant.")}
    party_basic = {k for k in keys if k.startswith("customers.") or k.startswith("suppliers.") or k == "items.view"}
    finance_keys = {k for k in keys if k.startswith("vouchers.") or k.startswith("expenses.") or k.startswith("cashboxes.") or k.startswith("bank_accounts.") or k.startswith("reports.")}
    inventory_read = {k for k in keys if k in {"warehouses.view", "warehouse_transfers.view", "items.view", "items.print"}}
    accountant_keys = {
        k for k in keys
        if k.startswith("purchase_")
        or k.startswith("vouchers.")
        or k.startswith("expenses.")
        or k.startswith("reports.")
        or k.startswith("customers.")
        or k.startswith("suppliers.")
        or k in {"items.view", "items.print", "warehouses.view", "warehouse_transfers.view"}
    }
    cashier_keys = {
        k for k in keys
        if k.startswith("pos.")
        or k.startswith("restaurant.")
        or k.startswith("sales_invoices.")
        or k.startswith("sales_returns.")
        or k in party_basic
        or k in inventory_read
    }
    manager_keys = set(keys) - {"settings.update", "settings.export", "users.create", "users.update", "users.delete"}

    return (
        RBACRoleSeed("admin", tuple(sorted(keys))),
        RBACRoleSeed("manager", tuple(sorted(manager_keys))),
        RBACRoleSeed("accountant", tuple(sorted(accountant_keys | finance_keys | print_export_keys | view_keys))),
        RBACRoleSeed("cashier", tuple(sorted(cashier_keys))),
        RBACRoleSeed("viewer", tuple(sorted(view_keys | {"reports.print"} & keys))),
    )


def role_seed_map() -> Mapping[str, tuple[str, ...]]:
    return {seed.role_name: seed.permission_keys for seed in role_seed_descriptors()}


def validate_rbac_contract(*, registered_keys: Iterable[str] | None = None) -> dict[str, list[str]]:
    issues: dict[str, list[str]] = {}
    descriptors = required_permission_descriptors()
    keys = [d.key for d in descriptors]
    duplicates = sorted({k for k in keys if keys.count(k) > 1})
    if duplicates:
        issues["duplicates"] = duplicates

    malformed = [k for k in keys if "." not in k or not k.split(".")[0] or not k.split(".")[-1]]
    if malformed:
        issues["malformed"] = sorted(malformed)

    if registered_keys is not None:
        registered = {str(k) for k in registered_keys if str(k)}
        missing = sorted(set(keys) - registered)
        if missing:
            issues["missing_registered_permissions"] = missing

    seeds = role_seed_map()
    for role, role_keys in seeds.items():
        unknown = sorted(set(role_keys) - set(keys))
        if unknown:
            issues[f"role_seed_unknown:{role}"] = unknown
    return issues


def rbac_contract_matrix() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seeds = role_seed_map()
    for d in required_permission_descriptors():
        rows.append({
            "key": d.key,
            "module": d.module,
            "action": d.action,
            "description": d.description,
            "source": d.source,
            "shell_family": d.shell_family,
            "api_resource": d.api_resource,
            "network_mode": d.network_mode,
            "branch_scoped": d.branch_scoped,
            "legacy_alias": d.legacy_alias,
            "admin": d.key in seeds.get("admin", ()),
            "manager": d.key in seeds.get("manager", ()),
            "accountant": d.key in seeds.get("accountant", ()),
            "cashier": d.key in seeds.get("cashier", ()),
            "viewer": d.key in seeds.get("viewer", ()),
        })
    return rows


__all__ = [
    "RBACPermissionDescriptor",
    "RBACRoleSeed",
    "RBAC_API_RESOURCE",
    "required_permission_descriptors",
    "required_permission_keys",
    "permission_descriptor_map",
    "role_seed_descriptors",
    "role_seed_map",
    "validate_rbac_contract",
    "rbac_contract_matrix",
]
