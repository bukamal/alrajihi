# -*- coding: utf-8 -*-
"""Phase 240 guard: invoice/return browser output must never expose raw dict repr.

This guard validates both the real template path and the emergency frozen-build
fallback path.  Users reported browser pages showing ``{'id': ...}`` and
``Decimal('...')`` for invoice/return printing; that is not acceptable even if
PyInstaller fails to load the full print template module.
"""
from __future__ import annotations

import importlib
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _bad_raw_repr(html: str) -> list[str]:
    markers = ["'id':", '"id":', "Decimal(", "<pre", "Invoice Html", "Return Html", "قالب طباعة احتياطي"]
    return [m for m in markers if m in html]


def _invoice_payload(kind: str = "sale") -> dict:
    return {
        "id": 6,
        "type": kind,
        "reference": "SAL-2026-0002" if kind == "sale" else "PUR-2026-0003",
        "date": "2026-06-20",
        "party_name": "عميل تجريبي" if kind == "sale" else "مورد تجريبي",
        "customer_name": "عميل تجريبي" if kind == "sale" else "",
        "supplier_name": "مورد تجريبي" if kind == "purchase" else "",
        "warehouse_name": "المستودع الرئيسي",
        "payment_method": "نقدي",
        "subtotal": Decimal("250000.00"),
        "total": Decimal("250000.00"),
        "paid": Decimal("0"),
        "paid_amount": Decimal("0"),
        "remaining": Decimal("250000.00"),
        "currency": "SYP",
        "lines": [
            {"item_name": "حليب", "qty": Decimal("1"), "quantity": Decimal("1"), "unit": "علبة", "unit_price": Decimal("250000.00"), "line_total": Decimal("250000.00"), "total": Decimal("250000.00")},
        ],
    }


def _return_payload(kind: str = "sale_return") -> dict:
    payload = _invoice_payload("sale" if kind == "sale_return" else "purchase")
    payload.update({
        "return_type": kind,
        "reference": "SR-2026-0002" if kind == "sale_return" else "PR-2026-0002",
        "return_number": "SR-2026-0002" if kind == "sale_return" else "PR-2026-0002",
        "original_invoice": "SAL-2026-0002 - 2026-06-20" if kind == "sale_return" else "PUR-2026-0003 - 2026-06-20",
        "refund_amount": Decimal("0"),
    })
    return payload


def main() -> None:
    sys.path.insert(0, str(CLIENT))
    loader = importlib.import_module("printing._template_loader")

    # Real source template path.
    for name, payload in (
        ("invoice_html", _invoice_payload("sale")),
        ("invoice_html", _invoice_payload("purchase")),
        ("return_html", _return_payload("sale_return")),
        ("return_html", _return_payload("purchase_return")),
    ):
        html = loader.require_template(name)(payload)
        bad = _bad_raw_repr(html)
        assert_true(not bad, f"{name} real template leaks raw payload markers: {bad}")
        assert_true("<table" in html and "حليب" in html, f"{name} real template must render a document table")

    # Emergency frozen fallback path.  This explicitly validates the path used if
    # PyInstaller misses print_templates at runtime.
    for name, payload in (
        ("invoice_html", _invoice_payload("sale")),
        ("invoice_html", _invoice_payload("purchase")),
        ("return_html", _return_payload("sale_return")),
        ("return_html", _return_payload("purchase_return")),
    ):
        html = loader._fallback_template(name)(payload)  # noqa: SLF001 - deliberate guard on fallback contract.
        bad = _bad_raw_repr(html)
        assert_true(not bad, f"{name} fallback leaks raw payload markers: {bad}")
        assert_true("<table" in html and "حليب" in html, f"{name} fallback must render a document table")
        assert_true("فاتورة" in html or "مرتجع" in html, f"{name} fallback must use document title, not technical template title")

    print("Phase 240 invoice/return browser HTML guard passed")


if __name__ == "__main__":
    main()
