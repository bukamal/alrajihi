# -*- coding: utf-8 -*-
"""Phase 190 guard: production-order lifecycle must be a real tab, not a dialog wrapper."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')

checks = []
life = read('alrajhi_client/features/manufacturing/production_order_lifecycle_tab.py')
init = read('alrajhi_client/features/manufacturing/__init__.py')
schema = read('alrajhi_client/features/manufacturing/grids/manufacturing_column_schema.py')
translator = read('alrajhi_client/i18n/translator.py')

checks.append(('lifecycle tab file exists and extends BaseDocumentTab', 'class ProductionOrderDetailsTab(BaseDocumentTab)' in life))
checks.append(('legacy details tab is explicit fallback only', 'class LegacyProductionOrderDetailsTab(DialogDocumentTab)' in life))
checks.append(('features export lifecycle tab from new file', 'production_order_lifecycle_tab import ProductionOrderDetailsTab' in init))
checks.append(('reservations model/grid are used', 'self.res_model = ProductionLifecycleTableModel' in life and 'self.res_grid = ProductionLifecycleGrid' in life))
checks.append(('consumptions model/grid are used', 'self.cons_model = ProductionLifecycleTableModel' in life and 'self.cons_grid = ProductionLifecycleGrid' in life))
checks.append(('outputs model/grid are used', 'self.out_model = ProductionLifecycleTableModel' in life and 'self.out_grid = ProductionLifecycleGrid' in life))
checks.append(('lifecycle actions go through ManufacturingService', 'self.service.start_production' in life and 'self.service.consume_material' in life and 'self.service.complete_production' in life and 'self.service.reverse_production_order' in life))
checks.append(('operation state respects manufacturing policy', 'manufacturing_operation_policy.OP_ORDER_START' in life and 'manufacturing_operation_policy.OP_MATERIAL_CONSUME' in life and 'manufacturing_operation_policy.OP_OUTPUT_COMPLETE' in life))
checks.append(('context menus use delete operations via service', 'self.service.delete_consumption' in life and 'self.service.delete_output' in life))
checks.append(('lifecycle schemas exist', 'def production_reservations_schema' in schema and 'def production_consumptions_schema' in schema and 'def production_outputs_schema' in schema))
checks.append(('lifecycle translations exist', 'phase190_production_lifecycle_unified' in translator and 'manufacturing_lifecycle_summary' in translator))

failed = [name for name, ok in checks if not ok]
if failed:
    raise SystemExit('Phase190 guard failed:\n- ' + '\n- '.join(failed))
print('phase190_production_lifecycle_tab_guard passed')
