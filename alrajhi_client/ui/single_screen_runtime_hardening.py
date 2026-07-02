# -*- coding: utf-8 -*-
"""Phase456 single-screen runtime hardening.

This pass hardens the specific screens that were rebuilt in Phase455.  It is a
visual/layout acceptance layer only: no business logic, no DAO/API, no printing,
no Enter-grid navigation, no permissions, and no persistence changes.
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
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QWidget,
)

from theme.brand import BRAND

SINGLE_SCREEN_RUNTIME_HARDENING_PHASE = 456

_PHASE456_TEXT_REPLACEMENTS = {
    "row density": "كثافة الصفوف",
    "Filters": "الفلاتر",
    "Fit": "ملاءمة العرض",
    "Columns": "الأعمدة",
    "Issues": "الملاحظات",
    "Lines": "السطور",
    "Qty": "الكمية",
    "Quantity": "الكمية",
    "Takeaway / session": "طلب خارجي / جلسة",
}

_CRITICAL_FAMILIES = {"login", "dashboard", "pos", "invoice", "material"}


def _safe_text(text: str) -> str:
    value = str(text or "")
    for old, new in _PHASE456_TEXT_REPLACEMENTS.items():
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
        str(root.property("targetedScreenRebuildFamily") or ""),
        str(root.property("runtimeLayoutReconstructionFamily") or ""),
        str(root.property("runtimeVisualAcceptancePage") or ""),
    ]).lower()
    # Material must be resolved before generic document/invoice because material
    # editors inherit document shell contracts.
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


def _height(widget: QWidget, minimum: int | None = None, maximum: int | None = None) -> None:
    try:
        if minimum is not None:
            widget.setMinimumHeight(int(minimum))
        if maximum is not None:
            widget.setMaximumHeight(int(maximum))
    except Exception:
        pass


def _width(widget: QWidget, minimum: int | None = None, maximum: int | None = None) -> None:
    try:
        if minimum is not None:
            widget.setMinimumWidth(int(minimum))
        if maximum is not None:
            widget.setMaximumWidth(int(maximum))
    except Exception:
        pass


def _polish(widget: QWidget | None) -> None:
    if widget is None:
        return
    try:
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()
    except Exception:
        pass


def _button_role(button: QAbstractButton, family: str) -> str:
    text = (button.text() or "").lower()
    name = (button.objectName() or "").lower()
    if any(x in text for x in ("حذف", "delete", "إلغاء", "الغاء", "خروج", "إغلاق", "اغلاق")) or any(x in name for x in ("danger", "delete", "cancel", "close")):
        return "screen_danger_action"
    if any(x in text for x in ("حفظ", "دفع", "تسجيل", "إضافة", "اضافة", "إنهاء", "انهاء")) or any(x in name for x in ("primary", "save", "checkout")):
        return "screen_primary_action"
    if family in {"invoice", "pos"} and any(x in text for x in ("طباعة", "print")):
        return "screen_primary_action"
    return "screen_secondary_action"


def _harden_common(root: QWidget, family: str) -> None:
    _set_prop(root, "singleScreenRuntimeHardeningPhase", SINGLE_SCREEN_RUNTIME_HARDENING_PHASE)
    _set_prop(root, "screenHardeningFamily", family)
    _set_prop(root, "visualStyleSource", "single_screen_runtime_hardening_phase456")
    _set_prop(root, "screenRebuildGuardSignature", f"phase456:{family}")

    for child in root.findChildren(QWidget):
        try:
            child.setProperty("singleScreenRuntimeHardeningPhase", SINGLE_SCREEN_RUNTIME_HARDENING_PHASE)
            child.setProperty("screenHardeningFamily", family)
            if isinstance(child, QLabel):
                new_text = _safe_text(child.text())
                if new_text != child.text():
                    child.setText(new_text)
            elif isinstance(child, QAbstractButton):
                role = _button_role(child, family)
                child.setProperty("visualRole", role)
                child.setProperty("screenHardeningAction", role.replace("screen_", ""))
                if role == "screen_primary_action":
                    child.setMinimumWidth(int(BRAND.get("screen_hardening_primary_button_min_width", 120)))
                elif role == "screen_secondary_action":
                    child.setMinimumWidth(int(BRAND.get("screen_hardening_secondary_button_min_width", 92)))
            elif isinstance(child, (QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox)):
                child.setProperty("screenHardeningInput", f"{family}_field")
                _height(child, int(BRAND.get("screen_hardening_control_height", 40)), None)
            elif isinstance(child, QAbstractItemView):
                child.setProperty("screenHardeningGrid", "major" if family in _CRITICAL_FAMILIES else "standard")
                try:
                    child.setAlternatingRowColors(True)
                except Exception:
                    pass
            elif isinstance(child, QSplitter):
                child.setProperty("screenHardeningSplitter", f"{family}_fixed_ratio")
            elif isinstance(child, (QFrame, QGroupBox)):
                name = child.objectName() or ""
                if name:
                    child.setProperty("screenHardeningPanel", name)
        except Exception:
            continue


def _harden_login(root: QWidget) -> None:
    _set_prop(root, "loginSingleScreenHardeningPhase", SINGLE_SCREEN_RUNTIME_HARDENING_PHASE)
    _set_prop(root, "loginScreenContract", "compact_brand_form_no_native_chrome")
    for child in root.findChildren(QWidget):
        name = child.objectName() or ""
        try:
            if name == "LoginRuntimeTitleBar":
                child.setProperty("screenHardeningPanel", "login_micro_titlebar")
                _height(child, BRAND.get("login_hardened_titlebar_height", 24), BRAND.get("login_hardened_titlebar_height", 24))
            elif name == "firstRunBrandPanel":
                child.setProperty("screenHardeningPanel", "login_brand_anchor")
                child.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
            elif name == "firstRunFormPanel":
                child.setProperty("screenHardeningPanel", "login_form_anchor")
                child.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            elif name == "loginCredentialsPanel":
                child.setProperty("screenHardeningPanel", "login_credentials_compact_card")
                _height(child, BRAND.get("login_hardened_credentials_height", 224), BRAND.get("login_hardened_credentials_max_height", 248))
            elif name == "loginOptionsPanel":
                child.setProperty("screenHardeningPanel", "login_options_micro_card")
                _height(child, BRAND.get("login_hardened_options_height", 48), BRAND.get("login_hardened_options_height", 48))
            elif name == "firstRunLoginModeChip":
                child.setProperty("screenHardeningPanel", "login_mode_micro_chip")
        except Exception:
            continue


def _harden_dashboard(root: QWidget) -> None:
    _set_prop(root, "dashboardSingleScreenHardeningPhase", SINGLE_SCREEN_RUNTIME_HARDENING_PHASE)
    _set_prop(root, "dashboardScreenContract", "kpi_shortcut_identity_balanced")
    for child in root.findChildren(QWidget):
        try:
            role = str(child.property("dashboardPanelRole") or "")
            if role:
                child.setProperty("screenHardeningPanel", f"dashboard_{role}_card")
                child.setProperty("screenHardeningCard", "dashboard_balanced_card")
            if isinstance(child, QAbstractButton) and child.property("visualRole") in {"dashboard_shortcut", "screen_secondary_action"}:
                child.setProperty("screenHardeningAction", "dashboard_shortcut")
                child.setMinimumHeight(int(BRAND.get("dashboard_hardened_shortcut_height", 64)))
        except Exception:
            continue


def _harden_pos(root: QWidget) -> None:
    _set_prop(root, "posSingleScreenHardeningPhase", SINGLE_SCREEN_RUNTIME_HARDENING_PHASE)
    _set_prop(root, "posScreenContract", "scan_grid_payment_three_zone")
    for child in root.findChildren(QWidget):
        name = child.objectName() or ""
        try:
            if name == "POSRuntimeTopTools":
                child.setProperty("screenHardeningPanel", "pos_micro_top_tools")
                _height(child, BRAND.get("pos_hardened_top_tools_height", 38), BRAND.get("pos_hardened_top_tools_height", 38))
            elif name == "POSRuntimeContextBar":
                child.setProperty("screenHardeningPanel", "pos_micro_context_bar")
                _height(child, BRAND.get("pos_hardened_context_height", 42), BRAND.get("pos_hardened_context_height", 42))
            elif name == "POSRuntimeScanBar":
                child.setProperty("screenHardeningPanel", "pos_scan_first_panel")
                _height(child, BRAND.get("pos_hardened_scan_bar_height", 88), BRAND.get("pos_hardened_scan_bar_height", 88))
            elif isinstance(child, QLineEdit) and child.property("visualRole") == "operational_scan_input":
                child.setProperty("screenHardeningInput", "pos_primary_barcode")
                _height(child, BRAND.get("pos_hardened_scan_input_height", 66), BRAND.get("pos_hardened_scan_input_height", 66))
            elif child.objectName() == "posPaymentShell" or child.property("posPaymentLayout"):
                child.setProperty("screenHardeningPanel", "pos_payment_command_footer")
                _height(child, BRAND.get("pos_hardened_payment_footer_height", 146), None)
        except Exception:
            continue


def _harden_invoice(root: QWidget) -> None:
    _set_prop(root, "invoiceSingleScreenHardeningPhase", SINGLE_SCREEN_RUNTIME_HARDENING_PHASE)
    _set_prop(root, "invoiceScreenContract", "header_entry_grid_summary_footer_locked")
    for child in root.findChildren(QWidget):
        name = child.objectName() or ""
        try:
            if name == "HeaderCard":
                child.setProperty("screenHardeningPanel", "invoice_header_fields_card")
            elif name == "ActionCard":
                child.setProperty("screenHardeningPanel", "invoice_fast_entry_card")
                _height(child, BRAND.get("invoice_hardened_quick_entry_height", 58), BRAND.get("invoice_hardened_quick_entry_height", 58))
            elif name == "RightPanel":
                child.setProperty("screenHardeningPanel", "invoice_financial_summary_locked")
                _width(child, BRAND.get("invoice_hardened_summary_width", 360), BRAND.get("invoice_hardened_summary_width", 360))
            elif name == "BottomActionBar":
                child.setProperty("screenHardeningPanel", "invoice_command_footer_locked")
                _height(child, BRAND.get("invoice_hardened_footer_height", 64), BRAND.get("invoice_hardened_footer_height", 64))
            elif name == "InvoiceRuntimeSearchInput":
                child.setProperty("screenHardeningInput", "invoice_primary_material_lookup")
                _height(child, BRAND.get("invoice_hardened_search_height", 48), BRAND.get("invoice_hardened_search_height", 48))
        except Exception:
            continue


def _harden_material(root: QWidget) -> None:
    _set_prop(root, "materialSingleScreenHardeningPhase", SINGLE_SCREEN_RUNTIME_HARDENING_PHASE)
    _set_prop(root, "materialScreenContract", "cards_units_barcode_footer_locked")
    for child in root.findChildren(QWidget):
        name = child.objectName() or ""
        try:
            if name in {"MaterialBasicCard", "MaterialPricingCard", "MaterialBarcodeCard", "MaterialUnitsCard"}:
                child.setProperty("screenHardeningPanel", f"{name}_locked_card")
                child.setProperty("screenHardeningCard", "material_editor_card")
                _width(child, BRAND.get("material_hardened_card_min_width", 380), None)
            elif name == "MaterialUnitsCard":
                _height(child, BRAND.get("material_hardened_units_height", 390), None)
            elif name == "MaterialEditorActionBar":
                child.setProperty("screenHardeningPanel", "material_command_footer_locked")
                _height(child, BRAND.get("material_hardened_footer_height", 64), BRAND.get("material_hardened_footer_height", 64))
        except Exception:
            continue


def apply_single_screen_runtime_hardening(root: QWidget | None, page_id: str = "", workspace_type: str = "") -> None:
    """Harden the rebuilt single-screen layouts against Windows runtime regressions."""
    if root is None:
        return
    family = _classify(root, page_id, workspace_type)
    _harden_common(root, family)
    if family == "login":
        _harden_login(root)
    elif family == "dashboard":
        _harden_dashboard(root)
    elif family == "pos":
        _harden_pos(root)
    elif family == "invoice":
        _harden_invoice(root)
    elif family == "material":
        _harden_material(root)

    _polish(root)
    try:
        QTimer.singleShot(0, lambda: _polish(root))
        QTimer.singleShot(220, lambda: _polish(root))
        QTimer.singleShot(520, lambda: _polish(root))
    except Exception:
        pass


__all__ = ["SINGLE_SCREEN_RUNTIME_HARDENING_PHASE", "apply_single_screen_runtime_hardening"]
