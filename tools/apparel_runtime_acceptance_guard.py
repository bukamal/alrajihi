# -*- coding: utf-8 -*-
"""Phase 322 apparel runtime acceptance guard.

This guard is intentionally source-based and PyQt-free.  It verifies that the
apparel workflow is closed through the existing product/warehouse/reporting
contracts and that reversal logic preserves color/size variant identity in
local and API modes.
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    runtime = read("alrajhi_client/features/apparel/apparel_runtime_acceptance.py")
    local_wh = read("alrajhi_client/database/repositories/warehouse_repo.py")
    server_wh = read("alrajhi_server/repositories/http_route_sql/warehouses.py")
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    i18n = read("alrajhi_client/i18n/translator.py")

    for step in (
        "create_base_item",
        "bulk_create_color_size_variants",
        "purchase_variant_stock",
        "scan_variant_barcode_for_sale",
        "post_sale_and_reduce_variant_stock",
        "return_same_variant",
        "transfer_variant_between_warehouses",
        "adjust_or_count_variant_stock",
        "review_apparel_report",
    ):
        require(step in runtime, f"missing apparel acceptance step: {step}")

    for guard in (
        "variant_barcode_resolves_exact_color_size",
        "invoice_line_keeps_variant_identity",
        "warehouse_movement_keeps_variant_identity",
        "reversal_preserves_variant_identity",
        "warehouse_transfer_preserves_variant_identity",
        "apparel_report_groups_by_color_size",
        "network_api_uses_same_variant_payload",
    ):
        require(guard in runtime, f"missing apparel acceptance guard: {guard}")

    require("variant_payloads" in local_wh and "variant_payloads.get(key" in local_wh, "local reverse_reference must retain variant payloads")
    require("vp['variant_id']" in local_wh and "vp['variant_color']" in local_wh and "vp['variant_size']" in local_wh, "local reverse key must include variant identity")
    require("reference_type IN (?, ?)" in server_wh, "server reverse_reference must consider prior reversals")
    require("payloads.get(key" in server_wh, "server reverse_reference must pass variant payloads")
    require("vp['variant_id']" in server_wh and "vp['variant_color']" in server_wh and "vp['variant_size']" in server_wh, "server reverse key must include variant identity")

    require('(322, "APPAREL_RUNTIME_ACCEPTANCE")' in gate, "phase 322 doc missing from release gate")
    require('(322, "apparel_runtime_acceptance")' in gate, "phase 322 test missing from release gate")
    require("tests/test_phase322_apparel_runtime_acceptance.py" in gate, "phase 322 test path missing from release gate")
    require((ROOT / "PHASE322_APPAREL_RUNTIME_ACCEPTANCE.md").exists(), "phase 322 markdown missing")
    require("SKU" not in i18n, "visible translations must not expose SKU")
    print("Phase 322 apparel runtime acceptance guard: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
