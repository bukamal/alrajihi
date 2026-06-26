# -*- coding: utf-8 -*-
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_phase340_final_ux_regression_contract_is_pyqt_free_and_ready():
    from workspace.quality.final_ux_regression_contract import (
        REQUIRED_BARCODE_PROFILES,
        REQUIRED_TABLE_CONTRACTS,
        final_ux_regression_checks,
        final_ux_regression_summary,
    )

    source = read("alrajhi_client/workspace/quality/final_ux_regression_contract.py")
    assert "PyQt5" not in source
    assert "dashboard_minimal_action_surface" in source
    assert "barcode_profiles_multi_print_browser_html" in source
    assert "keyboard_policy_wired_to_editable_tables" in source
    assert "restaurant.order_lines" in REQUIRED_TABLE_CONTRACTS
    assert "cafe.order_lines" in REQUIRED_TABLE_CONTRACTS
    assert "apparel.variant_labels" in REQUIRED_BARCODE_PROFILES
    checks = final_ux_regression_checks()
    assert checks
    assert all(check.ok for check in checks), [check.as_row() for check in checks if not check.ok]
    summary = final_ux_regression_summary()
    assert summary["ready"] is True
    assert summary["issues"] == 0
    assert summary["checks"] >= 18


def test_phase340_guard_cli_writes_audit_outputs():
    result = subprocess.run(
        [sys.executable, "tools/phase340_final_ux_regression_guard.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    matrix = ROOT / "tools/audit_outputs/final_ux_regression_matrix.csv"
    summary_file = ROOT / "tools/audit_outputs/final_ux_regression_summary.json"
    assert matrix.exists()
    assert summary_file.exists()
    payload = json.loads(summary_file.read_text(encoding="utf-8"))
    assert payload["ready"] is True
    assert payload["issues"] == 0
    assert "final UX checks" in result.stdout


def test_phase340_release_gate_registered_and_documented():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert '(340, "FINAL_UX_REGRESSION_GUARDS")' in gate
    assert '(340, "final_ux_regression_guards")' in gate
    assert 'ReleaseGateCheck("final_ux_regression_guards"' in gate
    assert "tools/phase340_final_ux_regression_guard.py" in gate
    assert "final_ux_regression_matrix.csv" in gate
    assert (ROOT / "PHASE340_FINAL_UX_REGRESSION_GUARDS.md").exists()
