# -*- coding: utf-8 -*-
"""Static contract for Phase384 dashboard/table runtime polish.

The contract intentionally validates source-level UX invariants that previously
regressed visually at runtime: dashboard label backgrounds, the monitoring
shortcut row, table-cell centering, and Enter commit/traversal behavior.
"""
from __future__ import annotations

from pathlib import Path

FILES = {
    "dashboard": "alrajhi_client/views/widgets/dashboard_widget.py",
    "dashboard_components": "alrajhi_client/views/widgets/dashboard_legacy_components.py",
    "keyboard": "alrajhi_client/ui/table_keyboard_policy.py",
    "visual_polish": "alrajhi_client/ui/runtime_visual_polish.py",
    "editable_grid": "alrajhi_client/ui/editable_smart_grid.py",
    "transaction_model": "alrajhi_client/features/transactions/grids/transaction_line_model.py",
    "inventory_model": "alrajhi_client/features/inventory/grids/inventory_transfer_lines_model.py",
    "bom_model": "alrajhi_client/features/manufacturing/grids/bom_components_model.py",
    "invoice_dialog": "alrajhi_client/views/dialogs/invoice_dialog.py",
}

REQUIRED_MARKERS = {
    "dashboard": (
        "background: transparent; border: 1px solid rgba(255,255,255,0.38)",
        "QLabel#CompanyLogoBox { background: transparent;",
        "QLabel#SystemBrandLogoBox {{\n                background: transparent;",
        "DashboardDailyActionButton",
        "Phase384: centered shortcut text without the legacy monitoring row.",
    ),
    "dashboard_components": ("text-align: center",),
    "keyboard": (
        "Phase384: Enter navigation must not clear existing/default values",
        "standard_enter_commit_filter",
        "editor.setAlignment(Qt.AlignCenter)",
        "self.commitData(obj)",
        "self.closeEditor(obj, QAbstractItemDelegate.NoHint)",
        "start_edit=True",
    ),
    "visual_polish": (
        "RuntimeCenterAlignDelegate",
        "option.displayAlignment = Qt.AlignCenter",
        "table.setItemDelegate(RuntimeCenterAlignDelegate(table))",
        "QTableWidget",
        "item.setTextAlignment(Qt.AlignCenter)",
        "QAbstractItemView.SelectItems",
    ),
    "editable_grid": (
        "def setItem(self, row: int, column: int, item)",
        "item.setTextAlignment(Qt.AlignCenter)",
    ),
    "transaction_model": ("if role == Qt.TextAlignmentRole:\n            return Qt.AlignCenter",),
    "inventory_model": ("if role == Qt.TextAlignmentRole:\n            return Qt.AlignCenter",),
    "bom_model": ("if role == Qt.TextAlignmentRole:\n            return Qt.AlignCenter",),
    "invoice_dialog": ("if role == Qt.TextAlignmentRole:\n            return Qt.AlignCenter",),
}

FORBIDDEN_MARKERS = {
    "dashboard": (
        "QuickActionButton(translate('monitoring_short')",
        "grid.addWidget(monitor, 3, 0, 1, 3)",
        "QLabel#StatusPill {{ color: white; background: rgba",
        "QLabel#CompanyLogoBox { background: #f8fafc;",
        "QLabel#SystemBrandLogoBox {{\n                background: #ffffff;",
    ),
    "keyboard": (
        "editor.clear()",
    ),
    "transaction_model": ("Qt.AlignRight", "Qt.AlignLeft"),
    "inventory_model": ("Qt.AlignRight", "Qt.AlignLeft"),
    "bom_model": ("Qt.AlignRight", "Qt.AlignLeft"),
    "invoice_dialog": ("Qt.AlignRight", "Qt.AlignLeft"),
}


def dashboard_table_runtime_polish_matrix(root: Path | str) -> list[dict[str, str]]:
    base = Path(root)
    rows: list[dict[str, str]] = []
    for key, rel in FILES.items():
        path = base / rel
        if not path.exists():
            rows.append({"key": key, "target": rel, "status": "fail", "detail": "missing file", "phase": "384"})
            continue
        text = path.read_text(encoding="utf-8")
        for marker in REQUIRED_MARKERS.get(key, ()):  # type: ignore[arg-type]
            rows.append({
                "key": marker,
                "target": rel,
                "status": "pass" if marker in text else "fail",
                "detail": "required marker present" if marker in text else "required marker missing",
                "phase": "384",
            })
        for marker in FORBIDDEN_MARKERS.get(key, ()):  # type: ignore[arg-type]
            rows.append({
                "key": marker,
                "target": rel,
                "status": "pass" if marker not in text else "fail",
                "detail": "forbidden marker absent" if marker not in text else "forbidden marker present",
                "phase": "384",
            })
    return rows


def dashboard_table_runtime_polish_summary(root: Path | str) -> dict[str, int | bool]:
    rows = dashboard_table_runtime_polish_matrix(root)
    issues = sum(1 for row in rows if row.get("status") != "pass")
    return {"checks": len(rows), "issues": issues, "ready": issues == 0}
