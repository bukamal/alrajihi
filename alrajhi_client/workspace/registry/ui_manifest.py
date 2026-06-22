# -*- coding: utf-8 -*-
"""Unified workspace manifest for the ERP shell.

Phase 331 foundation: this module is intentionally free of PyQt imports.  It is
safe for release guards and tests, and MainWindow consumes it to avoid losing
pages, action-bar rules, table contracts, or barcode-printing endpoints while
future UI unification work proceeds.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence


@dataclass(frozen=True)
class WorkspaceActionSpec:
    """One shell action exposed by a workspace or the global command strip."""

    key: str
    label_key: str
    icon: str
    shortcut: str = ""
    placement: str = "action_bar"
    permission: str = ""
    settings_key: str = ""


@dataclass(frozen=True)
class WorkspaceMenuEntrySpec:
    """One menu entry resolved by MainWindow through a page or callback key."""

    key: str
    label_key: str
    icon: str
    page_id: str = ""
    callback_key: str = ""
    shortcut: str = ""
    separator_before: bool = False
    admin_only: bool = False


@dataclass(frozen=True)
class WorkspaceMenuSpec:
    """Top-level business navigation menu declared outside MainWindow."""

    key: str
    label_key: str
    icon: str
    entries: tuple[WorkspaceMenuEntrySpec, ...]
    admin_only: bool = False


@dataclass(frozen=True)
class WorkspaceTableSpec:
    """Registry identity for a screen table before Phase 334 column rollout."""

    table_id: str
    table_type: str
    settings_prefix: str
    editable: bool = False
    printable: bool = True
    exportable: bool = True


@dataclass(frozen=True)
class WorkspaceBarcodeProfileSpec:
    """Barcode/QR print endpoint that will be bound to settings and HTML print.

    The profile id is the stable settings key root.  All profiles support
    multi-print by contract so restaurant, cafe and apparel can reach parity
    with the existing material barcode label workflow.
    """

    profile_id: str
    module: str
    title_key: str
    item_scope: str
    settings_prefix: str
    default_template_id: str
    printable_fields: tuple[str, ...]
    supports_multi_print: bool = True
    browser_html_only: bool = True


@dataclass(frozen=True)
class WorkspaceManifest:
    """One canonical definition for every primary ERP workspace page."""

    page_id: str
    title_key: str
    group_key: str
    nav_group: str
    icon: str
    factory_name: str
    workspace_type: str
    show_action_bar: bool = True
    module_checks: tuple[tuple[str, bool], ...] = field(default_factory=tuple)
    permission: str = ""
    settings_section: str = ""
    action_keys: tuple[str, ...] = field(default_factory=tuple)
    table_specs: tuple[WorkspaceTableSpec, ...] = field(default_factory=tuple)
    barcode_profiles: tuple[str, ...] = field(default_factory=tuple)


ACTION_SPECS: Mapping[str, WorkspaceActionSpec] = {
    "new": WorkspaceActionSpec("new", "new", "plus", "Ctrl+N"),
    "save": WorkspaceActionSpec("save", "save", "save", "Ctrl+S"),
    "refresh": WorkspaceActionSpec("refresh", "refresh_now", "sync-alt", "F5"),
    "print": WorkspaceActionSpec("print", "print", "print", "Ctrl+P"),
    "export": WorkspaceActionSpec("export", "export", "file-export"),
    "quick_open": WorkspaceActionSpec("quick_open", "workspace.quick_open", "search", "Ctrl+K"),
    "alert": WorkspaceActionSpec("alert", "alerts", "bell", placement="utility"),
    "theme": WorkspaceActionSpec("theme", "toggle_theme", "adjust", placement="utility"),
    "screenshot": WorkspaceActionSpec("screenshot", "export_screenshot", "camera", placement="utility"),
    "user": WorkspaceActionSpec("user", "user", "user", placement="utility"),
}

UTILITY_ACTION_KEYS: tuple[str, ...] = ("alert", "theme", "screenshot", "user")
COMMON_LIST_ACTIONS: tuple[str, ...] = ("new", "refresh", "print", "export", "quick_open")
DOCUMENT_ACTIONS: tuple[str, ...] = ("new", "save", "refresh", "print", "export", "quick_open")
OPERATION_ACTIONS: tuple[str, ...] = ("refresh", "print", "export", "quick_open")
# Dashboard must show only the allowed utility surface requested by UX: user,
# theme, refresh and screenshot.  Alerts and generic document buttons stay out.
DASHBOARD_ACTIONS: tuple[str, ...] = ("refresh", "theme", "screenshot", "user")


BARCODE_PRINT_PROFILES: Mapping[str, WorkspaceBarcodeProfileSpec] = {
    "items.default": WorkspaceBarcodeProfileSpec(
        profile_id="items.default",
        module="items",
        title_key="barcode_labels",
        item_scope="material",
        settings_prefix="printing/barcode/items/default",
        default_template_id="material_label_default",
        printable_fields=("company", "item_name", "barcode", "barcode_text", "price", "currency"),
    ),
    "apparel.variant_labels": WorkspaceBarcodeProfileSpec(
        profile_id="apparel.variant_labels",
        module="apparel",
        title_key="apparel.barcode_variant_labels",
        item_scope="apparel_variant",
        settings_prefix="printing/barcode/apparel/variant_labels",
        default_template_id="apparel_variant_label_default",
        printable_fields=(
            "company",
            "item_name",
            "variant_color",
            "variant_size",
            "variant_code",
            "barcode",
            "barcode_text",
            "price",
            "currency",
        ),
    ),
    "restaurant.menu_items": WorkspaceBarcodeProfileSpec(
        profile_id="restaurant.menu_items",
        module="restaurant",
        title_key="restaurant.barcode_menu_items",
        item_scope="restaurant_menu_item",
        settings_prefix="printing/barcode/restaurant/menu_items",
        default_template_id="restaurant_menu_label_default",
        printable_fields=("company", "menu_item", "section", "barcode", "barcode_text", "price", "currency"),
    ),
    "restaurant.table_labels": WorkspaceBarcodeProfileSpec(
        profile_id="restaurant.table_labels",
        module="restaurant",
        title_key="restaurant.barcode_table_labels",
        item_scope="restaurant_table",
        settings_prefix="printing/barcode/restaurant/table_labels",
        default_template_id="restaurant_table_qr_default",
        printable_fields=("company", "table_number", "zone", "qr", "barcode_text"),
    ),
    "cafe.products": WorkspaceBarcodeProfileSpec(
        profile_id="cafe.products",
        module="cafe",
        title_key="cafe.barcode_products",
        item_scope="cafe_product",
        settings_prefix="printing/barcode/cafe/products",
        default_template_id="cafe_product_label_default",
        printable_fields=("company", "product_name", "size", "barcode", "barcode_text", "price", "currency"),
    ),
    "cafe.modifier_labels": WorkspaceBarcodeProfileSpec(
        profile_id="cafe.modifier_labels",
        module="cafe",
        title_key="cafe.barcode_modifier_labels",
        item_scope="cafe_modifier",
        settings_prefix="printing/barcode/cafe/modifier_labels",
        default_template_id="cafe_modifier_label_default",
        printable_fields=("company", "modifier_name", "group", "barcode", "barcode_text", "price", "currency"),
    ),
}


def _table(page_id: str, table_id: str, table_type: str, *, editable: bool = False, printable: bool = True, exportable: bool = True) -> WorkspaceTableSpec:
    return WorkspaceTableSpec(
        table_id=table_id,
        table_type=table_type,
        settings_prefix=f"ui/columns/{page_id}/{table_id}",
        editable=editable,
        printable=printable,
        exportable=exportable,
    )


PAGE_MANIFESTS: Mapping[str, WorkspaceManifest] = {
    "dashboard": WorkspaceManifest(
        page_id="dashboard",
        title_key="dashboard",
        group_key="home_breadcrumb",
        nav_group="الرئيسية",
        icon="tachometer-alt",
        factory_name="DashboardWidget",
        workspace_type="dashboard",
        show_action_bar=True,
        action_keys=DASHBOARD_ACTIONS,
    ),
    "pos": WorkspaceManifest(
        page_id="pos",
        title_key="pos",
        group_key="nav_sales",
        nav_group="المبيعات",
        icon="barcode",
        factory_name="POSWidget",
        workspace_type="operational",
        module_checks=(("pos/enabled", True),),
        action_keys=OPERATION_ACTIONS,
        table_specs=(_table("pos", "lines", "editable_line", editable=True),),
        barcode_profiles=("items.default",),
    ),
    "sales_invoices": WorkspaceManifest(
        page_id="sales_invoices",
        title_key="sales_invoices",
        group_key="nav_sales",
        nav_group="المبيعات",
        icon="file-invoice-dollar",
        factory_name="SalesInvoicesWidget",
        workspace_type="document",
        module_checks=(("transactions/enabled", True),),
        action_keys=DOCUMENT_ACTIONS,
        table_specs=(_table("sales_invoices", "lines", "editable_line", editable=True),),
    ),
    "purchase_invoices": WorkspaceManifest(
        page_id="purchase_invoices",
        title_key="purchase_invoices",
        group_key="nav_purchases",
        nav_group="المشتريات",
        icon="file-invoice",
        factory_name="PurchaseInvoicesWidget",
        workspace_type="document",
        module_checks=(("transactions/enabled", True),),
        action_keys=DOCUMENT_ACTIONS,
        table_specs=(_table("purchase_invoices", "lines", "editable_line", editable=True),),
    ),
    "items": WorkspaceManifest(
        page_id="items",
        title_key="items_inventory",
        group_key="nav_inventory",
        nav_group="المخزون",
        icon="box",
        factory_name="ItemsWidget",
        workspace_type="list",
        module_checks=(("inventory/enabled", True),),
        action_keys=COMMON_LIST_ACTIONS,
        table_specs=(_table("items", "materials", "read_only_list"),),
        barcode_profiles=("items.default",),
    ),
    "categories": WorkspaceManifest(
        page_id="categories",
        title_key="categories",
        group_key="nav_inventory",
        nav_group="المخزون",
        icon="folder",
        factory_name="CategoriesWidget",
        workspace_type="list",
        module_checks=(("categories/enabled", True),),
        action_keys=COMMON_LIST_ACTIONS,
        table_specs=(_table("categories", "categories", "read_only_list"),),
    ),
    "warehouses": WorkspaceManifest(
        page_id="warehouses",
        title_key="warehouses",
        group_key="nav_inventory",
        nav_group="المخزون",
        icon="warehouse",
        factory_name="WarehousesWidget",
        workspace_type="list",
        module_checks=(("inventory/enabled", True),),
        action_keys=COMMON_LIST_ACTIONS,
        table_specs=(_table("warehouses", "warehouses", "read_only_list"),),
    ),
    "branches": WorkspaceManifest(
        page_id="branches",
        title_key="branches",
        group_key="nav_admin",
        nav_group="الإدارة",
        icon="code-branch",
        factory_name="BranchesWidget",
        workspace_type="list",
        module_checks=(("branches/enabled", True),),
        action_keys=COMMON_LIST_ACTIONS,
        table_specs=(_table("branches", "branches", "read_only_list"),),
    ),
    "cashboxes": WorkspaceManifest(
        page_id="cashboxes",
        title_key="cashboxes",
        group_key="nav_finance",
        nav_group="المبيعات",
        icon="cash-register",
        factory_name="CashboxesWidget",
        workspace_type="list",
        module_checks=(("finance/enabled", True),),
        action_keys=COMMON_LIST_ACTIONS,
        table_specs=(_table("cashboxes", "cashboxes", "read_only_list"),),
    ),
    "customers": WorkspaceManifest(
        page_id="customers",
        title_key="customers",
        group_key="nav_parties",
        nav_group="المبيعات",
        icon="user-friends",
        factory_name="CustomersWidget",
        workspace_type="list",
        module_checks=(("parties/enabled", True),),
        action_keys=COMMON_LIST_ACTIONS,
        table_specs=(_table("customers", "customers", "read_only_list"),),
    ),
    "suppliers": WorkspaceManifest(
        page_id="suppliers",
        title_key="suppliers",
        group_key="nav_parties",
        nav_group="المشتريات",
        icon="truck-loading",
        factory_name="SuppliersWidget",
        workspace_type="list",
        module_checks=(("parties/enabled", True),),
        action_keys=COMMON_LIST_ACTIONS,
        table_specs=(_table("suppliers", "suppliers", "read_only_list"),),
    ),
    "vouchers": WorkspaceManifest(
        page_id="vouchers",
        title_key="vouchers",
        group_key="nav_finance",
        nav_group="المبيعات",
        icon="receipt",
        factory_name="VouchersWidget",
        workspace_type="document",
        module_checks=(("finance/enabled", True),),
        action_keys=DOCUMENT_ACTIONS,
        table_specs=(_table("vouchers", "voucher_lines", "editable_line", editable=True),),
    ),
    "returns": WorkspaceManifest(
        page_id="returns",
        title_key="sales_returns",
        group_key="nav_sales",
        nav_group="المبيعات",
        icon="undo",
        factory_name="ReturnsWidget",
        workspace_type="document",
        module_checks=(("transactions/enabled", True),),
        action_keys=DOCUMENT_ACTIONS,
        table_specs=(_table("returns", "lines", "editable_line", editable=True),),
    ),
    "purchase_returns": WorkspaceManifest(
        page_id="purchase_returns",
        title_key="purchase_returns",
        group_key="nav_purchases",
        nav_group="المشتريات",
        icon="undo-alt",
        factory_name="PurchaseReturnsWidget",
        workspace_type="document",
        module_checks=(("transactions/enabled", True),),
        action_keys=DOCUMENT_ACTIONS,
        table_specs=(_table("purchase_returns", "lines", "editable_line", editable=True),),
    ),
    "manufacturing": WorkspaceManifest(
        page_id="manufacturing",
        title_key="nav_manufacturing",
        group_key="nav_manufacturing",
        nav_group="التصنيع",
        icon="industry",
        factory_name="ManufacturingWidget",
        workspace_type="document",
        module_checks=(("manufacturing/enabled", True),),
        action_keys=DOCUMENT_ACTIONS,
        table_specs=(_table("manufacturing", "orders", "editable_line", editable=True),),
    ),
    "reports": WorkspaceManifest(
        page_id="reports",
        title_key="reports",
        group_key="reports",
        nav_group="التقارير",
        icon="chart-line",
        factory_name="ReportsWidget",
        workspace_type="report",
        module_checks=(("reports/enabled", True),),
        action_keys=("refresh", "print", "export", "quick_open"),
        table_specs=(_table("reports", "result", "report", editable=False),),
    ),
    "settings": WorkspaceManifest(
        page_id="settings",
        title_key="settings",
        group_key="nav_admin",
        nav_group="الإدارة",
        icon="sliders-h",
        factory_name="SettingsWidget",
        workspace_type="settings",
        action_keys=("save", "refresh", "quick_open"),
    ),
    "users": WorkspaceManifest(
        page_id="users",
        title_key="users",
        group_key="nav_users",
        nav_group="المستخدمين",
        icon="users-cog",
        factory_name="UsersWidget",
        workspace_type="list",
        module_checks=(("users/enabled", True),),
        action_keys=COMMON_LIST_ACTIONS,
        table_specs=(_table("users", "users", "read_only_list"),),
    ),
    "audit_log": WorkspaceManifest(
        page_id="audit_log",
        title_key="audit_log",
        group_key="nav_users",
        nav_group="المستخدمين",
        icon="history",
        factory_name="AuditLogWidget",
        workspace_type="report",
        module_checks=(("users/enabled", True),),
        action_keys=("refresh", "export", "quick_open"),
        table_specs=(_table("audit_log", "events", "report"),),
    ),
    "offline_queue": WorkspaceManifest(
        page_id="offline_queue",
        title_key="offline_queue",
        group_key="nav_admin",
        nav_group="الإدارة",
        icon="cloud-upload-alt",
        factory_name="OfflineQueueWidget",
        workspace_type="operational",
        action_keys=("refresh", "export", "quick_open"),
        table_specs=(_table("offline_queue", "queue", "operational"),),
    ),
    "monitoring": WorkspaceManifest(
        page_id="monitoring",
        title_key="monitoring",
        group_key="nav_admin",
        nav_group="الإدارة",
        icon="heartbeat",
        factory_name="MonitoringWidget",
        workspace_type="operational",
        action_keys=("refresh", "export", "quick_open"),
        table_specs=(_table("monitoring", "health", "operational"),),
    ),
    "restaurant": WorkspaceManifest(
        page_id="restaurant",
        title_key="restaurant.dashboard",
        group_key="nav_restaurant",
        nav_group="المطعم",
        icon="utensils",
        factory_name="RestaurantDashboard",
        workspace_type="operational",
        module_checks=(("restaurant/enabled", True),),
        action_keys=OPERATION_ACTIONS,
        table_specs=(
            _table("restaurant", "order_lines", "operational", editable=True),
            _table("restaurant", "kitchen_queue", "operational"),
            _table("restaurant", "tables", "operational"),
        ),
        barcode_profiles=("restaurant.menu_items", "restaurant.table_labels"),
    ),
    "cafe": WorkspaceManifest(
        page_id="cafe",
        title_key="restaurant.cafe_workspace_title",
        group_key="nav_cafe",
        nav_group="الكافي",
        icon="coffee",
        factory_name="CafeWorkspaceWidget",
        workspace_type="operational",
        module_checks=(("cafe/enabled", True),),
        action_keys=OPERATION_ACTIONS,
        table_specs=(
            _table("cafe", "order_lines", "operational", editable=True),
            _table("cafe", "preparation_queue", "operational"),
            _table("cafe", "shift_report", "report"),
        ),
        barcode_profiles=("cafe.products", "cafe.modifier_labels"),
    ),
    "apparel": WorkspaceManifest(
        page_id="apparel",
        title_key="apparel.workspace_title",
        group_key="nav_apparel",
        nav_group="الألبسة",
        icon="tshirt",
        factory_name="ApparelWorkspaceWidget",
        workspace_type="matrix",
        module_checks=(("apparel/enabled", True),),
        action_keys=("new", "refresh", "print", "export", "quick_open"),
        table_specs=(
            _table("apparel", "variants", "read_only_list"),
            _table("apparel", "matrix", "matrix", editable=True),
            _table("apparel", "reports", "report"),
        ),
        barcode_profiles=("apparel.variant_labels",),
    ),
}


def _entry(
    key: str,
    label_key: str,
    icon: str,
    *,
    page_id: str = "",
    callback_key: str = "",
    shortcut: str = "",
    separator_before: bool = False,
    admin_only: bool = False,
) -> WorkspaceMenuEntrySpec:
    return WorkspaceMenuEntrySpec(
        key=key,
        label_key=label_key,
        icon=icon,
        page_id=page_id,
        callback_key=callback_key,
        shortcut=shortcut,
        separator_before=separator_before,
        admin_only=admin_only,
    )


MAIN_NAVIGATION_MENUS: tuple[WorkspaceMenuSpec, ...] = (
    WorkspaceMenuSpec(
        "home",
        "home_breadcrumb",
        "home",
        (
            _entry("dashboard", "dashboard", "tachometer-alt", page_id="dashboard", shortcut="F1"),
            _entry("pos", "pos", "barcode", page_id="pos", shortcut="F2"),
            _entry("restaurant", "restaurant.dashboard", "utensils", page_id="restaurant", shortcut="F8"),
            _entry("cafe", "restaurant.cafe_workspace_title", "coffee", page_id="cafe", shortcut="F10"),
            _entry("apparel", "apparel.workspace_title", "tshirt", page_id="apparel", shortcut="F11"),
            _entry("monitoring", "monitoring", "heartbeat", page_id="monitoring", separator_before=True),
        ),
    ),
    WorkspaceMenuSpec(
        "sales",
        "nav_sales",
        "shopping-cart",
        (
            _entry("pos", "pos", "barcode", page_id="pos", shortcut="F2"),
            _entry("sales_invoices", "sales_invoices", "file-invoice-dollar", page_id="sales_invoices", shortcut="F3"),
            _entry("returns", "sales_returns", "undo", page_id="returns"),
            _entry("vouchers_receipt", "receipt_voucher", "hand-holding-usd", page_id="vouchers", separator_before=True),
        ),
    ),
    WorkspaceMenuSpec(
        "restaurant",
        "nav_restaurant",
        "utensils",
        (
            _entry("restaurant", "restaurant.dashboard", "utensils", page_id="restaurant", shortcut="F8"),
            _entry("restaurant_open_table", "restaurant.open_table", "door-open", page_id="restaurant"),
            _entry("restaurant_kitchen", "restaurant.kitchen_ticket", "receipt", page_id="restaurant"),
        ),
    ),
    WorkspaceMenuSpec(
        "cafe",
        "nav_cafe",
        "coffee",
        (
            _entry("cafe", "restaurant.cafe_workspace_title", "coffee", page_id="cafe", shortcut="F10"),
            _entry("cafe_quick_order", "restaurant.cafe_new_quick_order", "plus-circle", page_id="cafe"),
            _entry("cafe_preparation", "restaurant.cafe_preparation", "mug-hot", page_id="cafe"),
            _entry("cafe_shift_report", "restaurant.cafe_shift_report", "chart-line", page_id="cafe"),
        ),
    ),
    WorkspaceMenuSpec(
        "purchases",
        "nav_purchases",
        "truck",
        (
            _entry("purchase_invoices", "purchase_invoices", "file-invoice", page_id="purchase_invoices"),
            _entry("purchase_returns", "purchase_returns", "undo-alt", page_id="purchase_returns"),
            _entry("vouchers_payment", "payment_voucher", "money-bill-wave", page_id="vouchers", separator_before=True),
        ),
    ),
    WorkspaceMenuSpec(
        "inventory",
        "nav_inventory",
        "boxes",
        (
            _entry("items", "items", "box", page_id="items", shortcut="F4"),
            _entry("apparel", "apparel.workspace_title", "tshirt", page_id="apparel", shortcut="F11"),
            _entry("new_item", "new_item", "box-open", callback_key="open_quick_item", separator_before=True),
            _entry("categories", "categories", "folder", page_id="categories"),
            _entry("add_category", "add_category", "folder-plus", callback_key="open_category_document"),
            _entry("warehouses", "warehouses", "warehouse", page_id="warehouses"),
            _entry("inventory_transfer", "inventory_transfer", "exchange-alt", callback_key="open_inventory_transfer_document"),
        ),
    ),
    WorkspaceMenuSpec(
        "parties",
        "nav_parties",
        "address-book",
        (
            _entry("customers", "customers", "user-friends", page_id="customers"),
            _entry("new_customer", "new_customer", "user-plus", callback_key="open_quick_customer"),
            _entry("suppliers", "suppliers", "truck-loading", page_id="suppliers", separator_before=True),
            _entry("new_supplier", "new_supplier", "truck-loading", callback_key="open_quick_supplier"),
        ),
    ),
    WorkspaceMenuSpec(
        "finance",
        "nav_finance",
        "coins",
        (
            _entry("vouchers", "vouchers", "receipt", page_id="vouchers"),
            _entry("cashboxes", "cashboxes", "cash-register", page_id="cashboxes"),
        ),
    ),
    WorkspaceMenuSpec(
        "manufacturing",
        "nav_manufacturing",
        "industry",
        (
            _entry("manufacturing", "nav_manufacturing", "industry", page_id="manufacturing"),
            _entry("new_bom", "bom_recipe", "cogs", callback_key="open_bom_document"),
            _entry("new_production_order", "new_production_order", "clipboard-list", callback_key="open_production_order_document"),
        ),
    ),
    WorkspaceMenuSpec(
        "reports",
        "reports",
        "chart-line",
        (_entry("reports", "reports", "chart-line", page_id="reports"),),
    ),
    WorkspaceMenuSpec(
        "admin",
        "nav_admin",
        "sliders-h",
        (
            _entry("settings", "settings", "sliders-h", page_id="settings"),
            _entry("offline_queue", "offline_queue", "cloud-upload-alt", page_id="offline_queue"),
            _entry("monitoring", "monitoring", "heartbeat", page_id="monitoring"),
            _entry("about", "about_app", "info-circle", callback_key="show_about", shortcut="F12", separator_before=True),
            _entry("logout", "logout", "sign-out-alt", callback_key="logout", shortcut="Ctrl+Q"),
            _entry("exit", "exit", "times-circle", callback_key="close_app", shortcut="Alt+F4"),
        ),
    ),
    WorkspaceMenuSpec(
        "users",
        "nav_users",
        "user-shield",
        (
            _entry("users", "users", "users-cog", page_id="users"),
            _entry("audit_log", "audit_log", "history", page_id="audit_log"),
        ),
        admin_only=True,
    ),
    WorkspaceMenuSpec(
        "quick",
        "quick_actions",
        "bolt",
        (
            _entry("quick_open", "workspace.quick_open", "search", callback_key="open_quick_open", shortcut="Ctrl+K"),
            _entry("new_sales_invoice", "new_sales_invoice", "file-invoice-dollar", callback_key="open_new_sales_invoice", shortcut="Ctrl+N", separator_before=True),
            _entry("new_purchase_invoice", "new_purchase_invoice", "file-invoice", callback_key="open_new_purchase_invoice"),
            _entry("receipt_voucher", "receipt_voucher", "hand-holding-usd", callback_key="open_receipt_voucher"),
            _entry("payment_voucher", "payment_voucher", "money-bill-wave", callback_key="open_payment_voucher"),
            _entry("new_customer", "new_customer", "user-plus", callback_key="open_quick_customer", separator_before=True),
            _entry("new_supplier", "new_supplier", "truck-loading", callback_key="open_quick_supplier"),
            _entry("new_item", "new_item", "box-open", callback_key="open_quick_item"),
        ),
    ),
)


def page_manifest(page_id: str) -> WorkspaceManifest:
    return PAGE_MANIFESTS[page_id]


def page_factory_ids() -> tuple[str, ...]:
    return tuple(PAGE_MANIFESTS.keys())


def page_meta_keys() -> dict[str, tuple[str, str]]:
    return {pid: (manifest.title_key, manifest.group_key) for pid, manifest in PAGE_MANIFESTS.items()}


def page_navigation_groups() -> dict[str, str]:
    return {pid: manifest.nav_group for pid, manifest in PAGE_MANIFESTS.items()}


def should_show_action_bar(page_id: str) -> bool:
    manifest = PAGE_MANIFESTS.get(page_id)
    return bool(manifest.show_action_bar) if manifest else True


def action_spec(action_key: str) -> WorkspaceActionSpec:
    return ACTION_SPECS[action_key]


def action_keys_for_page(page_id: str) -> tuple[str, ...]:
    manifest = PAGE_MANIFESTS.get(page_id)
    return tuple(manifest.action_keys) if manifest else tuple()


def effective_action_keys_for_page(page_id: str) -> tuple[str, ...]:
    """Visible shell actions after utility buttons are applied by contract."""
    keys = tuple(action_keys_for_page(page_id))
    if page_id == "dashboard":
        return DASHBOARD_ACTIONS
    merged: list[str] = []
    for key in (*keys, *UTILITY_ACTION_KEYS):
        if key in ACTION_SPECS and key not in merged:
            merged.append(key)
    return tuple(merged)


def action_specs_for_page(page_id: str) -> tuple[WorkspaceActionSpec, ...]:
    return tuple(ACTION_SPECS[key] for key in effective_action_keys_for_page(page_id) if key in ACTION_SPECS)


def table_ids_for_page(page_id: str) -> tuple[str, ...]:
    manifest = PAGE_MANIFESTS.get(page_id)
    if not manifest:
        return tuple()
    return tuple(table.table_id for table in manifest.table_specs)


def barcode_profile_spec(profile_id: str) -> WorkspaceBarcodeProfileSpec:
    return BARCODE_PRINT_PROFILES[profile_id]


def barcode_profile_ids(module: str | None = None) -> tuple[str, ...]:
    if module is None:
        return tuple(BARCODE_PRINT_PROFILES.keys())
    return tuple(profile_id for profile_id, profile in BARCODE_PRINT_PROFILES.items() if profile.module == module)


def barcode_profile_settings_prefixes() -> dict[str, str]:
    return {profile_id: profile.settings_prefix for profile_id, profile in BARCODE_PRINT_PROFILES.items()}


def navigation_menus() -> tuple[WorkspaceMenuSpec, ...]:
    return MAIN_NAVIGATION_MENUS


__all__ = [
    "WorkspaceActionSpec",
    "WorkspaceBarcodeProfileSpec",
    "WorkspaceManifest",
    "WorkspaceMenuEntrySpec",
    "WorkspaceMenuSpec",
    "WorkspaceTableSpec",
    "ACTION_SPECS",
    "UTILITY_ACTION_KEYS",
    "PAGE_MANIFESTS",
    "BARCODE_PRINT_PROFILES",
    "MAIN_NAVIGATION_MENUS",
    "page_manifest",
    "page_factory_ids",
    "page_meta_keys",
    "page_navigation_groups",
    "should_show_action_bar",
    "action_spec",
    "action_keys_for_page",
    "effective_action_keys_for_page",
    "action_specs_for_page",
    "table_ids_for_page",
    "barcode_profile_spec",
    "barcode_profile_ids",
    "barcode_profile_settings_prefixes",
    "navigation_menus",
]
