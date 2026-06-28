# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import csv
import importlib.util
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def _load_contract():
    path = ROOT / "alrajhi_client" / "workspace" / "quality" / "runtime_acceptance_harness_contract.py"
    spec = importlib.util.spec_from_file_location("phase416_runtime_acceptance_harness_contract", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_phase416_contract_documents_runtime_scope():
    module = _load_contract()
    contract = module.RUNTIME_ACCEPTANCE_HARNESS_CONTRACT
    assert contract["phase"] == 416
    assert contract["name"] == "runtime_acceptance_harness"
    assert "views.main_window CleanShellNavigationBar runtime geometry" in contract["scope"]
    assert any("QWidget trees" in item for item in contract["requirements"])
    assert module.runtime_acceptance_harness_summary(ROOT)["ready"] is True


def test_phase416_sources_parse_without_pyqt_runtime():
    for rel in (
        "alrajhi_client/workspace/runtime/runtime_acceptance_harness.py",
        "alrajhi_client/workspace/quality/runtime_acceptance_harness_contract.py",
        "tools/phase416_runtime_acceptance_harness_guard.py",
        "tools/run_phase416_runtime_acceptance.py",
    ):
        ast.parse(read(rel))


def test_phase416_harness_imports_without_pyqt_and_exposes_scenarios():
    from workspace.runtime.runtime_acceptance_harness import (  # noqa: E402
        pyqt_runtime_status,
        runtime_acceptance_scenarios,
        scenario_matrix_rows,
    )
    status = pyqt_runtime_status()
    assert "runtime_probe_possible" in status
    scenarios = runtime_acceptance_scenarios()
    assert len(scenarios) >= 10
    keys = {scenario.key for scenario in scenarios}
    assert "shell_ar_rtl_snapshot" in keys
    assert "shell_de_ltr_snapshot" in keys
    assert "sales_invoice_enter_route" in keys
    assert "sales_invoice_value_preservation" in keys
    rows = scenario_matrix_rows()
    assert len(rows) == len(scenarios)
    assert all("pyqt_runtime_status" in row for row in rows)


def test_phase416_widget_snapshot_analysis_detects_legacy_and_clean_shell():
    from workspace.runtime.runtime_acceptance_harness import RuntimeWidgetSnapshotRow, analyze_shell_snapshot  # noqa: E402
    clean_only = [
        RuntimeWidgetSnapshotRow("MainWindow/CleanShellNavigationBar", "CleanShellNavigationBar", "CleanShellNavigationBar", True, True, 0, 0, 1400, 48, "RTL"),
        RuntimeWidgetSnapshotRow("MainWindow/MainNavButton", "QPushButton", "MainNavButton", True, True, 20, 6, 110, 34, "RTL"),
    ]
    assert analyze_shell_snapshot(clean_only)["ok"] is True
    dirty = clean_only + [
        RuntimeWidgetSnapshotRow("MainWindow/ModernTopBar", "ModernTopBar", "ModernTopBar", True, True, 0, 0, 200, 40, "RTL"),
    ]
    result = analyze_shell_snapshot(dirty)
    assert result["ok"] is False
    assert result["visible_old_shell_count"] == 1


def test_phase416_harness_contains_real_qtest_and_screenshot_hooks():
    harness = read("alrajhi_client/workspace/runtime/runtime_acceptance_harness.py")
    assert "def run_shell_snapshot_probe" in harness
    assert "window.grab().save" in harness
    assert "collect_widget_tree" in harness
    assert "def run_sales_invoice_enter_probe" in harness
    assert "QTest.keyClick" in harness
    assert "Qt.Key_Return" in harness
    assert "value_before == value_after" in harness
    assert "trailing_empty <= 1" in harness


def test_phase416_guard_runs_and_writes_matrices():
    result = subprocess.run(
        [sys.executable, "tools/phase416_runtime_acceptance_harness_guard.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    matrix = ROOT / "tools" / "audit_outputs" / "runtime_acceptance_harness_matrix.csv"
    scenario_matrix = ROOT / "tools" / "audit_outputs" / "runtime_acceptance_scenario_matrix.csv"
    assert matrix.exists()
    assert scenario_matrix.exists()
    rows = list(csv.DictReader(matrix.open(encoding="utf-8")))
    scenario_rows = list(csv.DictReader(scenario_matrix.open(encoding="utf-8")))
    assert rows
    assert scenario_rows
    assert {row["status"] for row in rows} == {"OK"}


def test_phase416_manual_cli_matrix_only_runs_without_pyqt():
    result = subprocess.run(
        [sys.executable, "tools/run_phase416_runtime_acceptance.py", "--matrix-only", "--output-dir", "tools/audit_outputs/runtime_acceptance_cli_test"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    assert "runtime_probe_possible" in result.stdout
    assert (ROOT / "tools" / "audit_outputs" / "runtime_acceptance_cli_test" / "runtime_acceptance_scenario_matrix.csv").exists()


def test_phase416_release_gate_registration():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert "PHASE416_RUNTIME_ACCEPTANCE_HARNESS" in gate
    assert "tests/test_phase416_runtime_acceptance_harness.py" in gate
    assert "tools/phase416_runtime_acceptance_harness_guard.py" in gate
    assert "runtime_acceptance_harness" in gate
    assert "phase=416" in gate
