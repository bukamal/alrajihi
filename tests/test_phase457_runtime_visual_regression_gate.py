# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

from alrajhi_client.workspace.quality.runtime_visual_regression_gate_contract import phase457_runtime_visual_regression_gate_summary


def test_phase457_runtime_visual_regression_gate_contract_passes():
    root = Path(__file__).resolve().parents[1]
    summary = phase457_runtime_visual_regression_gate_summary(root)
    assert summary["status"] == "pass", summary
    assert summary["phase"] == 457
    assert summary["checks"] >= 20


def test_phase457_helper_is_visual_only_and_tracks_required_chain():
    root = Path(__file__).resolve().parents[1]
    helper = (root / "alrajhi_client/ui/runtime_visual_regression_gate.py").read_text(encoding="utf-8")
    assert "Phase453-456" in helper
    assert "no business logic" in helper
    assert "no DAO/API" in helper
    assert "no printing" in helper
    assert "no Enter-grid navigation" in helper
    for family in ["login", "dashboard", "pos", "invoice", "material"]:
        assert family in helper


def test_phase457_runtime_polish_order_is_after_phase456():
    root = Path(__file__).resolve().parents[1]
    polish = (root / "alrajhi_client/ui/runtime_visual_polish.py").read_text(encoding="utf-8")
    assert polish.find("apply_single_screen_runtime_hardening") < polish.find("apply_runtime_visual_regression_gate")
