# -*- coding: utf-8 -*-
"""Guard for Phase 168 transaction document printing/export bridge."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "alrajhi_client" / "features" / "transactions" / "transaction_document_tab.py"
BRIDGE = ROOT / "alrajhi_client" / "features" / "transactions" / "components" / "transaction_printing_bridge.py"
LEGACY = ROOT / "alrajhi_client" / "views" / "dialogs" / "invoice_dialog.py"


def _class_methods(path: Path, class_name: str) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {m.name for m in node.body if isinstance(m, ast.FunctionDef)}
    raise AssertionError(f"{class_name} not found in {path}")


def main() -> None:
    assert BRIDGE.exists(), "transaction_printing_bridge.py is missing"
    bridge_methods = _class_methods(BRIDGE, "TransactionPrintingBridge")
    for name in {"preview", "print", "browser", "pdf", "_invoice_payload", "_return_payload"}:
        assert name in bridge_methods, f"missing bridge method: {name}"

    tab_methods = _class_methods(TAB, "TransactionDocumentTab")
    for name in {"workspace_print", "workspace_export", "_preview_document", "_ensure_saved_for_output"}:
        assert name in tab_methods, f"TransactionDocumentTab must implement {name}"

    text = TAB.read_text(encoding="utf-8")
    assert "TransactionPrintingBridge" in text, "TransactionDocumentTab does not use the printing bridge"
    assert "PDF" in text and "معاينة" in text, "bottom action bar lacks print/export commands"

    legacy_text = LEGACY.read_text(encoding="utf-8")
    assert "TransactionPrintingBridge" not in legacy_text, "legacy invoice_dialog.py must not own Phase 168 printing bridge"
    print("phase168_transaction_printing_guard: passed")


if __name__ == "__main__":
    main()
