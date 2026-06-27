# -*- coding: utf-8 -*-
"""Phase 391 contract: item delete explains active BOM blockers by recipe name.

A material may remain blocked after invoices and production orders are deleted or
cancelled because an active BOM recipe is still master data.  This phase prevents
opaque messages such as bom_line=2 by resolving concrete BOM ids/product names and
adding an actionable resolution path.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Phase391Check:
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


def item_delete_bom_usage_resolver_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    db_path = "alrajhi_client/database/connection.py"
    gw_contract_path = "alrajhi_client/gateways/product_gateway.py"
    local_gw_path = "alrajhi_client/gateways/local/product_gateway.py"
    remote_gw_path = "alrajhi_client/gateways/remote/product_gateway.py"
    service_path = "alrajhi_client/core/services/product_service.py"

    db_src = _read(db_path, base) if _exists(db_path, base) else ""
    gw_src = _read(gw_contract_path, base) if _exists(gw_contract_path, base) else ""
    local_src = _read(local_gw_path, base) if _exists(local_gw_path, base) else ""
    remote_src = _read(remote_gw_path, base) if _exists(remote_gw_path, base) else ""
    service_src = _read(service_path, base) if _exists(service_path, base) else ""

    rows: List[Phase391Check] = []
    rows.append(Phase391Check(
        "bom_component_refs_resolved",
        "materials",
        "Material delete resolves BOM component blockers to concrete recipe/product names",
        db_path,
        "def _get_item_bom_component_refs" in db_src
        and "JOIN bom b ON b.id = bl.bom_id" in db_src
        and "COALESCE(p.name" in db_src
        and "line_count" in db_src,
        "A bom_line count alone is not enough for a user to fix the blocker",
    ))
    rows.append(Phase391Check(
        "bom_product_refs_resolved",
        "materials",
        "Material delete resolves BOM product blockers when the material is the finished product",
        db_path,
        "def _get_item_bom_product_refs" in db_src
        and "WHERE b.product_id=? AND b.user_id=?" in db_src
        and "component_count" in db_src,
        "The product side of BOM must be explained too",
    ))
    rows.append(Phase391Check(
        "delete_message_contains_recipe_resolution",
        "ux",
        "Delete-item blocker message names recipes and tells the user to edit/delete the BOM recipe",
        db_path,
        "وصفات تصنيع تستخدم هذه المادة كمكوّن" in db_src
        and "افتح التصنيع > الوصفات" in db_src
        and "احذف سطر المادة" in db_src
        and "Phase391" in db_src,
        "The resolution must be actionable, not only diagnostic",
    ))
    rows.append(Phase391Check(
        "usage_summary_carries_bom_refs_without_breaking_total",
        "quality",
        "Usage summary carries bom refs while blocking_total sums only numeric blockers",
        db_path,
        "'bom_product_refs': self._get_item_bom_product_refs" in db_src
        and "'bom_component_refs': self._get_item_bom_component_refs" in db_src
        and "sum(value for value in summary.values() if isinstance(value, int))" in db_src,
        "List-valued details must not corrupt blocking_total",
    ))
    rows.append(Phase391Check(
        "product_gateway_exposes_bom_usage_boundary",
        "architecture",
        "Product gateway/service expose a BOM usage resolver without UI SQL",
        gw_contract_path,
        "def bom_usage(self, item_id: int)" in gw_src
        and "def bom_usage(self, item_id: int)" in local_src
        and "get_item_bom_usage(item_id)" in local_src
        and "get_item_bom_usage" in remote_src
        and "def item_bom_usage" in service_src,
        "UI/application code should use product gateway/service boundaries",
    ))
    rows.append(Phase391Check(
        "delete_block_no_raw_bom_line_leakage",
        "ux",
        "The delete_item raise block does not leak raw bom_line/invoice_line identifiers",
        db_path,
        "def delete_item" in db_src
        and "bom_line" not in db_src.split("def delete_item", 1)[1].split("def get_item_by_id", 1)[0]
        and "invoice_line" not in db_src.split("def delete_item", 1)[1].split("def get_item_by_id", 1)[0],
        "Users must see business language, not physical table names",
    ))
    return [row.to_row() for row in rows]


def item_delete_bom_usage_resolver_summary(root: Path | None = None) -> Dict[str, object]:
    rows = item_delete_bom_usage_resolver_matrix(root)
    failed = [row for row in rows if not row["status"]]
    return {
        "phase": 391,
        "checks": len(rows),
        "failures": len(failed),
        "ready": not failed,
        "failed_keys": [str(row["key"]) for row in failed],
    }


__all__ = [
    "item_delete_bom_usage_resolver_matrix",
    "item_delete_bom_usage_resolver_summary",
]
