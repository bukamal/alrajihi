# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "audit_outputs" / "basit_transaction_surface_matrix.csv"

CHECKS = [
    ("contract_exists", "alrajhi_client/workspace/quality/basit_transaction_surface_contract.py", "BASIT_TRANSACTION_SURFACE_CONTRACT"),
    ("document_root_tagged", "alrajhi_client/features/transactions/transaction_document_tab.py", 'self.setProperty("basitTransactionDocument", True)'),
    ("document_inspired_tagged", "alrajhi_client/features/transactions/transaction_document_tab.py", 'self.setProperty("basitInspired", True)'),
    ("header_toolbar_tagged", "alrajhi_client/features/transactions/transaction_document_tab.py", 'inline_header.setProperty("basitToolbar", True)'),
    ("grid_basit_table", "alrajhi_client/features/transactions/transaction_document_tab.py", 'self.grid.setProperty("basitTable", True)'),
    ("grid_transaction_role", "alrajhi_client/features/transactions/transaction_document_tab.py", 'self.grid.setProperty("basitTransactionGrid", True)'),
    ("footer_basit_total", "alrajhi_client/features/transactions/transaction_document_tab.py", 'self.side_panel.setProperty("basitTotalFooter", True)'),
    ("toolbar_buttons", "alrajhi_client/features/transactions/transaction_document_tab.py", 'setProperty("basitToolbarButton", True)'),
    ("summary_basit_panel", "alrajhi_client/features/transactions/components/transaction_totals_panel.py", 'self.summary_frame.setProperty("basitTransactionSummary", True)'),
    ("payment_basit_panel", "alrajhi_client/features/transactions/components/transaction_totals_panel.py", 'self.payment_frame.setProperty("basitTransactionPayment", True)'),
    ("net_total_basit", "alrajhi_client/features/transactions/components/transaction_totals_panel.py", 'widget.setProperty("basitTotal", title_key == "transaction_net_total")'),
    ("qss_phase_marker", "alrajhi_client/theme/qss.py", "Phase403: Basit-inspired invoices and returns"),
    ("qss_toolbar", "alrajhi_client/theme/qss.py", 'QFrame#TransactionInlineHeaderBar[basitToolbar="true"]'),
    ("qss_transaction_grid", "alrajhi_client/theme/qss.py", 'QTableView[basitTransactionGrid="true"]'),
    ("qss_net_total", "alrajhi_client/theme/qss.py", 'QLabel#TransactionSummaryValue[basitTotal="true"]'),
]


def main() -> int:
    rows = []
    issues = []
    for name, rel, needle in CHECKS:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        ok = needle in text
        rows.append({"check": name, "path": rel, "needle": needle, "status": "OK" if ok else "FAIL"})
        if not ok:
            issues.append(f"{name}: missing {needle!r} in {rel}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "path", "needle", "status"])
        writer.writeheader()
        writer.writerows(rows)
    if issues:
        print("Phase403 Basit transaction surface guard failed:")
        for issue in issues:
            print("-", issue)
        return 1
    print(f"Phase403 Basit transaction surface guard OK ({len(rows)} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
