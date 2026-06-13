#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static regression checks for manufacturing UI/API data contracts."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []

def text(rel):
    return (ROOT / rel).read_text(encoding='utf-8')

pod = text('alrajhi_client/views/dialogs/production_order_dialog.py')
pdd = text('alrajhi_client/views/dialogs/production_details_dialog.py')
api = text('alrajhi_server/api/manufacturing.py')
svc = text('alrajhi_client/core/services/manufacturing_service.py')

if "QVBoxLayout(self.content_widget)" not in pdd:
    errors.append('ProductionDetailsDialog must attach its layout to content_widget, not the dialog itself.')
if "_material_label(mat)" not in pod:
    errors.append('ProductionOrderDialog must use a material-name fallback for required materials.')
if "_item_label(r)" not in pdd or "_item_label(c)" not in pdd:
    errors.append('ProductionDetailsDialog must use item-name fallbacks for detail rows.')
for fragment in ["i.name AS item_name", "rw.name AS raw_warehouse_name", "ow.name AS output_warehouse_name"]:
    if fragment not in api:
        errors.append(f'Manufacturing API must return display names: {fragment}')
if "return self.gateway.check_materials_availability(*args)" not in svc:
    errors.append('ManufacturingService.check_materials_availability must forward *args correctly.')

if errors:
    for err in errors:
        print('ERROR:', err)
    sys.exit(1)
print('manufacturing_ui_guard: OK')
