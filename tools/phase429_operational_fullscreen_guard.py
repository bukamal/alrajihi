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
MATRIX = OUT_DIR / "operational_fullscreen_matrix.csv"


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
    from workspace.quality.operational_fullscreen_contract import (
        PHASE429_SHARED_OPERATIONAL_FULLSCREEN_MODE,
        REQUIRED_SOURCES,
        operational_fullscreen_matrix,
        operational_fullscreen_summary,
    )

    rows: list[dict[str, str]] = []
    required = [
        "PHASE429_SHARED_OPERATIONAL_FULLSCREEN_MODE.md",
        "alrajhi_client/workspace/quality/operational_fullscreen_contract.py",
        "tools/phase429_operational_fullscreen_guard.py",
        "tests/test_phase429_operational_fullscreen.py",
        *REQUIRED_SOURCES,
    ]
    for rel in required:
        add(rows, f"exists::{rel}", "file", rel, (ROOT / rel).exists(), "required Phase429 file exists")
    for rel in required[1:]:
        if rel.endswith('.py'):
            add(rows, f"ast::{rel}", "syntax", rel, parses(rel), "source parses")

    add(rows, "contract_phase", "contract", required[1], PHASE429_SHARED_OPERATIONAL_FULLSCREEN_MODE["phase"] == 429, "Phase429 contract declared")
    add(rows, "contract_owner", "contract", required[1], PHASE429_SHARED_OPERATIONAL_FULLSCREEN_MODE["owner"] == "OperationalFullscreenController", "fullscreen controller is the central owner")
    add(rows, "contract_shortcut", "contract", required[1], PHASE429_SHARED_OPERATIONAL_FULLSCREEN_MODE["shortcut"] == "F11", "F11 toggles shared fullscreen")

    summary = operational_fullscreen_summary(ROOT)
    add(rows, "summary_ready", "contract", required[1], bool(summary["ready"]), "shared operational fullscreen is wired across shell/POS/restaurant")
    for row in operational_fullscreen_matrix(ROOT):
        rows.append({
            "key": str(row["key"]),
            "category": "operational_fullscreen",
            "path": str(row["path"]),
            "status": str(row["status"]),
            "detail": str(row["detail"]),
        })

    release = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    add(rows, "release_doc", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "PHASE429_SHARED_OPERATIONAL_FULLSCREEN_MODE" in release, "Phase429 doc registered")
    add(rows, "release_test", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "tests/test_phase429_operational_fullscreen.py" in release, "Phase429 test registered")
    add(rows, "release_check", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "operational_fullscreen" in release and "phase=429" in release, "Phase429 release check registered")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with MATRIX.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["key", "category", "path", "status", "detail"])
        writer.writeheader(); writer.writerows(rows)

    failed = [row for row in rows if row["status"] != "OK"]
    print(f"Phase429 operational fullscreen checks: {len(rows)} checks, failures={len(failed)}")
    print(f"Matrix: {MATRIX}")
    for row in failed:
        print(f"FAIL {row['key']}: {row['detail']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
