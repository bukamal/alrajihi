# -*- coding: utf-8 -*-
"""Phase454 runtime layout reconstruction.

This layer is intentionally visual/layout-only.  It reacts to the Windows
runtime screenshots by marking dense legacy surfaces and their child controls
with explicit layout roles.  It does not touch business logic, services,
permissions, printing, Enter navigation, DAO/API calls, or persistence.
"""
from __future__ import annotations

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QAbstractButton, QAbstractItemView, QComboBox, QFrame, QLabel,
    QLineEdit, QSplitter, QWidget,
)

RUNTIME_LAYOUT_RECONSTRUCTION_PHASE = 454

_PHASE454_ARABIC_REPLACEMENTS = {
    "Ctrl+Shift+F fit columns": "Ctrl+Shift+F ملاءمة الأعمدة",
    "F4 columns": "F4 الأعمدة",
    "Enter: next cell": "Enter: الخلية التالية",
    "Insert: new line": "Insert: سطر جديد",
    "Ctrl+D duplicate": "Ctrl+D تكرار",
    "Ctrl+L barcode": "Ctrl+L باركود",
    "F6 qty": "F6 الكمية",
}


def _replace_text(text: str) -> str:
    result = str(text or "")
    for old, new in _PHASE454_ARABIC_REPLACEMENTS.items():
        result = result.replace(old, new)
    return result


def _classify_page(root: QWidget | None, page_id: str = "", workspace_type: str = "") -> str:
    if root is None:
        return "generic"
    haystack = " ".join([
        str(page_id or ""),
        str(workspace_type or ""),
        str(root.objectName() or ""),
        str(root.property("visualWorkspaceType") or ""),
        str(root.property("runtimeVisualAcceptancePage") or ""),
        str(root.property("runtimeVisualAcceptanceType") or ""),
    ]).lower()
    if "login" in haystack:
        return "login"
    if "pos" in haystack or "operational" in haystack:
        return "pos"
    if "invoice" in haystack or "document" in haystack:
        return "document"
    if "material" in haystack or "materials" in haystack or "item" in haystack:
        return "material"
    return "generic"


def _button_weight(button: QAbstractButton, family: str) -> str:
    text = (button.text() or "").lower()
    name = (button.objectName() or "").lower()
    if "حذف" in text or "delete" in text or "إلغاء" in text or "الغاء" in text or "cancel" in name or "danger" in name:
        return "danger"
    if "حفظ" in text or "دفع" in text or "تسجيل" in text or "إضافة" in text or "اضافة" in text or "checkout" in name or "primary" in name:
        return "primary"
    if family in {"pos", "document"} and ("طباعة" in text or "print" in text):
        return "primary"
    return "secondary"


def apply_runtime_layout_reconstruction(root: QWidget | None, page_id: str = "", workspace_type: str = "") -> None:
    """Mark a visible page/dialog subtree with Phase454 layout reconstruction roles."""
    if root is None:
        return
    family = _classify_page(root, page_id, workspace_type)
    try:
        root.setProperty("runtimeLayoutReconstructionPhase", RUNTIME_LAYOUT_RECONSTRUCTION_PHASE)
        root.setProperty("runtimeLayoutReconstructionFamily", family)
        root.setProperty("visualStyleSource", "runtime_layout_reconstruction_phase454")
    except Exception:
        pass

    controls = list(root.findChildren(QWidget)) if hasattr(root, "findChildren") else []
    for child in controls:
        try:
            child.setProperty("runtimeLayoutReconstructionPhase", RUNTIME_LAYOUT_RECONSTRUCTION_PHASE)
            child.setProperty("runtimeLayoutReconstructionFamily", family)
            name = child.objectName() or ""
            if isinstance(child, QLabel):
                new_text = _replace_text(child.text())
                if new_text != child.text():
                    child.setText(new_text)
                if name.lower() in {"muted", "invoicegridstatus"}:
                    child.setProperty("visualRole", "runtime_helper_text")
            elif isinstance(child, QAbstractButton):
                child.setProperty("runtimeCommandWeight", _button_weight(child, family))
                if not child.property("visualRole") or str(child.property("visualRole")).startswith("runtime_"):
                    child.setProperty("visualRole", f"runtime_{_button_weight(child, family)}_action")
            elif isinstance(child, (QLineEdit, QComboBox)):
                if family == "pos":
                    child.setProperty("runtimeInputDensity", "touch")
                elif family in {"document", "material"}:
                    child.setProperty("runtimeInputDensity", "editor")
            elif isinstance(child, QAbstractItemView):
                child.setProperty("runtimeLayoutTable", "major_grid" if family in {"pos", "document", "material"} else "standard_grid")
            elif isinstance(child, QSplitter):
                child.setProperty("runtimeLayoutSplitter", f"{family}_splitter")
            elif isinstance(child, QFrame):
                if name in {"HeaderCard", "ActionCard", "RightPanel", "BottomActionBar", "MaterialEditorActionBar", "MaterialBasicCard", "MaterialPricingCard", "MaterialBarcodeCard", "MaterialUnitsCard"}:
                    child.setProperty("runtimeLayoutCard", name)
        except Exception:
            continue

    def _repolish(widget: QWidget = root) -> None:
        try:
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()
        except Exception:
            pass

    _repolish(root)
    try:
        QTimer.singleShot(0, lambda: _repolish(root))
        QTimer.singleShot(160, lambda: _repolish(root))
    except Exception:
        pass


__all__ = ["RUNTIME_LAYOUT_RECONSTRUCTION_PHASE", "apply_runtime_layout_reconstruction"]
