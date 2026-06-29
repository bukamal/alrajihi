# -*- coding: utf-8 -*-
"""Phase 440 Windows packaged runtime acceptance matrix."""
from __future__ import annotations

from pathlib import Path
import csv
import json

SCREEN_SCENARIOS = [
    {"id": "win_1366_768_100_rtl", "width": 1366, "height": 768, "scale": 100, "language": "ar", "direction": "RTL"},
    {"id": "win_1366_768_125_rtl", "width": 1366, "height": 768, "scale": 125, "language": "ar", "direction": "RTL"},
    {"id": "win_1920_1080_100_rtl", "width": 1920, "height": 1080, "scale": 100, "language": "ar", "direction": "RTL"},
    {"id": "win_1920_1080_125_rtl", "width": 1920, "height": 1080, "scale": 125, "language": "ar", "direction": "RTL"},
    {"id": "win_1366_768_100_ltr", "width": 1366, "height": 768, "scale": 100, "language": "en", "direction": "LTR"},
    {"id": "win_1920_1080_125_ltr", "width": 1920, "height": 1080, "scale": 125, "language": "de", "direction": "LTR"},
]

CHECK_SURFACES = [
    "pre_login_splash",
    "login_dialog",
    "post_login_overlay",
    "main_shell_dashboard",
    "main_menu_action_bar",
    "pos_barcode_table_first",
    "restaurant_card_grid",
    "operational_fullscreen",
    "transaction_grid_enter",
    "printing_templates",
]

ACCEPTANCE_ASSERTIONS = [
    "no_clipped_primary_controls",
    "no_horizontal_content_cutoff",
    "rtl_scroll_starts_at_visible_edge",
    "theme_identity_tokens_applied",
    "tabs_and_workspace_cards_consistent",
    "enter_navigation_does_not_clear_cells",
    "packaged_resources_load",
]


def windows_runtime_acceptance_rows() -> list[dict]:
    rows: list[dict] = []
    for scenario in SCREEN_SCENARIOS:
        for surface in CHECK_SURFACES:
            rows.append({
                **scenario,
                "surface": surface,
                "assertions": ";".join(ACCEPTANCE_ASSERTIONS),
                "required": "yes",
                "phase": 440,
            })
    return rows


def windows_runtime_acceptance_summary() -> dict:
    rows = windows_runtime_acceptance_rows()
    return {
        "ready": True,
        "phase": 440,
        "scenarios": len(SCREEN_SCENARIOS),
        "surfaces": len(CHECK_SURFACES),
        "checks": len(rows) * len(ACCEPTANCE_ASSERTIONS),
        "rows": len(rows),
    }


def write_windows_runtime_acceptance_matrix(root: Path, out_dir: Path | None = None) -> dict:
    out_dir = out_dir or (root / "tools" / "audit_outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = windows_runtime_acceptance_rows()
    csv_path = out_dir / "windows_runtime_acceptance_matrix_phase440.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["id", "width", "height", "scale", "language", "direction", "surface", "assertions", "required", "phase"])
        writer.writeheader()
        writer.writerows(rows)
    summary = windows_runtime_acceptance_summary()
    summary_path = out_dir / "windows_runtime_acceptance_matrix_phase440_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return {**summary, "csv": str(csv_path), "summary_json": str(summary_path)}


__all__ = [
    "SCREEN_SCENARIOS",
    "CHECK_SURFACES",
    "ACCEPTANCE_ASSERTIONS",
    "windows_runtime_acceptance_rows",
    "windows_runtime_acceptance_summary",
    "write_windows_runtime_acceptance_matrix",
]
