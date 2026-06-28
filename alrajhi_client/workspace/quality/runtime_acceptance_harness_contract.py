# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

RUNTIME_ACCEPTANCE_HARNESS_CONTRACT = {
    "phase": 416,
    "name": "runtime_acceptance_harness",
    "scope": (
        "views.main_window CleanShellNavigationBar runtime geometry",
        "features.transactions.grids.TransactionLineGrid QTest Enter navigation",
        "startup/login/activation RTL-LTR smoke surfaces",
        "settings/preferences persistence runtime smoke",
    ),
    "requirements": (
        "The harness must be import-safe without PyQt5 so CI can validate it on headless machines.",
        "Real Qt probes must collect QWidget trees with objectName, class, visibility, geometry and layout direction.",
        "Shell probes must support Arabic RTL and German/English LTR snapshots plus screenshots.",
        "Editable-grid probes must use QTest.keyClick and check Enter, Shift+Enter, hidden columns, value preservation and single trailing row behavior.",
        "The phase must emit a scenario matrix even when PyQt5 is unavailable locally.",
    ),
    "required_files": (
        "PHASE416_RUNTIME_ACCEPTANCE_HARNESS.md",
        "alrajhi_client/workspace/runtime/runtime_acceptance_harness.py",
        "alrajhi_client/workspace/quality/runtime_acceptance_harness_contract.py",
        "tools/phase416_runtime_acceptance_harness_guard.py",
        "tools/run_phase416_runtime_acceptance.py",
        "tests/test_phase416_runtime_acceptance_harness.py",
    ),
    "required_outputs": (
        "tools/audit_outputs/runtime_acceptance_harness_matrix.csv",
        "tools/audit_outputs/runtime_acceptance_scenario_matrix.csv",
    ),
}


def runtime_acceptance_harness_summary(root: Path | None = None) -> dict[str, object]:
    base = root or ROOT
    missing = [path for path in RUNTIME_ACCEPTANCE_HARNESS_CONTRACT["required_files"] if not (base / path).exists()]
    return {
        "phase": 416,
        "name": "runtime_acceptance_harness",
        "ready": not missing,
        "missing": missing,
    }
