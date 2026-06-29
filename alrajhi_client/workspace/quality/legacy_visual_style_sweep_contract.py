# -*- coding: utf-8 -*-
"""Phase 440 contract: legacy visual style sweep + Windows acceptance matrix."""
from __future__ import annotations

from pathlib import Path

from .legacy_visual_style_sweep import legacy_visual_style_summary, write_legacy_visual_style_audit
from .windows_runtime_acceptance_matrix import windows_runtime_acceptance_summary, write_windows_runtime_acceptance_matrix

REQUIRED_PHASE440_MARKERS = (
    "legacy_visual_style_sweep_phase",
    "windows_runtime_acceptance_phase",
    "visualIdentitySweepPhase",
    "visualStyleSource",
    "QWidget[projectVisualIdentityPhase=\"440\"]",
    "QScrollArea[visualRole=\"workspace_scroll\"]",
    "QSplitter[visualRole=\"workspace_splitter\"]",
    "windows_runtime_acceptance_matrix_phase440",
    "legacy_visual_style_sweep.csv",
)


def phase440_visual_sweep_summary(root: Path) -> dict:
    legacy = write_legacy_visual_style_audit(root)
    windows = write_windows_runtime_acceptance_matrix(root)
    combined = "\n".join([
        (root / "alrajhi_client/theme/brand.py").read_text(encoding="utf-8"),
        (root / "alrajhi_client/theme/qss.py").read_text(encoding="utf-8"),
        (root / "alrajhi_client/ui/runtime_visual_polish.py").read_text(encoding="utf-8"),
        str(legacy),
        str(windows),
    ])
    missing = [marker for marker in REQUIRED_PHASE440_MARKERS if marker not in combined]
    issues = list(legacy.get("details", [])) + [f"missing marker: {m}" for m in missing]
    ready = not issues and bool(windows.get("ready"))
    return {
        "ready": ready,
        "issues": len(issues),
        "details": issues,
        "checks": int(legacy.get("checks", 0)) + int(windows.get("checks", 0)) + len(REQUIRED_PHASE440_MARKERS),
        "legacy": legacy,
        "windows": windows,
    }


__all__ = ["REQUIRED_PHASE440_MARKERS", "phase440_visual_sweep_summary"]
