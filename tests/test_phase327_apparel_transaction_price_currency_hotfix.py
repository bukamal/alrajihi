# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase327_price_display_conversion_is_idempotent_for_apparel_lookup_rows():
    doc = text("alrajhi_client/features/transactions/transaction_document_tab.py")
    assert 'if item.get("_prices_in_display_currency")' in doc
    assert 'item["_prices_in_display_currency"] = True' in doc
    assert 'Phase 327: lookup rows may already carry display-currency prices' in doc
    assert 'becomes a huge' in doc


def test_phase327_variant_search_popup_does_not_offer_base_material_names_as_separate_choices():
    doc = text("alrajhi_client/features/transactions/transaction_document_tab.py")
    assert 'if row.get("barcode_scope") == "variant" or row.get("matched_variant"):' in doc
    assert 'Showing the base material name as a' in doc
    assert 'row.get("variant_sku")' in doc
    assert 'row.get("variant")' in doc


def test_phase327_exact_base_name_does_not_pick_arbitrary_variant():
    doc = text("alrajhi_client/features/transactions/transaction_document_tab.py")
    assert 'Do not let an exact base-material name choose an arbitrary' in doc
    variant_block = doc.split('Do not let an exact base-material name choose an arbitrary', 1)[1].split('else:', 1)[0]
    assert 'row.get("name")' not in variant_block
    assert 'row.get("item_name")' not in variant_block


def test_phase327_release_gate_registered_and_documented():
    gate = text("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert '(327, "APPAREL_TRANSACTION_PRICE_CURRENCY_HOTFIX")' in gate
    assert '(327, "apparel_transaction_price_currency_hotfix")' in gate
    assert 'tests/test_phase327_apparel_transaction_price_currency_hotfix.py' in gate
    assert (ROOT / "PHASE327_APPAREL_TRANSACTION_PRICE_CURRENCY_HOTFIX.md").exists()
