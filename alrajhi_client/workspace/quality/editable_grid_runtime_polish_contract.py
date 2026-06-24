# -*- coding: utf-8 -*-
"""Phase 382 editable grid runtime polish contract.

The contract is intentionally source-inspection based so it can run in CI and
inside the packaged audit tools without importing PyQt.  It protects the line
entry UX rules that are easy to regress while refactoring documents:

* material/item/barcode starts the entry flow;
* barcode cells use the same item resolver as material cells;
* committing material/barcode jumps to quantity;
* add-line actions focus the newly inserted line, not the first row;
* line-entry grids use current-cell selection, while POS/touch grids may keep
  row selection locally.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

FILES = {
    "keyboard": "alrajhi_client/ui/table_keyboard_policy.py",
    "transaction_grid": "alrajhi_client/features/transactions/grids/transaction_line_grid.py",
    "transaction_doc": "alrajhi_client/features/transactions/transaction_document_tab.py",
    "inventory_doc": "alrajhi_client/features/inventory/documents/inventory_transfer_document_tab.py",
    "bom_doc": "alrajhi_client/features/manufacturing/bom_document_tab.py",
    "transaction_model": "alrajhi_client/features/transactions/grids/transaction_line_model.py",
    "inventory_model": "alrajhi_client/features/inventory/grids/inventory_transfer_lines_model.py",
    "bom_model": "alrajhi_client/features/manufacturing/grids/bom_components_model.py",
}

REQUIRED_MARKERS = {
    "keyboard": (
        "_standard_material_entry_keys",
        "_standard_barcode_entry_keys",
        "_standard_quantity_entry_keys",
        "_standard_post_commit_index",
        "focus_last_entry_column",
        "schedule_last_entry_focus",
        "material/barcode -> quantity",
    ),
    "transaction_grid": (
        "_install_item_lookup_delegate_for_column",
        'self._install_item_lookup_delegate_for_column(self.column_index("item"))',
        'self._install_item_lookup_delegate_for_column(self.column_index("barcode"))',
        "self.setSelectionBehavior(self.SelectItems)",
        "self.setSelectionMode(self.ExtendedSelection)",
    ),
    "transaction_doc": (
        "row = self.lines_model.add_empty_line()",
        "schedule_initial_entry_focus(start_edit=True, row=row)",
        "schedule_last_entry_focus(start_edit=True)",
    ),
    "inventory_doc": (
        "def _add_empty_line(self)",
        "schedule_last_entry_focus(start_edit=True)",
        "QShortcut(QKeySequence('Insert'), self, activated=self._add_empty_line)",
    ),
    "bom_doc": (
        "def _add_empty_component_line(self)",
        "schedule_last_entry_focus(start_edit=True)",
        "QShortcut(QKeySequence('Insert'), self, activated=self._add_empty_component_line)",
    ),
    "transaction_model": ("def add_empty_line", "def remove_line", "def set_item"),
    "inventory_model": ("def add_empty_line", "def remove_row", "def set_item"),
    "bom_model": ("def add_empty_line", "def remove_row", "def set_item"),
}

FORBIDDEN_MARKERS = {
    "transaction_doc": ("self.lines_model.add_empty_line()\n        self.set_dirty(True)\n        try:\n            self.grid.schedule_initial_entry_focus(start_edit=True)",),
    "inventory_doc": ("self.add_empty_btn.clicked.connect(self.model.add_empty_line)",),
    "bom_doc": ("self.add_empty_btn.clicked.connect(lambda: self.model.add_empty_line())",),
}

@dataclass(frozen=True)
class EditableGridRuntimeCheck:
    key: str
    category: str
    target: str
    status: str
    detail: str
    phase: int = 382

    def as_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "category": self.category,
            "target": self.target,
            "status": self.status,
            "detail": self.detail,
            "phase": self.phase,
        }


def _read(root: Path, rel: str) -> str:
    path = root / rel
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def editable_grid_runtime_matrix(root: Path | None = None) -> list[dict[str, object]]:
    base = root or ROOT
    rows: list[EditableGridRuntimeCheck] = []
    for key, rel in FILES.items():
        path = base / rel
        text = _read(base, rel)
        rows.append(EditableGridRuntimeCheck(
            key="file_exists",
            category="source",
            target=key,
            status="pass" if path.exists() else "fail",
            detail=rel,
        ))
        for marker in REQUIRED_MARKERS.get(key, ()):  # type: ignore[arg-type]
            rows.append(EditableGridRuntimeCheck(
                key=f"requires::{marker[:48]}",
                category="marker",
                target=key,
                status="pass" if marker in text else "fail",
                detail=marker,
            ))
        for marker in FORBIDDEN_MARKERS.get(key, ()):  # type: ignore[arg-type]
            rows.append(EditableGridRuntimeCheck(
                key=f"forbids::{marker[:48]}",
                category="regression",
                target=key,
                status="pass" if marker not in text else "fail",
                detail=marker,
            ))
    return [row.as_dict() for row in rows]


def editable_grid_runtime_summary(root: Path | None = None) -> dict[str, object]:
    rows = editable_grid_runtime_matrix(root)
    issues = [row for row in rows if row.get("status") != "pass"]
    return {
        "phase": 382,
        "checks": len(rows),
        "issues": len(issues),
        "ready": not issues,
    }
