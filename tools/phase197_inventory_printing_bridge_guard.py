# -*- coding: utf-8 -*-
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
checks = {
    'bridge': ROOT/'alrajhi_client/features/inventory/inventory_printing_bridge.py',
    'printing_service': ROOT/'alrajhi_client/printing/printing_service.py',
    'templates': ROOT/'alrajhi_client/printing/print_templates.py',
    'policy': ROOT/'alrajhi_client/core/services/inventory_operation_policy.py',
    'transfer_tab': ROOT/'alrajhi_client/features/inventory/documents/inventory_transfer_document_tab.py',
    'warehouses': ROOT/'alrajhi_client/views/widgets/warehouses_widget.py',
}
for name, path in checks.items():
    if not path.exists():
        raise SystemExit(f'missing {name}: {path}')
text = {name: path.read_text(encoding='utf-8') for name, path in checks.items()}
required = [
    ('bridge', 'inventory_operation_policy.OP_PRINT'),
    ('bridge', 'printing_service.inventory_transfer_preview'),
    ('printing_service', 'inventory_transfer_preview'),
    ('printing_service', 'inventory_balances_preview'),
    ('printing_service', 'inventory_movements_preview'),
    ('templates', 'def inventory_transfer_html'),
    ('templates', 'def inventory_balances_html'),
    ('templates', 'def inventory_movements_html'),
    ('templates', 'def inventory_ledger_html'),
    ('policy', 'OP_PRINT'),
    ('policy', 'allow_print'),
    ('transfer_tab', 'inventory_printing_bridge.transfer_preview'),
    ('warehouses', 'print_selected_transfer'),
]
for name, needle in required:
    if needle not in text[name]:
        raise SystemExit(f'guard failed: {needle} not found in {name}')
print('phase197_inventory_printing_bridge_guard passed')
