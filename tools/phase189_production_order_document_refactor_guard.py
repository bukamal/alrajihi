# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

prod_tab = (ROOT / 'alrajhi_client/features/manufacturing/production_order_document_tab.py').read_text(encoding='utf-8')
schema = (ROOT / 'alrajhi_client/features/manufacturing/grids/manufacturing_column_schema.py').read_text(encoding='utf-8')
model = (ROOT / 'alrajhi_client/features/manufacturing/grids/production_required_materials_model.py').read_text(encoding='utf-8')
grid = (ROOT / 'alrajhi_client/features/manufacturing/grids/production_required_materials_grid.py').read_text(encoding='utf-8')
rest = (ROOT / 'alrajhi_client/database/connection_rest.py').read_text(encoding='utf-8')
remote = (ROOT / 'alrajhi_client/gateways/remote/manufacturing_gateway.py').read_text(encoding='utf-8')
tr = (ROOT / 'alrajhi_client/i18n/translator.py').read_text(encoding='utf-8')

assert 'class ProductionOrderDocumentTab(BaseDocumentTab)' in prod_tab
assert 'DialogDocumentTab' in prod_tab and 'LegacyProductionOrderDocumentTab' in prod_tab
assert 'ProductionOrderDialog' in prod_tab and 'LegacyProductionOrderDocumentTab' in prod_tab
assert 'dialog_cls=ProductionOrderDialog' not in prod_tab.split('class ProductionOrderDocumentTab(BaseDocumentTab)', 1)[1]
assert 'ProductionRequiredMaterialsModel' in prod_tab
assert 'ProductionRequiredMaterialsGrid' in prod_tab
assert 'manufacturing_operation_policy.OP_ORDER_CREATE' in prod_tab
assert 'settings_service.get_manufacturing_settings()' in prod_tab
assert 'create_production_order(payload)' in prod_tab
assert 'production_required_materials_schema' in schema
assert 'manufacturing_column_required_qty' in schema
assert 'class ProductionRequiredMaterialsModel' in model
assert 'insufficient_lines' in model
assert 'class ProductionRequiredMaterialsGrid(TransactionLineGrid)' in grid
assert 'warehouse_id' in rest and 'get_required_materials(self, bom_id: int, planned_qty, warehouse_id=None)' in rest
assert 'warehouse_id=warehouse_id' in remote
for key in [
    'manufacturing_column_required_qty',
    'manufacturing_production_summary',
    'manufacturing_material_shortage_line',
    'phase189_production_order_document_unified',
]:
    assert key in tr, key

print('phase189 production order document refactor guard passed')
