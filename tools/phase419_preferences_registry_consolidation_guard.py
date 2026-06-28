#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "audit_outputs" / "preferences_registry_consolidation_matrix.csv"


def read(rel: str) -> str:
    path = ROOT / rel
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def add(rows: list[dict[str, str]], key: str, category: str, path: str, ok: bool, detail: str) -> None:
    rows.append({"key": key, "category": category, "path": path, "status": "OK" if ok else "FAIL", "detail": detail})


def python_files() -> list[Path]:
    return [p for p in (ROOT / "alrajhi_client").rglob("*.py") if "__pycache__" not in str(p)]


def qsettings_occurrences() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in python_files():
        rel = path.relative_to(ROOT).as_posix()
        source = path.read_text(encoding="utf-8", errors="ignore")
        if "QSettings" in source:
            if "core/services/preferences_registry.py" in rel:
                owner = "central_backend"
            elif "core/services/user_preferences_service.py" in rel:
                owner = "registry_adapter"
            elif "views/dialogs/invoice_dialog.py" in rel:
                owner = "legacy_quarantined_backlog"
            elif "views/widgets/returns_widget.py" in rel:
                owner = "legacy_returns_backlog"
            elif any(token in rel for token in ("auth/session.py", "core/server_control.py", "database/connection.py", "gateways/remote/settings_gateway.py", "main.py", "config.py", "currency.py", "printer_manager.py", "views/dialogs/login_dialog.py", "views/widgets/settings_widget.py", "views/custom_table_view.py", "printing/label_designer.py", "views/widgets/dashboard_widget.py", "core/services/settings_service.py", "views/widgets/components/table_preferences.py")):
                owner = "migration_backlog_visible"
            elif any(token in rel for token in ("workspace/quality/release_gate_contract.py", "workspace/quality/preferences_registry_consolidation_contract.py", "workspace/runtime/runtime_acceptance_harness.py", "features/pos/pos_preferences.py", "features/transactions/grids/transaction_grid_preferences.py")):
                owner = "comment_or_contract_reference"
            else:
                owner = "unclassified"
            rows.append({"path": rel, "owner": owner, "count": str(source.count("QSettings"))})
    return rows


def main() -> int:
    rows: list[dict[str, str]] = []
    required = [
        "PHASE419_PREFERENCES_REGISTRY_CONSOLIDATION.md",
        "alrajhi_client/core/services/preferences_registry.py",
        "alrajhi_client/core/services/user_preferences_service.py",
        "alrajhi_client/features/transactions/grids/transaction_grid_preferences.py",
        "alrajhi_client/features/pos/pos_preferences.py",
        "alrajhi_client/workspace/quality/preferences_registry_consolidation_contract.py",
        "tools/phase419_preferences_registry_consolidation_guard.py",
        "tests/test_phase419_preferences_registry_consolidation.py",
    ]
    for rel in required:
        add(rows, f"exists::{rel}", "file", rel, (ROOT / rel).exists(), "required Phase419 file exists")

    registry = read("alrajhi_client/core/services/preferences_registry.py")
    user_service = read("alrajhi_client/core/services/user_preferences_service.py")
    tx_prefs = read("alrajhi_client/features/transactions/grids/transaction_grid_preferences.py")
    pos_prefs = read("alrajhi_client/features/pos/pos_preferences.py")
    theme = read("alrajhi_client/theme_manager.py")
    contract = read("alrajhi_client/workspace/quality/preferences_registry_consolidation_contract.py")
    release = read("alrajhi_client/workspace/quality/release_gate_contract.py")

    for rel in (
        "alrajhi_client/core/services/preferences_registry.py",
        "alrajhi_client/core/services/user_preferences_service.py",
        "alrajhi_client/features/transactions/grids/transaction_grid_preferences.py",
        "alrajhi_client/features/pos/pos_preferences.py",
        "alrajhi_client/workspace/quality/preferences_registry_consolidation_contract.py",
        "tools/phase419_preferences_registry_consolidation_guard.py",
    ):
        try:
            ast.parse(read(rel))
            ok = True
        except SyntaxError:
            ok = False
        add(rows, f"ast::{rel}", "syntax", rel, ok, "source parses")

    for symbol in (
        "PreferenceScope",
        "PreferenceContext",
        "PreferenceDefinition",
        "PreferencesRegistry",
        "QSettingsPreferenceBackend",
        "PREFERENCE_DEFINITIONS",
        "transaction_grid_key",
        "pos_key",
    ):
        add(rows, f"registry_symbol::{symbol}", "registry", "alrajhi_client/core/services/preferences_registry.py", symbol in registry, f"registry exposes {symbol}")

    for scope in ("SYSTEM", "COMPANY", "BRANCH", "USER", "USER_BRANCH", "WORKSTATION", "TABLE_LAYOUT", "DOCUMENT_TYPE", "POS_TERMINAL"):
        add(rows, f"scope::{scope.lower()}", "registry", "alrajhi_client/core/services/preferences_registry.py", scope in registry, f"scope {scope} declared")

    for pref_key in (
        "dashboard/cash_balances_hidden",
        "dashboard/cash_view_mode",
        "theme",
        "language",
        "company/name",
        "transaction_grid/headerState",
        "pos/visible_columns",
    ):
        add(rows, f"definition::{pref_key}", "definitions", "alrajhi_client/core/services/preferences_registry.py", pref_key in registry, f"definition for {pref_key}")

    add(rows, "user_service_uses_registry", "adapter", "alrajhi_client/core/services/user_preferences_service.py", "PreferencesRegistry" in user_service and "QSettingsPreferenceBackend" in user_service and "self._registry" in user_service, "UserPreferencesService is backed by registry")
    add(rows, "dashboard_keys_preserved", "compat", "alrajhi_client/core/services/user_preferences_service.py", "DASHBOARD_CASH_HIDDEN" in user_service and "DASHBOARD_CASH_VIEW_MODE" in user_service, "dashboard preference keys remain stable")
    add(rows, "transaction_prefs_registry", "adapter", "alrajhi_client/features/transactions/grids/transaction_grid_preferences.py", "preference_registry.transaction_grid_key" in tx_prefs and "PreferenceContext" in tx_prefs, "transaction grid layout keys resolve through registry")
    add(rows, "pos_prefs_registry", "adapter", "alrajhi_client/features/pos/pos_preferences.py", "preference_registry.pos_key" in pos_prefs and "PreferenceContext" in pos_prefs, "POS preference keys resolve through registry")
    add(rows, "theme_uses_user_preferences", "adapter", "alrajhi_client/theme_manager.py", "user_preferences_service.get_text('theme'" in theme and "QSettings" not in theme, "theme persistence no longer uses raw QSettings")
    add(rows, "contract_phase", "contract", "alrajhi_client/workspace/quality/preferences_registry_consolidation_contract.py", "PREFERENCES_REGISTRY_CONSOLIDATION_CONTRACT" in contract and '"phase": 419' in contract, "contract declares Phase419")
    add(rows, "release_doc", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "PHASE419_PREFERENCES_REGISTRY_CONSOLIDATION" in release, "Phase419 doc registered")
    add(rows, "release_test", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "tests/test_phase419_preferences_registry_consolidation.py" in release, "Phase419 test registered")
    add(rows, "release_check", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "preferences_registry_consolidation" in release and "phase=419" in release, "Phase419 release check registered")

    qsettings = qsettings_occurrences()
    unclassified = [row for row in qsettings if row["owner"] == "unclassified"]
    add(rows, "raw_qsettings_audited", "audit", "tools/audit_outputs/preferences_registry_qsettings_usage.csv", bool(qsettings), "direct QSettings usage is enumerated")
    add(rows, "raw_qsettings_classified", "audit", "tools/audit_outputs/preferences_registry_qsettings_usage.csv", not unclassified, "remaining QSettings usage is classified for migration")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["key", "category", "path", "status", "detail"])
        writer.writeheader()
        writer.writerows(rows)

    usage_out = OUT.parent / "preferences_registry_qsettings_usage.csv"
    with usage_out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["path", "owner", "count"])
        writer.writeheader()
        writer.writerows(qsettings)

    failures = [row for row in rows if row["status"] != "OK"]
    print(f"Phase419 preferences registry consolidation checks: {len(rows)} checks, failures={len(failures)}")
    print(f"Phase419 QSettings usage rows: {len(qsettings)}, unclassified={len(unclassified)}")
    for row in failures:
        print(f"FAIL {row['key']}: {row['detail']}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
