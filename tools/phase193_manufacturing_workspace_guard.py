# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
widget = ROOT / 'alrajhi_client/views/widgets/manufacturing_widget.py'
schema = ROOT / 'alrajhi_client/features/manufacturing/manufacturing_workspace_schema.py'
translator = ROOT / 'alrajhi_client/i18n/translator.py'

text = widget.read_text(encoding='utf-8')
module_header = text.split('class ManufacturingWidget', 1)[0]
schema_text = schema.read_text(encoding='utf-8')
tr = translator.read_text(encoding='utf-8')

assert 'from views.dialogs.bom_dialog import BOMDialog' not in module_header, 'ManufacturingWidget must not import BOMDialog at module level'
assert 'from views.dialogs.production_order_dialog import ProductionOrderDialog' not in module_header, 'ManufacturingWidget must not import ProductionOrderDialog at module level'
assert 'from views.dialogs.production_details_dialog import ProductionDetailsDialog' not in module_header, 'ManufacturingWidget must not import ProductionDetailsDialog at module level'
assert 'manufacturing.workspace.bom' in text, 'BOM table must use a stable workspace identity'
assert 'manufacturing.workspace.orders' in text, 'Orders table must use a stable workspace identity'
assert 'set_local_filter' in text, 'Manufacturing workspace must use SmartTableView local filtering'
assert '_source_row_for_index' in text and 'mapToSource' in text, 'Workspace must map proxy rows to source rows for actions'
assert 'orders_status_filter' in text, 'Orders list must expose a status filter'
assert 'orders_warehouse_filter' in text, 'Orders list must expose a warehouse filter'
assert 'visible_keys_for' in schema_text and 'workspace_preset_names' in schema_text, 'Workspace schema must define presets'
assert 'manufacturing_components_count' in schema_text, 'BOM columns must include components count'
for key in (
    'manufacturing_search_bom', 'manufacturing_search_orders', 'manufacturing_all_statuses',
    'manufacturing_workspace_preset_compact', 'manufacturing_workspace_preset_planner',
    'manufacturing_workspace_preset_warehouse', 'manufacturing_workspace_preset_manager',
):
    assert key in tr, f'Missing translation key: {key}'
print('phase193 manufacturing workspace guard passed')
