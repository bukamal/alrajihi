# -*- coding: utf-8 -*-
"""PyQt-free runtime visual polish contract.

Phase 344 closes the gap between the registry/column contracts and the actual
widgets users see.  It does not replace individual workspace logic; it defines
safe, measurable defaults that can be applied recursively at runtime:
workspace identity, visual density, spacing profile and table density.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping

from workspace.registry import PAGE_MANIFESTS


@dataclass(frozen=True)
class WorkspaceVisualPolicy:
    page_id: str
    workspace_type: str
    object_name: str
    spacing: int
    margin: int
    table_density: str
    button_role: str
    card_role: str = "card"

    def as_dict(self) -> dict[str, object]:
        return {
            "page_id": self.page_id,
            "workspace_type": self.workspace_type,
            "object_name": self.object_name,
            "spacing": self.spacing,
            "margin": self.margin,
            "table_density": self.table_density,
            "button_role": self.button_role,
            "card_role": self.card_role,
        }


TYPE_DEFAULTS: Mapping[str, dict[str, object]] = {
    "dashboard": {"spacing": 18, "margin": 18, "table_density": "comfortable", "button_role": "dashboard_shortcut"},
    "document": {"spacing": 10, "margin": 12, "table_density": "compact", "button_role": "document_action"},
    "list": {"spacing": 12, "margin": 14, "table_density": "comfortable", "button_role": "list_action"},
    "operational": {"spacing": 14, "margin": 14, "table_density": "touch", "button_role": "operation_action"},
    "matrix": {"spacing": 12, "margin": 14, "table_density": "comfortable", "button_role": "matrix_action"},
    "report": {"spacing": 12, "margin": 14, "table_density": "compact", "button_role": "report_action"},
    "settings": {"spacing": 12, "margin": 14, "table_density": "comfortable", "button_role": "settings_action"},
}

# Workspaces whose old visual fragments should be normalized first.  The set is
# intentionally page-based so adding a new page to PAGE_MANIFESTS will require a
# conscious visual policy rather than silently inheriting inconsistent defaults.
CRITICAL_VISUAL_PAGES: tuple[str, ...] = (
    "dashboard",
    "pos",
    "sales_invoices",
    "purchase_invoices",
    "items",
    "warehouses",
    "cashboxes",
    "restaurant",
    "cafe",
    "apparel",
    "reports",
    "settings",
)


def workspace_visual_policy(page_id: str, workspace_type: str | None = None) -> WorkspaceVisualPolicy:
    manifest = PAGE_MANIFESTS.get(page_id)
    wtype = (workspace_type or (manifest.workspace_type if manifest is not None else "list") or "list").strip().lower()
    defaults = TYPE_DEFAULTS.get(wtype, TYPE_DEFAULTS["list"])
    object_name = f"RuntimeWorkspace_{wtype}_{page_id}".replace(".", "_").replace(":", "_")
    return WorkspaceVisualPolicy(
        page_id=page_id,
        workspace_type=wtype,
        object_name=object_name,
        spacing=int(defaults["spacing"]),
        margin=int(defaults["margin"]),
        table_density=str(defaults["table_density"]),
        button_role=str(defaults["button_role"]),
    )


def workspace_visual_policies() -> Mapping[str, WorkspaceVisualPolicy]:
    return {page_id: workspace_visual_policy(page_id) for page_id in sorted(PAGE_MANIFESTS)}


def visual_polish_rows() -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for page_id, policy in workspace_visual_policies().items():
        manifest = PAGE_MANIFESTS.get(page_id)
        rows.append({
            "category": "workspace_policy",
            "key": page_id,
            "workspace_type": policy.workspace_type,
            "ok": bool(manifest) and policy.workspace_type in TYPE_DEFAULTS and policy.spacing > 0 and policy.margin >= 0,
            "detail": f"object={policy.object_name}; density={policy.table_density}",
        })
    for wtype in sorted(TYPE_DEFAULTS):
        rows.append({
            "category": "workspace_type_default",
            "key": wtype,
            "workspace_type": wtype,
            "ok": TYPE_DEFAULTS[wtype]["table_density"] in {"compact", "comfortable", "touch"},
            "detail": str(TYPE_DEFAULTS[wtype]),
        })
    for page_id in CRITICAL_VISUAL_PAGES:
        rows.append({
            "category": "critical_page",
            "key": page_id,
            "workspace_type": PAGE_MANIFESTS.get(page_id).workspace_type if page_id in PAGE_MANIFESTS else "",
            "ok": page_id in PAGE_MANIFESTS,
            "detail": "covered" if page_id in PAGE_MANIFESTS else "missing from PAGE_MANIFESTS",
        })
    return tuple(rows)


def validate_visual_polish_contract() -> Dict[str, list[str]]:
    issues: Dict[str, list[str]] = {}
    seen_object_names: set[str] = set()
    for row in visual_polish_rows():
        if not row["ok"]:
            issues.setdefault(str(row["category"]), []).append(f"{row['key']}: {row['detail']}")
    for page_id, policy in workspace_visual_policies().items():
        if policy.object_name in seen_object_names:
            issues.setdefault("duplicate_object_name", []).append(policy.object_name)
        seen_object_names.add(policy.object_name)
        if policy.workspace_type not in TYPE_DEFAULTS:
            issues.setdefault("unknown_workspace_type", []).append(f"{page_id}:{policy.workspace_type}")
    manifest_types = {m.workspace_type for m in PAGE_MANIFESTS.values()}
    missing_type_defaults = sorted(t for t in manifest_types if t not in TYPE_DEFAULTS)
    if missing_type_defaults:
        issues.setdefault("missing_type_defaults", []).extend(missing_type_defaults)
    return issues


__all__ = [
    "CRITICAL_VISUAL_PAGES",
    "TYPE_DEFAULTS",
    "WorkspaceVisualPolicy",
    "validate_visual_polish_contract",
    "visual_polish_rows",
    "workspace_visual_policies",
    "workspace_visual_policy",
]
