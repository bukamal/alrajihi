#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Project-wide architecture/UX audit for the tab-document migration.

This audit is intentionally non-fatal for known legacy areas. It produces a
machine-readable JSON report and a Markdown summary under tools/audit_outputs/.
It fails only for critical regressions that route primary workflows back to
large legacy dialogs.
"""
from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
OUT_DIR = ROOT / "tools" / "audit_outputs"
OUT_DIR.mkdir(exist_ok=True)

LARGE_LEGACY_DIALOGS = {
    "InvoiceDialog",
    "AddEntityDialog",
    "ItemDialog",
    "BOMDialog",
    "ProductionOrderDialog",
    "ProductionDetailsDialog",
    "VoucherDialog",
    "SalesReturnDialog",
    "PurchaseReturnDialog",
    "BranchDialog",
    "CashboxDialog",
    "BankDialog",
    "UserDialog",
}

ALLOWED_DIALOG_CONTEXT_HINTS = (
    "login", "activation", "password", "barcode_camera", "column", "customizer",
    "batch_print", "quick_open", "filedialog", "qmessagebox", "qinputdialog",
)

@dataclass
class Finding:
    severity: str
    area: str
    file: str
    line: int
    title: str
    detail: str
    recommendation: str


def py_files() -> Iterable[Path]:
    for p in CLIENT.rglob("*.py"):
        if "__pycache__" not in p.parts:
            yield p


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def classify_dialog_file(path: Path) -> str:
    low = str(path).lower()
    if any(h in low for h in ALLOWED_DIALOG_CONTEXT_HINTS):
        return "allowed-small-dialog"
    if "views/dialogs" in str(path) or "views/widgets" in str(path):
        return "legacy-large-dialog-candidate"
    return "dialog-usage"


def collect_findings() -> list[Finding]:
    findings: list[Finding] = []
    for p in py_files():
        rel = p.relative_to(ROOT).as_posix()
        txt = p.read_text(encoding="utf-8", errors="ignore")

        # Large legacy dialog direct references outside fallback-friendly areas.
        for name in LARGE_LEGACY_DIALOGS:
            if name in txt:
                # Imports/instantiation in dashboard are critical after Phase 216.
                sev = "high" if "views/widgets/dashboard_widget.py" in rel else "medium"
                # Definitions themselves are not critical, but mark as legacy inventory.
                if re.search(rf"class\s+{re.escape(name)}\b", txt):
                    sev = "inventory"
                findings.append(Finding(
                    severity=sev,
                    area="legacy-dialog",
                    file=rel,
                    line=line_number(txt, txt.find(name)),
                    title=f"Legacy dialog reference: {name}",
                    detail="Large modal dialog is still present or referenced. Some references may be explicit fallback paths.",
                    recommendation="Primary workflows should open DocumentTab/MainWindow open_* methods. Keep only explicit Legacy*/fallback or small utility dialogs.",
                ))

        # QDialog classes in widgets/features: likely not aligned with document tabs.
        for m in re.finditer(r"class\s+(\w+)\s*\([^)]*QDialog[^)]*\)", txt):
            cls = m.group(1)
            sev = "medium"
            if classify_dialog_file(p) == "allowed-small-dialog":
                sev = "low"
            findings.append(Finding(
                severity=sev,
                area="qdialog-class",
                file=rel,
                line=line_number(txt, m.start()),
                title=f"QDialog class: {cls}",
                detail="Class inherits QDialog. This may be acceptable for small utility dialogs, but CRUD/document screens should be tabs.",
                recommendation="If this is CRUD/document/edit workflow, migrate to BaseDocumentTab; otherwise document it as allowed utility dialog.",
            ))

        # Direct exec() in widgets/features can bypass tabs.
        for m in re.finditer(r"\.exec_?\s*\(", txt):
            if "views/dialogs" in rel or "printing" in rel or "login" in rel.lower():
                continue
            findings.append(Finding(
                severity="medium",
                area="dialog-exec",
                file=rel,
                line=line_number(txt, m.start()),
                title="Dialog exec() call",
                detail="Modal dialog execution detected outside low-level dialog modules.",
                recommendation="Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.",
            ))

        # QSettings in features/views except settings widget/login legacy.
        if "QSettings" in txt and ("features/" in rel or "views/widgets/" in rel):
            if "settings_widget.py" not in rel and "login_dialog.py" not in rel:
                findings.append(Finding(
                    severity="medium",
                    area="settings-boundary",
                    file=rel,
                    line=line_number(txt, txt.find("QSettings")),
                    title="Direct QSettings in UI/feature layer",
                    detail="UI/feature layer should use settings_service/preferences wrappers, not QSettings directly.",
                    recommendation="Move persistence to settings_service or a scoped preferences helper using user/branch/profile.",
                ))

        # Direct database/gateway imports inside views/features.
        if ("features/" in rel or "views/widgets/" in rel) and re.search(r"from\s+(database|gateways)\b|import\s+(database|gateways)\b", txt):
            findings.append(Finding(
                severity="high",
                area="service-boundary",
                file=rel,
                line=1,
                title="UI/feature imports database/gateway directly",
                detail="Business UI should depend on core.services, not DAO/gateway/database modules.",
                recommendation="Route through a service contract and local/remote gateways below the service layer.",
            ))

    # Explicit structural checks for screens mentioned by the user.
    targeted = {
        "party-editor": CLIENT / "features" / "parties" / "party_editor_tab.py",
        "voucher-editor": CLIENT / "features" / "vouchers" / "voucher_editor_tab.py",
        "expense-document": CLIENT / "features" / "finance" / "documents" / "expense_document_tab.py",
    }
    for area, path in targeted.items():
        rel = path.relative_to(ROOT).as_posix()
        txt = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        if "BaseDocumentTab" not in txt and "VoucherEditorTab" not in txt:
            findings.append(Finding("high", area, rel, 1, "Not a BaseDocumentTab", "Targeted document is not based on BaseDocumentTab or an approved BaseDocumentTab-derived document.", "Convert to DocumentTab."))
        # These are tabs but not aligned with TransactionDocument visual shell.
        if area == "voucher-editor" and "DocumentHeaderCard" not in txt and "BottomActionBar" not in txt:
            findings.append(Finding(
                severity="high",
                area=area,
                file=rel,
                line=1,
                title="Document tab is still form-stack, not professional document shell",
                detail="The screen uses panels/forms but lacks the same header/body/summary/bottom-action shell used in transaction documents.",
                recommendation="Refactor into FinanceDocumentTab shell: header, party/payment panels, linked invoice grid/context, totals/status side panel, bottom actions.",
            ))
        if area == "expense-document" and "VoucherEditorTab" not in txt and "ExpenseDocumentHeaderCard" not in txt:
            findings.append(Finding(
                severity="high",
                area=area,
                file=rel,
                line=1,
                title="Expense document lacks a finance document shell",
                detail="ExpenseDocumentTab must either inherit the unified voucher finance shell or provide its own expense-specific document shell.",
                recommendation="Keep ExpenseDocumentTab on the finance document shell or provide ExpenseDocumentHeaderCard/ExpenseSummaryPanel/ExpenseBottomActionBar.",
            ))
        if area == "party-editor" and "QTabWidget" in txt and "Bottom" not in txt:
            findings.append(Finding(
                severity="medium",
                area=area,
                file=rel,
                line=1,
                title="Party editor is a tabbed form, not full master-data document shell",
                detail="Customer/supplier document has basic form and context tabs, but lacks shared MasterDataDocumentTab shell and bottom actions.",
                recommendation="Refactor into PartyDocumentShell with header, identity/contact/credit panels, statement/invoices/vouchers grid area, and bottom action bar.",
            ))

    return findings


def main() -> int:
    findings = collect_findings()
    counts: dict[str, int] = {}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1

    data = {
        "summary": counts,
        "finding_count": len(findings),
        "findings": [asdict(f) for f in findings],
    }
    (OUT_DIR / "phase219_projectwide_architecture_audit.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Phase 219 — Project-wide Architecture / UX Audit",
        "",
        "## Summary",
        "",
    ]
    for k in sorted(counts):
        lines.append(f"- {k}: {counts[k]}")
    lines.extend([
        "",
        "## Critical interpretation",
        "",
        "The project has largely moved to tab-based documents, but several screens are technically tabs while still being form-stack UI rather than the professional document shell used for transactions.",
        "PartyEditorTab was refactored in Phase 220, VoucherEditorTab in Phase 221, and ExpenseDocumentTab in Phase 222 into its own expense-specific finance document shell.",
        "",
        "## Findings",
        "",
    ])
    for f in findings:
        if f.severity in {"high", "medium"}:
            lines.append(f"### [{f.severity}] {f.title}")
            lines.append(f"- File: `{f.file}:{f.line}`")
            lines.append(f"- Area: `{f.area}`")
            lines.append(f"- Detail: {f.detail}")
            lines.append(f"- Recommendation: {f.recommendation}")
            lines.append("")
    (OUT_DIR / "PHASE219_PROJECTWIDE_ARCHITECTURE_AUDIT.md").write_text("\n".join(lines), encoding="utf-8")

    # Fatal regressions: dashboard must not directly instantiate large legacy dialogs.
    critical = [f for f in findings if f.severity == "high" and f.file.endswith("dashboard_widget.py") and f.area == "legacy-dialog"]
    if critical:
        for f in critical:
            print(f"CRITICAL: {f.file}:{f.line}: {f.title}")
        return 1
    print(json.dumps(data["summary"], ensure_ascii=False, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
