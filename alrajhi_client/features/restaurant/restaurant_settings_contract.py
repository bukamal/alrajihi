# -*- coding: utf-8 -*-
from __future__ import annotations

"""Restaurant settings and print-routing contract (Phase 294).

Restaurant UI, printing bridge, and service-level workflows should consume one
normalized contract instead of reading scattered settings keys.  The visible
print pipeline is still Browser HTML, but restaurant documents have different
routing metadata: customer receipt, kitchen ticket, and session summary.
"""

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Mapping

_VALID_PAPERS = {"58mm", "80mm", "thermal58", "thermal80", "a4"}
_VALID_PAYMENT_METHODS = {"cash", "card", "credit", "bank_transfer", "bank", "mixed"}
_VALID_CONSUMPTION_POINTS = {"checkout", "served"}


def _bool(value: Any, default: bool = False) -> bool:
    if value in (None, ""):
        return bool(default)
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on", "نعم"}


def _decimal_text(value: Any, default: str = "0") -> str:
    try:
        dec = Decimal(str(value if value not in (None, "") else default))
    except (InvalidOperation, TypeError, ValueError):
        dec = Decimal(default)
    if dec < 0:
        dec = Decimal("0")
    return format(dec.normalize(), "f").rstrip("0").rstrip(".") or "0"


def normalize_restaurant_paper(value: Any, default: str = "80mm") -> str:
    paper = str(value or default or "80mm").strip().lower().replace("_", "")
    if paper in {"80", "80mm", "thermal80", "thermal-80", "thermal 80"}:
        return "80mm"
    if paper in {"58", "58mm", "thermal58", "thermal-58", "thermal 58"}:
        return "58mm"
    if paper == "a4":
        return "a4"
    return default if str(default).lower() in _VALID_PAPERS else "80mm"


def _printer(value: Any) -> str:
    # Empty means project default Browser HTML route.  Physical printer names are
    # retained as metadata for deployments that map HTML output externally.
    return str(value or "").strip()


def normalize_restaurant_settings(raw: Mapping[str, Any] | None) -> Dict[str, Any]:
    raw = dict(raw or {})
    operations = dict(raw.get("operations") or {})
    printing = dict(raw.get("printing") or {})

    payment = str(raw.get("default_payment_method") or "cash").strip().lower()
    if payment not in _VALID_PAYMENT_METHODS:
        payment = "cash"
    consume_inventory_on = str(raw.get("consume_inventory_on") or "checkout").strip().lower()
    if consume_inventory_on not in _VALID_CONSUMPTION_POINTS:
        consume_inventory_on = "checkout"

    receipt_paper = normalize_restaurant_paper(raw.get("receipt_paper"), "80mm")
    kitchen_paper = normalize_restaurant_paper(raw.get("kitchen_ticket_paper"), receipt_paper)
    summary_paper = normalize_restaurant_paper(raw.get("session_summary_paper"), receipt_paper)

    normalized = dict(raw)
    normalized.update({
        "enabled": _bool(raw.get("enabled"), True),
        "default_payment_method": payment,
        "service_charge_percent": _decimal_text(raw.get("service_charge_percent"), "0"),
        "default_tax_percent": _decimal_text(raw.get("default_tax_percent"), "0"),
        "consume_inventory_on": consume_inventory_on,
        "receipt_paper": receipt_paper,
        "kitchen_ticket_paper": kitchen_paper,
        "session_summary_paper": summary_paper,
    })

    normalized["operations"] = {
        **operations,
        "auto_print_kitchen_ticket": _bool(operations.get("auto_print_kitchen_ticket"), False),
        "auto_print_receipt_after_checkout": _bool(operations.get("auto_print_receipt_after_checkout"), False),
        "auto_print_session_summary_after_checkout": _bool(operations.get("auto_print_session_summary_after_checkout"), False),
    }
    normalized["printing"] = printing
    normalized["printer_routing"] = {
        "receipt": {
            "document_type": "restaurant_receipt",
            "paper": receipt_paper,
            "printer": _printer(printing.get("restaurant_receipt_printer") or raw.get("receipt_printer")),
            "auto_print": normalized["operations"]["auto_print_receipt_after_checkout"],
        },
        "kitchen": {
            "document_type": "restaurant_kitchen",
            "paper": kitchen_paper,
            "printer": _printer(printing.get("restaurant_kitchen_printer") or raw.get("kitchen_printer")),
            "auto_print": normalized["operations"]["auto_print_kitchen_ticket"],
        },
        "session_summary": {
            "document_type": "restaurant_session_summary",
            "paper": summary_paper,
            "printer": _printer(printing.get("restaurant_session_summary_printer") or raw.get("session_summary_printer")),
            "auto_print": normalized["operations"]["auto_print_session_summary_after_checkout"],
        },
    }
    return normalized


def restaurant_print_route(kind: str, settings: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    normalized = normalize_restaurant_settings(settings)
    key = "session_summary" if str(kind or "").lower() in {"summary", "session", "session_summary"} else str(kind or "receipt").lower()
    if key == "kitchen_ticket":
        key = "kitchen"
    return dict((normalized.get("printer_routing") or {}).get(key) or normalized["printer_routing"]["receipt"])


def restaurant_should_auto_print(kind: str, settings: Mapping[str, Any] | None = None) -> bool:
    return bool(restaurant_print_route(kind, settings).get("auto_print"))
