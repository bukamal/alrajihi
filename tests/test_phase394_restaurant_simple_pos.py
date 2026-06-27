# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_restaurant_page_routes_to_simple_pos_widget():
    main_window = read("alrajhi_client/views/main_window.py")
    assert "from views.restaurant.restaurant_simple_pos_widget import RestaurantSimplePOSWidget" in main_window
    assert "'restaurant': RestaurantSimplePOSWidget" in main_window
    manifest = read("alrajhi_client/workspace/registry/ui_manifest.py")
    assert 'factory_name="RestaurantSimplePOSWidget"' in manifest
    assert '"simple_invoice_lines"' in manifest
    assert '"kitchen_queue"' not in manifest.split('"restaurant": WorkspaceManifest', 1)[1].split('"cafe": WorkspaceManifest', 1)[0]


def test_simple_widget_has_three_operational_sections_and_invoice_columns():
    src = read("alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py")
    assert "restaurantSimpleCategoryButton" in src
    assert "restaurantSimpleItemButton" in src
    assert "restaurantSimpleInvoiceTable" in src
    assert "restaurant.simple_categories" in src
    assert "restaurant.simple_items" in src
    assert "restaurant.simple_invoice" in src
    for key in ["item_name", "quantity", "unit_price", "total", "notes"]:
        assert key in src


def test_simple_widget_uses_pos_checkout_without_kitchen_surface():
    src = read("alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py")
    assert "checkout_simple_pos_session" in src
    assert "mark_session_lines_served" in src
    assert "send_to_kitchen" not in src
    assert "KitchenDisplayWidget" not in src
    assert "RestaurantTableMapWidget" not in src


def test_restaurant_service_and_gateways_support_simple_pos_path():
    service = read("alrajhi_client/core/services/restaurant_service.py")
    local_gateway = read("alrajhi_client/gateways/local/restaurant_gateway.py")
    remote_gateway = read("alrajhi_client/gateways/remote/restaurant_gateway.py")
    abstract_gateway = read("alrajhi_client/gateways/restaurant_gateway.py")
    for src in [service, local_gateway, remote_gateway, abstract_gateway]:
        assert "list_menu_categories" in src
        assert "update_order_line" in src
        assert "mark_session_lines_served" in src
        assert "checkout_simple_pos_session" in src


def test_translation_keys_cover_four_languages():
    tr = read("alrajhi_client/i18n/translator.py")
    for lang in ["'ar'", "'de'", "'en'", "'fr'"]:
        assert lang in tr
    for key in [
        "restaurant.simple_pos_title",
        "restaurant.simple_categories",
        "restaurant.simple_items",
        "restaurant.simple_invoice",
        "restaurant.simple_checkout",
    ]:
        assert key in tr
