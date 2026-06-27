# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_phase390_item_usage_counts_only_active_parent_documents():
    src = read("alrajhi_client/database/connection.py")
    assert "Phase390 separates active references" in src
    assert "FROM invoice_lines il" in src
    assert "JOIN invoices i ON i.id = il.invoice_id" in src
    assert "i.deleted_at IS NULL" in src
    assert "COALESCE(UPPER(i.workflow_status), '') <> 'CANCELLED'" in src
    assert "active_invoice_lines" in src


def test_phase390_cancelled_production_not_counted_as_blocker():
    src = read("alrajhi_client/database/connection.py")
    assert "active_order_filter" in src
    assert "COALESCE(LOWER(po.status), '') NOT IN ('cancelled', 'deleted', 'void')" in src
    assert "JOIN production_orders po ON po.id = pc.order_id" in src
    assert "JOIN production_orders po ON po.id = po2.order_id" in src
    assert "active_production_consumptions" in src
    assert "active_production_outputs" in src


def test_phase390_inventory_movement_blockers_follow_active_sources():
    src = read("alrajhi_client/database/connection.py")
    assert "im.movement_type IN ('purchase','sale')" in src
    assert "im.movement_type = 'sales_return'" in src
    assert "im.movement_type = 'purchase_return'" in src
    assert "im.movement_type IN ('production_consume','production_out')" in src
    assert "WHERE po.id = im.reference_id AND po.user_id = im.user_id" in src


def test_phase390_error_message_is_user_facing_not_raw_table_names():
    src = read("alrajhi_client/database/connection.py")
    delete_block = src.split("def delete_item", 1)[1].split("def get_item_by_id", 1)[0]
    assert "_format_item_usage_details" in src
    assert "لا يمكن حذف المادة لأنها مرتبطة بعمليات نشطة" in delete_block
    assert "invoice_lines" not in delete_block
    assert "bom_lines" not in delete_block
    assert "أسطر فواتير نشطة" in src
    assert "أسطر BOM تستخدم المادة كمكوّن" in src


def test_phase390_guard_contract_ready_and_release_gate_registered():
    from workspace.quality.item_delete_active_usage_contract import item_delete_active_usage_summary

    summary = item_delete_active_usage_summary(ROOT)
    assert summary["ready"], summary
    assert summary["checks"] >= 6
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert "item_delete_active_usage" in gate
    assert "tools/phase390_item_delete_active_usage_guard.py" in gate
    assert '(390, "item_delete_active_usage")' in gate
    assert (ROOT / "PHASE390_ITEM_DELETE_ACTIVE_USAGE.md").exists()
