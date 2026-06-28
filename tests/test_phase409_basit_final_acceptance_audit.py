# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import importlib.util
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def _load_contract():
    path = ROOT / "alrajhi_client" / "workspace" / "quality" / "basit_final_acceptance_contract.py"
    spec = importlib.util.spec_from_file_location("phase409_basit_final_acceptance_contract", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_basit_final_acceptance_contract_declares_all_visual_layers():
    module = _load_contract()
    contract = module.BASIT_FINAL_ACCEPTANCE_CONTRACT
    assert contract["phase"] == 409
    for layer in (
        "theme_tokens",
        "restaurant_pos",
        "dashboard",
        "transaction_documents",
        "management_lists",
        "reports_settings",
        "shell_chrome",
        "startup_dialogs",
        "printing_exports",
        "release_gate",
    ):
        assert layer in contract["required_layers"]
    assert "BASIT_PRINTING_SURFACE_CONTRACT" in contract["required_phase_contracts"]


def test_basit_final_acceptance_audit_runs_and_writes_zero_failure_matrix():
    result = subprocess.run(
        [sys.executable, "tools/phase409_basit_final_acceptance_audit.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    matrix = ROOT / "tools" / "audit_outputs" / "basit_final_acceptance_matrix.csv"
    report = ROOT / "tools" / "audit_outputs" / "basit_final_acceptance_report.md"
    assert matrix.exists()
    assert report.exists()
    rows = list(csv.DictReader(matrix.open(encoding="utf-8")))
    assert rows
    assert {row["status"] for row in rows} == {"OK"}
    assert "READY" in report.read_text(encoding="utf-8")


def test_basit_final_acceptance_release_gate_registration():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert "PHASE409_BASIT_FINAL_ACCEPTANCE_AUDIT" in gate
    assert "tests/test_phase409_basit_final_acceptance_audit.py" in gate
    assert "tools/phase409_basit_final_acceptance_audit.py" in gate
    assert "basit_final_acceptance" in gate
    assert "phase=409" in gate


def test_basit_stack_documents_tests_and_guards_are_complete():
    for phase in range(401, 410):
        assert list(ROOT.glob(f"PHASE{phase}_*.md")), phase
        assert list((ROOT / "tests").glob(f"test_phase{phase}_*.py")), phase
        assert list((ROOT / "tools").glob(f"phase{phase}_*.py")), phase
