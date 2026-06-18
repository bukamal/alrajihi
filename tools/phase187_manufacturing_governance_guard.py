# -*- coding: utf-8 -*-
"""Phase 187 guard: manufacturing governance foundation."""
from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def fail(msg: str) -> None:
    raise SystemExit(f'Phase187 guard failed: {msg}')


def require_contains(rel: str, needles: list[str]) -> None:
    text = read(rel)
    for needle in needles:
        if needle not in text:
            fail(f'{rel} missing {needle!r}')


require_contains('alrajhi_client/core/services/settings_service.py', [
    'def get_manufacturing_settings',
    "'default_raw_warehouse_id'",
    "'default_output_warehouse_id'",
    "'operations'",
    "'allow_material_consume'",
    "'allow_order_reverse'",
    "'barcode_scanner'",
])

require_contains('alrajhi_client/core/services/manufacturing_operation_policy.py', [
    'class ManufacturingOperationPolicy',
    "OP_BOM_CREATE = 'bom_create'",
    "OP_ORDER_CREATE = 'order_create'",
    "OP_MATERIAL_CONSUME = 'material_consume'",
    "OP_OUTPUT_COMPLETE = 'output_complete'",
    'permission_service.can',
    'settings_service.get_manufacturing_settings',
    'manufacturing_operation_policy = ManufacturingOperationPolicy()',
])

require_contains('alrajhi_client/core/services/manufacturing_service.py', [
    'from core.services.manufacturing_operation_policy import manufacturing_operation_policy',
    'def _require(',
    'OP_BOM_CREATE',
    'OP_ORDER_CREATE',
    'OP_ORDER_START',
    'OP_MATERIAL_CONSUME',
    'OP_OUTPUT_COMPLETE',
    'OP_ORDER_REVERSE',
])

require_contains('alrajhi_client/core/services/permission_service.py', [
    'ACTION_USE_MANUFACTURING',
    "'manufacturing.use'",
    "'manufacturing.bom.create'",
    "'manufacturing.material.consume'",
    "'manufacturing.output.complete'",
    "'manufacturing.cost.view'",
    "'manufacturing.print'",
])

require_contains('alrajhi_client/core/services/rbac_service.py', [
    "'manufacturing.use'",
    "'manufacturing.bom.create'",
    "'manufacturing.order.create'",
    "'manufacturing.material.consume'",
    "'manufacturing.output.complete'",
    "'manufacturing.print'",
])

for rel in ['alrajhi_client/database/migrations.py', 'alrajhi_server/database/migrations.py']:
    require_contains(rel, [
        'Phase187: Manufacturing operation-level permissions',
        "'manufacturing.use'",
        "'manufacturing.bom.create'",
        "'manufacturing.order.reverse'",
        "'manufacturing.print'",
    ])

# Manufacturing feature layer must not bypass settings/services/gateways.
for path in (ROOT / 'alrajhi_client/features/manufacturing').rglob('*.py'):
    text = path.read_text(encoding='utf-8')
    banned = ['QSettings', 'requests.', 'from database', 'import database', 'from database.dao', 'connection_rest']
    for needle in banned:
        if needle in text:
            fail(f'{path.relative_to(ROOT)} contains banned dependency {needle!r}')
    ui_literals = re.findall(r'(QLabel|QPushButton|QAction|QGroupBox|setText|setPlaceholderText)\s*\(\s*["\']([^"\']+)["\']', text)
    for call, literal in ui_literals:
        if literal and not literal.startswith(('bom', 'production', 'manufacturing')):
            fail(f'{path.relative_to(ROOT)} has hardcoded UI literal via {call}: {literal!r}')

print('Phase187 manufacturing governance guard passed')
