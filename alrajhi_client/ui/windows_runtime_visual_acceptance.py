# -*- coding: utf-8 -*-
"""Windows runtime visual acceptance helpers.

Phase453 is a runtime-facing correction layer driven by real Windows screenshots.
It intentionally stays visual-only: Qt style normalization, inspectable dynamic
properties, Arabic label cleanup, and delayed repolish for widgets created after
lazy page loading. No business logic, routing, permissions, printing, or data
models are changed here.
"""
from __future__ import annotations

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QApplication, QAbstractButton, QComboBox, QLabel, QLineEdit, QTextEdit,
    QPlainTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QTableView,
    QTableWidget, QWidget,
)

from theme.brand import BRAND

WINDOWS_RUNTIME_VISUAL_ACCEPTANCE_PHASE = 453

_RUNTIME_ARABIC_REPLACEMENTS = {
    "row density": "كثافة الصفوف",
    "Filters": "الفلاتر",
    "Filter": "فلتر",
    "Fit": "ملاءمة العرض",
    "Excel": "تصدير Excel",
    "Restaurant table Takeaway / session": "طلب مطعم خارجي / جلسة",
    "Restaurant table Takeaway / ses": "طلب مطعم خارجي / جلسة",
    "Takeaway / session": "طلب خارجي / جلسة",
}


def install_windows_runtime_visual_acceptance(app: QApplication | None) -> None:
    """Normalize the Qt widget engine for Windows screenshots.

    Fusion avoids large native Windows controls leaking through QComboBox,
    QSpinBox, QDateEdit and table headers. The call is defensive and occurs
    before the theme manager applies the central stylesheet.
    """
    if app is None:
        return
    try:
        app.setProperty("windowsRuntimeVisualAcceptancePhase", WINDOWS_RUNTIME_VISUAL_ACCEPTANCE_PHASE)
        app.setProperty("runtimeVisualStyle", "Fusion")
        if bool(BRAND.get("windows_runtime_force_fusion", True)):
            app.setStyle(str(BRAND.get("windows_runtime_qt_style", "Fusion")))
    except Exception:
        pass


def _replace_runtime_text(text: str) -> str:
    result = str(text or "")
    for old, new in _RUNTIME_ARABIC_REPLACEMENTS.items():
        result = result.replace(old, new)
    return result


def _button_runtime_role(button: QAbstractButton, workspace_type: str) -> str:
    text = (button.text() or "").lower()
    name = (button.objectName() or "").lower()
    if "حذف" in text or "delete" in text or "إلغاء" in text or "الغاء" in text or name == "danger":
        return "runtime_danger_action"
    if "حفظ" in text or "دفع" in text or "تسجيل" in text or "اضاف" in text or "إضافة" in text or "checkout" in name or name == "primary":
        return "runtime_primary_action"
    if workspace_type == "operational":
        return "runtime_operational_action"
    return "runtime_secondary_action"


def apply_windows_runtime_visual_acceptance(root: QWidget | None, page_id: str = "", workspace_type: str = "") -> None:
    """Apply runtime-only visual metadata and light text cleanup to a subtree."""
    if root is None:
        return
    try:
        root.setProperty("windowsRuntimeVisualAcceptancePhase", WINDOWS_RUNTIME_VISUAL_ACCEPTANCE_PHASE)
        root.setProperty("runtimeVisualAcceptancePage", str(page_id or root.objectName() or "workspace"))
        root.setProperty("runtimeVisualAcceptanceType", str(workspace_type or root.property("visualWorkspaceType") or "workspace"))
        root.setProperty("visualStyleSource", "windows_runtime_visual_acceptance_corrections")
    except Exception:
        pass

    controls = list(root.findChildren(QWidget)) if hasattr(root, "findChildren") else []
    for child in controls:
        try:
            child.setProperty("windowsRuntimeVisualAcceptancePhase", WINDOWS_RUNTIME_VISUAL_ACCEPTANCE_PHASE)
            if isinstance(child, QLabel):
                new_text = _replace_runtime_text(child.text())
                if new_text != child.text():
                    child.setText(new_text)
            elif isinstance(child, QAbstractButton):
                new_text = _replace_runtime_text(child.text())
                if new_text != child.text():
                    child.setText(new_text)
                if not child.property("visualRole") or str(child.property("visualRole")).startswith("workspace"):
                    child.setProperty("visualRole", _button_runtime_role(child, str(workspace_type or "")))
            elif isinstance(child, QComboBox):
                for i in range(child.count()):
                    new_text = _replace_runtime_text(child.itemText(i))
                    if new_text != child.itemText(i):
                        child.setItemText(i, new_text)
                if not child.property("visualRole"):
                    child.setProperty("visualRole", "runtime_input")
            elif isinstance(child, (QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit)):
                if not child.property("visualRole"):
                    child.setProperty("visualRole", "runtime_input")
            elif isinstance(child, (QTableView, QTableWidget)):
                child.setProperty("runtimeTableNormalized", True)
        except Exception:
            continue

    try:
        root.style().unpolish(root)
        root.style().polish(root)
        root.update()
    except Exception:
        pass
    try:
        QTimer.singleShot(0, lambda r=root: (r.style().unpolish(r), r.style().polish(r), r.update()))
        QTimer.singleShot(120, lambda r=root: (r.style().unpolish(r), r.style().polish(r), r.update()))
    except Exception:
        pass


__all__ = [
    "WINDOWS_RUNTIME_VISUAL_ACCEPTANCE_PHASE",
    "install_windows_runtime_visual_acceptance",
    "apply_windows_runtime_visual_acceptance",
]
