# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from workspace.documents.document_contract import (
    BRANCH_NONE,
    BRANCH_OPTIONAL,
    BRANCH_REQUIRED,
    BRANCH_USER_ACCESS,
    NETWORK_LOCAL_ONLY,
    all_descriptors,
)
from workspace.lists.list_workspace_contract import list_descriptors
from workspace.operational.operational_shell_contract import operational_descriptors
from workspace.security.rbac_contract import required_permission_descriptors

try:  # reports live under features to avoid coupling the workspace package to UI widgets.
    from features.reports.report_shell_contract import all_report_descriptors
except Exception:  # pragma: no cover - defensive for partial analysis builds
    def all_report_descriptors():
        return ()

BRANCH_SOURCE_NONE = "none"
BRANCH_SOURCE_PAYLOAD = "payload.branch_id"
BRANCH_SOURCE_SESSION = "session.current_branch_id"
BRANCH_SOURCE_ALLOWED = "rbac.user_branch_access"
BRANCH_SOURCE_WAREHOUSE = "warehouse.branch_id"
BRANCH_SOURCE_CASHBOX = "cashbox.branch_id"
BRANCH_SOURCE_REPORT_FILTER = "report.filter.branch_id"

ENFORCEMENT_NONE = "none"
ENFORCEMENT_OPTIONAL = "optional_scope"
ENFORCEMENT_REQUIRED = "required_scope"
ENFORCEMENT_USER_ACCESS = "user_branch_access"

SERVER_STATUS_NOT_APPLICABLE = "not_applicable"
SERVER_STATUS_REQUIRED = "required"
SERVER_STATUS_CLIENT_SIDE_ONLY = "client_side_only"

BRANCH_POLICIES = {BRANCH_NONE, BRANCH_OPTIONAL, BRANCH_REQUIRED, BRANCH_USER_ACCESS}
ENFORCED_BRANCH_POLICIES = {BRANCH_OPTIONAL, BRANCH_REQUIRED, BRANCH_USER_ACCESS}


@dataclass(frozen=True)
class BranchAccessDescriptor:
    """Branch visibility/enforcement contract for one workspace surface.

    Branch access is intentionally separate from generic RBAC permissions.  A
    user can have ``sales_invoices.view`` and still be limited to branch 3.  The
    fields below make that distinction inspectable in CI and reusable by client
    helpers and server repositories.
    """

    key: str
    source_kind: str
    title_key: str
    branch_policy: str
    enforcement: str
    branch_source: str
    permission_view: str
    api_resource: str
    network_mode: str
    i18n_scope: str
    settings_scope: str
    audit_scope: str
    server_blueprint: str = ""
    requires_server_filter: bool = False
    requires_payload_branch: bool = False
    requires_allowed_branch_check: bool = False
    local_only: bool = False
    notes: str = ""

    @property
    def is_branch_scoped(self) -> bool:
        return self.branch_policy in ENFORCED_BRANCH_POLICIES

    @property
    def server_status(self) -> str:
        if self.branch_policy == BRANCH_NONE:
            return SERVER_STATUS_NOT_APPLICABLE
        if self.local_only:
            return SERVER_STATUS_CLIENT_SIDE_ONLY
        return SERVER_STATUS_REQUIRED if self.requires_server_filter else SERVER_STATUS_NOT_APPLICABLE


def _enforcement_for(policy: str) -> str:
    if policy == BRANCH_NONE:
        return ENFORCEMENT_NONE
    if policy == BRANCH_REQUIRED:
        return ENFORCEMENT_REQUIRED
    if policy == BRANCH_USER_ACCESS:
        return ENFORCEMENT_USER_ACCESS
    return ENFORCEMENT_OPTIONAL


def _branch_source_for(policy: str, *, source_kind: str) -> str:
    if policy == BRANCH_NONE:
        return BRANCH_SOURCE_NONE
    if source_kind == "report":
        return BRANCH_SOURCE_REPORT_FILTER
    if source_kind == "operational":
        return BRANCH_SOURCE_SESSION
    if policy == BRANCH_USER_ACCESS:
        return BRANCH_SOURCE_ALLOWED
    return BRANCH_SOURCE_PAYLOAD


def _permission_from_document(descriptor) -> str:
    permissions = getattr(descriptor, "permissions", None)
    return getattr(permissions, "view", "") if permissions is not None else ""


def _descriptor_key(prefix: str, key: str) -> str:
    return f"{prefix}:{key}"


def _from_document(descriptor) -> BranchAccessDescriptor:
    policy = getattr(descriptor, "branch_policy", BRANCH_NONE)
    local_only = getattr(descriptor, "network_mode", "") == NETWORK_LOCAL_ONLY
    return BranchAccessDescriptor(
        key=_descriptor_key("document", descriptor.document_type),
        source_kind="document",
        title_key=descriptor.title_key,
        branch_policy=policy,
        enforcement=_enforcement_for(policy),
        branch_source=_branch_source_for(policy, source_kind="document"),
        permission_view=_permission_from_document(descriptor),
        api_resource=descriptor.api_resource,
        network_mode=descriptor.network_mode,
        i18n_scope=descriptor.i18n_scope,
        settings_scope=descriptor.settings_scope,
        audit_scope=descriptor.audit_scope,
        server_blueprint=descriptor.server_blueprint,
        requires_server_filter=policy in {BRANCH_REQUIRED, BRANCH_USER_ACCESS},
        requires_payload_branch=policy == BRANCH_REQUIRED,
        requires_allowed_branch_check=policy in {BRANCH_REQUIRED, BRANCH_USER_ACCESS},
        local_only=local_only,
        notes=getattr(descriptor, "notes", ""),
    )


def _from_list(descriptor) -> BranchAccessDescriptor:
    policy = getattr(descriptor, "branch_policy", BRANCH_NONE)
    local_only = getattr(descriptor, "network_mode", "") == NETWORK_LOCAL_ONLY
    return BranchAccessDescriptor(
        key=_descriptor_key("list", descriptor.list_key),
        source_kind="list",
        title_key=descriptor.title_key,
        branch_policy=policy,
        enforcement=_enforcement_for(policy),
        branch_source=_branch_source_for(policy, source_kind="list"),
        permission_view=descriptor.permission_for("view"),
        api_resource=descriptor.api_resource,
        network_mode=descriptor.network_mode,
        i18n_scope=descriptor.i18n_scope,
        settings_scope=descriptor.settings_scope,
        audit_scope=descriptor.audit_scope,
        server_blueprint=descriptor.server_blueprint,
        requires_server_filter=policy in {BRANCH_OPTIONAL, BRANCH_REQUIRED, BRANCH_USER_ACCESS},
        requires_payload_branch=False,
        requires_allowed_branch_check=policy in {BRANCH_REQUIRED, BRANCH_USER_ACCESS},
        local_only=local_only,
        notes=getattr(descriptor, "notes", ""),
    )


def _from_report(descriptor) -> BranchAccessDescriptor:
    policy = getattr(descriptor, "branch_policy", BRANCH_OPTIONAL)
    local_only = getattr(descriptor, "network_mode", "") == NETWORK_LOCAL_ONLY
    return BranchAccessDescriptor(
        key=_descriptor_key("report", descriptor.report_key),
        source_kind="report",
        title_key=descriptor.title_key,
        branch_policy=policy,
        enforcement=_enforcement_for(policy),
        branch_source=_branch_source_for(policy, source_kind="report"),
        permission_view=getattr(descriptor, "permission_view", "reports.view"),
        api_resource=descriptor.api_resource,
        network_mode=descriptor.network_mode,
        i18n_scope=descriptor.i18n_scope,
        settings_scope=descriptor.settings_scope,
        audit_scope=descriptor.audit_scope,
        server_blueprint=getattr(descriptor, "server_blueprint", "reports"),
        requires_server_filter=policy in {BRANCH_OPTIONAL, BRANCH_REQUIRED, BRANCH_USER_ACCESS} and not local_only,
        requires_payload_branch=False,
        requires_allowed_branch_check=policy in {BRANCH_REQUIRED, BRANCH_USER_ACCESS},
        local_only=local_only,
        notes=getattr(descriptor, "notes", ""),
    )


def _from_operational(descriptor) -> BranchAccessDescriptor:
    policy = getattr(descriptor, "branch_policy", BRANCH_REQUIRED)
    local_only = getattr(descriptor, "network_mode", "") == NETWORK_LOCAL_ONLY
    branch_source = BRANCH_SOURCE_SESSION
    if getattr(descriptor, "cashbox_policy", "") == "required":
        branch_source = BRANCH_SOURCE_CASHBOX
    if getattr(descriptor, "warehouse_policy", "") == "required":
        branch_source = f"{branch_source}+{BRANCH_SOURCE_WAREHOUSE}"
    return BranchAccessDescriptor(
        key=_descriptor_key("operational", descriptor.shell_key),
        source_kind="operational",
        title_key=descriptor.title_key,
        branch_policy=policy,
        enforcement=_enforcement_for(policy),
        branch_source=branch_source,
        permission_view=_permission_from_document(descriptor.document_descriptor) or f"{descriptor.shell_key}.use",
        api_resource=descriptor.api_resource,
        network_mode=descriptor.network_mode,
        i18n_scope=descriptor.i18n_scope,
        settings_scope=descriptor.settings_scope,
        audit_scope=descriptor.audit_scope,
        server_blueprint=descriptor.server_blueprint,
        requires_server_filter=True,
        requires_payload_branch=True,
        requires_allowed_branch_check=True,
        local_only=local_only,
        notes=getattr(descriptor, "notes", ""),
    )


def branch_access_descriptors() -> tuple[BranchAccessDescriptor, ...]:
    result: list[BranchAccessDescriptor] = []
    result.extend(_from_document(d) for d in all_descriptors())
    result.extend(_from_list(d) for d in list_descriptors())
    result.extend(_from_report(d) for d in all_report_descriptors())
    result.extend(_from_operational(d) for d in operational_descriptors())
    return tuple(result)


def branch_access_descriptor_map() -> Mapping[str, BranchAccessDescriptor]:
    return {d.key: d for d in branch_access_descriptors()}


def branch_scoped_descriptors() -> tuple[BranchAccessDescriptor, ...]:
    return tuple(d for d in branch_access_descriptors() if d.is_branch_scoped)


def validate_branch_access_contract(*, rbac_branch_scoped_keys: Iterable[str] | None = None) -> dict[str, list[str]]:
    issues: dict[str, list[str]] = {}
    seen: set[str] = set()
    known_rbac = set(rbac_branch_scoped_keys or ())

    for descriptor in branch_access_descriptors():
        if descriptor.key in seen:
            issues.setdefault("duplicate_key", []).append(descriptor.key)
        seen.add(descriptor.key)
        if descriptor.branch_policy not in BRANCH_POLICIES:
            issues.setdefault("invalid_policy", []).append(f"{descriptor.key}: {descriptor.branch_policy}")
        if descriptor.is_branch_scoped and not descriptor.permission_view:
            issues.setdefault("missing_view_permission", []).append(descriptor.key)
        if descriptor.requires_payload_branch and descriptor.branch_source == BRANCH_SOURCE_NONE:
            issues.setdefault("missing_branch_source", []).append(descriptor.key)
        if descriptor.requires_server_filter and not descriptor.local_only and not descriptor.api_resource:
            issues.setdefault("missing_api_resource", []).append(descriptor.key)
        if descriptor.requires_allowed_branch_check and known_rbac and descriptor.permission_view not in known_rbac:
            issues.setdefault("rbac_branch_scope_mismatch", []).append(f"{descriptor.key}: {descriptor.permission_view}")

    # These cross-cutting permissions are used by PermissionService/RBACService to
    # decide all-branch access; the branch contract is incomplete without them.
    if known_rbac:
        for key in ("branches.view_all", "branches.manage_all"):
            if key not in known_rbac:
                issues.setdefault("missing_cross_branch_permission", []).append(key)
    return issues


def branch_access_matrix() -> list[dict[str, object]]:
    return [
        {
            "key": d.key,
            "source_kind": d.source_kind,
            "title_key": d.title_key,
            "branch_policy": d.branch_policy,
            "enforcement": d.enforcement,
            "branch_source": d.branch_source,
            "permission_view": d.permission_view,
            "api_resource": d.api_resource,
            "network_mode": d.network_mode,
            "i18n_scope": d.i18n_scope,
            "settings_scope": d.settings_scope,
            "audit_scope": d.audit_scope,
            "server_blueprint": d.server_blueprint,
            "requires_server_filter": d.requires_server_filter,
            "requires_payload_branch": d.requires_payload_branch,
            "requires_allowed_branch_check": d.requires_allowed_branch_check,
            "local_only": d.local_only,
            "server_status": d.server_status,
            "notes": d.notes,
        }
        for d in branch_access_descriptors()
    ]


__all__ = [
    "BranchAccessDescriptor",
    "branch_access_descriptors",
    "branch_access_descriptor_map",
    "branch_scoped_descriptors",
    "validate_branch_access_contract",
    "branch_access_matrix",
]
