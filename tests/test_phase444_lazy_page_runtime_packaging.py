# -*- coding: utf-8 -*-
from __future__ import annotations

from alrajhi_client.workspace.quality.lazy_page_runtime_packaging_audit import (
    run_audit,
    load_page_factory_specs,
    load_packaging_manifest,
    module_exists,
    is_collected,
)
from alrajhi_client.workspace.quality.lazy_page_runtime_packaging_contract import (
    REQUIRED_COLLECT_SUBMODULES,
    CRITICAL_LAZY_PAGE_IDS,
)


def test_critical_lazy_page_specs_exist():
    specs = load_page_factory_specs()
    missing = sorted(CRITICAL_LAZY_PAGE_IDS - set(specs))
    assert not missing
    for page_id in CRITICAL_LAZY_PAGE_IDS:
        module, _class_name = specs[page_id]
        assert module.startswith("alrajhi_client."), page_id
        assert module_exists(module), module


def test_lazy_page_modules_are_collected_or_hidden():
    specs = load_page_factory_specs()
    collect, hidden = load_packaging_manifest()
    for page_id, (module, _class_name) in specs.items():
        assert module in hidden or is_collected(module, collect), (page_id, module)


def test_required_view_collect_submodules_are_present():
    collect, _hidden = load_packaging_manifest()
    assert REQUIRED_COLLECT_SUBMODULES <= collect


def test_phase444_audit_passes():
    summary = run_audit(write_outputs=True)
    assert summary["ok"], summary["errors"]
    assert summary["spec_count"] >= len(CRITICAL_LAZY_PAGE_IDS)
