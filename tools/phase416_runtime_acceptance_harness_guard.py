# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

OUT = ROOT / "tools" / "audit_outputs" / "runtime_acceptance_harness_matrix.csv"
SCENARIO_OUT = ROOT / "tools" / "audit_outputs" / "runtime_acceptance_scenario_matrix.csv"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def add(rows: list[dict[str, str]], key: str, category: str, path: str, ok: bool, detail: str) -> None:
    rows.append({
        "key": key,
        "category": category,
        "path": path,
        "status": "OK" if ok else "FAIL",
        "detail": detail,
    })


def main() -> int:
    rows: list[dict[str, str]] = []
    required = [
        "PHASE416_RUNTIME_ACCEPTANCE_HARNESS.md",
        "alrajhi_client/workspace/runtime/runtime_acceptance_harness.py",
        "alrajhi_client/workspace/quality/runtime_acceptance_harness_contract.py",
        "tools/phase416_runtime_acceptance_harness_guard.py",
        "tools/run_phase416_runtime_acceptance.py",
        "tests/test_phase416_runtime_acceptance_harness.py",
    ]
    for rel in required:
        add(rows, f"exists::{rel}", "file", rel, (ROOT / rel).exists(), "required Phase416 file exists")

    harness_path = "alrajhi_client/workspace/runtime/runtime_acceptance_harness.py"
    contract_path = "alrajhi_client/workspace/quality/runtime_acceptance_harness_contract.py"
    release_path = "alrajhi_client/workspace/quality/release_gate_contract.py"
    cli_path = "tools/run_phase416_runtime_acceptance.py"

    harness = read(harness_path)
    contract = read(contract_path)
    release = read(release_path)
    cli = read(cli_path)

    add(rows, "pyqt_import_safe", "runtime", harness_path, "from PyQt5" not in harness.split("def _require_pyqt", 1)[0], "PyQt imports are delayed until runtime probe functions")
    add(rows, "scenario_matrix", "runtime", harness_path, "PHASE416_SCENARIOS" in harness and "runtime_acceptance_scenarios" in harness and "write_scenario_matrix" in harness, "scenario matrix is available without Qt")
    add(rows, "widget_tree_capture", "runtime", harness_path, "collect_widget_tree" in harness and "RuntimeWidgetSnapshotRow" in harness and "object_name" in harness and "layout_direction" in harness, "widget tree captures identity, geometry and direction")
    add(rows, "shell_snapshot_analysis", "runtime", harness_path, "analyze_shell_snapshot" in harness and "CleanShellNavigationBar" in harness and "top_left_candidates" in harness, "shell snapshot checks clean shell and top-left candidates")
    add(rows, "rtl_ltr_shell_probes", "runtime", harness_path, "run_shell_snapshot_probe" in harness and "language: str = \"ar\"" in harness and "shell_snapshot_{language}.png" in harness, "shell probes support language-specific screenshots")
    add(rows, "qtest_grid_probe", "runtime", harness_path, "run_sales_invoice_enter_probe" in harness and "QTest.keyClick" in harness and "Qt.Key_Return" in harness, "sales invoice probe uses real QTest key events")
    add(rows, "value_preservation_probe", "runtime", harness_path, "value_preserved" in harness and "value_before == value_after" in harness, "grid runtime probe checks Enter does not clear values")
    add(rows, "single_trailing_row_probe", "runtime", harness_path, "trailing_empty_count" in harness and "trailing_empty <= 1" in harness, "grid runtime probe checks duplicate trailing rows")
    add(rows, "all_available_probe_runner", "runtime", harness_path, "run_all_available_runtime_probes" in harness and "runtime_acceptance_probe_summary.json" in harness, "manual runner can execute every available runtime probe")

    add(rows, "contract_phase", "contract", contract_path, "RUNTIME_ACCEPTANCE_HARNESS_CONTRACT" in contract and "\"phase\": 416" in contract, "contract identifies Phase416")
    add(rows, "contract_runtime_requirements", "contract", contract_path, "QWidget trees" in contract and "QTest.keyClick" in contract and "scenario matrix" in contract, "contract documents runtime evidence requirements")

    add(rows, "cli_sets_client_path", "tool", cli_path, "sys.path.insert" in cli and "alrajhi_client" in cli, "manual runtime CLI runs from project root")
    add(rows, "cli_invokes_all_probes", "tool", cli_path, "run_all_available_runtime_probes" in cli and "--output-dir" in cli, "manual CLI invokes runtime harness")

    add(rows, "release_gate_doc", "release", release_path, "PHASE416_RUNTIME_ACCEPTANCE_HARNESS" in release, "Phase416 doc registered in release gate")
    add(rows, "release_gate_test", "release", release_path, "tests/test_phase416_runtime_acceptance_harness.py" in release, "Phase416 test registered in release gate")
    add(rows, "release_gate_check", "release", release_path, "runtime_acceptance_harness" in release and "phase=416" in release, "Phase416 release check registered")

    from workspace.runtime.runtime_acceptance_harness import write_scenario_matrix, scenario_matrix_rows, pyqt_runtime_status  # noqa: E402
    scenario_rows = scenario_matrix_rows()
    write_scenario_matrix(SCENARIO_OUT)
    add(rows, "scenario_count", "output", str(SCENARIO_OUT), len(scenario_rows) >= 10, f"scenario rows={len(scenario_rows)}")
    add(rows, "pyqt_status_explicit", "output", str(SCENARIO_OUT), "runtime_probe_possible" in pyqt_runtime_status(), "PyQt runtime availability is reported explicitly")
    add(rows, "scenario_output_written", "output", str(SCENARIO_OUT), SCENARIO_OUT.exists(), "scenario matrix output is written")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["key", "category", "path", "status", "detail"])
        writer.writeheader()
        writer.writerows(rows)

    failed = [row for row in rows if row["status"] != "OK"]
    print(f"Phase416 runtime acceptance harness checks: {len(rows)} checks, failures={len(failed)}")
    for row in failed:
        print(f"FAIL {row['key']}: {row['detail']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
