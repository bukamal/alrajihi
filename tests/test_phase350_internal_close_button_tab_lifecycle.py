# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "alrajhi_client"))

from workspace.quality.workspace_internal_close_contract import phase350_checks, phase350_issues


def test_phase350_contract_has_no_issues():
    assert not phase350_issues(ROOT)


def test_phase350_contract_covers_requested_areas():
    areas = {check.area for check in phase350_checks(ROOT)}
    assert {"lifecycle", "transactions", "returns", "documents", "release"}.issubset(areas)


def test_phase350_contract_is_substantial():
    assert len(phase350_checks(ROOT)) >= 10
