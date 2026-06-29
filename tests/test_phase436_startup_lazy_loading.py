# -*- coding: utf-8 -*-
"""Phase 436 startup lazy-loading tests."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.startup_lazy_loading_contract import (  # noqa: E402
    FORBIDDEN_EAGER_CONSTRUCTION_PATTERNS,
    FORBIDDEN_EAGER_IMPORTS,
    REQUIRED_LAZY_FACTORY_KEYS,
    REQUIRED_MAIN_WINDOW_MARKERS,
    startup_lazy_loading_summary,
)


def test_phase436_main_window_lazy_markers_present():
    source = (ROOT / "alrajhi_client" / "views" / "main_window.py").read_text(encoding="utf-8")
    for marker in REQUIRED_MAIN_WINDOW_MARKERS:
        assert marker in source


def test_phase436_all_manifest_page_keys_have_lazy_factory_specs():
    source = (ROOT / "alrajhi_client" / "views" / "main_window.py").read_text(encoding="utf-8")
    for marker in REQUIRED_LAZY_FACTORY_KEYS:
        assert marker in source


def test_phase436_heavy_workspace_imports_are_not_eager():
    source = (ROOT / "alrajhi_client" / "views" / "main_window.py").read_text(encoding="utf-8")
    for forbidden in FORBIDDEN_EAGER_IMPORTS:
        assert forbidden not in source


def test_phase436_old_eager_construction_path_removed():
    source = (ROOT / "alrajhi_client" / "views" / "main_window.py").read_text(encoding="utf-8")
    for forbidden in FORBIDDEN_EAGER_CONSTRUCTION_PATTERNS:
        assert forbidden not in source


def test_phase436_contract_summary_ready():
    summary = startup_lazy_loading_summary(ROOT)
    assert summary["ready"] is True
    assert summary["issues"] == 0
    assert summary["checks"] >= 55
