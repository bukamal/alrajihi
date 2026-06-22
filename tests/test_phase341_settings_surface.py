# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def test_phase341_settings_surface_contract_has_columns_and_barcode_profiles():
    from workspace.settings.preferences_surface_contract import settings_surface_matrix, validate_settings_surface

    rows = settings_surface_matrix()
    assert rows
    assert not validate_settings_surface()
    kinds = {row["surface_type"] for row in rows}
    assert {"columns", "barcode_profile"}.issubset(kinds)
    assert any(row["id"] == "apparel.variant_labels" for row in rows)
    assert any(row["id"] == "purchase_invoices.lines" for row in rows)


def test_phase341_barcode_profile_settings_are_persistable_api():
    from printing.barcode_profiles import barcode_profile_options

    service_text = (ROOT / "alrajhi_client" / "core" / "services" / "settings_service.py").read_text(encoding="utf-8")
    assert "def save_barcode_profile_settings" in service_text
    assert "printing/barcode/apparel/variant_labels" in service_text
    opts = barcode_profile_options("apparel.variant_labels", {"copies": 3, "columns": 2})
    assert opts["profile_id"] == "apparel.variant_labels"
    assert opts["copies"] == 3
    assert opts["columns"] == 2


def test_phase341_settings_widget_exposes_unified_surface_tab():
    text = (ROOT / "alrajhi_client" / "views" / "widgets" / "settings_widget.py").read_text(encoding="utf-8")
    assert "create_settings_surface_tab" in text
    assert "save_barcode_profile_settings_surface" in text
    assert "reset_unified_column_settings" in text
    assert "settings_surface" in text


def test_phase341_settings_surface_guard_cli_outputs_matrix():
    result = subprocess.run(
        [sys.executable, "tools/phase341_settings_surface_guard.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    summary_path = ROOT / "tools" / "audit_outputs" / "settings_surface_summary.json"
    assert summary_path.exists()
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert payload["issue_groups"] == 0
    assert payload["checks"] >= 6


def test_phase341_release_gate_registered_and_documented():
    gate = (ROOT / "alrajhi_client" / "workspace" / "quality" / "release_gate_contract.py").read_text(encoding="utf-8")
    assert "settings_surface_contract" in gate
    assert "tools/phase341_settings_surface_guard.py" in gate
    assert (ROOT / "PHASE341_SETTINGS_SURFACE_CONTRACT.md").exists()
