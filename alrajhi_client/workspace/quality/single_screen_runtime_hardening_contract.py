# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

REQUIRED_TOKENS = [
    "'single_screen_runtime_hardening_phase': 456",
    "SINGLE_SCREEN_RUNTIME_HARDENING_PHASE = 456",
    "def apply_single_screen_runtime_hardening",
    "apply_single_screen_runtime_hardening(root, policy.page_id, policy.workspace_type)",
    "apply_single_screen_runtime_hardening(self.main_frame, page_id='login', workspace_type='login')",
    "apply_single_screen_runtime_hardening(self, page_id='pos', workspace_type='operational')",
    "apply_single_screen_runtime_hardening(self.content_widget, page_id='invoice_dialog', workspace_type='document')",
    "apply_single_screen_runtime_hardening(self, page_id='material_editor', workspace_type='material')",
    "apply_single_screen_runtime_hardening(self, page_id='dashboard', workspace_type='dashboard')",
    "Phase456: Single-screen runtime hardening",
    "screenRebuildGuardSignature",
    "no business logic",
    "no DAO/API",
]


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def phase456_single_screen_runtime_hardening_summary(root: str | Path) -> dict:
    root = Path(root)
    files = {
        "brand": _read(root, "alrajhi_client/theme/brand.py"),
        "helper": _read(root, "alrajhi_client/ui/single_screen_runtime_hardening.py"),
        "runtime": _read(root, "alrajhi_client/ui/runtime_visual_polish.py"),
        "login": _read(root, "alrajhi_client/views/dialogs/login_dialog.py"),
        "pos": _read(root, "alrajhi_client/views/widgets/pos_widget.py"),
        "invoice": _read(root, "alrajhi_client/views/dialogs/invoice_dialog.py"),
        "material": _read(root, "alrajhi_client/features/items/item_editor_tab.py"),
        "dashboard": _read(root, "alrajhi_client/views/widgets/dashboard_widget.py"),
        "qss": _read(root, "alrajhi_client/theme/qss.py"),
        "doc": _read(root, "PHASE456_SINGLE_SCREEN_RUNTIME_HARDENING.md"),
    }
    blob = "\n".join(files.values())
    missing = [token for token in REQUIRED_TOKENS if token not in blob]
    forbidden = [
        "pos_service.checkout =",
        "UserSession.login =",
        "invoice_service.save =",
        "settings_service.save =",
        "def _do_login(self):\n        pass",
        "def save_item(self):\n        pass",
    ]
    forbidden_hits = [token for token in forbidden if token in blob]
    return {
        "phase": 456,
        "status": "pass" if not missing and not forbidden_hits else "fail",
        "checks": len(REQUIRED_TOKENS) + len(forbidden),
        "missing": missing,
        "forbidden_hits": forbidden_hits,
    }


__all__ = ["phase456_single_screen_runtime_hardening_summary"]
