# -*- coding: utf-8 -*-
"""Phase 427 contract: direct QTableWidget editable-surface sweep.

The Phase426 Enter fix lives in StandardTableKeyboardMixin.  Any editable
surface that bypasses EditableSmartGrid can still clear destination cells via a
local QTableWidget/editor path.  This contract classifies direct QTableWidget
construction and requires either migration to EditableSmartGrid or explicit
read-only status.
"""
from __future__ import annotations

import ast
from pathlib import Path

PHASE427_DIRECT_QTABLEWIDGET_EDITABLE_SWEEP = {
    "phase": 427,
    "name": "Direct QTableWidget Editable Surface Sweep",
    "owner": "EditableSmartGrid / StandardTableKeyboardMixin",
    "purpose": "No editable production table may bypass the unified Enter policy.",
    "runtime_rule": "Editable QTableWidget surfaces must be EditableSmartGrid; direct QTableWidget is allowed only for explicitly read-only display matrices.",
}

READONLY_DIRECT_QTABLEWIDGET_SURFACES = {
    "alrajhi_client/views/apparel/apparel_workspace_widget.py": {
        "report_table": "read-only apparel report output",
        "matrix_table": "read-only apparel color/size matrix output",
    },
}

MIGRATED_EDITABLE_SURFACES = {
    "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py": {
        "invoice_table": "restaurant simple POS invoice grid migrated to EditableSmartGrid",
    },
    "alrajhi_client/views/widgets/settings_widget.py": {
        "settings_surface_columns_table": "settings column contract surface migrated to EditableSmartGrid and made read-only at cell level",
    },
}

WRAPPER_QTABLEWIDGET_FILES = {
    "alrajhi_client/ui/editable_smart_grid.py",
}


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _assigned_name(node: ast.AST) -> str:
    if isinstance(node, ast.Assign) and node.targets:
        target = node.targets[0]
    elif isinstance(node, ast.AnnAssign):
        target = node.target
    else:
        return ""
    if isinstance(target, ast.Attribute):
        return target.attr
    if isinstance(target, ast.Name):
        return target.id
    return ""


def _has_no_edit_triggers(text: str, variable: str) -> bool:
    needles = (
        f".{variable}.setEditTriggers(QTableWidget.NoEditTriggers)",
        f".{variable}.setEditTriggers(EditableSmartGrid.NoEditTriggers)",
        f".{variable}.setEditTriggers(self.{variable}.NoEditTriggers)",
        f"{variable}.setEditTriggers(QTableWidget.NoEditTriggers)",
        f"{variable}.setEditTriggers(EditableSmartGrid.NoEditTriggers)",
        f"{variable}.setEditTriggers({variable}.NoEditTriggers)",
        ".setEditTriggers(QTableWidget.NoEditTriggers)",
        ".setEditTriggers(EditableSmartGrid.NoEditTriggers)",
    )
    return any(needle in text for needle in needles) or "NoEditTriggers" in text


def direct_qtablewidget_surface_matrix(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    client = root / "alrajhi_client"
    for path in sorted(client.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError as exc:
            rows.append({
                "path": rel,
                "line": "0",
                "surface": "syntax",
                "status": "FAIL",
                "detail": str(exc),
            })
            continue
        if rel in WRAPPER_QTABLEWIDGET_FILES:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                value = node.value if isinstance(node, ast.Assign) else node.value
                if not isinstance(value, ast.Call) or _call_name(value.func) != "QTableWidget":
                    continue
                variable = _assigned_name(node) or "<unknown>"
                allowed_readonly = variable in READONLY_DIRECT_QTABLEWIDGET_SURFACES.get(rel, {}) and _has_no_edit_triggers(text, variable)
                migrated_expected = variable in MIGRATED_EDITABLE_SURFACES.get(rel, {})
                if allowed_readonly:
                    status = "OK"
                    detail = READONLY_DIRECT_QTABLEWIDGET_SURFACES[rel][variable]
                elif migrated_expected:
                    status = "FAIL"
                    detail = "surface is expected to be migrated to EditableSmartGrid but still constructs QTableWidget"
                else:
                    status = "FAIL"
                    detail = "direct QTableWidget construction is not classified as read-only; migrate to EditableSmartGrid"
                rows.append({
                    "path": rel,
                    "line": str(getattr(node, "lineno", 0)),
                    "surface": variable,
                    "status": status,
                    "detail": detail,
                })
    return rows


def direct_qtablewidget_editable_sweep_summary(root: Path) -> dict[str, object]:
    rows = direct_qtablewidget_surface_matrix(root)
    failures = [row for row in rows if row["status"] != "OK"]
    restaurant = (root / "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py").read_text(encoding="utf-8", errors="ignore")
    settings = (root / "alrajhi_client/views/widgets/settings_widget.py").read_text(encoding="utf-8", errors="ignore")
    source_failures: list[str] = []
    if "self.invoice_table = EditableSmartGrid" not in restaurant:
        source_failures.append("restaurant_simple_pos_widget.invoice_table is not EditableSmartGrid")
    if "self.invoice_table = QTableWidget" in restaurant:
        source_failures.append("restaurant_simple_pos_widget.invoice_table still constructs QTableWidget")
    if "SelectedClicked" in restaurant:
        source_failures.append("restaurant_simple_pos_widget still opens editors through SelectedClicked")
    if "self.settings_surface_columns_table = EditableSmartGrid" not in settings:
        source_failures.append("settings_surface_columns_table is not EditableSmartGrid")
    if "self.settings_surface_columns_table = QTableWidget" in settings:
        source_failures.append("settings_surface_columns_table still constructs QTableWidget")
    if "settings_surface_columns_table.setEditTriggers(EditableSmartGrid.NoEditTriggers)" not in settings:
        source_failures.append("settings surface column table is not explicitly read-only")
    failures.extend({"path": "source", "line": "0", "surface": "marker", "status": "FAIL", "detail": msg} for msg in source_failures)
    return {
        "phase": 427,
        "ready": not failures,
        "direct_surfaces": len(rows),
        "failures": failures,
    }
