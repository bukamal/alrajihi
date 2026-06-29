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
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFrame,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableView,
    QTableWidget,
    QTabWidget,
    QTextEdit,
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
        button_box.setProperty("visualRole", "modal_button_box")
        for button in button_box.buttons():
            role = dialog_action_role(button)
            button.setProperty("dialogActionRole", role)
            button.setProperty("visualRole", _modal_button_visual_role(role))
            try:
                button.setMinimumHeight(BRAND.get("dialog_action_min_height", 42))
                button.setMinimumWidth(BRAND.get("dialog_action_min_width", 104))
            except Exception:
                pass
    for button in root.findChildren(QPushButton):
        role = dialog_action_role(button)
        button.setProperty("dialogActionRole", role)
        button.setProperty("visualRole", _modal_button_visual_role(role))
        try:
            button.setMinimumHeight(max(button.minimumHeight(), BRAND.get("dialog_action_min_height", 42)))
            if role == "primary":
                button.setMinimumWidth(max(button.minimumWidth(), BRAND.get("dialog_primary_min_width", 126)))
        except Exception:
            pass
        try:
            button.style().unpolish(button)
            button.style().polish(button)
        except Exception:
            pass


def _modal_button_visual_role(role: str) -> str:
    """Phase452: map old dialog action roles into central modal roles."""
    if role == "primary":
        return "modal_primary_action"
    if role == "danger":
        return "modal_danger_action"
    if role == "close":
        return "modal_close_action"
    return "modal_secondary_action"


def _modal_label_role(label: QLabel) -> str:
    name = (label.objectName() or "").lower()
    text = (label.text() or "").strip()
    existing = str(label.property("dialogLabelRole") or label.property("visualRole") or "").lower()
    if existing in {"title", "modal_title"} or "title" in name or name in {"branddialogtitle", "modernpagetitle"}:
        return "modal_title"
    if existing in {"subtitle", "help", "modal_help"} or "help" in name or "hint" in name or len(text) > 70:
        return "modal_help"
    if "status" in name or "error" in name or "warning" in name or "danger" in name:
        return "modal_status"
    return "modal_text"


def apply_modal_visual_template(root: QWidget, role: str = "system") -> QWidget:
    """Phase452: normalize dialog/modal chrome through dynamic properties only.

    This is intentionally cosmetic. It does not alter validation, persistence,
    accepted/rejected wiring, or modal lifetime. It simply marks existing
    dialogs, message boxes, controls, tables and action buttons so theme/qss.py
    can render them with one project-wide modal grammar.
    """
    if root is None:
        return root
    try:
        root.setProperty("modalVisualPhase", "452")
        root.setProperty("visualWorkspaceType", "modal")
        root.setProperty("visualStyleSource", "dialogs_modal_windows_visual_unification")
        if not root.property("dialogKind"):
            root.setProperty("dialogKind", role or "system")
        if isinstance(root, QDialog):
            root.setLayoutDirection(Qt.RightToLeft)
            root.setMinimumWidth(max(root.minimumWidth(), BRAND.get("dialog_min_width", 560)))
        elif isinstance(root, QMessageBox):
            root.setLayoutDirection(Qt.RightToLeft)
            root.setMinimumWidth(max(root.minimumWidth(), BRAND.get("message_box_min_width", 460)))
    except Exception:
        pass

    for child in root.findChildren(QWidget) if hasattr(root, "findChildren") else []:
        try:
            child.setProperty("modalVisualPhase", "452")
            child.setProperty("visualWorkspaceType", "modal")
            cname = child.__class__.__name__
            if isinstance(child, QDialogButtonBox):
                child.setProperty("visualRole", "modal_button_box")
                child.setProperty("dialogSurface", "footer")
            elif isinstance(child, (QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit, QCheckBox)):
                child.setProperty("visualRole", "modal_input")
                if hasattr(child, "setMinimumHeight") and child.minimumHeight() < 36:
                    child.setMinimumHeight(36)
            elif isinstance(child, (QTableView, QTableWidget)):
                child.setProperty("visualRole", "modal_table")
                try:
                    child.setAlternatingRowColors(True)
                except Exception:
                    pass
            elif isinstance(child, QTabWidget):
                child.setProperty("visualRole", "modal_tabs")
                child.setDocumentMode(True)
            elif isinstance(child, QGroupBox):
                child.setProperty("visualRole", "modal_card")
            elif isinstance(child, QFrame):
                if child.objectName() == "BrandDialogFrame":
                    child.setProperty("visualRole", "modal_shell")
                    child.setProperty("dialogSurface", "frame")
                elif child.objectName() == "BrandDialogHeader":
                    child.setProperty("visualRole", "modal_header")
                    child.setProperty("dialogSurface", "header")
                elif child.objectName() in {"ModernPageHeader", "BrandDialogHeaderCard"}:
                    child.setProperty("visualRole", "modal_header_card")
                elif not child.property("visualRole"):
                    child.setProperty("visualRole", "modal_card")
            elif isinstance(child, QLabel):
                role_name = _modal_label_role(child)
                child.setProperty("visualRole", role_name)
                name = (child.objectName() or "").lower()
                if "danger" in name or "error" in name:
                    child.setProperty("modalTone", "danger")
                elif "warning" in name:
                    child.setProperty("modalTone", "warning")
                elif "success" in name:
                    child.setProperty("modalTone", "success")
            elif isinstance(child, QScrollArea):
                child.setProperty("visualRole", "modal_scroll")
            elif isinstance(child, QAbstractButton):
                role_name = dialog_action_role(child)
                child.setProperty("dialogActionRole", role_name)
                child.setProperty("visualRole", _modal_button_visual_role(role_name))
        except Exception:
            continue
    normalize_dialog_buttons(root)
    try:
        root.style().unpolish(root)
        root.style().polish(root)
        root.update()
    except Exception:
        pass
    return root


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
    dialog.setProperty("basitDialogSurface", True)
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
    apply_modal_visual_template(dialog, role or "system")
    try:
        dialog.setStyleSheet(ThemeManager.get_stylesheet())
    except Exception:
        pass
    return dialog


def brand_message_box(box: QMessageBox, role: str = "info") -> QMessageBox:
    """Apply branded visual identity to an existing QMessageBox."""
    box.setProperty("brandDialog", True)
    box.setProperty("basitDialogSurface", True)
    box.setProperty("dialogKind", f"message_{role or 'info'}")
    box.setObjectName("BrandMessageBox")
    try:
        box.setMinimumWidth(BRAND.get("message_box_min_width", 460))
        box.setLayoutDirection(Qt.RightToLeft)
    except Exception:
        pass
    apply_modal_visual_template(box, role or "info")
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
    "apply_modal_visual_template",
    "brand_message_box",
    "branded_question",
    "dialog_action_role",
    "normalize_dialog_buttons",
]
