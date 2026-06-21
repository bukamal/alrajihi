# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from core.services.barcode_input_service import barcode_input_service
from core.services.restaurant_operation_policy import restaurant_operation_policy
from gateways.restaurant_gateway import create_restaurant_gateway
from features.restaurant.cafe_size_modifier_policy import build_line_modifiers, cafe_line_notes


class RestaurantService:
    """Touch-first restaurant workflow service.

    It keeps restaurant sessions separate from invoices until checkout. Closing a
    session can later be wired to InvoiceService without changing the table/KOT
    workflow.
    """

    def __init__(self):
        self.gateway = create_restaurant_gateway()

    def _require_and_log(self, operation: str, context: str, values: dict[str, Any] | None = None) -> None:
        restaurant_operation_policy.require(operation)
        restaurant_operation_policy.log(operation, allowed=True, context=context, values=values or {})

    def list_tables(self) -> list[dict[str, Any]]:
        return self.gateway.list_tables()

    def create_table(self, name: str, zone: str = "", seats: int = 4) -> dict[str, Any]:
        return self.gateway.upsert_table(name=name, zone=zone, seats=seats)

    def open_table(self, table_id: int, guests: int = 1, waiter_id: str | None = None, notes: str = "") -> dict[str, Any]:
        restaurant_operation_policy.require(restaurant_operation_policy.OP_OPEN_SESSION)
        result = self.gateway.open_table(table_id=table_id, guests=guests, waiter_id=waiter_id, notes=notes)
        restaurant_operation_policy.log(restaurant_operation_policy.OP_OPEN_SESSION, allowed=True, context="restaurant_service.open_table", values={"table_id": table_id, "guests": guests})
        return result

    def create_cafe_quick_order(self, customer_name: str = "", phone: str = "", notes: str = "") -> dict[str, Any]:
        restaurant_operation_policy.require(restaurant_operation_policy.OP_OPEN_SESSION)
        result = self.gateway.create_cafe_quick_order(customer_name=customer_name, phone=phone, notes=notes)
        restaurant_operation_policy.log(
            restaurant_operation_policy.OP_OPEN_SESSION,
            allowed=True,
            context="restaurant_service.create_cafe_quick_order",
            values={"order_type": "cafe_quick_order"},
        )
        return result

    def get_session(self, session_id: int) -> dict[str, Any]:
        return self.gateway.get_session(session_id)

    def _decimal(self, value: Any, default: str = "0") -> Decimal:
        try:
            return Decimal(str(value if value not in (None, "") else default))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal(default)

    def _barcode_item_payload(self, item: dict[str, Any], quantity: Any = "1", notes: str = "") -> dict[str, Any]:
        matched_unit = item.get("matched_unit") or {}
        conversion_factor = self._decimal(item.get("conversion_factor") or matched_unit.get("conversion_factor") or "1", "1")
        qty = self._decimal(quantity, "1")
        base_price = self._decimal(item.get("selling_price") or item.get("unit_price") or "0", "0")
        unit_price = base_price * conversion_factor
        unit_name = item.get("unit_name") or item.get("unit") or matched_unit.get("unit_name") or matched_unit.get("unit") or ""
        return {
            "item_id": item.get("id"),
            "item_name": item.get("name") or item.get("item_name") or "",
            "quantity": str(qty),
            "unit_price": str(unit_price),
            "notes": notes or "",
            "unit_id": item.get("unit_id") or matched_unit.get("unit_id") or matched_unit.get("id"),
            "unit": unit_name,
            "conversion_factor": str(conversion_factor),
            "base_qty": str(qty * conversion_factor),
            "barcode_scope": item.get("barcode_scope") or "base_unit",
            "matched_barcode": item.get("matched_barcode") or item.get("barcode") or matched_unit.get("barcode") or "",
        }

    def add_line(
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
        restaurant_operation_policy.require(restaurant_operation_policy.OP_ADD_LINE)
        result = self.gateway.add_order_line(
            session_id=session_id,
            item_name=item_name,
            item_id=item_id,
            quantity=quantity,
            unit_price=unit_price,
            notes=notes,
            unit_id=unit_id,
            unit=unit,
            conversion_factor=conversion_factor,
            base_qty=base_qty,
            barcode_scope=barcode_scope,
            matched_barcode=matched_barcode,
        )
        restaurant_operation_policy.log(restaurant_operation_policy.OP_ADD_LINE, allowed=True, context="restaurant_service.add_line", values={"session_id": session_id, "item_id": item_id, "quantity": quantity})
        return result

    def add_cafe_line(
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
        barcode_scope: str = "menu",
        matched_barcode: str = "",
        size: dict[str, Any] | None = None,
        modifiers: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Add a cafe quick-order line with one size marker and optional add-ons.

        Cafe uses the restaurant order/modifier contract instead of a separate
        order engine.  The base line keeps normal currency/unit behavior; size
        and add-ons are stored as line modifiers so totals, KOT notes, printing,
        and later recipe expansion stay attached to the same restaurant line.
        """
        line_notes = cafe_line_notes(notes, size=size, modifiers=modifiers)
        line = self.add_line(
            session_id=session_id,
            item_name=item_name,
            item_id=item_id,
            quantity=quantity,
            unit_price=unit_price,
            notes=line_notes,
            unit_id=unit_id,
            unit=unit,
            conversion_factor=conversion_factor,
            base_qty=base_qty,
            barcode_scope=barcode_scope or "menu",
            matched_barcode=matched_barcode,
        )
        line_id = int(line.get("id") or 0)
        for modifier in build_line_modifiers(size=size, modifiers=modifiers):
            self.gateway.add_order_line_modifier(
                line_id=line_id,
                option_id=modifier.get("option_id"),
                name=modifier.get("name") or "",
                price_delta=modifier.get("price_delta") or "0",
                quantity=modifier.get("quantity") or "1",
                action=modifier.get("action") or "add",
                group_id=modifier.get("group_id"),
                kitchen_label=modifier.get("kitchen_label") or modifier.get("name") or "",
            )
        restaurant_operation_policy.log(
            restaurant_operation_policy.OP_ADD_LINE,
            allowed=True,
            context="restaurant_service.add_cafe_line",
            values={"session_id": session_id, "item_id": item_id, "modifier_count": len(modifiers or []), "has_size": bool(size)},
        )
        try:
            return self.gateway.get_session(session_id).get("lines", [])[-1] or line
        except Exception:
            return line

    def add_entry(self, session_id: int, raw_entry: Any, quantity: Any = "1", notes: str = "", mode: str = "auto") -> dict[str, Any]:
        """Add a restaurant order line from the unified barcode/manual entry pipeline.

        Scanner-like input is exact-only and never falls back to the first text
        search result.  Unit barcode matches carry unit_id/conversion_factor and
        base_qty into restaurant order lines, so kitchen/POS/checkout can keep the
        material-unit relation intact.
        """
        result = barcode_input_service.lookup_entry(raw_entry, mode=mode)
        if not result.found or not result.item:
            raise ValueError(result.message_key or "transaction_item_not_found")
        payload = self._barcode_item_payload(result.item, quantity=quantity, notes=notes)
        return self.add_line(session_id=session_id, **payload)

    def send_to_kitchen(self, session_id: int, notes: str = "") -> dict[str, Any]:
        restaurant_operation_policy.require(restaurant_operation_policy.OP_SEND_KITCHEN)
        result = self.gateway.send_to_kitchen(session_id, notes=notes)
        restaurant_operation_policy.log(restaurant_operation_policy.OP_SEND_KITCHEN, allowed=True, context="restaurant_service.send_to_kitchen", values={"session_id": session_id})
        return result

    def update_line_status(self, line_id: int, status: str) -> dict[str, Any]:
        restaurant_operation_policy.require(restaurant_operation_policy.OP_UPDATE_KITCHEN_STATUS)
        result = self.gateway.update_line_status(line_id=line_id, status=status)
        restaurant_operation_policy.log(restaurant_operation_policy.OP_UPDATE_KITCHEN_STATUS, allowed=True, context="restaurant_service.update_line_status", values={"line_id": line_id, "status": status})
        return result

    def mark_payment_pending(self, session_id: int) -> dict[str, Any]:
        return self.gateway.mark_payment_pending(session_id=session_id)

    def list_menu_items(self, search: str = "", category_id: int | None = None, limit: int = 48) -> list[dict[str, Any]]:
        return self.gateway.list_menu_items(search=search, category_id=category_id, limit=limit)

    def session_balance(self, session_id: int) -> dict[str, Any]:
        return self.gateway.session_balance(session_id=session_id)

    def set_session_adjustments(self, session_id: int, discount_amount: Any = "0", service_charge_amount: Any = "0", tax_amount: Any = "0", notes: str = "") -> dict[str, Any]:
        restaurant_operation_policy.require(restaurant_operation_policy.OP_ADJUST_BILL)
        result = self.gateway.set_session_adjustments(
            session_id=session_id,
            discount_amount=discount_amount,
            service_charge_amount=service_charge_amount,
            tax_amount=tax_amount,
            notes=notes,
        )
        restaurant_operation_policy.log(restaurant_operation_policy.OP_ADJUST_BILL, allowed=True, context="restaurant_service.set_session_adjustments", values={"session_id": session_id})
        return result

    def record_payment(self, session_id: int, amount: Any, payment_method: str = "cash", notes: str = "") -> dict[str, Any]:
        restaurant_operation_policy.require(restaurant_operation_policy.OP_RECORD_PAYMENT)
        result = self.gateway.record_payment(session_id=session_id, amount=amount, payment_method=payment_method, notes=notes)
        restaurant_operation_policy.log(restaurant_operation_policy.OP_RECORD_PAYMENT, allowed=True, context="restaurant_service.record_payment", values={"session_id": session_id, "payment_method": payment_method})
        return result

    def checkout_session(self, session_id: int, paid_amount: Any | None = None, payment_method: str = "cash") -> dict[str, Any]:
        restaurant_operation_policy.require(restaurant_operation_policy.OP_CHECKOUT)
        result = self.gateway.checkout_session(session_id=session_id, paid_amount=paid_amount, payment_method=payment_method)
        restaurant_operation_policy.log(restaurant_operation_policy.OP_CHECKOUT, allowed=True, context="restaurant_service.checkout_session", values={"session_id": session_id, "payment_method": payment_method})
        return result

    def list_kitchen_tickets(self, status: str = "active", limit: int = 50, station_id: int | None = None, order_type: str | None = None) -> list[dict[str, Any]]:
        return self.gateway.list_kitchen_tickets(status=status, limit=limit, station_id=station_id, order_type=order_type)

    def get_kitchen_ticket(self, ticket_id: int) -> dict[str, Any]:
        return self.gateway.get_kitchen_ticket(ticket_id=ticket_id)

    def update_kitchen_ticket_status(self, ticket_id: int, status: str) -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_UPDATE_KITCHEN_STATUS,
            "restaurant_service.update_kitchen_ticket_status",
            {"ticket_id": ticket_id, "status": status},
        )
        return self.gateway.update_kitchen_ticket_status(ticket_id=ticket_id, status=status)

    def reserve_table(self, table_id: int, customer_name: str = "", phone: str = "", reserved_at: str = "", guests: int = 1, notes: str = "") -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_RESERVE_TABLE,
            "restaurant_service.reserve_table",
            {"table_id": table_id, "guests": guests},
        )
        return self.gateway.reserve_table(table_id=table_id, customer_name=customer_name, phone=phone, reserved_at=reserved_at, guests=guests, notes=notes)

    def cancel_reservation(self, reservation_id: int) -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_CANCEL_RESERVATION,
            "restaurant_service.cancel_reservation",
            {"reservation_id": reservation_id},
        )
        return self.gateway.cancel_reservation(reservation_id=reservation_id)

    def transfer_session(self, session_id: int, target_table_id: int) -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_TRANSFER_TABLE,
            "restaurant_service.transfer_session",
            {"session_id": session_id, "target_table_id": target_table_id},
        )
        return self.gateway.transfer_session(session_id=session_id, target_table_id=target_table_id)

    def merge_sessions(self, source_session_id: int, target_session_id: int) -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_MERGE_TABLES,
            "restaurant_service.merge_sessions",
            {"source_session_id": source_session_id, "target_session_id": target_session_id},
        )
        return self.gateway.merge_sessions(source_session_id=source_session_id, target_session_id=target_session_id)

    def split_lines_to_table(self, session_id: int, line_ids: list[int], target_table_id: int, guests: int = 1, notes: str = "") -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_MOVE_ORDER_LINE,
            "restaurant_service.split_lines_to_table",
            {"session_id": session_id, "line_ids": list(line_ids or []), "target_table_id": target_table_id},
        )
        return self.gateway.split_lines_to_table(session_id=session_id, line_ids=line_ids, target_table_id=target_table_id, guests=guests, notes=notes)

    def close_session(self, session_id: int, invoice_id: int | None = None) -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_CHECKOUT,
            "restaurant_service.close_session",
            {"session_id": session_id, "invoice_id": invoice_id},
        )
        return self.gateway.close_session(session_id=session_id, invoice_id=invoice_id)


    def assign_waiter(self, session_id: int, waiter_id: str, notes: str = "") -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_WAITER_WORKFLOW,
            "restaurant_service.assign_waiter",
            {"session_id": session_id, "waiter_id": waiter_id},
        )
        return self.gateway.assign_waiter(session_id=session_id, waiter_id=waiter_id, notes=notes)

    def call_waiter(self, session_id: int, notes: str = "") -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_WAITER_WORKFLOW,
            "restaurant_service.call_waiter",
            {"session_id": session_id},
        )
        return self.gateway.call_waiter(session_id=session_id, notes=notes)

    def resolve_waiter_call(self, session_id: int, notes: str = "") -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_WAITER_WORKFLOW,
            "restaurant_service.resolve_waiter_call",
            {"session_id": session_id},
        )
        return self.gateway.resolve_waiter_call(session_id=session_id, notes=notes)

    def waiter_session_summary(self, session_id: int) -> dict[str, Any]:
        return self.gateway.waiter_session_summary(session_id=session_id)

    def list_kitchen_stations(self, include_inactive: bool = False) -> list[dict[str, Any]]:
        return self.gateway.list_kitchen_stations(include_inactive=include_inactive)

    def upsert_kitchen_station(self, name: str, code: str = "", sort_order: int = 0, station_id: int | None = None, is_active: bool = True) -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_KITCHEN_STATION_MANAGE,
            "restaurant_service.upsert_kitchen_station",
            {"station_id": station_id, "name": name, "is_active": is_active},
        )
        return self.gateway.upsert_kitchen_station(name=name, code=code, sort_order=sort_order, station_id=station_id, is_active=is_active)

    def assign_menu_item_station(self, item_id: int, station_id: int) -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_KITCHEN_STATION_MANAGE,
            "restaurant_service.assign_menu_item_station",
            {"item_id": item_id, "station_id": station_id},
        )
        return self.gateway.assign_menu_item_station(item_id=item_id, station_id=station_id)


    def restaurant_analytics(self, start_date: str = "", end_date: str = "") -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_VIEW_ANALYTICS,
            "restaurant_service.restaurant_analytics",
            {"start_date": start_date, "end_date": end_date},
        )
        return self.gateway.restaurant_analytics(start_date=start_date, end_date=end_date)


    def restaurant_shift_report(self, start_datetime: str = "", end_datetime: str = "", cashier_id: str = "") -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_VIEW_ANALYTICS,
            "restaurant_service.restaurant_shift_report",
            {"start_datetime": start_datetime, "end_datetime": end_datetime, "cashier_id": cashier_id},
        )
        return self.gateway.restaurant_shift_report(start_datetime=start_datetime, end_datetime=end_datetime, cashier_id=cashier_id)


    def cafe_shift_report(self, start_datetime: str = "", end_datetime: str = "", cashier_id: str = "") -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_VIEW_ANALYTICS,
            "restaurant_service.cafe_shift_report",
            {"start_datetime": start_datetime, "end_datetime": end_datetime, "cashier_id": cashier_id, "order_type": "cafe_quick_order"},
        )
        return self.gateway.cafe_shift_report(start_datetime=start_datetime, end_datetime=end_datetime, cashier_id=cashier_id)


    # Phase 34: modifiers + recipe integration
    def list_modifier_groups(self, item_id: int | None = None, include_inactive: bool = False) -> list[dict[str, Any]]:
        return self.gateway.list_modifier_groups(item_id=item_id, include_inactive=include_inactive)

    def upsert_modifier_group(self, item_id: int | None, name: str, min_selected: int = 0, max_selected: int = 1, is_required: bool = False, group_id: int | None = None) -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_MODIFIER_MANAGE,
            "restaurant_service.upsert_modifier_group",
            {"item_id": item_id, "group_id": group_id, "name": name},
        )
        return self.gateway.upsert_modifier_group(item_id=item_id, name=name, min_selected=min_selected, max_selected=max_selected, is_required=is_required, group_id=group_id)

    def upsert_modifier_option(self, group_id: int, name: str, price_delta: Any = "0", item_id: int | None = None, kitchen_label: str = "", is_default: bool = False, option_id: int | None = None) -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_MODIFIER_MANAGE,
            "restaurant_service.upsert_modifier_option",
            {"group_id": group_id, "option_id": option_id, "name": name},
        )
        return self.gateway.upsert_modifier_option(group_id=group_id, name=name, price_delta=price_delta, item_id=item_id, kitchen_label=kitchen_label, is_default=is_default, option_id=option_id)

    def add_order_line_modifier(self, line_id: int, option_id: int | None = None, name: str = "", price_delta: Any = "0", quantity: Any = "1", action: str = "add", group_id: int | None = None, kitchen_label: str = "") -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_MODIFIER_MANAGE,
            "restaurant_service.add_order_line_modifier",
            {"line_id": line_id, "option_id": option_id, "action": action},
        )
        return self.gateway.add_order_line_modifier(line_id=line_id, option_id=option_id, name=name, price_delta=price_delta, quantity=quantity, action=action, group_id=group_id, kitchen_label=kitchen_label)

    def list_line_modifiers(self, line_id: int) -> list[dict[str, Any]]:
        return self.gateway.list_line_modifiers(line_id=line_id)

    def get_recipe_by_item(self, item_id: int) -> dict[str, Any]:
        return self.gateway.get_recipe_by_item(item_id=item_id)

    def upsert_recipe(self, item_id: int, name: str = "", yield_quantity: Any = "1", lines: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_RECIPE_MANAGE,
            "restaurant_service.upsert_recipe",
            {"item_id": item_id, "line_count": len(lines or [])},
        )
        return self.gateway.upsert_recipe(item_id=item_id, name=name, yield_quantity=yield_quantity, lines=lines or [])

    def consume_session_recipes(self, session_id: int, invoice_id: int | None = None) -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_RECIPE_MANAGE,
            "restaurant_service.consume_session_recipes",
            {"session_id": session_id, "invoice_id": invoice_id},
        )
        return self.gateway.consume_session_recipes(session_id=session_id, invoice_id=invoice_id)



    # Phase 35: takeaway/delivery workflow
    def create_takeaway_order(self, customer_name: str = "", phone: str = "", notes: str = "") -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_DELIVERY_TAKEAWAY,
            "restaurant_service.create_takeaway_order",
            {"customer_name": customer_name},
        )
        return self.gateway.create_takeaway_order(customer_name=customer_name, phone=phone, notes=notes)

    def create_delivery_order(self, customer_name: str = "", phone: str = "", address: str = "", delivery_fee: Any = "0", driver_id: str = "", notes: str = "") -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_DELIVERY_TAKEAWAY,
            "restaurant_service.create_delivery_order",
            {"customer_name": customer_name, "driver_id": driver_id},
        )
        return self.gateway.create_delivery_order(customer_name=customer_name, phone=phone, address=address, delivery_fee=delivery_fee, driver_id=driver_id, notes=notes)

    def update_delivery_status(self, session_id: int, status: str, driver_id: str = "", notes: str = "") -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_DELIVERY_TAKEAWAY,
            "restaurant_service.update_delivery_status",
            {"session_id": session_id, "status": status, "driver_id": driver_id},
        )
        return self.gateway.update_delivery_status(session_id=session_id, status=status, driver_id=driver_id, notes=notes)

    def list_restaurant_orders(self, order_type: str = "", status: str = "open", limit: int = 100) -> list[dict[str, Any]]:
        return self.gateway.list_restaurant_orders(order_type=order_type, status=status, limit=limit)

    # Phase 36: split bill + printer routing
    def create_split_bills(self, session_id: int, splits: list[dict[str, Any]], notes: str = "") -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_SPLIT_BILL,
            "restaurant_service.create_split_bills",
            {"session_id": session_id, "split_count": len(splits or [])},
        )
        return self.gateway.create_split_bills(session_id=session_id, splits=splits, notes=notes)

    def list_split_bills(self, session_id: int) -> list[dict[str, Any]]:
        return self.gateway.list_split_bills(session_id=session_id)

    def pay_split_bill(self, split_bill_id: int, amount: Any, payment_method: str = "cash", notes: str = "") -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_RECORD_PAYMENT,
            "restaurant_service.pay_split_bill",
            {"split_bill_id": split_bill_id, "payment_method": payment_method},
        )
        return self.gateway.pay_split_bill(split_bill_id=split_bill_id, amount=amount, payment_method=payment_method, notes=notes)

    def list_printers(self, include_inactive: bool = False) -> list[dict[str, Any]]:
        return self.gateway.list_printers(include_inactive=include_inactive)

    def upsert_printer(self, name: str, printer_type: str = "kitchen", device_uri: str = "", printer_id: int | None = None, is_active: bool = True) -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_PRINTER_MANAGE,
            "restaurant_service.upsert_printer",
            {"printer_id": printer_id, "printer_type": printer_type, "is_active": is_active},
        )
        return self.gateway.upsert_printer(name=name, printer_type=printer_type, device_uri=device_uri, printer_id=printer_id, is_active=is_active)

    def assign_station_printer(self, station_id: int, printer_id: int) -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_PRINTER_MANAGE,
            "restaurant_service.assign_station_printer",
            {"station_id": station_id, "printer_id": printer_id},
        )
        return self.gateway.assign_station_printer(station_id=station_id, printer_id=printer_id)

    def queue_ticket_print(self, ticket_id: int, job_type: str = "kot") -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_PRINT_QUEUE,
            "restaurant_service.queue_ticket_print",
            {"ticket_id": ticket_id, "job_type": job_type},
        )
        return self.gateway.queue_ticket_print(ticket_id=ticket_id, job_type=job_type)

    def mark_print_job_done(self, job_id: int) -> dict[str, Any]:
        self._require_and_log(
            restaurant_operation_policy.OP_PRINT_QUEUE,
            "restaurant_service.mark_print_job_done",
            {"job_id": job_id},
        )
        return self.gateway.mark_print_job_done(job_id=job_id)

    # Phase 37: production readiness diagnostics
    def restaurant_production_readiness(self) -> dict[str, Any]:
        return self.gateway.restaurant_production_readiness()


restaurant_service = RestaurantService()
