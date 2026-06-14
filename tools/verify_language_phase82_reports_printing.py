# -*- coding: utf-8 -*-
from pathlib import Path
import ast
ROOT = Path(__file__).resolve().parents[1]
tr = ROOT / 'alrajhi_client' / 'i18n' / 'translator.py'
pt = ROOT / 'alrajhi_client' / 'printing' / 'print_templates.py'
rw = ROOT / 'alrajhi_client' / 'views' / 'widgets' / 'reports_widget.py'
for p in (tr, pt, rw):
    ast.parse(p.read_text(encoding='utf-8'), filename=str(p))
text = tr.read_text(encoding='utf-8')
required = [
    'report_income_statement','report_balance_sheet','report_warehouse_valuation',
    'print_date_label','print_document_number','print_grand_total',
    'sales_return','purchase_return','production_order','production_order_generated_by'
]
missing = [k for k in required if text.count("'"+k+"'") < 3]
if missing:
    raise SystemExit('missing phase82 translation keys in all languages: ' + ', '.join(missing))
pt_text = pt.read_text(encoding='utf-8')
if 'def _tr(key:' not in pt_text or 'language_direction' not in pt_text:
    raise SystemExit('print templates are not connected to i18n')
rw_text = rw.read_text(encoding='utf-8')
for token in ['tr("period_label")','tr("report_income_statement")',"tr('period_subtitle'"]:
    if token not in rw_text:
        raise SystemExit('reports widget missing localized token: ' + token)
print('OK phase82 reports and printing localization')
