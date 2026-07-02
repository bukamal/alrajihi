# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

REQUIRED_TOKENS = [
    "'targeted_screen_rebuild_phase': 455",
    "TARGETED_SCREEN_REBUILD_PHASE = 455",
    "def apply_targeted_screen_rebuild",
    "apply_targeted_screen_rebuild(root, policy.page_id, policy.workspace_type)",
    "apply_targeted_screen_rebuild(self.main_frame, page_id='login', workspace_type='login')",
    "apply_targeted_screen_rebuild(self, page_id='pos', workspace_type='operational')",
    "apply_targeted_screen_rebuild(self.content_widget, page_id='invoice_dialog', workspace_type='document')",
    "apply_targeted_screen_rebuild(self, page_id='material_editor', workspace_type='material')",
    "Phase455: Targeted screen rebuild",
]


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def phase455_targeted_screen_rebuild_summary(root: str | Path) -> dict:
    root = Path(root)
    files = {
        "brand": _read(root, "alrajhi_client/theme/brand.py"),
        "helper": _read(root, "alrajhi_client/ui/targeted_screen_rebuild.py"),
        "runtime": _read(root, "alrajhi_client/ui/runtime_visual_polish.py"),
        "login": _read(root, "alrajhi_client/views/dialogs/login_dialog.py"),
        "pos": _read(root, "alrajhi_client/views/widgets/pos_widget.py"),
        "invoice": _read(root, "alrajhi_client/views/dialogs/invoice_dialog.py"),
        "material": _read(root, "alrajhi_client/features/items/item_editor_tab.py"),
        "dashboard": _read(root, "alrajhi_client/views/widgets/dashboard_widget.py"),
        "qss": _read(root, "alrajhi_client/theme/qss.py"),
        "doc": _read(root, "PHASE455_TARGETED_SCREEN_REBUILD.md"),
    }
    blob = "\n".join(files.values())
    missing = [token for token in REQUIRED_TOKENS if token not in blob]
    forbidden = [
        "pos_service.checkout =",
        "def scan_entered_barcode(self):\n        pass",
        "def on_save(self):\n        pass",
        "UserSession.login =",
    ]
    forbidden_hits = [token for token in forbidden if token in blob]
    return {
        "phase": 455,
        "status": "pass" if not missing and not forbidden_hits else "fail",
        "checks": len(REQUIRED_TOKENS) + len(forbidden),
        "missing": missing,
        "forbidden_hits": forbidden_hits,
    }


__all__ = ["phase455_targeted_screen_rebuild_summary"]
