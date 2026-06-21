# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase305_restaurant_print_contract_is_explicit_and_browser_html_only():
    from features.restaurant.restaurant_unified_printing_contract import (
        RESTAURANT_PRINT_SURFACE,
        attach_unified_print_contract,
        payload_uses_unified_restaurant_printing,
        restaurant_print_document_keys,
        restaurant_unified_print_contract_snapshot,
    )

    assert RESTAURANT_PRINT_SURFACE == "browser_html"
    assert restaurant_print_document_keys() == ("receipt", "kitchen", "session_summary")

    snapshot = restaurant_unified_print_contract_snapshot()
    assert snapshot["receipt"]["document_type"] == "restaurant_receipt"
    assert snapshot["kitchen"]["template_method"] == "restaurant_kitchen_ticket_html"
    assert snapshot["session_summary"]["printing_service_method"] == "restaurant_session_summary_print"
    assert {row["surface"] for row in snapshot.values()} == {"browser_html"}

    payload = attach_unified_print_contract({"session": {"id": 7}}, "kot", {"printer": "Kitchen", "paper": "58mm"})
    assert payload["print_kind"] == "kitchen"
    assert payload["print_document_type"] == "restaurant_kitchen"
    assert payload["print_route"]["document_type"] == "restaurant_kitchen"
    assert payload["print_route"]["surface"] == "browser_html"
    assert payload_uses_unified_restaurant_printing(payload, "kitchen_ticket") is True


def test_phase305_settings_routes_cover_restaurant_aliases_and_printer_metadata():
    from features.restaurant.restaurant_settings_contract import restaurant_print_route

    settings = {
        "receipt_paper": "80mm",
        "kitchen_ticket_paper": "58mm",
        "session_summary_paper": "a4",
        "printing": {
            "restaurant_receipt_printer": "Front Counter",
            "restaurant_kitchen_printer": "Kitchen Thermal",
            "restaurant_session_summary_printer": "Manager Printer",
        },
    }

    assert restaurant_print_route("customer_receipt", settings) == {
        "document_type": "restaurant_receipt",
        "paper": "80mm",
        "printer": "Front Counter",
        "auto_print": False,
        "surface": "browser_html",
    }
    assert restaurant_print_route("kot", settings)["document_type"] == "restaurant_kitchen"
    assert restaurant_print_route("kitchen_ticket", settings)["printer"] == "Kitchen Thermal"
    assert restaurant_print_route("session", settings)["document_type"] == "restaurant_session_summary"
    assert restaurant_print_route("restaurant_session_summary", settings)["paper"] == "a4"


def test_phase305_restaurant_bridge_delegates_to_central_printing_service_only():
    bridge = (ROOT / "alrajhi_client/features/restaurant/restaurant_printing_bridge.py").read_text(encoding="utf-8")
    widget = (ROOT / "alrajhi_client/views/restaurant/restaurant_pos_widget.py").read_text(encoding="utf-8")
    service = (ROOT / "alrajhi_client/printing/printing_service.py").read_text(encoding="utf-8")

    assert "attach_unified_print_contract" in bridge
    assert "restaurant_print_document" in bridge
    assert "printing_service" in bridge
    assert "restaurant_receipt_print" in bridge
    assert "restaurant_kitchen_ticket_print" in bridge
    assert "restaurant_session_summary_print" in bridge
    assert "restaurant_receipt_html(" not in bridge
    assert "restaurant_kitchen_ticket_html(" not in bridge
    assert "restaurant_session_summary_html(" not in bridge
    assert "open_html_in_browser" not in bridge
    assert "QPrinter" not in bridge and "QTextDocument" not in bridge

    assert "restaurant_printing_bridge.receipt_print" in widget
    assert "restaurant_printing_bridge.kitchen_ticket_print" in widget
    assert "restaurant_printing_bridge.session_summary_print" in widget
    assert "printing_service" not in widget
    assert "print_templates" not in widget

    for method, doc_type in {
        "restaurant_receipt_print": "restaurant_receipt",
        "restaurant_kitchen_ticket_print": "restaurant_kitchen",
        "restaurant_session_summary_print": "restaurant_session_summary",
    }.items():
        assert f"def {method}" in service
        assert f"document_type='{doc_type}'" in service


def test_phase305_restaurant_sources_have_no_direct_qt_or_template_printing():
    blocked_tokens = (
        "QPrinter",
        "QPrintDialog",
        "QPrintPreviewDialog",
        "QPageSetupDialog",
        "QTextDocument().print",
        "from printing.print_templates import",
        "import printing.print_templates",
    )
    audited_roots = [
        ROOT / "alrajhi_client/views/restaurant",
        ROOT / "alrajhi_client/features/restaurant",
    ]
    for audited_root in audited_roots:
        for path in audited_root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for token in blocked_tokens:
                assert token not in text, f"{path.relative_to(ROOT)} contains direct print token {token!r}"


def test_phase305_registered_in_release_gate_and_documented():
    gate = (ROOT / "alrajhi_client/workspace/quality/release_gate_contract.py").read_text(encoding="utf-8")
    assert '(305, "RESTAURANT_UNIFIED_PRINTING_AUDIT")' in gate
    assert "tests/test_phase305_restaurant_unified_printing_audit.py" in gate
    assert "restaurant_unified_printing_audit" in gate
    assert (ROOT / "PHASE305_RESTAURANT_UNIFIED_PRINTING_AUDIT.md").exists()
