# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_phase331_registry_covers_primary_pages_and_action_bar_policy():
    from workspace.registry import PAGE_MANIFESTS, page_meta_keys, page_factory_ids, should_show_action_bar

    required = {
        "dashboard",
        "pos",
        "sales_invoices",
        "purchase_invoices",
        "items",
        "reports",
        "settings",
        "restaurant",
        "cafe",
        "apparel",
    }
    assert required.issubset(PAGE_MANIFESTS.keys())
    assert required.issubset(set(page_factory_ids()))
    assert page_meta_keys()["apparel"] == ("apparel.workspace_title", "nav_apparel")
    # Phase 333 keeps the dashboard action strip visible but contract-limited
    # to refresh/theme/screenshot/user only.
    assert should_show_action_bar("dashboard") is True
    assert should_show_action_bar("sales_invoices") is True
    assert should_show_action_bar("purchase_invoices") is True


def test_phase331_registry_tracks_tables_for_column_rollout():
    from workspace.registry import PAGE_MANIFESTS, table_ids_for_page

    assert "lines" in table_ids_for_page("sales_invoices")
    assert "lines" in table_ids_for_page("purchase_invoices")
    assert {"variants", "matrix", "reports"}.issubset(set(table_ids_for_page("apparel")))
    for page_id, manifest in PAGE_MANIFESTS.items():
        for table in manifest.table_specs:
            assert table.settings_prefix.startswith(f"ui/columns/{page_id}/")
            assert table.table_type in {"editable_line", "read_only_list", "operational", "matrix", "report"}


def test_phase331_barcode_profiles_define_final_endpoint_scope():
    from workspace.registry import BARCODE_PRINT_PROFILES, barcode_profile_ids

    required = {
        "items.default",
        "apparel.variant_labels",
        "restaurant.menu_items",
        "restaurant.table_labels",
        "cafe.products",
        "cafe.modifier_labels",
    }
    assert required.issubset(BARCODE_PRINT_PROFILES.keys())
    assert set(barcode_profile_ids("apparel")) == {"apparel.variant_labels"}
    assert set(barcode_profile_ids("restaurant")) == {"restaurant.menu_items", "restaurant.table_labels"}
    assert set(barcode_profile_ids("cafe")) == {"cafe.products", "cafe.modifier_labels"}
    for profile in BARCODE_PRINT_PROFILES.values():
        assert profile.supports_multi_print is True
        assert profile.browser_html_only is True
        assert profile.settings_prefix.startswith("printing/barcode/")
        assert profile.default_template_id
        assert "barcode_text" in profile.printable_fields or "qr" in profile.printable_fields


def test_phase331_navigation_visibility_and_main_window_consume_registry():
    visibility = read("alrajhi_client/workspace/navigation/module_visibility_policy.py")
    main_window = read("alrajhi_client/views/main_window.py")
    assert "PAGE_MODULE_KEYS = {pid: manifest.module_checks for pid, manifest in PAGE_MANIFESTS.items()}" in visibility
    assert "PAGE_META_KEYS = page_meta_keys()" in main_window
    assert "NAV_GROUP_BY_PAGE = page_navigation_groups()" in main_window
    assert "page_factories = [(key, factory_by_key[key]) for key in page_factory_ids() if key in factory_by_key]" in main_window
    assert "self._apply_action_bar_contract_for_tab(pid)" in main_window


def test_phase331_release_gate_registered_and_documented():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert '(331, "UI_REGISTRY_AND_SHELL_MANIFEST")' in gate
    assert "tests/test_phase331_ui_registry_shell_manifest.py" in gate
    assert 'ReleaseGateCheck("ui_registry_shell_manifest"' in gate
    assert (ROOT / "PHASE331_UI_REGISTRY_AND_SHELL_MANIFEST.md").exists()
