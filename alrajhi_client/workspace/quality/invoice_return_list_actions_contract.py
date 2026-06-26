# -*- coding: utf-8 -*-
"""Phase 387 contract for invoice/return list Edit/Delete actions.

The contract is intentionally import-light.  It documents the runtime guarantees
for list-level actions on sales invoices, purchase invoices, sales returns and
purchase returns.
"""
from __future__ import annotations

INVOICE_RETURN_LIST_ACTION_PHASE = 387

INVOICE_ACTION_TARGETS = (
    "sales_invoices",
    "purchase_invoices",
)

RETURN_ACTION_TARGETS = (
    "sales_returns",
    "purchase_returns",
)

REQUIRED_ACTION_GUARANTEES = (
    "selection_resolves_source_row",
    "edit_uses_current_selected_id",
    "delete_uses_current_selected_id",
    "proxy_filtered_tables_map_to_source_model",
    "toolbar_buttons_track_selection_changed",
    "permissions_gate_edit_and_delete",
    "linked_invoice_dependencies_block_delete_before_confirmation",
    "current_list_refreshes_after_delete",
)


def contract_summary() -> dict:
    return {
        "phase": INVOICE_RETURN_LIST_ACTION_PHASE,
        "invoice_targets": INVOICE_ACTION_TARGETS,
        "return_targets": RETURN_ACTION_TARGETS,
        "guarantees": REQUIRED_ACTION_GUARANTEES,
    }


__all__ = [
    "INVOICE_RETURN_LIST_ACTION_PHASE",
    "INVOICE_ACTION_TARGETS",
    "RETURN_ACTION_TARGETS",
    "REQUIRED_ACTION_GUARANTEES",
    "contract_summary",
]
