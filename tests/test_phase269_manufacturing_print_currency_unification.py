# -*- coding: utf-8 -*-
"""Phase 269: manufacturing UI/print uses unified money and quantity formatting.

BOM and production-order printouts must not expose raw Decimal/scientific values
such as 0E+1 or 1E-22-, and manufacturing cost columns/panels must use the same
MoneyDisplayPolicy as invoices, returns, POS and reports.
"""
from __future__ import annotations

from pathlib import Path
import importlib.util
import py_compile
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _load_templates():
    sys.path.insert(0, str(CLIENT))
    try:
        path = CLIENT / "printing" / "print_templates.py"
        spec = importlib.util.spec_from_file_location("phase269_print_templates", path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        try:
            sys.path.remove(str(CLIENT))
        except ValueError:
            pass


def test_phase269_files_compile():
    for rel in [
        "alrajhi_client/printing/print_templates.py",
        "alrajhi_client/features/manufacturing/manufacturing_printing_bridge.py",
        "alrajhi_client/features/manufacturing/components/bom_summary_panel.py",
        "alrajhi_client/features/manufacturing/components/production_summary_panel.py",
        "alrajhi_client/features/manufacturing/components/production_lifecycle_summary_panel.py",
        "alrajhi_client/features/manufacturing/grids/bom_components_model.py",
        "alrajhi_client/features/manufacturing/grids/production_required_materials_model.py",
        "alrajhi_client/features/manufacturing/grids/production_lifecycle_model.py",
    ]:
        py_compile.compile(str(ROOT / rel), doraise=True)


def test_manufacturing_bom_print_formats_costs_quantities_and_currency():
    module = _load_templates()
    html = module.manufacturing_bom_html({
        "display_currency": "SYP",
        "bom": {"id": 2, "product_name": "طاولة", "quantity": "1.0000"},
        "lines": [{
            "item_name": "خشب",
            "quantity": "2.0000",
            "base_qty": "2.0000",
            "waste_percent": "0",
            "unit_cost": "0E+1",
            "total_cost": "14999.999999999999",
        }],
        "summary": {
            "material_cost": "14999.999999999999",
            "waste_cost": "1E-22-",
            "total_cost": "14999.999999999999",
            "base_qty": "5.0000",
            "unit_cost_output": "0E+1",
            "line_count": "3",
        },
    })
    assert "0E+1" not in html
    assert "1E-22" not in html
    assert "15,000.00 ل.س" in html
    assert "0.00 ل.س" in html
    assert "5" in html


def test_production_order_and_cost_report_print_format_money_values():
    module = _load_templates()
    payload = {
        "display_currency": "SYP",
        "order": {"id": 2, "product_name": "طاولة", "planned_qty": "1.0000", "produced_qty": "1.0000"},
        "consumptions": [{"item_name": "خشب", "consumed_qty": "2.0000", "unit_cost": "0E+1", "total_cost": "1E-22-"}],
        "outputs": [{"product_name": "طاولة", "produced_qty": "1.0000", "unit_cost": "14999.999999999999", "total_cost": "14999.999999999999"}],
        "reservations": [{"item_name": "دهان", "reserved_qty": "2.0000", "consumed_qty": "0", "remaining_qty": "2.0000"}],
    }
    html = module.production_order_html(payload)
    assert "0E+1" not in html
    assert "1E-22" not in html
    assert "15,000.00 ل.س" in html
    assert "0.00 ل.س" in html

    report_html = module.manufacturing_cost_report_html({
        "display_currency": "SYP",
        "order": payload["order"],
        "summary": {
            "consumption_cost": "1E-22-",
            "output_cost": "14999.999999999999",
            "variance_cost": "14999.999999999999",
            "produced_qty": "1.0000",
            "unit_cost": "0E+1",
        },
    })
    assert "0E+1" not in report_html
    assert "1E-22" not in report_html
    assert "15,000.00 ل.س" in report_html
    assert "0.00 ل.س" in report_html


def test_manufacturing_ui_components_delegate_to_money_display_policy():
    expected = [
        "alrajhi_client/features/manufacturing/components/bom_summary_panel.py",
        "alrajhi_client/features/manufacturing/components/production_lifecycle_summary_panel.py",
        "alrajhi_client/features/manufacturing/grids/bom_components_model.py",
        "alrajhi_client/features/manufacturing/grids/production_lifecycle_model.py",
        "alrajhi_client/features/manufacturing/grids/production_required_materials_model.py",
    ]
    for rel in expected:
        text = read(rel)
        assert "money_display_policy" in text, f"{rel} must use MoneyDisplayPolicy for manufacturing values"


def test_manufacturing_print_bridge_passes_currency_context():
    text = read("alrajhi_client/features/manufacturing/manufacturing_printing_bridge.py")
    assert "def _money_context" in text
    assert "display_currency" in text
    assert "payload.update(_money_context())" in text
