# -*- coding: utf-8 -*-
"""Runtime helpers for Phase 356 branded dialogs and system windows.

The helpers are deliberately cosmetic: they attach object names and dynamic
properties consumed by the global QSS.  They do not change business validation,
persistence, or tab lifecycle behavior.
"""
from __future__ import annotations

from typing import Iterable

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractButton,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QLabel,
    QMessageBox,
    QPushButton,
    QWidget,
)

from i18n import translate
from theme.brand import BRAND
from theme_manager import ThemeManager

PRIMARY_HINTS = ("حفظ", "موافق", "اعتماد", "تفعيل", "طباعة", "دخول", "save", "ok", "apply", "activate", "print", "login")
DANGER_HINTS = ("حذف", "إلغاء المستند", "تجاهل", "delete", "remove", "discard")
CLOSE_HINTS = ("إغلاق", "إلغاء", "خروج", "close", "cancel", "exit")


def _button_text(button: QAbstractButton) -> str:
    try:
        return str(button.text() or "").replace("&", "").strip().lower()
    except Exception:
        return ""


def _contains_any(text: str, hints: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(str(hint).lower() in lowered for hint in hints)


def dialog_action_role(button: QAbstractButton) -> str:
    """Return the visual role for a dialog command button."""
    text = _button_text(button)
    explicit = str(button.property("dialogActionRole") or "").strip()
    if explicit:
        return explicit
    object_name = str(button.objectName() or "").lower()
    if "danger" in object_name or _contains_any(text, DANGER_HINTS):
        return "danger"
    if "primary" in object_name or _contains_any(text, PRIMARY_HINTS):
        return "primary"
    if "close" in object_name or "cancel" in object_name or _contains_any(text, CLOSE_HINTS):
        return "close"
    return "secondary"


def normalize_dialog_buttons(root: QWidget) -> None:
    """Attach semantic visual roles to buttons in any dialog-like widget."""
    for button_box in root.findChildren(QDialogButtonBox):
        button_box.setProperty("dialogSurface", "footer")
        for button in button_box.buttons():
            button.setProperty("dialogActionRole", dialog_action_role(button))
            try:
                button.setMinimumHeight(BRAND.get("dialog_action_min_height", 42))
                button.setMinimumWidth(BRAND.get("dialog_action_min_width", 104))
            except Exception:
                pass
    for button in root.findChildren(QPushButton):
        button.setProperty("dialogActionRole", dialog_action_role(button))
        try:
            button.setMinimumHeight(max(button.minimumHeight(), BRAND.get("dialog_action_min_height", 42)))
            if dialog_action_role(button) == "primary":
                button.setMinimumWidth(max(button.minimumWidth(), BRAND.get("dialog_primary_min_width", 126)))
        except Exception:
            pass
        button.style().unpolish(button)
        button.style().polish(button)


def _mark_surfaces(dialog: QDialog) -> None:
    dialog.setProperty("brandDialog", True)
    dialog.setProperty("dialogKind", str(dialog.property("dialogKind") or "system"))
    if not dialog.objectName():
        dialog.setObjectName("BrandDialog")
    content = getattr(dialog, "content_widget", None)
    if isinstance(content, QWidget):
        content.setProperty("dialogSurface", "body")
        content.setObjectName(content.objectName() or "BrandDialogBody")
    frame = getattr(dialog, "main_frame", None)
    if isinstance(frame, QFrame):
        frame.setObjectName("BrandDialogFrame")
        frame.setProperty("dialogSurface", "frame")
    title_bar = getattr(dialog, "title_bar", None)
    if isinstance(title_bar, QFrame):
        title_bar.setObjectName("BrandDialogHeader")
        title_bar.setProperty("dialogSurface", "header")
    title_label = getattr(dialog, "title_label", None)
    if isinstance(title_label, QLabel):
        title_label.setObjectName("BrandDialogTitle")
    for child in dialog.findChildren(QWidget):
        if child.objectName() in ("ModernPageHeader", "BrandDialogHeaderCard"):
            child.setProperty("dialogSurface", "headerCard")


def apply_branded_dialog(dialog: QDialog, title: str = "", role: str = "system") -> QDialog:
    """Apply Al Rajhi branded dialog identity to a QDialog instance."""
    dialog.setProperty("dialogKind", role or "system")
    dialog.setProperty("brandDialog", True)
    if title:
        try:
            dialog.setWindowTitle(title)
        except Exception:
            pass
    try:
        dialog.setLayoutDirection(Qt.RightToLeft)
        dialog.setMinimumWidth(max(dialog.minimumWidth(), BRAND.get("dialog_min_width", 560)))
        dialog.setMinimumHeight(max(dialog.minimumHeight(), BRAND.get("dialog_min_height", 360)))
    except Exception:
        pass
    _mark_surfaces(dialog)
    normalize_dialog_buttons(dialog)
    try:
        dialog.setStyleSheet(ThemeManager.get_stylesheet())
    except Exception:
        pass
    return dialog


def brand_message_box(box: QMessageBox, role: str = "info") -> QMessageBox:
    """Apply branded visual identity to an existing QMessageBox."""
    box.setProperty("brandDialog", True)
    box.setProperty("dialogKind", f"message_{role or 'info'}")
    box.setObjectName("BrandMessageBox")
    try:
        box.setMinimumWidth(BRAND.get("message_box_min_width", 460))
        box.setLayoutDirection(Qt.RightToLeft)
    except Exception:
        pass
    normalize_dialog_buttons(box)
    try:
        box.setStyleSheet(ThemeManager.get_stylesheet())
    except Exception:
        pass
    return box


def branded_question(parent, title: str, text: str, buttons=None, default_button=None) -> int:
    """Branded QMessageBox.question replacement for new code paths."""
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Question)
    box.setWindowTitle(title or translate("confirm"))
    box.setText(text)
    if buttons is None:
        buttons = QMessageBox.Yes | QMessageBox.No
    box.setStandardButtons(buttons)
    if default_button is not None:
        box.setDefaultButton(default_button)
    brand_message_box(box, "question")
    return box.exec_()


__all__ = [
    "apply_branded_dialog",
    "brand_message_box",
    "branded_question",
    "dialog_action_role",
    "normalize_dialog_buttons",
]
