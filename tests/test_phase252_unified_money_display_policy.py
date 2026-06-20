# -*- coding: utf-8 -*-
"""Phase 252: UI/report/print surfaces share one money display policy.

The policy formats already-resolved display amounts.  It must not convert
currencies in presentation code, and it must suppress float/Decimal residues
before values reach grids, totals, POS/restaurant models, reports, and print.
"""
from __future__ import annotations

from pathlib import Path
import importlib.util
import py_compile
import sys

ROOT = Path(__file__).resolve().parents[1]


def _load_policy():
    path = ROOT / "alrajhi_client" / "core" / "money_display_policy.py"
    spec = importlib.util.spec_from_file_location("phase252_money_display_policy", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_money_display_policy_compiles_without_pyqt():
    py_compile.compile(str(ROOT / "alrajhi_client" / "core" / "money_display_policy.py"), doraise=True)
    py_compile.compile(str(ROOT / "alrajhi_client" / "currency.py"), doraise=True)
    py_compile.compile(str(ROOT / "alrajhi_client" / "utils.py"), doraise=True)


def test_policy_formats_syp_display_money_without_residue():
    module = _load_policy()
    policy = module.MoneyDisplayPolicy(currency_code="SYP", currency_symbol="ل.س", decimals=2)

    assert policy.format_money("14999.999999999999") == "15,000.00 ل.س"
    assert policy.format_money("300000.000000000000") == "300,000.00 ل.س"
    assert policy.format_money("549999.999999999999999999") == "550,000.00 ل.س"
    assert policy.format_money("1E-22-") == "0.00 ل.س"


def test_policy_respects_explicit_document_currency_without_conversion():
    module = _load_policy()
    assert module.format_money(30000, "SYP", payload={"display_currency": "USD", "currency_decimals": "2"}) == "30,000.00 ل.س"
    assert module.format_money(30000, "USD", payload={"display_currency": "SYP", "currency_decimals": "2"}) == "30,000.00 $"


def test_policy_formats_quantities_separately_from_money():
    module = _load_policy()
    policy = module.MoneyDisplayPolicy(currency_code="SYP", currency_symbol="ل.س", decimals=2)
    assert policy.format_quantity("10.000000") == "10"
    assert policy.format_quantity("10.500000") == "10.5"
    assert policy.format_for_key("unit_price", 15000) == "15,000.00 ل.س"
    assert policy.format_for_key("quantity", "10.000000") == "10"


def test_policy_normalizes_arabic_digits_and_trailing_minus():
    module = _load_policy()
    policy = module.MoneyDisplayPolicy(currency_code="SYP", currency_symbol="ل.س", decimals=2)
    assert policy.format_money("١٥٠٠٠٫٠٠".replace("٫", ".")) == "15,000.00 ل.س"
    assert policy.format_money("1E-22-") == "0.00 ل.س"


def test_core_surfaces_delegate_to_unified_money_policy_static_guard():
    expected_files = [
        ROOT / "alrajhi_client" / "currency.py",
        ROOT / "alrajhi_client" / "utils.py",
        ROOT / "alrajhi_client" / "printing" / "print_templates.py",
        ROOT / "alrajhi_client" / "features" / "transactions" / "grids" / "transaction_line_model.py",
        ROOT / "alrajhi_client" / "features" / "transactions" / "components" / "transaction_totals_panel.py",
        ROOT / "alrajhi_client" / "features" / "pos" / "pos_line_model.py",
        ROOT / "alrajhi_client" / "features" / "restaurant" / "restaurant_order_model.py",
    ]
    for path in expected_files:
        text = path.read_text(encoding="utf-8")
        assert "money_display_policy" in text, f"{path} must use the unified money display policy"
