# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import importlib.util
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def _load_contract():
    path = ROOT / "alrajhi_client" / "workspace" / "quality" / "basit_shell_menu_rebuild_contract.py"
    spec = importlib.util.spec_from_file_location("phase411_basit_shell_menu_rebuild_contract", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _addmenu_body(src: str) -> str:
    match = re.search(r"def addMenu\(self, icon, title\):(.*?)(?:\nclass MainWindow|\n    def [A-Za-z_])", src, flags=re.S)
    assert match
    return match.group(1)


def test_phase411_contract_documents_shell_rebuild_hotfix():
    module = _load_contract()
    contract = module.BASIT_SHELL_MENU_REBUILD_CONTRACT
    assert contract["phase"] == 411
    assert contract["name"] == "basit_shell_menu_rebuild_hotfix"
    assert "main_window.IconMenuBar" in contract["scope"] or "CleanShellNavigationBar" in read("alrajhi_client/views/main_window.py")
    assert any("styled background" in item for item in contract["requirements"])
    assert "tools/audit_outputs/basit_shell_menu_rebuild_matrix.csv" in contract["required_outputs"]


def test_icon_menu_bar_uses_manual_popup_and_forces_repaint_after_rebuild():
    src = read("alrajhi_client/views/main_window.py")
    addmenu = _addmenu_body(src)
    assert "self.setAttribute(Qt.WA_StyledBackground, True)" in src
    assert "NAV_VERTICAL_MARGIN" in src
    assert "setContentsMargins(12, NAV_VERTICAL_MARGIN, 12, NAV_VERTICAL_MARGIN)" in src
    assert "def _popup_menu_for_button" in src
    assert "menu.popup(button.mapToGlobal" in src
    assert "clicked.connect" in addmenu
    assert "self._popup_menu_for_button(b, m)" in addmenu
    assert "btn.setMenu(menu)" not in addmenu
    assert "btn.setPopupMode(QToolButton.InstantPopup)" not in addmenu
    assert "def finish_rebuild" in src
    assert "self.menu_bar.finish_rebuild()" in src


def test_shell_qss_suppresses_native_menu_subcontrols():
    main_window = read("alrajhi_client/views/main_window.py")
    qss = read("alrajhi_client/theme/qss.py")
    assert "QPushButton#MainNavButton" in main_window
    assert "QPushButton#MainNavButton" in qss
    assert "QFrame#CleanShellNavigationBar" in main_window
    assert "QFrame#CleanShellNavigationBar" in qss
    assert "QToolButton#MainNavToolButton" not in main_window
    assert "QToolButton#MainNavToolButton" not in qss


def test_nav_height_has_enough_space_for_button_and_vertical_margins():
    brand = read("alrajhi_client/theme/brand.py")
    def metric(key: str, fallback: int) -> int:
        match = re.search(rf"'{re.escape(key)}'\s*:\s*([0-9]+)", brand)
        return int(match.group(1)) if match else fallback
    nav_height = metric("basit_shell_nav_height", 70)
    button_height = metric("basit_shell_nav_button_height", 64)
    vertical_margin = metric("basit_shell_nav_vertical_margin", max(0, (nav_height - button_height) // 2))
    assert nav_height >= button_height + (2 * vertical_margin)


def test_phase411_guard_runs_and_writes_matrix():
    result = subprocess.run(
        [sys.executable, "tools/phase411_basit_shell_menu_rebuild_hotfix.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    matrix = ROOT / "tools" / "audit_outputs" / "basit_shell_menu_rebuild_matrix.csv"
    assert matrix.exists()
    rows = list(csv.DictReader(matrix.open(encoding="utf-8")))
    assert rows
    assert {row["status"] for row in rows} == {"OK"}


def test_phase411_release_gate_registration():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert "PHASE411_BASIT_SHELL_MENU_REBUILD_HOTFIX" in gate
    assert "tests/test_phase411_basit_shell_menu_rebuild_hotfix.py" in gate
    assert "tools/phase411_basit_shell_menu_rebuild_hotfix.py" in gate
    assert "basit_shell_menu_rebuild_hotfix" in gate
    assert "phase=411" in gate
