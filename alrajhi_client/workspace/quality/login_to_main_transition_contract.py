# -*- coding: utf-8 -*-
"""Phase 435 contract: login-to-main-window transition profiler and overlay."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

REQUIRED_MAIN_MARKERS = [
    "StartupTimelineProfiler()",
    "login_accepted",
    "PostLoginTransitionOverlay()",
    "post_login_overlay.show_transition()",
    "main_window_create_started",
    "main_window_created",
    "main_window_shown",
    "timeline.export()",
]

REQUIRED_PROFILER_MARKERS = [
    "PHASE435_TIMELINE_MARKER",
    "phase435_login_to_mainwindow_transition_profiler",
    "StartupTimelineEvent",
    "StartupTimelineProfiler",
    "post_login_to_main_ms",
    "startup_timeline.json",
    "startup_timeline.csv",
]

REQUIRED_OVERLAY_MARKERS = [
    "PHASE435_OVERLAY_MARKER",
    "phase435_post_login_transition_overlay",
    "postLoginTransitionOverlay",
    "postLoginTransitionCard",
    "postLoginTransitionProgress",
    "show_transition",
    "finish_transition",
]

REQUIRED_TRANSLATION_KEYS = [
    "post_login_loading_title",
    "post_login_loading_detail",
    "post_login_loading_hint",
    "post_login_step_permissions",
    "post_login_step_main_window",
    "post_login_step_dashboard",
    "post_login_step_done",
    "post_login_loading_done",
]

REQUIRED_BRAND_TOKENS = [
    "post_login_overlay_width",
    "post_login_overlay_height",
    "post_login_overlay_min_width",
    "post_login_overlay_min_height",
    "post_login_overlay_logo_px",
    "post_login_overlay_progress_height",
]

REQUIRED_QSS_MARKERS = [
    "postLoginTransitionOverlay",
    "postLoginTransitionCard",
    "postLoginTransitionTitle",
    "postLoginTransitionDetail",
    "postLoginTransitionStatus",
    "postLoginTransitionProgress",
]

FORBIDDEN_MAIN_PATTERNS = [
    "window = MainWindow()\n    splash.finish(window)\n    window.show()",
]


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def _row(key: str, status: bool, detail: str) -> Dict[str, object]:
    return {"key": key, "status": "pass" if status else "fail", "detail": detail}


def login_to_main_transition_matrix(root: str | Path) -> List[Dict[str, object]]:
    root = Path(root)
    main = _read(root, "alrajhi_client/main.py")
    profiler = _read(root, "alrajhi_client/workspace/runtime/startup_timeline_profiler.py")
    overlay = _read(root, "alrajhi_client/ui/post_login_transition_overlay.py")
    translator = _read(root, "alrajhi_client/i18n/translator.py")
    brand = _read(root, "alrajhi_client/theme/brand.py")
    qss = _read(root, "alrajhi_client/theme/qss.py")
    rows: List[Dict[str, object]] = []

    for marker in REQUIRED_MAIN_MARKERS:
        rows.append(_row(f"main:{marker}", marker in main, "main.py contains post-login transition marker"))
    for marker in REQUIRED_PROFILER_MARKERS:
        rows.append(_row(f"profiler:{marker}", marker in profiler, "Qt-free profiler contains required marker"))
    for marker in REQUIRED_OVERLAY_MARKERS:
        rows.append(_row(f"overlay:{marker}", marker in overlay, "overlay widget contains required marker"))
    for key in REQUIRED_TRANSLATION_KEYS:
        rows.append(_row(f"i18n:{key}", translator.count(key) >= 4, "translation key exists for supported languages"))
    for key in REQUIRED_BRAND_TOKENS:
        rows.append(_row(f"brand:{key}", key in brand, "brand token exists"))
    rows.append(_row("brand:phase", ("'brand_phase': 435" in brand or "'brand_phase': 436" in brand or "'brand_phase': 437" in brand), "brand phase advanced to 435 or newer"))
    for marker in REQUIRED_QSS_MARKERS:
        rows.append(_row(f"qss:{marker}", marker in qss, "QSS contains overlay marker"))
    for pattern in FORBIDDEN_MAIN_PATTERNS:
        rows.append(_row(f"forbidden:{pattern[:30]}", pattern not in main, "old silent login-to-main path removed"))
    return rows


def login_to_main_transition_summary(root: str | Path) -> Dict[str, object]:
    rows = login_to_main_transition_matrix(root)
    issues = [r for r in rows if r["status"] != "pass"]
    return {
        "phase": 435,
        "checks": len(rows),
        "issues": len(issues),
        "ready": not issues,
    }
