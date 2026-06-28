# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_qss_contains_basit_startup_login_activation_and_dialog_rules():
    qss = read("alrajhi_client/theme/qss.py")
    assert "Phase407: Basit-inspired startup" in qss
    assert 'QFrame#startupCard[basitStartupSurface="true"]' in qss
    assert 'QFrame#loginCard[basitFirstRunChrome="true"]' in qss
    assert 'QFrame#activationCard[basitFirstRunChrome="true"]' in qss
    assert 'QDialog[basitDialogSurface="true"] QFrame#BrandDialogHeader' in qss
    assert 'QDialog[basitDialogSurface="true"] QPushButton[dialogActionRole="primary"]' in qss
    assert "basit_yellow" in qss and "basit_red" in qss and "basit_blue" in qss


def test_startup_and_login_mark_basit_entry_surfaces():
    splash = read("alrajhi_client/views/splash_screen.py")
    login = read("alrajhi_client/views/dialogs/login_dialog.py")
    assert "basitStartupSurface" in splash
    assert "basitDialogSurface', 'splash'" in splash
    assert "firstRunStageChip" in splash
    assert "basitFirstRunChrome" in login
    assert "basitDialogSurface', 'login'" in login
    assert "loginUsernameCombo" in login
    assert "loginLanguageCombo" in login
    assert "basitPrimaryAction" in login
    assert "basitSecondaryAction" in login


def test_activation_and_module_activation_use_basit_dialog_surface():
    activation = read("alrajhi_client/views/dialogs/activation_dialog.py")
    module = read("alrajhi_client/views/dialogs/module_activation_dialog.py")
    assert "basitFirstRunChrome" in activation
    assert "basitDialogSurface', 'activation'" in activation
    assert "apply_branded_dialog(self, self.windowTitle(), role='module_activation')" in module
    assert "brand_message_box" in module
    assert "BasitDialogHelp" in module
    assert "dialogActionRole', 'primary'" in module
    assert "dialogActionRole', 'close'" in module


def test_dialog_branding_and_frameless_base_mark_all_runtime_dialogs():
    branding = read("alrajhi_client/ui/dialog_branding.py")
    frameless = read("alrajhi_client/views/frameless_dialog.py")
    assert 'dialog.setProperty("basitDialogSurface", True)' in branding
    assert 'box.setProperty("basitDialogSurface", True)' in branding
    assert "self.setProperty('basitDialogSurface', True)" in frameless
    assert "basitDialogFrame" in frameless


def test_contract_file_documents_phase407_surface_scope():
    contract = read("alrajhi_client/workspace/quality/basit_startup_dialogs_surface_contract.py")
    assert "BASIT_STARTUP_DIALOGS_SURFACE_CONTRACT" in contract
    assert "startup_splash" in contract
    assert "module_activation_dialog" in contract
    assert "message_box" in contract
