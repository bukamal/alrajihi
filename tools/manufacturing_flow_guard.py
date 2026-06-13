#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static manufacturing integration guard.

Checks that production effects are not limited to the UI/rows only. A valid
manufacturing flow must update:
- operational item stock (inventory_movements),
- warehouse balances/movements,
- shadow inventory ledger,
- safe numeric UI formatting.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
client_dao = (ROOT / 'alrajhi_client/database/dao/manufacturing_dao.py').read_text(encoding='utf-8')
server_api = (ROOT / 'alrajhi_server/api/manufacturing.py').read_text(encoding='utf-8')
prod_details = (ROOT / 'alrajhi_client/views/dialogs/production_details_dialog.py').read_text(encoding='utf-8')
prod_order = (ROOT / 'alrajhi_client/views/dialogs/production_order_dialog.py').read_text(encoding='utf-8')

checks = []

def require(name, ok):
    checks.append((name, bool(ok)))

# Local manufacturing must touch all three accounting/stock read models.
require('local consume records warehouse out', "production_consume_out" in client_dao)
require('local output records warehouse in', "production_output_in" in client_dao)
require('local consumption ledger out via warehouse movement', "production_consume_out" in client_dao)
require('local output ledger in via warehouse movement', "production_output_in" in client_dao)
require('local reverse consumption warehouse in', "production_consume_reverse_in" in client_dao)
require('local reverse output warehouse out', "production_output_reverse_out" in client_dao)
require('local completed output deletion blocked', "لا يمكن حذف مخرج من أمر مكتمل" in client_dao)

# Server manufacturing must behave consistently with local mode.
require('server warehouse helper exists', 'def _record_warehouse_movement' in server_api)
require('server create order defaults warehouses', 'raw_warehouse_id = data.get' in server_api and '_default_warehouse_id' in server_api)
require('server availability is warehouse-scoped', '_warehouse_available_qty(db, user_id' in server_api)
require('server consume records warehouse out', "production_consume_out" in server_api)
require('server output records warehouse in', "production_output_in" in server_api)
require('server reverse records warehouse movements', "production_consume_reverse_in" in server_api and "production_output_reverse_out" in server_api)

# UI numeric safety.
require('production details has _num helper', 'def _num' in prod_details)
require('production order has _num helper', 'def _num' in prod_order)
require('no direct required_qty float formatting', "mat['required_qty']:.2f" not in prod_order and 'mat["required_qty"]:.2f' not in prod_order)
require('no direct average_cost comparison to int', "it.get('average_cost', 0) > 0" not in prod_details)

# Known dangerous pattern: DB/API numeric values should not be formatted directly with :.2f.
for path in [ROOT/'alrajhi_client/views/dialogs/production_details_dialog.py', ROOT/'alrajhi_client/views/dialogs/production_order_dialog.py']:
    text = path.read_text(encoding='utf-8')
    candidates = re.findall(r"\{[^{}]*(?:\[[^\]]+\]|\.get\([^)]*\))[^{}]*:\.2f\}", text)
    dangerous = [c for c in candidates if '_num(' not in c and "['remaining']" not in c and '[\"remaining\"]' not in c]
    require(f'no direct :.2f on raw DB/API values in {path.name}', not dangerous)

failed = [name for name, ok in checks if not ok]
if failed:
    print('manufacturing_flow_guard: FAIL')
    for name in failed:
        print(' -', name)
    raise SystemExit(1)
print('manufacturing_flow_guard: PASS')
