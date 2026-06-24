# -*- coding: utf-8 -*-
"""Phase375 inline editor contract for parties and finance vouchers.

Customer/supplier list pages and the vouchers list page must open add/edit
surfaces inside the same tab.  The legacy workspace-tab routes remain available
from global shortcuts and dashboards, but list-local Add/Edit actions are not
allowed to spawn a new workspace tab.
"""
from __future__ import annotations

INLINE_PARTY_VOUCHER_EDITOR_PHASE = 375

INLINE_LIST_WIDGETS = (
    "alrajhi_client/views/widgets/customers_widget.py",
    "alrajhi_client/views/widgets/suppliers_widget.py",
    "alrajhi_client/views/widgets/vouchers_widget.py",
)

INLINE_EDITOR_MARKERS = {
    "customers": ("PartyInlineEditorHostMixin", "_install_party_inline_host", "_show_inline_party_editor"),
    "suppliers": ("PartyInlineEditorHostMixin", "_install_party_inline_host", "_show_inline_party_editor"),
    "vouchers": ("UnifiedInlineWorkspaceMixin", "_install_unified_inline_workspace", "_show_inline_voucher_editor", "VoucherEditorTab", "ExpenseDocumentTab"),
}

FORBIDDEN_LIST_ROUTE_CALLS = {
    "customers": ("open_party_document",),
    "suppliers": ("open_party_document",),
    "vouchers": ("open_quick_voucher",),
}

VOUCHER_INLINE_TYPES = ("receipt", "payment", "expense")

__all__ = [
    "INLINE_PARTY_VOUCHER_EDITOR_PHASE",
    "INLINE_LIST_WIDGETS",
    "INLINE_EDITOR_MARKERS",
    "FORBIDDEN_LIST_ROUTE_CALLS",
    "VOUCHER_INLINE_TYPES",
]
