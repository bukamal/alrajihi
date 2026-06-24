# -*- coding: utf-8 -*-
"""Phase383 main menu/action-bar inline routing contract."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

FILES = {
    "main_window": "alrajhi_client/views/main_window.py",
    "manifest": "alrajhi_client/workspace/registry/ui_manifest.py",
    "policy": "alrajhi_client/workspace/actions/inline_menu_action_policy.py",
}

REQUIRED_MARKERS = {
    "main_window": (
        "self.action_bar.bind('new', self.new_current_workspace)",
        "def new_current_workspace(self):",
        "ACTION_BAR_NEW_ROUTES.get",
        "TABULAR_DOCUMENT_NEW_TARGETS.get",
        "open_expense_voucher",
        "open_new_warehouse",
        "open_new_branch",
        "open_new_cashbox",
        "open_new_bank_account",
        "open_new_user",
        "_open_page_inline_action(route.page_id, route.method_name, *route.args)",
    ),
    "manifest": (
        'callback_key="open_new_warehouse"',
        'callback_key="open_inventory_transfer_document"',
        'callback_key="open_receipt_voucher"',
        'callback_key="open_payment_voucher"',
        'callback_key="open_expense_voucher"',
        'callback_key="open_new_cashbox"',
        'callback_key="open_new_bank_account"',
        'callback_key="open_new_branch"',
        'callback_key="open_new_user"',
        'page_id="branches"',
    ),
    "policy": (
        "MENU_INLINE_CALLBACKS",
        "ACTION_BAR_NEW_ROUTES",
        "TABULAR_DOCUMENT_NEW_TARGETS",
        '"open_quick_customer": InlineCreationRoute("customers", "add_customer")',
        '"open_quick_supplier": InlineCreationRoute("suppliers", "add_supplier")',
        '"open_expense_voucher": InlineCreationRoute("vouchers", "open_voucher_inline", ("expense", None))',
        '"cashboxes": InlineCreationRoute("cashboxes", "add_cashbox")',
        '"users": InlineCreationRoute("users", "add_user")',
    ),
}

FORBIDDEN_MARKERS = {
    "main_window": (
        "self.action_bar.bind('new', lambda: self.open_quick_invoice('sale'))",
    ),
}

INLINE_MENU_EXPECTATIONS = {
    "open_quick_customer": ("customers", "add_customer"),
    "open_quick_supplier": ("suppliers", "add_supplier"),
    "open_category_document": ("categories", "add_category"),
    "open_receipt_voucher": ("vouchers", "open_voucher_inline"),
    "open_payment_voucher": ("vouchers", "open_voucher_inline"),
    "open_expense_voucher": ("vouchers", "open_voucher_inline"),
    "open_new_warehouse": ("warehouses", "open_warehouse_inline"),
    "open_inventory_transfer_document": ("warehouses", "add_transfer"),
    "open_new_branch": ("branches", "open_branch_inline"),
    "open_new_cashbox": ("cashboxes", "open_cashbox_inline"),
    "open_new_bank_account": ("cashboxes", "open_bank_inline"),
    "open_new_user": ("users", "open_user_inline"),
}

ACTION_BAR_INLINE_PAGES = {
    "customers",
    "suppliers",
    "categories",
    "vouchers",
    "warehouses",
    "branches",
    "cashboxes",
    "users",
}


@dataclass(frozen=True)
class MenuInlineActionCheck:
    key: str
    category: str
    target: str
    status: str
    detail: str
    phase: int = 383

    def as_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "category": self.category,
            "target": self.target,
            "status": self.status,
            "detail": self.detail,
            "phase": self.phase,
        }


def _read(root: Path, rel: str) -> str:
    try:
        return (root / rel).read_text(encoding="utf-8")
    except Exception:
        return ""


def menu_inline_action_matrix(root: Path | None = None) -> list[dict[str, object]]:
    base = root or ROOT
    rows: list[MenuInlineActionCheck] = []
    for key, rel in FILES.items():
        path = base / rel
        text = _read(base, rel)
        rows.append(MenuInlineActionCheck("file_exists", "source", key, "pass" if path.exists() else "fail", rel))
        for marker in REQUIRED_MARKERS.get(key, ()):  # type: ignore[arg-type]
            rows.append(MenuInlineActionCheck(f"requires::{marker[:54]}", "marker", key, "pass" if marker in text else "fail", marker))
        for marker in FORBIDDEN_MARKERS.get(key, ()):  # type: ignore[arg-type]
            rows.append(MenuInlineActionCheck(f"forbids::{marker[:54]}", "regression", key, "pass" if marker not in text else "fail", marker))
    try:
        from workspace.actions.inline_menu_action_policy import ACTION_BAR_NEW_ROUTES, MENU_INLINE_CALLBACKS
        for callback, (page_id, method_name) in INLINE_MENU_EXPECTATIONS.items():
            route = MENU_INLINE_CALLBACKS.get(callback)
            rows.append(MenuInlineActionCheck(
                f"menu_route::{callback}",
                "runtime_contract",
                callback,
                "pass" if route is not None and route.page_id == page_id and route.method_name == method_name else "fail",
                f"{page_id}.{method_name}",
            ))
        for page_id in sorted(ACTION_BAR_INLINE_PAGES):
            rows.append(MenuInlineActionCheck(
                f"action_bar_new::{page_id}",
                "runtime_contract",
                page_id,
                "pass" if page_id in ACTION_BAR_NEW_ROUTES else "fail",
                "New delegates to inline workspace action",
            ))
    except Exception as exc:
        rows.append(MenuInlineActionCheck("policy_import", "runtime_contract", "policy", "fail", str(exc)))
    return [row.as_dict() for row in rows]


def menu_inline_action_summary(root: Path | None = None) -> dict[str, object]:
    rows = menu_inline_action_matrix(root)
    issues = [row for row in rows if row.get("status") != "pass"]
    return {"phase": 383, "checks": len(rows), "issues": len(issues), "ready": not issues}
