# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.dashboard_table_runtime_polish_contract import (  # noqa: E402
    FILES,
    FORBIDDEN_MARKERS,
    REQUIRED_MARKERS,
    dashboard_table_runtime_polish_summary,
)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase384_sources_parse_and_required_markers_hold():
    for key, path in FILES.items():
        source = read(path)
        ast.parse(source)
        for marker in REQUIRED_MARKERS.get(key, ()):  # type: ignore[arg-type]
            assert marker in source, (key, marker)


def test_phase384_forbidden_visual_and_navigation_regressions_absent():
    for key, path in FILES.items():
        source = read(path)
        for marker in FORBIDDEN_MARKERS.get(key, ()):  # type: ignore[arg-type]
            assert marker not in source, (key, marker)


def test_phase384_guard_summary_ready():
    summary = dashboard_table_runtime_polish_summary(ROOT)
    assert summary["ready"] is True
    assert summary["issues"] == 0
    assert summary["checks"] >= 25
