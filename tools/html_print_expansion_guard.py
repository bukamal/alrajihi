# -*- coding: utf-8 -*-
from pathlib import Path
root = Path(__file__).resolve().parents[1] / 'alrajhi_client'
checks = {
    'printing/print_templates.py': ['def production_order_html', 'def voucher_html', 'def return_html', 'def report_html'],
    'printing/printing_service.py': ['def voucher_browser', 'def return_browser', 'def production_browser', 'def report_browser'],
    'views/widgets/reports_widget.py': ['فتح HTML في المتصفح', "def print_report(self, mode='preview')"],
    'views/widgets/vouchers_widget.py': ['def print_selected', 'voucher_browser'],
    'views/widgets/returns_widget.py': ['def print_selected_return', 'return_browser'],
    'views/dialogs/production_details_dialog.py': ['def print_order', 'production_browser'],
}
missing=[]
for rel, needles in checks.items():
    text=(root/rel).read_text(encoding='utf-8')
    for n in needles:
        if n not in text:
            missing.append(f'{rel}: {n}')
if missing:
    raise SystemExit('Missing HTML print expansion hooks:\n' + '\n'.join(missing))
print('html_print_expansion_guard: PASS')
