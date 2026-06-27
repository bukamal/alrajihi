# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_generic_feature_activation_extends_network_activation_without_breaking_name():
    src = read("alrajhi_client/auth/activation.py")
    assert "def activate_feature(feature: str, license_key: str)" in src
    assert "def check_feature_activation(feature: str)" in src
    assert "return activate_feature('network', license_key)" in src
    assert "def check_network_activation()" in src
    assert "feature_license_file(feature_id)" in src


def test_vertical_pages_are_guarded_before_workspace_entry():
    src = read("alrajhi_client/views/main_window.py")
    assert "PAID_FEATURE_PAGES" in src
    for page in ("manufacturing", "restaurant", "cafe", "apparel"):
        assert f"'{page}': '{page}'" in src
    switch_block = src.split("def switch_page", 1)[1].split("def closeEvent", 1)[0]
    assert "not self._ensure_page_feature_activation(pid)" in switch_block
    assert "not page_enabled(pid)" in switch_block


def test_manufacturing_direct_document_shortcuts_are_guarded():
    src = read("alrajhi_client/views/main_window.py")
    for name in ("open_bom_document", "open_production_order_document", "open_production_order_details"):
        block = src.split(f"def {name}", 1)[1].split("\n    def ", 1)[0]
        assert "_ensure_feature_activation('manufacturing'" in block


def test_unified_activation_dialog_and_i18n_cover_network_and_verticals():
    dialog = read("alrajhi_client/views/dialogs/module_activation_dialog.py")
    assert "class ModuleActivationDialog" in dialog
    assert "activate_feature(self.feature, key)" in dialog
    assert "check_feature_activation(feature_id)" in dialog
    settings = read("alrajhi_client/views/widgets/settings_widget.py")
    assert "ModuleActivationDialog.ensure_feature" in settings
    i18n = read("alrajhi_client/i18n/translator.py")
    for key in ("feature_activation_network", "feature_activation_manufacturing", "feature_activation_restaurant", "feature_activation_cafe", "feature_activation_apparel"):
        assert key in i18n


def test_quality_contract_documents_activation_gate():
    contract = read("alrajhi_client/workspace/quality/feature_activation_gate_contract.py")
    assert "FEATURE_ACTIVATION_GATE_CONTRACT" in contract
    assert "manufacturing" in contract and "restaurant" in contract and "cafe" in contract and "apparel" in contract
