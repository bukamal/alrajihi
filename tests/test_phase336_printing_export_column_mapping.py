# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_phase336_column_output_resolves_print_and_export_keys_from_contracts():
    from workspace.tables import keys_for_output, columns_for_output, column_setting_key

    purchase_print = keys_for_output("purchase_invoices.lines", "print")
    sales_export = keys_for_output("sales_invoices.lines", "export")
    restaurant_print = keys_for_output("restaurant.order_lines", "print")
    cafe_print = keys_for_output("cafe.order_lines", "print")

    assert "cost" in purchase_print and "price" not in purchase_print
    assert {"barcode", "item", "variant", "qty", "price", "total"}.issubset(set(sales_export))
    assert "modifiers" not in restaurant_print
    assert "modifiers" in cafe_print and "notes" in cafe_print
    first = columns_for_output("apparel.variants", "print")[0]
    assert column_setting_key(first, "print").endswith("/printable")
    assert column_setting_key(first, "export").endswith("/exportable")


def test_phase336_custom_table_print_export_do_not_depend_on_hidden_display_columns():
    custom = read("alrajhi_client/views/custom_table_view.py")
    assert "from workspace.tables import keys_for_output" in custom
    assert "candidate_cols = display_cols if normalized == \"display\" else list(range(model.columnCount()))" in custom
    assert "Printing/exporting" in custom
    assert "self._columns_for_purpose('export')" in custom
    assert "self._columns_for_purpose('print')" in custom


def test_phase336_print_templates_consume_contract_tables_for_invoice_pos_restaurant():
    templates = read("alrajhi_client/printing/print_templates.py")
    trx_bridge = read("alrajhi_client/features/transactions/components/transaction_printing_bridge.py")

    assert "def _contract_table" in templates
    assert "from workspace.tables import columns_for_output" in templates
    assert "invoice.get(\"line_table_contract_id\")" in templates
    assert "purchase_invoices.lines" in templates
    assert "pos.lines" in templates
    assert "restaurant.order_lines" in templates
    assert "restaurant.kds_lines" in templates
    assert '"table_contract_id": table_contract_id' in trx_bridge
    assert '"line_table_contract_id": table_contract_id' in trx_bridge
    assert '"variant": row.get("variant")' in trx_bridge


def test_phase336_invoice_html_uses_purchase_cost_and_variant_contract_columns():
    from printing.print_templates import invoice_html

    html = invoice_html({
        "type": "purchase",
        "reference": "P-336",
        "line_table_contract_id": "purchase_invoices.lines",
        "currency": "SYP",
        "lines": [{
            "item_name": "قميص رجالي",
            "variant": "أبيض / L",
            "barcode": "VAR-001",
            "unit": "قطعة",
            "qty": 2,
            "cost": 20000,
            "total": 40000,
        }],
    })
    assert "قميص رجالي" in html
    assert "أبيض / L" in html
    assert "VAR-001" in html
    assert "40000" in html or "40,000" in html or "٤٠" in html
    assert "P-336" in html


def test_phase336_release_gate_registered_and_documented():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert '(336, "PRINTING_EXPORT_COLUMN_MAPPING")' in gate
    assert '(336, "printing_export_column_mapping")' in gate
    assert "tests/test_phase336_printing_export_column_mapping.py" in gate
    assert 'ReleaseGateCheck("printing_export_column_mapping"' in gate
    assert (ROOT / "PHASE336_PRINTING_EXPORT_COLUMN_MAPPING.md").exists()
