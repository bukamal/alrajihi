# -*- coding: utf-8 -*-
from pathlib import Path

from alrajhi_client.features.apparel.apparel_runtime_acceptance import (
    apparel_acceptance_required_guards,
    apparel_acceptance_step_keys,
    apparel_report_acceptance,
    barcode_lookup_acceptance,
    line_keeps_variant_identity,
    movement_keeps_variant_identity,
    reversal_keeps_variant_identity,
    scenario_snapshot,
    stock_delta_acceptance,
    transfer_keeps_variant_identity,
    variant_identity,
)

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase322_acceptance_sequence_closes_full_apparel_workflow():
    assert apparel_acceptance_step_keys() == (
        "create_base_item",
        "bulk_create_color_size_variants",
        "purchase_variant_stock",
        "scan_variant_barcode_for_sale",
        "post_sale_and_reduce_variant_stock",
        "return_same_variant",
        "transfer_variant_between_warehouses",
        "adjust_or_count_variant_stock",
        "review_apparel_report",
    )
    guards = apparel_acceptance_required_guards()
    assert "variant_barcode_resolves_exact_color_size" in guards
    assert "invoice_line_keeps_variant_identity" in guards
    assert "warehouse_movement_keeps_variant_identity" in guards
    assert "reversal_preserves_variant_identity" in guards
    assert "warehouse_transfer_preserves_variant_identity" in guards
    assert "network_api_uses_same_variant_payload" in guards
    assert "unified_printing_contract_is_not_bypassed" in guards


def test_phase322_variant_identity_helpers_validate_scan_line_movement_transfer_and_report():
    expected = {
        "variant_id": 17,
        "variant_color": "أسود",
        "variant_size": "L",
        "variant_sku": "TSH-BLK-L",
        "barcode_scope": "variant",
        "matched_barcode": "APP-17",
    }
    lookup = {
        "matched_variant": {"id": 17, "color": "أسود", "size": "L", "sku": "TSH-BLK-L", "barcode": "APP-17"},
        "barcode_scope": "variant",
    }
    assert barcode_lookup_acceptance(lookup, color="أسود", size="L") is True
    assert variant_identity(lookup)["variant_id"] == 17
    assert line_keeps_variant_identity({**expected, "quantity": "1"}, expected) is True
    assert movement_keeps_variant_identity({**expected, "movement_type": "invoice_sale_out"}, expected) is True
    assert transfer_keeps_variant_identity({**expected, "from_warehouse_id": 1, "to_warehouse_id": 2}, expected) is True
    assert stock_delta_acceptance("10", "-1", "9") is True
    report = {
        "summary": {},
        "variants": [{"variant_id": 17, "variant_color": "أسود", "variant_size": "L"}],
        "low_stock": [],
        "by_item": [],
        "by_color": [{"color": "أسود", "quantity": "9"}],
        "by_size": [{"size": "L", "quantity": "9"}],
    }
    assert apparel_report_acceptance(report, expected_variant_id=17) is True


def test_phase322_reversal_preserves_variant_identity_and_opposite_quantity():
    original = {
        "variant_id": 23,
        "variant_color": "أبيض",
        "variant_size": "M",
        "variant_sku": "SH-W-M",
        "barcode_scope": "variant",
        "matched_barcode": "APP-23",
        "quantity": "-2",
    }
    reversal = {
        "variant_id": 23,
        "variant_color": "أبيض",
        "variant_size": "M",
        "variant_sku": "SH-W-M",
        "barcode_scope": "variant",
        "matched_barcode": "APP-23",
        "quantity": "2",
    }
    wrong_size = {**reversal, "variant_size": "L"}
    assert reversal_keeps_variant_identity(original, reversal) is True
    assert reversal_keeps_variant_identity(original, wrong_size) is False


def test_phase322_local_and_server_reverse_reference_group_by_variant_identity():
    local_repo = text("alrajhi_client/database/repositories/warehouse_repo.py")
    server_repo = text("alrajhi_server/repositories/http_route_sql/warehouses.py")
    for source in (local_repo, server_repo):
        assert "Phase 322" in source
        assert "vp['variant_id']" in source
        assert "vp['variant_color']" in source
        assert "vp['variant_size']" in source
        assert "vp['variant_sku']" in source
        assert "vp['barcode_scope']" in source
        assert "vp['matched_barcode']" in source
    assert "variant_payloads" in local_repo
    assert "variant_payloads.get(key" in local_repo
    assert "reference_type IN (?, ?)" in server_repo
    assert "payloads.get(key" in server_repo


def test_phase322_no_visible_sku_term_and_runtime_guard_registered():
    i18n = text("alrajhi_client/i18n/translator.py")
    guard = text("tools/apparel_runtime_acceptance_guard.py")
    gate = text("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert "SKU" not in i18n
    assert "رمز المتغير" in i18n
    assert "Variant code" in i18n
    assert "Variantencode" in i18n
    assert "Phase 322 apparel runtime acceptance guard" in guard
    assert '(322, "APPAREL_RUNTIME_ACCEPTANCE")' in gate
    assert '(322, "apparel_runtime_acceptance")' in gate
    assert "tests/test_phase322_apparel_runtime_acceptance.py" in gate
    assert (ROOT / "PHASE322_APPAREL_RUNTIME_ACCEPTANCE.md").exists()


def test_phase322_scenario_snapshot_is_serializable_and_clear():
    snapshot = scenario_snapshot(item_name="قميص رجالي", color="أسود", size="L", quantity="9", warehouse_name="المستودع الرئيسي")
    assert snapshot == {
        "item_name": "قميص رجالي",
        "variant_color": "أسود",
        "variant_size": "L",
        "quantity": "9",
        "warehouse_name": "المستودع الرئيسي",
        "identity_label": "قميص رجالي / أسود / L",
    }
