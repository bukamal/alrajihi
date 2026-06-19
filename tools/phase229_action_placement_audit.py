# -*- coding: utf-8 -*-
"""Phase 229 document action placement audit.

The policy introduced in this phase is deliberately narrow and testable:
- document headers are informational only;
- save/print/export/close document commands live in bottom action bars and/or
  the workspace UnifiedActionBar;
- direct print rendering remains behind printing_service.render_html.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "audit_outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HEADER_ACTION_PATTERNS = [
    "header_save_btn",
    "header_print_btn",
    "header_export_btn",
    "header_refresh_btn",
    "header.addWidget(self.save_btn",
    "header.addWidget(self.close_btn",
    "title_row.addWidget(self.print_btn",
    "title_row.addWidget(self.save_btn",
    "top_row.addWidget(self.print_btn",
    "top_row.addWidget(self.save_btn",
    "top.addWidget(self.save_btn",
]

DOCUMENT_FILES = [
    "alrajhi_client/features/parties/party_editor_tab.py",
    "alrajhi_client/features/vouchers/voucher_editor_tab.py",
    "alrajhi_client/features/finance/documents/expense_document_tab.py",
    "alrajhi_client/features/items/item_editor_tab.py",
    "alrajhi_client/features/inventory/documents/inventory_transfer_document_tab.py",
    "alrajhi_client/features/inventory/documents/warehouse_document_tab.py",
    "alrajhi_client/features/branches/documents/branch_document_tab.py",
    "alrajhi_client/features/finance/documents/cashbox_document_tab.py",
    "alrajhi_client/features/finance/documents/bank_account_document_tab.py",
    "alrajhi_client/features/users/documents/user_document_tab.py",
    "alrajhi_client/features/manufacturing/bom_document_tab.py",
    "alrajhi_client/features/manufacturing/production_order_document_tab.py",
]

REQUIRED_BOTTOM_MARKERS = {
    "alrajhi_client/features/parties/party_editor_tab.py": ["BottomActionBar", "bottom_save_btn"],
    "alrajhi_client/features/vouchers/voucher_editor_tab.py": ["BottomActionBar", "bottom_save_btn", "bottom_print_btn", "bottom_export_btn"],
    "alrajhi_client/features/finance/documents/expense_document_tab.py": ["ExpenseBottomActionBar", "bottom_save_btn", "bottom_print_btn", "bottom_export_btn"],
    "alrajhi_client/features/items/item_editor_tab.py": ["BottomActionBar", "save_btn", "generate_barcode_btn"],
    "alrajhi_client/features/inventory/documents/inventory_transfer_document_tab.py": ["bottom_print_btn", "bottom_save_btn"],
    "alrajhi_client/features/manufacturing/bom_document_tab.py": ["bottom_print_btn", "bottom_save_btn"],
    "alrajhi_client/features/manufacturing/production_order_document_tab.py": ["bottom_save_btn"],
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def audit() -> Dict[str, object]:
    findings: List[Dict[str, object]] = []

    for relpath in DOCUMENT_FILES:
        path = ROOT / relpath
        if not path.exists():
            findings.append({"severity": "high", "area": "documents", "file": relpath, "message": "Expected document file is missing."})
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in HEADER_ACTION_PATTERNS:
            if pattern in text:
                findings.append({
                    "severity": "high",
                    "area": "action-placement",
                    "file": relpath,
                    "pattern": pattern,
                    "message": "Document command still appears in header/title row instead of bottom action bar.",
                })
        for marker in REQUIRED_BOTTOM_MARKERS.get(relpath, []):
            if marker not in text:
                findings.append({
                    "severity": "medium",
                    "area": "action-placement",
                    "file": relpath,
                    "pattern": marker,
                    "message": "Expected bottom action marker is missing.",
                })

    printing = read("alrajhi_client/printing/printing_service.py")
    if "def render_html(" not in printing:
        findings.append({"severity": "high", "area": "printing", "file": "alrajhi_client/printing/printing_service.py", "message": "HTML printing dispatcher is missing."})

    # Direct Qt print APIs outside the printing package remain a violation of the
    # unified HTML printing boundary.
    direct_print_patterns = ["QPrintDialog", "QPrintPreviewDialog", "QPrinter(", "QTextDocument()", ".setHtml("]
    for base in (ROOT / "alrajhi_client").rglob("*.py"):
        if "__pycache__" in base.parts:
            continue
        file_rel = rel(base)
        if file_rel.startswith("alrajhi_client/printing/"):
            continue
        text = base.read_text(encoding="utf-8", errors="ignore")
        for pattern in direct_print_patterns:
            if pattern in text:
                findings.append({
                    "severity": "medium",
                    "area": "printing-boundary",
                    "file": file_rel,
                    "pattern": pattern,
                    "message": "Direct Qt printing/rendering outside printing package.",
                })

    summary: Dict[str, int] = {}
    for finding in findings:
        summary[finding["severity"]] = summary.get(finding["severity"], 0) + 1

    opinion = [
        "The clean rule is now: header = identity/context, bottom bar = local document actions, UnifiedActionBar = workspace-level shortcuts.",
        "The remaining risk is not function but consistency: dialogs and lifecycle operation screens may still carry contextual buttons that should be treated separately from save/print/export document commands.",
        "HTML printing should stay centralized; thermal/barcode internals may remain specialized inside the printing package only.",
    ]
    return {"summary": summary, "findings": findings, "opinion": opinion}


def main() -> None:
    result = audit()
    json_path = OUT_DIR / "phase229_action_placement_audit.json"
    md_path = OUT_DIR / "PHASE229_ACTION_PLACEMENT_AUDIT.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Phase 229 Action Placement Audit", "", "## Summary"]
    for key in ("high", "medium", "low"):
        lines.append(f"- {key}: {result['summary'].get(key, 0)}")
    lines += ["", "## Opinion"]
    for item in result["opinion"]:
        lines.append(f"- {item}")
    lines += ["", "## Findings"]
    if result["findings"]:
        for finding in result["findings"][:120]:
            loc = finding.get("file", "project")
            pattern = finding.get("pattern")
            suffix = f" pattern={pattern!r}" if pattern else ""
            lines.append(f"- [{finding['severity']}] {finding['area']} — {finding['message']} ({loc}{suffix})")
        if len(result["findings"]) > 120:
            lines.append(f"- ... {len(result['findings']) - 120} more findings in JSON")
    else:
        lines.append("- No action-placement violations.")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
