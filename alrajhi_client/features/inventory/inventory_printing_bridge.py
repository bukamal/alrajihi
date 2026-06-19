# -*- coding: utf-8 -*-
"""Inventory/warehouse printing bridge (Phase 197).

Inventory UI components build data payloads; this bridge enforces the inventory
print policy and delegates rendering/output to printing_service.  Do not build
HTML directly in inventory widgets/documents.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List

from core.services.inventory_operation_policy import inventory_operation_policy
from core.services.settings_service import settings_service
from printing.printing_service import printing_service


class InventoryPrintingBridge:
    def _paper(self, paper: str = 'default') -> str:
        if paper and paper != 'default':
            return paper
        try:
            return settings_service.get_inventory_settings().get('print_template') or 'default'
        except Exception:
            return 'default'

    def _require(self, payload: Dict[str, Any] | None = None) -> None:
        inventory_operation_policy.require(inventory_operation_policy.OP_PRINT, context='inventory_printing_bridge', payload=payload or {})

    def transfer_payload(self, transfer: Dict[str, Any] | None = None, lines: Iterable[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        transfer = dict(transfer or {})
        rows = [dict(line or {}) for line in (lines or [])]
        if not rows and transfer:
            rows = [transfer]
        return {'transfer': transfer, 'lines': rows}

    def transfer_preview(self, payload: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.transfer_print(payload, parent, paper)

    def transfer_print(self, payload: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        self._require({'document': 'inventory_transfer'})
        return printing_service.inventory_transfer_print(payload, parent, self._paper(paper))

    def transfer_pdf(self, payload: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.transfer_print(payload, parent, paper)

    def balances_payload(self, rows: Iterable[Dict[str, Any]], **meta: Any) -> Dict[str, Any]:
        return {'rows': [dict(row or {}) for row in rows or []], **meta}

    def balances_preview(self, payload: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.balances_print(payload, parent, paper)

    def balances_print(self, payload: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        self._require({'document': 'inventory_balances'})
        return printing_service.inventory_balances_print(payload, parent, self._paper(paper))

    def movements_payload(self, rows: Iterable[Dict[str, Any]], **meta: Any) -> Dict[str, Any]:
        return {'rows': [dict(row or {}) for row in rows or []], **meta}

    def movements_preview(self, payload: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.movements_print(payload, parent, paper)

    def movements_print(self, payload: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        self._require({'document': 'inventory_movements'})
        return printing_service.inventory_movements_print(payload, parent, self._paper(paper))

    def ledger_payload(self, rows: Iterable[Dict[str, Any]], **meta: Any) -> Dict[str, Any]:
        return {'rows': [dict(row or {}) for row in rows or []], **meta}

    def ledger_preview(self, payload: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.ledger_print(payload, parent, paper)

    def ledger_print(self, payload: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        self._require({'document': 'inventory_ledger'})
        return printing_service.inventory_ledger_print(payload, parent, self._paper(paper))


inventory_printing_bridge = InventoryPrintingBridge()
