# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

from alrajhi_client.workspace.quality.single_screen_runtime_hardening_contract import phase456_single_screen_runtime_hardening_summary


def test_phase456_single_screen_runtime_hardening_contract_passes():
    root = Path(__file__).resolve().parents[1]
    summary = phase456_single_screen_runtime_hardening_summary(root)
    assert summary["status"] == "pass", summary
    assert summary["phase"] == 456
    assert summary["checks"] >= 16


def test_phase456_helper_declares_visual_only_scope_and_critical_families():
    root = Path(__file__).resolve().parents[1]
    helper = (root / "alrajhi_client/ui/single_screen_runtime_hardening.py").read_text(encoding="utf-8")
    assert "no business logic" in helper
    assert "no DAO/API" in helper
    assert "no printing" in helper
    assert "no Enter-grid navigation" in helper
    for family in ["login", "dashboard", "pos", "invoice", "material"]:
        assert family in helper
