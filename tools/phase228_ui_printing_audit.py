# -*- coding: utf-8 -*-
"""Phase 228 project-wide UI/printing audit.

Audits the exact UX decisions requested in Phase 228:
- dashboard KPI/chart removal
- global top search removal
- duplicate shell action reduction
- centralized HTML printing boundary
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
OUT_DIR = ROOT / "tools" / "audit_outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_PRINTING_FILES = {
    "alrajhi_client/printing/printing_service.py",
    "alrajhi_client/printing/print_manager.py",
    "alrajhi_client/printing/thermal_printer.py",
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def scan_text(patterns: List[str], include=("alrajhi_client",)) -> List[Dict[str, object]]:
    findings: List[Dict[str, object]] = []
    for base in include:
        for path in (ROOT / base).rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for lineno, line in enumerate(text.splitlines(), 1):
                for pattern in patterns:
                    if pattern in line:
                        findings.append({"file": rel(path), "line": lineno, "pattern": pattern, "text": line.strip()})
    return findings


def audit() -> Dict[str, object]:
    findings: List[Dict[str, object]] = []

    dashboard = read("alrajhi_client/views/widgets/dashboard_widget.py")
    if "self._build_kpi_grid()" in dashboard:
        findings.append({"severity": "high", "area": "dashboard", "message": "Dashboard still builds the removed KPI/chart section."})
    if "DashboardChartPanel(" in dashboard or "ModernKpiCard(" in dashboard:
        findings.append({"severity": "high", "area": "dashboard", "message": "Dashboard still instantiates top KPI cards or the chart panel."})

    topbar = read("alrajhi_client/views/modern_topbar.py")
    if "QLineEdit()" in topbar or "GlobalSearchBox" in topbar or "utility_layout.addWidget(self.search_box" in topbar:
        findings.append({"severity": "high", "area": "topbar", "message": "Global search widget is still present in ModernTopBar."})
    if "self.refresh_btn = QToolButton()" in topbar:
        findings.append({"severity": "medium", "area": "buttons", "message": "Refresh button still exists in the topbar and duplicates UnifiedActionBar."})

    main_window = read("alrajhi_client/views/main_window.py")
    if ".search_box.textChanged" in main_window or ".search_box.returnPressed" in main_window:
        findings.append({"severity": "high", "area": "topbar", "message": "MainWindow still wires the removed global search widget."})

    printing = read("alrajhi_client/printing/printing_service.py")
    if "def render_html(" not in printing:
        findings.append({"severity": "high", "area": "printing", "message": "PrintingService lacks the central render_html dispatcher."})

    direct_print_patterns = ["QPrintDialog", "QPrintPreviewDialog", "QPrinter(", "QTextDocument()", ".setHtml("]
    for item in scan_text(direct_print_patterns):
        if item["file"] not in ALLOWED_PRINTING_FILES and not str(item["file"]).startswith("alrajhi_client/printing/"):
            findings.append({"severity": "medium", "area": "printing-boundary", "message": "Direct Qt printing/rendering outside printing package.", **item})

    # Duplicate action surfaces: document shells are allowed to have local save/print
    # actions, but they should remain concentrated in shell classes, not every random widget.
    duplicate_button_patterns = ["QPushButton(translate('print'", "QPushButton(tr('print'", "QPushButton(translate(\"print\"", "print_btn = QPushButton"]
    duplicate_candidates = scan_text(duplicate_button_patterns, include=("alrajhi_client/views", "alrajhi_client/features"))
    for item in duplicate_candidates:
        f = str(item["file"])
        if "dialogs/login_dialog" in f or "dialogs/change_password" in f:
            continue
        findings.append({"severity": "low", "area": "button-duplication", "message": "Potential local print button; prefer workspace/action-shell or document shell print menu.", **item})

    summary: Dict[str, int] = {}
    for finding in findings:
        summary[finding["severity"]] = summary.get(finding["severity"], 0) + 1

    opinion = [
        "Dashboard simplification is correct: the removed KPI/chart layer was visually heavy and duplicated deeper reports.",
        "The global top search should stay removed; page-local search is clearer and less surprising in an ERP shell.",
        "Printing is now mostly centralized around HTML via printing_service, but the remaining thermal/barcode internals should stay isolated in the printing package only.",
        "The next UX cleanup should standardize document-shell action placement: one top-level workspace action bar plus one local document bottom bar, not scattered print/save buttons.",
    ]
    return {"summary": summary, "findings": findings, "opinion": opinion}


def main() -> None:
    result = audit()
    json_path = OUT_DIR / "phase228_ui_printing_audit.json"
    md_path = OUT_DIR / "PHASE228_UI_PRINTING_AUDIT.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Phase 228 UI / Printing Audit", "", "## Summary"]
    for key in ("high", "medium", "low"):
        lines.append(f"- {key}: {result['summary'].get(key, 0)}")
    lines += ["", "## Opinion"]
    for item in result["opinion"]:
        lines.append(f"- {item}")
    lines += ["", "## Findings"]
    for f in result["findings"][:120]:
        loc = f.get("file", "")
        line = f.get("line")
        where = f"{loc}:{line}" if loc and line else str(loc or "project")
        lines.append(f"- [{f['severity']}] {f['area']} — {f['message']} ({where})")
    if len(result["findings"]) > 120:
        lines.append(f"- ... {len(result['findings']) - 120} more findings in JSON")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
