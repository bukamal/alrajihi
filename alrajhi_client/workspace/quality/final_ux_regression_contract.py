# -*- coding: utf-8 -*-
"""Final UX regression contract for the unified shell rollout.

Phase 340 is deliberately PyQt-free.  It checks the contracts introduced in
Phases 331-339 so future UI work cannot silently re-introduce isolated menus,
unregistered action buttons, table columns that bypass print/export settings,
or sector-specific barcode printing islands.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Sequence

ROOT = Path(__file__).resolve().parents[3]
CLIENT = ROOT / "alrajhi_client"


@dataclass(frozen=True)
class FinalUxCheck:
    key: str
    category: str
    title: str
    ok: bool
    detail: str = ""

    def as_row(self) -> dict[str, object]:
        return {
            "key": self.key,
            "category": self.category,
            "title": self.title,
            "ok": bool(self.ok),
            "detail": self.detail,
        }


REQUIRED_PAGES: tuple[str, ...] = (
    "dashboard",
    "sales_invoices",
    "purchase_invoices",
    "pos",
    "restaurant",
    "cafe",
    "apparel",
    "settings",
)

REQUIRED_TABLE_CONTRACTS: tuple[str, ...] = (
    "sales_invoices.lines",
    "purchase_invoices.lines",
    "returns.lines",
    "purchase_returns.lines",
    "pos.lines",
    "restaurant.order_lines",
    "restaurant.kds_tickets",
    "restaurant.kds_lines",
    "cafe.order_lines",
    "cafe.preparation_tickets",
    "cafe.preparation_lines",
    "apparel.variants",
    "apparel.reports",
)

REQUIRED_BARCODE_PROFILES: tuple[str, ...] = (
    "items.default",
    "apparel.variant_labels",
    "restaurant.menu_items",
    "restaurant.table_labels",
    "cafe.products",
    "cafe.modifier_labels",
)

REQUIRED_BARCODE_SETTINGS_PREFIXES: tuple[str, ...] = (
    "printing/barcode/items/default",
    "printing/barcode/apparel/variant_labels",
    "printing/barcode/restaurant/menu_items",
    "printing/barcode/restaurant/table_labels",
    "printing/barcode/cafe/products",
    "printing/barcode/cafe/modifier_labels",
)


def _source(path: str) -> str:
    try:
        return (ROOT / path).read_text(encoding="utf-8")
    except Exception:
        return ""


def _ok(key: str, category: str, title: str, detail: str = "") -> FinalUxCheck:
    return FinalUxCheck(key, category, title, True, detail)


def _fail(key: str, category: str, title: str, detail: str) -> FinalUxCheck:
    return FinalUxCheck(key, category, title, False, detail)


def _check_ui_registry() -> list[FinalUxCheck]:
    from workspace.registry import (
        ACTION_SPECS,
        PAGE_MANIFESTS,
        action_keys_for_page,
        navigation_menus,
        table_ids_for_page,
    )

    checks: list[FinalUxCheck] = []
    missing_pages = [page for page in REQUIRED_PAGES if page not in PAGE_MANIFESTS]
    checks.append(
        _ok("required_pages_registered", "registry", "Required workspaces are registered")
        if not missing_pages
        else _fail("required_pages_registered", "registry", "Required workspaces are registered", f"missing: {missing_pages}")
    )

    invalid_actions: list[str] = []
    for page_id, manifest in PAGE_MANIFESTS.items():
        for action_key in manifest.action_keys:
            if action_key not in ACTION_SPECS:
                invalid_actions.append(f"{page_id}:{action_key}")
    checks.append(
        _ok("workspace_actions_known", "actions", "Every workspace action is declared in ACTION_SPECS")
        if not invalid_actions
        else _fail("workspace_actions_known", "actions", "Every workspace action is declared in ACTION_SPECS", ", ".join(invalid_actions))
    )

    dashboard_actions = tuple(action_keys_for_page("dashboard"))
    checks.append(
        _ok("dashboard_minimal_action_surface", "actions", "Dashboard only exposes refresh/theme/screenshot/user", str(dashboard_actions))
        if dashboard_actions == ("refresh", "theme", "screenshot", "user")
        else _fail("dashboard_minimal_action_surface", "actions", "Dashboard only exposes refresh/theme/screenshot/user", str(dashboard_actions))
    )

    menu_page_refs: list[str] = []
    bad_menu_refs: list[str] = []
    for menu in navigation_menus():
        for entry in menu.entries:
            if entry.page_id:
                menu_page_refs.append(entry.page_id)
                if entry.page_id not in PAGE_MANIFESTS:
                    bad_menu_refs.append(f"{menu.key}:{entry.page_id}")
    checks.append(
        _ok("navigation_entries_resolve", "navigation", "Main navigation page references resolve to registered workspaces")
        if not bad_menu_refs and menu_page_refs
        else _fail("navigation_entries_resolve", "navigation", "Main navigation page references resolve to registered workspaces", f"bad={bad_menu_refs} total_refs={len(menu_page_refs)}")
    )

    manifest_tables_without_contract_identity = [
        f"{page_id}:{table.table_id}"
        for page_id, manifest in PAGE_MANIFESTS.items()
        for table in manifest.table_specs
        if not table.settings_prefix.startswith(f"ui/columns/{page_id}/")
    ]
    checks.append(
        _ok("manifest_table_settings_scoped", "columns", "Workspace table settings are scoped under ui/columns/<page>/<table>")
        if not manifest_tables_without_contract_identity
        else _fail("manifest_table_settings_scoped", "columns", "Workspace table settings are scoped under ui/columns/<page>/<table>", ", ".join(manifest_tables_without_contract_identity))
    )

    return checks


def _check_design_tokens() -> list[FinalUxCheck]:
    from theme.brand import BRAND

    expectations = {
        "nav_height": 70,
        "nav_icon_size": 24,
        "nav_font_px": 12,
        "action_bar_height": 50,
        "action_button_min_height": 36,
        "input_min_height": 32,
    }
    bad = [f"{key}={BRAND.get(key)}<min {minimum}" for key, minimum in expectations.items() if int(BRAND.get(key, 0) or 0) < minimum]
    return [
        _ok("design_tokens_minimum_shell_metrics", "design", "Menu/action/table typography metrics are centralized and readable")
        if not bad
        else _fail("design_tokens_minimum_shell_metrics", "design", "Menu/action/table typography metrics are centralized and readable", ", ".join(bad))
    ]


def _check_table_contracts() -> list[FinalUxCheck]:
    from workspace.tables.column_contract import validate_unique_keys
    from workspace.tables.table_column_registry import TABLE_COLUMN_CONTRACTS

    checks: list[FinalUxCheck] = []
    missing = [cid for cid in REQUIRED_TABLE_CONTRACTS if cid not in TABLE_COLUMN_CONTRACTS]
    checks.append(
        _ok("required_table_contracts_registered", "columns", "Required business tables have universal column contracts")
        if not missing
        else _fail("required_table_contracts_registered", "columns", "Required business tables have universal column contracts", f"missing: {missing}")
    )

    duplicate_keys = [cid for cid, contract in TABLE_COLUMN_CONTRACTS.items() if not validate_unique_keys(contract.columns)]
    checks.append(
        _ok("table_column_keys_unique", "columns", "Column keys are unique per contract")
        if not duplicate_keys
        else _fail("table_column_keys_unique", "columns", "Column keys are unique per contract", ", ".join(duplicate_keys))
    )

    bad_settings: list[str] = []
    missing_required_visibility: list[str] = []
    for cid, contract in TABLE_COLUMN_CONTRACTS.items():
        if not contract.settings_prefix.startswith(f"ui/columns/{contract.page_id}/{contract.table_id}"):
            bad_settings.append(f"{cid}:prefix={contract.settings_prefix}")
        for column in contract.columns:
            if not column.settings_key.startswith(contract.settings_prefix + "/"):
                bad_settings.append(f"{cid}.{column.key}:settings={column.settings_key}")
            if column.required and column.key not in contract.default_visible_keys():
                missing_required_visibility.append(f"{cid}.{column.key}")
    checks.append(
        _ok("table_column_settings_scoped", "columns", "Column settings keys are scoped to their table contract")
        if not bad_settings
        else _fail("table_column_settings_scoped", "columns", "Column settings keys are scoped to their table contract", "; ".join(bad_settings[:12]))
    )
    checks.append(
        _ok("required_columns_visible_by_default", "columns", "Required columns stay visible by default")
        if not missing_required_visibility
        else _fail("required_columns_visible_by_default", "columns", "Required columns stay visible by default", ", ".join(missing_required_visibility))
    )

    empty_print_export = [
        cid for cid, contract in TABLE_COLUMN_CONTRACTS.items()
        if contract.printable and not contract.default_printable_keys() or contract.exportable and not contract.default_exportable_keys()
    ]
    checks.append(
        _ok("print_export_defaults_exist", "columns", "Printable/exportable contracts expose default columns")
        if not empty_print_export
        else _fail("print_export_defaults_exist", "columns", "Printable/exportable contracts expose default columns", ", ".join(empty_print_export))
    )
    return checks


def _check_column_output_mapping() -> list[FinalUxCheck]:
    source_custom = _source("alrajhi_client/views/custom_table_view.py")
    source_output = _source("alrajhi_client/workspace/tables/column_output.py")
    checks: list[FinalUxCheck] = []
    checks.append(
        _ok("custom_table_uses_contract_for_output", "columns", "CustomTableView routes display/print/export through column contract")
        if "keys_for_output" in source_custom and "purpose in {\"print\"" in source_custom and "column_contract_id" in source_custom
        else _fail("custom_table_uses_contract_for_output", "columns", "CustomTableView routes display/print/export through column contract", "missing keys_for_output/print-export contract wiring")
    )
    checks.append(
        _ok("column_output_separates_purposes", "columns", "Column output separates visible, printable and exportable settings")
        if "visible" in source_output and "printable" in source_output and "exportable" in source_output and "filter_dict_for_output" in source_output
        else _fail("column_output_separates_purposes", "columns", "Column output separates visible, printable and exportable settings", "column_output.py missing purpose split")
    )
    return checks


def _check_keyboard_policy() -> list[FinalUxCheck]:
    custom = _source("alrajhi_client/views/custom_table_view.py")
    editable = _source("alrajhi_client/ui/editable_smart_grid.py")
    transaction_grid = _source("alrajhi_client/features/transactions/grids/transaction_line_grid.py")
    policy = _source("alrajhi_client/ui/table_keyboard_policy.py")
    checks: list[FinalUxCheck] = []
    checks.append(
        _ok("keyboard_policy_contract_exists", "keyboard", "Unified Enter/Shift+Enter/Esc table policy exists")
        if "class StandardTableKeyboardMixin" in policy and "Shift" in policy and "Enter" in policy and "Esc" in policy
        else _fail("keyboard_policy_contract_exists", "keyboard", "Unified Enter/Shift+Enter/Esc table policy exists", "table_keyboard_policy.py incomplete")
    )
    checks.append(
        _ok("keyboard_policy_wired_to_editable_tables", "keyboard", "Keyboard policy is wired to editable grids without forcing list tables into cell selection")
        if "StandardTableKeyboardMixin" in custom and "Phase389" in custom and "StandardTableKeyboardMixin" in editable and "init_standard_table_keyboard" in editable and "init_standard_table_keyboard" in transaction_grid
        else _fail("keyboard_policy_wired_to_editable_tables", "keyboard", "Keyboard policy is wired to editable grids without forcing list tables into cell selection", "editable grid classes missing mixin/init or CustomTableView lacks Phase389 row-action boundary")
    )
    return checks


def _check_barcode_contracts() -> list[FinalUxCheck]:
    from workspace.registry import BARCODE_PRINT_PROFILES
    from printing.barcode_multi_print import PROFILE_CANDIDATE_PROVIDERS
    from printing.barcode_profiles import barcode_profile_options

    checks: list[FinalUxCheck] = []
    missing = [pid for pid in REQUIRED_BARCODE_PROFILES if pid not in BARCODE_PRINT_PROFILES]
    checks.append(
        _ok("barcode_profiles_registered", "barcode", "Items/apparel/restaurant/cafe barcode profiles are registered")
        if not missing
        else _fail("barcode_profiles_registered", "barcode", "Items/apparel/restaurant/cafe barcode profiles are registered", f"missing: {missing}")
    )

    bad_profile_options: list[str] = []
    for pid in REQUIRED_BARCODE_PROFILES:
        spec = BARCODE_PRINT_PROFILES.get(pid)
        if spec is None:
            continue
        opts = barcode_profile_options(pid)
        if not spec.supports_multi_print or not spec.browser_html_only:
            bad_profile_options.append(f"{pid}:spec flags")
        if opts.get("supports_multi_print") is not True or opts.get("browser_html_only") is not True:
            bad_profile_options.append(f"{pid}:options flags")
        if not str(spec.settings_prefix).startswith("printing/barcode/"):
            bad_profile_options.append(f"{pid}:settings={spec.settings_prefix}")
    checks.append(
        _ok("barcode_profiles_multi_print_browser_html", "barcode", "Barcode profiles are multi-print and Browser-HTML only")
        if not bad_profile_options
        else _fail("barcode_profiles_multi_print_browser_html", "barcode", "Barcode profiles are multi-print and Browser-HTML only", ", ".join(bad_profile_options))
    )

    missing_providers = [pid for pid in REQUIRED_BARCODE_PROFILES if pid not in PROFILE_CANDIDATE_PROVIDERS]
    checks.append(
        _ok("barcode_profile_candidate_providers", "barcode", "Every barcode profile has a multi-print candidate provider")
        if not missing_providers
        else _fail("barcode_profile_candidate_providers", "barcode", "Every barcode profile has a multi-print candidate provider", f"missing: {missing_providers}")
    )

    printing = _source("alrajhi_client/printing/printing_service.py")
    batch_dialog = _source("alrajhi_client/views/dialogs/batch_print_dialog.py")
    checks.append(
        _ok("barcode_printing_service_path", "barcode", "Barcode labels route through unified printing_service Browser HTML path")
        if "barcode_profile_labels_html" in printing and "barcode_profile_labels_print" in printing and ("browser_html" in printing.lower() or "browser html" in printing.lower())
        else _fail("barcode_printing_service_path", "barcode", "Barcode labels route through unified printing_service Browser HTML path", "printing_service missing profile functions/browser HTML")
    )
    checks.append(
        _ok("barcode_batch_dialog_profile_aware", "barcode", "Batch print dialog is profile-aware")
        if "profile_id" in batch_dialog and "barcode_profile_candidates" in batch_dialog and "barcode_profile_labels_print" in batch_dialog
        else _fail("barcode_batch_dialog_profile_aware", "barcode", "Batch print dialog is profile-aware", "BatchPrintDialog missing profile-aware route")
    )
    return checks


def final_ux_regression_checks() -> tuple[FinalUxCheck, ...]:
    checks: list[FinalUxCheck] = []
    for fn in (
        _check_ui_registry,
        _check_design_tokens,
        _check_table_contracts,
        _check_column_output_mapping,
        _check_keyboard_policy,
        _check_barcode_contracts,
    ):
        try:
            checks.extend(fn())
        except Exception as exc:
            checks.append(_fail(fn.__name__, "runtime", fn.__name__, repr(exc)))
    return tuple(checks)


def final_ux_regression_issues() -> list[FinalUxCheck]:
    return [check for check in final_ux_regression_checks() if not check.ok]


def final_ux_regression_summary() -> dict[str, object]:
    checks = final_ux_regression_checks()
    categories: dict[str, int] = {}
    for check in checks:
        categories[check.category] = categories.get(check.category, 0) + 1
    issues = [check for check in checks if not check.ok]
    return {
        "phase": 340,
        "checks": len(checks),
        "categories": categories,
        "issues": len(issues),
        "ready": not issues,
    }


__all__ = [
    "FinalUxCheck",
    "REQUIRED_PAGES",
    "REQUIRED_TABLE_CONTRACTS",
    "REQUIRED_BARCODE_PROFILES",
    "final_ux_regression_checks",
    "final_ux_regression_issues",
    "final_ux_regression_summary",
]
