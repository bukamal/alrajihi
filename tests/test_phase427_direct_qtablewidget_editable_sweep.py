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
    path = ROOT / "alrajhi_client" / "workspace" / "quality" / "direct_qtablewidget_editable_sweep_contract.py"
    spec = importlib.util.spec_from_file_location("phase427_direct_qtablewidget_editable_sweep_contract", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_phase427_contract_ready():
    module = _load_contract()
    assert module.PHASE427_DIRECT_QTABLEWIDGET_EDITABLE_SWEEP["phase"] == 427
    summary = module.direct_qtablewidget_editable_sweep_summary(ROOT)
    assert summary["ready"] is True
    assert summary["failures"] == []


def test_phase427_sources_parse():
    for rel in (
        "alrajhi_client/workspace/quality/direct_qtablewidget_editable_sweep_contract.py",
        "tools/phase427_direct_qtablewidget_editable_sweep_guard.py",
        "tests/test_phase427_direct_qtablewidget_editable_sweep.py",
        "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py",
        "alrajhi_client/views/widgets/settings_widget.py",
    ):
        ast.parse(read(rel))


def test_phase427_restaurant_simple_invoice_table_uses_editable_smart_grid():
    text = read("alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py")
    assert "from ui.editable_smart_grid import EditableSmartGrid" in text
    assert "self.invoice_table = EditableSmartGrid" in text
    assert "self.invoice_table = QTableWidget" not in text
    assert "SelectedClicked" not in text
    assert "QAbstractItemView.AnyKeyPressed" in text


def test_phase427_settings_surface_table_is_not_an_editable_direct_qtablewidget():
    text = read("alrajhi_client/views/widgets/settings_widget.py")
    assert "self.settings_surface_columns_table = EditableSmartGrid" in text
    assert "self.settings_surface_columns_table = QTableWidget" not in text
    assert "settings_surface_columns_table.setEditTriggers(EditableSmartGrid.NoEditTriggers)" in text


def test_phase427_direct_qtablewidget_matrix_contains_only_readonly_surfaces():
    module = _load_contract()
    rows = module.direct_qtablewidget_surface_matrix(ROOT)
    assert rows
    assert {row["status"] for row in rows} == {"OK"}
    surfaces = {(row["path"], row["surface"]) for row in rows}
    assert ("alrajhi_client/views/apparel/apparel_workspace_widget.py", "report_table") in surfaces
    assert ("alrajhi_client/views/apparel/apparel_workspace_widget.py", "matrix_table") in surfaces


def test_phase427_guard_runs_and_writes_matrix():
    result = subprocess.run(
        [sys.executable, "tools/phase427_direct_qtablewidget_editable_sweep_guard.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    matrix = ROOT / "tools" / "audit_outputs" / "direct_qtablewidget_editable_sweep_matrix.csv"
    assert matrix.exists()
    rows = list(csv.DictReader(matrix.open(encoding="utf-8-sig")))
    assert rows
    assert {row["status"] for row in rows} == {"OK"}


def test_phase427_release_gate_registration():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert "PHASE427_DIRECT_QTABLEWIDGET_EDITABLE_SWEEP" in gate
    assert "tests/test_phase427_direct_qtablewidget_editable_sweep.py" in gate
    assert "tools/phase427_direct_qtablewidget_editable_sweep_guard.py" in gate
    assert "direct_qtablewidget_editable_sweep" in gate
    assert "phase=427" in gate
