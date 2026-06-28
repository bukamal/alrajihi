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


def load_module(rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_phase419_contract_summary_ready():
    module = load_module(
        "alrajhi_client/workspace/quality/preferences_registry_consolidation_contract.py",
        "phase419_preferences_registry_consolidation_contract",
    )
    contract = module.PREFERENCES_REGISTRY_CONSOLIDATION_CONTRACT
    assert contract["phase"] == 419
    assert contract["name"] == "preferences_registry_consolidation"
    assert "user_branch" in contract["scopes"]
    assert "document_type" in contract["scopes"]
    assert module.preferences_registry_consolidation_summary(ROOT)["ready"] is True


def test_phase419_sources_parse():
    for rel in (
        "alrajhi_client/core/services/preferences_registry.py",
        "alrajhi_client/core/services/user_preferences_service.py",
        "alrajhi_client/features/transactions/grids/transaction_grid_preferences.py",
        "alrajhi_client/features/pos/pos_preferences.py",
        "alrajhi_client/workspace/quality/preferences_registry_consolidation_contract.py",
        "tools/phase419_preferences_registry_consolidation_guard.py",
    ):
        ast.parse(read(rel))


def test_phase419_registry_is_qt_free_and_builds_stable_keys():
    module = load_module("alrajhi_client/core/services/preferences_registry.py", "phase419_preferences_registry")
    backend = module.DictPreferenceBackend()
    registry = module.PreferencesRegistry(backend)
    ctx = module.PreferenceContext(user_id="u 1", branch_id="b/2", profile_id="7", document_type="sales.invoice", identity="pos main")

    assert registry.scoped_key("dashboard/cash_balances_hidden", context=ctx) == "user_preferences/u_1/dashboard/cash_balances_hidden"
    assert registry.scoped_key("dashboard/cash_view_mode", context=ctx, scope=module.PreferenceScope.USER_BRANCH) == "user_preferences/u_1/b_2/dashboard/cash_view_mode"
    assert registry.transaction_grid_key("sales_invoice", "headerState", context=ctx) == "transactions/users/u_1/branches/b_2/profiles/7/sales_invoice/headerState"
    assert registry.pos_key("pos.lines", "density", context=ctx) == "pos/users/u_1/branches/b_2/profiles/7/pos.lines/density"

    registry.set_bool("dashboard/cash_balances_hidden", True, context=ctx)
    assert registry.get_bool("dashboard/cash_balances_hidden", False, context=ctx) is True


def test_phase419_registry_definitions_cover_required_surfaces():
    module = load_module("alrajhi_client/core/services/preferences_registry.py", "phase419_preferences_registry_defs")
    keys = set(module.PREFERENCE_DEFINITIONS)
    for key in (
        "dashboard/cash_balances_hidden",
        "dashboard/cash_view_mode",
        "theme",
        "language",
        "company/name",
        "transaction_grid/headerState",
        "transaction_grid/visibleKeys",
        "pos/visible_columns",
        "pos/density",
        "pos/preset",
    ):
        assert key in keys
    assert module.PREFERENCE_DEFINITIONS["theme"].scope == module.PreferenceScope.USER
    assert module.PREFERENCE_DEFINITIONS["company/logo_path"].scope == module.PreferenceScope.WORKSTATION


def test_phase419_adapters_use_registry_not_local_key_duplication():
    user_service = read("alrajhi_client/core/services/user_preferences_service.py")
    tx_prefs = read("alrajhi_client/features/transactions/grids/transaction_grid_preferences.py")
    pos_prefs = read("alrajhi_client/features/pos/pos_preferences.py")
    theme = read("alrajhi_client/theme_manager.py")

    assert "PreferencesRegistry" in user_service
    assert "QSettingsPreferenceBackend" in user_service
    assert "self._registry.scoped_key" in user_service
    assert "preference_registry.transaction_grid_key" in tx_prefs
    assert "preference_registry.pos_key" in pos_prefs
    assert "user_preferences_service.get_text('theme'" in theme
    assert "QSettings" not in theme


def test_phase419_guard_runs_and_writes_matrices():
    result = subprocess.run(
        [sys.executable, "tools/phase419_preferences_registry_consolidation_guard.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    matrix = ROOT / "tools" / "audit_outputs" / "preferences_registry_consolidation_matrix.csv"
    qsettings = ROOT / "tools" / "audit_outputs" / "preferences_registry_qsettings_usage.csv"
    assert matrix.exists()
    assert qsettings.exists()
    rows = list(csv.DictReader(matrix.open(encoding="utf-8")))
    assert rows
    assert {row["status"] for row in rows} == {"OK"}
    qsettings_rows = list(csv.DictReader(qsettings.open(encoding="utf-8")))
    assert qsettings_rows
    assert {row["owner"] for row in qsettings_rows} <= {
        "central_backend",
        "registry_adapter",
        "legacy_quarantined_backlog",
        "legacy_returns_backlog",
        "migration_backlog_visible",
        "comment_or_contract_reference",
    }


def test_phase419_release_gate_registration():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert "PHASE419_PREFERENCES_REGISTRY_CONSOLIDATION" in gate
    assert "tests/test_phase419_preferences_registry_consolidation.py" in gate
    assert "tools/phase419_preferences_registry_consolidation_guard.py" in gate
    assert "preferences_registry_consolidation" in gate
    assert "phase=419" in gate
