# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / 'alrajhi_client'
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.document_layout_family_contract import (  # noqa: E402
    EXPECTED_TYPE_MARKERS,
    FILES,
    FORBIDDEN_MARKERS,
    REQUIRED_MARKERS,
    document_layout_family_summary,
)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_phase381_layout_policy_markers():
    for key, path in FILES.items():
        source = read(path)
        ast.parse(source)
        for marker in REQUIRED_MARKERS.get(key, ()):  # type: ignore[arg-type]
            assert marker in source, (key, marker)
        for marker in FORBIDDEN_MARKERS.get(key, ()):  # type: ignore[arg-type]
            assert marker not in source, (key, marker)


def test_phase381_expected_families_are_declared():
    source = read(FILES['layout_policy'])
    for family, markers in EXPECTED_TYPE_MARKERS.items():
        for marker in markers:
            assert f'"{marker}"' in source, (family, marker)


def test_phase381_guard_summary_ready():
    summary = document_layout_family_summary(ROOT)
    assert summary['ready'] is True
    assert summary['issues'] == 0
    assert summary['checks'] >= 45
