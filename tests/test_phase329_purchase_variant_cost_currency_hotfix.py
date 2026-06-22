# -*- coding: utf-8 -*-
from decimal import Decimal
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "alrajhi_client") not in sys.path:
    sys.path.insert(0, str(ROOT / "alrajhi_client"))


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase329_purchase_variant_cost_guard_is_narrow_and_purchase_specific():
    model = text("alrajhi_client/features/transactions/grids/transaction_line_model.py")
    assert "def _apparel_variant_price_guard" in model
    assert 'if not item.get(inherit_key):' in model
    assert '"_apparel_variant_inherits_purchase_price"' in model
    assert 'price_key in purchase_like_keys' in model
    assert 'fixed >= (ratio * ratio)' in model
    assert 'fixed = fixed / ratio' in model
    assert 'return self._money(fixed)' in model
    # The guard must be applied before the line chooses explicit/base prices.
    assert 'explicit_price = self._apparel_variant_price_guard(item, explicit_price, price_key)' in model
    assert 'base_candidate = self._apparel_variant_price_guard(item, base_candidate, price_key)' in model


def test_phase329_explicit_variant_prices_are_not_collapsed():
    model = text("alrajhi_client/features/transactions/grids/transaction_line_model.py")
    guard_body = model.split("def _apparel_variant_price_guard", 1)[1].split("def set_item", 1)[0]
    assert 'if not item.get(inherit_key):' in guard_body
    assert 'return value' in guard_body
    doc = text("PHASE329_PURCHASE_VARIANT_COST_CURRENCY_HOTFIX.md")
    assert "Keep explicit variant prices untouched" in doc


def test_phase329_transaction_rows_mark_inherited_apparel_purchase_prices():
    doc = text("alrajhi_client/features/transactions/transaction_document_tab.py")
    assert '"_apparel_variant_inherits_purchase_price": inherits_purchase_price' in doc
    assert 'matched_variant.get("cost_price") in (None, "")' in doc
    model = text("alrajhi_client/features/transactions/grids/transaction_line_model.py")
    assert "def _apparel_variant_price_guard" in model
    assert "3,920,000,000,000 instead of 20,000" in model


def test_phase329_release_gate_registered_and_documented():
    gate = text("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert '(329, "PURCHASE_VARIANT_COST_CURRENCY_HOTFIX")' in gate
    assert 'tests/test_phase329_purchase_variant_cost_currency_hotfix.py' in gate
    assert (ROOT / "PHASE329_PURCHASE_VARIANT_COST_CURRENCY_HOTFIX.md").exists()
