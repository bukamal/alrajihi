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
    path = ROOT / "alrajhi_client" / "workspace" / "quality" / "operational_fullscreen_contract.py"
    spec = importlib.util.spec_from_file_location("phase429_operational_fullscreen_contract", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_phase429_contract_ready():
    module = _load_contract()
    assert module.PHASE429_SHARED_OPERATIONAL_FULLSCREEN_MODE["phase"] == 429
    assert module.PHASE429_SHARED_OPERATIONAL_FULLSCREEN_MODE["owner"] == "OperationalFullscreenController"
    summary = module.operational_fullscreen_summary(ROOT)
    assert summary["ready"] is True
    assert summary["failures"] == []


def test_phase429_sources_parse():
    for rel in (
        "alrajhi_client/ui/operational_fullscreen_controller.py",
        "alrajhi_client/views/main_window.py",
        "alrajhi_client/shell/unified_action_bar.py",
        "alrajhi_client/workspace/registry/ui_manifest.py",
        "alrajhi_client/views/widgets/pos_widget.py",
        "alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py",
        "alrajhi_client/views/restaurant/restaurant_pos_widget.py",
        "alrajhi_client/workspace/quality/operational_fullscreen_contract.py",
        "tools/phase429_operational_fullscreen_guard.py",
        "tests/test_phase429_operational_fullscreen.py",
    ):
        ast.parse(read(rel))


def test_phase429_controller_hides_shell_and_restores_state():
    text = read("alrajhi_client/ui/operational_fullscreen_controller.py")
    assert "class OperationalFullscreenController" in text
    assert "OperationalFullscreenSnapshot" in text
    assert "CHROME_WIDGET_ATTRS" in text
    assert "menu_bar" in text
    assert "action_bar" in text
    assert "notification_center" in text
    assert "QToolBar" in text
    assert "tabBar().setVisible(False)" in text
    assert "widget.setVisible(False)" in text
    assert "self.main_window.showFullScreen()" in text
    assert "OperationalFullscreenExitButton" in text


def test_phase429_mainwindow_wires_f11_esc_and_action_bar():
    text = read("alrajhi_client/views/main_window.py")
    assert "OperationalFullscreenController(self)" in text
    assert "def toggle_operational_fullscreen" in text
    assert "ActionBarUtilityButton_fullscreen" not in text  # owned by action bar, not MainWindow
    assert "utility_bar.fullscreen_btn.clicked.connect(self.toggle_operational_fullscreen)" in text
    assert "QKeySequence('F11')" in text
    assert "operational_fullscreen_shortcut.setContext(Qt.ApplicationShortcut)" in text
    assert "controller.is_active()" in text
    assert "controller.exit()" in text


def test_phase429_action_bar_and_registry_expose_shared_button():
    action_bar = read("alrajhi_client/shell/unified_action_bar.py")
    registry = read("alrajhi_client/workspace/registry/ui_manifest.py")
    assert '"fullscreen": WorkspaceActionSpec("fullscreen", "fullscreen", "expand", "F11", placement="utility")' in registry
    assert 'UTILITY_ACTION_KEYS: tuple[str, ...] = ("alert", "theme", "screenshot", "fullscreen", "user")' in registry
    assert "ActionBarUtilityButton_fullscreen" in action_bar
    assert "self.fullscreen_btn" in action_bar
    assert '"fullscreen": self.fullscreen_btn' in action_bar


def test_phase429_pos_and_restaurant_delegate_no_local_fullscreen_owner():
    files = {
        "pos": read("alrajhi_client/views/widgets/pos_widget.py"),
        "restaurant_simple": read("alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py"),
        "restaurant_pos": read("alrajhi_client/views/restaurant/restaurant_pos_widget.py"),
    }
    assert "QKeySequence(\"F11\")" not in files["pos"]
    assert "window.toggle_operational_fullscreen()" in files["pos"]
    assert "restaurantSimpleFullscreenButton" in files["restaurant_simple"]
    assert "restaurantOrderFullscreenButton" in files["restaurant_pos"]
    for name, text in files.items():
        assert "showFullScreen" not in text, name


def test_phase429_guard_runs_and_writes_matrix():
    result = subprocess.run(
        [sys.executable, "tools/phase429_operational_fullscreen_guard.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    matrix = ROOT / "tools" / "audit_outputs" / "operational_fullscreen_matrix.csv"
    assert matrix.exists()
    rows = list(csv.DictReader(matrix.open(encoding="utf-8-sig")))
    assert rows
    assert {row["status"] for row in rows} == {"OK"}


def test_phase429_release_gate_registration():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert "PHASE429_SHARED_OPERATIONAL_FULLSCREEN_MODE" in gate
    assert "tests/test_phase429_operational_fullscreen.py" in gate
    assert "tools/phase429_operational_fullscreen_guard.py" in gate
    assert "operational_fullscreen" in gate
    assert "phase=429" in gate
