import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase294_kds_widget_is_python311_parse_safe():
    source = (ROOT / "alrajhi_client/views/restaurant/kitchen_display_widget.py").read_text(encoding="utf-8")
    ast.parse(source, feature_version=(3, 11))
    assert '{_("restaurant.lines_count")}' not in source


def test_phase294_restaurant_settings_contract_normalizes_routes():
    from features.restaurant.restaurant_settings_contract import (
        normalize_restaurant_settings,
        restaurant_print_route,
        restaurant_should_auto_print,
    )

    settings = normalize_restaurant_settings({
        "receipt_paper": "thermal80",
        "kitchen_ticket_paper": "58mm",
        "session_summary_paper": "bad-value",
        "default_payment_method": "mixed",
        "service_charge_percent": "7.5",
        "default_tax_percent": "15",
        "consume_inventory_on": "served",
        "printing": {
            "restaurant_receipt_printer": "Front Counter",
            "restaurant_kitchen_printer": "Kitchen Thermal",
            "restaurant_session_summary_printer": "Manager Printer",
        },
        "operations": {
            "auto_print_kitchen_ticket": True,
            "auto_print_receipt_after_checkout": False,
            "auto_print_session_summary_after_checkout": "true",
        },
    })

    assert settings["receipt_paper"] == "80mm"
    assert settings["kitchen_ticket_paper"] == "58mm"
    assert settings["session_summary_paper"] == "80mm"
    assert settings["service_charge_percent"] == "7.5"
    assert settings["default_tax_percent"] == "15"
    assert settings["consume_inventory_on"] == "served"
    assert restaurant_print_route("kitchen", settings)["printer"] == "Kitchen Thermal"
    assert restaurant_should_auto_print("kitchen", settings) is True
    assert restaurant_should_auto_print("receipt", settings) is False
    assert restaurant_should_auto_print("session_summary", settings) is True


def test_phase294_restaurant_printing_bridge_attaches_routes_in_source():
    bridge = (ROOT / "alrajhi_client/features/restaurant/restaurant_printing_bridge.py").read_text(encoding="utf-8")
    assert "def _route" in bridge
    assert "def _attach_route" in bridge
    assert "restaurant_print_route" in bridge
    assert "print_route" in bridge
    assert "session_summary_payload" in bridge

def test_phase294_contract_sources_are_wired():
    root = ROOT
    settings_service = (root / "alrajhi_client/core/services/settings_service.py").read_text(encoding="utf-8")
    settings_tabs = (root / "alrajhi_client/features/settings/settings_document_tabs.py").read_text(encoding="utf-8")
    bridge = (root / "alrajhi_client/features/restaurant/restaurant_printing_bridge.py").read_text(encoding="utf-8")
    ui = (root / "alrajhi_client/views/restaurant/restaurant_pos_widget.py").read_text(encoding="utf-8")
    release_gate = (root / "alrajhi_client/workspace/quality/release_gate_contract.py").read_text(encoding="utf-8")

    assert "restaurant_settings_contract" in settings_service
    assert "restaurant/printing/kitchen_printer" in settings_tabs
    assert "print_route" in bridge and "restaurant_print_route" in bridge
    assert "session_summary_print" in ui and "restaurant_should_auto_print" in ui
    assert "restaurant_settings_printer_routing" in release_gate
