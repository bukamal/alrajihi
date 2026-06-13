#!/usr/bin/env python3
"""Phase 32 static/runtime-light invoice/offline integration guard.

This guard avoids PyQt/runtime DB dependencies and checks for the exact classes
of regressions found during manual testing:
- Remote invoices must not post client-side warehouse movements.
- Offline queued invoice IDs must be tolerated as negative IDs.
- Permanent queue 4xx failures must be marked failed, not replayed forever.
- Phase 30 inventory-ledger health/snapshot endpoints must exist.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def require(cond: bool, msg: str, failures: list[str]) -> None:
    if not cond:
        failures.append(msg)


def main() -> int:
    failures: list[str] = []
    inv_service = read('alrajhi_client/core/services/invoice_service.py')
    require('def _client_side_movements_enabled' in inv_service, 'InvoiceService missing remote/local movement gate', failures)
    require('return not bool(self.gateway.is_remote())' in inv_service, 'InvoiceService movement gate must disable movements in remote mode', failures)
    require('if self._client_side_movements_enabled():\n            warehouse_service.record_invoice_movements' in inv_service, 'create() must guard record_invoice_movements', failures)
    require('if self._client_side_movements_enabled():\n            warehouse_service.reverse_invoice_movements' in inv_service, 'update/delete must guard reverse_invoice_movements', failures)

    remote_inv = read('alrajhi_client/gateways/remote/invoice_gateway.py')
    local_inv = read('alrajhi_client/gateways/local/invoice_gateway.py')
    require('def is_remote(self) -> bool:' in remote_inv and 'return True' in remote_inv, 'RemoteInvoiceGateway.is_remote must return True', failures)
    require('def is_remote(self) -> bool:' in local_inv and 'return False' in local_inv, 'LocalInvoiceGateway.is_remote must return False', failures)

    rest = read('alrajhi_client/database/connection_rest.py')
    require("offline_queue.add_request(endpoint, method, data" in rest, 'RestClient must queue safe writes on connection failure', failures)
    require("return {'queued': True, 'queue_id': qid, 'id': -qid}" in rest, 'Queued writes must return stable negative id', failures)
    require("def get_inventory_ledger_health" in rest and "def get_inventory_ledger_snapshot" in rest, 'RestClient missing Phase 30 ledger health/snapshot methods', failures)

    queue = read('alrajhi_client/gateways/local/offline_queue_gateway.py')
    require('400, 401, 403, 404, 409, 422' in queue or all(f"API error {code}" in queue for code in (400, 401, 403, 404, 409, 422)),
            'Offline queue must permanently fail validation/auth/not-found/conflict 4xx responses', failures)
    require('offline_queue.mark_failed' in queue, 'Offline queue must mark permanent validation failures as failed', failures)

    items_api = read('alrajhi_server/api/items.py')
    require("/inventory-ledger/health" in items_api, 'Server missing /inventory-ledger/health endpoint', failures)
    require("/inventory-ledger/snapshot" in items_api, 'Server missing /inventory-ledger/snapshot endpoint', failures)

    inv_gateway = read('alrajhi_client/gateways/inventory_gateway.py')
    require('def ledger_health(' in inv_gateway and 'def ledger_snapshot(' in inv_gateway, 'InventoryGateway missing Phase 30 health/snapshot contract', failures)

    # Syntax/AST parse for all touched files.
    for rel in [
        'alrajhi_client/core/services/invoice_service.py',
        'alrajhi_client/core/services/inventory_service.py',
        'alrajhi_client/gateways/inventory_gateway.py',
        'alrajhi_client/gateways/local/inventory_gateway.py',
        'alrajhi_client/gateways/remote/inventory_gateway.py',
        'alrajhi_client/database/dao/inventory_ledger_dao.py',
        'alrajhi_client/database/connection_rest.py',
        'alrajhi_server/api/items.py',
    ]:
        try:
            ast.parse(read(rel), filename=rel)
        except SyntaxError as exc:
            failures.append(f'{rel}: syntax error: {exc}')

    if failures:
        print('Phase 32 invoice/ledger guard failed:')
        for f in failures:
            print(' -', f)
        return 1
    print('Phase 32 invoice/ledger guard passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
