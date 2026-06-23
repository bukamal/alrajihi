# -*- coding: utf-8 -*-
"""Phase 359 contract: restore LoginDialog visual design to Phase 355 only."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from workspace.quality.login_layout_stability_contract import (
    login_layout_stability_matrix,
    login_layout_stability_summary,
)

ROOT = Path(__file__).resolve().parents[3]


def login_phase355_restore_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    rows = login_layout_stability_matrix(root or ROOT)
    for row in rows:
        row["phase"] = 359
    return rows


def login_phase355_restore_summary(root: Path | None = None) -> Dict[str, object]:
    summary = login_layout_stability_summary(root or ROOT)
    payload = dict(summary)
    payload["phase"] = 359
    return payload


__all__ = ["login_phase355_restore_matrix", "login_phase355_restore_summary"]
