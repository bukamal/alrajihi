# -*- coding: utf-8 -*-
from pathlib import Path

from alrajhi_client.features.restaurant.cafe_runtime_acceptance import (
    cafe_acceptance_required_guards,
    cafe_acceptance_step_keys,
    cafe_barista_send_is_idempotent,
    cafe_checkout_allowed,
    cafe_hidden_restaurant_sections,
    cafe_payment_snapshot,
    cafe_preparation_note,
    cafe_print_payload_is_unified,
    cafe_quick_order_visibility,
    cafe_shift_acceptance,
    cafe_visible_workspace_sections,
)
from alrajhi_client.features.restaurant.restaurant_unified_printing_contract import (
    attach_unified_print_contract,
    normalize_restaurant_print_kind,
    restaurant_print_document,
)

ROOT = Path(__file__).resolve().parents[1]


def test_phase311_cafe_runtime_acceptance_flow_and_workspace_contract():
    steps = cafe_acceptance_step_keys()
    assert steps == (
        "open_quick_order",
        "customize_drink",
        "send_to_barista",
        "barista_progress",
        "record_payment",
        "print_receipt",
        "close_order",
        "shift_report",
    )
    guards = cafe_acceptance_required_guards()
    assert "cafe_order_uses_hidden_engine_table" in guards
    assert "cafe_print_uses_browser_html_bridge" in guards
    assert "cafe_shift_closes_only_when_clear" in guards
    assert "quick_order" in cafe_visible_workspace_sections()
    assert "barista" in cafe_visible_workspace_sections()
    assert "table_map" in cafe_hidden_restaurant_sections()
    assert "guest_count_required" in cafe_hidden_restaurant_sections()


def test_phase311_cafe_quick_order_is_tableless_in_ui_but_engine_safe():
    session = {"order_type": "cafe_quick_order", "table_name": "Cafe", "hidden_table": True}
    visibility = cafe_quick_order_visibility(session)
    assert visibility["is_cafe_order"] is True
    assert visibility["uses_hidden_engine_table"] is True
    assert visibility["show_table_map"] is False
    assert visibility["requires_guest_count"] is False


def test_phase311_cafe_payment_checkout_and_barista_idempotency():
    balance = cafe_payment_snapshot("12.50", "12.50")
    assert balance["remaining"] in {"0", "0.00"}
    assert balance["can_checkout"] is True
    assert cafe_checkout_allowed("12.50", "12.50") is True
    assert cafe_checkout_allowed("12.50", "10.00") is False
    assert cafe_checkout_allowed("12.50", "12.50", has_active_barista_tickets=True) is False
    assert cafe_barista_send_is_idempotent(
        {"tickets": [{"id": 1}]}, {"tickets": [], "message": "no_new_lines"}
    ) is True


def test_phase311_cafe_preparation_note_keeps_size_addons_and_notes():
    note = cafe_preparation_note(
        "no sugar",
        size={"name": "Large", "price_delta": "1"},
        modifiers=[{"name": "Extra shot", "price_delta": "0.50"}],
    )
    assert note == "Large | Extra shot | no sugar"


def test_phase311_cafe_print_aliases_use_restaurant_unified_browser_surface():
    assert normalize_restaurant_print_kind("cafe_receipt") == "receipt"
    assert normalize_restaurant_print_kind("barista_ticket") == "kitchen"
    assert normalize_restaurant_print_kind("cafe_session_summary") == "session_summary"
    assert restaurant_print_document("cafe_receipt").document_type == "restaurant_receipt"
    assert restaurant_print_document("barista_ticket").document_type == "restaurant_kitchen"
    receipt_payload = attach_unified_print_contract({}, "cafe_receipt", {})
    barista_payload = attach_unified_print_contract({}, "barista_ticket", {})
    assert cafe_print_payload_is_unified(receipt_payload, "cafe_receipt") is True
    assert cafe_print_payload_is_unified(barista_payload, "barista_ticket") is True
    assert receipt_payload["print_surface"] == "browser_html"
    assert barista_payload["print_route"]["surface"] == "browser_html"


def test_phase311_cafe_shift_acceptance_blocks_unclear_shift():
    clear = {"operational_controls": {"can_close_shift": True, "blockers": []}}
    blocked = {"operational_controls": {"can_close_shift": False, "blockers": ["open_orders", "queued_print_jobs"]}}
    assert cafe_shift_acceptance(clear)["can_close_shift"] is True
    result = cafe_shift_acceptance(blocked)
    assert result["can_close_shift"] is False
    assert result["blockers"] == ("open_orders", "queued_print_jobs")


def test_phase311_registered_in_release_gate_and_documented():
    gate = (ROOT / "alrajhi_client/workspace/quality/release_gate_contract.py").read_text(encoding="utf-8")
    assert '(311, "cafe_runtime_acceptance")' in gate
    assert "tests/test_phase311_cafe_runtime_acceptance.py" in gate
    assert "cafe_runtime_acceptance" in gate
    assert (ROOT / "PHASE311_CAFE_RUNTIME_ACCEPTANCE.md").exists()
