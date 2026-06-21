# -*- coding: utf-8 -*-
import importlib.util
import sqlite3
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_gateway(monkeypatch, tmp_path):
    class TempDatabaseConnection:
        def __init__(self):
            self.path = tmp_path / "restaurant_runtime_acceptance.sqlite3"
            self.conn = sqlite3.connect(self.path)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys=ON")
            self.conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    type TEXT,
                    customer_id INTEGER,
                    supplier_id INTEGER,
                    date TEXT,
                    reference TEXT,
                    notes TEXT,
                    total TEXT DEFAULT '0',
                    paid TEXT DEFAULT '0',
                    status TEXT,
                    workflow_status TEXT DEFAULT 'DRAFT',
                    original_currency TEXT DEFAULT 'USD',
                    payment_method TEXT DEFAULT 'cash'
                );
                CREATE TABLE IF NOT EXISTS invoice_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER,
                    item_id INTEGER,
                    description TEXT,
                    quantity TEXT DEFAULT '0',
                    unit_price TEXT DEFAULT '0',
                    total TEXT DEFAULT '0',
                    unit TEXT,
                    quantity_in_base TEXT DEFAULT '0',
                    unit_cost TEXT DEFAULT '0',
                    cost_amount TEXT DEFAULT '0',
                    conversion_factor REAL DEFAULT 1.0,
                    FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    category_id INTEGER,
                    selling_price TEXT,
                    unit TEXT,
                    barcode TEXT,
                    quantity TEXT,
                    average_cost TEXT,
                    purchase_price TEXT,
                    deleted_at TEXT
                );
                CREATE TABLE IF NOT EXISTS inventory_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER,
                    movement_type TEXT,
                    quantity TEXT,
                    unit_cost TEXT,
                    total_cost TEXT,
                    reference_id TEXT,
                    source_type TEXT,
                    source_key TEXT,
                    notes TEXT,
                    created_at TEXT
                );
                """
            )
            self.conn.commit()

        def get_connection(self):
            return self.conn

    connection_mod = types.ModuleType("database.connection")
    connection_mod.DatabaseConnection = TempDatabaseConnection
    restaurant_gateway_mod = types.ModuleType("gateways.restaurant_gateway")
    restaurant_gateway_mod.RestaurantGateway = object
    monkeypatch.setitem(sys.modules, "database.connection", connection_mod)
    monkeypatch.setitem(sys.modules, "gateways.restaurant_gateway", restaurant_gateway_mod)

    path = ROOT / "alrajhi_client" / "gateways" / "local" / "restaurant_gateway.py"
    spec = importlib.util.spec_from_file_location("phase304_local_restaurant_gateway", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.LocalRestaurantGateway()


def _table_payload(gateway, table_id):
    return next(table for table in gateway.list_tables() if int(table["id"]) == int(table_id))


def test_runtime_acceptance_contract_sequence_and_pure_state_snapshots():
    from alrajhi_client.features.restaurant.restaurant_runtime_acceptance import (
        acceptance_required_guards,
        acceptance_step_keys,
        accepted_runtime_state_names,
        kitchen_send_is_idempotent,
        payment_snapshot,
        runtime_state_snapshot,
    )

    assert acceptance_step_keys() == (
        "open_table",
        "add_order_lines",
        "send_to_kitchen",
        "kitchen_progress",
        "record_payment",
        "checkout",
        "print_receipt",
        "release_table",
    )
    assert "checkout_requires_fully_paid_bill" in acceptance_required_guards()
    assert kitchen_send_is_idempotent({"tickets": [{"id": 1}]}, {"tickets": [], "message": "no_new_lines"}) is True
    assert payment_snapshot("20", "5")["remaining"] == "15"
    assert payment_snapshot("20", "20")["can_checkout"] is True

    names = accepted_runtime_state_names()
    snapshot = runtime_state_snapshot([
        {"kitchen_status": "served", "quantity": "2", "unit_price": "10"},
    ], total="20", paid="0", session_status="open", base_table_status="occupied")
    assert snapshot["order_state"] == names["payment_due"]
    assert snapshot["table_state"] == names["table_payment"]
    assert snapshot["can_checkout"] is False


def test_local_gateway_accepts_full_restaurant_runtime_flow_without_duplication(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    table = gateway.list_tables()[0]
    session = gateway.open_table(table["id"], guests=2, waiter_id="waiter-1")
    line = gateway.add_order_line(session["id"], item_name="Burger", quantity="2", unit_price="7.50")

    assert line["kitchen_status"] == "new"
    assert _table_payload(gateway, table["id"])["active_order_state"] == "editing"

    first_send = gateway.send_to_kitchen(session["id"], notes="first KOT")
    repeat_send = gateway.send_to_kitchen(session["id"], notes="repeat should be empty")
    assert len(first_send["tickets"]) == 1
    assert repeat_send == {"tickets": [], "ticket": None, "lines": [], "message": "no_new_lines"}
    assert len(gateway.list_kitchen_tickets(status="all")) == 1

    ticket_id = first_send["ticket"]["id"]
    gateway.update_kitchen_ticket_status(ticket_id, "preparing")
    assert _table_payload(gateway, table["id"])["ui_status"] == "kitchen"
    gateway.update_kitchen_ticket_status(ticket_id, "ready")
    assert _table_payload(gateway, table["id"])["ui_status"] == "ready"
    gateway.update_kitchen_ticket_status(ticket_id, "served")
    assert _table_payload(gateway, table["id"])["ui_status"] == "payment"

    try:
        gateway.checkout_session(session["id"], paid_amount="0", payment_method="cash")
    except ValueError as exc:
        assert "fully paid" in str(exc).lower()
    else:
        raise AssertionError("Restaurant checkout must be blocked before full payment")

    partial = gateway.record_payment(session["id"], amount="5", payment_method="cash")
    assert partial["remaining"] == "10.00"
    try:
        gateway.checkout_session(session["id"], paid_amount="0", payment_method="cash")
    except ValueError as exc:
        assert "fully paid" in str(exc).lower()
    else:
        raise AssertionError("Partial restaurant payment must not close the table")

    final_payment = gateway.record_payment(session["id"], amount="999", payment_method="card")
    assert final_payment["applied_amount"] == "10.00"
    assert final_payment["remaining"] in {"0", "0.00"}
    closed = gateway.checkout_session(session["id"], paid_amount="0", payment_method="mixed")

    assert closed["status"] == "closed"
    assert closed["invoice_reference"].startswith("RST-")
    assert closed["paid_amount"] == "15.00"
    table_after = _table_payload(gateway, table["id"])
    assert table_after["status"] == "free"
    readiness = gateway.restaurant_production_readiness()
    assert readiness["ready"] is True
    assert readiness["diagnostics"]["open_sessions"] == 0
    assert readiness["diagnostics"]["new_unsent_lines"] == 0


def test_print_queue_acceptance_and_central_bridge_contract(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    table = gateway.list_tables()[0]
    session = gateway.open_table(table["id"])
    gateway.add_order_line(session["id"], item_name="Tea", quantity="1", unit_price="2")
    sent = gateway.send_to_kitchen(session["id"])
    ticket_id = sent["ticket"]["id"]

    job = gateway.queue_ticket_print(ticket_id, job_type="kot")
    assert job["ticket_id"] == ticket_id
    assert job["status"] == "queued"
    assert gateway.restaurant_production_readiness()["diagnostics"]["queued_print_jobs"] == 1
    printed = gateway.mark_print_job_done(job["job_id"])
    assert printed["status"] == "printed"
    assert gateway.restaurant_production_readiness()["diagnostics"]["queued_print_jobs"] == 0

    bridge = (ROOT / "alrajhi_client" / "features" / "restaurant" / "restaurant_printing_bridge.py").read_text(encoding="utf-8")
    widget = (ROOT / "alrajhi_client" / "views" / "restaurant" / "restaurant_pos_widget.py").read_text(encoding="utf-8")
    assert "restaurant_receipt_print" in bridge
    assert "restaurant_kitchen_ticket_print" in bridge
    assert "restaurant_printing_bridge.receipt_print" in widget
    assert "restaurant_printing_bridge.kitchen_ticket_print" in widget


def test_phase304_registered_and_money_display_contract_is_preserved():
    gate = (ROOT / "alrajhi_client" / "workspace" / "quality" / "release_gate_contract.py").read_text(encoding="utf-8")
    model = (ROOT / "alrajhi_client" / "features" / "restaurant" / "restaurant_order_model.py").read_text(encoding="utf-8")
    widget = (ROOT / "alrajhi_client" / "views" / "restaurant" / "restaurant_pos_widget.py").read_text(encoding="utf-8")

    assert '(304, "RESTAURANT_RUNTIME_ACCEPTANCE")' in gate
    assert "tests/test_phase304_restaurant_runtime_acceptance.py" in gate
    assert "restaurant_runtime_acceptance" in gate
    assert (ROOT / "PHASE304_RESTAURANT_RUNTIME_ACCEPTANCE.md").exists()
    assert "policy_for(currency_code=self.display_currency).format_money" in model
    assert "currency.format_display_amount(currency.to_display(_dec(value)))" in widget
