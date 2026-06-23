# -*- coding: utf-8 -*-
"""Runtime application sweep for universal table column contracts.

Phase 343 makes the column contract rollout measurable beyond the high-risk
invoice/restaurant/apparel screens.  The module stays PyQt-free so release
checks can confirm that every registered workspace table has a contract and
that legacy SmartTable identities resolve to those contracts before runtime.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping

from workspace.registry import PAGE_MANIFESTS
from workspace.tables.table_column_registry import (
    TABLE_COLUMN_CONTRACTS,
    TABLE_IDENTITY_CONTRACTS,
    table_column_contract_by_id,
)


@dataclass(frozen=True)
class RuntimeTableSweepRow:
    category: str
    key: str
    contract_id: str
    ok: bool
    detail: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "category": self.category,
            "key": self.key,
            "contract_id": self.contract_id,
            "ok": bool(self.ok),
            "detail": self.detail,
        }


def manifest_table_contract_rows() -> tuple[RuntimeTableSweepRow, ...]:
    rows: list[RuntimeTableSweepRow] = []
    for page_id, manifest in sorted(PAGE_MANIFESTS.items()):
        for spec in manifest.table_specs:
            cid = f"{page_id}.{spec.table_id}"
            contract = table_column_contract_by_id(cid)
            rows.append(RuntimeTableSweepRow(
                category="manifest_table",
                key=f"{page_id}.{spec.table_id}",
                contract_id=cid,
                ok=contract is not None,
                detail="registered" if contract is not None else "missing contract",
            ))
    return tuple(rows)


def identity_contract_rows() -> tuple[RuntimeTableSweepRow, ...]:
    rows: list[RuntimeTableSweepRow] = []
    for identity, cid in sorted(TABLE_IDENTITY_CONTRACTS.items()):
        contract = table_column_contract_by_id(cid)
        rows.append(RuntimeTableSweepRow(
            category="runtime_identity",
            key=identity,
            contract_id=cid,
            ok=contract is not None,
            detail="registered" if contract is not None else "alias points to missing contract",
        ))
    return tuple(rows)


def contract_runtime_sweep_rows() -> tuple[RuntimeTableSweepRow, ...]:
    rows: list[RuntimeTableSweepRow] = []
    rows.extend(manifest_table_contract_rows())
    rows.extend(identity_contract_rows())
    for cid, contract in sorted(TABLE_COLUMN_CONTRACTS.items()):
        rows.append(RuntimeTableSweepRow(
            category="contract_payload",
            key=cid,
            contract_id=cid,
            ok=bool(contract.columns) and bool(contract.default_visible_keys()) and (not contract.printable or bool(contract.default_printable_keys())) and (not contract.exportable or bool(contract.default_exportable_keys())),
            detail=f"columns={len(contract.columns)} display={len(contract.default_visible_keys())} print={len(contract.default_printable_keys())} export={len(contract.default_exportable_keys())}",
        ))
    return tuple(rows)


def validate_runtime_table_contract_sweep() -> Dict[str, list[str]]:
    issues: Dict[str, list[str]] = {}
    for row in contract_runtime_sweep_rows():
        if not row.ok:
            issues.setdefault(row.category, []).append(f"{row.key} -> {row.contract_id}: {row.detail}")
    # Every identity alias must use a stable non-empty contract id and no alias
    # should be accidental whitespace/casing-only duplication.
    normalized = {}
    for identity, cid in TABLE_IDENTITY_CONTRACTS.items():
        if not identity.strip() or not cid.strip():
            issues.setdefault("empty_identity_alias", []).append(f"{identity!r}:{cid!r}")
        low = identity.lower()
        if low in normalized and normalized[low] != identity:
            issues.setdefault("duplicate_identity_alias", []).append(f"{normalized[low]} / {identity}")
        normalized[low] = identity
    return issues


__all__ = [
    "RuntimeTableSweepRow",
    "contract_runtime_sweep_rows",
    "identity_contract_rows",
    "manifest_table_contract_rows",
    "validate_runtime_table_contract_sweep",
]
