# -*- coding: utf-8 -*-
"""Phase 243: print settings tab exposes the complete browser-HTML contract."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_printing_settings_contract_contains_company_identity_toggles_and_languages():
    text = read('alrajhi_client/core/services/settings_service.py')
    for key in [
        'printing/show_company_name',
        'printing/show_address',
        'printing/show_phone',
        'printing/show_email',
        'printing/show_commercial_register',
        'printing/show_website',
        'printing/reverse_print_table_columns',
    ]:
        assert key in text
    assert "'print_language': self.print_language()" in text
    assert "self.set('printing/print_button_mode', 'browser')" in text


def test_print_settings_widget_exposes_existing_tab_with_new_controls():
    text = read('alrajhi_client/views/widgets/settings_widget.py')
    assert 'def create_printing_tab' in text
    assert 'self.print_language_combo' in text
    assert 'settings_service.save_language_settings' in text
    for attr in [
        'print_show_company_name',
        'print_show_address',
        'print_show_phone',
        'print_show_email',
        'print_show_commercial_register',
        'print_show_website',
        'print_reverse_columns',
    ]:
        assert attr in text
    assert 'def preview_test_print_settings' in text
    assert 'printing_service.invoice_browser' in text


def test_print_templates_obey_identity_visibility_settings():
    text = read('alrajhi_client/printing/print_templates.py')
    for key in [
        'show_company_name',
        'show_address',
        'show_phone',
        'show_email',
        'show_commercial_register',
        'show_website',
    ]:
        assert key in text
    assert 'SettingsService/SettingsGateway contract' in text


def test_workspace_printing_section_matches_main_printing_contract():
    text = read('alrajhi_client/features/settings/settings_document_tabs.py')
    assert "('language/print', 'settings_print_language_label'" in text
    assert "('printing/show_company_name'" in text
    assert "('printing/reverse_print_table_columns'" in text


def test_i18n_has_ar_en_de_print_settings_labels():
    text = read('alrajhi_client/i18n/translator.py')
    for token in [
        'settings_print_show_company_name',
        'settings_print_language_label',
        'settings_print_reverse_columns',
        'settings_print_test_document',
    ]:
        assert text.count(token) >= 3
