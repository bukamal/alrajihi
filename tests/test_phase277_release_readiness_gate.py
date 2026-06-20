from pathlib import Path
import csv
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def test_release_gate_contract_covers_all_general_governance_layers():
    from workspace.quality.release_gate_contract import (
        RELEASE_BASELINE_PHASE,
        RELEASE_GATE_PHASE,
        release_gate_checks,
        release_gate_summary,
        validate_release_gate,
    )

    assert RELEASE_GATE_PHASE == 277
    assert RELEASE_BASELINE_PHASE == 276
    checks = list(release_gate_checks())
    keys = {check.key for check in checks}
    assert {
        "document_shell",
        "report_shell",
        "list_workspace",
        "operational_shell",
        "settings_contract",
        "rbac_contract",
        "branch_contract",
        "audit_contract",
        "offline_sync",
        "offline_replay",
        "e2e_scenarios",
        "runtime_smoke",
        "reports_currency",
        "reports_printing",
    }.issubset(keys)
    assert not validate_release_gate(ROOT)
    summary = release_gate_summary(ROOT)
    assert summary["ready"] is True
    assert summary["checks"] >= 17


def test_release_gate_audit_tool_writes_matrix_and_summary():
    proc = subprocess.run(
        [sys.executable, "tools/release_readiness_gate_audit.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    matrix = ROOT / "tools/audit_outputs/release_readiness_gate_matrix.csv"
    summary_file = ROOT / "tools/audit_outputs/release_readiness_gate_summary.json"
    assert matrix.exists()
    assert summary_file.exists()
    rows = list(csv.DictReader(matrix.open(encoding="utf-8-sig")))
    assert len(rows) >= 17
    summary = json.loads(summary_file.read_text(encoding="utf-8"))
    assert summary["ready"] is True
    assert summary["baseline_phase"] == 276


def test_settings_diagnostics_includes_release_gate():
    settings = read("alrajhi_client/views/widgets/settings_widget.py")
    assert "release_gate_summary" in settings
    assert "validate_release_gate" in settings
    assert "Release Gate" in settings


def test_phase277_documentation_exists_and_references_phase276_baseline():
    doc = read("PHASE277_RELEASE_READINESS_GATE.md")
    assert "Phase 276" in doc
    assert "Release Gate" in doc
    assert "reports" in doc.lower()
