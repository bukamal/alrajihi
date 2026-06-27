# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_phase391_bom_component_blockers_are_resolved_to_recipe_names():
    src = read("alrajhi_client/database/connection.py")
    assert "def _get_item_bom_component_refs" in src
    assert "JOIN bom b ON b.id = bl.bom_id" in src
    assert "LEFT JOIN items p ON p.id = b.product_id" in src
    assert "product_name" in src
    assert "line_count" in src


def test_phase391_bom_product_blockers_are_resolved_too():
    src = read("alrajhi_client/database/connection.py")
    assert "def _get_item_bom_product_refs" in src
    assert "WHERE b.product_id=? AND b.user_id=?" in src
    assert "component_count" in src
    assert "as_product" in src
    assert "as_component" in src


def test_phase391_delete_message_is_actionable_and_not_raw_sql_names():
    src = read("alrajhi_client/database/connection.py")
    assert "وصفات تصنيع تستخدم هذه المادة كمكوّن" in src
    assert "وصفات تصنيع يكون فيها هذا الصنف منتجًا نهائيًا" in src
    assert "افتح التصنيع > الوصفات" in src
    assert "احذف سطر المادة" in src
    delete_block = src.split("def delete_item", 1)[1].split("def get_item_by_id", 1)[0]
    assert "bom_line" not in delete_block
    assert "invoice_line" not in delete_block


def test_phase391_bom_refs_do_not_break_blocking_total():
    src = read("alrajhi_client/database/connection.py")
    assert "'bom_product_refs': self._get_item_bom_product_refs" in src
    assert "'bom_component_refs': self._get_item_bom_component_refs" in src
    assert "sum(value for value in summary.values() if isinstance(value, int))" in src


def test_phase391_gateway_and_service_boundary_exist():
    assert "def bom_usage(self, item_id: int)" in read("alrajhi_client/gateways/product_gateway.py")
    assert "get_item_bom_usage(item_id)" in read("alrajhi_client/gateways/local/product_gateway.py")
    assert "get_item_bom_usage" in read("alrajhi_client/gateways/remote/product_gateway.py")
    assert "def item_bom_usage" in read("alrajhi_client/core/services/product_service.py")


def test_phase391_guard_contract_ready_and_release_gate_registered():
    from workspace.quality.item_delete_bom_usage_resolver_contract import item_delete_bom_usage_resolver_summary

    summary = item_delete_bom_usage_resolver_summary(ROOT)
    assert summary["ready"], summary
    assert summary["checks"] >= 6
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert "item_delete_bom_usage_resolver" in gate
    assert "tools/phase391_item_delete_bom_usage_resolver_guard.py" in gate
    assert '(391, "item_delete_bom_usage_resolver")' in gate
    assert (ROOT / "PHASE391_ITEM_DELETE_BOM_USAGE_RESOLVER.md").exists()
