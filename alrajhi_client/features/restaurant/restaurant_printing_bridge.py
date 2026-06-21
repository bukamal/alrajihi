# -*- coding: utf-8 -*-
from __future__ import annotations

"""Restaurant printing bridge (Phase 183).

The restaurant module must not build printable HTML in widgets.  This bridge
collects restaurant session/ticket payloads from RestaurantService and delegates
all rendering, language, company header, paper size, and PDF/print output to the
central PrintingService.
"""

from typing import Any, Dict, Iterable

from core.services.restaurant_operation_policy import restaurant_operation_policy
from core.services.restaurant_service import restaurant_service
from core.services.settings_service import settings_service
from printing.printing_service import printing_service
from features.restaurant.restaurant_settings_contract import restaurant_print_route
from features.restaurant.restaurant_unified_printing_contract import (
    attach_unified_print_contract,
    restaurant_print_document,
)


class RestaurantPrintingBridge:
    def __init__(self, service=None, printer=None):
        self.service = service or restaurant_service
        self.printer = printer or printing_service

    def _route(self, kind: str = "receipt") -> Dict[str, Any]:
        document = restaurant_print_document(kind)
        try:
            route = restaurant_print_route(document.route_key, settings_service.get_restaurant_settings())
        except Exception:
            route = {"document_type": document.document_type, "paper": document.default_paper, "printer": "", "auto_print": False}
        route = dict(route or {})
        route.setdefault("document_type", document.document_type)
        route.setdefault("paper", document.default_paper)
        route.setdefault("surface", "browser_html")
        return route

    def _paper(self, kind: str = "receipt") -> str:
        document = restaurant_print_document(kind)
        return str(self._route(document.route_key).get("paper") or document.default_paper)

    def _attach_route(self, payload: Dict[str, Any], kind: str) -> Dict[str, Any]:
        document = restaurant_print_document(kind)
        return attach_unified_print_contract(payload, document.route_key, self._route(document.route_key))

    def receipt_payload(self, session_id: int) -> Dict[str, Any]:
        session = self.service.get_session(int(session_id))
        balance = self.service.session_balance(int(session_id))
        split_bills = []
        try:
            split_bills = self.service.list_split_bills(int(session_id))
        except Exception:
            split_bills = []
        return self._attach_route({"session": session, "balance": balance, "split_bills": split_bills}, "receipt")

    def session_summary_payload(self, session_id: int) -> Dict[str, Any]:
        payload = self.receipt_payload(session_id)
        return self._attach_route(payload, "session_summary")

    def kitchen_ticket_payload(self, ticket_id: int) -> Dict[str, Any]:
        return self._attach_route(self.service.get_kitchen_ticket(int(ticket_id)), "kitchen")

    def receipt_preview(self, session_id: int, parent=None) -> bool:
        return self.receipt_print(session_id, parent)

    def receipt_print(self, session_id: int, parent=None) -> bool:
        restaurant_operation_policy.require(restaurant_operation_policy.OP_PRINT_RECEIPT)
        payload = self.receipt_payload(session_id)
        ok = self.printer.restaurant_receipt_print(payload, parent, paper=self._paper("receipt"))
        restaurant_operation_policy.log(restaurant_operation_policy.OP_PRINT_RECEIPT, allowed=bool(ok), context="restaurant_printing.receipt_print", values={"session_id": session_id, "route": self._route("receipt")})
        return bool(ok)

    def receipt_pdf(self, session_id: int, parent=None) -> bool:
        return self.receipt_print(session_id, parent)

    def session_summary_preview(self, session_id: int, parent=None) -> bool:
        return self.session_summary_print(session_id, parent)

    def session_summary_print(self, session_id: int, parent=None) -> bool:
        restaurant_operation_policy.require(restaurant_operation_policy.OP_PRINT_RECEIPT)
        payload = self.session_summary_payload(session_id)
        ok = self.printer.restaurant_session_summary_print(payload, parent, paper=self._paper("session_summary"))
        restaurant_operation_policy.log(restaurant_operation_policy.OP_PRINT_RECEIPT, allowed=bool(ok), context="restaurant_printing.session_summary_print", values={"session_id": session_id, "route": self._route("session_summary")})
        return bool(ok)

    def session_summary_pdf(self, session_id: int, parent=None) -> bool:
        return self.session_summary_print(session_id, parent)

    def kitchen_ticket_preview(self, ticket_id: int, parent=None) -> bool:
        return self.kitchen_ticket_print(ticket_id, parent)

    def kitchen_ticket_print(self, ticket_id: int, parent=None) -> bool:
        restaurant_operation_policy.require(restaurant_operation_policy.OP_PRINT_KITCHEN_TICKET)
        payload = self.kitchen_ticket_payload(ticket_id)
        ok = self.printer.restaurant_kitchen_ticket_print(payload, parent, paper=self._paper("kitchen"))
        if ok:
            try:
                self.service.queue_ticket_print(int(ticket_id), job_type="kot")
            except Exception:
                pass
        restaurant_operation_policy.log(restaurant_operation_policy.OP_PRINT_KITCHEN_TICKET, allowed=bool(ok), context="restaurant_printing.ticket_print", values={"ticket_id": ticket_id, "route": self._route("kitchen")})
        return bool(ok)

    def kitchen_tickets_print(self, tickets: Iterable[Dict[str, Any]], parent=None) -> int:
        printed = 0
        for ticket in tickets or []:
            ticket_id = ticket.get("id") if isinstance(ticket, dict) else None
            if not ticket_id:
                continue
            if self.kitchen_ticket_print(int(ticket_id), parent):
                printed += 1
        return printed


restaurant_printing_bridge = RestaurantPrintingBridge()
