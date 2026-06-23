# -*- coding: utf-8 -*-
"""Phase 356 guard contract: branded dialogs and system windows.

Validates that modal/system surfaces are not visually independent islands:
frameless dialogs, modern dialogs, message boxes, toast notifications and
specialized pickers all expose common object names/properties and QSS tokens.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from theme.brand import BRAND, get_tokens
from theme.dialog_identity import (
    DIALOG_IDENTITY_PHASE,
    REQUIRED_DIALOG_OBJECT_MARKERS,
    REQUIRED_DIALOG_QSS_MARKERS,
    dialog_identity_matrix,
    validate_dialog_identity_tokens,
)

ROOT = Path(__file__).resolve().parents[3]

REQUIRED_DIALOG_RUNTIME_FILES = (
    "alrajhi_client/theme/dialog_identity.py",
    "alrajhi_client/theme/brand.py",
    "alrajhi_client/theme/qss.py",
    "alrajhi_client/ui/dialog_branding.py",
    "alrajhi_client/views/frameless_dialog.py",
    "alrajhi_client/views/centered_dialog.py",
    "alrajhi_client/views/widgets/modern_ui.py",
    "alrajhi_client/views/widgets/toast_notification.py",
    "alrajhi_client/views/dialogs/column_contract_customizer.py",
)

REQUIRED_DIALOG_RUNTIME_MARKERS = {
    "alrajhi_client/ui/dialog_branding.py": (
        "apply_branded_dialog",
        "normalize_dialog_buttons",
        "dialogActionRole",
        "brand_message_box",
        "branded_question",
    ),
    "alrajhi_client/views/frameless_dialog.py": (
        "BrandDialogFrame",
        "BrandDialogHeader",
        "BrandDialogTitle",
        "apply_branded_dialog",
        "dialogActionRole",
    ),
    "alrajhi_client/views/centered_dialog.py": (
        "branded_question",
        "تغييرات غير محفوظة",
    ),
    "alrajhi_client/views/widgets/modern_ui.py": (
        "BrandDialogHeaderCard",
        "apply_branded_dialog(dialog",
        "normalize_dialog_buttons(dialog)",
    ),
    "alrajhi_client/views/widgets/toast_notification.py": (
        "toastType",
        "toast_success_bg",
        "toast_min_width",
    ),
    "alrajhi_client/views/dialogs/column_contract_customizer.py": (
        "brandDialog",
        "dialogKind",
        "column_customizer",
        "apply_branded_dialog",
    ),
}


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding="utf-8")


def branded_dialogs_system_windows_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    rows: List[Dict[str, object]] = []

    rows.append({
        "key": "brand_phase",
        "category": "tokens",
        "description": "BRAND phase advanced to branded dialogs/system windows",
        "status": "pass" if int(BRAND.get("brand_phase", 0)) >= DIALOG_IDENTITY_PHASE else "fail",
        "detail": BRAND.get("brand_phase"),
    })

    for theme in ("light", "dark"):
        issues = validate_dialog_identity_tokens(get_tokens(theme))
        rows.append({
            "key": f"{theme}_dialog_tokens",
            "category": "tokens",
            "description": f"{theme} palette includes Phase {DIALOG_IDENTITY_PHASE} dialog tokens",
            "status": "pass" if not issues else "fail",
            "detail": "; ".join(f"{k}:{','.join(v)}" for k, v in issues.items()),
        })

    for item in dialog_identity_matrix(get_tokens("light")):
        rows.append({
            "key": f"dialog_identity_{item['kind']}_{item['key']}",
            "category": str(item["kind"]),
            "description": item["description"],
            "status": "pass" if item.get("present", True) else "fail",
            "detail": item.get("marker", item["key"]),
        })

    for path in REQUIRED_DIALOG_RUNTIME_FILES:
        rows.append({
            "key": f"file_{Path(path).stem}",
            "category": "file",
            "description": "Required branded dialog runtime file exists",
            "status": "pass" if (base / path).exists() else "fail",
            "detail": path,
        })

    qss = _read("alrajhi_client/theme/qss.py", base)
    for marker in REQUIRED_DIALOG_QSS_MARKERS:
        rows.append({
            "key": f"qss_{marker[:42]}",
            "category": "qss",
            "description": f"QSS contains {marker}",
            "status": "pass" if marker in qss else "fail",
            "detail": marker,
        })

    searchable_paths = tuple(REQUIRED_DIALOG_RUNTIME_MARKERS.keys()) + ("alrajhi_client/theme/qss.py",)
    for marker in REQUIRED_DIALOG_OBJECT_MARKERS:
        found = any(marker.marker in _read(path, base) for path in searchable_paths)
        rows.append({
            "key": f"object_{marker.key}",
            "category": marker.category,
            "description": marker.description,
            "status": "pass" if found else "fail",
            "detail": marker.marker,
        })

    for path, markers in REQUIRED_DIALOG_RUNTIME_MARKERS.items():
        text = _read(path, base)
        for marker in markers:
            rows.append({
                "key": f"runtime_{Path(path).stem}_{marker[:28]}",
                "category": "runtime",
                "description": f"{path} uses {marker}",
                "status": "pass" if marker in text else "fail",
                "detail": marker,
            })

    return rows


def branded_dialogs_system_windows_summary(root: Path | None = None) -> Dict[str, object]:
    rows = branded_dialogs_system_windows_matrix(root)
    issues = [row for row in rows if row.get("status") != "pass"]
    categories: Dict[str, int] = {}
    for row in rows:
        cat = str(row.get("category", "unknown"))
        categories[cat] = categories.get(cat, 0) + 1
    return {
        "phase": DIALOG_IDENTITY_PHASE,
        "checks": len(rows),
        "issues": len(issues),
        "issue_groups": len({row.get("category") for row in issues}),
        "categories": categories,
        "ready": not issues,
    }


__all__ = [
    "REQUIRED_DIALOG_RUNTIME_FILES",
    "REQUIRED_DIALOG_RUNTIME_MARKERS",
    "branded_dialogs_system_windows_matrix",
    "branded_dialogs_system_windows_summary",
]
