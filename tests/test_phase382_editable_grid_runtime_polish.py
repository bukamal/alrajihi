# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / 'alrajhi_client'
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.editable_grid_runtime_polish_contract import (  # noqa: E402
    FILES,
    FORBIDDEN_MARKERS,
    REQUIRED_MARKERS,
    editable_grid_runtime_summary,
)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_phase382_sources_parse_and_markers_hold():
    for key, path in FILES.items():
        source = read(path)
        ast.parse(source)
        for marker in REQUIRED_MARKERS.get(key, ()):  # type: ignore[arg-type]
            assert marker in source, (key, marker)
        for marker in FORBIDDEN_MARKERS.get(key, ()):  # type: ignore[arg-type]
            assert marker not in source, (key, marker)


def test_phase382_guard_summary_ready():
    summary = editable_grid_runtime_summary(ROOT)
    assert summary['ready'] is True
    assert summary['issues'] == 0
    assert summary['checks'] >= 30
