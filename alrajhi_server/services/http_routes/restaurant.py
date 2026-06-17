from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from alrajhi_server.decorators import admin_required
from alrajhi_server.repositories.restaurant_repository import get_restaurant_repository

restaurant_bp = Blueprint("restaurant", __name__)
_repo = get_restaurant_repository()


@restaurant_bp.route("/restaurant/tables", methods=["GET"])
@jwt_required()
def list_tables():
    return jsonify(_repo.list_tables(include_inactive=request.args.get("include_inactive") == "1"))


@restaurant_bp.route("/restaurant/tables", methods=["POST"])
@admin_required
def upsert_table():
    data = request.get_json() or {}
    try:
        return jsonify(_repo.upsert_table(
            name=data.get("name") or "Table",
            zone=data.get("zone") or "",
            seats=int(data.get("seats") or 4),
            table_id=data.get("id"),
        ))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/tables/<int:table_id>/open", methods=["POST"])
@jwt_required()
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
def get_session(session_id: int):
    try:
        payload = _repo.get_session(session_id)
        payload["lines"] = _repo.list_session_lines(session_id)
        return jsonify(payload)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 404



@restaurant_bp.route("/restaurant/menu_items", methods=["GET"])
@jwt_required()
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
        ))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/send_to_kitchen", methods=["POST"])
@jwt_required()
def send_to_kitchen(session_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.send_to_kitchen(session_id, notes=data.get("notes") or ""))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/lines/<int:line_id>/status", methods=["POST"])
@jwt_required()
def update_line_status(line_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.update_line_status(line_id, data.get("status") or ""))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/payment_pending", methods=["POST"])
@jwt_required()
def mark_payment_pending(session_id: int):
    try:
        return jsonify(_repo.mark_payment_pending(session_id))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/balance", methods=["GET"])
@jwt_required()
def session_balance(session_id: int):
    try:
        return jsonify(_repo.session_balance(session_id))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/payments", methods=["POST"])
@jwt_required()
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
def list_kitchen_tickets():
    try:
        station_arg = request.args.get("station_id")
        station_id = int(station_arg) if station_arg not in (None, "") else None
        return jsonify(_repo.list_kitchen_tickets(
            status=request.args.get("status") or "sent",
            limit=int(request.args.get("limit") or 50),
            station_id=station_id,
        ))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/kitchen/tickets/<int:ticket_id>", methods=["GET"])
@jwt_required()
def get_kitchen_ticket(ticket_id: int):
    try:
        return jsonify(_repo.get_kitchen_ticket(ticket_id))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 404


@restaurant_bp.route("/restaurant/kitchen/tickets/<int:ticket_id>/status", methods=["POST"])
@jwt_required()
def update_kitchen_ticket_status(ticket_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.update_kitchen_ticket_status(ticket_id, data.get("status") or ""))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/tables/<int:table_id>/reserve", methods=["POST"])
@jwt_required()
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
def cancel_reservation(reservation_id: int):
    try:
        return jsonify(_repo.cancel_reservation(reservation_id))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/transfer", methods=["POST"])
@jwt_required()
def transfer_session(session_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.transfer_session(session_id, int(data.get("target_table_id"))))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:target_session_id>/merge", methods=["POST"])
@jwt_required()
def merge_sessions(target_session_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.merge_sessions(int(data.get("source_session_id")), target_session_id))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/split_lines", methods=["POST"])
@jwt_required()
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
def close_session(session_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.close_session(session_id, invoice_id=data.get("invoice_id")))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

@restaurant_bp.route("/restaurant/kitchen/stations", methods=["GET"])
@jwt_required()
def list_kitchen_stations():
    try:
        return jsonify(_repo.list_kitchen_stations(include_inactive=request.args.get("include_inactive") == "1"))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/kitchen/stations", methods=["POST"])
@admin_required
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
def assign_menu_item_station(item_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.assign_menu_item_station(item_id, int(data.get("station_id"))))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/waiter", methods=["POST"])
@jwt_required()
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
def call_waiter(session_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.call_waiter(session_id=session_id, notes=data.get("notes") or ""))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/waiter_call/resolve", methods=["POST"])
@jwt_required()
def resolve_waiter_call(session_id: int):
    data = request.get_json() or {}
    try:
        return jsonify(_repo.resolve_waiter_call(session_id=session_id, notes=data.get("notes") or ""))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@restaurant_bp.route("/restaurant/sessions/<int:session_id>/waiter_summary", methods=["GET"])
@jwt_required()
def waiter_session_summary(session_id: int):
    try:
        return jsonify(_repo.waiter_session_summary(session_id=session_id))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

