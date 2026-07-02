# -*- coding: utf-8 -*-
"""Phase 349 PyQt-free contract for transaction entry, cash party, and footer polish."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Phase349Check:
    code: str
    area: str
    title: str
    path: str
    ok: bool
    detail: str = ""


def phase349_checks(root: Path | None = None) -> List[Phase349Check]:
    base = root or ROOT

    def exists(path: str) -> bool:
        return (base / path).exists()

    def read(path: str) -> str:
        return (base / path).read_text(encoding="utf-8")

    checks: List[Phase349Check] = []

    keyboard = "alrajhi_client/ui/table_keyboard_policy.py"
    keyboard_text = read(keyboard) if exists(keyboard) else ""
    checks.extend([
        Phase349Check(
            "current_cell_property",
            "keyboard",
            "Editable grids expose a current-cell visual highlight property",
            keyboard,
            "current_cell_highlight" in keyboard_text and "standard_table_keyboard" in keyboard_text,
        ),
        Phase349Check(
            "entry_grid_selects_current_cell",
            "keyboard",
            "Entry-grid focus selects the current cell, not only a row",
            keyboard,
            "QItemSelectionModel.ClearAndSelect" in keyboard_text and "SelectItems" in keyboard_text,
        ),
        Phase349Check(
            "editor_default_clear_preserved",
            "keyboard",
            "Default editor tokens still clear on Enter while real values select all",
            keyboard,
            "_standard_prepare_active_editor" in keyboard_text and "editor.clear()" not in keyboard_text and "selectAll()" in keyboard_text,
        ),
    ])

    qss = "alrajhi_client/theme/qss.py"
    qss_text = read(qss) if exists(qss) else ""
    checks.extend([
        Phase349Check(
            "current_cell_qss",
            "visual",
            "QSS paints the active editable cell with a distinct border/background",
            qss,
            "current_cell_highlight" in qss_text and "current_cell_bg" in qss_text and "current_cell_border" in qss_text,
        ),
        Phase349Check(
            "footer_summary_qss",
            "visual",
            "Transaction footer summary/payment panels have unified typography",
            qss,
            "TransactionHorizontalSummaryFrame" in qss_text and "TransactionSummaryValue" in qss_text and "transaction_footer_value_font_px" in qss_text,
        ),
        Phase349Check(
            "bottom_actions_qss",
            "visual",
            "Bottom transaction action buttons are larger and role-styled",
            qss,
            "TransactionBottomActionBar" in qss_text and "transaction_action" in qss_text and "transaction_footer_action_min_height" in qss_text,
        ),
    ])

    brand = "alrajhi_client/theme/brand.py"
    brand_text = read(brand) if exists(brand) else ""
    checks.extend([
        Phase349Check(
            "footer_design_tokens",
            "visual",
            "Footer and bottom-button sizes use central design tokens",
            brand,
            "transaction_footer_font_px" in brand_text and "transaction_footer_action_min_height" in brand_text,
        ),
        Phase349Check(
            "current_cell_tokens",
            "visual",
            "Current-cell highlight colors are theme tokens for light/dark mode",
            brand,
            "current_cell_bg" in brand_text and "current_cell_border" in brand_text,
        ),
    ])

    doc = "alrajhi_client/features/transactions/transaction_document_tab.py"
    doc_text = read(doc) if exists(doc) else ""
    checks.extend([
        Phase349Check(
            "cash_party_default",
            "cash_party",
            "Transaction party combo defaults to Cash instead of No party",
            doc,
            "def _cash_party_label" in doc_text and "self.party_combo.addItem(self._cash_party_label(), None)" in doc_text,
        ),
        Phase349Check(
            "no_party_no_question",
            "cash_party",
            "Saving without customer/supplier is a cash document and does not ask a blocking question",
            doc,
            "transaction_save_without_party" not in doc_text and "valid cash/counter" in doc_text,
        ),
        Phase349Check(
            "returns_cash_original_label",
            "returns",
            "Return invoice helper labels also show Cash when no party is present",
            doc,
            "party or self._cash_party_label()" in doc_text,
        ),
    ])

    totals = "alrajhi_client/features/transactions/components/transaction_totals_panel.py"
    totals_text = read(totals) if exists(totals) else ""
    checks.extend([
        Phase349Check(
            "footer_label_object_names",
            "visual",
            "Totals/payment labels expose object names for unified styling",
            totals,
            "TransactionSummaryCaption" in totals_text and "TransactionSummaryValue" in totals_text and "TransactionPaymentCaption" in totals_text,
        ),
        Phase349Check(
            "footer_button_object_names",
            "visual",
            "Footer mini buttons are named and sized consistently",
            totals,
            "TransactionFooterMiniButton" in totals_text and "setMinimumWidth(98)" in totals_text,
        ),
    ])

    actions = "alrajhi_client/features/transactions/components/transaction_bottom_actions.py"
    actions_text = read(actions) if exists(actions) else ""
    checks.extend([
        Phase349Check(
            "bottom_action_roles",
            "actions",
            "Bottom action buttons expose semantic transaction_action roles",
            actions,
            "setProperty(\"transaction_action\", action_name)" in actions_text and "TransactionBottomActionBar" in actions_text,
        ),
        Phase349Check(
            "bottom_action_size",
            "actions",
            "Bottom actions are larger and clearer by default",
            actions,
            "setMinimumHeight(44)" in actions_text and "setMinimumWidth(108)" in actions_text,
        ),
    ])

    return checks


def phase349_issues(root: Path | None = None) -> List[Phase349Check]:
    return [check for check in phase349_checks(root) if not check.ok]


__all__ = ["Phase349Check", "phase349_checks", "phase349_issues"]
