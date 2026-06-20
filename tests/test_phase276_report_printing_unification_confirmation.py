from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def test_reports_visible_button_uses_unified_report_print():
    widget = read('alrajhi_client/views/widgets/reports_widget.py')
    mixin = read('alrajhi_client/views/widgets/reports_phase36_mixin.py')
    assert "self.print_btn = QPushButton" in widget
    assert "reportPrintButton" in widget
    assert "self.print_report('print')" in widget
    assert "printing_service.report_print" in mixin
    assert "_require_report_print_permission" in mixin


def test_report_printing_service_is_browser_html_only():
    svc = read('alrajhi_client/printing/printing_service.py')
    assert "def report_print" in svc
    assert "document_type='report'" in svc
    assert "return self._print_button_render(html" in svc
    assert "def report_preview" in svc and "mode='preview'" in svc
    assert "def report_pdf" in svc and "mode='pdf'" in svc
    assert "return self.open_html_in_browser(html" in svc


def test_report_print_settings_are_visible_in_main_settings_and_contracts():
    settings = read('alrajhi_client/views/widgets/settings_widget.py')
    service = read('alrajhi_client/core/services/settings_service.py')
    assert "contract_reports_print" in settings
    assert "reports/operations/allow_print" in settings
    assert "print_report_template" in settings
    assert "report_template=self.print_report_template.currentData()" in settings
    assert "get_report_settings" in service
    assert "reports/operations/allow_print" in service
    assert "printing/report_template" in service


def test_report_template_uses_company_header_and_base_document():
    tpl = read('alrajhi_client/printing/print_templates.py')
    assert "def report_html" in tpl
    assert "_company_header(settings, title)" in tpl
    assert "_table(headers, rows" in tpl
    assert "return base_document(title, body, paper, settings)" in tpl


def test_report_print_translation_keys_exist_in_three_languages():
    tr = read('alrajhi_client/i18n/translator.py')
    assert "'settings_operation_reports_print': 'السماح بطباعة التقارير'" in tr
    assert "'settings_operation_reports_print': 'Berichtsdruck erlauben'" in tr
    assert "'settings_operation_reports_print': 'Allow report printing'" in tr
