# -*- coding: utf-8 -*-
"""Phase 356: branded dialogs and system-window identity contract.

This module is intentionally PyQt-free.  It describes the visual contract for
modal dialogs, system windows, confirmation prompts, picker dialogs and toast
notifications so guards can validate the identity layer without launching Qt.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence

DIALOG_IDENTITY_PHASE = 356


@dataclass(frozen=True)
class DialogTokenSpec:
    key: str
    description: str


@dataclass(frozen=True)
class DialogObjectMarker:
    key: str
    marker: str
    category: str
    description: str


REQUIRED_DIALOG_TOKEN_KEYS: Sequence[str] = (
    "dialog_bg",
    "dialog_header_bg",
    "dialog_footer_bg",
    "dialog_button_bg",
    "dialog_title_text",
    "dialog_subtitle_text",
    "dialog_accent_line",
    "dialog_primary_bg",
    "dialog_secondary_bg",
    "dialog_close_bg",
    "dialog_warning_bg",
    "dialog_danger_bg",
    "dialog_success_bg",
    "dialog_overlay_bg",
    "toast_success_bg",
    "toast_info_bg",
    "toast_warning_bg",
    "toast_error_bg",
)

DIALOG_TOKEN_SPECS: Sequence[DialogTokenSpec] = (
    DialogTokenSpec("dialog_bg", "dialog body surface"),
    DialogTokenSpec("dialog_header_bg", "dialog branded header surface"),
    DialogTokenSpec("dialog_footer_bg", "dialog footer/action surface"),
    DialogTokenSpec("dialog_button_bg", "neutral dialog button surface"),
    DialogTokenSpec("dialog_title_text", "dialog title foreground"),
    DialogTokenSpec("dialog_subtitle_text", "dialog subtitle foreground"),
    DialogTokenSpec("dialog_accent_line", "dialog accent/identity separator"),
    DialogTokenSpec("dialog_primary_bg", "primary dialog command surface"),
    DialogTokenSpec("dialog_secondary_bg", "secondary dialog command surface"),
    DialogTokenSpec("dialog_close_bg", "safe close/cancel command surface"),
    DialogTokenSpec("dialog_warning_bg", "warning prompt surface"),
    DialogTokenSpec("dialog_danger_bg", "danger prompt surface"),
    DialogTokenSpec("dialog_success_bg", "success prompt surface"),
    DialogTokenSpec("dialog_overlay_bg", "modal overlay/outer shell surface"),
    DialogTokenSpec("toast_success_bg", "success toast background"),
    DialogTokenSpec("toast_info_bg", "informational toast background"),
    DialogTokenSpec("toast_warning_bg", "warning toast background"),
    DialogTokenSpec("toast_error_bg", "error toast background"),
)

REQUIRED_DIALOG_QSS_MARKERS: Sequence[str] = (
    "Phase356: branded dialogs and system windows",
    "QDialog[brandDialog=\"true\"]",
    "QFrame#BrandDialogFrame",
    "QFrame#BrandDialogHeader",
    "QWidget[dialogSurface=\"body\"]",
    "QWidget[dialogSurface=\"footer\"]",
    "QPushButton[dialogActionRole=\"primary\"]",
    "QPushButton[dialogActionRole=\"secondary\"]",
    "QPushButton[dialogActionRole=\"danger\"]",
    "QMessageBox QLabel",
    "QFrame#ToastNotification",
)

REQUIRED_DIALOG_OBJECT_MARKERS: Sequence[DialogObjectMarker] = (
    DialogObjectMarker("branded_runtime_helper", "apply_branded_dialog", "runtime", "central branded dialog applicator"),
    DialogObjectMarker("dialog_button_normalizer", "normalize_dialog_buttons", "runtime", "shared button role normalization"),
    DialogObjectMarker("message_box_runtime", "brand_message_box", "runtime", "message-box branding entry point"),
    DialogObjectMarker("frameless_frame", "BrandDialogFrame", "frameless", "frameless dialogs use branded frame object"),
    DialogObjectMarker("frameless_header", "BrandDialogHeader", "frameless", "frameless dialogs use branded header object"),
    DialogObjectMarker("frameless_title", "BrandDialogTitle", "frameless", "frameless dialogs expose branded title object"),
    DialogObjectMarker("modern_dialog_hook", "apply_branded_dialog(dialog", "modern", "legacy modern dialog helper delegates to brand layer"),
    DialogObjectMarker("column_customizer_hook", "brandDialog", "customizer", "column customizer participates in dialog identity"),
    DialogObjectMarker("toast_branding", "toastType", "toast", "toast notification exposes semantic type to QSS"),
)


def validate_dialog_identity_tokens(tokens: Mapping[str, str]) -> Dict[str, List[str]]:
    issues: Dict[str, List[str]] = {}
    for key in REQUIRED_DIALOG_TOKEN_KEYS:
        value = str(tokens.get(key, "") or "").strip()
        if not value:
            issues.setdefault("missing_dialog_tokens", []).append(key)
    return issues


def dialog_identity_matrix(tokens: Mapping[str, str]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for spec in DIALOG_TOKEN_SPECS:
        value = str(tokens.get(spec.key, "") or "").strip()
        rows.append({
            "kind": "token",
            "key": spec.key,
            "description": spec.description,
            "present": bool(value),
            "value": value,
        })
    for marker in REQUIRED_DIALOG_OBJECT_MARKERS:
        rows.append({
            "kind": marker.category,
            "key": marker.key,
            "description": marker.description,
            "present": True,
            "marker": marker.marker,
        })
    return rows


__all__ = [
    "DIALOG_IDENTITY_PHASE",
    "DialogTokenSpec",
    "DialogObjectMarker",
    "DIALOG_TOKEN_SPECS",
    "REQUIRED_DIALOG_TOKEN_KEYS",
    "REQUIRED_DIALOG_QSS_MARKERS",
    "REQUIRED_DIALOG_OBJECT_MARKERS",
    "dialog_identity_matrix",
    "validate_dialog_identity_tokens",
]
