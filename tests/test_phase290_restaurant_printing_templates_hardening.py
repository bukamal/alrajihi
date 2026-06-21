from pathlib import Path


def _sample_payload():
    return {
        "currency": "SYP",
        "session": {
            "id": 42,
            "table_name": "Table 7",
            "guests": 3,
            "opened_at": "2026-01-01 12:00",
            "closed_at": "2026-01-01 13:00",
            "waiter_name": "Ali",
            "order_state": "paid",
            "lines": [
                {"item_name": "Pizza", "quantity": "2", "unit": "pcs", "unit_price": "30000", "total": "60000", "kitchen_status": "ready"},
                {"item_name": "Tea", "quantity": "1", "unit": "cup", "unit_price": "5000", "total": "5000", "kitchen_status": "served"},
            ],
            "payments": [
                {"payment_method": "cash", "amount": "30000", "created_at": "2026-01-01 12:50"},
                {"payment_method": "card", "amount": "35000", "created_at": "2026-01-01 12:52"},
            ],
        },
        "balance": {"subtotal": "65000", "discount_amount": "0", "service_charge_amount": "0", "tax_amount": "0", "total": "65000", "paid": "65000", "remaining": "0"},
        "split_bills": [{"name": "Guest 1", "total": "30000", "paid_amount": "30000", "remaining_amount": "0", "status": "paid"}],
    }


def test_phase290_restaurant_receipt_formats_money_and_payments():
    from printing.print_templates import restaurant_receipt_html

    html = restaurant_receipt_html(_sample_payload(), paper="thermal80")
    assert "إيصال مطعم" in html or "Restaurant Receipt" in html
    assert "65,000.00 ل.س" in html or "65,000" in html
    assert "Pizza" in html and "Tea" in html
    assert "cash" not in html.lower() or "نقد" in html or "Cash" in html
    assert "Guest 1" in html
    assert "1E-" not in html


def test_phase290_kitchen_ticket_omits_prices_and_payment_data():
    from printing.print_templates import restaurant_kitchen_ticket_html

    html = restaurant_kitchen_ticket_html({
        "id": 7,
        "table_name": "Table 7",
        "station_name": "Hot",
        "status": "sent",
        "elapsed_minutes": 12,
        "is_overdue": True,
        "lines": [
            {"item_name": "Pizza", "quantity": "2", "unit": "pcs", "notes": "No onion", "unit_price": "30000", "total": "60000"},
        ],
    }, paper="thermal80")
    assert "تذكرة المطبخ" in html or "Kitchen Ticket" in html
    assert "Pizza" in html and "No onion" in html
    assert "30000" not in html and "60,000" not in html and "ل.س" not in html
    assert "payment" not in html.lower()


def test_phase290_session_summary_template_renders_and_service_methods_are_present():
    from printing.print_templates import restaurant_session_summary_html

    html = restaurant_session_summary_html(_sample_payload(), paper="thermal80")
    assert "ملخص جلسة المطعم" in html or "Restaurant Session Summary" in html
    assert "65,000" in html

    root = Path(__file__).resolve().parents[1]
    service = (root / "alrajhi_client/printing/printing_service.py").read_text(encoding="utf-8")
    bridge = (root / "alrajhi_client/features/restaurant/restaurant_printing_bridge.py").read_text(encoding="utf-8")
    assert "def restaurant_session_summary_print" in service
    assert "def session_summary_print" in bridge


def test_phase290_restaurant_printing_contract_sources_are_wired():
    root = Path(__file__).resolve().parents[1]
    service = (root / "alrajhi_client/printing/printing_service.py").read_text(encoding="utf-8")
    bridge = (root / "alrajhi_client/features/restaurant/restaurant_printing_bridge.py").read_text(encoding="utf-8")
    templates = (root / "alrajhi_client/printing/print_templates.py").read_text(encoding="utf-8")
    settings = (root / "alrajhi_client/core/services/settings_service.py").read_text(encoding="utf-8")
    assert 'require_template("restaurant_session_summary_html")' in service
    assert "session_summary_payload" in bridge
    assert "queue_ticket_print" in bridge
    assert "def restaurant_session_summary_html" in templates
    assert "restaurant/session_summary_paper" in settings
