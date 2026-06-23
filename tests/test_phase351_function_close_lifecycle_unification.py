# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "alrajhi_client"))

from workspace.quality.function_close_unification_contract import phase351_checks, phase351_issues


def test_phase351_function_close_has_no_issues():
    assert not phase351_issues(ROOT)


def test_phase351_covers_all_business_functions():
    areas = {check.area for check in phase351_checks(ROOT)}
    assert {"transactions", "returns", "materials", "inventory", "finance", "branches", "users", "manufacturing", "dialog_documents"}.issubset(areas)


def test_phase351_contract_is_substantial():
    assert len(phase351_checks(ROOT)) >= 30
