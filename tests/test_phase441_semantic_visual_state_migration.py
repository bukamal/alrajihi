# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.semantic_visual_state_migration_contract import phase441_semantic_visual_state_summary


def test_phase441_semantic_visual_state_contract_ready():
    summary = phase441_semantic_visual_state_summary(ROOT)
    assert summary["ready"], summary["details"]
    assert summary["issues"] == 0


def test_phase441_material_surfaces_use_semantic_state():
    summary = phase441_semantic_visual_state_summary(ROOT)
    files = summary["migrated_files"]
    assert files["alrajhi_client/features/items/item_editor_tab.py"]["semantic_calls"] >= 6
    assert files["alrajhi_client/views/dialogs/item_dialog.py"]["semantic_calls"] >= 6


def test_phase441_legacy_style_debt_reduced():
    summary = phase441_semantic_visual_state_summary(ROOT)
    legacy = summary["legacy_visual_style_summary"]
    assert legacy["total_local_styles"] <= 90
    assert legacy["counts"].get("legacy_local_style", 0) <= 50
