# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.settings_workspace_visual_consolidation_contract import phase451_settings_workspace_visual_consolidation_summary


def test_phase451_settings_visual_consolidation_ready():
    summary = phase451_settings_workspace_visual_consolidation_summary(ROOT)
    assert summary["ready"], summary["details"]
    assert summary["issues"] == 0


def test_settings_qss_order_and_roles():
    qss = (ROOT / "alrajhi_client/theme/qss.py").read_text(encoding="utf-8")
    assert qss.find("Phase451: settings workspace visual consolidation") > qss.find("Phase450: unified document editor visual template")
    assert 'QWidget[settingsVisualPhase="451"]' in qss
    assert 'QTabWidget[visualRole="settings_group_tabs"]' in qss
    assert 'QPushButton[visualRole="settings_primary_action"]' in qss


def test_settings_widget_uses_central_roles_not_local_qss():
    text = (ROOT / "alrajhi_client/views/widgets/settings_widget.py").read_text(encoding="utf-8")
    assert "settingsLocalStylesSuppressed" in text
    assert "def _apply_settings_visual_template" in text
    assert "apply_modern_widget(self)" not in text
    assert "self.setStyleSheet(self.styleSheet() + f\"\"\"" not in text


def test_settings_document_tabs_keep_persistence_and_visual_roles():
    text = (ROOT / "alrajhi_client/features/settings/settings_document_tabs.py").read_text(encoding="utf-8")
    assert "settings_service.set" in text
    assert "settings_service.clear_cache" in text
    assert "visualRole', 'settings_primary_action'" in text
    assert "settingsLocalStylesSuppressed" in text
