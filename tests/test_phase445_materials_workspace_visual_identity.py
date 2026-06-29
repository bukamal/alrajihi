# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.materials_workspace_visual_identity_migration_contract import phase445_materials_workspace_visual_identity_summary


def test_phase445_contract_ready():
    summary = phase445_materials_workspace_visual_identity_summary(ROOT)
    assert summary["ready"], summary["details"]
    assert summary["issues"] == 0


def test_phase445_materials_list_uses_filter_card():
    src = (ROOT / "alrajhi_client/views/widgets/items_widget.py").read_text(encoding="utf-8")
    assert "MaterialsFilterCard" in src
    assert "insertWidget(1, filter_card)" in src
    assert "insertLayout(1, filter_layout)" not in src


def test_phase445_material_editor_uses_semantic_cards():
    src = (ROOT / "alrajhi_client/features/items/item_editor_tab.py").read_text(encoding="utf-8")
    for marker in ("MaterialBasicCard", "MaterialPricingCard", "MaterialBarcodeCard", "MaterialUnitsCard"):
        assert marker in src
    assert "QGroupBox#FormCard" not in src
