# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / 'alrajhi_client'
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.inline_party_layout_unification_contract import (  # noqa: E402
    CHECKS,
    FORBIDDEN_CALLS,
    inline_party_layout_unification_summary,
)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def calls_in_function(source: str, fn: str):
    tree = ast.parse(source)
    calls = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == fn:
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    func = sub.func
                    if isinstance(func, ast.Attribute):
                        calls.add(func.attr)
                    elif isinstance(func, ast.Name):
                        calls.add(func.id)
    return calls


def test_phase379_markers_and_removed_party_title_cards():
    for spec in CHECKS:
        source = read(spec['path'])
        ast.parse(source)
        for marker in spec.get('required', ()):  # type: ignore[assignment]
            assert marker in source, (spec['target'], marker)
        for marker in spec.get('forbidden_text', ()):  # type: ignore[assignment]
            assert marker not in source, (spec['target'], marker)


def test_phase379_customer_supplier_inline_no_subtabs():
    for path, functions in FORBIDDEN_CALLS.items():
        source = read(path)
        for fn, forbidden_calls in functions.items():
            calls = calls_in_function(source, fn)
            for call in forbidden_calls:
                assert call not in calls, (path, fn, call, calls)


def test_phase379_guard_summary_ready():
    summary = inline_party_layout_unification_summary(ROOT)
    assert summary['ready'] is True
    assert summary['issues'] == 0
    assert summary['checks'] >= 20
