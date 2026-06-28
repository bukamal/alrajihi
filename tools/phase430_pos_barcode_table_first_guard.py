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
MATRIX = OUT_DIR / "pos_barcode_table_first_matrix.csv"


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
    from workspace.quality.pos_barcode_table_first_contract import (
        PHASE430_POS_BARCODE_TABLE_FIRST_LAYOUT,
        REQUIRED_SOURCES,
        pos_barcode_table_first_matrix,
        pos_barcode_table_first_summary,
    )

    rows: list[dict[str, str]] = []
    required = [
        "PHASE430_POS_BARCODE_TABLE_FIRST_LAYOUT.md",
        "alrajhi_client/workspace/quality/pos_barcode_table_first_contract.py",
        "tools/phase430_pos_barcode_table_first_guard.py",
        "tests/test_phase430_pos_barcode_table_first.py",
        *REQUIRED_SOURCES,
    ]
    for rel in required:
        add(rows, f"exists::{rel}", "file", rel, (ROOT / rel).exists(), "required Phase430 file exists")
    for rel in required[1:]:
        if rel.endswith(".py"):
            add(rows, f"ast::{rel}", "syntax", rel, parses(rel), "source parses")

    add(rows, "contract_phase", "contract", required[1], PHASE430_POS_BARCODE_TABLE_FIRST_LAYOUT["phase"] == 430, "Phase430 contract declared")
    add(rows, "contract_surface", "contract", required[1], PHASE430_POS_BARCODE_TABLE_FIRST_LAYOUT["pos_surface"] == "barcode_table_first", "POS is barcode/table-first")

    summary = pos_barcode_table_first_summary(ROOT)
    add(rows, "summary_ready", "contract", required[1], bool(summary["ready"]), "POS has no material cards while Restaurant/Cafe keep card grids")
    for row in pos_barcode_table_first_matrix(ROOT):
        rows.append({
            "key": str(row["key"]),
            "category": "pos_barcode_table_first",
            "path": str(row["path"]),
            "status": str(row["status"]),
            "detail": str(row["detail"]),
        })

    release = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    add(rows, "release_doc", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "PHASE430_POS_BARCODE_TABLE_FIRST_LAYOUT" in release, "Phase430 doc registered")
    add(rows, "release_test", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "tests/test_phase430_pos_barcode_table_first.py" in release, "Phase430 test registered")
    add(rows, "release_check", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "pos_barcode_table_first" in release and "phase=430" in release, "Phase430 release check registered")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with MATRIX.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["key", "category", "path", "status", "detail"])
        writer.writeheader(); writer.writerows(rows)

    failed = [row for row in rows if row["status"] != "OK"]
    print(f"Phase430 POS barcode/table-first checks: {len(rows)} checks, failures={len(failed)}")
    print(f"Matrix: {MATRIX}")
    for row in failed:
        print(f"FAIL {row['key']}: {row['detail']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
