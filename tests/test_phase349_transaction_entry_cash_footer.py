# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "alrajhi_client"))

from workspace.quality.transaction_entry_cash_footer_contract import phase349_checks, phase349_issues


def test_phase349_contract_has_no_issues():
    assert not phase349_issues(ROOT)


def test_phase349_contract_covers_requested_areas():
    areas = {check.area for check in phase349_checks(ROOT)}
    assert {"keyboard", "cash_party", "visual", "actions", "returns"}.issubset(areas)


def test_phase349_contract_is_substantial():
    assert len(phase349_checks(ROOT)) >= 14
