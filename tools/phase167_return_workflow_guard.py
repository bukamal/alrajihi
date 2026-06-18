from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

checks = {
    "return tools component": ROOT / "alrajhi_client/features/transactions/components/transaction_return_tools.py",
    "transaction document tab": ROOT / "alrajhi_client/features/transactions/transaction_document_tab.py",
    "transaction line model": ROOT / "alrajhi_client/features/transactions/grids/transaction_line_model.py",
}

missing = [name for name, path in checks.items() if not path.exists()]
if missing:
    raise SystemExit("Missing Phase 167 files: " + ", ".join(missing))

doc_tab = checks["transaction document tab"].read_text(encoding="utf-8")
model = checks["transaction line model"].read_text(encoding="utf-8")
component = checks["return tools component"].read_text(encoding="utf-8")

required_markers = [
    (doc_tab, "TransactionReturnTools", "TransactionDocumentTab must use TransactionReturnTools"),
    (doc_tab, "_fill_all_return_quantities", "TransactionDocumentTab must expose fill-all return action"),
    (doc_tab, "return_validation_errors", "TransactionDocumentTab must validate return base quantities before save"),
    (model, "fill_return_quantities_to_max", "TransactionLineModel must support filling return quantities"),
    (model, "clear_return_quantities", "TransactionLineModel must support clearing return quantities"),
    (model, "return_summary", "TransactionLineModel must expose return summary"),
    (model, "return_validation_errors", "TransactionLineModel must validate return quantities in base units"),
    (component, "إرجاع كامل المتاح", "Return tools must include full-return action"),
]

for content, marker, message in required_markers:
    if marker not in content:
        raise SystemExit(message)

legacy_dialog = ROOT / "alrajhi_client/views/dialogs/invoice_dialog.py"
if legacy_dialog.exists() and "Phase 167" in legacy_dialog.read_text(encoding="utf-8", errors="ignore"):
    raise SystemExit("Phase 167 must not extend legacy invoice_dialog.py")

print("Phase 167 return workflow guard passed")
