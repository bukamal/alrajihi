# -*- coding: utf-8 -*-
"""Phase376 voucher list master-detail inline editor contract.

The vouchers surface must follow the same list/detail structure as customer and
supplier surfaces. Receipt, payment, and expense add/edit actions remain inside
this list widget and must not spawn new workspace tabs.
"""

PHASE = 376
CONTRACT_NAME = "voucher_master_detail_inline"

REQUIRED_WIDGET_MARKERS = (
    "ResponsiveMasterDetail",
    "DetailPlaceholder",
    "detail_stack",
    "inline_editor_page",
    "inline_editor_host",
    "_update_detail_preview",
    "_show_inline_voucher_editor",
)

REQUIRED_INLINE_TYPES = ("receipt", "payment", "expense")
FORBIDDEN_WORKSPACE_ROUTES = ("open_quick_voucher", "open_document_tab", "open_tab")
