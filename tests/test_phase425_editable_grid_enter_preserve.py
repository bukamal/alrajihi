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
    path = ROOT / "alrajhi_client" / "workspace" / "quality" / "editable_grid_enter_preserve_contract.py"
    spec = importlib.util.spec_from_file_location("phase425_editable_grid_enter_preserve_contract", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_phase425_contract_ready():
    module = _load_contract()
    assert module.PHASE425_EDITABLE_GRID_ENTER_PRESERVE["phase"] == 425
    summary = module.editable_grid_enter_preserve_summary(ROOT)
    assert summary["ready"] is True
    assert summary["failures"] == []


def test_phase425_sources_parse():
    for rel in (
        "alrajhi_client/ui/table_keyboard_policy.py",
        "alrajhi_client/workspace/quality/editable_grid_enter_preserve_contract.py",
        "tools/phase425_editable_grid_enter_preserve_guard.py",
    ):
        ast.parse(read(rel))


def test_phase425_enter_commit_is_gated_for_untouched_editors():
    text = read("alrajhi_client/ui/table_keyboard_policy.py")
    assert "def _standard_commit_enter_editor_if_modified" in text
    assert "if not self._standard_editor_user_modified(editor):\n            return False" in text
    assert text.count("self._standard_commit_enter_editor_if_modified(obj)") >= 2
    assert "self.closeEditor(obj, QAbstractItemDelegate.NoHint)" in text
    assert "self.closeEditor(obj, QAbstractItemDelegate.EditPreviousItem)" in text


def test_phase425_dirty_tracking_covers_common_editors():
    text = read("alrajhi_client/ui/table_keyboard_policy.py")
    assert "standard_enter_user_modified" in text
    assert "standard_enter_initial_text" in text
    assert "editor.textEdited.connect(mark_modified)" in text
    assert "editor.activated.connect(mark_modified)" in text
    assert "editor.currentIndexChanged.connect(mark_modified)" in text
    assert "editor.valueChanged.connect(mark_modified)" in text
    assert "editor.textChanged.connect(mark_modified)" in text


def test_phase425_guard_runs_and_writes_matrix():
    result = subprocess.run(
        [sys.executable, "tools/phase425_editable_grid_enter_preserve_guard.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    matrix = ROOT / "tools" / "audit_outputs" / "editable_grid_enter_preserve_matrix.csv"
    assert matrix.exists()
    rows = list(csv.DictReader(matrix.open(encoding="utf-8-sig")))
    assert rows
    assert {row["status"] for row in rows} == {"OK"}


def test_phase425_release_gate_registration():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert "PHASE425_EDITABLE_GRID_ENTER_PRESERVE_HOTFIX" in gate
    assert "tests/test_phase425_editable_grid_enter_preserve.py" in gate
    assert "tools/phase425_editable_grid_enter_preserve_guard.py" in gate
    assert "editable_grid_enter_preserve" in gate
    assert "phase=425" in gate
