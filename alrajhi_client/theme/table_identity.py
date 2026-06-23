# -*- coding: utf-8 -*-
"""Phase 355: branded table and transaction-footer identity contract.

PyQt-free contract for the visual language used by editable/list tables and
invoice-like footer/action strips.  Runtime widgets consume these object names,
properties and token keys through the global QSS rather than local ad-hoc
styles.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence

TABLE_IDENTITY_PHASE = 355


@dataclass(frozen=True)
class TableVisualTokenSpec:
    key: str
    role: str
    description: str


@dataclass(frozen=True)
class TableRuntimeMarker:
    key: str
    marker: str
    category: str
    description: str


REQUIRED_TABLE_TOKEN_KEYS: Sequence[str] = (
    "table_current_bg",
    "table_current_border",
    "table_current_text",
    "table_focus_ring",
    "table_header_line",
    "table_row_hover_bg",
    "transaction_footer_surface",
    "transaction_footer_summary_bg",
    "transaction_footer_summary_border",
    "transaction_footer_label",
    "transaction_footer_value",
    "transaction_footer_primary_bg",
    "transaction_footer_secondary_bg",
    "transaction_footer_close_bg",
)

TABLE_VISUAL_TOKENS: Sequence[TableVisualTokenSpec] = (
    TableVisualTokenSpec("table_current_bg", "table", "Background for the exact active editable cell."),
    TableVisualTokenSpec("table_current_border", "table", "Border/indicator for the current cell."),
    TableVisualTokenSpec("table_current_text", "table", "Readable text color inside the current editable cell."),
    TableVisualTokenSpec("table_focus_ring", "table", "Secondary focus ring for editors embedded inside grids."),
    TableVisualTokenSpec("table_header_line", "table", "Thin identity accent under table headers."),
    TableVisualTokenSpec("table_row_hover_bg", "table", "Soft hover surface for dense accounting rows."),
    TableVisualTokenSpec("transaction_footer_surface", "transaction", "Outer transaction footer panel surface."),
    TableVisualTokenSpec("transaction_footer_summary_bg", "transaction", "Summary/payment strip surface."),
    TableVisualTokenSpec("transaction_footer_summary_border", "transaction", "Summary/payment strip border."),
    TableVisualTokenSpec("transaction_footer_label", "transaction", "Footer label/caption color."),
    TableVisualTokenSpec("transaction_footer_value", "transaction", "Footer financial value color."),
    TableVisualTokenSpec("transaction_footer_primary_bg", "transaction", "Primary bottom command button color."),
    TableVisualTokenSpec("transaction_footer_secondary_bg", "transaction", "Secondary bottom command button surface."),
    TableVisualTokenSpec("transaction_footer_close_bg", "transaction", "Close/cancel button neutral surface."),
)

REQUIRED_TABLE_OBJECT_MARKERS: Sequence[TableRuntimeMarker] = (
    TableRuntimeMarker("table_property", "brand_table_surface", "runtime", "Custom/Smart tables opt in to branded table QSS."),
    TableRuntimeMarker("entry_table_property", "brand_entry_table", "runtime", "Editable transaction grids expose a stronger current-cell profile."),
    TableRuntimeMarker("transaction_grid_name", "TransactionLineGrid", "runtime", "Transaction document line grid keeps a stable object name."),
    TableRuntimeMarker("footer_panel", "TransactionFooterPanel", "footer", "Invoice-like documents expose the unified footer panel."),
    TableRuntimeMarker("summary_frame", "TransactionHorizontalSummaryFrame", "footer", "Totals frame is horizontally branded."),
    TableRuntimeMarker("payment_frame", "TransactionHorizontalPaymentFrame", "footer", "Payment frame uses same summary visual system."),
    TableRuntimeMarker("bottom_actions", "TransactionBottomActionBar", "footer", "Bottom command buttons are a unified action surface."),
    TableRuntimeMarker("action_role", "transaction_action", "footer", "Buttons carry semantic action roles for QSS."),
)

REQUIRED_TABLE_QSS_MARKERS: Sequence[str] = (
    "Phase355: branded table surface and active editable cell",
    "Phase355: branded transaction footer and bottom commands",
    "brand_table_surface",
    "brand_entry_table",
    "table_current_bg",
    "transaction_footer_primary_bg",
)


def validate_table_identity_tokens(tokens: Mapping[str, str]) -> Dict[str, List[str]]:
    issues: Dict[str, List[str]] = {}
    for key in REQUIRED_TABLE_TOKEN_KEYS:
        value = str(tokens.get(key, "")).strip()
        if not value:
            issues.setdefault("missing_tokens", []).append(key)
    return issues


def table_identity_matrix(tokens: Mapping[str, str] | None = None) -> List[Dict[str, object]]:
    token_map = tokens or {}
    rows: List[Dict[str, object]] = []
    for spec in TABLE_VISUAL_TOKENS:
        rows.append({
            "kind": "token",
            "key": spec.key,
            "role": spec.role,
            "description": spec.description,
            "present": spec.key in token_map if token_map else True,
        })
    for marker in REQUIRED_TABLE_OBJECT_MARKERS:
        rows.append({
            "kind": marker.category,
            "key": marker.key,
            "role": marker.category,
            "description": marker.description,
            "marker": marker.marker,
            "present": True,
        })
    return rows


__all__ = [
    "TABLE_IDENTITY_PHASE",
    "TableVisualTokenSpec",
    "TableRuntimeMarker",
    "REQUIRED_TABLE_TOKEN_KEYS",
    "TABLE_VISUAL_TOKENS",
    "REQUIRED_TABLE_OBJECT_MARKERS",
    "REQUIRED_TABLE_QSS_MARKERS",
    "validate_table_identity_tokens",
    "table_identity_matrix",
]
