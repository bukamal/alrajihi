# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.projectwide_visual_style_cleanup_contract import phase442_projectwide_visual_style_cleanup_summary


def test_phase442_contract_ready():
    summary = phase442_projectwide_visual_style_cleanup_summary(ROOT)
    assert summary["ready"], summary["details"]
    assert summary["issues"] == 0


def test_phase442_dialogs_use_central_visual_roles():
    summary = phase442_projectwide_visual_style_cleanup_summary(ROOT)
    migrated = summary["migrated_files"]
    assert migrated["alrajhi_client/views/dialogs/barcode_camera_dialog.py"]["visual_role_markers"] >= 1
    assert migrated["alrajhi_client/views/dialogs/column_contract_customizer.py"]["visual_role_markers"] >= 1
    assert migrated["alrajhi_client/views/widgets/offline_queue_widget.py"]["visual_role_markers"] >= 1


def test_phase442_legacy_style_debt_not_increased():
    summary = phase442_projectwide_visual_style_cleanup_summary(ROOT)
    legacy = summary["legacy_visual_style_summary"]
    assert legacy["total_local_styles"] <= 85
    assert legacy["counts"].get("legacy_local_style", 0) <= 45
