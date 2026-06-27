# -*- coding: utf-8 -*-
"""Phase 390 contract: item delete guards count only active dependencies.

Invoices are soft-deleted in this project. Their detail rows remain for audit, so
material deletion must not be blocked by raw orphan-looking invoice_lines after a
parent invoice has deleted_at/status cancelled. Cancelled production orders follow
the same rule. Active BOM recipes still block because they are master data, not a
cancelled runtime operation.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Phase390Check:
    key: str
    category: str
    description: str
    path: str
    status: bool
    detail: str = ""

    def to_row(self) -> Dict[str, object]:
        return asdict(self)


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding="utf-8")


def _exists(path: str, root: Path | None = None) -> bool:
    return ((root or ROOT) / path).exists()


def item_delete_active_usage_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    path = "alrajhi_client/database/connection.py"
    src = _read(path, base) if _exists(path, base) else ""
    checks: List[Phase390Check] = []

    checks.append(Phase390Check(
        "invoice_lines_join_active_invoices",
        "materials",
        "Material delete counts invoice lines only through active parent invoices, not raw invoice_lines rows",
        path,
        "FROM invoice_lines il" in src and "JOIN invoices i ON i.id = il.invoice_id" in src and "i.deleted_at IS NULL" in src and "workflow_status" in src,
        "Soft-deleted/cancelled invoices must not keep blocking item archive/delete",
    ))
    checks.append(Phase390Check(
        "production_orders_exclude_cancelled",
        "manufacturing",
        "Cancelled production orders and their consumption/output rows do not block material delete",
        path,
        "active_order_filter" in src and "NOT IN ('cancelled', 'deleted', 'void')" in src and "JOIN production_orders po ON po.id = pc.order_id" in src and "JOIN production_orders po ON po.id = po2.order_id" in src,
        "Production detail rows must be joined to non-cancelled orders",
    ))
    checks.append(Phase390Check(
        "inventory_movements_follow_active_parent",
        "inventory",
        "Inventory movements tied to deleted invoices/cancelled production orders are not counted as active blockers",
        path,
        "im.movement_type IN ('purchase','sale')" in src and "EXISTS (" in src and "FROM production_orders po" in src and "im.movement_type IN ('production_consume','production_out')" in src,
        "Movement blockers must follow active source documents instead of raw movement counts",
    ))
    checks.append(Phase390Check(
        "returns_count_only_active_return_documents",
        "returns",
        "Return lines and return movements count only active, non-deleted return documents",
        path,
        "FROM sales_return_lines srl" in src and "JOIN sales_returns sr" in src and "FROM purchase_return_lines prl" in src and "JOIN purchase_returns pr" in src and "sr.deleted_at IS NULL" in src and "pr.deleted_at IS NULL" in src,
        "Deleted/cancelled returns should not block item archive/delete",
    ))
    checks.append(Phase390Check(
        "bom_remains_active_master_data_blocker",
        "manufacturing",
        "Active BOM recipe references remain blockers even when production orders are cancelled",
        path,
        "active_bom_lines" in src and "JOIN bom b ON b.id = bl.bom_id" in src and "active_bom_products" in src,
        "BOM is master data and must be removed/edited explicitly",
    ))
    checks.append(Phase390Check(
        "user_facing_error_message",
        "ux",
        "Delete item error uses Arabic user-facing labels instead of raw table names like invoice_line/bom_line",
        path,
        "_format_item_usage_details" in src and "أسطر فواتير نشطة" in src and "حركات مخزون نشطة" in src and "invoice_lines" not in src.split("def delete_item", 1)[1].split("def get_item_by_id", 1)[0],
        "The delete_item message must not leak raw database table names",
    ))
    return [c.to_row() for c in checks]


def item_delete_active_usage_summary(root: Path | None = None) -> Dict[str, object]:
    rows = item_delete_active_usage_matrix(root)
    failed = [row for row in rows if not row["status"]]
    return {
        "phase": 390,
        "checks": len(rows),
        "failures": len(failed),
        "ready": not failed,
        "failed_keys": [str(row["key"]) for row in failed],
    }


__all__ = [
    "item_delete_active_usage_matrix",
    "item_delete_active_usage_summary",
]
