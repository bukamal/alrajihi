# -*- coding: utf-8 -*-
"""Phase 442 project-wide visual style cleanup contract.

This phase continues the safe migration away from ad-hoc local QSS by moving
small dialog/workspace status surfaces to semantic visual properties.  It is a
cleanup layer only: business logic, data models, permissions and printing are
not changed.
"""
from __future__ import annotations

from pathlib import Path
import json

from workspace.quality.legacy_visual_style_sweep import legacy_visual_style_summary, write_legacy_visual_style_audit

MIGRATED_FILES = {
    "alrajhi_client/views/dialogs/barcode_camera_dialog.py": [
        "visualRole', 'camera_preview'",
        "set_visual_state(self.status_label",
    ],
    "alrajhi_client/views/dialogs/column_contract_customizer.py": [
        "visualRole', 'table_column_header'",
    ],
    "alrajhi_client/views/widgets/offline_queue_widget.py": [
        "visualRole', 'section_header'",
    ],
    "alrajhi_client/views/main_window.py": [
        "set_visual_state(msg, 'danger'",
        "semantic_error_card",
    ],
}

REQUIRED_MARKERS = [
    ('project_visual_identity_phase', ("project_visual_identity_phase': 442", "project_visual_identity_phase': 445")),
    ('legacy_visual_style_sweep_phase', ("legacy_visual_style_sweep_phase': 442", "legacy_visual_style_sweep_phase': 445")),
    ('semantic_visual_state_phase', ("semantic_visual_state_phase': 442", "semantic_visual_state_phase': 445")),
    ('phase442_widget_selector', ('QWidget[projectVisualIdentityPhase="442"]', 'QWidget[projectVisualIdentityPhase="445"]')),
    ('phase442_sweep_selector', ('QWidget[visualIdentitySweepPhase="442"]', 'QWidget[visualIdentitySweepPhase="445"]')),
    ('phase442_tab_selector', ('QTabWidget[projectVisualIdentityPhase="442"]::pane', 'QTabWidget[projectVisualIdentityPhase="445"]::pane')),
    ('semantic_error_card', ('QLabel[visualRole="semantic_error_card"]',)),
    ('table_column_header', ('QLabel[visualRole="table_column_header"]',)),
    ('camera_preview', ('QLabel[visualRole="camera_preview"]',)),
]


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def phase442_projectwide_visual_style_cleanup_summary(root: Path) -> dict:
    brand = _read(root, "alrajhi_client/theme/brand.py")
    qss = _read(root, "alrajhi_client/theme/qss.py")
    combined = "\n".join([brand, qss])
    details: list[str] = []
    for marker_name, alternatives in REQUIRED_MARKERS:
        if not any(marker in combined for marker in alternatives):
            details.append(f"missing central visual marker: {marker_name}")

    migrated: dict[str, dict] = {}
    for rel, markers in MIGRATED_FILES.items():
        text = _read(root, rel)
        file_issues = [f"missing migrated marker: {marker}" for marker in markers if marker not in text]
        forbidden = []
        if rel.endswith("barcode_camera_dialog.py") and "border: 1px solid #aaa" in text:
            forbidden.append("camera preview still uses hard-coded local QSS")
        if rel.endswith("column_contract_customizer.py") and "font-weight: 800;" in text:
            forbidden.append("column header still uses local font-weight QSS")
        if rel.endswith("offline_queue_widget.py") and "font-size:20px;font-weight:700;" in text:
            forbidden.append("offline queue title still uses local title QSS")
        if rel.endswith("main_window.py") and "background:#fff1f2" in text:
            forbidden.append("remote error page still uses hard-coded danger QSS")
        file_issues.extend(forbidden)
        if file_issues:
            details.extend([f"{rel}: {issue}" for issue in file_issues])
        migrated[rel] = {
            "issues": file_issues,
            "semantic_calls": text.count("set_visual_state("),
            "visual_role_markers": text.count("visualRole"),
        }

    audit = write_legacy_visual_style_audit(root)
    legacy_count = int(audit["counts"].get("legacy_local_style", 0))
    total_styles = int(audit["total_local_styles"])
    if legacy_count > 45:
        details.append(f"legacy_local_style did not stay at/below Phase441 baseline: {legacy_count} > 45")
    if total_styles > 85:
        details.append(f"total local styles increased above Phase441 baseline: {total_styles} > 85")

    out_dir = root / "tools" / "audit_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "ready": not details,
        "checks": len(REQUIRED_MARKERS) + sum(len(v) for v in MIGRATED_FILES.values()) + total_styles,
        "issues": len(details),
        "details": details,
        "migrated_files": migrated,
        "legacy_visual_style_summary": audit,
    }
    (out_dir / "projectwide_visual_style_cleanup_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


__all__ = ["phase442_projectwide_visual_style_cleanup_summary"]
