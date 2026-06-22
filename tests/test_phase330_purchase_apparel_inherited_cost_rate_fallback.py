# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase330_purchase_cost_keys_use_purchase_inheritance_guard():
    model = text("alrajhi_client/features/transactions/grids/transaction_line_model.py")
    assert 'purchase_like_keys = {"purchase_price", "cost", "cost_price", "average_cost", "unit_cost"}' in model
    guard_body = model.split("def _apparel_variant_price_guard", 1)[1].split("def set_item", 1)[0]
    assert 'if price_key in purchase_like_keys' in guard_body
    assert '"_apparel_variant_inherits_purchase_price"' in guard_body


def test_phase330_storage_display_equal_still_uses_display_rate_fallback():
    model = text("alrajhi_client/features/transactions/grids/transaction_line_model.py")
    guard_body = model.split("def _apparel_variant_price_guard", 1)[1].split("def set_item", 1)[0]
    assert 'if storage == display:' not in guard_body
    assert 'currency.get_current_rate(display)' in guard_body
    assert 'some live installations keep storage/display both' in guard_body
    assert 'fixed >= (ratio * ratio)' in guard_body
    assert 'fixed = fixed / ratio' in guard_body


def test_phase330_release_gate_registered_and_documented():
    gate = text("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert '(330, "PURCHASE_APPAREL_INHERITED_COST_RATE_FALLBACK")' in gate
    assert 'tests/test_phase330_purchase_apparel_inherited_cost_rate_fallback.py' in gate
    assert (ROOT / "PHASE330_PURCHASE_APPAREL_INHERITED_COST_RATE_FALLBACK.md").exists()
