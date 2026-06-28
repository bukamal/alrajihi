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
    path = ROOT / "alrajhi_client" / "workspace" / "quality" / "pos_barcode_table_first_contract.py"
    spec = importlib.util.spec_from_file_location("phase430_pos_barcode_table_first_contract", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_phase430_contract_ready():
    module = _load_contract()
    assert module.PHASE430_POS_BARCODE_TABLE_FIRST_LAYOUT["phase"] == 430
    assert module.PHASE430_POS_BARCODE_TABLE_FIRST_LAYOUT["pos_surface"] == "barcode_table_first"
    summary = module.pos_barcode_table_first_summary(ROOT)
    assert summary["ready"] is True
    assert summary["failures"] == []


def test_phase430_sources_parse():
    for rel in (
        "alrajhi_client/views/widgets/pos_widget.py",
        "alrajhi_client/workspace/quality/pos_barcode_table_first_contract.py",
        "tools/phase430_pos_barcode_table_first_guard.py",
        "tests/test_phase430_pos_barcode_table_first.py",
    ):
        ast.parse(read(rel))


def test_phase430_pos_has_no_material_card_grid_above_table():
    text = read("alrajhi_client/views/widgets/pos_widget.py")
    assert "POSLineGrid" in text
    assert "self.barcode_input = QLineEdit()" in text
    assert "from ui.operational_item_card_grid import OperationalItemCardGrid" not in text
    assert "posOperationalItemCardGrid" not in text
    assert "self.item_card_grid" not in text
    assert "catalog_service.items" not in text
    assert "_load_pos_item_cards" not in text


def test_phase430_pos_table_follows_scan_row():
    text = read("alrajhi_client/views/widgets/pos_widget.py")
    scan_idx = text.find("layout.addLayout(scan_row)")
    table_idx = text.find("self.table = POSLineGrid")
    assert scan_idx >= 0
    assert table_idx > scan_idx
    between = text[scan_idx:table_idx]
    assert "OperationalItemCardGrid" not in between
    assert "item_card_grid" not in between


def test_phase430_restaurant_cards_preserved():
    restaurant = read("alrajhi_client/views/restaurant/restaurant_pos_widget.py")
    simple = read("alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py")
    assert "OperationalItemCardGrid" in restaurant
    assert "restaurantMenuOperationalItemCardGrid" in restaurant
    assert "OperationalItemCardGrid" in simple
    assert "restaurantSimpleItemCardGrid" in simple


def test_phase430_guard_runs_and_writes_matrix():
    result = subprocess.run(
        [sys.executable, "tools/phase430_pos_barcode_table_first_guard.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    matrix = ROOT / "tools" / "audit_outputs" / "pos_barcode_table_first_matrix.csv"
    assert matrix.exists()
    rows = list(csv.DictReader(matrix.open(encoding="utf-8-sig")))
    assert rows
    assert {row["status"] for row in rows} == {"OK"}


def test_phase430_release_gate_registration():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert "PHASE430_POS_BARCODE_TABLE_FIRST_LAYOUT" in gate
    assert "tests/test_phase430_pos_barcode_table_first.py" in gate
    assert "tools/phase430_pos_barcode_table_first_guard.py" in gate
    assert "pos_barcode_table_first" in gate
    assert "phase=430" in gate
