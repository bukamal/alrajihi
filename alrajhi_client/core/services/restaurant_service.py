# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from gateways.restaurant_gateway import create_restaurant_gateway


class RestaurantService:
    """Touch-first restaurant workflow service.

    It keeps restaurant sessions separate from invoices until checkout. Closing a
    session can later be wired to InvoiceService without changing the table/KOT
    workflow.
    """

    def __init__(self):
        self.gateway = create_restaurant_gateway()

    def list_tables(self) -> list[dict[str, Any]]:
        return self.gateway.list_tables()

    def create_table(self, name: str, zone: str = "", seats: int = 4) -> dict[str, Any]:
        return self.gateway.upsert_table(name=name, zone=zone, seats=seats)

    def open_table(self, table_id: int, guests: int = 1, waiter_id: str | None = None, notes: str = "") -> dict[str, Any]:
        return self.gateway.open_table(table_id=table_id, guests=guests, waiter_id=waiter_id, notes=notes)

    def get_session(self, session_id: int) -> dict[str, Any]:
        return self.gateway.get_session(session_id)

    def add_line(self, session_id: int, item_name: str, item_id: int | None = None, quantity: Any = "1", unit_price: Any = "0", notes: str = "") -> dict[str, Any]:
        return self.gateway.add_order_line(session_id=session_id, item_name=item_name, item_id=item_id, quantity=quantity, unit_price=unit_price, notes=notes)

    def send_to_kitchen(self, session_id: int, notes: str = "") -> dict[str, Any]:
        return self.gateway.send_to_kitchen(session_id, notes=notes)

    def update_line_status(self, line_id: int, status: str) -> dict[str, Any]:
        return self.gateway.update_line_status(line_id=line_id, status=status)

    def mark_payment_pending(self, session_id: int) -> dict[str, Any]:
        return self.gateway.mark_payment_pending(session_id=session_id)

    def list_menu_items(self, search: str = "", category_id: int | None = None, limit: int = 48) -> list[dict[str, Any]]:
        return self.gateway.list_menu_items(search=search, category_id=category_id, limit=limit)

    def session_balance(self, session_id: int) -> dict[str, Any]:
        return self.gateway.session_balance(session_id=session_id)

    def record_payment(self, session_id: int, amount: Any, payment_method: str = "cash", notes: str = "") -> dict[str, Any]:
        return self.gateway.record_payment(session_id=session_id, amount=amount, payment_method=payment_method, notes=notes)

    def checkout_session(self, session_id: int, paid_amount: Any | None = None, payment_method: str = "cash") -> dict[str, Any]:
        return self.gateway.checkout_session(session_id=session_id, paid_amount=paid_amount, payment_method=payment_method)

    def list_kitchen_tickets(self, status: str = "sent", limit: int = 50, station_id: int | None = None) -> list[dict[str, Any]]:
        return self.gateway.list_kitchen_tickets(status=status, limit=limit, station_id=station_id)

    def get_kitchen_ticket(self, ticket_id: int) -> dict[str, Any]:
        return self.gateway.get_kitchen_ticket(ticket_id=ticket_id)

    def update_kitchen_ticket_status(self, ticket_id: int, status: str) -> dict[str, Any]:
        return self.gateway.update_kitchen_ticket_status(ticket_id=ticket_id, status=status)

    def reserve_table(self, table_id: int, customer_name: str = "", phone: str = "", reserved_at: str = "", guests: int = 1, notes: str = "") -> dict[str, Any]:
        return self.gateway.reserve_table(table_id=table_id, customer_name=customer_name, phone=phone, reserved_at=reserved_at, guests=guests, notes=notes)

    def cancel_reservation(self, reservation_id: int) -> dict[str, Any]:
        return self.gateway.cancel_reservation(reservation_id=reservation_id)

    def transfer_session(self, session_id: int, target_table_id: int) -> dict[str, Any]:
        return self.gateway.transfer_session(session_id=session_id, target_table_id=target_table_id)

    def merge_sessions(self, source_session_id: int, target_session_id: int) -> dict[str, Any]:
        return self.gateway.merge_sessions(source_session_id=source_session_id, target_session_id=target_session_id)

    def split_lines_to_table(self, session_id: int, line_ids: list[int], target_table_id: int, guests: int = 1, notes: str = "") -> dict[str, Any]:
        return self.gateway.split_lines_to_table(session_id=session_id, line_ids=line_ids, target_table_id=target_table_id, guests=guests, notes=notes)

    def close_session(self, session_id: int, invoice_id: int | None = None) -> dict[str, Any]:
        return self.gateway.close_session(session_id=session_id, invoice_id=invoice_id)


    def assign_waiter(self, session_id: int, waiter_id: str, notes: str = "") -> dict[str, Any]:
        return self.gateway.assign_waiter(session_id=session_id, waiter_id=waiter_id, notes=notes)

    def call_waiter(self, session_id: int, notes: str = "") -> dict[str, Any]:
        return self.gateway.call_waiter(session_id=session_id, notes=notes)

    def resolve_waiter_call(self, session_id: int, notes: str = "") -> dict[str, Any]:
        return self.gateway.resolve_waiter_call(session_id=session_id, notes=notes)

    def waiter_session_summary(self, session_id: int) -> dict[str, Any]:
        return self.gateway.waiter_session_summary(session_id=session_id)

    def list_kitchen_stations(self, include_inactive: bool = False) -> list[dict[str, Any]]:
        return self.gateway.list_kitchen_stations(include_inactive=include_inactive)

    def upsert_kitchen_station(self, name: str, code: str = "", sort_order: int = 0, station_id: int | None = None, is_active: bool = True) -> dict[str, Any]:
        return self.gateway.upsert_kitchen_station(name=name, code=code, sort_order=sort_order, station_id=station_id, is_active=is_active)

    def assign_menu_item_station(self, item_id: int, station_id: int) -> dict[str, Any]:
        return self.gateway.assign_menu_item_station(item_id=item_id, station_id=station_id)


    def restaurant_analytics(self, start_date: str = "", end_date: str = "") -> dict[str, Any]:
        return self.gateway.restaurant_analytics(start_date=start_date, end_date=end_date)


restaurant_service = RestaurantService()
