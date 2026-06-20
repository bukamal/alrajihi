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
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")


def test_windows_packaging_gate_contract_is_ready():
    from workspace.packaging.windows_packaging_gate_contract import (
        WINDOWS_PACKAGING_GATE_PHASE,
        packaging_gate_checks,
        validate_windows_packaging_gate,
        windows_packaging_gate_summary,
    )

    assert WINDOWS_PACKAGING_GATE_PHASE == 278
    checks = list(packaging_gate_checks())
    keys = {check.key for check in checks}
    assert {
        "runtime_files",
        "source_syntax",
        "hidden_import_manifest",
        "collect_submodules",
        "printing_data_files",
        "hooks",
        "workflow_gate",
        "build_ps1_gate",
        "post_build_runtime_files",
    }.issubset(keys)
    assert validate_windows_packaging_gate(ROOT) == {}
    summary = windows_packaging_gate_summary(ROOT)
    assert summary["ready"] is True
    assert summary["checks"] >= 9


def test_windows_packaging_gate_audit_outputs_matrix_and_summary():
    proc = subprocess.run(
        [sys.executable, "tools/windows_runtime_packaging_gate_audit.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    matrix = ROOT / "tools/audit_outputs/windows_runtime_packaging_gate_matrix.csv"
    summary_file = ROOT / "tools/audit_outputs/windows_runtime_packaging_gate_summary.json"
    assert matrix.exists()
    assert summary_file.exists()
    rows = list(csv.DictReader(matrix.open(encoding="utf-8-sig")))
    assert len(rows) >= 9
    assert {row["status"] for row in rows} == {"pass"}
    summary = json.loads(summary_file.read_text(encoding="utf-8"))
    assert summary["phase"] == 278
    assert summary["ready"] is True


def test_windows_build_scripts_run_packaging_gate_and_verify_print_templates():
    workflow = read(".github/workflows/build-windows-installer.yml")
    build_ps1 = read("build/build_windows.ps1")
    assert "python tools\\windows_runtime_packaging_gate_audit.py" in workflow
    assert "python tools\\windows_runtime_packaging_gate_audit.py" in build_ps1
    for text in (workflow, build_ps1):
        assert "Portable build missing packaged print template files" in text
        assert "Portable build missing packaged print template loader" in text
        assert "print_templates.py" in text
        assert "_template_loader.py" in text


def test_release_gate_includes_phase278_windows_packaging():
    from workspace.quality.release_gate_contract import (
        REQUIRED_PHASE_DOCS,
        REQUIRED_PHASE_TESTS,
        release_gate_checks,
        validate_release_gate,
    )

    assert "PHASE278_WINDOWS_RUNTIME_PACKAGING_GATE.md" in REQUIRED_PHASE_DOCS
    assert "tests/test_phase278_windows_runtime_packaging_gate.py" in REQUIRED_PHASE_TESTS
    keys = {check.key for check in release_gate_checks()}
    assert "windows_packaging" in keys
    assert validate_release_gate(ROOT) == {}
