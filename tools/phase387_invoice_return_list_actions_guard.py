#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 387 guard: invoice/return list Edit/Delete actions stay wired."""
from __future__ import annotations

import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "tools" / "audit_outputs" / "invoice_return_list_actions_matrix.csv"

CHECKS = []


def add_check(name: str, ok: bool, detail: str) -> None:
    CHECKS.append({"check": name, "ok": bool(ok), "detail": detail})


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def main() -> int:
    invoices = read("alrajhi_client/views/widgets/invoices_widget.py")
    returns = read("alrajhi_client/views/widgets/returns_widget.py")
    translator = read("alrajhi_client/i18n/translator.py")
    quality = read("alrajhi_client/workspace/quality/invoice_return_list_actions_contract.py")

    add_check("invoice edit/delete toolbar signals", "editRequested.connect(lambda: self.edit_selected_invoice('sale'))" in invoices and "deleteRequested.connect(lambda: self.delete_selected_invoice('purchase'))" in invoices, "sales and purchase toolbar actions are wired")
    add_check("invoice source row mapping", "def _source_row_from_index(self, inv_type, index):" in invoices and "proxy.mapToSource(index)" in invoices, "invoice double-click and selected row map through proxy")
    add_check("invoice selected source row helper", "def _selected_invoice_source_row(self, inv_type):" in invoices and "table.selected_source_rows()" in invoices, "invoice selected row uses SmartTableView source-row helper")
    add_check("invoice source model helper", "def _source_model_for_invoice_type(self, inv_type):" in invoices and "source_model" in invoices, "invoice id resolution reads the source model")
    add_check("invoice valid selection gates buttons", "has_valid_selection = self._selected_invoice_id(inv_type) is not None" in invoices and "set_edit_enabled" in invoices and "set_delete_enabled" in invoices, "invoice Edit/Delete buttons follow actual selected id")
    add_check("invoice edit opens document", "def _open_invoice_editor" in invoices and "main.open_quick_invoice(inv_type, invoice_id=inv_id)" in invoices, "invoice edit opens the correct sale/purchase document")
    add_check("invoice delete dependency blocks", "has_linked_vouchers(inv_id)" in invoices and "has_linked_returns(inv_id)" in invoices, "invoice delete checks vouchers and returns before confirmation")
    add_check("invoice delete refreshes current list", "self.refresh_tab(inv_type, reset_page=True)" in invoices, "invoice delete refreshes only the affected list")
    add_check("invoice linked returns translation", "delete_invoice_linked_returns_message" in translator, "linked-return delete block message is translated")

    add_check("return toolbar signals", returns.count("self.toolbar.editRequested.connect(self.edit_selected)") >= 2 and returns.count("self.toolbar.deleteRequested.connect(self.cancel_selected)") >= 2, "sales and purchase return toolbar actions are wired")
    add_check("return selection signal", returns.count("selectionChanged.connect(self._update_return_actions)") >= 2 and returns.count("def _connect_table_selection(self):") >= 2, "return action buttons follow selection changes")
    add_check("return no blind click enable", "clicked.connect(lambda *_: self.toolbar.set_delete_enabled(True))" not in returns and "clicked.connect(lambda *_: self.toolbar.set_edit_enabled(True))" not in returns, "return buttons are not blindly enabled on click")
    add_check("return source row mapping", returns.count("def _source_row_from_index(self, index):") >= 2 and returns.count("proxy.mapToSource(index)") >= 2, "return double-click and selection map through proxy")
    add_check("return selected id guarded", returns.count("if not hasattr(self, 'model'):") >= 2, "return actions are safe before the first model is loaded")
    add_check("return permissions", "permission_service.ACTION_EDIT_RETURNS" in returns and "permission_service.ACTION_DELETE" in returns, "return edit/delete actions honor permissions")
    add_check("return missing selection feedback", "show_toast(translate('select_return_first')" in returns, "return edit/delete show feedback when no row is selected")

    add_check("quality contract", "INVOICE_RETURN_LIST_ACTION_PHASE = 387" in quality and "linked_invoice_dependencies_block_delete_before_confirmation" in quality, "quality contract documents Phase 387")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "ok", "detail"])
        writer.writeheader()
        writer.writerows(CHECKS)

    failed = [row for row in CHECKS if not row["ok"]]
    if failed:
        print(f"Phase 387 invoice/return action guard FAILED: {len(failed)} issue(s)")
        for row in failed:
            print(f"- {row['check']}: {row['detail']}")
        return 1
    print(f"Phase 387 invoice/return action guard passed: {len(CHECKS)} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
