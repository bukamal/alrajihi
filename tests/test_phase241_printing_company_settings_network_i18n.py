# -*- coding: utf-8 -*-
"""Phase 241: browser HTML printing must use settings/API-safe company identity."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_company_settings_contract_is_logo_path_and_data_uri_aware():
    text = read("alrajhi_client/core/services/settings_service.py")
    assert "'company/logo_path'" in text
    assert "'company/logo_data_uri'" in text
    assert "def _logo_data_uri_from_path" in text
    assert "SettingsGateway/API boundary" in text


def test_print_templates_embed_logo_for_network_browser_printing():
    text = read("alrajhi_client/printing/print_templates.py")
    assert "def _image_data_uri" in text
    assert "logo_data_uri" in text
    assert "logo_src" in text
    assert "data URI is required in client-server mode" in text


def test_settings_company_tab_uses_settings_service_not_local_config_as_source():
    text = read("alrajhi_client/views/widgets/settings_widget.py")
    assert "info = settings_service.company_info()" in text
    assert "from config import get_company_info" not in text
    assert "from config import save_company_info" not in text


def test_barcode_labels_use_same_company_identity_contract():
    text = read("alrajhi_client/core/services/barcode_label_service.py")
    assert "def _company_info" in text
    assert "settings_service.company_info()" in text
    assert "logo_data_uri" in text


def test_template_loader_reports_fallback_diagnostics_and_uses_print_language():
    text = read("alrajhi_client/printing/_template_loader.py")
    assert "_LAST_TEMPLATE_LOAD_ERROR" in text
    assert "fallback-print-template" in text
    assert "settings_service.print_language()" in text
