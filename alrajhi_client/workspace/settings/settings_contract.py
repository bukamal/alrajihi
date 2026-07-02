# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping


NETWORK_REMOTE_AVAILABLE = "remote_available"
NETWORK_LOCAL_ONLY = "local_only"

VALUE_BOOL = "bool"
VALUE_STRING = "string"
VALUE_INT = "int"
VALUE_DECIMAL = "decimal"
VALUE_CHOICE = "choice"


@dataclass(frozen=True)
class SettingsKeyDescriptor:
    """A persistent setting key used by one or more shells.

    The contract is data-only so CI and PyInstaller builds can audit settings
    coverage without importing PyQt widgets or instantiating repositories.
    """

    key: str
    value_type: str = VALUE_STRING
    default: str = ""
    label_key: str = ""
    choices: tuple[str, ...] = ()
    required: bool = True
    network_synced: bool = True
    profile_aware: bool = True


@dataclass(frozen=True)
class SettingsScopeDescriptor:
    """Settings coverage declaration for a shell settings_scope.

    ``scope`` may be exact (``reports``) or a family prefix
    (``transactions`` covers ``transactions.sales_invoice`` and its list scope).
    """

    scope: str
    section_key: str
    title_key: str
    service_getter: str
    ui_sections: tuple[str, ...]
    keys: tuple[SettingsKeyDescriptor, ...]
    api_resource: str = "/api/settings/<path:key>"
    network_mode: str = NETWORK_REMOTE_AVAILABLE
    language_keys: tuple[str, ...] = ("language", "language/print", "language/report")
    currency_keys: tuple[str, ...] = ("base_currency", "display_currency", "currency_decimals", "number_format")
    print_keys: tuple[str, ...] = ("printing/invoice_template", "printing/report_template", "printing/show_logo")
    operation_key_prefixes: tuple[str, ...] = ()
    profile_aware: bool = True
    notes: str = ""

    @property
    def required_keys(self) -> tuple[str, ...]:
        return tuple(k.key for k in self.keys if k.required)

    def covers(self, settings_scope: str) -> bool:
        scope = normalize_settings_scope(settings_scope)
        if scope == self.scope:
            return True
        return bool(self.scope and scope.startswith(f"{self.scope}."))


def _key(key: str, value_type: str = VALUE_STRING, default: str = "", label_key: str = "", choices: tuple[str, ...] = (), *, required: bool = True) -> SettingsKeyDescriptor:
    return SettingsKeyDescriptor(key=key, value_type=value_type, default=default, label_key=label_key or key, choices=choices, required=required)


SETTINGS_SCOPE_DESCRIPTORS: tuple[SettingsScopeDescriptor, ...] = (
    SettingsScopeDescriptor(
        scope="transactions",
        section_key="transactions",
        title_key="settings.transactions",
        service_getter="get_transaction_settings",
        ui_sections=("transactions", "accounting", "inventory", "printing", "ui"),
        operation_key_prefixes=("transactions/operations",),
        keys=(
            _key("transactions/enabled", VALUE_BOOL, "true"),
            _key("invoice/sales_prefix", default="SAL-"),
            _key("invoice/purchase_prefix", default="PUR-"),
            _key("invoice/number_format", default="{PREFIX}{00000}"),
            _key("invoice/auto_numbering", VALUE_BOOL, "true"),
            _key("transactions/default_warehouse_id", required=False),
            _key("transactions/default_payment_method", VALUE_CHOICE, "cash", choices=("cash", "card", "credit", "bank_transfer")),
            _key("transactions/grid/auto_responsive", VALUE_BOOL, "true"),
            _key("transactions/show_profit", VALUE_BOOL, "true"),
            _key("transactions/show_cost", VALUE_BOOL, "true"),
            _key("transactions/default_preset", VALUE_CHOICE, "manager", choices=("compact", "cashier", "manager")),
            _key("barcode/scanner/min_length", VALUE_INT, "6"),
        ),
        print_keys=("printing/invoice_template", "printing/return_template", "printing/show_qr", "language/print"),
        notes="Invoice and return document shells; currency conversion is not performed here, only display/profile settings are declared.",
    ),
    SettingsScopeDescriptor(
        scope="materials",
        section_key="materials",
        title_key="settings.materials",
        service_getter="get_material_settings",
        ui_sections=("materials", "inventory", "printing"),
        operation_key_prefixes=("materials/operations", "materials/barcode", "materials/units"),
        keys=(
            _key("materials/default_unit", default="قطعة"),
            _key("materials/default_item_type", default="مخزون"),
            _key("materials/barcode/default_symbology", VALUE_CHOICE, "EAN13", choices=("EAN13", "CODE128")),
            _key("materials/barcode/auto_generate", VALUE_BOOL, "true"),
            _key("materials/barcode/allow_manual_edit", VALUE_BOOL, "true"),
            _key("materials/barcode/ean13_prefix", default="290"),
            _key("materials/units/require_unique_names", VALUE_BOOL, "true"),
            _key("materials/units/validate_unit_barcodes", VALUE_BOOL, "true"),
            _key("materials/security/prevent_opening_quantity_edit_after_activity", VALUE_BOOL, "true"),
        ),
        print_keys=("printing/barcode/label_size", "printing/barcode/symbology", "printing/barcode/show_price"),
        notes="Material master-data, units, barcode and label printing settings.",
    ),

    SettingsScopeDescriptor(
        scope="apparel",
        section_key="apparel",
        title_key="settings.apparel",
        service_getter="get_material_settings",
        ui_sections=("apparel", "materials", "inventory", "printing"),
        operation_key_prefixes=("apparel/operations", "materials/operations"),
        keys=(
            _key("apparel/enabled", VALUE_BOOL, "true"),
            _key("apparel/default_size_set", default="XS,S,M,L,XL,XXL"),
            _key("apparel/default_color_set", default="أبيض,أسود,أزرق,أحمر"),
            _key("apparel/barcode_required", VALUE_BOOL, "true"),
            _key("apparel/ui/density", VALUE_CHOICE, "comfortable", choices=("compact", "comfortable", "touch")),
        ),
        print_keys=("printing/barcode/label_size", "printing/barcode/symbology", "printing/barcode/show_price"),
        notes="Standalone apparel workspace settings. Product identity remains item-variant based, not unit based.",
    ),
    SettingsScopeDescriptor(
        scope="categories",
        section_key="categories",
        title_key="settings.categories",
        service_getter="get_category_settings",
        ui_sections=("categories",),
        operation_key_prefixes=("categories/operations",),
        keys=(
            _key("categories/enabled", VALUE_BOOL, "true"),
            _key("categories/ui/density", VALUE_CHOICE, "comfortable", choices=("compact", "comfortable", "touch")),
            _key("categories/operations/allow_create", VALUE_BOOL, "true"),
            _key("categories/operations/allow_edit", VALUE_BOOL, "true"),
            _key("categories/operations/allow_archive", VALUE_BOOL, "true"),
        ),
        currency_keys=(),
        print_keys=(),
    ),
    SettingsScopeDescriptor(
        scope="parties",
        section_key="parties",
        title_key="settings.parties",
        service_getter="get_party_settings",
        ui_sections=("parties", "ui"),
        operation_key_prefixes=("parties/operations",),
        keys=(
            _key("parties/default_credit_limit", VALUE_DECIMAL, "0", required=False),
            _key("parties/ui/density", VALUE_CHOICE, "comfortable", choices=("compact", "comfortable", "touch")),
            _key("parties/operations/allow_create", VALUE_BOOL, "true"),
            _key("parties/operations/allow_edit", VALUE_BOOL, "true"),
            _key("parties/operations/allow_archive", VALUE_BOOL, "true"),
            _key("parties/operations/allow_statement_print", VALUE_BOOL, "true"),
        ),
    ),
    SettingsScopeDescriptor(
        scope="finance",
        section_key="finance",
        title_key="settings.finance",
        service_getter="get_finance_settings",
        ui_sections=("finance", "accounting", "printing"),
        operation_key_prefixes=("finance/operations",),
        keys=(
            _key("finance/enabled", VALUE_BOOL, "true"),
            _key("finance/ui/density", VALUE_CHOICE, "comfortable", choices=("compact", "comfortable", "touch")),
            _key("finance/operations/allow_voucher_create", VALUE_BOOL, "true"),
            _key("finance/operations/allow_voucher_edit", VALUE_BOOL, "true"),
            _key("finance/operations/allow_voucher_print", VALUE_BOOL, "true"),
            _key("finance/operations/allow_expense_create", VALUE_BOOL, "true"),
            _key("finance/operations/allow_expense_print", VALUE_BOOL, "true"),
        ),
        print_keys=("printing/voucher_template", "printing/report_template"),
    ),
    SettingsScopeDescriptor(
        scope="inventory",
        section_key="inventory",
        title_key="settings.inventory",
        service_getter="get_inventory_settings",
        ui_sections=("inventory", "materials", "printing"),
        operation_key_prefixes=("inventory/operations",),
        keys=(
            _key("inventory/enabled", VALUE_BOOL, "true"),
            _key("inventory/default_warehouse_id", required=False),
            _key("inventory/allow_negative_stock", VALUE_BOOL, "false"),
            _key("inventory/warn_on_stock_exceed", VALUE_BOOL, "true"),
            _key("inventory/stock_read_mode", VALUE_CHOICE, "operational", choices=("operational", "dual", "ledger_trial", "ledger_authoritative")),
            _key("inventory/cost_method", VALUE_CHOICE, "AVERAGE", choices=("AVERAGE", "FIFO", "LIFO", "STANDARD", "LAST_PURCHASE")),
            _key("inventory/operations/allow_print", VALUE_BOOL, "true"),
        ),
        print_keys=("inventory/print_template", "printing/report_template"),
    ),
    SettingsScopeDescriptor(
        scope="branches",
        section_key="branches",
        title_key="settings.branches",
        service_getter="get_branch_settings",
        ui_sections=("branches", "security"),
        operation_key_prefixes=("branches/operations",),
        keys=(
            _key("branches/enabled", VALUE_BOOL, "true"),
            _key("branches/ui/density", VALUE_CHOICE, "comfortable", choices=("compact", "comfortable", "touch")),
            _key("branches/operations/allow_create", VALUE_BOOL, "true"),
            _key("branches/operations/allow_edit", VALUE_BOOL, "true"),
            _key("branches/operations/allow_archive", VALUE_BOOL, "true"),
            _key("branches/operations/allow_set_default", VALUE_BOOL, "true"),
        ),
        currency_keys=(),
        print_keys=(),
    ),
    SettingsScopeDescriptor(
        scope="manufacturing",
        section_key="manufacturing",
        title_key="settings.manufacturing",
        service_getter="get_manufacturing_settings",
        ui_sections=("manufacturing", "inventory", "printing"),
        operation_key_prefixes=("manufacturing/operations",),
        keys=(
            _key("manufacturing/enabled", VALUE_BOOL, "true"),
            _key("manufacturing/default_raw_warehouse_id", required=False),
            _key("manufacturing/default_output_warehouse_id", required=False),
            _key("manufacturing/costing_method", VALUE_CHOICE, "AVERAGE", choices=("AVERAGE", "FIFO", "LIFO", "STANDARD", "LAST_PURCHASE")),
            _key("manufacturing/allow_negative_raw_consumption", VALUE_BOOL, "false"),
            _key("manufacturing/operations/allow_print", VALUE_BOOL, "true"),
            _key("manufacturing/operations/allow_order_cancel", VALUE_BOOL, "true"),
        ),
        print_keys=("printing/manufacturing_template", "printing/report_template"),
    ),
    SettingsScopeDescriptor(
        scope="reports",
        section_key="reports",
        title_key="settings.reports",
        service_getter="get_report_settings",
        ui_sections=("reports", "accounting", "printing"),
        operation_key_prefixes=("reports/operations",),
        keys=(
            _key("reports/enabled", VALUE_BOOL, "true"),
            _key("language/report", VALUE_CHOICE, "ar", choices=("ar", "en", "de")),
            _key("reports/default_export_format", VALUE_CHOICE, "pdf", choices=("pdf", "xlsx", "csv", "html")),
            _key("reports/operations/allow_view", VALUE_BOOL, "true"),
            _key("reports/operations/allow_print", VALUE_BOOL, "true"),
            _key("reports/operations/allow_export", VALUE_BOOL, "true"),
        ),
        print_keys=("printing/report_template", "language/report", "language/print"),
    ),
    SettingsScopeDescriptor(
        scope="pos",
        section_key="pos",
        title_key="settings.pos",
        service_getter="get_pos_settings",
        ui_sections=("pos", "inventory", "finance", "printing"),
        operation_key_prefixes=("pos/operations",),
        keys=(
            _key("pos/use_shifts", VALUE_BOOL, "false"),
            _key("pos/ui/density", VALUE_CHOICE, "touch", choices=("compact", "comfortable", "touch")),
            _key("pos/default_warehouse_id", required=False),
            _key("pos/default_cashbox_id", required=False),
            _key("pos/default_payment_method", VALUE_CHOICE, "cash", choices=("cash", "card", "credit", "bank_transfer")),
            _key("pos/receipt_paper", VALUE_CHOICE, "80mm", choices=("80mm", "58mm")),
            _key("pos/operations/allow_checkout", VALUE_BOOL, "true"),
            _key("pos/operations/allow_print_receipt", VALUE_BOOL, "true"),
        ),
        print_keys=("printing/thermal_size", "pos/receipt_paper", "language/print"),
    ),
    SettingsScopeDescriptor(
        scope="restaurant",
        section_key="restaurant",
        title_key="settings.restaurant",
        service_getter="get_restaurant_settings",
        ui_sections=("restaurant", "pos", "printing"),
        operation_key_prefixes=("restaurant/operations",),
        keys=(
            _key("restaurant/enabled", VALUE_BOOL, "true"),
            _key("cafe/enabled", VALUE_BOOL, "true"),
            _key("cafe/auto_open_quick_order", VALUE_BOOL, "true"),
            _key("restaurant/ui/density", VALUE_CHOICE, "touch", choices=("compact", "comfortable", "touch")),
            _key("restaurant/default_payment_method", VALUE_CHOICE, "cash", choices=("cash", "card", "credit", "bank_transfer", "bank")),
            _key("restaurant/receipt_paper", VALUE_CHOICE, "80mm", choices=("80mm", "58mm")),
            _key("restaurant/kitchen_ticket_paper", VALUE_CHOICE, "80mm", choices=("80mm", "58mm")),
            _key("restaurant/session_summary_paper", VALUE_CHOICE, "80mm", choices=("80mm", "58mm")),
            _key("restaurant/operations/allow_checkout", VALUE_BOOL, "true"),
            _key("restaurant/operations/allow_print_receipt", VALUE_BOOL, "true"),
            _key("restaurant/operations/allow_print_kitchen_ticket", VALUE_BOOL, "true"),
        ),
        print_keys=("restaurant/receipt_paper", "restaurant/kitchen_ticket_paper", "restaurant/session_summary_paper", "language/print"),
    ),

    SettingsScopeDescriptor(
        scope="cafe",
        section_key="cafe",
        title_key="settings.cafe",
        service_getter="get_restaurant_settings",
        ui_sections=("cafe", "restaurant", "printing"),
        operation_key_prefixes=("cafe/operations", "restaurant/operations"),
        keys=(
            _key("cafe/enabled", VALUE_BOOL, "true"),
            _key("cafe/auto_open_quick_order", VALUE_BOOL, "true"),
            _key("cafe/quick_order_type", VALUE_CHOICE, "cafe_quick_order", choices=("cafe_quick_order",)),
            _key("cafe/preparation_route", VALUE_CHOICE, "barista", choices=("barista",)),
            _key("cafe/receipt_paper", VALUE_CHOICE, "80mm", choices=("80mm", "58mm")),
            _key("cafe/barista_ticket_paper", VALUE_CHOICE, "80mm", choices=("80mm", "58mm")),
            _key("cafe/printing/receipt_printer", required=False),
            _key("cafe/printing/barista_printer", required=False),
        ),
        print_keys=("cafe/receipt_paper", "cafe/barista_ticket_paper", "language/print"),
        notes="Standalone cafe workspace settings; the business engine remains restaurant-backed.",
    ),
    SettingsScopeDescriptor(
        scope="users",
        section_key="users",
        title_key="settings.users",
        service_getter="get_user_settings",
        ui_sections=("users", "security"),
        operation_key_prefixes=("users/operations",),
        keys=(
            _key("users/enabled", VALUE_BOOL, "true"),
            _key("users/ui/density", VALUE_CHOICE, "comfortable", choices=("compact", "comfortable", "touch")),
            _key("users/operations/allow_create", VALUE_BOOL, "true"),
            _key("users/operations/allow_edit", VALUE_BOOL, "true"),
            _key("users/operations/allow_disable", VALUE_BOOL, "true"),
        ),
        currency_keys=(),
        print_keys=(),
    ),
    SettingsScopeDescriptor(
        scope="settings",
        section_key="settings",
        title_key="settings",
        service_getter="get_language_settings",
        ui_sections=("company", "accounting", "inventory", "transactions", "materials", "parties", "finance", "manufacturing", "reports", "pos", "restaurant", "cafe", "printing", "ui", "security"),
        keys=(
            _key("language", VALUE_CHOICE, "ar", choices=("ar", "en", "de")),
            _key("language/print", VALUE_CHOICE, "ar", choices=("ar", "en", "de")),
            _key("language/report", VALUE_CHOICE, "ar", choices=("ar", "en", "de")),
            _key("base_currency", default="SYP"),
            _key("display_currency", default="SYP"),
            _key("printing/print_button_mode", VALUE_CHOICE, "browser", choices=("browser",)),
        ),
        operation_key_prefixes=(),
    ),
)

_BY_SCOPE = {d.scope: d for d in SETTINGS_SCOPE_DESCRIPTORS}


def normalize_settings_scope(settings_scope: str) -> str:
    scope = str(settings_scope or "").strip().replace("/", ".")
    if scope.endswith(".list"):
        scope = scope[:-5]
    return scope


def settings_scope_descriptors() -> tuple[SettingsScopeDescriptor, ...]:
    return SETTINGS_SCOPE_DESCRIPTORS


def settings_descriptor_for(scope: str, default: SettingsScopeDescriptor | None = None) -> SettingsScopeDescriptor | None:
    normalized = normalize_settings_scope(scope)
    if normalized in _BY_SCOPE:
        return _BY_SCOPE[normalized]
    best: SettingsScopeDescriptor | None = None
    for descriptor in SETTINGS_SCOPE_DESCRIPTORS:
        if descriptor.covers(normalized):
            if best is None or len(descriptor.scope) > len(best.scope):
                best = descriptor
    return best or default


def all_settings_keys() -> tuple[SettingsKeyDescriptor, ...]:
    seen: set[str] = set()
    keys: list[SettingsKeyDescriptor] = []
    for descriptor in SETTINGS_SCOPE_DESCRIPTORS:
        for key in descriptor.keys:
            if key.key not in seen:
                seen.add(key.key)
                keys.append(key)
    return tuple(keys)


def validate_settings_scope_descriptor(descriptor: SettingsScopeDescriptor) -> list[str]:
    warnings: list[str] = []
    required = ("scope", "section_key", "title_key", "service_getter", "api_resource")
    for attr in required:
        if not str(getattr(descriptor, attr, "") or "").strip():
            warnings.append(f"{descriptor.scope}: missing {attr}")
    if not descriptor.ui_sections:
        warnings.append(f"{descriptor.scope}: missing ui_sections")
    if not descriptor.keys:
        warnings.append(f"{descriptor.scope}: missing settings keys")
    for key in descriptor.keys:
        if not key.key:
            warnings.append(f"{descriptor.scope}: empty setting key")
        if key.value_type == VALUE_CHOICE and not key.choices:
            warnings.append(f"{descriptor.scope}:{key.key}: choice without choices")
        if key.network_synced and not descriptor.api_resource.startswith("/api/settings"):
            warnings.append(f"{descriptor.scope}:{key.key}: network key without settings API")
    return warnings


def validate_settings_scope_descriptors(descriptors: Iterable[SettingsScopeDescriptor] | None = None) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for descriptor in descriptors or SETTINGS_SCOPE_DESCRIPTORS:
        warnings = validate_settings_scope_descriptor(descriptor)
        if warnings:
            result[descriptor.scope] = warnings
    return result


def collect_shell_settings_scopes() -> tuple[str, ...]:
    """Collect settings_scope values from all shell/list/report/operational contracts."""
    scopes: set[str] = set()
    try:
        from workspace.documents.document_contract import all_descriptors
        scopes.update(d.settings_scope for d in all_descriptors())
    except Exception:
        pass
    try:
        from workspace.lists.list_workspace_contract import list_descriptors
        scopes.update(d.settings_scope for d in list_descriptors())
    except Exception:
        pass
    try:
        from features.reports.report_shell_contract import all_report_descriptors
        scopes.update(d.settings_scope for d in all_report_descriptors())
    except Exception:
        pass
    try:
        from workspace.operational.operational_shell_contract import operational_descriptors
        scopes.update(d.settings_scope for d in operational_descriptors())
    except Exception:
        pass
    return tuple(sorted(s for s in scopes if s))


def uncovered_settings_scopes(scopes: Iterable[str] | None = None) -> tuple[str, ...]:
    missing: list[str] = []
    for scope in scopes or collect_shell_settings_scopes():
        if settings_descriptor_for(scope) is None:
            missing.append(scope)
    return tuple(sorted(set(missing)))


def settings_coverage_matrix(scopes: Iterable[str] | None = None) -> tuple[Mapping[str, str], ...]:
    rows: list[Mapping[str, str]] = []
    for scope in scopes or collect_shell_settings_scopes():
        descriptor = settings_descriptor_for(scope)
        rows.append({
            "settings_scope": scope,
            "normalized_scope": normalize_settings_scope(scope),
            "covered_by": descriptor.scope if descriptor else "",
            "section_key": descriptor.section_key if descriptor else "",
            "service_getter": descriptor.service_getter if descriptor else "",
            "ui_sections": "|".join(descriptor.ui_sections) if descriptor else "",
            "api_resource": descriptor.api_resource if descriptor else "",
            "network_mode": descriptor.network_mode if descriptor else "",
            "required_keys": "|".join(descriptor.required_keys) if descriptor else "",
            "operation_key_prefixes": "|".join(descriptor.operation_key_prefixes) if descriptor else "",
        })
    return tuple(rows)


__all__ = [
    "SettingsKeyDescriptor",
    "SettingsScopeDescriptor",
    "settings_scope_descriptors",
    "settings_descriptor_for",
    "all_settings_keys",
    "validate_settings_scope_descriptors",
    "collect_shell_settings_scopes",
    "uncovered_settings_scopes",
    "settings_coverage_matrix",
    "normalize_settings_scope",
]
