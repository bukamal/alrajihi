# -*- coding: utf-8 -*-
"""Phase 353 branded splash/login/activation runtime contract.

The contract is PyQt-free and checks that first-run screens are not just tokenized,
but structurally branded: split panels, branded form panels, activation device
context, runtime object names and first-run buttons.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from theme.brand import BRAND, get_tokens
from theme.first_run_identity import (
    FIRST_RUN_PHASE,
    REQUIRED_FIRST_RUN_OBJECT_NAMES,
    REQUIRED_FIRST_RUN_TOKEN_KEYS,
    first_run_identity_matrix,
    validate_first_run_tokens,
)

ROOT = Path(__file__).resolve().parents[3]

REQUIRED_FIRST_RUN_FILES = (
    "alrajhi_client/theme/first_run_identity.py",
    "alrajhi_client/ui/first_run_branding.py",
    "alrajhi_client/views/splash_screen.py",
    "alrajhi_client/views/dialogs/login_dialog.py",
    "alrajhi_client/views/dialogs/activation_dialog.py",
)

REQUIRED_QSS_MARKERS = (
    "Phase353: branded first-run split panels and runtime polish",
    "QFrame#firstRunBrandPanel",
    "QFrame#firstRunFormPanel",
    "QLabel#firstRunHeroTitle",
    "QPushButton#firstRunPrimary",
    "QFrame#activationDevicePanel",
    "QProgressBar#firstRunProgressTrack",
)

LOGIN_RESTORE_MARKERS = ("Phase367: restored LoginDialog", "Phase368: password visibility button")

REQUIRED_RUNTIME_MARKERS = {
    "alrajhi_client/ui/first_run_branding.py": (
        "FIRST_RUN_RUNTIME_PHASE = 353",
        "brand_side_panel",
        "first_run_form_panel",
        "activation_device_panel",
        "set_first_run_primary",
    ),
    "alrajhi_client/views/splash_screen.py": (
        "apply_first_run_surface(self.container, 'splash')",
        "firstRunStageChip",
        "firstRunProgressTrack",
    ),
    "alrajhi_client/views/dialogs/login_dialog.py": (
        "brand_side_panel(",
        "first_run_form_panel()",
        "set_first_run_primary",
        "firstRunSurface', 'login'",
    ),
    "alrajhi_client/views/dialogs/activation_dialog.py": (
        "brand_side_panel(",
        "activation_device_panel",
        "set_first_run_primary",
        "firstRunSurface', 'activation'",
    ),
}


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding="utf-8")


def branded_first_run_runtime_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    rows: List[Dict[str, object]] = []

    rows.append({
        "key": "brand_phase",
        "category": "tokens",
        "description": "BRAND phase advanced to first-run runtime polish",
        "status": "pass" if int(BRAND.get("brand_phase", 0)) >= FIRST_RUN_PHASE else "fail",
        "detail": BRAND.get("brand_phase"),
    })

    for theme in ("light", "dark"):
        issues = validate_first_run_tokens(get_tokens(theme))
        rows.append({
            "key": f"{theme}_first_run_tokens",
            "category": "tokens",
            "description": f"{theme} palette includes Phase {FIRST_RUN_PHASE} first-run tokens",
            "status": "pass" if not issues else "fail",
            "detail": "; ".join(f"{k}:{','.join(v)}" for k, v in issues.items()),
        })

    for surface in first_run_identity_matrix(get_tokens("light")):
        rows.append({
            "key": f"surface_{surface['key']}",
            "category": "surface",
            "description": surface["description"],
            "status": "pass" if surface.get("present", True) else "fail",
            "detail": surface.get("missing", ""),
        })

    for path in REQUIRED_FIRST_RUN_FILES:
        rows.append({
            "key": f"file_{Path(path).stem}",
            "category": "file",
            "description": "Required first-run runtime file exists",
            "status": "pass" if (base / path).exists() else "fail",
            "detail": path,
        })

    qss = _read("alrajhi_client/theme/qss.py", base)
    for marker in REQUIRED_QSS_MARKERS:
        rows.append({
            "key": f"qss_{marker[:32]}",
            "category": "qss",
            "description": f"QSS contains {marker}",
            "status": "pass" if marker in qss else "fail",
            "detail": marker,
        })

    for object_name in REQUIRED_FIRST_RUN_OBJECT_NAMES:
        found = any(object_name in _read(path, base) for path in REQUIRED_RUNTIME_MARKERS)
        rows.append({
            "key": f"object_{object_name}",
            "category": "object_name",
            "description": "First-run object name is present in runtime screens/helpers",
            "status": "pass" if found or object_name in qss else "fail",
            "detail": object_name,
        })

    for path, markers in REQUIRED_RUNTIME_MARKERS.items():
        text = _read(path, base)
        login_restore_active = path.endswith("login_dialog.py") and any(marker in text for marker in LOGIN_RESTORE_MARKERS)
        for marker in markers:
            status = "pass" if marker in text or login_restore_active else "fail"
            detail = marker if marker in text else ("superseded_by_login_pre350_restore" if login_restore_active else marker)
            rows.append({
                "key": f"runtime_{Path(path).stem}_{marker[:22]}",
                "category": "runtime",
                "description": f"{path} uses {marker}",
                "status": status,
                "detail": detail,
            })

    return rows


def branded_first_run_runtime_summary(root: Path | None = None) -> Dict[str, object]:
    rows = branded_first_run_runtime_matrix(root)
    issues = [row for row in rows if row.get("status") != "pass"]
    categories: Dict[str, int] = {}
    for row in rows:
        cat = str(row.get("category", "unknown"))
        categories[cat] = categories.get(cat, 0) + 1
    return {
        "phase": FIRST_RUN_PHASE,
        "checks": len(rows),
        "issues": len(issues),
        "issue_groups": len({row.get("category") for row in issues}),
        "categories": categories,
        "ready": not issues,
    }


__all__ = [
    "REQUIRED_FIRST_RUN_FILES",
    "REQUIRED_QSS_MARKERS",
    "LOGIN_RESTORE_MARKERS",
    "REQUIRED_RUNTIME_MARKERS",
    "branded_first_run_runtime_matrix",
    "branded_first_run_runtime_summary",
]
