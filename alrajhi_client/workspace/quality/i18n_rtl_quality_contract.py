# -*- coding: utf-8 -*-
"""Phase 422 i18n / RTL quality gate contract.

The project supports Arabic, German, English and French.  Arabic is the only
RTL UI language; every other supported language must be LTR.  This contract is
Qt-free so it can run in CI, packaging guards and release audits.
"""
from __future__ import annotations

I18N_RTL_QUALITY_CONTRACT = {
    "phase": 422,
    "name": "i18n / RTL Quality Gate",
    "supported_languages": ("ar", "de", "en", "fr"),
    "rtl_languages": ("ar",),
    "critical_surface_groups": {
        "shell": (
            "app_title", "nav_home", "nav_sales", "nav_purchases", "nav_inventory",
            "nav_manufacturing", "nav_parties", "nav_finance", "nav_admin",
            "nav_quick_actions", "nav_special_interfaces", "settings_header_title",
        ),
        "transactions": (
            "sales_invoice", "purchase_invoice", "sales_returns", "purchase_returns",
            "transaction_sales_invoice_new", "transaction_purchase_invoice_new",
            "transaction_sales_return_new", "transaction_purchase_return_new",
            "transaction_column_item", "transaction_column_unit", "transaction_column_qty",
            "transaction_column_price", "transaction_column_discount", "transaction_column_tax",
            "transaction_column_total", "transaction_column_notes", "transaction_column_cost",
            "module_activation_title", "module_activation_success", "module_activation_failed",
        ),
        "pos_restaurant_cafe": (
            "pos", "restaurant.dashboard", "restaurant.kitchen_display",
            "feature_activation_restaurant", "feature_activation_cafe", "feature_activation_apparel",
            "barcode.restaurant_menu_labels", "barcode.restaurant_table_labels",
            "barcode.cafe_product_labels", "barcode.cafe_modifier_labels",
        ),
        "settings_print_reports": (
            "language_label", "language_ar", "language_de", "language_en", "language_fr",
            "ui_language", "print_language", "report_language",
            "settings_print_language_label", "settings_print_templates_title",
            "settings_print_save", "settings_print_saved",
        ),
    },
    "runtime_direction_invariants": (
        "translator_declares_arabic_as_the_only_rtl_language",
        "settings_runtime_language_switch_applies_table_direction_tree",
        "main_window_applies_layout_direction_and_table_direction_tree",
        "main_menu_bar_receives_runtime_language_direction",
        "phase416_runtime_probe_captures_ar_rtl_and_de_ltr_shell_snapshots",
    ),
    "accepted_transition_risks": (
        "the monolithic translator module remains large until language packs are split by feature",
        "some legacy screens still carry explicit setLayoutDirection calls and are audited rather than removed in this phase",
        "visual RTL screenshots still require running the Phase416 harness on a machine with PyQt5",
    ),
}


def critical_keys() -> tuple[str, ...]:
    keys: list[str] = []
    for group in I18N_RTL_QUALITY_CONTRACT["critical_surface_groups"].values():
        keys.extend(group)
    return tuple(dict.fromkeys(keys))


def contract_summary() -> dict[str, object]:
    groups = I18N_RTL_QUALITY_CONTRACT["critical_surface_groups"]
    return {
        "phase": I18N_RTL_QUALITY_CONTRACT["phase"],
        "name": I18N_RTL_QUALITY_CONTRACT["name"],
        "supported_languages": I18N_RTL_QUALITY_CONTRACT["supported_languages"],
        "rtl_languages": I18N_RTL_QUALITY_CONTRACT["rtl_languages"],
        "surface_group_count": len(groups),
        "critical_key_count": len(critical_keys()),
        "runtime_direction_invariant_count": len(I18N_RTL_QUALITY_CONTRACT["runtime_direction_invariants"]),
        "accepted_transition_risks": I18N_RTL_QUALITY_CONTRACT["accepted_transition_risks"],
    }


__all__ = ["I18N_RTL_QUALITY_CONTRACT", "contract_summary", "critical_keys"]
