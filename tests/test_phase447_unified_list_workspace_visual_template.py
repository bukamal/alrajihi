# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.unified_list_workspace_visual_template_contract import phase447_unified_list_workspace_visual_template_summary


def test_phase447_unified_list_workspace_visual_template_ready():
    summary = phase447_unified_list_workspace_visual_template_summary(ROOT)
    assert summary["ready"], summary["details"]
    assert summary["issues"] == 0


def test_phase447_overrides_legacy_list_toolbar_skin():
    qss = (ROOT / "alrajhi_client/theme/qss.py").read_text(encoding="utf-8")
    assert "Phase404: Basit-inspired management/list workspaces" in qss
    assert "Phase447: unified list workspace visual template" in qss
    assert qss.find("Phase447: unified list workspace visual template") > qss.find("Phase404: Basit-inspired management/list workspaces")


def test_table_toolbar_uses_semantic_list_roles():
    toolbar = (ROOT / "alrajhi_client/views/widgets/components/table_toolbar.py").read_text(encoding="utf-8")
    assert "list_filter_bar" in toolbar
    assert "list_primary_action" in toolbar
    assert "list_danger_action" in toolbar
    assert "list_search_input" in toolbar
    assert "list_counter" in toolbar


def test_runtime_polish_applies_list_template_after_generic_roles():
    runtime = (ROOT / "alrajhi_client/ui/runtime_visual_polish.py").read_text(encoding="utf-8")
    assert "_apply_list_workspace_template(root, policy)" in runtime
    assert "list_workspace_surface" in runtime
    assert "list_filter_input" in runtime
    assert "list_table" in runtime
