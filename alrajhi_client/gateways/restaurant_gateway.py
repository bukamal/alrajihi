# -*- coding: utf-8 -*-
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class RestaurantGateway(ABC):
    @abstractmethod
    def list_tables(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def upsert_table(self, name: str, zone: str = "", seats: int = 4, table_id: int | None = None) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def open_table(self, table_id: int, guests: int = 1, waiter_id: str | None = None, notes: str = "") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_session(self, session_id: int) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    def send_to_kitchen(self, session_id: int, notes: str = "") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def update_line_status(self, line_id: int, status: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def mark_payment_pending(self, session_id: int) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def list_menu_items(self, search: str = "", category_id: int | None = None, limit: int = 48) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def session_balance(self, session_id: int) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def set_session_adjustments(self, session_id: int, discount_amount: Any = "0", service_charge_amount: Any = "0", tax_amount: Any = "0", notes: str = "") -> dict[str, Any]:
        raise NotImplementedError


    @abstractmethod
    def record_payment(self, session_id: int, amount: Any, payment_method: str = "cash", notes: str = "") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def checkout_session(self, session_id: int, paid_amount: Any | None = None, payment_method: str = "cash") -> dict[str, Any]:
        raise NotImplementedError


    @abstractmethod
    def list_kitchen_tickets(self, status: str = "active", limit: int = 50, station_id: int | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_kitchen_ticket(self, ticket_id: int) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def update_kitchen_ticket_status(self, ticket_id: int, status: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def reserve_table(self, table_id: int, customer_name: str = "", phone: str = "", reserved_at: str = "", guests: int = 1, notes: str = "") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def cancel_reservation(self, reservation_id: int) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def transfer_session(self, session_id: int, target_table_id: int) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def merge_sessions(self, source_session_id: int, target_session_id: int) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def split_lines_to_table(self, session_id: int, line_ids: list[int], target_table_id: int, guests: int = 1, notes: str = "") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def close_session(self, session_id: int, invoice_id: int | None = None) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def assign_waiter(self, session_id: int, waiter_id: str, notes: str = "") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def call_waiter(self, session_id: int, notes: str = "") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def resolve_waiter_call(self, session_id: int, notes: str = "") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def waiter_session_summary(self, session_id: int) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def list_kitchen_stations(self, include_inactive: bool = False) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def upsert_kitchen_station(self, name: str, code: str = "", sort_order: int = 0, station_id: int | None = None, is_active: bool = True) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def assign_menu_item_station(self, item_id: int, station_id: int) -> dict[str, Any]:
        raise NotImplementedError


    @abstractmethod
    def restaurant_analytics(self, start_date: str = "", end_date: str = "") -> dict[str, Any]:
        raise NotImplementedError



    @abstractmethod
    def list_modifier_groups(self, item_id: int | None = None, include_inactive: bool = False) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def upsert_modifier_group(self, item_id: int | None, name: str, min_selected: int = 0, max_selected: int = 1, is_required: bool = False, group_id: int | None = None) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def upsert_modifier_option(self, group_id: int, name: str, price_delta: Any = "0", item_id: int | None = None, kitchen_label: str = "", is_default: bool = False, option_id: int | None = None) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def add_order_line_modifier(self, line_id: int, option_id: int | None = None, name: str = "", price_delta: Any = "0", quantity: Any = "1", action: str = "add", group_id: int | None = None, kitchen_label: str = "") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def list_line_modifiers(self, line_id: int) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_recipe_by_item(self, item_id: int) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def upsert_recipe(self, item_id: int, name: str = "", yield_quantity: Any = "1", lines: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def consume_session_recipes(self, session_id: int, invoice_id: int | None = None) -> dict[str, Any]:
        raise NotImplementedError


    @abstractmethod
    def create_takeaway_order(self, customer_name: str = "", phone: str = "", notes: str = "") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def create_delivery_order(self, customer_name: str = "", phone: str = "", address: str = "", delivery_fee: Any = "0", driver_id: str = "", notes: str = "") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def update_delivery_status(self, session_id: int, status: str, driver_id: str = "", notes: str = "") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def list_restaurant_orders(self, order_type: str = "", status: str = "open", limit: int = 100) -> list[dict[str, Any]]:
        raise NotImplementedError


    @abstractmethod
    def create_split_bills(self, session_id: int, splits: list[dict[str, Any]], notes: str = "") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def list_split_bills(self, session_id: int) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def pay_split_bill(self, split_bill_id: int, amount: Any, payment_method: str = "cash", notes: str = "") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def list_printers(self, include_inactive: bool = False) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def upsert_printer(self, name: str, printer_type: str = "kitchen", device_uri: str = "", printer_id: int | None = None, is_active: bool = True) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def assign_station_printer(self, station_id: int, printer_id: int) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def queue_ticket_print(self, ticket_id: int, job_type: str = "kot") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def mark_print_job_done(self, job_id: int) -> dict[str, Any]:
        raise NotImplementedError


    @abstractmethod
    def restaurant_production_readiness(self) -> dict[str, Any]:
        raise NotImplementedError


def create_restaurant_gateway() -> RestaurantGateway:
    from database.connection import DatabaseConnection
    db = DatabaseConnection()
    if db.is_remote():
        from gateways.remote.restaurant_gateway import RemoteRestaurantGateway
        return RemoteRestaurantGateway(db.get_rest_client())
    from gateways.local.restaurant_gateway import LocalRestaurantGateway
    return LocalRestaurantGateway()
