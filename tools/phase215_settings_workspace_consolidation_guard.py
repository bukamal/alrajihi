# -*- coding: utf-8 -*-
"""Phase 215 guard: settings workspace exposes unified contracts.

This is a static guard so it can run in CI without PyQt5.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETTINGS_WIDGET = ROOT / "alrajhi_client" / "views" / "widgets" / "settings_widget.py"
TRANSLATOR = ROOT / "alrajhi_client" / "i18n" / "translator.py"
SERVICE = ROOT / "alrajhi_client" / "core" / "services" / "settings_service.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    widget = SETTINGS_WIDGET.read_text(encoding="utf-8")
    trans = TRANSLATOR.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")

    require("create_contracts_tab" in widget, "SettingsWidget must expose the unified contracts tab")
    require("save_contracts_settings" in widget, "SettingsWidget must persist unified contract settings")
    require("settings_contracts_tab" in widget, "SettingsWidget must add the unified contracts tab to QTabWidget")

    required_keys = [
        "restaurant/enabled",
        "manufacturing/enabled",
        "inventory/enabled",
        "finance/enabled",
        "reports/enabled",
        "users/enabled",
        "parties/enabled",
        "categories/enabled",
        "branches/enabled",
        "pos/operations/allow_checkout",
        "pos/operations/allow_print_receipt",
        "restaurant/operations/allow_send_kitchen",
        "restaurant/operations/allow_print_kitchen_ticket",
        "inventory/operations/allow_transfer_create",
        "inventory/operations/allow_print",
        "manufacturing/operations/allow_print",
        "reports/operations/allow_export",
        "finance/operations/allow_expense_create",
        "finance/operations/allow_voucher_create",
        "barcode/scanner/min_length",
        "materials/barcode/default_symbology",
    ]
    missing = [key for key in required_keys if key not in widget]
    require(not missing, f"Unified contracts tab is missing settings keys: {missing}")

    for method in [
        "get_pos_settings",
        "get_restaurant_settings",
        "get_manufacturing_settings",
        "get_inventory_settings",
        "get_finance_settings",
        "get_report_settings",
        "get_material_settings",
        "get_user_settings",
        "get_party_settings",
        "get_category_settings",
        "get_branch_settings",
    ]:
        require(f"def {method}" in service, f"SettingsService is missing {method}")

    translation_keys = [
        "settings_contracts_tab",
        "settings_contracts_title",
        "settings_modules_title",
        "settings_pos_contract_title",
        "settings_restaurant_contract_title",
        "settings_barcode_contract_title",
        "settings_contracts_saved",
    ]
    for key in translation_keys:
        require(key in trans, f"Missing Phase215 translation key: {key}")

    print("phase215_settings_workspace_consolidation_guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
