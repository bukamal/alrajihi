# -*- coding: utf-8 -*-
"""Phase 373 tests: remove visible main/sub prefixes from workspace tabs."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "alrajhi_client"))


def _load_policy():
    import importlib.util
    import sys as _sys

    spec = importlib.util.spec_from_file_location(
        "phase373_tab_label_policy", ROOT / "alrajhi_client/shell/tab_label_policy.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    _sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_tab_labels_show_business_title_only():
    module = _load_policy()
    BRANDED_TAB_PHASE = module.BRANDED_TAB_PHASE
    compose_tab_label = module.compose_tab_label

    assert BRANDED_TAB_PHASE >= 373
    main = compose_tab_label("sales_invoices", "فواتير البيع")
    sub = compose_tab_label("invoice:sale:new", "فاتورة بيع جديدة")

    assert main.kind == "main"
    assert sub.kind == "sub"
    assert main.display_text == "فواتير البيع"
    assert sub.display_text == "فاتورة بيع جديدة"
    assert main.tooltip == "فواتير البيع"
    assert sub.tooltip == "فاتورة بيع جديدة"


def test_visible_labels_do_not_include_old_prefixes():
    compose_tab_label = _load_policy().compose_tab_label

    forbidden = ("رئيسي ·", "فرعي ·", "رئيسية ·", "فرعية ·", "رئيسي —", "فرعي —")
    for tab_id, title in [
        ("materials", "المواد"),
        ("settings:print", "إعدادات الطباعة"),
        ("warehouse:1", "المستودع"),
    ]:
        identity = compose_tab_label(tab_id, title)
        assert not any(identity.display_text.startswith(prefix) for prefix in forbidden)
        assert not any(identity.tooltip.startswith(prefix) for prefix in forbidden)


def test_tab_kind_metadata_remains_available():
    module = _load_policy()
    compose_tab_label = module.compose_tab_label
    label_for_kind = module.label_for_kind
    tab_kind_for_id = module.tab_kind_for_id

    assert tab_kind_for_id("sales_invoices") == "main"
    assert tab_kind_for_id("invoice:sale:new") == "sub"
    assert label_for_kind("main") == "main"
    assert label_for_kind("sub") == "sub"
    assert compose_tab_label("invoice:sale:new", "فاتورة").label == "sub"


def test_phase373_contract_is_clean():
    from workspace.quality.tab_plain_title_contract import tab_plain_title_summary

    summary = tab_plain_title_summary(ROOT)
    assert summary["ready"] is True
    assert summary["issues"] == 0
    assert summary["checks"] >= 18
