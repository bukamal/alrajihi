# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

from alrajhi_client.workspace.quality.targeted_screen_rebuild_contract import phase455_targeted_screen_rebuild_summary


def test_phase455_targeted_screen_rebuild_contract_passes():
    root = Path(__file__).resolve().parents[1]
    summary = phase455_targeted_screen_rebuild_summary(root)
    assert summary["status"] == "pass", summary
    assert summary["phase"] == 455
    assert summary["checks"] >= 10


def test_phase455_helper_declares_non_business_scope():
    root = Path(__file__).resolve().parents[1]
    helper = (root / "alrajhi_client/ui/targeted_screen_rebuild.py").read_text(encoding="utf-8")
    assert "no business logic" in helper
    assert "no DAO/API" in helper
    assert "no printing" in helper
    assert "no permissions" in helper
