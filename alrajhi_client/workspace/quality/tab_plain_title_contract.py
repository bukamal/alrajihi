# -*- coding: utf-8 -*-
"""Phase 373 contract: workspace tab captions use plain business titles.

The shell may keep internal main/sub kind metadata, but the visible tab text and
tooltip must not include the old Arabic prefixes.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[3]
FORBIDDEN_VISIBLE_PREFIXES = ("رئيسي ·", "فرعي ·", "رئيسية ·", "فرعية ·")
FORBIDDEN_TOOLTIP_PREFIXES = ("رئيسي —", "فرعي —", "رئيسية —", "فرعية —")
PHASE = 373


def _load_policy(root: Path | None = None):
    import importlib.util
    import sys

    base = root or ROOT
    path = base / "alrajhi_client" / "shell" / "tab_label_policy.py"
    spec = importlib.util.spec_from_file_location("phase373_tab_label_policy", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load tab label policy from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.compose_tab_label, module.label_for_kind, module.tab_kind_for_id, module.BRANDED_TAB_PHASE


def tab_plain_title_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    rows: List[Dict[str, object]] = []
    policy_path = base / "alrajhi_client" / "shell" / "tab_label_policy.py"
    workspace_path = base / "alrajhi_client" / "shell" / "tab_workspace.py"

    rows.append({
        "key": "policy_file",
        "category": "file",
        "description": "Tab label policy file exists",
        "status": "pass" if policy_path.exists() else "fail",
        "detail": str(policy_path.relative_to(base)) if policy_path.exists() else str(policy_path),
    })
    rows.append({
        "key": "workspace_file",
        "category": "file",
        "description": "Tabbed workspace runtime file exists",
        "status": "pass" if workspace_path.exists() else "fail",
        "detail": str(workspace_path.relative_to(base)) if workspace_path.exists() else str(workspace_path),
    })
    if not policy_path.exists():
        return rows

    policy_text = policy_path.read_text(encoding="utf-8")
    rows.append({
        "key": "phase_marker",
        "category": "policy",
        "description": "Tab label policy marks Phase373 plain-title behavior",
        "status": "pass" if "BRANDED_TAB_PHASE = 373" in policy_text and "Phase373" in policy_text else "fail",
        "detail": "BRANDED_TAB_PHASE = 373 / Phase373",
    })
    rows.append({
        "key": "no_visible_label_composition",
        "category": "policy",
        "description": "Display text no longer composes visible kind label with title",
        "status": "pass" if 'f"{label} ·' not in policy_text and "f'{label} ·" not in policy_text else "fail",
        "detail": "no f'{label} · {title}' display composition",
    })
    rows.append({
        "key": "plain_display_assignment",
        "category": "policy",
        "description": "Policy assigns display from clean_title only",
        "status": "pass" if "display = clean_title" in policy_text else "fail",
        "detail": "display = clean_title",
    })

    try:
        compose_tab_label, label_for_kind, tab_kind_for_id, branded_phase = _load_policy(base)
    except Exception as exc:  # pragma: no cover - guard diagnostics
        rows.append({"key": "policy_import", "category": "runtime", "description": "Policy imports", "status": "fail", "detail": repr(exc)})
        return rows

    rows.append({
        "key": "phase_runtime",
        "category": "runtime",
        "description": "Runtime policy phase is at least Phase373",
        "status": "pass" if int(branded_phase) >= PHASE else "fail",
        "detail": branded_phase,
    })

    samples = [
        ("sales_invoices", "فواتير البيع", "main"),
        ("invoice:sale:new", "فاتورة بيع جديدة", "sub"),
        ("settings:print", "إعدادات الطباعة", "sub"),
        ("materials", "المواد", "main"),
    ]
    for tab_id, title, expected_kind in samples:
        identity = compose_tab_label(tab_id, title)
        forbidden_display = any(str(identity.display_text).startswith(prefix) for prefix in FORBIDDEN_VISIBLE_PREFIXES)
        forbidden_tooltip = any(str(identity.tooltip).startswith(prefix) for prefix in FORBIDDEN_TOOLTIP_PREFIXES)
        rows.append({
            "key": f"display_{tab_id.replace(':', '_')}",
            "category": "visible_text",
            "description": "Visible tab text is exactly the business title",
            "status": "pass" if identity.display_text == title and not forbidden_display else "fail",
            "detail": identity.display_text,
        })
        rows.append({
            "key": f"tooltip_{tab_id.replace(':', '_')}",
            "category": "visible_text",
            "description": "Tab tooltip is exactly the business title",
            "status": "pass" if identity.tooltip == title and not forbidden_tooltip else "fail",
            "detail": identity.tooltip,
        })
        rows.append({
            "key": f"kind_{tab_id.replace(':', '_')}",
            "category": "metadata",
            "description": "Internal tab kind metadata remains available",
            "status": "pass" if identity.kind == expected_kind and tab_kind_for_id(tab_id) == expected_kind else "fail",
            "detail": f"{identity.kind}/{tab_kind_for_id(tab_id)}",
        })

    rows.append({
        "key": "label_metadata_main",
        "category": "metadata",
        "description": "Internal main label is non-visible English metadata",
        "status": "pass" if label_for_kind("main") == "main" else "fail",
        "detail": label_for_kind("main"),
    })
    rows.append({
        "key": "label_metadata_sub",
        "category": "metadata",
        "description": "Internal sub label is non-visible English metadata",
        "status": "pass" if label_for_kind("sub") == "sub" else "fail",
        "detail": label_for_kind("sub"),
    })

    if workspace_path.exists():
        workspace_text = workspace_path.read_text(encoding="utf-8")
        rows.append({
            "key": "workspace_uses_display_text",
            "category": "runtime",
            "description": "TabbedWorkspace renders the policy display_text",
            "status": "pass" if "self.setTabText(index, identity.display_text)" in workspace_text else "fail",
            "detail": "setTabText(index, identity.display_text)",
        })
        rows.append({
            "key": "workspace_keeps_kind_metadata",
            "category": "runtime",
            "description": "TabbedWorkspace still stores kind metadata",
            "status": "pass" if "'tab_kind': identity.kind" in workspace_text and "setTabWhatsThis(index, identity.kind)" in workspace_text else "fail",
            "detail": "tab_kind / WhatsThis",
        })

    return rows


def tab_plain_title_summary(root: Path | None = None) -> Dict[str, object]:
    rows = tab_plain_title_matrix(root)
    issues = [row for row in rows if row.get("status") != "pass"]
    return {"phase": PHASE, "checks": len(rows), "issues": len(issues), "ready": not issues}


__all__ = [
    "PHASE",
    "FORBIDDEN_VISIBLE_PREFIXES",
    "FORBIDDEN_TOOLTIP_PREFIXES",
    "tab_plain_title_matrix",
    "tab_plain_title_summary",
]
