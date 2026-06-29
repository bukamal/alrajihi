# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.legacy_visual_style_sweep import (
    legacy_visual_style_summary,
    scan_local_visual_styles,
)
from workspace.quality.windows_runtime_acceptance_matrix import (
    SCREEN_SCENARIOS,
    CHECK_SURFACES,
    ACCEPTANCE_ASSERTIONS,
    windows_runtime_acceptance_rows,
)
from workspace.quality.legacy_visual_style_sweep_contract import (
    REQUIRED_PHASE440_MARKERS,
    phase440_visual_sweep_summary,
)


def test_phase440_runtime_polish_sets_sweep_properties():
    source = (ROOT / "alrajhi_client" / "ui" / "runtime_visual_polish.py").read_text(encoding="utf-8")
    assert "visualIdentitySweepPhase" in source
    assert "visualStyleSource" in source
    assert "workspace_scroll" in source
    assert "workspace_splitter" in source


def test_phase440_qss_supports_phase_440_and_workspace_containers():
    qss = (ROOT / "alrajhi_client" / "theme" / "qss.py").read_text(encoding="utf-8")
    assert 'QWidget[projectVisualIdentityPhase="440"]' in qss
    assert 'QTabWidget[projectVisualIdentityPhase="440"]::pane' in qss
    assert 'QScrollArea[visualRole="workspace_scroll"]' in qss
    assert 'QSplitter[visualRole="workspace_splitter"]' in qss


def test_phase440_legacy_style_audit_is_categorized_not_silent():
    records = scan_local_visual_styles(ROOT)
    assert records
    summary = legacy_visual_style_summary(ROOT)
    assert summary["ready"] is True
    assert summary["total_local_styles"] == len(records)
    assert sum(summary["counts"].values()) == len(records)


def test_phase440_windows_acceptance_matrix_covers_required_screens_and_surfaces():
    rows = windows_runtime_acceptance_rows()
    assert len(SCREEN_SCENARIOS) >= 6
    assert "main_shell_dashboard" in CHECK_SURFACES
    assert "operational_fullscreen" in CHECK_SURFACES
    assert "enter_navigation_does_not_clear_cells" in ACCEPTANCE_ASSERTIONS
    assert len(rows) == len(SCREEN_SCENARIOS) * len(CHECK_SURFACES)


def test_phase440_contract_summary_ready():
    summary = phase440_visual_sweep_summary(ROOT)
    assert summary["ready"] is True
    assert summary["issues"] == 0
    assert summary["checks"] >= 400
    combined = str(summary)
    for marker in REQUIRED_PHASE440_MARKERS:
        assert marker in combined or marker in (ROOT / "alrajhi_client/theme/qss.py").read_text(encoding="utf-8") or marker in (ROOT / "alrajhi_client/theme/brand.py").read_text(encoding="utf-8")
