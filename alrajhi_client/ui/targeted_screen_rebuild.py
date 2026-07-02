# -*- coding: utf-8 -*-
"""Phase455 targeted screen rebuild.

This pass is deliberately narrow: it rebuilds the visual hierarchy of the
screens that still looked legacy in Windows screenshots after Phase454.  It is
layout/property only: no business logic, no DAO/API, no printing, no Enter-grid
navigation, no permissions, and no persistence changes.
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
    QSplitter,
    QTableView,
    QWidget,
)

from theme.brand import BRAND

TARGETED_SCREEN_REBUILD_PHASE = 455

_PHASE455_TEXT_REPLACEMENTS = {
    "row density": "كثافة الصفوف",
    "Filters": "الفلاتر",
    "Fit": "ملاءمة العرض",
    "Restaurant table Takeaway / session": "طلب مطعم خارجي / جلسة",
    "Quantity used by barcode/quick add": "الكمية المستخدمة عند الإضافة السريعة/الباركود",
    "Lines:": "السطور:",
    "Qty:": "الكمية:",
    "Columns:": "الأعمدة:",
    "Issues:": "الملاحظات:",
}


def _relabel(text: str) -> str:
    value = str(text or "")
    for old, new in _PHASE455_TEXT_REPLACEMENTS.items():
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
        str(root.property("runtimeLayoutReconstructionFamily") or ""),
        str(root.property("runtimeVisualAcceptancePage") or ""),
    ]).lower()
    if "login" in haystack:
        return "login"
    if "dashboard" in haystack:
        return "dashboard"
    if "pos" in haystack or "operational" in haystack:
        return "pos"
    if "invoice" in haystack or "transaction" in haystack or "document" in haystack:
        return "invoice"
    if "material" in haystack or "item" in haystack:
        return "material"
    return "generic"


def _set_height(widget: QWidget, minimum: int | None = None, maximum: int | None = None) -> None:
    try:
        if minimum is not None:
            widget.setMinimumHeight(int(minimum))
        if maximum is not None:
            widget.setMaximumHeight(int(maximum))
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


def _mark_button(button: QAbstractButton, family: str) -> None:
    text = (button.text() or "").lower()
    name = (button.objectName() or "").lower()
    if "حذف" in text or "delete" in text or "إلغاء" in text or "الغاء" in text or "خروج" in text or name in {"danger", "cancel"}:
        role = "targeted_danger_action"
    elif "حفظ" in text or "دفع" in text or "تسجيل" in text or "إضافة" in text or "اضافة" in text or "مسح" in text or name in {"primary", "checkout"}:
        role = "targeted_primary_action"
    elif family in {"invoice", "pos"} and ("طباعة" in text or "print" in text):
        role = "targeted_primary_action"
    else:
        role = "targeted_secondary_action"
    try:
        button.setProperty("visualRole", role)
        button.setProperty("targetedActionRole", role.replace("targeted_", ""))
        button.setProperty("targetedScreenRebuildPhase", TARGETED_SCREEN_REBUILD_PHASE)
    except Exception:
        pass


def _apply_login(root: QWidget) -> None:
    try:
        root.setProperty("loginTargetedRebuildPhase", TARGETED_SCREEN_REBUILD_PHASE)
        root.setProperty("loginChromeMode", "compact_custom_titlebar")
        root.setProperty("loginLayoutIntent", "brand_form_split_clean")
    except Exception:
        pass
    for child in root.findChildren(QWidget):
        name = child.objectName() or ""
        try:
            if name == "LoginRuntimeTitleBar":
                child.setProperty("loginChromeMode", "compact_custom_titlebar")
                _set_height(child, BRAND.get("login_targeted_titlebar_height", 26), BRAND.get("login_targeted_titlebar_height", 26))
            elif name == "firstRunFormPanel":
                child.setProperty("visualRole", "login_form_panel_targeted")
                child.setProperty("loginTargetedPanel", "form")
            elif name == "firstRunBrandPanel":
                child.setProperty("visualRole", "login_brand_panel_targeted")
                child.setProperty("loginTargetedPanel", "brand")
            elif name == "loginCredentialsPanel":
                child.setProperty("visualRole", "login_credentials_card_targeted")
                _set_height(child, BRAND.get("login_targeted_credentials_height", 230), BRAND.get("login_targeted_credentials_max_height", 258))
            elif name == "loginOptionsPanel":
                child.setProperty("visualRole", "login_options_card_targeted")
                _set_height(child, BRAND.get("login_targeted_options_height", 50), BRAND.get("login_targeted_options_max_height", 58))
            elif name == "firstRunLoginModeChip":
                child.setProperty("visualRole", "login_mode_chip_targeted")
            elif isinstance(child, (QLineEdit, QComboBox)):
                child.setProperty("targetedInputRole", "login_field")
                _set_height(child, BRAND.get("login_targeted_field_height", 44), BRAND.get("login_targeted_field_height", 44))
        except Exception:
            continue


def _apply_pos(root: QWidget) -> None:
    try:
        root.setProperty("posTargetedRebuildPhase", TARGETED_SCREEN_REBUILD_PHASE)
        root.setProperty("posLayoutIntent", "barcode_table_payment")
    except Exception:
        pass
    for child in root.findChildren(QWidget):
        name = child.objectName() or ""
        try:
            if name == "POSRuntimeTopTools":
                child.setProperty("visualRole", "pos_top_tools_compact")
                _set_height(child, BRAND.get("pos_targeted_top_tools_height", 42), BRAND.get("pos_targeted_top_tools_height", 42))
            elif name == "POSRuntimeContextBar":
                child.setProperty("visualRole", "pos_context_bar_compact")
                _set_height(child, BRAND.get("pos_targeted_context_height", 46), BRAND.get("pos_targeted_context_height", 46))
            elif name == "POSRuntimeScanBar":
                child.setProperty("visualRole", "pos_scan_bar_primary")
                _set_height(child, BRAND.get("pos_targeted_scan_bar_height", 82), BRAND.get("pos_targeted_scan_bar_height", 82))
            elif isinstance(child, QLineEdit) and child.property("visualRole") == "operational_scan_input":
                child.setProperty("targetedInputRole", "pos_barcode_focus")
                _set_height(child, BRAND.get("pos_targeted_scan_input_height", 62), BRAND.get("pos_targeted_scan_input_height", 62))
            elif isinstance(child, QDoubleSpinBox):
                child.setProperty("targetedInputRole", "pos_quantity")
                _set_height(child, BRAND.get("pos_targeted_control_height", 42), BRAND.get("pos_targeted_control_height", 42))
            elif isinstance(child, QTableView):
                child.setProperty("targetedTableRole", "pos_invoice_lines")
                child.setProperty("runtimeLayoutTable", "pos_targeted_major_grid")
                child.setMinimumHeight(int(BRAND.get("pos_targeted_table_min_height", 360)))
            elif child.property("visualRole") == "operational_payment_shell" or child.property("posPaymentLayout"):
                child.setProperty("visualRole", "pos_payment_footer_targeted")
                child.setProperty("posPaymentLayout", "targeted_primary_footer")
                _set_height(child, BRAND.get("pos_targeted_payment_footer_height", 136), None)
            elif isinstance(child, QAbstractButton):
                _mark_button(child, "pos")
            elif isinstance(child, QLabel):
                text = _relabel(child.text())
                if text != child.text():
                    child.setText(text)
        except Exception:
            continue


def _apply_invoice(root: QWidget) -> None:
    try:
        root.setProperty("invoiceTargetedRebuildPhase", TARGETED_SCREEN_REBUILD_PHASE)
        root.setProperty("invoiceLayoutIntent", "header_entry_grid_financial_footer")
    except Exception:
        pass
    for child in root.findChildren(QWidget):
        name = child.objectName() or ""
        try:
            if name == "HeaderCard":
                card = str(child.property("runtimeLayoutCard") or "")
                child.setProperty("targetedCardRole", card or "invoice_header")
                if card == "invoice_title_header":
                    _set_height(child, BRAND.get("invoice_targeted_title_height", 64), BRAND.get("invoice_targeted_title_height", 64))
                elif card == "invoice_header_fields":
                    _set_height(child, BRAND.get("invoice_targeted_header_fields_height", 132), BRAND.get("invoice_targeted_header_fields_max_height", 156))
            elif name == "ActionCard":
                child.setProperty("targetedCardRole", "invoice_quick_entry")
                _set_height(child, BRAND.get("invoice_targeted_quick_entry_height", 62), BRAND.get("invoice_targeted_quick_entry_height", 62))
            elif name == "RightPanel":
                child.setProperty("targetedCardRole", "invoice_financial_summary")
                child.setMinimumWidth(int(BRAND.get("invoice_targeted_summary_width", 350)))
                child.setMaximumWidth(int(BRAND.get("invoice_targeted_summary_width", 350)) + 30)
            elif name == "BottomActionBar":
                child.setProperty("targetedCardRole", "invoice_sticky_action_footer")
                _set_height(child, BRAND.get("invoice_targeted_action_footer_height", 66), BRAND.get("invoice_targeted_action_footer_height", 66))
            elif name == "InvoiceRuntimeSearchInput":
                child.setProperty("targetedInputRole", "invoice_barcode_search")
                _set_height(child, BRAND.get("invoice_targeted_search_height", 46), BRAND.get("invoice_targeted_search_height", 46))
            elif name == "InvoiceLinesTable" or isinstance(child, QTableView):
                child.setProperty("targetedTableRole", "invoice_lines_editor")
                child.setProperty("runtimeLayoutTable", "invoice_targeted_major_grid")
                child.setMinimumHeight(int(BRAND.get("invoice_targeted_table_min_height", 370)))
            elif isinstance(child, QLabel):
                text = _relabel(child.text())
                if text != child.text():
                    child.setText(text)
            elif isinstance(child, QAbstractButton):
                _mark_button(child, "invoice")
        except Exception:
            continue


def _apply_material(root: QWidget) -> None:
    try:
        root.setProperty("materialTargetedRebuildPhase", TARGETED_SCREEN_REBUILD_PHASE)
        root.setProperty("materialLayoutIntent", "basic_pricing_barcode_units_sticky_footer")
    except Exception:
        pass
    for child in root.findChildren(QWidget):
        name = child.objectName() or ""
        try:
            if name in {"MaterialBasicCard", "MaterialPricingCard", "MaterialBarcodeCard", "MaterialUnitsCard"}:
                child.setProperty("targetedCardRole", name)
                child.setMinimumWidth(int(BRAND.get("material_targeted_card_min_width", 360)))
                if name == "MaterialUnitsCard":
                    child.setMinimumHeight(int(BRAND.get("material_targeted_units_min_height", 360)))
            elif name == "MaterialEditorActionBar":
                child.setProperty("targetedCardRole", "material_sticky_action_footer")
                _set_height(child, BRAND.get("material_targeted_footer_height", 66), BRAND.get("material_targeted_footer_height", 66))
            elif isinstance(child, (QLineEdit, QComboBox, QDoubleSpinBox)):
                child.setProperty("targetedInputRole", "material_editor_field")
                _set_height(child, BRAND.get("material_targeted_field_height", 38), None)
            elif isinstance(child, QTableView):
                child.setProperty("targetedTableRole", "material_units_grid")
                child.setMinimumHeight(int(BRAND.get("material_targeted_units_table_min_height", 250)))
            elif isinstance(child, QAbstractButton):
                _mark_button(child, "material")
        except Exception:
            continue


def _apply_dashboard(root: QWidget) -> None:
    try:
        root.setProperty("dashboardTargetedRebuildPhase", TARGETED_SCREEN_REBUILD_PHASE)
        root.setProperty("dashboardLayoutIntent", "kpi_shortcuts_cashbox_identity")
    except Exception:
        pass
    for child in root.findChildren(QWidget):
        try:
            role = str(child.property("dashboardPanelRole") or "")
            if role:
                child.setProperty("targetedCardRole", f"dashboard_{role}")
                child.setProperty("dashboardTargetedRebuildPhase", TARGETED_SCREEN_REBUILD_PHASE)
            if isinstance(child, QAbstractButton) and child.property("visualRole") == "dashboard_shortcut":
                child.setProperty("targetedActionRole", "dashboard_shortcut")
                child.setProperty("dashboardTargetedRebuildPhase", TARGETED_SCREEN_REBUILD_PHASE)
        except Exception:
            continue


def apply_targeted_screen_rebuild(root: QWidget | None, page_id: str = "", workspace_type: str = "") -> None:
    """Apply Phase455 targeted rebuild roles to known screenshot-problem screens."""
    if root is None:
        return
    family = _classify(root, page_id, workspace_type)
    try:
        root.setProperty("targetedScreenRebuildPhase", TARGETED_SCREEN_REBUILD_PHASE)
        root.setProperty("targetedScreenRebuildFamily", family)
        root.setProperty("visualStyleSource", "targeted_screen_rebuild_phase455")
    except Exception:
        pass

    if family == "login":
        _apply_login(root)
    elif family == "pos":
        _apply_pos(root)
    elif family == "invoice":
        _apply_invoice(root)
    elif family == "material":
        _apply_material(root)
    elif family == "dashboard":
        _apply_dashboard(root)

    _polish(root)
    try:
        QTimer.singleShot(0, lambda: _polish(root))
        QTimer.singleShot(180, lambda: _polish(root))
    except Exception:
        pass


__all__ = ["TARGETED_SCREEN_REBUILD_PHASE", "apply_targeted_screen_rebuild"]
