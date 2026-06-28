#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
from pathlib import Path
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "tools" / "audit_outputs" / "basit_final_acceptance_matrix.csv"
OUT_MD = ROOT / "tools" / "audit_outputs" / "basit_final_acceptance_report.md"

REQUIRED_PHASES = tuple(range(401, 410))

CHECKS: tuple[tuple[str, str, str, str], ...] = (
    # Phase409 artifacts.
    ("phase409_contract", "acceptance", "alrajhi_client/workspace/quality/basit_final_acceptance_contract.py", "BASIT_FINAL_ACCEPTANCE_CONTRACT"),
    ("phase409_doc", "acceptance", "PHASE409_BASIT_FINAL_ACCEPTANCE_AUDIT.md", "Phase409"),
    ("phase409_test", "acceptance", "tests/test_phase409_basit_final_acceptance_audit.py", "test_basit_final_acceptance"),
    ("phase409_tool", "acceptance", "tools/phase409_basit_final_acceptance_audit.py", "basit_final_acceptance_matrix.csv"),
    # Contracts produced by the Basit conversion stack.
    ("phase401_contract", "contracts", "alrajhi_client/workspace/quality/basit_visual_system_contract.py", "BASIT_VISUAL_SYSTEM_CONTRACT"),
    ("phase402_contract", "contracts", "alrajhi_client/workspace/quality/basit_dashboard_surface_contract.py", "BASIT_DASHBOARD_SURFACE_CONTRACT"),
    ("phase403_contract", "contracts", "alrajhi_client/workspace/quality/basit_transaction_surface_contract.py", "BASIT_TRANSACTION_SURFACE_CONTRACT"),
    ("phase404_contract", "contracts", "alrajhi_client/workspace/quality/basit_management_surface_contract.py", "BASIT_MANAGEMENT_SURFACE_CONTRACT"),
    ("phase405_contract", "contracts", "alrajhi_client/workspace/quality/basit_reports_settings_surface_contract.py", "BASIT_REPORTS_SETTINGS_SURFACE_CONTRACT"),
    ("phase406_contract", "contracts", "alrajhi_client/workspace/quality/basit_shell_chrome_contract.py", "BASIT_SHELL_CHROME_CONTRACT"),
    ("phase407_contract", "contracts", "alrajhi_client/workspace/quality/basit_startup_dialogs_surface_contract.py", "BASIT_STARTUP_DIALOGS_SURFACE_CONTRACT"),
    ("phase408_contract", "contracts", "alrajhi_client/workspace/quality/basit_printing_surface_contract.py", "BASIT_PRINTING_SURFACE_CONTRACT"),
    # Central theme and QSS markers.
    ("palette_blue", "theme", "alrajhi_client/theme/brand.py", "BASIT_BLUE = '#0076D7'"),
    ("palette_yellow", "theme", "alrajhi_client/theme/brand.py", "BASIT_YELLOW = '#F2D21B'"),
    ("palette_red", "theme", "alrajhi_client/theme/brand.py", "BASIT_RED = '#D93600'"),
    ("metrics", "theme", "alrajhi_client/theme/brand.py", "basit_toolbar_height"),
    ("qss_phase401", "qss", "alrajhi_client/theme/qss.py", "Phase401: Basit inspired operational skin"),
    ("qss_phase403", "qss", "alrajhi_client/theme/qss.py", "Phase403: Basit-inspired invoices and returns"),
    ("qss_phase404", "qss", "alrajhi_client/theme/qss.py", "Phase404: Basit-inspired management/list workspaces"),
    ("qss_phase405", "qss", "alrajhi_client/theme/qss.py", "Phase405: Basit-inspired reports and settings surfaces"),
    ("qss_phase406", "qss", "alrajhi_client/theme/qss.py", "Phase406: Basit-inspired shell chrome fallback"),
    ("qss_phase407", "qss", "alrajhi_client/theme/qss.py", "Phase407: Basit-inspired startup, login, activation and dialogs"),
    # Runtime property hooks.
    ("restaurant_root", "runtime", "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py", "basitInspired"),
    ("dashboard_root", "runtime", "alrajhi_client/views/widgets/dashboard_widget.py", "basitInspired"),
    ("transaction_root", "runtime", "alrajhi_client/features/transactions/transaction_document_tab.py", "basitTransactionDocument"),
    ("transaction_grid", "runtime", "alrajhi_client/features/transactions/transaction_document_tab.py", "basitTransactionGrid"),
    ("management_base", "runtime", "alrajhi_client/views/widgets/base_widget.py", "basitManagementWorkspace"),
    ("management_table", "runtime", "alrajhi_client/views/widgets/base_widget.py", "basitManagementTable"),
    ("reports_root", "runtime", "alrajhi_client/views/widgets/reports_widget.py", "basitReportsSurface"),
    ("settings_root", "runtime", "alrajhi_client/views/widgets/settings_widget.py", "basitSettingsSurface"),
    ("shell_menu", "runtime", "alrajhi_client/views/main_window.py", "basitShellChrome"),
    ("shell_action_bar", "runtime", "alrajhi_client/shell/unified_action_bar.py", "basitShellChrome"),
    ("shell_tabs", "runtime", "alrajhi_client/shell/tab_workspace.py", "basitShellTabs"),
    ("startup_splash", "runtime", "alrajhi_client/views/splash_screen.py", "basitStartupSurface"),
    # Printing bridge.
    ("print_token_bridge", "printing", "alrajhi_client/printing/print_templates.py", "def _basit_print_tokens"),
    ("print_phase_marker", "printing", "alrajhi_client/printing/print_templates.py", "Phase408: Basit-inspired print/export surface"),
    ("print_final_total", "printing", "alrajhi_client/printing/print_templates.py", ".totals-table tr.final td"),
    # Release gate registration.
    ("release_doc_409", "release_gate", "alrajhi_client/workspace/quality/release_gate_contract.py", "PHASE409_BASIT_FINAL_ACCEPTANCE_AUDIT"),
    ("release_test_409", "release_gate", "alrajhi_client/workspace/quality/release_gate_contract.py", "basit_final_acceptance_audit"),
    ("release_check_409", "release_gate", "alrajhi_client/workspace/quality/release_gate_contract.py", "basit_final_acceptance"),
)


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def _status(rel: str, needle: str) -> bool:
    return exists(rel) and needle in read(rel)


def _phase_artifact_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for phase in REQUIRED_PHASES:
        doc_ok = any(ROOT.glob(f"PHASE{phase}_*.md"))
        test_ok = any((ROOT / "tests").glob(f"test_phase{phase}_*.py"))
        guard_ok = any((ROOT / "tools").glob(f"phase{phase}_*.py"))
        for kind, ok in (("doc", doc_ok), ("test", test_ok), ("guard", guard_ok)):
            rows.append({
                "check": f"phase{phase}_{kind}",
                "category": "phase_artifacts",
                "path": f"PHASE{phase}_* / tests/test_phase{phase}_* / tools/phase{phase}_*",
                "needle": kind,
                "status": "OK" if ok else "FAIL",
            })
    return rows


def _write_report(rows: Iterable[dict[str, str]]) -> None:
    rows = list(rows)
    total = len(rows)
    failed = [row for row in rows if row["status"] != "OK"]
    categories: dict[str, tuple[int, int]] = {}
    for row in rows:
        ok, count = categories.get(row["category"], (0, 0))
        categories[row["category"]] = (ok + (1 if row["status"] == "OK" else 0), count + 1)
    lines = [
        "# Phase409 Basit Final Acceptance Report",
        "",
        f"Total checks: {total}",
        f"Passed: {total - len(failed)}",
        f"Failed: {len(failed)}",
        "",
        "## Category summary",
        "",
    ]
    for category, (ok, count) in sorted(categories.items()):
        lines.append(f"- {category}: {ok}/{count} OK")
    lines.extend(["", "## Result", "", "READY" if not failed else "NOT READY", ""])
    if failed:
        lines.extend(["## Failures", ""])
        for row in failed:
            lines.append(f"- {row['check']}: missing `{row['needle']}` in `{row['path']}`")
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    rows: list[dict[str, str]] = []
    for name, category, rel, needle in CHECKS:
        ok = _status(rel, needle)
        rows.append({
            "check": name,
            "category": category,
            "path": rel,
            "needle": needle,
            "status": "OK" if ok else "FAIL",
        })
    rows.extend(_phase_artifact_rows())
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "category", "path", "needle", "status"])
        writer.writeheader()
        writer.writerows(rows)
    _write_report(rows)
    failures = [row for row in rows if row["status"] != "OK"]
    if failures:
        print("Phase409 Basit final acceptance audit failed:")
        for row in failures:
            print(f"- {row['check']}: missing {row['needle']!r} in {row['path']}")
        print(f"Audit report: {OUT_MD.relative_to(ROOT)}")
        return 1
    print(f"Phase409 Basit final acceptance audit OK ({len(rows)} checks)")
    print(f"Audit report: {OUT_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
