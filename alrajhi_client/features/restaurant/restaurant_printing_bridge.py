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


class RestaurantPrintingBridge:
    def __init__(self, service=None, printer=None):
        self.service = service or restaurant_service
        self.printer = printer or printing_service

    def _paper(self, kind: str = "receipt") -> str:
        try:
            settings = settings_service.get_restaurant_settings()
            if kind == "kitchen":
                return str(settings.get("kitchen_ticket_paper") or settings.get("receipt_paper") or "thermal")
            return str(settings.get("receipt_paper") or "thermal")
        except Exception:
            return "thermal"

    def receipt_payload(self, session_id: int) -> Dict[str, Any]:
        session = self.service.get_session(int(session_id))
        balance = self.service.session_balance(int(session_id))
        return {"session": session, "balance": balance}

    def kitchen_ticket_payload(self, ticket_id: int) -> Dict[str, Any]:
        return self.service.get_kitchen_ticket(int(ticket_id))

    def receipt_preview(self, session_id: int, parent=None) -> bool:
        return self.receipt_print(session_id, parent)

    def receipt_print(self, session_id: int, parent=None) -> bool:
        restaurant_operation_policy.require(restaurant_operation_policy.OP_PRINT_RECEIPT)
        payload = self.receipt_payload(session_id)
        ok = self.printer.restaurant_receipt_print(payload, parent, paper=self._paper("receipt"))
        restaurant_operation_policy.log(restaurant_operation_policy.OP_PRINT_RECEIPT, allowed=bool(ok), context="restaurant_printing.receipt_print", values={"session_id": session_id})
        return bool(ok)

    def receipt_pdf(self, session_id: int, parent=None) -> bool:
        return self.receipt_print(session_id, parent)

    def kitchen_ticket_preview(self, ticket_id: int, parent=None) -> bool:
        return self.kitchen_ticket_print(ticket_id, parent)

    def kitchen_ticket_print(self, ticket_id: int, parent=None) -> bool:
        restaurant_operation_policy.require(restaurant_operation_policy.OP_PRINT_KITCHEN_TICKET)
        payload = self.kitchen_ticket_payload(ticket_id)
        ok = self.printer.restaurant_kitchen_ticket_print(payload, parent, paper=self._paper("kitchen"))
        restaurant_operation_policy.log(restaurant_operation_policy.OP_PRINT_KITCHEN_TICKET, allowed=bool(ok), context="restaurant_printing.ticket_print", values={"ticket_id": ticket_id})
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
