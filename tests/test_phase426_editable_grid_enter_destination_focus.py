# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import csv
import importlib.util
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def _load_contract():
    path = ROOT / "alrajhi_client" / "workspace" / "quality" / "editable_grid_enter_destination_focus_contract.py"
    spec = importlib.util.spec_from_file_location("phase426_editable_grid_enter_destination_focus_contract", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _handle_enter_block(text: str) -> str:
    start = text.find("def _standard_handle_enter_key")
    end = text.find("\n    def currentChanged", start)
    return text[start:end]


def _close_editor_block(text: str) -> str:
    start = text.find("def closeEditor")
    next_def = text.find("\n    def ", start + 1)
    return text[start:next_def if next_def > start else len(text)]


def test_phase426_contract_ready():
    module = _load_contract()
    assert module.PHASE426_EDITABLE_GRID_ENTER_DESTINATION_FOCUS["phase"] == 426
    summary = module.editable_grid_enter_destination_focus_summary(ROOT)
    assert summary["ready"] is True
    assert summary["failures"] == []


def test_phase426_sources_parse():
    for rel in (
        "alrajhi_client/ui/table_keyboard_policy.py",
        "alrajhi_client/workspace/quality/editable_grid_enter_destination_focus_contract.py",
        "tools/phase426_editable_grid_enter_destination_focus_guard.py",
    ):
        ast.parse(read(rel))


def test_phase426_enter_on_focused_cell_does_not_open_editor():
    text = read("alrajhi_client/ui/table_keyboard_policy.py")
    block = _handle_enter_block(text)
    assert "Enter on a focused, non-editing cell is navigation only" in block
    assert "self.edit(current)" not in block
    assert "self._standard_focus_index(next_index, start_edit=False)" in block
    assert "QAbstractItemView.AnyKeyPressed" in text


def test_phase426_close_editor_focuses_destination_without_auto_edit():
    text = read("alrajhi_client/ui/table_keyboard_policy.py")
    block = _close_editor_block(text)
    assert "self._standard_focus_index(target, start_edit=False)" in block
    assert "self._standard_focus_index(self._standard_next_index(idx, True), start_edit=False)" in block
    assert "self._standard_focus_index(self._standard_next_index(idx, False), start_edit=False)" in block
    assert "start_edit=True" not in block


def test_phase426_guard_runs_and_writes_matrix():
    result = subprocess.run(
        [sys.executable, "tools/phase426_editable_grid_enter_destination_focus_guard.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    matrix = ROOT / "tools" / "audit_outputs" / "editable_grid_enter_destination_focus_matrix.csv"
    assert matrix.exists()
    rows = list(csv.DictReader(matrix.open(encoding="utf-8-sig")))
    assert rows
    assert {row["status"] for row in rows} == {"OK"}


def test_phase426_release_gate_registration():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert "PHASE426_EDITABLE_GRID_ENTER_DESTINATION_FOCUS_HOTFIX" in gate
    assert "tests/test_phase426_editable_grid_enter_destination_focus.py" in gate
    assert "tools/phase426_editable_grid_enter_destination_focus_guard.py" in gate
    assert "editable_grid_enter_destination_focus" in gate
    assert "phase=426" in gate
