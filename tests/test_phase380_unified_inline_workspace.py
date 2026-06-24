# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / 'alrajhi_client'
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.unified_inline_workspace_contract import (  # noqa: E402
    FILES,
    FORBIDDEN_MARKERS,
    NO_DIRECT_SUBTAB_FUNCTIONS,
    REQUIRED_MARKERS,
    unified_inline_workspace_summary,
)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def calls_in_function(source: str, function_name: str) -> set[str]:
    tree = ast.parse(source)
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    func = sub.func
                    if isinstance(func, ast.Attribute):
                        calls.add(func.attr)
                    elif isinstance(func, ast.Name):
                        calls.add(func.id)
    return calls


def test_phase380_unified_inline_markers():
    for key, path in FILES.items():
        source = read(path)
        ast.parse(source)
        for marker in REQUIRED_MARKERS.get(key, ()):  # type: ignore[arg-type]
            assert marker in source, (key, marker)
        for marker in FORBIDDEN_MARKERS.get(key, ()):  # type: ignore[arg-type]
            assert marker not in source, (key, marker)


def test_phase380_no_inline_subtab_regression():
    for key, functions in NO_DIRECT_SUBTAB_FUNCTIONS.items():
        source = read(FILES[key])
        for fn, forbidden in functions.items():
            calls = calls_in_function(source, fn)
            for call in forbidden:
                assert call not in calls, (key, fn, call, calls)


def test_phase380_guard_summary_ready():
    summary = unified_inline_workspace_summary(ROOT)
    assert summary['ready'] is True
    assert summary['issues'] == 0
    assert summary['checks'] >= 40
