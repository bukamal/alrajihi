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

    def add_order_line(
        self,
        session_id: int,
        item_name: str,
        item_id: int | None = None,
        quantity: Any = "1",
        unit_price: Any = "0",
        notes: str = "",
        unit_id: int | None = None,
        unit: str = "",
        conversion_factor: Any = "1",
        base_qty: Any | None = None,
        barcode_scope: str = "",
        matched_barcode: str = "",
    ) -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/sessions/{int(session_id)}/lines", {
            "item_id": item_id,
            "item_name": item_name,
            "quantity": quantity,
            "unit_price": unit_price,
            "notes": notes,
            "unit_id": unit_id,
            "unit": unit,
            "conversion_factor": conversion_factor,
            "base_qty": base_qty,
            "barcode_scope": barcode_scope,
            "matched_barcode": matched_barcode,
        }) or {}

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

    def set_session_adjustments(self, session_id: int, discount_amount: Any = "0", service_charge_amount: Any = "0", tax_amount: Any = "0", notes: str = "") -> dict[str, Any]:
        return self.client._request(
            "POST",
            f"/api/restaurant/sessions/{int(session_id)}/adjustments",
            {
                "discount_amount": discount_amount,
                "service_charge_amount": service_charge_amount,
                "tax_amount": tax_amount,
                "notes": notes,
            },
        ) or {}

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



    def create_takeaway_order(self, customer_name: str = "", phone: str = "", notes: str = "") -> dict[str, Any]:
        return self.client.post('/restaurant/takeaway_orders', json={'customer_name': customer_name, 'phone': phone, 'notes': notes})

    def create_delivery_order(self, customer_name: str = "", phone: str = "", address: str = "", delivery_fee: Any = "0", driver_id: str = "", notes: str = "") -> dict[str, Any]:
        return self.client.post('/restaurant/delivery_orders', json={'customer_name': customer_name, 'phone': phone, 'address': address, 'delivery_fee': delivery_fee, 'driver_id': driver_id, 'notes': notes})

    def update_delivery_status(self, session_id: int, status: str, driver_id: str = "", notes: str = "") -> dict[str, Any]:
        return self.client.post(f'/restaurant/sessions/{int(session_id)}/delivery_status', json={'status': status, 'driver_id': driver_id, 'notes': notes})

    def list_restaurant_orders(self, order_type: str = "", status: str = "open", limit: int = 100) -> list[dict[str, Any]]:
        return self.client.get('/restaurant/orders', params={'order_type': order_type, 'status': status, 'limit': int(limit or 100)})

    # Phase 34: modifiers + recipe integration
    def list_modifier_groups(self, item_id: int | None = None, include_inactive: bool = False) -> list[dict[str, Any]]:
        if item_id is None:
            return self.client._request("GET", "/api/restaurant/menu_items/0/modifier_groups", {"include_inactive": "1" if include_inactive else "0"}) or []
        return self.client._request("GET", f"/api/restaurant/menu_items/{int(item_id)}/modifier_groups", {"include_inactive": "1" if include_inactive else "0"}) or []

    def upsert_modifier_group(self, item_id: int | None, name: str, min_selected: int = 0, max_selected: int = 1, is_required: bool = False, group_id: int | None = None) -> dict[str, Any]:
        return self.client._request("POST", "/api/restaurant/modifier_groups", {"id": group_id, "item_id": item_id, "name": name, "min_selected": min_selected, "max_selected": max_selected, "is_required": is_required}) or {}

    def upsert_modifier_option(self, group_id: int, name: str, price_delta: Any = "0", item_id: int | None = None, kitchen_label: str = "", is_default: bool = False, option_id: int | None = None) -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/modifier_groups/{int(group_id)}/options", {"id": option_id, "name": name, "price_delta": price_delta, "item_id": item_id, "kitchen_label": kitchen_label, "is_default": is_default}) or {}

    def add_order_line_modifier(self, line_id: int, option_id: int | None = None, name: str = "", price_delta: Any = "0", quantity: Any = "1", action: str = "add", group_id: int | None = None, kitchen_label: str = "") -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/lines/{int(line_id)}/modifiers", {"option_id": option_id, "name": name, "price_delta": price_delta, "quantity": quantity, "action": action, "group_id": group_id, "kitchen_label": kitchen_label}) or {}

    def list_line_modifiers(self, line_id: int) -> list[dict[str, Any]]:
        return self.client._request("GET", f"/api/restaurant/lines/{int(line_id)}/modifiers") or []

    def get_recipe_by_item(self, item_id: int) -> dict[str, Any]:
        return self.client._request("GET", f"/api/restaurant/menu_items/{int(item_id)}/recipe") or {}

    def upsert_recipe(self, item_id: int, name: str = "", yield_quantity: Any = "1", lines: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/menu_items/{int(item_id)}/recipe", {"name": name, "yield_quantity": yield_quantity, "lines": lines or []}) or {}

    def consume_session_recipes(self, session_id: int, invoice_id: int | None = None) -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/sessions/{int(session_id)}/recipe_consumption", {"invoice_id": invoice_id}) or {}

    # Phase 36: split bill + printer routing
    def create_split_bills(self, session_id: int, splits: list[dict[str, Any]], notes: str = "") -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/sessions/{int(session_id)}/split_bills", {"splits": splits or [], "notes": notes}) or {}

    def list_split_bills(self, session_id: int) -> list[dict[str, Any]]:
        return self.client._request("GET", f"/api/restaurant/sessions/{int(session_id)}/split_bills") or []

    def pay_split_bill(self, split_bill_id: int, amount: Any, payment_method: str = "cash", notes: str = "") -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/split_bills/{int(split_bill_id)}/payments", {"amount": amount, "payment_method": payment_method, "notes": notes}) or {}

    def list_printers(self, include_inactive: bool = False) -> list[dict[str, Any]]:
        return self.client._request("GET", "/api/restaurant/printers", {"include_inactive": "1" if include_inactive else "0"}) or []

    def upsert_printer(self, name: str, printer_type: str = "kitchen", device_uri: str = "", printer_id: int | None = None, is_active: bool = True) -> dict[str, Any]:
        return self.client._request("POST", "/api/restaurant/printers", {"id": printer_id, "name": name, "printer_type": printer_type, "device_uri": device_uri, "is_active": bool(is_active)}) or {}

    def assign_station_printer(self, station_id: int, printer_id: int) -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/kitchen/stations/{int(station_id)}/printer", {"printer_id": int(printer_id)}) or {}

    def queue_ticket_print(self, ticket_id: int, job_type: str = "kot") -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/kitchen/tickets/{int(ticket_id)}/print_jobs", {"job_type": job_type}) or {}

    def mark_print_job_done(self, job_id: int) -> dict[str, Any]:
        return self.client._request("POST", f"/api/restaurant/print_jobs/{int(job_id)}/printed", {}) or {}


    def restaurant_production_readiness(self) -> dict[str, Any]:
        return self.client._request("GET", "/api/restaurant/readiness") or {}

