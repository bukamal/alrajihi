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
MATRIX = OUT_DIR / "editable_grid_enter_destination_focus_matrix.csv"


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
    from workspace.quality.editable_grid_enter_destination_focus_contract import (
        PHASE426_EDITABLE_GRID_ENTER_DESTINATION_FOCUS,
        editable_grid_enter_destination_focus_matrix,
        editable_grid_enter_destination_focus_summary,
    )

    rows: list[dict[str, str]] = []
    required = [
        "PHASE426_EDITABLE_GRID_ENTER_DESTINATION_FOCUS_HOTFIX.md",
        "alrajhi_client/workspace/quality/editable_grid_enter_destination_focus_contract.py",
        "tools/phase426_editable_grid_enter_destination_focus_guard.py",
        "tests/test_phase426_editable_grid_enter_destination_focus.py",
        "alrajhi_client/ui/table_keyboard_policy.py",
    ]
    for rel in required:
        add(rows, f"exists::{rel}", "file", rel, (ROOT / rel).exists(), "required Phase426 file exists")
    for rel in required[1:]:
        add(rows, f"ast::{rel}", "syntax", rel, parses(rel), "source parses")

    add(rows, "contract_phase", "contract", required[1], PHASE426_EDITABLE_GRID_ENTER_DESTINATION_FOCUS["phase"] == 426, "Phase426 contract declared")
    add(rows, "contract_owner", "contract", required[1], "StandardTableKeyboardMixin" in PHASE426_EDITABLE_GRID_ENTER_DESTINATION_FOCUS["owner"], "central keyboard engine remains owner")

    summary = editable_grid_enter_destination_focus_summary(ROOT)
    add(rows, "summary_ready", "contract", required[1], bool(summary["ready"]), "all Phase426 source markers are present")
    rows.extend(editable_grid_enter_destination_focus_matrix(ROOT))

    keyboard = read("alrajhi_client/ui/table_keyboard_policy.py")
    add(rows, "no_navigation_start_edit_true", "source", required[4], "_standard_focus_index(target, start_edit=True)" not in keyboard and "_standard_focus_index(next_index, start_edit=True)" not in keyboard, "Enter navigation destinations are not auto-edited")
    add(rows, "any_key_pressed_kept", "source", required[4], "QAbstractItemView.AnyKeyPressed" in keyboard, "typing still opens editors via Qt")
    add(rows, "commit_gate_kept", "source", required[4], "def _standard_commit_enter_editor_if_modified" in keyboard, "Phase425 source commit guard remains active")

    release = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    add(rows, "release_doc", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "PHASE426_EDITABLE_GRID_ENTER_DESTINATION_FOCUS_HOTFIX" in release, "Phase426 doc registered")
    add(rows, "release_test", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "tests/test_phase426_editable_grid_enter_destination_focus.py" in release, "Phase426 test registered")
    add(rows, "release_check", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "editable_grid_enter_destination_focus" in release and "phase=426" in release, "Phase426 release check registered")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with MATRIX.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["key", "category", "path", "status", "detail"])
        writer.writeheader(); writer.writerows(rows)

    failed = [row for row in rows if row["status"] != "OK"]
    print(f"Phase426 editable-grid Enter destination focus checks: {len(rows)} checks, failures={len(failed)}")
    print(f"Matrix: {MATRIX}")
    for row in failed:
        print(f"FAIL {row['key']}: {row['detail']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
