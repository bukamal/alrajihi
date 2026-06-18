# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')

checks = []

def require(condition: bool, message: str) -> None:
    if not condition:
        checks.append(message)

bridge = read('alrajhi_client/features/manufacturing/manufacturing_printing_bridge.py')
printing = read('alrajhi_client/printing/printing_service.py')
templates = read('alrajhi_client/printing/print_templates.py')
bom_tab = read('alrajhi_client/features/manufacturing/bom_document_tab.py')
lifecycle = read('alrajhi_client/features/manufacturing/production_order_lifecycle_tab.py')
translator = read('alrajhi_client/i18n/translator.py')

require('class ManufacturingPrintingBridge' in bridge, 'Missing ManufacturingPrintingBridge')
require('manufacturing_operation_policy.require' in bridge and 'OP_PRINT' in bridge, 'Bridge must enforce manufacturing OP_PRINT')
require('printing_service.manufacturing_bom_preview' in bridge, 'Bridge must call central BOM printing service')
require('printing_service.manufacturing_pick_ticket_preview' in bridge, 'Bridge must call central pick-ticket printing service')
require('printing_service.manufacturing_cost_report_preview' in bridge, 'Bridge must call central cost-report printing service')
require('def manufacturing_bom_html' in templates, 'Missing BOM print template')
require('def manufacturing_pick_ticket_html' in templates, 'Missing pick-ticket print template')
require('def manufacturing_cost_report_html' in templates, 'Missing manufacturing cost-report template')
require("_normalize_paper(paper, settings, \"manufacturing" in templates, 'Manufacturing templates must use normalized paper/settings')
require('manufacturing_bom_html' in printing, 'printing_service must expose manufacturing BOM output')
require('manufacturing_pick_ticket_html' in printing, 'printing_service must expose manufacturing pick ticket output')
require('manufacturing_cost_report_html' in printing, 'printing_service must expose manufacturing cost report output')
require('manufacturing_printing_bridge.bom_preview' in bom_tab, 'BOM tab must use manufacturing_printing_bridge')
require('manufacturing_printing_bridge.production_order_preview' in lifecycle, 'Lifecycle tab must use bridge for order print')
require('manufacturing_printing_bridge.pick_ticket_preview' in lifecycle, 'Lifecycle tab must use bridge for pick ticket')
require('manufacturing_printing_bridge.cost_report_preview' in lifecycle, 'Lifecycle tab must use bridge for cost report')
for key in ('manufacturing_bom_document', 'manufacturing_pick_ticket', 'manufacturing_cost_report', 'warehouse_keeper'):
    require(key in translator, f'Missing translation key: {key}')

if checks:
    print('Phase192 guard failed:')
    for item in checks:
        print('-', item)
    sys.exit(1)
print('Phase192 manufacturing printing bridge guard passed')
