# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / 'alrajhi_client'
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.inline_management_editor_contract import TARGETS, inline_management_editor_summary  # noqa: E402


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


def test_management_widgets_share_inline_master_detail_host():
    helper = read('alrajhi_client/views/widgets/inline_document_host.py')
    assert 'ResponsiveMasterDetail' in helper
    assert 'DetailPlaceholder' in helper
    assert '_wire_inline_editor_close' in helper
    for target, spec in TARGETS.items():
        src = read(spec['path'])
        assert f"class {spec['class']}(InlineDocumentHostMixin, QWidget):" in src
        assert '_install_inline_document_host' in src
        assert '_show_inline_document' in src
        assert '_connect_inline_detail_preview' in src
        assert spec['required_editor'] in src


def test_management_add_edit_do_not_spawn_workspace_subtabs():
    for target, spec in TARGETS.items():
        src = read(spec['path'])
        for fn in spec['functions']:
            calls = calls_in_function(src, fn)
            for forbidden in spec['forbidden_calls']:
                assert forbidden not in calls, (target, fn, forbidden, calls)


def test_phase377_guard_summary_ready():
    summary = inline_management_editor_summary(ROOT)
    assert summary['ready'] is True
    assert summary['issues'] == 0
    assert summary['checks'] >= 40
