# -*- coding: utf-8 -*-
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.registry import PAGE_MANIFESTS
from workspace.runtime.visual_polish_contract import (
    CRITICAL_VISUAL_PAGES,
    TYPE_DEFAULTS,
    validate_visual_polish_contract,
    visual_polish_rows,
    workspace_visual_policies,
    workspace_visual_policy,
)


def test_phase344_all_manifest_pages_have_visual_policy():
    policies = workspace_visual_policies()
    assert set(policies) == set(PAGE_MANIFESTS)
    assert {p.workspace_type for p in policies.values()} == {m.workspace_type for m in PAGE_MANIFESTS.values()}
    assert all(p.object_name.startswith("RuntimeWorkspace_") for p in policies.values())


def test_phase344_workspace_type_defaults_cover_manifest_types():
    manifest_types = {m.workspace_type for m in PAGE_MANIFESTS.values()}
    assert manifest_types.issubset(set(TYPE_DEFAULTS))
    assert TYPE_DEFAULTS["operational"]["table_density"] == "touch"
    assert TYPE_DEFAULTS["document"]["table_density"] == "compact"
    assert TYPE_DEFAULTS["dashboard"]["button_role"] == "dashboard_shortcut"


def test_phase344_critical_pages_are_covered():
    assert set(CRITICAL_VISUAL_PAGES).issubset(set(PAGE_MANIFESTS))
    assert workspace_visual_policy("restaurant").workspace_type == "operational"
    assert workspace_visual_policy("apparel").workspace_type == "matrix"
    assert workspace_visual_policy("reports").workspace_type == "report"


def test_phase344_visual_polish_has_no_contract_issues():
    rows = visual_polish_rows()
    assert rows
    assert validate_visual_polish_contract() == {}


def test_phase344_runtime_wiring_and_qss_selectors_exist():
    main_window = (ROOT / "alrajhi_client/views/main_window.py").read_text(encoding="utf-8")
    qss = (ROOT / "alrajhi_client/theme/qss.py").read_text(encoding="utf-8")
    runtime = (ROOT / "alrajhi_client/ui/runtime_visual_polish.py").read_text(encoding="utf-8")
    assert "apply_runtime_visual_polish" in main_window
    assert "_apply_runtime_visual_polish_for_tab" in main_window
    assert "visualWorkspaceType" in runtime
    assert "runtime_table" in runtime
    assert "Phase 344: runtime visual polish sweep" in qss
    assert "QWidget[visualWorkspaceType" in qss
