# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.dialogs_modal_windows_visual_unification_contract import phase452_dialogs_modal_windows_visual_unification_summary


def test_phase452_dialogs_modal_windows_visual_unification_ready():
    summary = phase452_dialogs_modal_windows_visual_unification_summary(ROOT)
    assert summary["ready"], summary["details"]
    assert summary["issues"] == 0


def test_modal_qss_comes_after_settings_rules():
    qss = (ROOT / "alrajhi_client/theme/qss.py").read_text(encoding="utf-8")
    assert qss.find("Phase452: dialogs and modal windows visual unification") > qss.find("Phase451: settings workspace visual consolidation")
    assert 'QDialog[modalVisualPhase="452"]' in qss
    assert 'QPushButton[visualRole="modal_primary_action"]' in qss
    assert 'QTableView[visualRole="modal_table"]' in qss


def test_global_modal_event_filter_is_installed_after_theme_init():
    text = (ROOT / "alrajhi_client/main.py").read_text(encoding="utf-8")
    assert "ThemeManager.init_app(app)" in text
    assert "install_modal_visual_event_filter(app)" in text
    assert text.find("install_modal_visual_event_filter(app)") > text.find("ThemeManager.init_app(app)")


def test_dialog_branding_exports_phase452_modal_template():
    text = (ROOT / "alrajhi_client/ui/dialog_branding.py").read_text(encoding="utf-8")
    assert "def apply_modal_visual_template" in text
    assert 'root.setProperty("modalVisualPhase", "452")' in text
    assert '"apply_modal_visual_template"' in text
    assert "branded_question" in text


def test_known_dialogs_keep_logic_and_gain_modal_roles():
    change = (ROOT / "alrajhi_client/views/dialogs/change_password_dialog.py").read_text(encoding="utf-8")
    assert "user_service.change_password" in change
    assert "apply_modal_visual_template(self, role='change_password')" in change
    module = (ROOT / "alrajhi_client/views/dialogs/module_activation_dialog.py").read_text(encoding="utf-8")
    assert "activate_feature" in module
    assert "set_visual_state(self.status_label" in module
    camera = (ROOT / "alrajhi_client/views/dialogs/barcode_camera_dialog.py").read_text(encoding="utf-8")
    assert "barcode_scanner_service.open_camera" in camera
    assert "apply_modal_visual_template(self, role='barcode_camera')" in camera

def test_modal_template_preserves_language_direction_and_message_box_size_path():
    text = (ROOT / "alrajhi_client/ui/dialog_branding.py").read_text(encoding="utf-8")
    assert "qt_layout_direction" in text
    assert "setLayoutDirection(Qt.RightToLeft)" not in text
    assert text.find("isinstance(root, QMessageBox)") < text.find("isinstance(root, QDialog):")

