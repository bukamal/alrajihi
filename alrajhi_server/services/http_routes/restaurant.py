from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from alrajhi_server.decorators import admin_required
from alrajhi_server.repositories.restaurant_repository import get_restaurant_repository
from alrajhi_server.services.restaurant_branch_scope import (
    branch_denied_response,
    filter_restaurant_records,
    restaurant_branch_guard,
    scope_creation_payload,
)

restaurant_bp = Blueprint("restaurant", __name__)
_repo = get_restaurant_repository()


@restaurant_bp.route("/restaurant/tables", methods=["GET"])
@jwt_required()
@restaurant_branch_guard()
def list_tables():
    return jsonify(filter_restaurant_records(get_jwt_identity(), _repo.list_tables(include_inactive=request.args.get("include_inactive") == "1")))


@restaurant_bp.route("/restaurant/tables", methods=["POST"])
@admin_required
@restaurant_branch_guard(create=True)
def upsert_table():
    data = request.get_json() or {}
    try:
        scope_creation_payload(get_jwt_identity(), context="restaurant_table")
        data = request.get_json() or {}
        return jsonify(_repo.upsert_table(
            name=data.get("name") or "Table",
            zone=data.get("zone") or "",
            seats=int(data.get("seats") or 4),
            table_id=data.get("id"),
            branch_id=data.get("branch_id"),
        ))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/tables/<int:table_id>/open", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def open_table(table_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.open_table(
            table_id=table_id,
            waiter_id=data.get("waiter_id"),
            guests=int(data.get("guests") or 1),
            notes=data.get("notes") or "",
        ))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>", methods=["GET"])
@jwt_required()
@restaurant_branch_guard()
def get_session(session_id: int):
    try:
        payload = _repo.get_session(session_id)
        payload["lines"] = _repo.list_session_lines(session_id)
        return jsonify(payload)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 404



@restaurant_bp.route("/restaurant/menu_items", methods=["GET"])
@jwt_required()
@restaurant_branch_guard()
def list_menu_items():
    try:
        category = request.args.get("category_id")
        category_id = int(category) if category not in (None, "") else None
        return jsonify(_repo.list_menu_items(
            search=request.args.get("search") or "",
            category_id=category_id,
            limit=int(request.args.get("limit") or 48),
        ))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/lines", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def add_line(session_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.add_order_line(
            session_id=session_id,
            item_id=data.get("item_id"),
            item_name=data.get("item_name") or data.get("description") or "Item",
            quantity=data.get("quantity") or "1",
            unit_price=data.get("unit_price") or "0",
            notes=data.get("notes") or "",
            unit_id=data.get("unit_id"),
            unit=data.get("unit") or "",
            conversion_factor=data.get("conversion_factor") or "1",
            base_qty=data.get("base_qty"),
            barcode_scope=data.get("barcode_scope") or "",
            matched_barcode=data.get("matched_barcode") or "",
        ))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/send_to_kitchen", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def send_to_kitchen(session_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.send_to_kitchen(session_id, notes=data.get("notes") or ""))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/lines/<int:line_id>/status", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def update_line_status(line_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.update_line_status(line_id, data.get("status") or ""))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/payment_pending", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def mark_payment_pending(session_id: int):
    try:
        return jsonify(_repo.mark_payment_pending(session_id))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/balance", methods=["GET"])
@jwt_required()
@restaurant_branch_guard()
def session_balance(session_id: int):
    try:
        return jsonify(_repo.session_balance(session_id))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/adjustments", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def set_session_adjustments(session_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.set_session_adjustments(
            session_id=session_id,
            discount_amount=data.get("discount_amount") or "0",
            service_charge_amount=data.get("service_charge_amount") or "0",
            tax_amount=data.get("tax_amount") or "0",
            notes=data.get("notes") or "",
        ))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/payments", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def record_payment(session_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.record_payment(
            session_id=session_id,
            amount=data.get("amount") or "0",
            payment_method=data.get("payment_method") or "cash",
            notes=data.get("notes") or "",
        ))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/checkout", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def checkout_session(session_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.checkout_session(
            session_id=session_id,
            user_id=get_jwt_identity() or data.get("user_id") or "restaurant",
            paid_amount=data.get("paid_amount"),
            payment_method=data.get("payment_method") or "cash",
        ))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/kitchen/tickets", methods=["GET"])
@jwt_required()
@restaurant_branch_guard()
def list_kitchen_tickets():
    try:
        station_arg = request.args.get("station_id")
        station_id = int(station_arg) if station_arg not in (None, "") else None
        return jsonify(filter_restaurant_records(get_jwt_identity(), _repo.list_kitchen_tickets(
            status=request.args.get("status") or "sent",
            limit=int(request.args.get("limit") or 50),
            station_id=station_id,
        )))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/kitchen/tickets/<int:ticket_id>", methods=["GET"])
@jwt_required()
@restaurant_branch_guard()
def get_kitchen_ticket(ticket_id: int):
    try:
        return jsonify(_repo.get_kitchen_ticket(ticket_id))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 404


@restaurant_bp.route("/restaurant/kitchen/tickets/<int:ticket_id>/status", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def update_kitchen_ticket_status(ticket_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.update_kitchen_ticket_status(ticket_id, data.get("status") or ""))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/tables/<int:table_id>/reserve", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def reserve_table(table_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.reserve_table(
            table_id=table_id,
            customer_name=data.get("customer_name") or "",
            phone=data.get("phone") or "",
            reserved_at=data.get("reserved_at") or "",
            guests=int(data.get("guests") or 1),
            notes=data.get("notes") or "",
        ))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/reservations/<int:reservation_id>/cancel", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def cancel_reservation(reservation_id: int):
    try:
        return jsonify(_repo.cancel_reservation(reservation_id))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/transfer", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def transfer_session(session_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.transfer_session(session_id, int(data.get("target_table_id"))))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:target_session_id>/merge", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def merge_sessions(target_session_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.merge_sessions(int(data.get("source_session_id")), target_session_id))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/split_lines", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def split_lines(session_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.split_lines_to_table(
            session_id=session_id,
            line_ids=[int(x) for x in (data.get("line_ids") or [])],
            target_table_id=int(data.get("target_table_id")),
            guests=int(data.get("guests") or 1),
            notes=data.get("notes") or "",
        ))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/close", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def close_session(session_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.close_session(session_id, invoice_id=data.get("invoice_id")))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

@restaurant_bp.route("/restaurant/kitchen/stations", methods=["GET"])
@jwt_required()
@restaurant_branch_guard()
def list_kitchen_stations():
    try:
        return jsonify(_repo.list_kitchen_stations(include_inactive=request.args.get("include_inactive") == "1"))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/kitchen/stations", methods=["POST"])
@admin_required
@restaurant_branch_guard(create=True)
def upsert_kitchen_station():
    data = request.get_json() or {}
    try:
        return jsonify(_repo.upsert_kitchen_station(
            name=data.get("name") or "Station",
            code=data.get("code") or "",
            sort_order=int(data.get("sort_order") or 0),
            station_id=data.get("id"),
            is_active=bool(data.get("is_active", True)),
        ))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/menu_items/<int:item_id>/station", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def assign_menu_item_station(item_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.assign_menu_item_station(item_id, int(data.get("station_id"))))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/waiter", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def assign_waiter(session_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.assign_waiter(
            session_id=session_id,
            waiter_id=data.get("waiter_id") or get_jwt_identity() or "",
            notes=data.get("notes") or "",
        ))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/waiter_call", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def call_waiter(session_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.call_waiter(session_id=session_id, notes=data.get("notes") or ""))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/waiter_call/resolve", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def resolve_waiter_call(session_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.resolve_waiter_call(session_id=session_id, notes=data.get("notes") or ""))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/waiter_summary", methods=["GET"])
@jwt_required()
@restaurant_branch_guard()
def waiter_session_summary(session_id: int):
    try:
        return jsonify(_repo.waiter_session_summary(session_id=session_id))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400



@restaurant_bp.route("/restaurant/analytics", methods=["GET"])
@jwt_required()
@restaurant_branch_guard()
def restaurant_analytics():
    try:
        return jsonify(_repo.restaurant_analytics(
            start_date=request.args.get("start_date") or "",
            end_date=request.args.get("end_date") or "",
        ))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400



# Phase 35: takeaway and delivery endpoints
@restaurant_bp.route("/restaurant/orders", methods=["GET"])
@jwt_required()
@restaurant_branch_guard()
def list_restaurant_orders():
    try:
        return jsonify(filter_restaurant_records(get_jwt_identity(), _repo.list_restaurant_orders(
            order_type=request.args.get("order_type") or "",
            status=request.args.get("status") or "open",
            limit=int(request.args.get("limit") or 100),
        )))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/takeaway_orders", methods=["POST"])
@jwt_required()
@restaurant_branch_guard(create=True)
def create_takeaway_order():
    data = request.get_json() or {}
    try:
        scope_creation_payload(get_jwt_identity(), context="restaurant_takeaway_order")
        data = request.get_json() or {}
        return jsonify(_repo.create_takeaway_order(
            customer_name=data.get("customer_name") or "",
            phone=data.get("phone") or "",
            notes=data.get("notes") or "",
            branch_id=data.get("branch_id"),
        ))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/delivery_orders", methods=["POST"])
@jwt_required()
@restaurant_branch_guard(create=True)
def create_delivery_order():
    data = request.get_json() or {}
    try:
        scope_creation_payload(get_jwt_identity(), context="restaurant_delivery_order")
        data = request.get_json() or {}
        return jsonify(_repo.create_delivery_order(
            customer_name=data.get("customer_name") or "",
            phone=data.get("phone") or "",
            address=data.get("address") or data.get("delivery_address") or "",
            delivery_fee=data.get("delivery_fee") or "0",
            driver_id=data.get("driver_id") or "",
            notes=data.get("notes") or "",
            branch_id=data.get("branch_id"),
        ))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/delivery_status", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def update_delivery_status(session_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.update_delivery_status(
            session_id=session_id,
            status=data.get("status") or "pending",
            driver_id=data.get("driver_id") or "",
            notes=data.get("notes") or "",
        ))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


# Phase 34: modifiers and recipe/consumption endpoints
@restaurant_bp.route("/restaurant/menu_items/<int:item_id>/modifier_groups", methods=["GET"])
@jwt_required()
@restaurant_branch_guard()
def list_item_modifier_groups(item_id: int):
    try:
        return jsonify(_repo.list_modifier_groups(item_id=item_id, include_inactive=request.args.get("include_inactive") == "1"))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/modifier_groups", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def upsert_modifier_group():
    data = request.get_json() or {}
    try:
        return jsonify(_repo.upsert_modifier_group(
            item_id=data.get("item_id"),
            name=data.get("name") or "Modifier Group",
            min_selected=int(data.get("min_selected") or 0),
            max_selected=int(data.get("max_selected") or 1),
            is_required=bool(data.get("is_required", False)),
            group_id=data.get("id"),
        ))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/modifier_groups/<int:group_id>/options", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def upsert_modifier_option(group_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.upsert_modifier_option(
            group_id=group_id,
            name=data.get("name") or "Option",
            price_delta=data.get("price_delta") or "0",
            item_id=data.get("item_id"),
            kitchen_label=data.get("kitchen_label") or "",
            is_default=bool(data.get("is_default", False)),
            option_id=data.get("id"),
        ))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/lines/<int:line_id>/modifiers", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def add_line_modifier(line_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.add_order_line_modifier(
            line_id=line_id,
            option_id=data.get("option_id"),
            name=data.get("name") or "",
            price_delta=data.get("price_delta") or "0",
            quantity=data.get("quantity") or "1",
            action=data.get("action") or "add",
            group_id=data.get("group_id"),
            kitchen_label=data.get("kitchen_label") or "",
        ))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/lines/<int:line_id>/modifiers", methods=["GET"])
@jwt_required()
@restaurant_branch_guard()
def list_line_modifiers(line_id: int):
    try:
        return jsonify(_repo.list_line_modifiers(line_id))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/menu_items/<int:item_id>/recipe", methods=["GET"])
@jwt_required()
@restaurant_branch_guard()
def get_item_recipe(item_id: int):
    try:
        return jsonify(_repo.get_recipe_by_item(item_id))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/menu_items/<int:item_id>/recipe", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def upsert_item_recipe(item_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.upsert_recipe(
            item_id=item_id,
            name=data.get("name") or "",
            yield_quantity=data.get("yield_quantity") or "1",
            lines=data.get("lines") or [],
        ))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/recipe_consumption", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def consume_session_recipes(session_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.consume_session_recipes(session_id=session_id, invoice_id=data.get("invoice_id")))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


# Phase 36: advanced split bill + printer routing endpoints
@restaurant_bp.route("/restaurant/sessions/<int:session_id>/split_bills", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def create_split_bills(session_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.create_split_bills(session_id=session_id, splits=data.get("splits") or [], notes=data.get("notes") or ""))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/split_bills", methods=["GET"])
@jwt_required()
@restaurant_branch_guard()
def list_split_bills(session_id: int):
    try:
        return jsonify(_repo.list_split_bills(session_id=session_id))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/split_bills/<int:split_bill_id>/payments", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def pay_split_bill(split_bill_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.pay_split_bill(split_bill_id=split_bill_id, amount=data.get("amount") or "0", payment_method=data.get("payment_method") or "cash", notes=data.get("notes") or ""))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/printers", methods=["GET"])
@jwt_required()
@restaurant_branch_guard()
def list_restaurant_printers():
    try:
        return jsonify(_repo.list_printers(include_inactive=request.args.get("include_inactive") == "1"))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/printers", methods=["POST"])
@admin_required
@restaurant_branch_guard(create=True)
def upsert_restaurant_printer():
    data = request.get_json() or {}
    try:
        return jsonify(_repo.upsert_printer(name=data.get("name") or "Kitchen Printer", printer_type=data.get("printer_type") or "kitchen", device_uri=data.get("device_uri") or "", printer_id=data.get("id"), is_active=bool(data.get("is_active", True))))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/kitchen/stations/<int:station_id>/printer", methods=["POST"])
@admin_required
@restaurant_branch_guard(create=True)
def assign_station_printer(station_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.assign_station_printer(station_id=station_id, printer_id=int(data.get("printer_id"))))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/kitchen/tickets/<int:ticket_id>/print_jobs", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def queue_ticket_print(ticket_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.queue_ticket_print(ticket_id=ticket_id, job_type=data.get("job_type") or "kot"))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/print_jobs/<int:job_id>/printed", methods=["POST"])
@jwt_required()
@restaurant_branch_guard()
def mark_print_job_done(job_id: int):
    try:
        return jsonify(_repo.mark_print_job_done(job_id=job_id))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


# Phase 37: production readiness diagnostics
@restaurant_bp.route("/restaurant/readiness", methods=["GET"])
@jwt_required()
@restaurant_branch_guard()
def restaurant_production_readiness():
    try:
        return jsonify(_repo.restaurant_production_readiness())
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
