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
    path = ROOT / "alrajhi_client" / "workspace" / "quality" / "operational_item_card_grid_contract.py"
    spec = importlib.util.spec_from_file_location("phase428_operational_item_card_grid_contract", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_phase428_contract_ready():
    module = _load_contract()
    assert module.PHASE428_OPERATIONAL_ITEM_CARD_GRID_UNIFICATION["phase"] == 428
    assert module.PHASE428_OPERATIONAL_ITEM_CARD_GRID_UNIFICATION["default_columns"] == 3
    summary = module.operational_item_card_grid_summary(ROOT)
    assert summary["ready"] is True
    assert summary["failures"] == []


def test_phase428_sources_parse():
    for rel in (
        "alrajhi_client/ui/operational_item_card_grid.py",
        "alrajhi_client/views/widgets/pos_widget.py",
        "alrajhi_client/views/restaurant/restaurant_pos_widget.py",
        "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py",
        "alrajhi_client/workspace/quality/operational_item_card_grid_contract.py",
        "tools/phase428_operational_item_card_grid_guard.py",
        "tests/test_phase428_operational_item_card_grid.py",
    ):
        ast.parse(read(rel))


def test_phase428_component_defaults_to_three_columns():
    text = read("alrajhi_client/ui/operational_item_card_grid.py")
    assert "class OperationalItemCardGrid" in text
    assert "default_columns: int = 3" in text
    assert "itemActivated = pyqtSignal(object)" in text
    assert "self.default_columns" in text


def test_phase428_pos_stays_barcode_table_first_after_phase430():
    text = read("alrajhi_client/views/widgets/pos_widget.py")
    assert "POSLineGrid" in text
    assert "barcode_input" in text
    assert "from ui.operational_item_card_grid import OperationalItemCardGrid" not in text
    assert "posOperationalItemCardGrid" not in text
    assert "catalog_service.items" not in text
    assert "restaurantMenuItemButton" not in text


def test_phase428_restaurant_surfaces_use_shared_grid():
    restaurant = read("alrajhi_client/views/restaurant/restaurant_pos_widget.py")
    simple = read("alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py")
    assert "restaurantMenuOperationalItemCardGrid" in restaurant
    assert "button = QPushButton(self._menu_card_label(item))" not in restaurant
    assert "restaurantSimpleItemCardGrid" in simple
    assert "default_columns=3" in simple


def test_phase428_qss_shared_surface_exists():
    qss = read("alrajhi_client/theme/qss.py")
    assert "Phase428/430: shared Restaurant/Cafe operational material card grid" in qss
    assert "operationalItemCardButton" in qss
    assert "posOperationalItemCardGrid" not in qss


def test_phase428_guard_runs_and_writes_matrix():
    result = subprocess.run(
        [sys.executable, "tools/phase428_operational_item_card_grid_guard.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    matrix = ROOT / "tools" / "audit_outputs" / "operational_item_card_grid_matrix.csv"
    assert matrix.exists()
    rows = list(csv.DictReader(matrix.open(encoding="utf-8-sig")))
    assert rows
    assert {row["status"] for row in rows} == {"OK"}


def test_phase428_release_gate_registration():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert "PHASE428_OPERATIONAL_ITEM_CARD_GRID_UNIFICATION" in gate
    assert "tests/test_phase428_operational_item_card_grid.py" in gate
    assert "tools/phase428_operational_item_card_grid_guard.py" in gate
    assert "operational_item_card_grid" in gate
    assert "phase=428" in gate
