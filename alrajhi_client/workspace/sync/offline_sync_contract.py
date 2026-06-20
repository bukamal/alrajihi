# -*- coding: utf-8 -*-
"""Canonical offline queue / sync contract for workspace surfaces.

This module is intentionally data-only: it must be importable in CI, PyInstaller
builds, and server/client diagnostic tools without importing PyQt widgets or
opening a database connection.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from workspace.documents.document_contract import (
    NETWORK_LOCAL_ONLY,
    NETWORK_MIXED,
    NETWORK_REMOTE_AVAILABLE,
    NETWORK_REMOTE_REQUIRED,
    all_descriptors,
)

try:  # report descriptors are optional in older builds
    from features.reports.report_shell_contract import all_report_descriptors
except Exception:  # pragma: no cover - compatibility import boundary
    def all_report_descriptors():
        return ()

try:
    from workspace.operational.operational_shell_contract import operational_descriptors
except Exception:  # pragma: no cover
    def operational_descriptors():
        return ()


OFFLINE_POLICY_QUEUE = "queue_when_offline"
OFFLINE_POLICY_BLOCK = "block_when_offline"
OFFLINE_POLICY_READ_ONLY = "read_only_when_offline"
OFFLINE_POLICY_LOCAL_ONLY = "local_only"
OFFLINE_POLICY_PRINT_LOCAL = "print_export_local"
OFFLINE_POLICY_DIAGNOSTIC = "diagnostic_only"

CONFLICT_SERVER_WINS = "server_wins"
CONFLICT_CLIENT_REPLAY = "client_replay"
CONFLICT_IDEMPOTENT_CREATE = "idempotent_create"
CONFLICT_MANUAL_REVIEW = "manual_review"
CONFLICT_NONE = "none"

SYNC_PRIORITY_CRITICAL = 10
SYNC_PRIORITY_NORMAL = 50
SYNC_PRIORITY_LOW = 90

WRITE_METHODS = ("POST", "PUT", "PATCH", "DELETE")
READ_METHODS = ("GET",)


@dataclass(frozen=True)
class OfflineSyncDescriptor:
    """Offline behavior of a workspace/API surface.

    A queued write must declare its API prefixes, allowed write methods, conflict
    policy, branch behavior, and audit behavior.  Read-only/report/print surfaces
    must explicitly declare that they are not queued so the UI can show a clear
    offline message instead of silently losing work.
    """

    surface_key: str
    surface_family: str
    document_type: str
    api_resource: str
    network_mode: str
    offline_policy: str
    allowed_methods: tuple[str, ...] = WRITE_METHODS
    queueable_prefixes: tuple[str, ...] = ()
    conflict_policy: str = CONFLICT_MANUAL_REVIEW
    replay_priority: int = SYNC_PRIORITY_NORMAL
    idempotency_key: str = ""
    branch_required: bool = False
    audit_required: bool = True
    settings_scope: str = ""
    permission_keys: tuple[str, ...] = ()
    source_contract: str = ""
    notes: str = ""

    @property
    def queueable(self) -> bool:
        return self.offline_policy == OFFLINE_POLICY_QUEUE

    def method_allowed(self, method: str) -> bool:
        return (method or "").upper() in {m.upper() for m in self.allowed_methods}

    def matches(self, endpoint: str, method: str = "POST") -> bool:
        endpoint = str(endpoint or "")
        return self.method_allowed(method) and any(endpoint.startswith(prefix) for prefix in self.queueable_prefixes)


@dataclass(frozen=True)
class OfflineDecision:
    endpoint: str
    method: str
    queueable: bool
    offline_policy: str
    surface_key: str = ""
    conflict_policy: str = ""
    replay_priority: int = SYNC_PRIORITY_NORMAL
    reason: str = ""


def _permissions_tuple(obj) -> tuple[str, ...]:
    permissions = getattr(obj, "permissions", None)
    if permissions is None:
        return ()
    values = []
    try:
        for key in permissions.action_map().values():
            if key and key not in values:
                values.append(key)
    except Exception:
        pass
    return tuple(values)


def _descriptor_from_document(document) -> OfflineSyncDescriptor:
    dt = document.document_type
    api = document.api_resource
    queue_documents = {
        "sales_invoice": ("/api/invoices", CONFLICT_IDEMPOTENT_CREATE, SYNC_PRIORITY_CRITICAL),
        "purchase_invoice": ("/api/invoices", CONFLICT_IDEMPOTENT_CREATE, SYNC_PRIORITY_CRITICAL),
        "sales_return": ("/api/returns/sales", CONFLICT_CLIENT_REPLAY, SYNC_PRIORITY_CRITICAL),
        "purchase_return": ("/api/returns/purchase", CONFLICT_CLIENT_REPLAY, SYNC_PRIORITY_CRITICAL),
        "material": ("/api/items", CONFLICT_MANUAL_REVIEW, SYNC_PRIORITY_NORMAL),
        "customer": ("/api/customers", CONFLICT_MANUAL_REVIEW, SYNC_PRIORITY_NORMAL),
        "supplier": ("/api/suppliers", CONFLICT_MANUAL_REVIEW, SYNC_PRIORITY_NORMAL),
        "voucher": ("/api/vouchers", CONFLICT_CLIENT_REPLAY, SYNC_PRIORITY_CRITICAL),
        "expense": ("/api/expenses", CONFLICT_CLIENT_REPLAY, SYNC_PRIORITY_NORMAL),
    }
    if dt in queue_documents:
        prefix, conflict, priority = queue_documents[dt]
        return OfflineSyncDescriptor(
            surface_key=f"document.{dt}",
            surface_family="document",
            document_type=dt,
            api_resource=api or prefix,
            network_mode=document.network_mode,
            offline_policy=OFFLINE_POLICY_QUEUE,
            queueable_prefixes=(prefix,),
            conflict_policy=conflict,
            replay_priority=priority,
            idempotency_key="reference_or_payload_hash",
            branch_required=str(getattr(document, "branch_policy", "")) == "required",
            audit_required=bool(getattr(document.capabilities, "audit", True)),
            settings_scope=document.settings_scope,
            permission_keys=_permissions_tuple(document),
            source_contract="document_shell",
            notes="Write operations are queued only after transport failure; server validation/conflicts still win during replay.",
        )

    if document.network_mode == NETWORK_LOCAL_ONLY:
        policy = OFFLINE_POLICY_LOCAL_ONLY
    elif getattr(document.capabilities, "print", False) or getattr(document.capabilities, "export", False):
        policy = OFFLINE_POLICY_PRINT_LOCAL
    else:
        policy = OFFLINE_POLICY_BLOCK

    return OfflineSyncDescriptor(
        surface_key=f"document.{dt}",
        surface_family="document",
        document_type=dt,
        api_resource=api,
        network_mode=document.network_mode,
        offline_policy=policy,
        allowed_methods=(),
        conflict_policy=CONFLICT_NONE,
        branch_required=str(getattr(document, "branch_policy", "")) == "required",
        audit_required=bool(getattr(document.capabilities, "audit", True)),
        settings_scope=document.settings_scope,
        permission_keys=_permissions_tuple(document),
        source_contract="document_shell",
        notes="Not queued by default; either local-only, print/export local, or requires online server-side consistency.",
    )


def _report_descriptors() -> tuple[OfflineSyncDescriptor, ...]:
    rows: list[OfflineSyncDescriptor] = []
    for report in all_report_descriptors():
        key = getattr(report, "report_key", getattr(report, "key", "report"))
        rows.append(OfflineSyncDescriptor(
            surface_key=f"report.{key}",
            surface_family="report",
            document_type="reports",
            api_resource=getattr(report, "api_resource", "/api/reports"),
            network_mode=getattr(report, "network_mode", NETWORK_MIXED),
            offline_policy=OFFLINE_POLICY_READ_ONLY,
            allowed_methods=READ_METHODS,
            conflict_policy=CONFLICT_NONE,
            replay_priority=SYNC_PRIORITY_LOW,
            branch_required=bool(getattr(report, "branch_filter", False) or getattr(report, "branch_required", False)),
            audit_required=True,
            settings_scope=getattr(report, "settings_scope", "reports"),
            permission_keys=tuple(k for k in (getattr(report, "view_permission", ""), getattr(report, "print_permission", ""), getattr(report, "export_permission", "")) if k),
            source_contract="report_shell",
            notes="Reports are never queued as writes.  Print/export can use the last loaded result; refresh requires online access.",
        ))
    return tuple(rows)


def _operational_descriptors() -> tuple[OfflineSyncDescriptor, ...]:
    rows: list[OfflineSyncDescriptor] = []
    for shell in operational_descriptors():
        if shell.shell_key == "pos":
            rows.append(OfflineSyncDescriptor(
                surface_key="operational.pos.checkout",
                surface_family="operational",
                document_type="pos",
                api_resource="/api/invoices",
                network_mode=shell.network_mode,
                offline_policy=OFFLINE_POLICY_QUEUE,
                allowed_methods=("POST",),
                queueable_prefixes=("/api/invoices",),
                conflict_policy=CONFLICT_IDEMPOTENT_CREATE,
                replay_priority=SYNC_PRIORITY_CRITICAL,
                idempotency_key="pos_ticket_or_payload_hash",
                branch_required=True,
                audit_required=True,
                settings_scope=shell.settings_scope,
                permission_keys=("pos.use", "pos.receipt.print"),
                source_contract="operational_shell",
                notes="POS checkout queues as a sales invoice only.  Shift open/close and cashbox operations remain online-only.",
            ))
            rows.append(OfflineSyncDescriptor(
                surface_key="operational.pos.shift_cashbox",
                surface_family="operational",
                document_type="pos",
                api_resource="/api/pos_shifts",
                network_mode=shell.network_mode,
                offline_policy=OFFLINE_POLICY_BLOCK,
                allowed_methods=(),
                conflict_policy=CONFLICT_NONE,
                branch_required=True,
                audit_required=True,
                settings_scope=shell.settings_scope,
                permission_keys=("pos.shift.open", "pos.shift.close"),
                source_contract="operational_shell",
                notes="Opening/closing shifts and cashbox state are not safe to replay blindly.",
            ))
        elif shell.shell_key == "restaurant":
            rows.append(OfflineSyncDescriptor(
                surface_key="operational.restaurant.session_order_payment",
                surface_family="operational",
                document_type="restaurant",
                api_resource="/api/restaurant",
                network_mode=shell.network_mode,
                offline_policy=OFFLINE_POLICY_BLOCK,
                allowed_methods=(),
                conflict_policy=CONFLICT_NONE,
                branch_required=True,
                audit_required=True,
                settings_scope=shell.settings_scope,
                permission_keys=tuple(sorted({f"restaurant.{op.permission_action}" for op in shell.operations if op.permission_action})),
                source_contract="operational_shell",
                notes="Restaurant sessions, kitchen state, table moves, and split bills require online branch/server consistency.",
            ))
    return tuple(rows)


_AUDIT_LOG_DESCRIPTOR = OfflineSyncDescriptor(
    surface_key="audit.audit_log",
    surface_family="audit",
    document_type="audit_log",
    api_resource="/api/audit_log",
    network_mode=NETWORK_REMOTE_AVAILABLE,
    offline_policy=OFFLINE_POLICY_QUEUE,
    allowed_methods=("POST",),
    queueable_prefixes=("/api/audit_log",),
    conflict_policy=CONFLICT_IDEMPOTENT_CREATE,
    replay_priority=SYNC_PRIORITY_LOW,
    idempotency_key="event_hash",
    branch_required=False,
    audit_required=False,
    settings_scope="security.audit",
    permission_keys=("audit.view",),
    source_contract="audit_trail",
    notes="Client-side audit events should not disappear when the server is temporarily unreachable.",
)


def offline_sync_descriptors() -> tuple[OfflineSyncDescriptor, ...]:
    docs = tuple(_descriptor_from_document(d) for d in all_descriptors())
    return docs + _report_descriptors() + _operational_descriptors() + (_AUDIT_LOG_DESCRIPTOR,)


def offline_descriptor_for(surface_key: str, default: OfflineSyncDescriptor | None = None) -> OfflineSyncDescriptor | None:
    for descriptor in offline_sync_descriptors():
        if descriptor.surface_key == surface_key:
            return descriptor
    return default


def queueable_descriptors() -> tuple[OfflineSyncDescriptor, ...]:
    return tuple(d for d in offline_sync_descriptors() if d.queueable)


def queueable_api_prefixes() -> tuple[str, ...]:
    prefixes: list[str] = []
    for descriptor in queueable_descriptors():
        for prefix in descriptor.queueable_prefixes:
            if prefix and prefix not in prefixes:
                prefixes.append(prefix)
    return tuple(prefixes)


def offline_decision_for_api(endpoint: str, method: str) -> OfflineDecision:
    endpoint = str(endpoint or "")
    method = str(method or "").upper()
    for descriptor in queueable_descriptors():
        if descriptor.matches(endpoint, method):
            return OfflineDecision(
                endpoint=endpoint,
                method=method,
                queueable=True,
                offline_policy=descriptor.offline_policy,
                surface_key=descriptor.surface_key,
                conflict_policy=descriptor.conflict_policy,
                replay_priority=descriptor.replay_priority,
                reason="matched queueable offline sync contract",
            )
    for descriptor in offline_sync_descriptors():
        if endpoint and descriptor.api_resource and endpoint.startswith(descriptor.api_resource):
            return OfflineDecision(
                endpoint=endpoint,
                method=method,
                queueable=False,
                offline_policy=descriptor.offline_policy,
                surface_key=descriptor.surface_key,
                conflict_policy=descriptor.conflict_policy,
                replay_priority=descriptor.replay_priority,
                reason="matched non-queueable offline sync contract",
            )
    return OfflineDecision(
        endpoint=endpoint,
        method=method,
        queueable=False,
        offline_policy=OFFLINE_POLICY_BLOCK,
        reason="no offline sync contract matched this endpoint",
    )


def offline_sync_matrix(descriptors: Iterable[OfflineSyncDescriptor] | None = None) -> list[dict[str, object]]:
    rows = []
    for descriptor in descriptors or offline_sync_descriptors():
        rows.append({
            "surface_key": descriptor.surface_key,
            "surface_family": descriptor.surface_family,
            "document_type": descriptor.document_type,
            "api_resource": descriptor.api_resource,
            "network_mode": descriptor.network_mode,
            "offline_policy": descriptor.offline_policy,
            "queueable": descriptor.queueable,
            "allowed_methods": ",".join(descriptor.allowed_methods),
            "queueable_prefixes": ",".join(descriptor.queueable_prefixes),
            "conflict_policy": descriptor.conflict_policy,
            "replay_priority": descriptor.replay_priority,
            "idempotency_key": descriptor.idempotency_key,
            "branch_required": descriptor.branch_required,
            "audit_required": descriptor.audit_required,
            "settings_scope": descriptor.settings_scope,
            "permission_keys": ",".join(descriptor.permission_keys),
            "source_contract": descriptor.source_contract,
            "notes": descriptor.notes,
        })
    return rows


def validate_offline_sync_descriptors(descriptors: Iterable[OfflineSyncDescriptor] | None = None) -> list[str]:
    warnings: list[str] = []
    seen: set[str] = set()
    for descriptor in descriptors or offline_sync_descriptors():
        if not descriptor.surface_key:
            warnings.append("offline sync descriptor missing surface_key")
        if descriptor.surface_key in seen:
            warnings.append(f"duplicate offline sync descriptor: {descriptor.surface_key}")
        seen.add(descriptor.surface_key)
        if descriptor.network_mode in {NETWORK_REMOTE_AVAILABLE, NETWORK_REMOTE_REQUIRED, NETWORK_MIXED} and not descriptor.api_resource:
            warnings.append(f"{descriptor.surface_key}: network surface without api_resource")
        if descriptor.queueable:
            if not descriptor.queueable_prefixes:
                warnings.append(f"{descriptor.surface_key}: queueable without queueable_prefixes")
            if not descriptor.allowed_methods:
                warnings.append(f"{descriptor.surface_key}: queueable without allowed_methods")
            if any(m not in WRITE_METHODS for m in descriptor.allowed_methods):
                warnings.append(f"{descriptor.surface_key}: queueable read method declared as write replay")
            if not descriptor.idempotency_key:
                warnings.append(f"{descriptor.surface_key}: queueable without idempotency_key")
            if descriptor.conflict_policy == CONFLICT_NONE:
                warnings.append(f"{descriptor.surface_key}: queueable without conflict_policy")
        else:
            if descriptor.queueable_prefixes:
                warnings.append(f"{descriptor.surface_key}: non-queueable descriptor has prefixes")
    return warnings


__all__ = [
    "OfflineSyncDescriptor",
    "OfflineDecision",
    "OFFLINE_POLICY_QUEUE",
    "OFFLINE_POLICY_BLOCK",
    "OFFLINE_POLICY_READ_ONLY",
    "OFFLINE_POLICY_LOCAL_ONLY",
    "OFFLINE_POLICY_PRINT_LOCAL",
    "OFFLINE_POLICY_DIAGNOSTIC",
    "CONFLICT_SERVER_WINS",
    "CONFLICT_CLIENT_REPLAY",
    "CONFLICT_IDEMPOTENT_CREATE",
    "CONFLICT_MANUAL_REVIEW",
    "offline_sync_descriptors",
    "offline_descriptor_for",
    "queueable_descriptors",
    "queueable_api_prefixes",
    "offline_decision_for_api",
    "offline_sync_matrix",
    "validate_offline_sync_descriptors",
]
