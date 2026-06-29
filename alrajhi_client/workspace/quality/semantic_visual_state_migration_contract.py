# -*- coding: utf-8 -*-
"""Phase441 contract: semantic visual-state migration.

This phase targets high-impact local hard-coded status colors in material
surfaces.  It does not delete every local stylesheet in the project; it creates
and enforces the central semantic-state path used by migrated surfaces.
"""
from __future__ import annotations

import json
from pathlib import Path

from workspace.quality.legacy_visual_style_sweep import write_legacy_visual_style_audit

_STATUS_HEX_NEEDLES = (
    "#b91c1c",
    "#047857",
    "#4b5563",
    "#b45309",
    "#2e7d32",
    "#c62828",
    "#666",
    "#fecaca",
    "#fef2f2",
    "#dbeafe",
    "#eff6ff",
)
_MIGRATED_FILES = (
    "alrajhi_client/features/items/item_editor_tab.py",
    "alrajhi_client/views/dialogs/item_dialog.py",
)


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def phase441_semantic_visual_state_summary(root: Path) -> dict:
    checks = 0
    issues: list[str] = []

    visual_state = _read(root, "alrajhi_client/ui/visual_state.py")
    qss = _read(root, "alrajhi_client/theme/qss.py")
    brand = _read(root, "alrajhi_client/theme/brand.py")

    required_markers = [
        "def set_visual_state",
        "visualStyleSource",
        "centralized_visual_state",
        "Phase441: semantic visual states",
        "QLabel[visualState=\"danger\"]",
        "QFrame[visualState=\"info\"]",
        "semantic_visual_state_phase",
        "project_visual_identity_phase",
        "QWidget[projectVisualIdentityPhase=\"441\"]",
    ]
    combined = "\n".join([visual_state, qss, brand])
    for marker in required_markers:
        checks += 1
        if marker not in combined:
            issues.append(f"missing marker: {marker}")

    migrated: dict[str, dict] = {}
    for rel in _MIGRATED_FILES:
        text = _read(root, rel)
        file_issues: list[str] = []
        if "from ui.visual_state import set_visual_state" not in text:
            file_issues.append("missing set_visual_state import")
        if "set_visual_state(" not in text:
            file_issues.append("no semantic visual state calls")
        for needle in _STATUS_HEX_NEEDLES:
            if needle in text:
                file_issues.append(f"hard-coded status color remains: {needle}")
        checks += 3 + len(_STATUS_HEX_NEEDLES)
        if file_issues:
            issues.extend(f"{rel}: {issue}" for issue in file_issues)
        migrated[rel] = {"issues": file_issues, "semantic_calls": text.count("set_visual_state(")}

    legacy = write_legacy_visual_style_audit(root)
    # Phase441 should materially reduce the Phase440 local-style debt.
    checks += 2
    if int(legacy.get("total_local_styles", 9999)) > 90:
        issues.append(f"local style count too high after semantic migration: {legacy.get('total_local_styles')}")
    if int(legacy.get("counts", {}).get("legacy_local_style", 9999)) > 50:
        issues.append(f"legacy local style count too high after semantic migration: {legacy.get('counts', {}).get('legacy_local_style')}")

    summary = {
        "ready": not issues,
        "checks": checks,
        "issues": len(issues),
        "details": issues,
        "legacy_visual_style_summary": legacy,
        "migrated_files": migrated,
    }
    out_dir = root / "tools" / "audit_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "semantic_visual_state_migration_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


__all__ = ["phase441_semantic_visual_state_summary"]
