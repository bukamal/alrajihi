# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping


SHELL_DOCUMENT = "document"
SHELL_TRANSACTION = "transaction_document"
SHELL_REPORT = "report_shell"
SHELL_OPERATIONAL = "operational_shell"
SHELL_LIST = "list_workspace"

CURRENCY_NONE = "none"
CURRENCY_DISPLAY = "display_currency"
CURRENCY_DOCUMENT = "document_currency"
CURRENCY_MONEY = "money_display_policy"

BRANCH_NONE = "none"
BRANCH_OPTIONAL = "optional"
BRANCH_REQUIRED = "required"
BRANCH_USER_ACCESS = "user_branch_access"

NETWORK_LOCAL_ONLY = "local_only"
NETWORK_REMOTE_REQUIRED = "remote_required"
NETWORK_REMOTE_AVAILABLE = "remote_available"
NETWORK_MIXED = "mixed"


@dataclass(frozen=True)
class DocumentCapabilities:
    """Actions and operating modes that a workspace surface must declare.

    This is deliberately data-only so the contract can be inspected in CI and in
    PyInstaller builds without importing PyQt widgets.
    """

    save: bool = True
    print: bool = False
    export: bool = False
    delete: bool = False
    approve: bool = False
    cancel: bool = False
    barcode: bool = False
    grid_layout: bool = False
    workflow: bool = False
    audit: bool = True
    offline_queue: bool = False


@dataclass(frozen=True)
class DocumentPermissions:
    """Permission keys expected by the UI and service/API layers.

    Empty strings are allowed only when the action is not supported.  The
    validation helper checks the supported actions and warns if a permission key
    is missing.
    """

    view: str
    create: str = ""
    update: str = ""
    delete: str = ""
    print: str = ""
    export: str = ""
    approve: str = ""
    cancel: str = ""

    def action_map(self) -> Mapping[str, str]:
        return {
            "view": self.view,
            "create": self.create,
            "update": self.update,
            "delete": self.delete,
            "print": self.print,
            "export": self.export,
            "approve": self.approve,
            "cancel": self.cancel,
        }


@dataclass(frozen=True)
class DocumentDescriptor:
    """Canonical contract for any document-like or operational workspace.

    The goal is not to make all screens visually identical.  The goal is that
    every screen declares its language scope, settings scope, permission surface,
    API/network status, currency/branch policy, print/export capability, and
    audit scope in one inspectable place.
    """

    document_type: str
    shell_family: str
    title_key: str
    i18n_scope: str
    settings_scope: str
    gateway: str
    api_resource: str
    network_mode: str
    permissions: DocumentPermissions
    capabilities: DocumentCapabilities = field(default_factory=DocumentCapabilities)
    currency_policy: str = CURRENCY_NONE
    branch_policy: str = BRANCH_NONE
    audit_scope: str = ""
    workspace_route: str = ""
    list_route: str = ""
    document_class: str = ""
    local_gateway: str = ""
    remote_gateway: str = ""
    server_blueprint: str = ""
    legacy_adapter: bool = False
    notes: str = ""

    def permission_for(self, action: str) -> str:
        return self.permissions.action_map().get(action, "")

    @property
    def is_network_ready(self) -> bool:
        return self.network_mode in {NETWORK_REMOTE_AVAILABLE, NETWORK_REMOTE_REQUIRED}


class DocumentContractError(ValueError):
    pass


_REQUIRED_FIELDS = (
    "document_type",
    "shell_family",
    "title_key",
    "i18n_scope",
    "settings_scope",
    "gateway",
    "api_resource",
    "network_mode",
    "audit_scope",
)


def validate_descriptor(descriptor: DocumentDescriptor) -> list[str]:
    """Return contract warnings; raise nothing to keep CI diagnostics readable."""

    warnings: list[str] = []
    for field_name in _REQUIRED_FIELDS:
        if not str(getattr(descriptor, field_name, "") or "").strip():
            warnings.append(f"{descriptor.document_type}: missing {field_name}")

    if not descriptor.permissions.view:
        warnings.append(f"{descriptor.document_type}: missing view permission")
    if descriptor.capabilities.save and not (descriptor.permissions.create or descriptor.permissions.update):
        warnings.append(f"{descriptor.document_type}: save capability without create/update permission")
    if descriptor.capabilities.print and not descriptor.permissions.print:
        warnings.append(f"{descriptor.document_type}: print capability without print permission")
    if descriptor.capabilities.export and not descriptor.permissions.export:
        warnings.append(f"{descriptor.document_type}: export capability without export permission")
    if descriptor.capabilities.delete and not descriptor.permissions.delete:
        warnings.append(f"{descriptor.document_type}: delete capability without delete permission")
    if descriptor.capabilities.approve and not descriptor.permissions.approve:
        warnings.append(f"{descriptor.document_type}: approve capability without approve permission")
    if descriptor.capabilities.cancel and not descriptor.permissions.cancel:
        warnings.append(f"{descriptor.document_type}: cancel capability without cancel permission")

    if descriptor.network_mode == NETWORK_REMOTE_REQUIRED and not descriptor.remote_gateway:
        warnings.append(f"{descriptor.document_type}: remote_required without remote_gateway")
    if descriptor.network_mode in {NETWORK_REMOTE_REQUIRED, NETWORK_REMOTE_AVAILABLE} and not descriptor.api_resource:
        warnings.append(f"{descriptor.document_type}: network document without api_resource")

    if descriptor.shell_family in {SHELL_TRANSACTION, SHELL_REPORT, SHELL_OPERATIONAL} and descriptor.currency_policy == CURRENCY_NONE:
        warnings.append(f"{descriptor.document_type}: money/report/operational shell without currency policy")

    return warnings


def assert_descriptor_valid(descriptor: DocumentDescriptor) -> None:
    warnings = validate_descriptor(descriptor)
    if warnings:
        raise DocumentContractError("; ".join(warnings))


def _p(scope: str, action: str) -> str:
    return f"{scope}.{action}"


def _std_permissions(scope: str, *, printable: bool = False, exportable: bool = False, deletable: bool = True, approvable: bool = False, cancellable: bool = False) -> DocumentPermissions:
    return DocumentPermissions(
        view=_p(scope, "view"),
        create=_p(scope, "create"),
        update=_p(scope, "update"),
        delete=_p(scope, "delete") if deletable else "",
        print=_p(scope, "print") if printable else "",
        export=_p(scope, "export") if exportable else "",
        approve=_p(scope, "approve") if approvable else "",
        cancel=_p(scope, "cancel") if cancellable else "",
    )


DOCUMENT_SHELL_DESCRIPTORS: tuple[DocumentDescriptor, ...] = (
    DocumentDescriptor(
        document_type="sales_invoice",
        shell_family=SHELL_TRANSACTION,
        title_key="sales_invoice",
        i18n_scope="transactions.sales_invoice",
        settings_scope="transactions.sales_invoice",
        gateway="invoice_gateway",
        api_resource="/api/invoices",
        network_mode=NETWORK_REMOTE_AVAILABLE,
        permissions=_std_permissions("sales_invoices", printable=True, exportable=True, approvable=True, cancellable=True),
        capabilities=DocumentCapabilities(print=True, export=True, delete=True, approve=True, cancel=True, grid_layout=True, workflow=True),
        currency_policy=CURRENCY_DOCUMENT,
        branch_policy=BRANCH_REQUIRED,
        audit_scope="transactions.sales_invoice",
        workspace_route="open_quick_invoice('sale')",
        list_route="sales_invoices",
        document_class="features.transactions.documents.sales_invoice_tab.SalesInvoiceTab",
        local_gateway="gateways.local.invoice_gateway.LocalInvoiceGateway",
        remote_gateway="gateways.remote.invoice_gateway.RemoteInvoiceGateway",
        server_blueprint="invoices",
    ),
    DocumentDescriptor(
        document_type="purchase_invoice",
        shell_family=SHELL_TRANSACTION,
        title_key="purchase_invoice",
        i18n_scope="transactions.purchase_invoice",
        settings_scope="transactions.purchase_invoice",
        gateway="invoice_gateway",
        api_resource="/api/invoices",
        network_mode=NETWORK_REMOTE_AVAILABLE,
        permissions=_std_permissions("purchase_invoices", printable=True, exportable=True, approvable=True, cancellable=True),
        capabilities=DocumentCapabilities(print=True, export=True, delete=True, approve=True, cancel=True, grid_layout=True, workflow=True),
        currency_policy=CURRENCY_DOCUMENT,
        branch_policy=BRANCH_REQUIRED,
        audit_scope="transactions.purchase_invoice",
        workspace_route="open_quick_invoice('purchase')",
        list_route="purchase_invoices",
        document_class="features.transactions.documents.purchase_invoice_tab.PurchaseInvoiceTab",
        local_gateway="gateways.local.invoice_gateway.LocalInvoiceGateway",
        remote_gateway="gateways.remote.invoice_gateway.RemoteInvoiceGateway",
        server_blueprint="invoices",
    ),
    DocumentDescriptor(
        document_type="sales_return",
        shell_family=SHELL_TRANSACTION,
        title_key="sales_return",
        i18n_scope="transactions.sales_return",
        settings_scope="transactions.sales_return",
        gateway="sales_return_gateway",
        api_resource="/api/returns/sales",
        network_mode=NETWORK_REMOTE_REQUIRED,
        permissions=_std_permissions("sales_returns", printable=True, exportable=True, approvable=True, cancellable=True),
        capabilities=DocumentCapabilities(print=True, export=True, delete=True, approve=True, cancel=True, grid_layout=True, workflow=True),
        currency_policy=CURRENCY_DOCUMENT,
        branch_policy=BRANCH_REQUIRED,
        audit_scope="transactions.sales_return",
        workspace_route="open_return_document('sale')",
        list_route="returns",
        document_class="features.transactions.documents.sales_return_tab.SalesReturnTab",
        local_gateway="gateways.local.sales_return_gateway.LocalSalesReturnGateway",
        remote_gateway="gateways.remote.sales_return_gateway.RemoteSalesReturnGateway",
        server_blueprint="returns",
        notes="Remote update parity must remain guarded by tests.",
    ),
    DocumentDescriptor(
        document_type="purchase_return",
        shell_family=SHELL_TRANSACTION,
        title_key="purchase_return",
        i18n_scope="transactions.purchase_return",
        settings_scope="transactions.purchase_return",
        gateway="purchase_return_gateway",
        api_resource="/api/returns/purchase",
        network_mode=NETWORK_REMOTE_REQUIRED,
        permissions=_std_permissions("purchase_returns", printable=True, exportable=True, approvable=True, cancellable=True),
        capabilities=DocumentCapabilities(print=True, export=True, delete=True, approve=True, cancel=True, grid_layout=True, workflow=True),
        currency_policy=CURRENCY_DOCUMENT,
        branch_policy=BRANCH_REQUIRED,
        audit_scope="transactions.purchase_return",
        workspace_route="open_return_document('purchase')",
        list_route="purchase_returns",
        document_class="features.transactions.documents.purchase_return_tab.PurchaseReturnTab",
        local_gateway="gateways.local.purchase_return_gateway.LocalPurchaseReturnGateway",
        remote_gateway="gateways.remote.purchase_return_gateway.RemotePurchaseReturnGateway",
        server_blueprint="returns",
        notes="Remote update parity must remain guarded by tests.",
    ),
    DocumentDescriptor(
        document_type="material",
        shell_family=SHELL_DOCUMENT,
        title_key="items",
        i18n_scope="materials.document",
        settings_scope="materials",
        gateway="product_gateway",
        api_resource="/api/items",
        network_mode=NETWORK_REMOTE_AVAILABLE,
        permissions=_std_permissions("items", printable=True, exportable=True, deletable=True),
        capabilities=DocumentCapabilities(print=True, export=True, delete=True, barcode=True, grid_layout=True),
        currency_policy=CURRENCY_DISPLAY,
        branch_policy=BRANCH_OPTIONAL,
        audit_scope="materials",
        workspace_route="open_item_document",
        list_route="items",
        document_class="features.items.item_editor_tab.MaterialDocumentTab",
        local_gateway="gateways.local.product_gateway.LocalProductGateway",
        remote_gateway="gateways.remote.product_gateway.RemoteProductGateway",
        server_blueprint="items",
    ),
    DocumentDescriptor(
        document_type="category",
        shell_family=SHELL_DOCUMENT,
        title_key="categories",
        i18n_scope="categories.document",
        settings_scope="categories",
        gateway="category_gateway",
        api_resource="/api/categories",
        network_mode=NETWORK_MIXED,
        permissions=_std_permissions("categories", printable=False, exportable=False, deletable=True),
        capabilities=DocumentCapabilities(delete=True),
        currency_policy=CURRENCY_NONE,
        branch_policy=BRANCH_NONE,
        audit_scope="categories",
        workspace_route="open_category_document",
        list_route="categories",
        document_class="features.categories.category_editor_tab.CategoryEditorTab",
        server_blueprint="categories",
    ),
    DocumentDescriptor(
        document_type="customer",
        shell_family=SHELL_DOCUMENT,
        title_key="customers",
        i18n_scope="parties.customer",
        settings_scope="parties.customers",
        gateway="entity_gateway",
        api_resource="/api/customers",
        network_mode=NETWORK_REMOTE_AVAILABLE,
        permissions=_std_permissions("customers", printable=True, exportable=True, deletable=True),
        capabilities=DocumentCapabilities(print=True, export=True, delete=True),
        currency_policy=CURRENCY_DISPLAY,
        branch_policy=BRANCH_OPTIONAL,
        audit_scope="parties.customer",
        workspace_route="open_party_document('customer')",
        list_route="customers",
        document_class="features.parties.party_editor_tab.PartyEditorTab",
        local_gateway="gateways.local.entity_gateway.LocalEntityGateway",
        remote_gateway="gateways.remote.entity_gateway.RemoteEntityGateway",
        server_blueprint="customers",
    ),
    DocumentDescriptor(
        document_type="supplier",
        shell_family=SHELL_DOCUMENT,
        title_key="suppliers",
        i18n_scope="parties.supplier",
        settings_scope="parties.suppliers",
        gateway="entity_gateway",
        api_resource="/api/suppliers",
        network_mode=NETWORK_REMOTE_AVAILABLE,
        permissions=_std_permissions("suppliers", printable=True, exportable=True, deletable=True),
        capabilities=DocumentCapabilities(print=True, export=True, delete=True),
        currency_policy=CURRENCY_DISPLAY,
        branch_policy=BRANCH_OPTIONAL,
        audit_scope="parties.supplier",
        workspace_route="open_party_document('supplier')",
        list_route="suppliers",
        document_class="features.parties.party_editor_tab.PartyEditorTab",
        local_gateway="gateways.local.entity_gateway.LocalEntityGateway",
        remote_gateway="gateways.remote.entity_gateway.RemoteEntityGateway",
        server_blueprint="suppliers",
    ),
    DocumentDescriptor(
        document_type="voucher",
        shell_family=SHELL_DOCUMENT,
        title_key="vouchers",
        i18n_scope="finance.voucher",
        settings_scope="finance.vouchers",
        gateway="voucher_gateway",
        api_resource="/api/vouchers",
        network_mode=NETWORK_REMOTE_AVAILABLE,
        permissions=_std_permissions("vouchers", printable=True, exportable=True, deletable=True, approvable=True, cancellable=True),
        capabilities=DocumentCapabilities(print=True, export=True, delete=True, approve=True, cancel=True, workflow=True),
        currency_policy=CURRENCY_MONEY,
        branch_policy=BRANCH_OPTIONAL,
        audit_scope="finance.voucher",
        workspace_route="open_quick_voucher",
        list_route="vouchers",
        document_class="features.vouchers.voucher_editor_tab.VoucherEditorTab",
        local_gateway="gateways.local.voucher_gateway.LocalVoucherGateway",
        remote_gateway="gateways.remote.voucher_gateway.RemoteVoucherGateway",
        server_blueprint="vouchers",
    ),
    DocumentDescriptor(
        document_type="expense",
        shell_family=SHELL_DOCUMENT,
        title_key="expense",
        i18n_scope="finance.expense",
        settings_scope="finance.expenses",
        gateway="expense_gateway",
        api_resource="/api/expenses",
        network_mode=NETWORK_REMOTE_AVAILABLE,
        permissions=_std_permissions("expenses", printable=True, exportable=True, deletable=True, approvable=False, cancellable=True),
        capabilities=DocumentCapabilities(print=True, export=True, delete=True, cancel=True),
        currency_policy=CURRENCY_MONEY,
        branch_policy=BRANCH_OPTIONAL,
        audit_scope="finance.expense",
        workspace_route="open_expense_document",
        list_route="expenses",
        document_class="features.finance.documents.expense_document_tab.ExpenseDocumentTab",
        local_gateway="gateways.local.expense_gateway.LocalExpenseGateway",
        remote_gateway="gateways.remote.expense_gateway.RemoteExpenseGateway",
        server_blueprint="expenses",
    ),
    DocumentDescriptor(
        document_type="cashbox",
        shell_family=SHELL_DOCUMENT,
        title_key="cashboxes",
        i18n_scope="finance.cashbox",
        settings_scope="finance.cashboxes",
        gateway="cashbox_gateway",
        api_resource="/api/cashboxes",
        network_mode=NETWORK_REMOTE_AVAILABLE,
        permissions=_std_permissions("cashboxes", printable=False, exportable=False, deletable=True),
        capabilities=DocumentCapabilities(delete=True),
        currency_policy=CURRENCY_DISPLAY,
        branch_policy=BRANCH_OPTIONAL,
        audit_scope="finance.cashbox",
        workspace_route="open_cashbox_document",
        list_route="cashboxes",
        document_class="features.finance.documents.cashbox_document_tab.CashboxDocumentTab",
        local_gateway="gateways.local.cashbox_gateway.LocalCashboxGateway",
        remote_gateway="gateways.remote.cashbox_gateway.RemoteCashboxGateway",
        server_blueprint="cashboxes",
    ),
    DocumentDescriptor(
        document_type="bank_account",
        shell_family=SHELL_DOCUMENT,
        title_key="bank_accounts",
        i18n_scope="finance.bank_account",
        settings_scope="finance.bank_accounts",
        gateway="cashbox_gateway",
        api_resource="/api/bank_accounts",
        network_mode=NETWORK_REMOTE_AVAILABLE,
        permissions=_std_permissions("bank_accounts", printable=False, exportable=False, deletable=True),
        capabilities=DocumentCapabilities(delete=True),
        currency_policy=CURRENCY_DISPLAY,
        branch_policy=BRANCH_OPTIONAL,
        audit_scope="finance.bank_account",
        workspace_route="open_bank_account_document",
        list_route="cashboxes",
        document_class="features.finance.documents.bank_account_document_tab.BankAccountDocumentTab",
        local_gateway="gateways.local.cashbox_gateway.LocalCashboxGateway",
        remote_gateway="gateways.remote.cashbox_gateway.RemoteCashboxGateway",
        server_blueprint="cashboxes",
    ),
    DocumentDescriptor(
        document_type="warehouse",
        shell_family=SHELL_DOCUMENT,
        title_key="warehouses",
        i18n_scope="inventory.warehouse",
        settings_scope="inventory.warehouses",
        gateway="warehouse_gateway",
        api_resource="/api/warehouses",
        network_mode=NETWORK_REMOTE_AVAILABLE,
        permissions=_std_permissions("warehouses", printable=True, exportable=True, deletable=True),
        capabilities=DocumentCapabilities(print=True, export=True, delete=True),
        currency_policy=CURRENCY_NONE,
        branch_policy=BRANCH_OPTIONAL,
        audit_scope="inventory.warehouse",
        workspace_route="open_warehouse_document",
        list_route="warehouses",
        document_class="features.inventory.documents.warehouse_document_tab.WarehouseDocumentTab",
        local_gateway="gateways.local.warehouse_gateway.LocalWarehouseGateway",
        remote_gateway="gateways.remote.warehouse_gateway.RemoteWarehouseGateway",
        server_blueprint="warehouses",
    ),
    DocumentDescriptor(
        document_type="warehouse_transfer",
        shell_family=SHELL_DOCUMENT,
        title_key="inventory_transfer",
        i18n_scope="inventory.transfer",
        settings_scope="inventory.transfers",
        gateway="warehouse_gateway",
        api_resource="/api/warehouse-transfers",
        network_mode=NETWORK_REMOTE_AVAILABLE,
        permissions=_std_permissions("warehouse_transfers", printable=True, exportable=True, deletable=False, cancellable=True),
        capabilities=DocumentCapabilities(print=True, export=True, cancel=True, grid_layout=True),
        currency_policy=CURRENCY_NONE,
        branch_policy=BRANCH_REQUIRED,
        audit_scope="inventory.transfer",
        workspace_route="open_inventory_transfer_document",
        list_route="warehouses",
        document_class="features.inventory.documents.inventory_transfer_document_tab.InventoryTransferDocumentTab",
        local_gateway="gateways.local.warehouse_gateway.LocalWarehouseGateway",
        remote_gateway="gateways.remote.warehouse_gateway.RemoteWarehouseGateway",
        server_blueprint="warehouses",
    ),
    DocumentDescriptor(
        document_type="branch",
        shell_family=SHELL_DOCUMENT,
        title_key="branches",
        i18n_scope="branches.document",
        settings_scope="branches",
        gateway="branch_gateway",
        api_resource="/api/branches",
        network_mode=NETWORK_REMOTE_AVAILABLE,
        permissions=_std_permissions("branches", printable=False, exportable=False, deletable=True),
        capabilities=DocumentCapabilities(delete=True),
        currency_policy=CURRENCY_NONE,
        branch_policy=BRANCH_NONE,
        audit_scope="branches",
        workspace_route="open_branch_document",
        list_route="branches",
        document_class="features.branches.documents.branch_document_tab.BranchDocumentTab",
        local_gateway="gateways.local.branch_gateway.LocalBranchGateway",
        remote_gateway="gateways.remote.branch_gateway.RemoteBranchGateway",
        server_blueprint="branches",
    ),
    DocumentDescriptor(
        document_type="bom",
        shell_family=SHELL_DOCUMENT,
        title_key="bom",
        i18n_scope="manufacturing.bom",
        settings_scope="manufacturing.bom",
        gateway="manufacturing_gateway",
        api_resource="/api/manufacturing/boms",
        network_mode=NETWORK_REMOTE_AVAILABLE,
        permissions=_std_permissions("manufacturing.bom", printable=True, exportable=True, deletable=True, approvable=True, cancellable=True),
        capabilities=DocumentCapabilities(print=True, export=True, delete=True, approve=True, cancel=True, grid_layout=True, workflow=True),
        currency_policy=CURRENCY_MONEY,
        branch_policy=BRANCH_OPTIONAL,
        audit_scope="manufacturing.bom",
        workspace_route="open_bom_document",
        list_route="manufacturing",
        document_class="features.manufacturing.bom_document_tab.BomDocumentTab",
        local_gateway="gateways.local.manufacturing_gateway.LocalManufacturingGateway",
        remote_gateway="gateways.remote.manufacturing_gateway.RemoteManufacturingGateway",
        server_blueprint="manufacturing",
    ),
    DocumentDescriptor(
        document_type="production_order",
        shell_family=SHELL_DOCUMENT,
        title_key="production_order",
        i18n_scope="manufacturing.production_order",
        settings_scope="manufacturing.production_orders",
        gateway="manufacturing_gateway",
        api_resource="/api/manufacturing/production-orders",
        network_mode=NETWORK_REMOTE_AVAILABLE,
        permissions=_std_permissions("manufacturing.production_orders", printable=True, exportable=True, deletable=False, approvable=True, cancellable=True),
        capabilities=DocumentCapabilities(print=True, export=True, approve=True, cancel=True, grid_layout=True, workflow=True),
        currency_policy=CURRENCY_MONEY,
        branch_policy=BRANCH_OPTIONAL,
        audit_scope="manufacturing.production_order",
        workspace_route="open_production_order_document",
        list_route="manufacturing",
        document_class="features.manufacturing.production_order_document_tab.ProductionOrderDocumentTab",
        local_gateway="gateways.local.manufacturing_gateway.LocalManufacturingGateway",
        remote_gateway="gateways.remote.manufacturing_gateway.RemoteManufacturingGateway",
        server_blueprint="manufacturing",
    ),
    DocumentDescriptor(
        document_type="user",
        shell_family=SHELL_DOCUMENT,
        title_key="users",
        i18n_scope="users.document",
        settings_scope="users",
        gateway="user_gateway",
        api_resource="/api/users",
        network_mode=NETWORK_REMOTE_AVAILABLE,
        permissions=_std_permissions("users", printable=False, exportable=False, deletable=True),
        capabilities=DocumentCapabilities(delete=True, audit=True),
        currency_policy=CURRENCY_NONE,
        branch_policy=BRANCH_USER_ACCESS,
        audit_scope="users",
        workspace_route="open_user_document",
        list_route="users",
        document_class="features.users.documents.user_document_tab.UserDocumentTab",
        local_gateway="gateways.local.user_gateway.LocalUserGateway",
        remote_gateway="gateways.remote.user_gateway.RemoteUserGateway",
        server_blueprint="users",
    ),
    DocumentDescriptor(
        document_type="settings_section",
        shell_family=SHELL_DOCUMENT,
        title_key="settings",
        i18n_scope="settings.document",
        settings_scope="settings",
        gateway="settings_gateway",
        api_resource="/api/settings",
        network_mode=NETWORK_REMOTE_AVAILABLE,
        permissions=DocumentPermissions(view="settings.view", update="settings.update", export="settings.export"),
        capabilities=DocumentCapabilities(save=True, print=False, export=True, delete=False, audit=True),
        currency_policy=CURRENCY_NONE,
        branch_policy=BRANCH_NONE,
        audit_scope="settings",
        workspace_route="open_settings_section_document",
        list_route="settings",
        document_class="features.settings.settings_document_tabs.SettingsSectionDocumentTab",
        local_gateway="gateways.local.settings_gateway.LocalSettingsGateway",
        remote_gateway="gateways.remote.settings_gateway.RemoteSettingsGateway",
        server_blueprint="settings",
    ),
    DocumentDescriptor(
        document_type="reports",
        shell_family=SHELL_REPORT,
        title_key="reports",
        i18n_scope="reports.shell",
        settings_scope="reports",
        gateway="reporting_gateway",
        api_resource="/api/reports",
        network_mode=NETWORK_REMOTE_AVAILABLE,
        permissions=DocumentPermissions(view="reports.view", print="reports.print", export="reports.export"),
        capabilities=DocumentCapabilities(save=False, print=True, export=True, delete=False, audit=True),
        currency_policy=CURRENCY_DISPLAY,
        branch_policy=BRANCH_OPTIONAL,
        audit_scope="reports",
        workspace_route="reports widget",
        list_route="reports",
        document_class="views.widgets.reports_widget.ReportsWidget",
        local_gateway="gateways.local.reporting_gateway.LocalReportingGateway",
        remote_gateway="gateways.remote.reporting_gateway.RemoteReportingGateway",
        server_blueprint="reports",
        notes="ReportShell is currently a widget contract target, not yet a BaseDocumentTab.",
    ),
    DocumentDescriptor(
        document_type="pos",
        shell_family=SHELL_OPERATIONAL,
        title_key="pos",
        i18n_scope="pos.shell",
        settings_scope="pos",
        gateway="invoice_gateway",
        api_resource="/api/invoices",
        network_mode=NETWORK_REMOTE_AVAILABLE,
        permissions=DocumentPermissions(view="pos.view", create="pos.checkout", print="pos.print", cancel="pos.void"),
        capabilities=DocumentCapabilities(save=True, print=True, export=False, delete=False, cancel=True, barcode=True, audit=True, offline_queue=True),
        currency_policy=CURRENCY_DISPLAY,
        branch_policy=BRANCH_REQUIRED,
        audit_scope="pos",
        workspace_route="pos widget",
        list_route="pos",
        document_class="views.widgets.pos_widget.POSWidget",
        local_gateway="gateways.local.invoice_gateway.LocalInvoiceGateway",
        remote_gateway="gateways.remote.invoice_gateway.RemoteInvoiceGateway",
        server_blueprint="invoices",
        notes="OperationalShell: shift/cashbox/warehouse policy is intentionally different from document tabs.",
    ),
    DocumentDescriptor(
        document_type="restaurant",
        shell_family=SHELL_OPERATIONAL,
        title_key="restaurant",
        i18n_scope="restaurant.shell",
        settings_scope="restaurant",
        gateway="restaurant_gateway",
        api_resource="/api/restaurant",
        network_mode=NETWORK_REMOTE_AVAILABLE,
        permissions=DocumentPermissions(view="restaurant.view", create="restaurant.order", update="restaurant.order.update", print="restaurant.print", cancel="restaurant.cancel"),
        capabilities=DocumentCapabilities(save=True, print=True, export=False, delete=False, cancel=True, barcode=True, audit=True, offline_queue=True),
        currency_policy=CURRENCY_DISPLAY,
        branch_policy=BRANCH_REQUIRED,
        audit_scope="restaurant",
        workspace_route="restaurant widget",
        list_route="restaurant",
        document_class="views.restaurant.restaurant_pos_widget.RestaurantPOSWidget",
        local_gateway="gateways.local.restaurant_gateway.LocalRestaurantGateway",
        remote_gateway="gateways.remote.restaurant_gateway.RemoteRestaurantGateway",
        server_blueprint="restaurant",
        notes="OperationalShell: table/session/kitchen policy is intentionally different from document tabs.",
    ),
    DocumentDescriptor(
        document_type="cafe",
        shell_family=SHELL_OPERATIONAL,
        title_key="restaurant.cafe_workspace_title",
        i18n_scope="cafe.shell",
        settings_scope="cafe",
        gateway="restaurant_gateway",
        api_resource="/api/restaurant",
        network_mode=NETWORK_REMOTE_AVAILABLE,
        permissions=DocumentPermissions(view="cafe.view", create="cafe.order", update="cafe.payment", print="cafe.print", export="cafe.report", cancel="restaurant.cancel"),
        capabilities=DocumentCapabilities(save=True, print=True, export=True, delete=False, cancel=True, barcode=True, audit=True, offline_queue=True),
        currency_policy=CURRENCY_DISPLAY,
        branch_policy=BRANCH_REQUIRED,
        audit_scope="cafe",
        workspace_route="cafe widget",
        list_route="cafe",
        document_class="views.cafe.cafe_workspace_widget.CafeWorkspaceWidget",
        local_gateway="gateways.local.restaurant_gateway.LocalRestaurantGateway",
        remote_gateway="gateways.remote.restaurant_gateway.RemoteRestaurantGateway",
        server_blueprint="restaurant",
        notes="Standalone Cafe UI: visible module is separate, but orders/payment/printing/inventory reuse the restaurant engine.",
    ),
)


_DESCRIPTOR_BY_TYPE: dict[str, DocumentDescriptor] = {d.document_type: d for d in DOCUMENT_SHELL_DESCRIPTORS}


def descriptor_for(document_type: str, default: DocumentDescriptor | None = None) -> DocumentDescriptor | None:
    return _DESCRIPTOR_BY_TYPE.get(str(document_type or ""), default)


def all_descriptors() -> tuple[DocumentDescriptor, ...]:
    return DOCUMENT_SHELL_DESCRIPTORS


def descriptors_by_family(shell_family: str) -> tuple[DocumentDescriptor, ...]:
    return tuple(d for d in DOCUMENT_SHELL_DESCRIPTORS if d.shell_family == shell_family)


def validate_all_descriptors(descriptors: Iterable[DocumentDescriptor] | None = None) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for descriptor in descriptors or DOCUMENT_SHELL_DESCRIPTORS:
        warnings = validate_descriptor(descriptor)
        if warnings:
            result[descriptor.document_type] = warnings
    return result


def contract_matrix() -> list[dict[str, object]]:
    """Small serialisable matrix for diagnostics, CI output and future UI report."""

    rows: list[dict[str, object]] = []
    for d in DOCUMENT_SHELL_DESCRIPTORS:
        rows.append({
            "document_type": d.document_type,
            "shell_family": d.shell_family,
            "class": d.document_class,
            "api_resource": d.api_resource,
            "network_mode": d.network_mode,
            "settings_scope": d.settings_scope,
            "i18n_scope": d.i18n_scope,
            "currency_policy": d.currency_policy,
            "branch_policy": d.branch_policy,
            "can_print": d.capabilities.print,
            "can_export": d.capabilities.export,
            "can_delete": d.capabilities.delete,
            "can_approve": d.capabilities.approve,
            "can_cancel": d.capabilities.cancel,
            "permission_view": d.permissions.view,
            "permission_print": d.permissions.print,
            "permission_export": d.permissions.export,
            "local_gateway": d.local_gateway,
            "remote_gateway": d.remote_gateway,
            "legacy_adapter": d.legacy_adapter,
        })
    return rows
