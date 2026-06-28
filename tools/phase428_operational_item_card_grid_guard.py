#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

OUT_DIR = ROOT / "tools" / "audit_outputs"
MATRIX = OUT_DIR / "operational_item_card_grid_matrix.csv"


def read(rel: str) -> str:
    path = ROOT / rel
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def parses(rel: str) -> bool:
    try:
        ast.parse(read(rel))
        return True
    except SyntaxError:
        return False


def add(rows: list[dict[str, str]], key: str, category: str, path: str, ok: bool, detail: str) -> None:
    rows.append({"key": key, "category": category, "path": path, "status": "OK" if ok else "FAIL", "detail": detail})


def main() -> int:
    from workspace.quality.operational_item_card_grid_contract import (
        PHASE428_OPERATIONAL_ITEM_CARD_GRID_UNIFICATION,
        REQUIRED_SOURCES,
        operational_item_card_grid_matrix,
        operational_item_card_grid_summary,
    )

    rows: list[dict[str, str]] = []
    required = [
        "PHASE428_OPERATIONAL_ITEM_CARD_GRID_UNIFICATION.md",
        "alrajhi_client/workspace/quality/operational_item_card_grid_contract.py",
        "tools/phase428_operational_item_card_grid_guard.py",
        "tests/test_phase428_operational_item_card_grid.py",
        *REQUIRED_SOURCES,
    ]
    for rel in required:
        add(rows, f"exists::{rel}", "file", rel, (ROOT / rel).exists(), "required Phase428 file exists")
    for rel in required[1:]:
        if rel.endswith('.py'):
            add(rows, f"ast::{rel}", "syntax", rel, parses(rel), "source parses")

    add(rows, "contract_phase", "contract", required[1], PHASE428_OPERATIONAL_ITEM_CARD_GRID_UNIFICATION["phase"] == 428, "Phase428 contract declared")
    add(rows, "contract_owner", "contract", required[1], PHASE428_OPERATIONAL_ITEM_CARD_GRID_UNIFICATION["owner"] == "OperationalItemCardGrid", "shared operational item card grid owns card surface")
    add(rows, "contract_default_columns", "contract", required[1], PHASE428_OPERATIONAL_ITEM_CARD_GRID_UNIFICATION["default_columns"] == 3, "default material grid uses three columns")

    summary = operational_item_card_grid_summary(ROOT)
    add(rows, "summary_ready", "contract", required[1], bool(summary["ready"]), "Restaurant/Cafe surfaces use shared card grid while POS stays barcode/table-first")
    for row in operational_item_card_grid_matrix(ROOT):
        rows.append({
            "key": str(row["key"]),
            "category": "operational_item_card_grid",
            "path": str(row["path"]),
            "status": str(row["status"]),
            "detail": str(row["detail"]),
        })

    release = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    add(rows, "release_doc", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "PHASE428_OPERATIONAL_ITEM_CARD_GRID_UNIFICATION" in release, "Phase428 doc registered")
    add(rows, "release_test", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "tests/test_phase428_operational_item_card_grid.py" in release, "Phase428 test registered")
    add(rows, "release_check", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "operational_item_card_grid" in release and "phase=428" in release, "Phase428 release check registered")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with MATRIX.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["key", "category", "path", "status", "detail"])
        writer.writeheader(); writer.writerows(rows)

    failed = [row for row in rows if row["status"] != "OK"]
    print(f"Phase428 operational item card grid checks: {len(rows)} checks, failures={len(failed)}")
    print(f"Matrix: {MATRIX}")
    for row in failed:
        print(f"FAIL {row['key']}: {row['detail']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
