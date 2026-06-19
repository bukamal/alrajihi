# -*- coding: utf-8 -*-
"""Phase 234 guard: shell utilities, dashboard cashbox, invoice columns, workflow and return labels."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')

def require(cond, msg):
    if not cond:
        raise AssertionError(msg)

def main():
    mw = read('alrajhi_client/views/main_window.py')
    action = read('alrajhi_client/shell/unified_action_bar.py')
    top = read('alrajhi_client/views/modern_topbar.py')
    dash_service = read('alrajhi_client/core/services/dashboard_service.py')
    reports = read('alrajhi_client/core/services/reporting_service.py')
    dash = read('alrajhi_client/views/widgets/dashboard_widget.py')
    inv = read('alrajhi_client/views/widgets/invoices_widget.py')
    tr = read('alrajhi_client/i18n/translator.py')

    require('self.top_bar.setVisible(False)' in mw and 'self.top_bar.setFixedHeight(0)' in mw,
            'Compatibility top bar must be hidden after moving utility controls to UnifiedActionBar')
    for attr in ('alert_btn', 'theme_btn', 'screenshot_btn', 'user_label', 'set_alert_badge', 'set_user'):
        require(attr in action, f'UnifiedActionBar missing shell utility control/contract: {attr}')
    require('utility_bar.theme_btn.clicked.connect' in mw and 'utility_bar.alert_btn.clicked.connect' in mw,
            'MainWindow must bind moved utility buttons from UnifiedActionBar')
    require('self.top_bar.theme_btn.clicked.connect' not in mw and 'self.top_bar.alert_btn.clicked.connect' not in mw,
            'MainWindow must not bind hidden top-bar utility buttons')

    require("'current_balance'" in reports and "'cash_balance'" in reports,
            'cash_bank_summary must normalize remote/local cashbox balance field names')
    require('cash_bank_summary' in dash_service and 'cashbox_movement' in dash_service,
            'Dashboard snapshot must include cashbox summary and movement data')
    require('currency.format_base_amount' in dash,
            'Dashboard cashbox card must format amounts through the currency helper')

    sales_block = inv[inv.find("if inv_type == 'sale':"):inv.find('        else:', inv.find("if inv_type == 'sale':"))]
    require("'paid'" not in sales_block.split('headers =', 1)[1].split('\n', 1)[0],
            'Sales invoices table must not expose the duplicated paid column')
    require('reporting_service.invoice_profit_report' in inv,
            'Sales invoices must load invoice profit from reporting_service')
    require("inv.get('paid_amount', inv.get('paid', 0))" in inv,
            'Sales received amount must prefer paid_amount over the legacy paid field')
    require('if not workflow_enabled:' in inv and 'return\n        actions = []' in inv,
            'Workflow block must be hidden entirely when workflow is disabled')
    require("'original_invoice': 'الفاتورة الأصلية'" in tr and "'original_invoice': 'الفاتورة الأصلية:'" not in tr,
            'Arabic original invoice label must not include a trailing colon')

if __name__ == '__main__':
    main()
    print('phase234_ui_finance_workflow_guard: OK')
