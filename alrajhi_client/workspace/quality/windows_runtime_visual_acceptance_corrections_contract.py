# -*- coding: utf-8 -*-
"""Phase453 Windows Runtime Visual Acceptance Corrections contract.

Static/Qt-free guard. Phase453 is based on actual Windows runtime screenshots:
Fusion style enforcement, post-lazy runtime repolish, Arabic label cleanup,
Login/Shell/POS/document/material runtime visual selectors, and suppression of
legacy invoice/POS local stylesheet fragments.
"""
from __future__ import annotations
from pathlib import Path

REQUIRED_BRAND_TOKENS = [
    "windows_runtime_visual_acceptance_phase",
    "windows_runtime_force_fusion",
    "windows_runtime_qt_style",
    "runtime_control_height",
    "runtime_table_header_bg",
    "runtime_current_cell_bg",
    "login_runtime_visual_phase",
    "shell_density_visual_phase",
    "pos_runtime_acceptance_phase",
    "document_runtime_acceptance_phase",
    "material_editor_runtime_acceptance_phase",
]

REQUIRED_RUNTIME_HELPER_MARKERS = [
    "WINDOWS_RUNTIME_VISUAL_ACCEPTANCE_PHASE = 453",
    "def install_windows_runtime_visual_acceptance",
    'app.setStyle(str(BRAND.get("windows_runtime_qt_style", "Fusion")))',
    "def apply_windows_runtime_visual_acceptance",
    'root.setProperty("windowsRuntimeVisualAcceptancePhase", WINDOWS_RUNTIME_VISUAL_ACCEPTANCE_PHASE)',
    '"row density": "كثافة الصفوف"',
    '"Filters": "الفلاتر"',
    '"Fit": "ملاءمة العرض"',
    '"Restaurant table Takeaway / session": "طلب مطعم خارجي / جلسة"',
    "QTimer.singleShot(120",
]

REQUIRED_MAIN_MARKERS = [
    "from ui.windows_runtime_visual_acceptance import install_windows_runtime_visual_acceptance",
    "install_windows_runtime_visual_acceptance(app)",
    "ThemeManager.init_app(app)",
]

REQUIRED_RUNTIME_POLISH_MARKERS = [
    "from ui.windows_runtime_visual_acceptance import apply_windows_runtime_visual_acceptance",
    "apply_windows_runtime_visual_acceptance(root, policy.page_id, policy.workspace_type)",
    "Phase453: final Windows screenshot-facing acceptance pass",
]

REQUIRED_QSS_MARKERS = [
    "Phase453: Windows runtime visual acceptance corrections",
    'QWidget[windowsRuntimeVisualAcceptancePhase="453"] QLineEdit',
    'QWidget[windowsRuntimeVisualAcceptancePhase="453"] QComboBox::drop-down',
    'QWidget[windowsRuntimeVisualAcceptancePhase="453"] QSpinBox::up-button',
    'QWidget[windowsRuntimeVisualAcceptancePhase="453"] QHeaderView::section',
    'QFrame#loginCard[loginRuntimeVisualPhase="453"]',
    'QLabel[visualRole="operational_metric_value"]',
    'QWidget[visualRole="material_editor"][windowsRuntimeVisualAcceptancePhase="453"] QGroupBox[visualRole="material_form_card"]',
]

REQUIRED_DOCUMENT_POLICY_MARKERS = [
    "def _force_visual_role",
    'widget.setProperty("windowsRuntimeVisualAcceptancePhase", 453)',
    '"HeaderCard"',
    '"ActionCard"',
    '"RightPanel"',
    '"TotalsCard"',
    '_force_visual_role(child, "document_header")',
    '_force_visual_role(child, "document_card")',
    '_force_visual_role(child, "document_summary")',
    '_force_visual_role(child, "document_action_bar")',
]

REQUIRED_INVOICE_MARKERS = [
    "documentLocalStylesSuppressed",
    "apply_document_layout_policy(self, kind='tabular_document'",
    "self.setStyleSheet('')",
    "separator.setProperty('visualRole', 'document_separator')",
]

FORBIDDEN_INVOICE_MARKERS = [
    "QDialog {{ background:",
    "QPushButton#danger {{ background:",
    "separator.setStyleSheet(\"background-color: #e2e8f0;\")",
]

REQUIRED_POS_MARKERS = [
    "windowsRuntimeVisualAcceptancePhase",
    "operational_metric_value",
    "metricRuntimeStyle",
    "metricTone",
]

FORBIDDEN_POS_MARKERS = [
    "ThemeManager.get('primary')",
    "ThemeManager.get('success')",
    "ThemeManager.get('danger')",
]

REQUIRED_MATERIAL_MARKERS = [
    "windowsRuntimeVisualAcceptancePhase",
    "document_primary_action",
    "document_danger_action",
    "body.setStretchFactor(0, 4)",
    "body.setStretchFactor(1, 5)",
]


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def phase453_windows_runtime_visual_acceptance_corrections_summary(root: str | Path) -> dict:
    root = Path(root)
    details: list[str] = []
    checks = 0

    brand = _read(root, "alrajhi_client/theme/brand.py")
    for token in REQUIRED_BRAND_TOKENS:
        checks += 1
        if token not in brand:
            details.append(f"missing Phase453 brand token: {token}")
    checks += 1
    if "'windows_runtime_visual_acceptance_phase': 453" not in brand:
        details.append("windows_runtime_visual_acceptance_phase must be 453")

    helper = _read(root, "alrajhi_client/ui/windows_runtime_visual_acceptance.py")
    for marker in REQUIRED_RUNTIME_HELPER_MARKERS:
        checks += 1
        if marker not in helper:
            details.append(f"runtime helper missing marker: {marker}")

    main = _read(root, "alrajhi_client/main.py")
    for marker in REQUIRED_MAIN_MARKERS:
        checks += 1
        if marker not in main:
            details.append(f"main missing runtime acceptance marker: {marker}")

    polish = _read(root, "alrajhi_client/ui/runtime_visual_polish.py")
    for marker in REQUIRED_RUNTIME_POLISH_MARKERS:
        checks += 1
        if marker not in polish:
            details.append(f"runtime polish missing marker: {marker}")

    qss = _read(root, "alrajhi_client/theme/qss.py")
    for marker in REQUIRED_QSS_MARKERS:
        checks += 1
        if marker not in qss:
            details.append(f"central QSS missing Phase453 marker: {marker}")
    checks += 1
    if qss.find("Phase453: Windows runtime visual acceptance corrections") < qss.find("Phase452: dialogs and modal windows visual unification"):
        details.append("Phase453 QSS must come after Phase452 modal rules")

    doc_policy = _read(root, "alrajhi_client/workspace/documents/document_layout_policy.py")
    for marker in REQUIRED_DOCUMENT_POLICY_MARKERS:
        checks += 1
        if marker not in doc_policy:
            details.append(f"document layout policy missing marker: {marker}")

    invoice = _read(root, "alrajhi_client/views/dialogs/invoice_dialog.py")
    for marker in REQUIRED_INVOICE_MARKERS:
        checks += 1
        if marker not in invoice:
            details.append(f"invoice dialog missing marker: {marker}")
    for marker in FORBIDDEN_INVOICE_MARKERS:
        checks += 1
        if marker in invoice:
            details.append(f"invoice dialog still contains local style marker: {marker}")

    pos_payment = _read(root, "alrajhi_client/features/pos/pos_payment_shell.py")
    pos_widget = _read(root, "alrajhi_client/views/widgets/pos_widget.py")
    pos_combined = pos_payment + "\n" + pos_widget
    for marker in REQUIRED_POS_MARKERS:
        checks += 1
        if marker not in pos_combined:
            details.append(f"POS runtime visual marker missing: {marker}")
    for marker in FORBIDDEN_POS_MARKERS:
        checks += 1
        if marker in pos_payment:
            details.append(f"POS payment shell still contains local ThemeManager style marker: {marker}")

    material = _read(root, "alrajhi_client/features/items/item_editor_tab.py")
    for marker in REQUIRED_MATERIAL_MARKERS:
        checks += 1
        if marker not in material:
            details.append(f"material editor missing marker: {marker}")

    return {
        "ready": not details,
        "issues": len(details),
        "checks": checks,
        "details": details,
        "phase": 453,
    }


__all__ = ["phase453_windows_runtime_visual_acceptance_corrections_summary"]
