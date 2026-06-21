# -*- coding: utf-8 -*-
from __future__ import annotations

"""Restaurant unified printing contract (Phase 305).

Restaurant documents are operationally different from normal invoices, but they
must still pass through the same Browser HTML printing surface.  This module is a
small explicit contract consumed by the restaurant bridge and the release gate so
future restaurant work cannot quietly reintroduce widget-built HTML, legacy Qt printer paths, or divergent PDF/direct-print flows.
"""

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Sequence

@dataclass(frozen=True)
class RestaurantPrintDocument:
    key: str
    document_type: str
    template_method: str
    printing_service_method: str
    bridge_method: str
    route_key: str
    default_paper: str
    permission: str


RESTAURANT_PRINT_SURFACE = "browser_html"

RESTAURANT_PRINT_DOCUMENTS: Sequence[RestaurantPrintDocument] = (
    RestaurantPrintDocument(
        key="receipt",
        document_type="restaurant_receipt",
        template_method="restaurant_receipt_html",
        printing_service_method="restaurant_receipt_print",
        bridge_method="receipt_print",
        route_key="receipt",
        default_paper="80mm",
        permission="print_receipt",
    ),
    RestaurantPrintDocument(
        key="kitchen",
        document_type="restaurant_kitchen",
        template_method="restaurant_kitchen_ticket_html",
        printing_service_method="restaurant_kitchen_ticket_print",
        bridge_method="kitchen_ticket_print",
        route_key="kitchen",
        default_paper="80mm",
        permission="print_kitchen_ticket",
    ),
    RestaurantPrintDocument(
        key="session_summary",
        document_type="restaurant_session_summary",
        template_method="restaurant_session_summary_html",
        printing_service_method="restaurant_session_summary_print",
        bridge_method="session_summary_print",
        route_key="session_summary",
        default_paper="80mm",
        permission="print_receipt",
    ),
)

_PRINT_KIND_ALIASES = {
    "": "receipt",
    "customer": "receipt",
    "customer_receipt": "receipt",
    "receipt": "receipt",
    "restaurant_receipt": "receipt",
    "kot": "kitchen",
    "kitchen": "kitchen",
    "kitchen_ticket": "kitchen",
    "restaurant_kitchen": "kitchen",
    "restaurant_kitchen_ticket": "kitchen",
    "barista": "kitchen",
    "barista_ticket": "kitchen",
    "cafe_barista": "kitchen",
    "cafe_preparation": "kitchen",
    "cafe_preparation_ticket": "kitchen",
    "cafe": "receipt",
    "cafe_receipt": "receipt",
    "cafe_customer_receipt": "receipt",
    "summary": "session_summary",
    "session": "session_summary",
    "cafe_session": "session_summary",
    "cafe_session_summary": "session_summary",
    "session_summary": "session_summary",
    "restaurant_session_summary": "session_summary",
}


def normalize_restaurant_print_kind(kind: Any) -> str:
    text = str(kind or "receipt").strip().lower().replace("-", "_").replace(" ", "_")
    return _PRINT_KIND_ALIASES.get(text, "receipt")


def restaurant_print_document(kind: Any) -> RestaurantPrintDocument:
    key = normalize_restaurant_print_kind(kind)
    for document in RESTAURANT_PRINT_DOCUMENTS:
        if document.key == key:
            return document
    return RESTAURANT_PRINT_DOCUMENTS[0]


def restaurant_print_document_keys() -> tuple[str, ...]:
    return tuple(document.key for document in RESTAURANT_PRINT_DOCUMENTS)


def restaurant_unified_print_contract_snapshot() -> Dict[str, Dict[str, str]]:
    return {
        document.key: {
            "document_type": document.document_type,
            "template_method": document.template_method,
            "printing_service_method": document.printing_service_method,
            "bridge_method": document.bridge_method,
            "route_key": document.route_key,
            "surface": RESTAURANT_PRINT_SURFACE,
            "default_paper": document.default_paper,
            "permission": document.permission,
        }
        for document in RESTAURANT_PRINT_DOCUMENTS
    }


def attach_unified_print_contract(payload: Mapping[str, Any] | None, kind: Any, route: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Attach immutable restaurant print metadata to a payload.

    The metadata is deliberately explicit.  Templates and tests can identify the
    active route and document type without guessing from widget state, while the
    actual rendering remains owned by ``printing.printing_service``.
    """
    document = restaurant_print_document(kind)
    data = dict(payload or {})
    route_data = dict(route or {})
    route_data.setdefault("document_type", document.document_type)
    route_data.setdefault("paper", document.default_paper)
    route_data.setdefault("surface", RESTAURANT_PRINT_SURFACE)
    data.update({
        "print_kind": document.key,
        "print_document_type": document.document_type,
        "print_route": route_data,
        "print_surface": RESTAURANT_PRINT_SURFACE,
        "unified_printing": True,
    })
    return data


def payload_uses_unified_restaurant_printing(payload: Mapping[str, Any] | None, kind: Any) -> bool:
    document = restaurant_print_document(kind)
    data = dict(payload or {})
    route = dict(data.get("print_route") or {})
    return (
        data.get("unified_printing") is True
        and data.get("print_surface") == RESTAURANT_PRINT_SURFACE
        and data.get("print_document_type") == document.document_type
        and route.get("document_type") == document.document_type
        and route.get("surface") == RESTAURANT_PRINT_SURFACE
    )
