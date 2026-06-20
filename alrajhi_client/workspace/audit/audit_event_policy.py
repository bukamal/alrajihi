# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Mapping

from .audit_contract import audit_event_descriptor_for


def _safe_getattr(obj: Any, name: str, default=None):
    try:
        return getattr(obj, name, default)
    except Exception:
        return default


def descriptor_from_widget(widget: Any):
    for attr in ("document_descriptor", "list_workspace_descriptor", "operational_shell_descriptor"):
        descriptor = _safe_getattr(widget, attr)
        if descriptor is not None:
            return descriptor
    return None


def document_id_from_widget(widget: Any):
    state = _safe_getattr(widget, "document_state")
    if state is not None:
        return _safe_getattr(state, "document_id")
    for attr in ("document_id", "current_id", "record_id", "invoice_id", "return_id"):
        value = _safe_getattr(widget, attr)
        if value is not None:
            return value
    return None


def audit_scope_from_descriptor(descriptor: Any) -> str:
    return str(_safe_getattr(descriptor, "audit_scope", "") or _safe_getattr(descriptor, "document_type", "") or _safe_getattr(descriptor, "list_key", "") or _safe_getattr(descriptor, "shell_key", ""))


def entity_type_from_descriptor(descriptor: Any) -> str:
    return str(_safe_getattr(descriptor, "document_type", "") or _safe_getattr(descriptor, "list_key", "") or _safe_getattr(descriptor, "shell_key", "") or "WORKSPACE")


def permission_for_descriptor_action(descriptor: Any, action: str) -> str:
    try:
        permissions = _safe_getattr(descriptor, "permissions")
        if permissions and hasattr(permissions, "action_map"):
            if action == "save":
                return permissions.action_map().get("update") or permissions.action_map().get("create") or ""
            return permissions.action_map().get(action, "")
    except Exception:
        pass
    for attr in (f"permission_{action}", "permission_view"):
        value = _safe_getattr(descriptor, attr, "")
        if value:
            return str(value)
    return ""


def branch_id_from_widget(widget: Any):
    for attr in ("branch_id", "current_branch_id", "selected_branch_id"):
        value = _safe_getattr(widget, attr)
        if value:
            return value
    try:
        state = _safe_getattr(widget, "document_state")
        value = _safe_getattr(state, "branch_id")
        if value:
            return value
    except Exception:
        pass
    return None


def log_workspace_event(
    widget: Any,
    action: str,
    *,
    permitted: bool = True,
    details: str = "",
    extra: Mapping[str, Any] | None = None,
) -> None:
    """Best-effort audit logger for workspace-level UI actions.

    Business services still log authoritative create/update/delete events.  This
    helper covers UI-only events such as print/export, permission denials and
    shell routing diagnostics, especially in client/server mode where the server
    cannot otherwise see a browser print action.
    """
    try:
        from core.services.audit_service import audit_service

        descriptor = descriptor_from_widget(widget)
        entity_type = entity_type_from_descriptor(descriptor)
        audit_scope = audit_scope_from_descriptor(descriptor)
        entity_id = document_id_from_widget(widget)
        permission_key = permission_for_descriptor_action(descriptor, action)
        branch_id = branch_id_from_widget(widget)
        event_action = ("DENIED_" if not permitted else "SHELL_") + str(action or "action").upper()
        payload = {
            "ui_action": action,
            "permitted": bool(permitted),
            "document_type": entity_type,
            "audit_scope": audit_scope,
            "permission_key": permission_key,
            "branch_id": branch_id,
        }
        if extra:
            payload.update(dict(extra))
        audit_service.log(
            event_action,
            entity_type.upper(),
            entity_id,
            new_values=payload,
            details=details or f"Workspace {action}",
            source="WORKSPACE",
            audit_scope=audit_scope,
            permission_key=permission_key,
            branch_id=branch_id,
            event_category="workspace",
        )
    except Exception:
        pass


def log_contract_event(event_key: str, *, entity_id=None, old_values=None, new_values=None, details: str = "", source: str = "CONTRACT") -> None:
    try:
        from core.services.audit_service import audit_service
        descriptor = audit_event_descriptor_for(event_key)
        if descriptor is None:
            return
        audit_service.log(
            descriptor.action_code,
            descriptor.entity_type.upper(),
            entity_id,
            old_values=old_values,
            new_values=new_values,
            details=details or descriptor.details or event_key,
            source=source,
            audit_scope=descriptor.audit_scope,
            permission_key=descriptor.permission_key,
            event_category=descriptor.category,
        )
    except Exception:
        pass
