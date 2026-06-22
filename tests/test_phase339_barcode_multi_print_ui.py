# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_phase339_profile_aware_batch_dialog_routes_to_unified_browser_printing():
    dialog = read("alrajhi_client/views/dialogs/batch_print_dialog.py")
    assert "profile_id" in dialog
    assert "barcode_profile_candidates" in dialog
    assert "normalize_dialog_rows" in dialog
    assert "barcode_profile_labels_print" in dialog
    assert "barcode_labels_print_settings" not in dialog or "profile_id" in dialog
    assert "class BatchPrintDialog" in dialog


def test_phase339_candidate_providers_cover_items_apparel_restaurant_cafe():
    provider = read("alrajhi_client/printing/barcode_multi_print.py")
    for profile in (
        "items.default",
        "apparel.variant_labels",
        "restaurant.menu_items",
        "restaurant.table_labels",
        "cafe.products",
        "cafe.modifier_labels",
    ):
        assert profile in provider
    assert "apparel_variant_label_candidates" in provider
    assert "restaurant_table_label_candidates" in provider
    assert "cafe_modifier_label_candidates" in provider
    assert "normalize_barcode_items" in provider


def test_phase339_apparel_workspace_exposes_variant_barcode_buttons():
    apparel = read("alrajhi_client/views/apparel/apparel_workspace_widget.py")
    assert "print_selected_variant_barcodes" in apparel
    assert "batch_print_variant_barcodes" in apparel
    assert "apparel.variant_labels" in apparel
    assert "variant_barcode" in apparel
    assert "BatchPrintDialog" in apparel


def test_phase339_restaurant_and_cafe_shell_expose_profile_barcode_buttons():
    restaurant = read("alrajhi_client/views/restaurant/restaurant_dashboard.py")
    assert "print_restaurant_menu_barcodes" in restaurant
    assert "print_restaurant_table_barcodes" in restaurant
    assert "print_cafe_product_barcodes" in restaurant
    assert "print_cafe_modifier_barcodes" in restaurant
    assert "restaurant.menu_items" in restaurant
    assert "restaurant.table_labels" in restaurant
    assert "cafe.products" in restaurant
    assert "cafe.modifier_labels" in restaurant
    assert "BatchPrintDialog" in restaurant


def test_phase339_release_gate_registered_and_documented():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert '(339, "BARCODE_MULTI_PRINT_UI")' in gate
    assert '(339, "barcode_multi_print_ui")' in gate
    assert "tests/test_phase339_barcode_multi_print_ui.py" in gate
    assert 'ReleaseGateCheck("barcode_multi_print_ui"' in gate
    assert (ROOT / "PHASE339_BARCODE_MULTI_PRINT_UI.md").exists()
