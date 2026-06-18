# -*- coding: utf-8 -*-
"""Phase 63 guard: invoice quick-entry and grid status UX.

Protects the practical invoice workflow added after enterprise table rollout:
- barcode/quick item entry has a quantity control;
- the invoice grid shows live row/status feedback;
- unresolved/invalid lines are visible in the grid instead of failing only on save;
- existing item scans increment by the quick quantity, not a hard-coded 1.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(path: str, needle: str, errors: list[str], label: str | None = None) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    if needle not in text:
        errors.append(f"{path}: missing {label or needle!r}")


def main() -> int:
    errors: list[str] = []
    invoice = "alrajhi_client/views/dialogs/invoice_dialog.py"

    for needle in [
        "InvoiceQuickQtySpin",
        "_quick_add_qty",
        "_reset_quick_add_qty",
        "self._increment_existing_line(existing_row, self._quick_add_qty())",
        "quick_qty = self._quick_add_qty()",
        "Qt.Key_F6",
        "InvoiceGridStatus",
        "update_invoice_grid_status",
        "row_validation_message",
        "invalid_rows",
        "Qt.BackgroundRole",
        "Qt.ToolTipRole",
    ]:
        require(invoice, needle, errors)

    if errors:
        print("Phase 63 invoice quick-entry guard failed:")
        for err in errors:
            print(f" - {err}")
        return 1
    print("Phase 63 invoice quick-entry guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
