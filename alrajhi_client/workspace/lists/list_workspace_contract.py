# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from workspace.documents.document_contract import (
    BRANCH_NONE,
    BRANCH_OPTIONAL,
    BRANCH_REQUIRED,
    BRANCH_USER_ACCESS,
    CURRENCY_DISPLAY,
    CURRENCY_DOCUMENT,
    CURRENCY_MONEY,
    CURRENCY_NONE,
    NETWORK_LOCAL_ONLY,
    NETWORK_MIXED,
    NETWORK_REMOTE_AVAILABLE,
    DocumentDescriptor,
    descriptor_for,
)


LIST_ACTIONS = (
    "view",
    "search",
    "filter",
    "refresh",
    "columns",
    "open",
    "create",
    "update",
    "delete",
    "print",
    "export",
)


@dataclass(frozen=True)
class ListWorkspaceCapabilities:
    """Capabilities every list/grid workspace must declare.

    The list shell is intentionally separate from Document Shell: lists are
    query/open/filter surfaces, while document tabs are edit surfaces.  Both
    point to the same DocumentDescriptor so permissions, API, language, branch,
    money, and audit policies remain aligned.
    """

    search: bool = True
    filters: bool = True
    pagination: bool = False
    column_preferences: bool = True
    row_open: bool = True
    create: bool = True
    update: bool = True
    delete: bool = False
    print: bool = False
    export: bool = False
    batch_actions: bool = False
    barcode: bool = False


@dataclass(frozen=True)
class ListWorkspaceDescriptor:
    list_key: str
    document_type: str
    title_key: str
    widget_class: str
    workspace_route: str
    open_route: str
    api_resource: str
    network_mode: str
    i18n_scope: str
    settings_scope: str
    table_identity: str
    search_placeholder_key: str = "search_placeholder"
    filter_keys: tuple[str, ...] = ()
    column_keys: tuple[str, ...] = ()
    capabilities: ListWorkspaceCapabilities = field(default_factory=ListWorkspaceCapabilities)
    currency_policy: str = CURRENCY_NONE
    branch_policy: str = BRANCH_NONE
    document_descriptor_type: str = ""
    local_gateway: str = ""
    remote_gateway: str = ""
    server_blueprint: str = ""
    audit_scope: str = ""
    legacy_adapter: bool = False
    notes: str = ""

    @property
    def document_descriptor(self) -> DocumentDescriptor | None:
        return descriptor_for(self.document_descriptor_type or self.document_type)

    @property
    def permissions(self):
        descriptor = self.document_descriptor
        return descriptor.permissions if descriptor else None

    def permission_for(self, action: str) -> str:
        permissions = self.permissions
        if permissions is None:
            return ""
        if action == "open":
            return permissions.view
        if action == "search" or action == "filter" or action == "refresh" or action == "columns":
            return permissions.view
        if action == "create":
            return permissions.create
        if action == "update":
            return permissions.update
        return permissions.action_map().get(action, "")

    @property
    def is_network_ready(self) -> bool:
        return self.network_mode in {NETWORK_REMOTE_AVAILABLE}


def _doc(document_type: str) -> DocumentDescriptor:
    descriptor = descriptor_for(document_type)
    if descriptor is None:
        raise KeyError(f"Missing document descriptor for {document_type}")
    return descriptor


def _list(
    *,
    list_key: str,
    document_type: str,
    title_key: str,
    widget_class: str,
    workspace_route: str,
    open_route: str,
    table_identity: str,
    filter_keys: tuple[str, ...] = (),
    column_keys: tuple[str, ...] = (),
    capabilities: ListWorkspaceCapabilities | None = None,
    currency_policy: str | None = None,
    branch_policy: str | None = None,
    legacy_adapter: bool = False,
    notes: str = "",
) -> ListWorkspaceDescriptor:
    doc = _doc(document_type)
    return ListWorkspaceDescriptor(
        list_key=list_key,
        document_type=document_type,
        title_key=title_key,
        widget_class=widget_class,
        workspace_route=workspace_route,
        open_route=open_route,
        api_resource=doc.api_resource,
        network_mode=doc.network_mode,
        i18n_scope=doc.i18n_scope,
        settings_scope=f"{doc.settings_scope}.list",
        table_identity=table_identity,
        filter_keys=filter_keys,
        column_keys=column_keys,
        capabilities=capabilities or ListWorkspaceCapabilities(
            delete=doc.capabilities.delete,
            print=doc.capabilities.print,
            export=doc.capabilities.export,
            pagination=True,
        ),
        currency_policy=currency_policy or doc.currency_policy,
        branch_policy=branch_policy or doc.branch_policy,
        document_descriptor_type=document_type,
        local_gateway=doc.local_gateway,
        remote_gateway=doc.remote_gateway,
        server_blueprint=doc.server_blueprint,
        audit_scope=f"{doc.audit_scope}.list" if doc.audit_scope else f"{document_type}.list",
        legacy_adapter=legacy_adapter,
        notes=notes,
    )


LIST_WORKSPACE_DESCRIPTORS: tuple[ListWorkspaceDescriptor, ...] = (
    _list(
        list_key="sales_invoices",
        document_type="sales_invoice",
        title_key="sales_invoices",
        widget_class="views.widgets.invoices_widget.SalesInvoicesWidget",
        workspace_route="sales_invoices",
        open_route="open_quick_invoice('sale')",
        table_identity="transactions.sales_invoices.list",
        filter_keys=("date_from", "date_to", "status", "customer", "branch"),
        column_keys=("reference", "invoice_total", "customer", "received", "remaining", "workflow_status", "date", "notes"),
    ),
    _list(
        list_key="purchase_invoices",
        document_type="purchase_invoice",
        title_key="purchase_invoices",
        widget_class="views.widgets.invoices_widget.PurchaseInvoicesWidget",
        workspace_route="purchase_invoices",
        open_route="open_quick_invoice('purchase')",
        table_identity="transactions.purchase_invoices.list",
        filter_keys=("date_from", "date_to", "status", "supplier", "branch"),
        column_keys=("reference", "invoice_total", "supplier", "paid", "remaining", "workflow_status", "date", "notes"),
    ),
    _list(
        list_key="sales_returns",
        document_type="sales_return",
        title_key="sales_returns",
        widget_class="views.widgets.returns_widget.ReturnsWidget",
        workspace_route="returns",
        open_route="open_return_document('sale')",
        table_identity="transactions.sales_returns.list",
        filter_keys=("date_from", "date_to", "customer", "branch"),
        column_keys=("reference", "return_total", "customer", "received", "remaining", "workflow_status", "date", "notes"),
    ),
    _list(
        list_key="purchase_returns",
        document_type="purchase_return",
        title_key="purchase_returns",
        widget_class="views.widgets.returns_widget.PurchaseReturnsWidget",
        workspace_route="purchase_returns",
        open_route="open_return_document('purchase')",
        table_identity="transactions.purchase_returns.list",
        filter_keys=("date_from", "date_to", "supplier", "branch"),
        column_keys=("reference", "return_total", "supplier", "paid", "remaining", "workflow_status", "date", "notes"),
    ),
    _list(
        list_key="materials",
        document_type="material",
        title_key="items_inventory",
        widget_class="views.widgets.items_widget.ItemsWidget",
        workspace_route="items",
        open_route="open_item_document(item_id=...) / open_item_document()",
        table_identity="materials.workspace.items_grid",
        filter_keys=("category", "item_type", "stock_status", "preset", "density"),
        column_keys=("barcode", "name", "category_name", "item_type", "sale_price", "purchase_price", "stock", "unit_name"),
        capabilities=ListWorkspaceCapabilities(pagination=True, delete=True, print=True, export=True, batch_actions=True, barcode=True),
    ),
    _list(
        list_key="categories",
        document_type="category",
        title_key="categories",
        widget_class="views.widgets.categories_widget.CategoriesWidget",
        workspace_route="categories",
        open_route="category document/editor",
        table_identity="categories.list",
        filter_keys=("parent", "status"),
        column_keys=("path", "parent", "items_count", "child_categories", "status", "description"),
    ),
    _list(
        list_key="customers",
        document_type="customer",
        title_key="customers",
        widget_class="views.widgets.customers_widget.CustomersWidget",
        workspace_route="customers",
        open_route="open_party_document('customer')",
        table_identity="customers.list",
        filter_keys=("balance_status",),
        column_keys=("name", "phone", "address", "balance"),
        capabilities=ListWorkspaceCapabilities(pagination=True, delete=False, print=False, export=True),
        currency_policy=CURRENCY_DISPLAY,
        branch_policy=BRANCH_OPTIONAL,
    ),
    _list(
        list_key="suppliers",
        document_type="supplier",
        title_key="suppliers",
        widget_class="views.widgets.suppliers_widget.SuppliersWidget",
        workspace_route="suppliers",
        open_route="open_party_document('supplier')",
        table_identity="suppliers.list",
        filter_keys=("balance_status",),
        column_keys=("name", "phone", "address", "balance"),
        capabilities=ListWorkspaceCapabilities(pagination=True, delete=False, print=False, export=True),
        currency_policy=CURRENCY_DISPLAY,
        branch_policy=BRANCH_OPTIONAL,
    ),
    _list(
        list_key="vouchers",
        document_type="voucher",
        title_key="vouchers_title",
        widget_class="views.widgets.vouchers_widget.VouchersWidget",
        workspace_route="vouchers",
        open_route="open_quick_voucher(voucher_id=...) / open_quick_voucher()",
        table_identity="vouchers.list",
        filter_keys=("voucher_type", "date_from", "date_to", "account"),
        column_keys=("date", "type", "party", "amount", "account", "description"),
        capabilities=ListWorkspaceCapabilities(pagination=True, delete=True, print=True, export=True),
        currency_policy=CURRENCY_MONEY,
    ),
    _list(
        list_key="cashboxes",
        document_type="cashbox",
        title_key="cashboxes",
        widget_class="views.widgets.cashboxes_widget.CashboxesWidget",
        workspace_route="cashboxes",
        open_route="cashbox editor/document",
        table_identity="cashboxes.list",
        filter_keys=("active", "branch"),
        column_keys=("name", "branch", "balance", "currency", "is_default"),
        capabilities=ListWorkspaceCapabilities(pagination=False, delete=True, print=False, export=False),
        currency_policy=CURRENCY_DISPLAY,
        branch_policy=BRANCH_OPTIONAL,
    ),
    _list(
        list_key="warehouses",
        document_type="warehouse",
        title_key="warehouses",
        widget_class="views.widgets.warehouses_widget.WarehousesWidget",
        workspace_route="warehouses",
        open_route="warehouse document/editor",
        table_identity="warehouses.list",
        filter_keys=("branch", "active"),
        column_keys=("name", "branch", "code", "is_default", "status"),
        capabilities=ListWorkspaceCapabilities(pagination=False, delete=True, print=True, export=True),
        branch_policy=BRANCH_USER_ACCESS,
    ),
    _list(
        list_key="warehouse_transfers",
        document_type="warehouse_transfer",
        title_key="warehouse_transfers",
        widget_class="views.widgets.warehouses_widget.WarehousesWidget",
        workspace_route="warehouses.transfers",
        open_route="open_inventory_transfer_document(...) / transfer tab",
        table_identity="inventory.transfers.list",
        filter_keys=("date_from", "date_to", "from_warehouse", "to_warehouse", "status"),
        column_keys=("reference", "date", "from_warehouse", "to_warehouse", "status", "notes"),
        capabilities=ListWorkspaceCapabilities(pagination=False, delete=False, print=True, export=True),
        branch_policy=BRANCH_USER_ACCESS,
    ),
    _list(
        list_key="branches",
        document_type="branch",
        title_key="branches",
        widget_class="views.widgets.branches_widget.BranchesWidget",
        workspace_route="branches",
        open_route="open_branch_document(...) / branch tab",
        table_identity="branches.list",
        filter_keys=("active",),
        column_keys=("name", "code", "address", "phone", "warehouse_count", "is_default", "status"),
        capabilities=ListWorkspaceCapabilities(pagination=False, delete=True, print=False, export=False),
        branch_policy=BRANCH_USER_ACCESS,
    ),
)

_LIST_BY_KEY: dict[str, ListWorkspaceDescriptor] = {d.list_key: d for d in LIST_WORKSPACE_DESCRIPTORS}
_LIST_BY_DOCUMENT: dict[str, tuple[ListWorkspaceDescriptor, ...]] = {}
for _descriptor in LIST_WORKSPACE_DESCRIPTORS:
    _LIST_BY_DOCUMENT.setdefault(_descriptor.document_type, tuple())
for _doc_type in {d.document_type for d in LIST_WORKSPACE_DESCRIPTORS}:
    _LIST_BY_DOCUMENT[_doc_type] = tuple(d for d in LIST_WORKSPACE_DESCRIPTORS if d.document_type == _doc_type)


def list_descriptor_for(list_key: str, default: ListWorkspaceDescriptor | None = None) -> ListWorkspaceDescriptor | None:
    return _LIST_BY_KEY.get(list_key, default)


def list_descriptors() -> tuple[ListWorkspaceDescriptor, ...]:
    return LIST_WORKSPACE_DESCRIPTORS


def list_descriptors_for_document(document_type: str) -> tuple[ListWorkspaceDescriptor, ...]:
    return _LIST_BY_DOCUMENT.get(document_type, tuple())


def validate_list_descriptor(descriptor: ListWorkspaceDescriptor) -> list[str]:
    warnings: list[str] = []
    required = (
        "list_key",
        "document_type",
        "title_key",
        "widget_class",
        "workspace_route",
        "open_route",
        "api_resource",
        "network_mode",
        "i18n_scope",
        "settings_scope",
        "table_identity",
        "audit_scope",
    )
    for field_name in required:
        if not str(getattr(descriptor, field_name, "") or "").strip():
            warnings.append(f"{descriptor.list_key}: missing {field_name}")
    if descriptor.document_descriptor is None:
        warnings.append(f"{descriptor.list_key}: missing backing DocumentDescriptor {descriptor.document_type}")
    if descriptor.capabilities.create and not descriptor.permission_for("create"):
        warnings.append(f"{descriptor.list_key}: create capability without create permission")
    if descriptor.capabilities.update and not descriptor.permission_for("update"):
        warnings.append(f"{descriptor.list_key}: update capability without update permission")
    if descriptor.capabilities.delete and not descriptor.permission_for("delete"):
        warnings.append(f"{descriptor.list_key}: delete capability without delete permission")
    if descriptor.capabilities.print and not descriptor.permission_for("print"):
        warnings.append(f"{descriptor.list_key}: print capability without print permission")
    if descriptor.capabilities.export and not descriptor.permission_for("export"):
        warnings.append(f"{descriptor.list_key}: export capability without export permission")
    if descriptor.network_mode == NETWORK_REMOTE_AVAILABLE and not descriptor.remote_gateway:
        warnings.append(f"{descriptor.list_key}: remote_available without remote_gateway")
    if descriptor.currency_policy == CURRENCY_NONE and descriptor.document_descriptor and descriptor.document_descriptor.currency_policy != CURRENCY_NONE:
        warnings.append(f"{descriptor.list_key}: missing list currency policy for money-aware document")
    return warnings


def validate_list_descriptors(descriptors: tuple[ListWorkspaceDescriptor, ...] | None = None) -> list[str]:
    warnings: list[str] = []
    seen: set[str] = set()
    for descriptor in descriptors or LIST_WORKSPACE_DESCRIPTORS:
        if descriptor.list_key in seen:
            warnings.append(f"duplicate list_key {descriptor.list_key}")
        seen.add(descriptor.list_key)
        warnings.extend(validate_list_descriptor(descriptor))
    return warnings


def list_workspace_matrix(descriptors: tuple[ListWorkspaceDescriptor, ...] | None = None) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for descriptor in descriptors or LIST_WORKSPACE_DESCRIPTORS:
        rows.append({
            "list_key": descriptor.list_key,
            "document_type": descriptor.document_type,
            "widget_class": descriptor.widget_class,
            "workspace_route": descriptor.workspace_route,
            "open_route": descriptor.open_route,
            "api_resource": descriptor.api_resource,
            "network_mode": descriptor.network_mode,
            "table_identity": descriptor.table_identity,
            "filters": ",".join(descriptor.filter_keys),
            "columns": ",".join(descriptor.column_keys),
            "currency_policy": descriptor.currency_policy,
            "branch_policy": descriptor.branch_policy,
            "can_print": descriptor.capabilities.print,
            "can_export": descriptor.capabilities.export,
            "can_delete": descriptor.capabilities.delete,
        })
    return rows


class ListWorkspacePermissionBinder:
    """Small adapter from list actions to the existing document permission binder."""

    def __init__(self, descriptor: ListWorkspaceDescriptor):
        self.descriptor = descriptor
        self.document_descriptor = descriptor.document_descriptor

    def can(self, action: str, *, document_id=None) -> bool:
        if action in {"search", "filter", "refresh", "columns", "open"}:
            action = "view"
        try:
            from workspace.documents.document_permission_binder import DocumentPermissionBinder
            if self.document_descriptor is None:
                return True
            return DocumentPermissionBinder(self.document_descriptor).can(action, document_id=document_id)
        except Exception:
            return True

    def states(self, *, has_selection: bool = False) -> Mapping[str, bool]:
        d = self.descriptor.capabilities
        return {
            "add": d.create and self.can("create"),
            "edit": d.update and has_selection and self.can("update"),
            "delete": d.delete and has_selection and self.can("delete"),
            "print": d.print and self.can("print"),
            "export": d.export and self.can("export"),
            "columns": d.column_preferences and self.can("columns"),
            "search": d.search and self.can("search"),
            "refresh": self.can("refresh"),
        }

    def apply_to_widget(self, widget, *, has_selection: bool | None = None) -> Mapping[str, bool]:
        if has_selection is None:
            has_selection = False
            try:
                table = getattr(widget, "table", None)
                sm = table.selectionModel() if table is not None else None
                has_selection = bool(sm and sm.selectedRows())
            except Exception:
                has_selection = False
        states = self.states(has_selection=has_selection)
        button_map = {
            "add": ("add_btn", "new_btn"),
            "edit": ("edit_btn",),
            "delete": ("delete_btn", "remove_btn"),
            "print": ("print_btn", "print_barcode_btn", "batch_print_btn"),
            "export": ("export_btn",),
            "refresh": ("refresh_btn",),
        }
        for action, names in button_map.items():
            for name in names:
                btn = getattr(widget, name, None)
                if btn is not None and hasattr(btn, "setEnabled"):
                    try:
                        btn.setEnabled(bool(states.get(action, True)))
                    except Exception:
                        pass
        toolbar = getattr(widget, "toolbar", None)
        if toolbar is not None:
            for setter, action in (
                ("set_add_enabled", "add"),
                ("set_edit_enabled", "edit"),
                ("set_delete_enabled", "delete"),
                ("set_print_enabled", "print"),
                ("set_export_enabled", "export"),
            ):
                if hasattr(toolbar, setter):
                    try:
                        getattr(toolbar, setter)(bool(states.get(action, True)))
                    except Exception:
                        pass
        return states


def bind_list_workspace(widget, list_key: str) -> ListWorkspaceDescriptor | None:
    descriptor = list_descriptor_for(list_key)
    if descriptor is None:
        return None
    widget.list_workspace_descriptor = descriptor
    widget.document_descriptor = descriptor.document_descriptor
    widget.list_permission_binder = ListWorkspacePermissionBinder(descriptor)
    return descriptor
