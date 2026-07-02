# -*- coding: utf-8 -*-
"""Phase454 Runtime Layout Reconstruction static contract."""
from __future__ import annotations
from pathlib import Path

REQUIRED_BRAND_TOKENS = [
    "runtime_layout_reconstruction_phase",
    "login_runtime_reconstruction_phase",
    "shell_density_reconstruction_phase",
    "pos_runtime_layout_reconstruction_phase",
    "invoice_runtime_layout_reconstruction_phase",
    "material_runtime_layout_reconstruction_phase",
]

REQUIRED_HELPER_MARKERS = [
    "RUNTIME_LAYOUT_RECONSTRUCTION_PHASE = 454",
    "def apply_runtime_layout_reconstruction",
    'root.setProperty("runtimeLayoutReconstructionPhase", RUNTIME_LAYOUT_RECONSTRUCTION_PHASE)',
    'child.setProperty("runtimeLayoutReconstructionPhase", RUNTIME_LAYOUT_RECONSTRUCTION_PHASE)',
    'child.setProperty("runtimeCommandWeight", _button_weight(child, family))',
    'child.setProperty("runtimeLayoutTable", "major_grid"',
    "QTimer.singleShot(160",
]

REQUIRED_INTEGRATION_MARKERS = [
    "from ui.runtime_layout_reconstruction import apply_runtime_layout_reconstruction",
    "apply_runtime_layout_reconstruction(root, policy.page_id, policy.workspace_type)",
]

REQUIRED_LOGIN_MARKERS = [
    "loginRuntimeReconstructionPhase",
    "login_runtime_reconstructed_outer_margin",
    "login_mode_chip_compact",
    "apply_runtime_layout_reconstruction(self.main_frame, page_id='login', workspace_type='login')",
]

REQUIRED_POS_MARKERS = [
    "POSRuntimeTopTools",
    "POSRuntimeContextBar",
    "POSRuntimeScanBar",
    "posRuntimeLayoutReconstructionPhase",
    "pos_runtime_reconstructed_scan_height",
    "posPaymentLayout",
]

REQUIRED_INVOICE_MARKERS = [
    "invoiceRuntimeLayoutReconstructionPhase",
    "InvoiceRuntimeLinesPanel",
    "InvoiceRuntimeSearchInput",
    "invoice_quick_entry",
    "invoice_financial_summary",
    "invoice_runtime_reconstructed_table_min_height",
    "apply_runtime_layout_reconstruction(self.content_widget, page_id='invoice_dialog', workspace_type='document')",
]

REQUIRED_MATERIAL_MARKERS = [
    "materialRuntimeLayoutReconstructionPhase",
    "material_cards_rebalanced_splitter",
    "material_runtime_card_min_width",
    "material_runtime_action_footer_height",
    "apply_runtime_layout_reconstruction(self, page_id='material_editor', workspace_type='material')",
]

REQUIRED_QSS_MARKERS = [
    "Phase454: Runtime layout reconstruction",
    'QFrame#UnifiedActionBar[shellDensityReconstructionPhase=\"454\"]',
    'QFrame#POSRuntimeScanBar QLineEdit[visualRole=\"operational_scan_input\"]',
    'QWidget[invoiceRuntimeLayoutReconstructionPhase=\"454\"] QLineEdit#InvoiceRuntimeSearchInput',
    'QWidget[materialRuntimeLayoutReconstructionPhase=\"454\"] QFrame#MaterialEditorActionBar',
]


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def phase454_runtime_layout_reconstruction_summary(root: str | Path) -> dict:
    root = Path(root)
    details: list[str] = []
    checks = 0

    files = {
        "brand": _read(root, "alrajhi_client/theme/brand.py"),
        "helper": _read(root, "alrajhi_client/ui/runtime_layout_reconstruction.py"),
        "polish": _read(root, "alrajhi_client/ui/runtime_visual_polish.py"),
        "login": _read(root, "alrajhi_client/views/dialogs/login_dialog.py"),
        "pos": _read(root, "alrajhi_client/views/widgets/pos_widget.py"),
        "invoice": _read(root, "alrajhi_client/views/dialogs/invoice_dialog.py"),
        "material": _read(root, "alrajhi_client/features/items/item_editor_tab.py"),
        "qss": _read(root, "alrajhi_client/theme/qss.py"),
        "action_bar": _read(root, "alrajhi_client/shell/unified_action_bar.py"),
    }

    for marker in REQUIRED_BRAND_TOKENS:
        checks += 1
        if marker not in files["brand"]:
            details.append(f"missing Phase454 brand token: {marker}")
    checks += 1
    if "'runtime_layout_reconstruction_phase': 454" not in files["brand"]:
        details.append("runtime_layout_reconstruction_phase must be 454")

    for marker in REQUIRED_HELPER_MARKERS:
        checks += 1
        if marker not in files["helper"]:
            details.append(f"helper missing marker: {marker}")

    for marker in REQUIRED_INTEGRATION_MARKERS:
        checks += 1
        if marker not in files["polish"] and marker not in files["login"] and marker not in files["pos"] and marker not in files["invoice"] and marker not in files["material"]:
            details.append(f"integration missing marker: {marker}")

    for marker in REQUIRED_LOGIN_MARKERS:
        checks += 1
        if marker not in files["login"]:
            details.append(f"login missing marker: {marker}")

    for marker in REQUIRED_POS_MARKERS:
        checks += 1
        if marker not in files["pos"]:
            details.append(f"POS missing marker: {marker}")

    for marker in REQUIRED_INVOICE_MARKERS:
        checks += 1
        if marker not in files["invoice"]:
            details.append(f"invoice missing marker: {marker}")

    for marker in REQUIRED_MATERIAL_MARKERS:
        checks += 1
        if marker not in files["material"]:
            details.append(f"material missing marker: {marker}")

    for marker in REQUIRED_QSS_MARKERS:
        checks += 1
        if marker not in files["qss"]:
            details.append(f"QSS missing marker: {marker}")
    checks += 1
    if files["qss"].find("Phase454: Runtime layout reconstruction") < files["qss"].find("Phase453: Windows runtime visual acceptance corrections"):
        details.append("Phase454 QSS must come after Phase453 runtime visual acceptance rules")

    checks += 1
    if "shellDensityReconstructionPhase" not in files["action_bar"]:
        details.append("unified action bar missing shellDensityReconstructionPhase")

    return {"ready": not details, "issues": len(details), "checks": checks, "details": details, "phase": 454}


__all__ = ["phase454_runtime_layout_reconstruction_summary"]
