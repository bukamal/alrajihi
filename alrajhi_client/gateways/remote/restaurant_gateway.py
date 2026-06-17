# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from gateways.restaurant_gateway import RestaurantGateway


class RemoteRestaurantGateway(RestaurantGateway):
    def __init__(self, client):
        self.client = client

    def list_tables(self) -> list[dict[str, Any]]:
        return self.client._request("GET", "/api/restaurant/tables") or []

    def upsert_table(self, name: str, zone: str = "", seats: int = 4, table_id: int | None = None) -> dict[str, Any]:
        return self.client._request("POST", "/api/restaurant/tables", {"id": table_id, "name": name, "zone": zone, "seats": seats}) or {}

    def open_table(self, table_id: int, guests: int = 1, waiter_id: str | None = None, notes: str = "") -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/tables/{int(table_id)}/open", {"guests": guests, "waiter_id": waiter_id, "notes": notes}) or {}

    def get_session(self, session_id: int) -> dict[str, Any]:
        return self.client._request("GET", f"/api/restaurant/sessions/{int(session_id)}") or {}

    def add_order_line(self, session_id: int, item_name: str, item_id: int | None = None, quantity: Any = "1", unit_price: Any = "0", notes: str = "") -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/sessions/{int(session_id)}/lines", {"item_id": item_id, "item_name": item_name, "quantity": quantity, "unit_price": unit_price, "notes": notes}) or {}

    def send_to_kitchen(self, session_id: int, notes: str = "") -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/sessions/{int(session_id)}/send_to_kitchen", {"notes": notes}) or {}

    def update_line_status(self, line_id: int, status: str) -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/lines/{int(line_id)}/status", {"status": status}) or {}

    def mark_payment_pending(self, session_id: int) -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/sessions/{int(session_id)}/payment_pending", {}) or {}

    def list_menu_items(self, search: str = "", category_id: int | None = None, limit: int = 48) -> list[dict[str, Any]]:
        params = {"search": search or "", "limit": int(limit or 48)}
        if category_id is not None:
            params["category_id"] = int(category_id)
        return self.client._request("GET", "/api/restaurant/menu_items", params) or []

    def session_balance(self, session_id: int) -> dict[str, Any]:
        return self.client._request("GET", f"/api/restaurant/sessions/{int(session_id)}/balance") or {}

    def record_payment(self, session_id: int, amount: Any, payment_method: str = "cash", notes: str = "") -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/sessions/{int(session_id)}/payments", {"amount": amount, "payment_method": payment_method, "notes": notes}) or {}

    def checkout_session(self, session_id: int, paid_amount: Any | None = None, payment_method: str = "cash") -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/sessions/{int(session_id)}/checkout", {"paid_amount": paid_amount, "payment_method": payment_method}) or {}


    def list_kitchen_tickets(self, status: str = "sent", limit: int = 50, station_id: int | None = None) -> list[dict[str, Any]]:
        params = {"status": status or "sent", "limit": int(limit or 50)}
        if station_id is not None:
            params["station_id"] = int(station_id)
        return self.client._request("GET", "/api/restaurant/kitchen/tickets", params) or []

    def get_kitchen_ticket(self, ticket_id: int) -> dict[str, Any]:
        return self.client._request("GET", f"/api/restaurant/kitchen/tickets/{int(ticket_id)}") or {}

    def update_kitchen_ticket_status(self, ticket_id: int, status: str) -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/kitchen/tickets/{int(ticket_id)}/status", {"status": status}) or {}

    def reserve_table(self, table_id: int, customer_name: str = "", phone: str = "", reserved_at: str = "", guests: int = 1, notes: str = "") -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/tables/{int(table_id)}/reserve", {"customer_name": customer_name, "phone": phone, "reserved_at": reserved_at, "guests": guests, "notes": notes}) or {}

    def cancel_reservation(self, reservation_id: int) -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/reservations/{int(reservation_id)}/cancel", {}) or {}

    def transfer_session(self, session_id: int, target_table_id: int) -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/sessions/{int(session_id)}/transfer", {"target_table_id": int(target_table_id)}) or {}

    def merge_sessions(self, source_session_id: int, target_session_id: int) -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/sessions/{int(target_session_id)}/merge", {"source_session_id": int(source_session_id)}) or {}

    def split_lines_to_table(self, session_id: int, line_ids: list[int], target_table_id: int, guests: int = 1, notes: str = "") -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/sessions/{int(session_id)}/split_lines", {"line_ids": line_ids or [], "target_table_id": int(target_table_id), "guests": guests, "notes": notes}) or {}

    def close_session(self, session_id: int, invoice_id: int | None = None) -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/sessions/{int(session_id)}/close", {"invoice_id": invoice_id}) or {}

    def assign_waiter(self, session_id: int, waiter_id: str, notes: str = "") -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/sessions/{int(session_id)}/waiter", {"waiter_id": waiter_id, "notes": notes}) or {}

    def call_waiter(self, session_id: int, notes: str = "") -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/sessions/{int(session_id)}/waiter_call", {"notes": notes}) or {}

    def resolve_waiter_call(self, session_id: int, notes: str = "") -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/sessions/{int(session_id)}/waiter_call/resolve", {"notes": notes}) or {}

    def waiter_session_summary(self, session_id: int) -> dict[str, Any]:
        return self.client._request("GET", f"/api/restaurant/sessions/{int(session_id)}/waiter_summary") or {}


    def list_kitchen_stations(self, include_inactive: bool = False) -> list[dict[str, Any]]:
        return self.client._request("GET", "/api/restaurant/kitchen/stations", {"include_inactive": "1" if include_inactive else "0"}) or []

    def upsert_kitchen_station(self, name: str, code: str = "", sort_order: int = 0, station_id: int | None = None, is_active: bool = True) -> dict[str, Any]:
        return self.client._request("POST", "/api/restaurant/kitchen/stations", {"id": station_id, "name": name, "code": code, "sort_order": sort_order, "is_active": bool(is_active)}) or {}

    def assign_menu_item_station(self, item_id: int, station_id: int) -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/menu_items/{int(item_id)}/station", {"station_id": int(station_id)}) or {}

    def restaurant_analytics(self, start_date: str = "", end_date: str = "") -> dict[str, Any]:
        params = {"start_date": start_date or "", "end_date": end_date or ""}
        return self.client._request("GET", "/api/restaurant/analytics", params) or {}
