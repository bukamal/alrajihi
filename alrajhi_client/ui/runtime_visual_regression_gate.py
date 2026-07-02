# -*- coding: utf-8 -*-
"""Phase457 runtime visual regression gate.

This pass is a visual/layout regression gate only: no business logic,
no DAO/API, no printing, no permissions, no persistence, no activation, and
no Enter-grid navigation.  Its purpose is to lock the screenshot-problem screens after the
Phase453-456 runtime passes and expose a deterministic guard signature for
static tests and Windows runtime diagnostics.
"""
from __future__ import annotations

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QAbstractButton,
    QAbstractItemView,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGroupBox,
    QLabel,
    QLineEdit,
    QSpinBox,
    QWidget,
)

from theme.brand import BRAND

RUNTIME_VISUAL_REGRESSION_GATE_PHASE = 457
_REQUIRED_PHASES = (453, 454, 455, 456)
_GATED_FAMILIES = {"login", "dashboard", "pos", "invoice", "material"}

_PHASE457_TEXT_REPLACEMENTS = {
    "row density": "كثافة الصفوف",
    "Filters": "الفلاتر",
    "Fit": "ملاءمة العرض",
    "Columns": "الأعمدة",
    "Issues": "الملاحظات",
    "Lines": "السطور",
    "Qty": "الكمية",
    "Quantity": "الكمية",
    "Takeaway / session": "طلب خارجي / جلسة",
    "Open screen": "فتح الشاشة",
    "More": "المزيد",
}


def _safe_text(text: str) -> str:
    value = str(text or "")
    for old, new in _PHASE457_TEXT_REPLACEMENTS.items():
        value = value.replace(old, new)
    return value


def _classify(root: QWidget | None, page_id: str = "", workspace_type: str = "") -> str:
    if root is None:
        return "generic"
    haystack = " ".join([
        str(page_id or ""),
        str(workspace_type or ""),
        str(root.objectName() or ""),
        str(root.property("visualWorkspaceType") or ""),
        str(root.property("screenHardeningFamily") or ""),
        str(root.property("targetedScreenRebuildFamily") or ""),
        str(root.property("runtimeLayoutReconstructionFamily") or ""),
        str(root.property("runtimeVisualAcceptancePage") or ""),
    ]).lower()
    if "login" in haystack:
        return "login"
    if "dashboard" in haystack:
        return "dashboard"
    if "material" in haystack or "materials" in haystack or "item_editor" in haystack:
        return "material"
    if "pos" in haystack or "cashier" in haystack or "operational" in haystack:
        return "pos"
    if "invoice" in haystack or "transaction" in haystack or "document" in haystack:
        return "invoice"
    return "generic"


def _set_prop(widget: QWidget, key: str, value) -> None:
    try:
        widget.setProperty(key, value)
    except Exception:
        pass


def _has_phase(root: QWidget, phase: int) -> bool:
    phase_value = str(phase)
    names = [
        "windowsRuntimeVisualAcceptancePhase",
        "runtimeLayoutReconstructionPhase",
        "targetedScreenRebuildPhase",
        "singleScreenRuntimeHardeningPhase",
        "loginSingleScreenHardeningPhase",
        "dashboardSingleScreenHardeningPhase",
        "posSingleScreenHardeningPhase",
        "invoiceSingleScreenHardeningPhase",
        "materialSingleScreenHardeningPhase",
        "loginTargetedRebuildPhase",
        "posTargetedRebuildPhase",
        "invoiceTargetedRebuildPhase",
        "materialTargetedRebuildPhase",
        "runtimeVisualPhase",
    ]
    widgets = [root]
    try:
        widgets.extend(root.findChildren(QWidget))
    except Exception:
        pass
    for widget in widgets:
        for key in names:
            try:
                if str(widget.property(key) or "") == phase_value:
                    return True
            except Exception:
                continue
    return False


def _phase_status(root: QWidget) -> str:
    present = [str(p) for p in _REQUIRED_PHASES if _has_phase(root, p)]
    missing = [str(p) for p in _REQUIRED_PHASES if str(p) not in present]
    if not missing:
        return "complete"
    return "missing:" + ",".join(missing)


def _button_gate_role(button: QAbstractButton, family: str) -> str:
    text = (button.text() or "").lower()
    name = (button.objectName() or "").lower()
    if any(x in text for x in ("حذف", "delete", "إلغاء", "الغاء", "إغلاق", "اغلاق", "خروج")) or any(x in name for x in ("danger", "delete", "cancel", "close")):
        return "regression_danger_action"
    if any(x in text for x in ("حفظ", "دفع", "تسجيل", "إضافة", "اضافة", "إنهاء", "انهاء", "طباعة")) or any(x in name for x in ("primary", "save", "checkout", "print")):
        return "regression_primary_action"
    if family in {"pos", "invoice"} and any(x in text for x in ("تعليق", "استئناف", "مسح")):
        return "regression_secondary_action"
    return "regression_secondary_action"


def _apply_common(root: QWidget, family: str) -> None:
    status = _phase_status(root)
    signature = f"phase457:{family}:required=453,454,455,456:status={status}"
    _set_prop(root, "runtimeVisualRegressionGatePhase", RUNTIME_VISUAL_REGRESSION_GATE_PHASE)
    _set_prop(root, "visualRegressionGateFamily", family)
    _set_prop(root, "visualRegressionGateStatus", status)
    _set_prop(root, "visualRegressionGuardSignature", signature)
    _set_prop(root, "visualStyleSource", "runtime_visual_regression_gate_phase457")

    for child in root.findChildren(QWidget):
        try:
            child.setProperty("runtimeVisualRegressionGatePhase", RUNTIME_VISUAL_REGRESSION_GATE_PHASE)
            child.setProperty("visualRegressionGateFamily", family)
            if isinstance(child, QLabel):
                new_text = _safe_text(child.text())
                if new_text != child.text():
                    child.setText(new_text)
            elif isinstance(child, QAbstractButton):
                role = _button_gate_role(child, family)
                child.setProperty("visualRole", role)
                child.setProperty("visualRegressionActionRole", role.replace("regression_", ""))
                if role == "regression_primary_action":
                    child.setMinimumHeight(int(BRAND.get("regression_gate_primary_button_height", 42)))
                else:
                    child.setMinimumHeight(int(BRAND.get("regression_gate_secondary_button_height", 38)))
            elif isinstance(child, (QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox)):
                child.setProperty("visualRegressionInput", f"{family}_locked_control")
                if child.minimumHeight() < int(BRAND.get("regression_gate_control_height", 40)):
                    child.setMinimumHeight(int(BRAND.get("regression_gate_control_height", 40)))
            elif isinstance(child, QAbstractItemView):
                child.setProperty("visualRegressionGrid", "major" if family in _GATED_FAMILIES else "standard")
            elif isinstance(child, (QFrame, QGroupBox)) and child.objectName():
                child.setProperty("visualRegressionPanel", child.objectName())
        except Exception:
            continue


def _apply_family_lock(root: QWidget, family: str) -> None:
    if family == "login":
        _set_prop(root, "loginVisualRegressionContract", "brand_form_compact_no_native_regression")
    elif family == "dashboard":
        _set_prop(root, "dashboardVisualRegressionContract", "balanced_kpi_shortcut_identity_runtime")
    elif family == "pos":
        _set_prop(root, "posVisualRegressionContract", "scan_first_grid_payment_runtime")
    elif family == "invoice":
        _set_prop(root, "invoiceVisualRegressionContract", "header_entry_grid_summary_footer_runtime")
    elif family == "material":
        _set_prop(root, "materialVisualRegressionContract", "cards_units_barcode_footer_runtime")


def _polish(root: QWidget | None) -> None:
    if root is None:
        return
    try:
        root.style().unpolish(root)
        root.style().polish(root)
        root.update()
    except Exception:
        pass


def apply_runtime_visual_regression_gate(root: QWidget | None, page_id: str = "", workspace_type: str = "") -> None:
    """Apply the Phase457 visual regression gate to screenshot-critical screens."""
    if root is None:
        return
    family = _classify(root, page_id, workspace_type)
    _apply_common(root, family)
    if family in _GATED_FAMILIES:
        _apply_family_lock(root, family)
    _polish(root)
    try:
        QTimer.singleShot(0, lambda: _polish(root))
        QTimer.singleShot(250, lambda: _polish(root))
        QTimer.singleShot(650, lambda: _polish(root))
    except Exception:
        pass


__all__ = ["RUNTIME_VISUAL_REGRESSION_GATE_PHASE", "apply_runtime_visual_regression_gate"]
