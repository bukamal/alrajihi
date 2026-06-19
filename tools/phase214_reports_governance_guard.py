# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')

def main():
    policy = read('alrajhi_client/core/services/report_operation_policy.py')
    assert 'class ReportOperationPolicy' in policy
    assert "OP_VIEW = 'view'" in policy
    assert "OP_EXPORT = 'export'" in policy
    assert 'ACTION_VIEW_REPORTS' in policy
    assert 'ACTION_EXPORT_REPORTS' in policy
    assert 'get_report_settings' in policy

    settings = read('alrajhi_client/core/services/settings_service.py')
    assert 'def get_report_settings' in settings
    assert "reports/operations/allow_view" in settings
    assert "reports/operations/allow_export" in settings
    assert "printing/report_template" in settings

    widget = read('alrajhi_client/views/widgets/reports_widget.py')
    assert 'report_operation_policy' in widget
    assert 'def _apply_report_operation_state' in widget
    assert 'def _require_report_operation' in widget
    assert 'OP_VIEW' in widget
    assert 'self.print_btn.setEnabled(can_view and can_export)' in widget

    mixin = read('alrajhi_client/views/widgets/reports_phase36_mixin.py')
    assert 'report_operation_policy.require(report_operation_policy.OP_EXPORT' in mixin
    assert 'printing_service.report_pdf' in mixin

    translations = read('alrajhi_client/i18n/translator.py')
    for key in ('reports_access_denied', 'reports_export_denied', 'reports.operation.view', 'reports.operation.export'):
        assert translations.count(key) >= 3, key

    contract = read('tools/reports_contract_check.py')
    assert '_refresh_phase36_reports' in widget
    print('phase214_reports_governance_guard passed')

if __name__ == '__main__':
    main()
