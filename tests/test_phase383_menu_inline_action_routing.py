# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / 'alrajhi_client'
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.menu_inline_action_contract import (  # noqa: E402
    ACTION_BAR_INLINE_PAGES,
    FILES,
    FORBIDDEN_MARKERS,
    INLINE_MENU_EXPECTATIONS,
    REQUIRED_MARKERS,
    menu_inline_action_summary,
)
from workspace.actions.inline_menu_action_policy import ACTION_BAR_NEW_ROUTES, MENU_INLINE_CALLBACKS  # noqa: E402


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_phase383_sources_parse_and_markers_hold():
    for key, path in FILES.items():
        source = read(path)
        ast.parse(source)
        for marker in REQUIRED_MARKERS.get(key, ()):  # type: ignore[arg-type]
            assert marker in source, (key, marker)
        for marker in FORBIDDEN_MARKERS.get(key, ()):  # type: ignore[arg-type]
            assert marker not in source, (key, marker)


def test_phase383_inline_policy_maps_menu_to_owning_workspaces():
    for callback, (page_id, method_name) in INLINE_MENU_EXPECTATIONS.items():
        route = MENU_INLINE_CALLBACKS[callback]
        assert route.page_id == page_id
        assert route.method_name == method_name


def test_phase383_action_bar_new_uses_inline_for_management_pages():
    for page_id in ACTION_BAR_INLINE_PAGES:
        assert page_id in ACTION_BAR_NEW_ROUTES


def test_phase383_guard_summary_ready():
    summary = menu_inline_action_summary(ROOT)
    assert summary['ready'] is True
    assert summary['issues'] == 0
    assert summary['checks'] >= 35
