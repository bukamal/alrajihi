# -*- coding: utf-8 -*-
"""Phase383 menu/action-bar inline creation routing contract.

The shell may expose creation commands from the main menu, quick actions, and
shared action bar.  Management-style entities must be created inside their owning
workspace inline editor instead of opening secondary tabs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class InlineCreationRoute:
    page_id: str
    method_name: str
    args: Tuple[object, ...] = ()


MENU_INLINE_CALLBACKS: dict[str, InlineCreationRoute] = {
    "open_quick_customer": InlineCreationRoute("customers", "add_customer"),
    "open_quick_supplier": InlineCreationRoute("suppliers", "add_supplier"),
    "open_category_document": InlineCreationRoute("categories", "add_category"),
    "open_receipt_voucher": InlineCreationRoute("vouchers", "open_voucher_inline", ("receipt", None)),
    "open_payment_voucher": InlineCreationRoute("vouchers", "open_voucher_inline", ("payment", None)),
    "open_expense_voucher": InlineCreationRoute("vouchers", "open_voucher_inline", ("expense", None)),
    "open_new_warehouse": InlineCreationRoute("warehouses", "open_warehouse_inline", (None,)),
    "open_inventory_transfer_document": InlineCreationRoute("warehouses", "add_transfer"),
    "open_new_branch": InlineCreationRoute("branches", "open_branch_inline", (None,)),
    "open_new_cashbox": InlineCreationRoute("cashboxes", "open_cashbox_inline", (None,)),
    "open_new_bank_account": InlineCreationRoute("cashboxes", "open_bank_inline", (None,)),
    "open_new_user": InlineCreationRoute("users", "open_user_inline", (None,)),
}


ACTION_BAR_NEW_ROUTES: dict[str, InlineCreationRoute] = {
    "customers": InlineCreationRoute("customers", "add_customer"),
    "suppliers": InlineCreationRoute("suppliers", "add_supplier"),
    "categories": InlineCreationRoute("categories", "add_category"),
    "vouchers": InlineCreationRoute("vouchers", "add_voucher", ("receipt",)),
    "warehouses": InlineCreationRoute("warehouses", "add_warehouse"),
    "branches": InlineCreationRoute("branches", "add_branch"),
    "cashboxes": InlineCreationRoute("cashboxes", "add_cashbox"),
    "users": InlineCreationRoute("users", "add_user"),
}


TABULAR_DOCUMENT_NEW_TARGETS: dict[str, tuple[str, tuple[object, ...]]] = {
    "sales_invoices": ("open_quick_invoice", ("sale",)),
    "purchase_invoices": ("open_quick_invoice", ("purchase",)),
    "returns": ("open_return_document", ("sale",)),
    "purchase_returns": ("open_return_document", ("purchase",)),
    "items": ("open_item_document", ()),
    "manufacturing": ("open_bom_document", ()),
    "dashboard": ("open_quick_invoice", ("sale",)),
}


INLINE_MENU_CALLBACK_KEYS = frozenset(MENU_INLINE_CALLBACKS)
INLINE_ACTION_BAR_PAGE_IDS = frozenset(ACTION_BAR_NEW_ROUTES)
