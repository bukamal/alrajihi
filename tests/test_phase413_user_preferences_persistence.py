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
    path = ROOT / "alrajhi_client" / "workspace" / "quality" / "user_preferences_persistence_contract.py"
    spec = importlib.util.spec_from_file_location("phase413_user_preferences_persistence_contract", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_phase413_contract_documents_persistence_scope():
    module = _load_contract()
    contract = module.USER_PREFERENCES_PERSISTENCE_CONTRACT
    assert contract["phase"] == 413
    assert contract["name"] == "user_preferences_persistence"
    assert "core.services.user_preferences_service" in contract["scope"]
    assert any("Dashboard cash balance hiding" in item for item in contract["requirements"])
    assert module.user_preferences_persistence_summary(ROOT)["ready"] is True


def test_phase413_sources_parse_and_service_keys_exist():
    for rel in (
        "alrajhi_client/core/services/user_preferences_service.py",
        "alrajhi_client/views/widgets/dashboard_widget.py",
        "tools/phase413_user_preferences_persistence_guard.py",
    ):
        ast.parse(read(rel))
    service = read("alrajhi_client/core/services/user_preferences_service.py")
    assert "class UserPreferencesService" in service
    assert "ROOT = \"user_preferences\"" in service
    assert "DASHBOARD_CASH_HIDDEN" in service
    assert "DASHBOARD_CASH_VIEW_MODE" in service
    assert "self._settings.sync()" in service
    assert "def _current_user_key" in service
    assert "def _current_branch_key" in service


def test_phase413_dashboard_loads_and_saves_cash_preferences():
    dashboard = read("alrajhi_client/views/widgets/dashboard_widget.py")
    assert "from core.services.user_preferences_service import user_preferences_service" in dashboard
    assert "self._cash_view_mode = user_preferences_service.dashboard_cash_view_mode()" in dashboard
    assert "self._cash_balances_hidden = user_preferences_service.dashboard_cash_balances_hidden()" in dashboard
    assert "self._cash_balances_hidden = False" not in dashboard
    assert "user_preferences_service.set_dashboard_cash_view_mode(self._cash_view_mode)" in dashboard
    assert "user_preferences_service.set_dashboard_cash_balances_hidden(self._cash_balances_hidden)" in dashboard
    assert "'fa5s.eye-slash' if self._cash_balances_hidden else 'fa5s.eye'" in dashboard


def test_phase413_guard_runs_and_writes_matrix():
    result = subprocess.run(
        [sys.executable, "tools/phase413_user_preferences_persistence_guard.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    matrix = ROOT / "tools" / "audit_outputs" / "user_preferences_persistence_matrix.csv"
    assert matrix.exists()
    rows = list(csv.DictReader(matrix.open(encoding="utf-8")))
    assert rows
    assert {row["status"] for row in rows} == {"OK"}


def test_phase413_release_gate_registration():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert "PHASE413_USER_PREFERENCES_PERSISTENCE" in gate
    assert "tests/test_phase413_user_preferences_persistence.py" in gate
    assert "tools/phase413_user_preferences_persistence_guard.py" in gate
    assert "user_preferences_persistence" in gate
    assert "phase=413" in gate
