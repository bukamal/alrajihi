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
    def add_order_line(self, session_id: int, item_name: str, item_id: int | None = None, quantity: Any = "1", unit_price: Any = "0", notes: str = "") -> dict[str, Any]:
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
    def record_payment(self, session_id: int, amount: Any, payment_method: str = "cash", notes: str = "") -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def checkout_session(self, session_id: int, paid_amount: Any | None = None, payment_method: str = "cash") -> dict[str, Any]:
        raise NotImplementedError


    @abstractmethod
    def list_kitchen_tickets(self, status: str = "sent", limit: int = 50, station_id: int | None = None) -> list[dict[str, Any]]:
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


def create_restaurant_gateway() -> RestaurantGateway:
    from database.connection import DatabaseConnection
    db = DatabaseConnection()
    if db.is_remote():
        from gateways.remote.restaurant_gateway import RemoteRestaurantGateway
        return RemoteRestaurantGateway(db.get_rest_client())
    from gateways.local.restaurant_gateway import LocalRestaurantGateway
    return LocalRestaurantGateway()
