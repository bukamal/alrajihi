# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def _load_contract():
    path = ROOT / "alrajhi_client" / "workspace" / "quality" / "basit_release_candidate_contract.py"
    spec = importlib.util.spec_from_file_location("phase410_basit_release_candidate_contract", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_basit_release_candidate_contract_freezes_phase401_to_409_stack():
    module = _load_contract()
    contract = module.BASIT_RELEASE_CANDIDATE_CONTRACT
    assert contract["phase"] == 410
    assert contract["release_candidate"] == "RC1"
    assert contract["locked_phase_range"] == (401, 409)
    assert "BASIT_FINAL_ACCEPTANCE_CONTRACT" in contract["depends_on"]
    assert "tools/audit_outputs/basit_release_candidate_manifest.json" in contract["required_outputs"]


def test_phase410_guard_runs_and_writes_ready_manifest():
    result = subprocess.run(
        [sys.executable, "tools/phase410_basit_release_candidate_freeze.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    matrix = ROOT / "tools" / "audit_outputs" / "basit_release_candidate_matrix.csv"
    manifest_md = ROOT / "tools" / "audit_outputs" / "basit_release_candidate_manifest.md"
    manifest_json = ROOT / "tools" / "audit_outputs" / "basit_release_candidate_manifest.json"
    assert matrix.exists()
    assert manifest_md.exists()
    assert manifest_json.exists()
    rows = list(csv.DictReader(matrix.open(encoding="utf-8")))
    assert rows
    assert {row["status"] for row in rows} == {"OK"}
    payload = json.loads(manifest_json.read_text(encoding="utf-8"))
    assert payload["phase"] == 410
    assert payload["status"] == "READY"
    assert payload["locked_phase_range"] == [401, 409]
    assert "READY FOR RELEASE CANDIDATE ZIP" in manifest_md.read_text(encoding="utf-8")


def test_phase410_release_gate_registration():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert "PHASE410_BASIT_RELEASE_CANDIDATE_FREEZE" in gate
    assert "tests/test_phase410_basit_release_candidate_freeze.py" in gate
    assert "tools/phase410_basit_release_candidate_freeze.py" in gate
    assert "basit_release_candidate_freeze" in gate
    assert "phase=410" in gate


def test_basit_release_candidate_keeps_all_prior_basit_phase_artifacts():
    for phase in range(401, 410):
        assert list(ROOT.glob(f"PHASE{phase}_*.md")), phase
        assert list((ROOT / "tests").glob(f"test_phase{phase}_*.py")), phase
        assert list((ROOT / "tools").glob(f"phase{phase}_*.py")), phase
