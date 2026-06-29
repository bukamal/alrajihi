# -*- coding: utf-8 -*-
"""Canonical visual layout policy for ERP document editors.

Phase 381 defines three editor families and one runtime policy function so
inline hosts, standalone tabs, and future editors do not drift visually:

* card_form: simple master data cards such as customer, supplier, user,
  branch, warehouse, cashbox, bank account, category and material.
* financial_document: voucher/expense documents with form panels and a money
  summary panel.
* tabular_document: invoice/return/transfer/manufacturing documents whose
  primary workspace is a line grid.

The policy is intentionally structural: it sets inspectable widget properties,
adjusts margins/size policies, suppresses duplicate title cards in inline mode,
and normalizes known splitter/grid proportions without performing any data
access.
"""
from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QAbstractItemView, QComboBox, QDateEdit, QDoubleSpinBox, QFrame, QGroupBox,
    QLabel, QLineEdit, QPushButton, QSizePolicy, QSplitter, QSpinBox, QTabWidget,
    QTextEdit, QWidget,
)

try:
    from .document_contract import CURRENCY_NONE
except Exception:  # pragma: no cover - imported by tooling without package context
    CURRENCY_NONE = "none"

KIND_CARD_FORM = "card_form"
KIND_FINANCIAL_DOCUMENT = "financial_document"
KIND_TABULAR_DOCUMENT = "tabular_document"

CARD_FORM_TYPES = frozenset({
    "material",
    "category",
    "customer",
    "supplier",
    "cashbox",
    "bank_account",
    "warehouse",
    "branch",
    "user",
    "settings",
    "settings_section",
})
FINANCIAL_DOCUMENT_TYPES = frozenset({"voucher", "expense", "receipt", "payment"})
TABULAR_DOCUMENT_TYPES = frozenset({
    "sales_invoice",
    "purchase_invoice",
    "sales_return",
    "purchase_return",
    "warehouse_transfer",
    "inventory_transfer",
    "bom",
    "production_order",
    "production_order_details",
})

HEADER_OBJECT_NAMES = frozenset({
    "DocumentHeaderCard",
    "ExpenseDocumentHeaderCard",
    "TransactionHeaderCard",
    "DocumentTitleCard",
})
TITLE_LABEL_ATTRS = (
    "title_label",
    "subtitle_label",
)


def infer_document_layout_kind(widget: QWidget, explicit: Optional[str] = None) -> str:
    """Return the canonical layout family for a document widget."""
    if explicit in {KIND_CARD_FORM, KIND_FINANCIAL_DOCUMENT, KIND_TABULAR_DOCUMENT}:
        return explicit

    state = getattr(widget, "document_state", None)
    document_type = str(getattr(state, "document_type", "") or "").strip()
    descriptor = getattr(widget, "document_descriptor", None)

    if document_type in TABULAR_DOCUMENT_TYPES:
        return KIND_TABULAR_DOCUMENT
    if document_type in FINANCIAL_DOCUMENT_TYPES:
        return KIND_FINANCIAL_DOCUMENT
    if document_type in CARD_FORM_TYPES:
        return KIND_CARD_FORM

    try:
        if bool(getattr(getattr(descriptor, "capabilities", None), "grid_layout", False)):
            return KIND_TABULAR_DOCUMENT
    except Exception:
        pass
    try:
        currency_policy = str(getattr(descriptor, "currency_policy", CURRENCY_NONE) or CURRENCY_NONE)
        if currency_policy != CURRENCY_NONE:
            return KIND_FINANCIAL_DOCUMENT
    except Exception:
        pass
    return KIND_CARD_FORM


def _layout(widget: QWidget):
    try:
        return widget.layout()
    except Exception:
        return None


def _set_layout_margins(widget: QWidget, *, inline: bool, kind: str) -> None:
    layout = _layout(widget)
    if layout is None:
        return
    if inline:
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8 if kind == KIND_CARD_FORM else 10)
    else:
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)


def _set_common_properties(widget: QWidget, *, kind: str, inline: bool) -> None:
    try:
        widget.setProperty("documentLayoutKind", kind)
        widget.setProperty("documentInlineMode", bool(inline))
        widget.setProperty("documentLayoutManaged", True)
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    except Exception:
        pass


def _hide_duplicate_inline_headers(widget: QWidget) -> None:
    """Hide local title/header surfaces inside inline editors.

    The outer inline workspace already supplies context and back navigation, so
    embedded editors should not repeat a second title card.  This is defensive
    and works for frame-based headers and simple title-label headers.
    """
    for attr in TITLE_LABEL_ATTRS:
        child = getattr(widget, attr, None)
        if child is not None and hasattr(child, "setVisible"):
            try:
                child.setVisible(False)
            except Exception:
                pass

    try:
        frames = widget.findChildren(QFrame)
    except Exception:
        frames = []
    for frame in frames:
        try:
            if frame.objectName() in HEADER_OBJECT_NAMES:
                frame.setVisible(False)
        except Exception:
            pass


def _configure_card_form(widget: QWidget, *, inline: bool) -> None:
    # Card forms should read as wide forms in inline mode, not stacked dialogs.
    for obj_name in ("DocumentPanel", "FormCard", "DocumentPanelCard"):
        for child in widget.findChildren(QWidget, obj_name):
            try:
                child.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            except Exception:
                pass


def _configure_financial_document(widget: QWidget, *, inline: bool) -> None:
    # Financial documents use form panels plus a compact summary column.
    for name in ("DocumentPanel", "ExpenseDocumentPanel"):
        for child in widget.findChildren(QWidget, name):
            try:
                child.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            except Exception:
                pass
    for name in ("SummaryPanel", "ExpenseSummaryPanel"):
        for child in widget.findChildren(QWidget, name):
            try:
                child.setMinimumWidth(230 if inline else 260)
                child.setMaximumWidth(420)
                child.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
            except Exception:
                pass


def _configure_tabular_document(widget: QWidget, *, inline: bool) -> None:
    # Table/grid documents allocate most horizontal space to editable lines.
    for splitter in widget.findChildren(QSplitter):
        try:
            splitter.setChildrenCollapsible(False)
            splitter.setStretchFactor(0, 7)
            splitter.setStretchFactor(1, 2)
            QTimer.singleShot(0, lambda s=splitter: s.setSizes([980, 320]))
        except Exception:
            pass
    for table_name in ("TransactionLineGrid", "InventoryTransferLinesGrid", "BomComponentsGrid", "ProductionRequiredMaterialsGrid"):
        for child in widget.findChildren(QWidget, table_name):
            try:
                child.setMinimumHeight(360 if inline else 420)
                child.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            except Exception:
                pass
    for tabs in widget.findChildren(QTabWidget):
        try:
            tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        except Exception:
            pass



def _set_visual_role(widget: QWidget, role: str) -> None:
    try:
        if not widget.property("visualRole"):
            widget.setProperty("visualRole", role)
    except Exception:
        pass


def _apply_document_visual_template(widget: QWidget, *, kind: str) -> None:
    """Apply Phase450 document-editor visual identity roles.

    This is deliberately styling-only metadata.  It does not alter persistence,
    Enter navigation, financial calculations, printing, permissions, or data
    loading.  Central QSS consumes these roles so document editors stop relying
    on feature-local hard-coded styles.
    """
    try:
        widget.setProperty("documentVisualTemplatePhase", 450)
        widget.setProperty("projectVisualIdentityPhase", 450)
        widget.setProperty("visualWorkspaceType", "document")
        widget.setProperty("visualRole", "document_editor_surface")
    except Exception:
        pass

    header_names = {
        "DocumentHeaderCard", "ExpenseDocumentHeaderCard", "TransactionHeaderCard",
        "DocumentTitleCard", "TransactionInlineHeaderBar",
    }
    panel_names = {
        "DocumentPanel", "ExpenseDocumentPanel", "DocumentSection", "ExpenseDocumentSection",
        "FormCard", "DocumentPanelCard", "MaterialBasicCard", "MaterialPricingCard",
        "MaterialBarcodeCard", "MaterialUnitsCard",
    }
    summary_names = {
        "SummaryPanel", "ExpenseSummaryPanel", "TransactionFooterPanel",
        "BomSummaryPanel", "ProductionSummaryPanel", "MetricCard",
    }
    action_names = {
        "BottomActionBar", "ExpenseBottomActionBar", "TransactionBottomActionBar",
        "MaterialEditorActionBar", "CategoryInlineActionBar",
    }

    for child in widget.findChildren(QWidget):
        try:
            name = child.objectName() or ""
            child.setProperty("documentVisualTemplatePhase", 450)
            if name in header_names:
                _set_visual_role(child, "document_header")
            elif name in panel_names:
                _set_visual_role(child, "document_card")
            elif name in summary_names:
                _set_visual_role(child, "document_summary")
            elif name in action_names:
                _set_visual_role(child, "document_action_bar")
            elif name in {"TransactionInlineHeaderField"}:
                _set_visual_role(child, "document_header_field")
        except Exception:
            pass

    for title_name in ("DocumentTitle", "PanelTitle", "SectionTitle"):
        for label in widget.findChildren(QLabel, title_name):
            _set_visual_role(label, "document_section_title" if title_name != "DocumentTitle" else "document_title")
    for label in widget.findChildren(QLabel, "DocumentSubtitle"):
        _set_visual_role(label, "document_subtitle")
    for label in widget.findChildren(QLabel, "MetricTitle"):
        _set_visual_role(label, "document_metric_title")
    for label in widget.findChildren(QLabel, "MetricValue"):
        _set_visual_role(label, "document_metric_value")

    for table in widget.findChildren(QAbstractItemView):
        _set_visual_role(table, "document_table")

    for splitter in widget.findChildren(QSplitter):
        _set_visual_role(splitter, "document_splitter")

    input_classes = (QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QSpinBox, QTextEdit)
    for klass in input_classes:
        for field in widget.findChildren(klass):
            _set_visual_role(field, "document_input")

    for button in widget.findChildren(QPushButton):
        try:
            if button.objectName() == "primary" or button in (getattr(widget, "bottom_save_btn", None), getattr(widget, "header_save_btn", None), getattr(widget, "save_btn", None)):
                button.setProperty("visualRole", "document_primary_action")
            elif "delete" in (button.objectName() or "").lower() or "حذف" in button.text():
                button.setProperty("visualRole", "document_danger_action")
            else:
                _set_visual_role(button, "document_action")
        except Exception:
            pass

def apply_document_layout_policy(widget: QWidget, *, kind: Optional[str] = None, inline: Optional[bool] = None) -> str:
    """Apply the canonical document layout policy and return the resolved kind."""
    resolved_kind = infer_document_layout_kind(widget, kind)
    inline_mode = bool(inline if inline is not None else (widget.property("inlineEditor") or widget.property("documentInlineMode")))

    _set_common_properties(widget, kind=resolved_kind, inline=inline_mode)
    _apply_document_visual_template(widget, kind=resolved_kind)
    _set_layout_margins(widget, inline=inline_mode, kind=resolved_kind)
    if inline_mode:
        _hide_duplicate_inline_headers(widget)

    if resolved_kind == KIND_TABULAR_DOCUMENT:
        _configure_tabular_document(widget, inline=inline_mode)
    elif resolved_kind == KIND_FINANCIAL_DOCUMENT:
        _configure_financial_document(widget, inline=inline_mode)
    else:
        _configure_card_form(widget, inline=inline_mode)

    return resolved_kind


__all__ = [
    "KIND_CARD_FORM",
    "KIND_FINANCIAL_DOCUMENT",
    "KIND_TABULAR_DOCUMENT",
    "CARD_FORM_TYPES",
    "FINANCIAL_DOCUMENT_TYPES",
    "TABULAR_DOCUMENT_TYPES",
    "infer_document_layout_kind",
    "apply_document_layout_policy",
    "_apply_document_visual_template",
]
