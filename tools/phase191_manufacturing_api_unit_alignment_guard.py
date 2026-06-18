# -*- coding: utf-8 -*-
"""Phase 191 guard: manufacturing unit/base-quantity alignment."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def text(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def require(cond, msg):
    if not cond:
        raise AssertionError(msg)


def main():
    schema_client = text('alrajhi_client/database/schema_manager.py')
    schema_server = text('alrajhi_server/database/schema_manager.py')
    for schema, name in [(schema_client, 'client schema'), (schema_server, 'server schema')]:
        for table in ['bom_lines', 'bom_snapshot_lines', 'material_reservations', 'production_consumptions', 'production_outputs']:
            require(f'"{table}"' in schema, f'{name}: missing REQUIRED_COLUMNS for {table}')
        for col in ['unit_id', 'conversion_factor', 'base_qty', 'reserved_base_qty', 'consumed_base_qty', 'produced_base_qty', 'barcode_scope']:
            require(col in schema, f'{name}: missing manufacturing unit/base column {col}')

    dao = text('alrajhi_client/database/dao/manufacturing_dao.py')
    require('_manufacturing_line_unit_payload' in dao, 'DAO must normalize manufacturing unit payloads')
    require('INSERT INTO bom_lines (bom_id, item_id, quantity, unit_id, conversion_factor, base_qty' in dao, 'DAO must persist unit/base data in bom_lines')
    require('INSERT INTO material_reservations (order_id, item_id, reserved_qty, consumed_qty, unit_id' in dao, 'DAO must persist unit/base data in reservations')
    require('INSERT INTO production_consumptions (order_id, item_id, consumed_qty, unit_id' in dao, 'DAO must persist unit/base data in consumptions')
    require('INSERT INTO production_outputs (order_id, item_id, produced_qty, unit_id' in dao, 'DAO must persist unit/base data in outputs')
    require('consumed_base_qty = CAST(COALESCE(consumed_base_qty, 0) AS REAL) +' in dao, 'DAO must update consumed_base_qty on consumption')

    server = text('alrajhi_server/repositories/http_route_sql/manufacturing.py')
    require('_manufacturing_line_unit_payload' in server, 'Server must normalize manufacturing unit payloads')
    require('INSERT INTO bom_lines (bom_id, item_id, quantity, unit_id, conversion_factor, base_qty' in server, 'Server must persist unit/base data in bom_lines')
    require('INSERT INTO material_reservations (order_id, item_id, reserved_qty, consumed_qty, unit_id' in server, 'Server must persist unit/base data in reservations')
    require('INSERT INTO production_consumptions (order_id, item_id, consumed_qty, unit_id' in server, 'Server must persist unit/base data in consumptions')
    require('INSERT INTO production_outputs (order_id, item_id, produced_qty, unit_id' in server, 'Server must persist unit/base data in outputs')
    require('LEFT JOIN item_units u ON u.id = mr.unit_id' in server, 'Server must expose reservation unit names')
    require('LEFT JOIN item_units u ON u.id = pc.unit_id' in server, 'Server must expose consumption unit names')
    require('LEFT JOIN item_units u ON u.id = po2.unit_id' in server, 'Server must expose output unit names')

    print('phase191_manufacturing_api_unit_alignment_guard passed')

if __name__ == '__main__':
    main()
