# -*- coding: utf-8 -*-
"""Phase452 Dialogs & Modal Windows Visual Unification contract.

Static/Qt-free guard.  Phase452 must centralize dialog/modal visual grammar via
runtime properties and theme/qss.py selectors while preserving accept/reject,
validation, activation, camera scanning, and message/toast behavior.
"""
from __future__ import annotations
from pathlib import Path

REQUIRED_BRAND_TOKENS = [
    "modal_visual_phase",
    "modal_surface_bg",
    "modal_shell_bg",
    "modal_shell_border",
    "modal_header_bg",
    "modal_header_text",
    "modal_body_bg",
    "modal_footer_bg",
    "modal_input_bg",
    "modal_table_header_bg",
    "modal_primary_bg",
    "modal_secondary_bg",
    "modal_danger_bg",
    "modal_warning_bg",
]

REQUIRED_QSS_MARKERS = [
    "Phase452: dialogs and modal windows visual unification",
    'QDialog[modalVisualPhase="452"]',
    'QMessageBox[modalVisualPhase="452"]',
    'visualRole="modal_shell"',
    'visualRole="modal_header"',
    'visualRole="modal_body"',
    'visualRole="modal_footer"',
    'visualRole="modal_button_box"',
    'visualRole="modal_title"',
    'visualRole="modal_help"',
    'visualRole="modal_status"',
    'visualRole="modal_input"',
    'visualRole="modal_table"',
    'visualRole="modal_primary_action"',
    'visualRole="modal_secondary_action"',
    'visualRole="modal_danger_action"',
    'visualRole="modal_close_action"',
]

REQUIRED_DIALOG_BRANDING_MARKERS = [
    "def apply_modal_visual_template",
    'root.setProperty("modalVisualPhase", "452")',
    'root.setProperty("visualWorkspaceType", "modal")',
    'root.setProperty("visualStyleSource", "dialogs_modal_windows_visual_unification")',
    '"modal_button_box"',
    '"modal_input"',
    '"modal_table"',
    '"modal_tabs"',
    '"modal_primary_action"',
    '"modal_danger_action"',
    'apply_modal_visual_template(dialog, role or "system")',
    'apply_modal_visual_template(box, role or "info")',
]

REQUIRED_EVENT_FILTER_MARKERS = [
    "class ModalVisualEventFilter",
    "install_modal_visual_event_filter",
    "QEvent.Show",
    "isinstance(obj, (QDialog, QMessageBox))",
    "apply_modal_visual_template",
    "brand_message_box",
]

REQUIRED_MAIN_MARKERS = [
    "install_modal_visual_event_filter(app)",
    "apply_modal_visual_template(dialog, role='network_settings')",
    "modalLocalStylesSuppressed",
    "set_visual_state(status, 'success'",
    "set_visual_state(status, 'danger'",
]

REQUIRED_FRAMELESS_MARKERS = [
    "modalLocalStylesSuppressed",
    "apply_branded_dialog(self, self.windowTitle(), role='frameless')",
    "normalize_dialog_buttons(self)",
]

REQUIRED_DIALOG_FILE_MARKERS = {
    "alrajhi_client/views/dialogs/change_password_dialog.py": [
        "apply_modal_visual_template(self, role='change_password')",
        "set_visual_state(self.strength_label",
        "visualRole', 'modal_title'",
        "visualRole', 'modal_help'",
        "user_service.change_password",
    ],
    "alrajhi_client/views/dialogs/module_activation_dialog.py": [
        "apply_branded_dialog(self, self.windowTitle(), role='module_activation')",
        "set_visual_state(self.status_label",
        "activate_feature",
        "check_feature_activation",
    ],
    "alrajhi_client/views/dialogs/barcode_camera_dialog.py": [
        "apply_modal_visual_template(self, role='barcode_camera')",
        "barcode_scanner_service.open_camera",
        "barcode_scanned.emit",
    ],
    "alrajhi_client/views/widgets/modern_ui.py": [
        "apply_modal_visual_template(dialog, role='modern')",
        "apply_branded_dialog(dialog, title, role='modern')",
    ],
}

FORBIDDEN_FRAMELESS_SNIPPETS = [
    "#BrandDialogFrame {",
    "background-color: {ThemeManager.get('bg_sidebar')}",
    "background-color: {ThemeManager.get('bg_panel')}",
    "font-weight: bold; font-size: 14px",
]


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def phase452_dialogs_modal_windows_visual_unification_summary(root: str | Path) -> dict:
    root = Path(root)
    details: list[str] = []
    checks = 0

    brand = _read(root, "alrajhi_client/theme/brand.py")
    for token in REQUIRED_BRAND_TOKENS:
        checks += 1
        if token not in brand:
            details.append(f"missing Phase452 modal brand token: {token}")
    checks += 1
    if "'modal_visual_phase': 452" not in brand:
        details.append("modal_visual_phase must be 452")

    qss = _read(root, "alrajhi_client/theme/qss.py")
    for marker in REQUIRED_QSS_MARKERS:
        checks += 1
        if marker not in qss:
            details.append(f"central QSS missing modal marker: {marker}")
    checks += 1
    if qss.find("Phase452: dialogs and modal windows visual unification") < qss.find("Phase451: settings workspace visual consolidation"):
        details.append("Phase452 modal QSS must come after Phase451 settings rules")

    branding = _read(root, "alrajhi_client/ui/dialog_branding.py")
    for marker in REQUIRED_DIALOG_BRANDING_MARKERS:
        checks += 1
        if marker not in branding:
            details.append(f"dialog branding missing Phase452 marker: {marker}")
    for marker in ("branded_question", "normalize_dialog_buttons", "dialog_action_role"):
        checks += 1
        if marker not in branding:
            details.append(f"dialog branding lost existing behavior marker: {marker}")

    event_filter = _read(root, "alrajhi_client/ui/modal_visual_event_filter.py")
    for marker in REQUIRED_EVENT_FILTER_MARKERS:
        checks += 1
        if marker not in event_filter:
            details.append(f"modal event filter missing marker: {marker}")

    main = _read(root, "alrajhi_client/main.py")
    for marker in REQUIRED_MAIN_MARKERS:
        checks += 1
        if marker not in main:
            details.append(f"main startup/network dialog missing marker: {marker}")
    for marker in ("install_non_blocking_message_boxes(app)", "ThemeManager.init_app(app)", "open_network_settings"):
        checks += 1
        if marker not in main:
            details.append(f"main lost critical non-visual marker: {marker}")

    frameless = _read(root, "alrajhi_client/views/frameless_dialog.py")
    for marker in REQUIRED_FRAMELESS_MARKERS:
        checks += 1
        if marker not in frameless:
            details.append(f"frameless dialog missing marker: {marker}")
    for snippet in FORBIDDEN_FRAMELESS_SNIPPETS:
        checks += 1
        if snippet in frameless:
            details.append(f"frameless dialog still contains local modal style snippet: {snippet}")

    for rel, markers in REQUIRED_DIALOG_FILE_MARKERS.items():
        text = _read(root, rel)
        for marker in markers:
            checks += 1
            if marker not in text:
                details.append(f"{rel} missing marker: {marker}")

    return {
        "ready": not details,
        "issues": len(details),
        "checks": checks,
        "details": details,
        "phase": 452,
    }


__all__ = ["phase452_dialogs_modal_windows_visual_unification_summary"]
