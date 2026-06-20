# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from workspace.documents.document_contract import all_descriptors
from workspace.lists.list_workspace_contract import list_descriptors
from workspace.operational.operational_shell_contract import operational_descriptors

try:
    from features.reports.report_shell_contract import all_report_descriptors
except Exception:  # pragma: no cover - keeps PyQt-free contract imports robust
    all_report_descriptors = lambda: ()

AUDIT_CATEGORY_DOCUMENT = "document"
AUDIT_CATEGORY_LIST = "list"
AUDIT_CATEGORY_REPORT = "report"
AUDIT_CATEGORY_OPERATIONAL = "operational"
AUDIT_CATEGORY_SECURITY = "security"

AUDIT_SEVERITY_INFO = "info"
AUDIT_SEVERITY_WARNING = "warning"
AUDIT_SEVERITY_CRITICAL = "critical"


@dataclass(frozen=True)
class AuditEventDescriptor:
    """Canonical audit contract for a business/UI/API event.

    The descriptor is data-only by design so CI, PyInstaller builds and support
    diagnostics can inspect audit coverage without importing PyQt widgets.
    """

    event_key: str
    audit_scope: str
    category: str
    action: str
    entity_type: str
    permission_key: str = ""
    api_resource: str = ""
    source_contract: str = ""
    network_mode: str = ""
    branch_scoped: bool = False
    required: bool = True
    severity: str = AUDIT_SEVERITY_INFO
    details: str = ""

    @property
    def action_code(self) -> str:
        return self.action.upper().replace(".", "_").replace("-", "_")


def _document_events() -> list[AuditEventDescriptor]:
    events: list[AuditEventDescriptor] = []
    for descriptor in all_descriptors():
        if not descriptor.capabilities.audit:
            continue
        scope = descriptor.audit_scope or descriptor.document_type
        action_map = descriptor.permissions.action_map()
        base = {
            "audit_scope": scope,
            "entity_type": descriptor.document_type,
            "api_resource": descriptor.api_resource,
            "source_contract": "document_shell",
            "network_mode": descriptor.network_mode,
            "branch_scoped": descriptor.branch_policy in {"required", "user_branch_access"},
        }
        # View is always auditable for sensitive support diagnostics, but it is
        # info-level and can be filtered out at retention/UI level if desired.
        events.append(AuditEventDescriptor(
            event_key=f"document.{descriptor.document_type}.view",
            category=AUDIT_CATEGORY_DOCUMENT,
            action="view",
            permission_key=action_map.get("view", ""),
            severity=AUDIT_SEVERITY_INFO,
            **base,
        ))
        for action, supported in (
            ("save", descriptor.capabilities.save),
            ("delete", descriptor.capabilities.delete),
            ("print", descriptor.capabilities.print),
            ("export", descriptor.capabilities.export),
            ("approve", descriptor.capabilities.approve),
            ("cancel", descriptor.capabilities.cancel),
        ):
            if not supported:
                continue
            permission_action = "update" if action == "save" else action
            permission = action_map.get(permission_action, "") or action_map.get("create", "")
            severity = AUDIT_SEVERITY_CRITICAL if action in {"delete", "approve", "cancel"} else AUDIT_SEVERITY_INFO
            events.append(AuditEventDescriptor(
                event_key=f"document.{descriptor.document_type}.{action}",
                category=AUDIT_CATEGORY_DOCUMENT,
                action=action,
                permission_key=permission,
                severity=severity,
                **base,
            ))
    return events


def _list_events() -> list[AuditEventDescriptor]:
    events: list[AuditEventDescriptor] = []
    for descriptor in list_descriptors():
        scope = descriptor.audit_scope or descriptor.list_key
        document = descriptor.document_descriptor
        permissions = document.permissions.action_map() if document else {}
        base = {
            "audit_scope": scope,
            "entity_type": descriptor.document_type,
            "api_resource": descriptor.api_resource,
            "source_contract": "list_workspace",
            "network_mode": descriptor.network_mode,
            "branch_scoped": descriptor.branch_policy in {"required", "user_branch_access"},
        }
        for action, supported, permission_action in (
            ("open", descriptor.capabilities.row_open, "view"),
            ("search", descriptor.capabilities.search, "view"),
            ("filter", descriptor.capabilities.filters, "view"),
            ("create", descriptor.capabilities.create, "create"),
            ("delete", descriptor.capabilities.delete, "delete"),
            ("print", descriptor.capabilities.print, "print"),
            ("export", descriptor.capabilities.export, "export"),
        ):
            if not supported:
                continue
            events.append(AuditEventDescriptor(
                event_key=f"list.{descriptor.list_key}.{action}",
                category=AUDIT_CATEGORY_LIST,
                action=action,
                permission_key=permissions.get(permission_action, ""),
                severity=AUDIT_SEVERITY_CRITICAL if action == "delete" else AUDIT_SEVERITY_INFO,
                **base,
            ))
    return events


def _report_events() -> list[AuditEventDescriptor]:
    events: list[AuditEventDescriptor] = []
    for descriptor in all_report_descriptors():
        scope = descriptor.audit_scope or descriptor.report_key
        base = {
            "audit_scope": scope,
            "entity_type": f"report.{descriptor.report_key}",
            "api_resource": descriptor.api_resource,
            "source_contract": "report_shell",
            "network_mode": descriptor.network_mode,
            "branch_scoped": descriptor.branch_policy in {"required", "user_branch_access"},
        }
        events.append(AuditEventDescriptor(
            event_key=f"report.{descriptor.report_key}.view",
            category=AUDIT_CATEGORY_REPORT,
            action="view",
            permission_key=descriptor.permission_view,
            **base,
        ))
        if descriptor.supports_print:
            events.append(AuditEventDescriptor(
                event_key=f"report.{descriptor.report_key}.print",
                category=AUDIT_CATEGORY_REPORT,
                action="print",
                permission_key=descriptor.permission_print,
                **base,
            ))
        if descriptor.supports_export:
            events.append(AuditEventDescriptor(
                event_key=f"report.{descriptor.report_key}.export",
                category=AUDIT_CATEGORY_REPORT,
                action="export",
                permission_key=descriptor.permission_export,
                **base,
            ))
    return events


def _operational_events() -> list[AuditEventDescriptor]:
    from workspace.security.rbac_contract import OPERATION_ACTION_PERMISSION_MAP

    events: list[AuditEventDescriptor] = []
    for descriptor in operational_descriptors():
        doc_permissions = descriptor.document_descriptor.permissions.action_map() if descriptor.document_descriptor else {}
        base = {
            "audit_scope": descriptor.audit_scope or descriptor.shell_key,
            "entity_type": descriptor.document_type,
            "api_resource": descriptor.api_resource,
            "source_contract": "operational_shell",
            "network_mode": descriptor.network_mode,
            "branch_scoped": descriptor.branch_policy in {"required", "user_branch_access"},
        }
        for operation in descriptor.operations:
            # Prefer explicit operation permission mapping from the shell, but
            # fall back to the document descriptor when the operation uses a
            # generic print/view action.
            permission = OPERATION_ACTION_PERMISSION_MAP.get(operation.permission_action, getattr(operation, "permission_key", "") or doc_permissions.get(operation.permission_action, ""))
            severity = AUDIT_SEVERITY_CRITICAL if operation.category in {"payment", "shift"} or operation.key in {"checkout", "close_shift"} else AUDIT_SEVERITY_INFO
            events.append(AuditEventDescriptor(
                event_key=f"operational.{descriptor.shell_key}.{operation.key}",
                category=AUDIT_CATEGORY_OPERATIONAL,
                action=operation.key,
                permission_key=permission,
                severity=severity,
                details=f"requires_session={operation.requires_session}; requires_shift={operation.requires_shift}; requires_cashbox={operation.requires_cashbox}; requires_warehouse={operation.requires_warehouse}",
                **base,
            ))
    return events


def audit_event_descriptors() -> tuple[AuditEventDescriptor, ...]:
    return tuple(_document_events() + _list_events() + _report_events() + _operational_events())


def audit_event_descriptor_for(event_key: str, default: AuditEventDescriptor | None = None) -> AuditEventDescriptor | None:
    key = str(event_key or "")
    for descriptor in audit_event_descriptors():
        if descriptor.event_key == key:
            return descriptor
    return default


def audit_event_matrix(descriptors: Iterable[AuditEventDescriptor] | None = None) -> list[dict[str, object]]:
    rows = []
    for descriptor in descriptors or audit_event_descriptors():
        rows.append({
            "event_key": descriptor.event_key,
            "audit_scope": descriptor.audit_scope,
            "category": descriptor.category,
            "action": descriptor.action,
            "action_code": descriptor.action_code,
            "entity_type": descriptor.entity_type,
            "permission_key": descriptor.permission_key,
            "api_resource": descriptor.api_resource,
            "source_contract": descriptor.source_contract,
            "network_mode": descriptor.network_mode,
            "branch_scoped": descriptor.branch_scoped,
            "required": descriptor.required,
            "severity": descriptor.severity,
            "details": descriptor.details,
        })
    return rows


def validate_audit_event_descriptors(descriptors: Iterable[AuditEventDescriptor] | None = None) -> list[str]:
    warnings: list[str] = []
    seen: set[str] = set()
    for descriptor in descriptors or audit_event_descriptors():
        if not descriptor.event_key:
            warnings.append("audit event without event_key")
        if descriptor.event_key in seen:
            warnings.append(f"duplicate audit event: {descriptor.event_key}")
        seen.add(descriptor.event_key)
        for field_name in ("audit_scope", "category", "action", "entity_type", "source_contract"):
            if not str(getattr(descriptor, field_name, "") or "").strip():
                warnings.append(f"{descriptor.event_key}: missing {field_name}")
        if descriptor.required and descriptor.category != AUDIT_CATEGORY_SECURITY and not descriptor.permission_key and descriptor.action not in {"search", "filter"}:
            warnings.append(f"{descriptor.event_key}: missing permission_key")
    return warnings


def audit_scope_map() -> Mapping[str, tuple[AuditEventDescriptor, ...]]:
    scopes: dict[str, list[AuditEventDescriptor]] = {}
    for descriptor in audit_event_descriptors():
        scopes.setdefault(descriptor.audit_scope, []).append(descriptor)
    return {key: tuple(value) for key, value in scopes.items()}
