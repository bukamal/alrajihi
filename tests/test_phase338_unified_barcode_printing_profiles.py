# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_phase338_barcode_profile_options_cover_all_final_scopes():
    from workspace.registry import BARCODE_PRINT_PROFILES, barcode_profile_settings_prefixes
    from printing.barcode_profiles import barcode_profile_options, normalize_barcode_item

    required = {
        "items.default",
        "apparel.variant_labels",
        "restaurant.menu_items",
        "restaurant.table_labels",
        "cafe.products",
        "cafe.modifier_labels",
    }
    assert required.issubset(BARCODE_PRINT_PROFILES)
    prefixes = barcode_profile_settings_prefixes()
    assert prefixes["apparel.variant_labels"] == "printing/barcode/apparel/variant_labels"
    for profile_id in required:
        opts = barcode_profile_options(profile_id)
        assert opts["profile_id"] == profile_id
        assert opts["browser_html_only"] is True
        assert opts["supports_multi_print"] is True
        assert opts["template_id"] == BARCODE_PRINT_PROFILES[profile_id].default_template_id
        assert str(BARCODE_PRINT_PROFILES[profile_id].settings_prefix).startswith("printing/barcode/")

    apparel = normalize_barcode_item({
        "item_name": "قميص",
        "color": "أبيض",
        "size": "L",
        "sku": "SHIRT-W-L",
        "variant_barcode": "VAR-001",
        "barcode": "BASE-001",
    }, "apparel.variant_labels")
    assert apparel["barcode"] == "VAR-001"
    assert apparel["variant_color"] == "أبيض"
    assert apparel["variant_size"] == "L"
    assert apparel["variant_code"] == "SHIRT-W-L"


def test_phase338_barcode_label_renderer_supports_sector_specific_fields_without_print_islands():
    service = read("alrajhi_client/core/services/barcode_label_service.py")
    printing = read("alrajhi_client/printing/printing_service.py")
    profiles = read("alrajhi_client/printing/barcode_profiles.py")

    assert "show_variant_color_size" in service
    assert "show_variant_code" in service
    assert "show_table_zone" in service
    assert "show_modifier_group" in service
    assert "qr_value" in service
    assert "profile-" in service and "data-template" in service
    assert "barcode_profile_options" in printing
    assert "normalize_barcode_items" in printing
    assert "barcode_profile_labels_html" in printing
    assert "barcode_profile_labels_print" in printing
    assert "Browser HTML" in profiles or "Browser-HTML" in profiles
    assert "parent material barcode" in profiles


def test_phase338_settings_expose_profile_specific_barcode_controls():
    settings = read("alrajhi_client/features/settings/settings_document_tabs.py")
    service = read("alrajhi_client/core/services/settings_service.py")

    assert "class BarcodeProfilesSettingsTab" in settings
    assert "printing/barcode/apparel/variant_labels/show_variant_color_size" in settings
    assert "printing/barcode/restaurant/table_labels/show_table_zone" in settings
    assert "printing/barcode/cafe/modifier_labels/show_modifier_group" in settings
    assert "'barcode_profiles': BarcodeProfilesSettingsTab" in settings
    assert "def get_barcode_profile_settings" in service
    assert "barcode_profile_options(profile_id)" in service


def test_phase338_release_gate_registered_and_documented():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert '(338, "UNIFIED_BARCODE_PRINTING_PROFILES")' in gate
    assert '(338, "unified_barcode_printing_profiles")' in gate
    assert "tests/test_phase338_unified_barcode_printing_profiles.py" in gate
    assert 'ReleaseGateCheck("unified_barcode_printing_profiles"' in gate
    assert (ROOT / "PHASE338_UNIFIED_BARCODE_PRINTING_PROFILES.md").exists()
