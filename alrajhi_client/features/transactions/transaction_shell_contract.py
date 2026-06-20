# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from workspace.documents.document_contract import (
    BRANCH_REQUIRED,
    CURRENCY_DOCUMENT,
    NETWORK_REMOTE_AVAILABLE,
    NETWORK_REMOTE_REQUIRED,
    SHELL_TRANSACTION,
    DocumentDescriptor,
    descriptor_for,
)


@dataclass(frozen=True)
class TransactionShellRoute:
    """Canonical transaction-document route.

    This is intentionally Qt-free.  MainWindow and list widgets can use the
    route contract at runtime, while CI can inspect it without importing
    PyQt.  All invoice/return document surfaces must route through the
    classes declared here unless the explicit legacy emergency setting is
    enabled.
    """

    document_type: str
    transaction_kind: str
    invoice_type: str
    is_return: bool
    class_path: str
    opener: str
    list_route: str
    api_resource: str
    gateway: str
    service_name: str
    print_bridge: str = "features.transactions.components.transaction_printing_bridge.TransactionPrintingBridge"


SALES_INVOICE_ROUTE = TransactionShellRoute(
    document_type="sales_invoice",
    transaction_kind="invoice",
    invoice_type="sale",
    is_return=False,
    class_path="features.transactions.documents.sales_invoice_tab.SalesInvoiceTab",
    opener="open_quick_invoice('sale')",
    list_route="sales_invoices",
    api_resource="/api/invoices",
    gateway="invoice_gateway",
    service_name="invoice_service",
)

PURCHASE_INVOICE_ROUTE = TransactionShellRoute(
    document_type="purchase_invoice",
    transaction_kind="invoice",
    invoice_type="purchase",
    is_return=False,
    class_path="features.transactions.documents.purchase_invoice_tab.PurchaseInvoiceTab",
    opener="open_quick_invoice('purchase')",
    list_route="purchase_invoices",
    api_resource="/api/invoices",
    gateway="invoice_gateway",
    service_name="invoice_service",
)

SALES_RETURN_ROUTE = TransactionShellRoute(
    document_type="sales_return",
    transaction_kind="return",
    invoice_type="sale",
    is_return=True,
    class_path="features.transactions.documents.sales_return_tab.SalesReturnTab",
    opener="open_return_document('sale')",
    list_route="returns",
    api_resource="/api/returns/sales",
    gateway="sales_return_gateway",
    service_name="sales_return_service",
)

PURCHASE_RETURN_ROUTE = TransactionShellRoute(
    document_type="purchase_return",
    transaction_kind="return",
    invoice_type="purchase",
    is_return=True,
    class_path="features.transactions.documents.purchase_return_tab.PurchaseReturnTab",
    opener="open_return_document('purchase')",
    list_route="purchase_returns",
    api_resource="/api/returns/purchase",
    gateway="purchase_return_gateway",
    service_name="purchase_return_service",
)

TRANSACTION_SHELL_ROUTES: tuple[TransactionShellRoute, ...] = (
    SALES_INVOICE_ROUTE,
    PURCHASE_INVOICE_ROUTE,
    SALES_RETURN_ROUTE,
    PURCHASE_RETURN_ROUTE,
)

TRANSACTION_DOCUMENT_TYPES: tuple[str, ...] = tuple(r.document_type for r in TRANSACTION_SHELL_ROUTES)

_ROUTE_BY_DOCUMENT_TYPE = {r.document_type: r for r in TRANSACTION_SHELL_ROUTES}
_INVOICE_ROUTE_BY_TYPE = {r.invoice_type: r for r in TRANSACTION_SHELL_ROUTES if not r.is_return}
_RETURN_ROUTE_BY_TYPE = {r.invoice_type: r for r in TRANSACTION_SHELL_ROUTES if r.is_return}


def normalize_invoice_type(invoice_type: str | None) -> str:
    value = str(invoice_type or "sale").strip().lower()
    return "purchase" if value in {"purchase", "purchases", "buy", "supplier"} else "sale"


def normalize_return_type(return_type: str | None) -> str:
    value = str(return_type or "sale").strip().lower()
    return "purchase" if value in {"purchase", "purchases", "buy", "supplier"} else "sale"


def route_for_document_type(document_type: str) -> TransactionShellRoute | None:
    return _ROUTE_BY_DOCUMENT_TYPE.get(str(document_type or ""))


def route_for_invoice_type(invoice_type: str | None) -> TransactionShellRoute:
    return _INVOICE_ROUTE_BY_TYPE[normalize_invoice_type(invoice_type)]


def route_for_return_type(return_type: str | None) -> TransactionShellRoute:
    return _RETURN_ROUTE_BY_TYPE[normalize_return_type(return_type)]


def document_type_for_invoice(invoice_type: str | None) -> str:
    return route_for_invoice_type(invoice_type).document_type


def document_type_for_return(return_type: str | None) -> str:
    return route_for_return_type(return_type).document_type


def descriptor_for_invoice(invoice_type: str | None) -> DocumentDescriptor | None:
    return descriptor_for(document_type_for_invoice(invoice_type))


def descriptor_for_return(return_type: str | None) -> DocumentDescriptor | None:
    return descriptor_for(document_type_for_return(return_type))


def transaction_descriptors() -> tuple[DocumentDescriptor, ...]:
    result: list[DocumentDescriptor] = []
    for route in TRANSACTION_SHELL_ROUTES:
        descriptor = descriptor_for(route.document_type)
        if descriptor is not None:
            result.append(descriptor)
    return tuple(result)


def validate_transaction_shell_routes(routes: Iterable[TransactionShellRoute] | None = None) -> dict[str, list[str]]:
    """Return transaction route contract warnings, grouped by document type."""

    warnings: dict[str, list[str]] = {}
    seen: set[str] = set()
    for route in routes or TRANSACTION_SHELL_ROUTES:
        row: list[str] = []
        if route.document_type in seen:
            row.append("duplicate document_type")
        seen.add(route.document_type)
        descriptor = descriptor_for(route.document_type)
        if descriptor is None:
            row.append("missing DocumentDescriptor")
        else:
            if descriptor.shell_family != SHELL_TRANSACTION:
                row.append(f"descriptor shell_family is {descriptor.shell_family!r}, expected {SHELL_TRANSACTION!r}")
            if descriptor.document_class != route.class_path:
                row.append(f"descriptor document_class mismatch: {descriptor.document_class!r}")
            if descriptor.api_resource != route.api_resource:
                row.append(f"descriptor api_resource mismatch: {descriptor.api_resource!r}")
            if descriptor.gateway != route.gateway:
                row.append(f"descriptor gateway mismatch: {descriptor.gateway!r}")
            if descriptor.currency_policy != CURRENCY_DOCUMENT:
                row.append(f"descriptor currency_policy is {descriptor.currency_policy!r}, expected {CURRENCY_DOCUMENT!r}")
            if descriptor.branch_policy != BRANCH_REQUIRED:
                row.append(f"descriptor branch_policy is {descriptor.branch_policy!r}, expected {BRANCH_REQUIRED!r}")
            if descriptor.network_mode not in {NETWORK_REMOTE_AVAILABLE, NETWORK_REMOTE_REQUIRED}:
                row.append(f"descriptor network_mode is {descriptor.network_mode!r}, expected remote mode")
            if not descriptor.capabilities.print:
                row.append("print capability is not declared")
            if not descriptor.capabilities.export:
                row.append("export capability is not declared")
            if not descriptor.capabilities.grid_layout:
                row.append("grid_layout capability is not declared")
            if not descriptor.permissions.view:
                row.append("view permission is missing")
            if not descriptor.permissions.print:
                row.append("print permission is missing")
        if row:
            warnings[route.document_type] = row
    return warnings


__all__ = [
    "TransactionShellRoute",
    "TRANSACTION_SHELL_ROUTES",
    "TRANSACTION_DOCUMENT_TYPES",
    "normalize_invoice_type",
    "normalize_return_type",
    "route_for_document_type",
    "route_for_invoice_type",
    "route_for_return_type",
    "document_type_for_invoice",
    "document_type_for_return",
    "descriptor_for_invoice",
    "descriptor_for_return",
    "transaction_descriptors",
    "validate_transaction_shell_routes",
]
