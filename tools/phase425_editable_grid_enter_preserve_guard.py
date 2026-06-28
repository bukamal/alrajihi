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
MATRIX = OUT_DIR / "editable_grid_enter_preserve_matrix.csv"


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
    from workspace.quality.editable_grid_enter_preserve_contract import (
        PHASE425_EDITABLE_GRID_ENTER_PRESERVE,
        editable_grid_enter_preserve_matrix,
        editable_grid_enter_preserve_summary,
    )

    rows: list[dict[str, str]] = []
    required = [
        "PHASE425_EDITABLE_GRID_ENTER_PRESERVE_HOTFIX.md",
        "alrajhi_client/workspace/quality/editable_grid_enter_preserve_contract.py",
        "tools/phase425_editable_grid_enter_preserve_guard.py",
        "tests/test_phase425_editable_grid_enter_preserve.py",
        "alrajhi_client/ui/table_keyboard_policy.py",
    ]
    for rel in required:
        add(rows, f"exists::{rel}", "file", rel, (ROOT / rel).exists(), "required Phase425 file exists")
    for rel in required[1:]:
        add(rows, f"ast::{rel}", "syntax", rel, parses(rel), "source parses")

    add(rows, "contract_phase", "contract", required[1], PHASE425_EDITABLE_GRID_ENTER_PRESERVE["phase"] == 425, "Phase425 contract declared")
    add(rows, "contract_owner", "contract", required[1], "StandardTableKeyboardMixin" in PHASE425_EDITABLE_GRID_ENTER_PRESERVE["owner"], "central keyboard engine remains owner")

    summary = editable_grid_enter_preserve_summary(ROOT)
    add(rows, "summary_ready", "contract", required[1], bool(summary["ready"]), "all Phase425 source markers are present")
    rows.extend(editable_grid_enter_preserve_matrix(ROOT))

    keyboard = read("alrajhi_client/ui/table_keyboard_policy.py")
    add(rows, "enter_forward_gated_once", "source", required[4], keyboard.count("self._standard_commit_enter_editor_if_modified(obj)") >= 2, "Enter and Shift+Enter use gated commit")
    add(rows, "untouched_editor_close_only", "source", required[4], "was untouched and should be closed for navigation" in keyboard, "untouched editor path is documented")
    add(rows, "dirty_signals_line_edit", "source", required[4], "editor.textEdited.connect(mark_modified)" in keyboard, "QLineEdit user edits are tracked")
    add(rows, "dirty_signals_combo", "source", required[4], "editor.activated.connect(mark_modified)" in keyboard and "editor.currentIndexChanged.connect(mark_modified)" in keyboard, "QComboBox user edits are tracked")
    add(rows, "dirty_signals_spin", "source", required[4], "editor.valueChanged.connect(mark_modified)" in keyboard, "Spin editor user edits are tracked")

    release = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    add(rows, "release_doc", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "PHASE425_EDITABLE_GRID_ENTER_PRESERVE_HOTFIX" in release, "Phase425 doc registered")
    add(rows, "release_test", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "tests/test_phase425_editable_grid_enter_preserve.py" in release, "Phase425 test registered")
    add(rows, "release_check", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "editable_grid_enter_preserve" in release and "phase=425" in release, "Phase425 release check registered")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with MATRIX.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["key", "category", "path", "status", "detail"])
        writer.writeheader(); writer.writerows(rows)

    failed = [row for row in rows if row["status"] != "OK"]
    print(f"Phase425 editable-grid Enter preserve checks: {len(rows)} checks, failures={len(failed)}")
    print(f"Matrix: {MATRIX}")
    for row in failed:
        print(f"FAIL {row['key']}: {row['detail']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
