# -*- coding: utf-8 -*-
"""Phase 438 main shell responsive runtime fit contract."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

REQUIRED_RUNTIME_FIT_MODULE_MARKERS = (
    "PHASE = 438",
    "MainShellRuntimeFitProfile",
    "compute_main_shell_runtime_fit_profile",
    "apply_main_shell_runtime_fit",
    "show_main_window_runtime_fitted",
    "ALRAJHI_WINDOWED_START",
    "screen_aware_maximized",
)

REQUIRED_MAIN_WINDOW_MARKERS = (
    "apply_main_shell_runtime_fit",
    "mainShellRuntimeFitPhase",
    "self._runtime_fit_profile = apply_main_shell_runtime_fit(self)",
)

REQUIRED_MAIN_ENTRY_MARKERS = (
    "show_main_window_runtime_fitted",
    "runtime_fit_profile = show_main_window_runtime_fitted(window)",
    "main_shell_runtime_fit",
)

REQUIRED_DASHBOARD_RESPONSIVE_MARKERS = (
    "dashboardResponsivePhase",
    "scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)",
    "dashboard_responsive_phase",
)

FORBIDDEN_MAIN_ENTRY_SNIPPETS = (
    "\n    window.show()\n    timeline.mark(\"main_window_shown\"",
)


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def main_shell_responsive_runtime_fit_matrix(root: Path) -> List[Dict[str, str]]:
    runtime_fit = _read(root, "alrajhi_client/ui/main_shell_runtime_fit.py")
    main_window = _read(root, "alrajhi_client/views/main_window.py")
    main_entry = _read(root, "alrajhi_client/main.py")
    dashboard = _read(root, "alrajhi_client/views/widgets/dashboard_widget.py")
    brand = _read(root, "alrajhi_client/theme/brand.py")
    rows: List[Dict[str, str]] = []
    for marker in REQUIRED_RUNTIME_FIT_MODULE_MARKERS:
        rows.append({"area": "runtime_fit_module", "check": marker, "status": "pass" if marker in runtime_fit else "fail"})
    for marker in REQUIRED_MAIN_WINDOW_MARKERS:
        rows.append({"area": "main_window", "check": marker, "status": "pass" if marker in main_window else "fail"})
    for marker in REQUIRED_MAIN_ENTRY_MARKERS:
        rows.append({"area": "main_entry", "check": marker, "status": "pass" if marker in main_entry else "fail"})
    for marker in REQUIRED_DASHBOARD_RESPONSIVE_MARKERS:
        source = dashboard if marker != "dashboard_responsive_phase" else brand
        rows.append({"area": "dashboard_responsive", "check": marker, "status": "pass" if marker in source else "fail"})
    for marker in FORBIDDEN_MAIN_ENTRY_SNIPPETS:
        rows.append({"area": "legacy_window_show", "check": marker, "status": "fail" if marker in main_entry else "pass"})
    return rows


def main_shell_responsive_runtime_fit_summary(root: Path) -> Dict[str, object]:
    rows = main_shell_responsive_runtime_fit_matrix(root)
    issues = [row for row in rows if row["status"] != "pass"]
    return {
        "phase": 438,
        "ready": not issues,
        "checks": len(rows),
        "issues": len(issues),
        "policy": "screen_aware_maximized_main_shell",
    }
