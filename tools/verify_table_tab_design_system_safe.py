# -*- coding: utf-8 -*-
"""Static guard for Phase 73 table/tab design-system coverage.

This guard intentionally does not import PyQt.  It verifies that the safe QSS-only
coverage exists in the central theme and in the known local styles that otherwise
override the global application stylesheet.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = {
    "alrajhi_client/theme/qss.py": [
        "Phase 73: safe table/tab coverage",
        "QAbstractItemView",
        "QTabWidget QTableView",
        "QDialog QTableView",
        "QTabWidget QHeaderView::section",
    ],
    "alrajhi_client/views/widgets/modern_ui.py": [
        "def _modern_widget_style()",
        "ThemeManager.colors()",
        "QTableView, QTableWidget, QTreeView, QTreeWidget",
        "QTabWidget::pane",
    ],
    "alrajhi_client/views/widgets/invoices_widget.py": [
        "ThemeManager.colors()",
        "QTableView, QTableWidget",
        "QTabWidget::pane",
        "QHeaderView::section",
    ],
    "alrajhi_client/views/dialogs/invoice_dialog.py": [
        "ThemeManager.colors()",
        "QTableView, QTableWidget",
        "QHeaderView::section",
    ],
    "alrajhi_client/views/dialogs/item_dialog.py": [
        "ThemeManager.colors()",
        "QTableWidget, QTableView",
        "QHeaderView::section",
    ],
    "alrajhi_client/views/widgets/settings_widget.py": [
        "ThemeManager.colors()",
        "QTabWidget#settingsTabs",
        "QTableWidget, QTableView",
        "QHeaderView::section",
    ],
}


def main() -> int:
    missing = []
    for rel, needles in REQUIRED.items():
        path = ROOT / rel
        if not path.exists():
            missing.append(f"missing file: {rel}")
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for needle in needles:
            if needle not in text:
                missing.append(f"{rel}: missing {needle!r}")
    if missing:
        print("FAIL: table/tab design-system guard failed")
        for item in missing:
            print(" -", item)
        return 1
    print("OK: Phase 73 table/tab QSS coverage is present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
