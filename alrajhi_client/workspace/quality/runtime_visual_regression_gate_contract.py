# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

_REQUIRED_STRINGS = [
    "'runtime_visual_regression_gate_phase': 457",
    "'runtime_visual_regression_required_chain': '453>454>455>456>457'",
    "def apply_runtime_visual_regression_gate",
    "RUNTIME_VISUAL_REGRESSION_GATE_PHASE = 457",
    "runtimeVisualRegressionGatePhase",
    "visualRegressionGuardSignature",
    "visualRegressionGateStatus",
    "apply_runtime_visual_regression_gate(root, policy.page_id, policy.workspace_type)",
    "apply_runtime_visual_regression_gate(self.main_frame, page_id='login', workspace_type='login')",
    "apply_runtime_visual_regression_gate(self, page_id='pos', workspace_type='operational')",
    "apply_runtime_visual_regression_gate(self.content_widget, page_id='invoice_dialog', workspace_type='document')",
    "apply_runtime_visual_regression_gate(self, page_id='material_editor', workspace_type='material')",
    "apply_runtime_visual_regression_gate(self, page_id='dashboard', workspace_type='dashboard')",
    "QWidget[runtimeVisualRegressionGatePhase=\"457\"]",
]

_CRITICAL_FILES = [
    "alrajhi_client/theme/brand.py",
    "alrajhi_client/theme/qss.py",
    "alrajhi_client/ui/runtime_visual_regression_gate.py",
    "alrajhi_client/ui/runtime_visual_polish.py",
    "alrajhi_client/views/dialogs/login_dialog.py",
    "alrajhi_client/views/widgets/pos_widget.py",
    "alrajhi_client/views/dialogs/invoice_dialog.py",
    "alrajhi_client/features/items/item_editor_tab.py",
    "alrajhi_client/views/widgets/dashboard_widget.py",
]


def _read(root: str | Path, relative: str) -> str:
    return (Path(root) / relative).read_text(encoding="utf-8")


def phase457_runtime_visual_regression_gate_summary(root: str | Path) -> dict:
    root = Path(root)
    files = {path: _read(root, path) for path in _CRITICAL_FILES}
    combined = "\n".join(files.values())
    details: list[str] = []

    for required in _REQUIRED_STRINGS:
        if required not in combined:
            details.append(f"missing required marker: {required}")

    helper = files["alrajhi_client/ui/runtime_visual_regression_gate.py"]
    for phrase in ["no business logic", "no DAO/API", "no printing", "no Enter-grid navigation"]:
        if phrase not in helper:
            details.append(f"helper must declare visual-only boundary: {phrase}")
    for family in ["login", "dashboard", "pos", "invoice", "material"]:
        if family not in helper:
            details.append(f"helper must include critical family: {family}")

    polish = files["alrajhi_client/ui/runtime_visual_polish.py"]
    expected_order = [
        "apply_windows_runtime_visual_acceptance(root, policy.page_id, policy.workspace_type)",
        "apply_runtime_layout_reconstruction(root, policy.page_id, policy.workspace_type)",
        "apply_targeted_screen_rebuild(root, policy.page_id, policy.workspace_type)",
        "apply_single_screen_runtime_hardening(root, policy.page_id, policy.workspace_type)",
        "apply_runtime_visual_regression_gate(root, policy.page_id, policy.workspace_type)",
    ]
    positions = [polish.find(item) for item in expected_order]
    if any(pos < 0 for pos in positions) or positions != sorted(positions):
        details.append("runtime visual passes must run in Phase453 -> 454 -> 455 -> 456 -> 457 order")

    checks = len(_REQUIRED_STRINGS) + 4 + 5 + 1
    return {
        "phase": 457,
        "name": "Runtime Visual Regression Gate",
        "status": "pass" if not details else "fail",
        "checks": checks,
        "details": details,
    }


__all__ = ["phase457_runtime_visual_regression_gate_summary"]
