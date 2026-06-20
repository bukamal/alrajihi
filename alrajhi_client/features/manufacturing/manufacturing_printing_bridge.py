# -*- coding: utf-8 -*-
"""Unified manufacturing printing bridge.

This bridge is the only printing boundary for manufacturing tabs.  UI documents
build or provide IDs/payloads here; the bridge enforces manufacturing print
policy and then delegates to the central printing_service.  Templates and paper
selection remain owned by printing.print_templates / settings_service.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional

from core.services.manufacturing_operation_policy import manufacturing_operation_policy
from core.services.manufacturing_service import manufacturing_service
from core.services.settings_service import settings_service
from i18n import translate
from printing.printing_service import printing_service


def _dec(value, default='0') -> Decimal:
    try:
        if value in (None, ''):
            return Decimal(str(default))
        return Decimal(str(value))
    except Exception:
        return Decimal(str(default))


def _line_item_name(row: Dict[str, Any]) -> str:
    return str(row.get('item_name') or row.get('product_name') or row.get('name') or row.get('item') or row.get('component_name') or row.get('item_id') or '')


def _display_currency() -> str:
    try:
        return str(settings_service.get('display_currency', 'SYP') or 'SYP')
    except Exception:
        return 'SYP'


def _money_context() -> Dict[str, Any]:
    currency = _display_currency()
    return {
        'display_currency': currency,
        'currency': currency,
        'currency_code': currency,
    }


class ManufacturingPrintingBridge:
    """Build manufacturing print payloads and call the unified printing service."""

    def _require_print(self, context: str, payload: Optional[Dict[str, Any]] = None) -> None:
        manufacturing_operation_policy.require(
            manufacturing_operation_policy.OP_PRINT,
            context=context,
            payload=payload or {},
        )

    def _paper(self, key: str = 'print_template', fallback: str = 'default') -> str:
        try:
            cfg = settings_service.get_manufacturing_settings() or {}
            return str(cfg.get(key) or cfg.get('print_template') or fallback or 'default')
        except Exception:
            return fallback or 'default'

    def bom_payload(self, bom_id: Optional[int] = None, bom_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        bom = dict(bom_data or {})
        if bom_id and not bom:
            bom = dict(manufacturing_service.get_bom(int(bom_id)) or {})
        lines = list(bom.get('lines') or bom.get('components') or bom.get('bom_lines') or [])
        material_cost = Decimal('0')
        waste_cost = Decimal('0')
        base_qty = Decimal('0')
        for row in lines:
            qty = _dec(row.get('quantity') or row.get('qty') or row.get('component_qty') or 0)
            factor = _dec(row.get('conversion_factor') or 1, '1')
            cost = _dec(row.get('unit_cost') or row.get('cost') or row.get('purchase_price') or 0)
            waste = _dec(row.get('waste_percent') or 0)
            if waste > 1:
                waste = waste / Decimal('100')
            line_base = _dec(row.get('base_qty') or row.get('required_base_qty') or (qty * factor))
            line_cost = _dec(row.get('total_cost') or (qty * cost))
            material_cost += line_cost
            waste_cost += line_cost * waste
            base_qty += line_base
        output_qty = _dec(bom.get('output_qty') or bom.get('quantity') or bom.get('product_qty') or 1, '1')
        unit_cost = (material_cost + waste_cost) / output_qty if output_qty else Decimal('0')
        payload = {
            'bom': bom,
            'lines': lines,
            'summary': {
                'material_cost': material_cost,
                'waste_cost': waste_cost,
                'total_cost': material_cost + waste_cost,
                'base_qty': base_qty,
                'line_count': len(lines),
                'output_qty': output_qty,
                'unit_cost_output': unit_cost,
            },
        }
        payload.update(_money_context())
        return payload

    def production_payload(self, order_id: int) -> Dict[str, Any]:
        order = manufacturing_service.get_production_order(int(order_id)) or {}
        payload = {
            'order': order,
            'reservations': manufacturing_service.get_reservations(int(order_id)) or [],
            'consumptions': manufacturing_service.get_consumptions(int(order_id)) or [],
            'outputs': manufacturing_service.get_outputs(int(order_id)) or [],
        }
        payload.update(_money_context())
        return payload

    def pick_ticket_payload(self, order_id: int) -> Dict[str, Any]:
        payload = self.production_payload(order_id)
        rows: List[Dict[str, Any]] = []
        for row in payload.get('reservations') or []:
            reserved = _dec(row.get('reserved_qty') or row.get('required_qty') or row.get('qty') or 0)
            consumed = _dec(row.get('consumed_qty') or 0)
            remaining = row.get('remaining_qty')
            if remaining in (None, ''):
                remaining = reserved - consumed
            rows.append({
                **dict(row),
                'item_name': _line_item_name(row),
                'pick_qty': remaining,
                'remaining_qty': remaining,
                'reserved_qty': reserved,
                'consumed_qty': consumed,
            })
        return {'order': payload.get('order') or {}, 'lines': rows}

    def cost_report_payload(self, order_id: int) -> Dict[str, Any]:
        payload = self.production_payload(order_id)
        cons_total = sum((_dec(r.get('total_cost') or (_dec(r.get('consumed_qty') or r.get('qty')) * _dec(r.get('unit_cost')))) for r in payload.get('consumptions') or []), Decimal('0'))
        out_total = sum((_dec(r.get('total_cost') or (_dec(r.get('produced_qty') or r.get('qty')) * _dec(r.get('unit_cost')))) for r in payload.get('outputs') or []), Decimal('0'))
        produced_qty = sum((_dec(r.get('produced_qty') or r.get('qty')) for r in payload.get('outputs') or []), Decimal('0'))
        payload['summary'] = {
            'consumption_cost': cons_total,
            'output_cost': out_total,
            'variance_cost': out_total - cons_total,
            'produced_qty': produced_qty,
            'unit_cost': (cons_total / produced_qty) if produced_qty else Decimal('0'),
        }
        return payload

    # BOM
    def bom_preview(self, bom_id: Optional[int] = None, bom_data: Optional[Dict[str, Any]] = None, parent=None) -> bool:
        return self.bom_print(bom_id, bom_data, parent)

    def bom_print(self, bom_id: Optional[int] = None, bom_data: Optional[Dict[str, Any]] = None, parent=None) -> bool:
        self._require_print('bom_print', {'bom_id': bom_id})
        return printing_service.manufacturing_bom_print(self.bom_payload(bom_id, bom_data), parent, self._paper('bom_print_template'))

    def bom_pdf(self, bom_id: Optional[int] = None, bom_data: Optional[Dict[str, Any]] = None, parent=None) -> bool:
        return self.bom_print(bom_id, bom_data, parent)

    # Production order full document
    def production_order_preview(self, order_id: int, parent=None) -> bool:
        return self.production_order_print(order_id, parent)

    def production_order_print(self, order_id: int, parent=None) -> bool:
        self._require_print('production_order_print', {'order_id': order_id})
        return printing_service.manufacturing_production_order_print(self.production_payload(order_id), parent, self._paper('production_order_print_template'))

    def production_order_pdf(self, order_id: int, parent=None) -> bool:
        return self.production_order_print(order_id, parent)

    # Raw material pick ticket
    def pick_ticket_preview(self, order_id: int, parent=None) -> bool:
        return self.pick_ticket_print(order_id, parent)

    def pick_ticket_print(self, order_id: int, parent=None) -> bool:
        self._require_print('pick_ticket_print', {'order_id': order_id})
        return printing_service.manufacturing_pick_ticket_print(self.pick_ticket_payload(order_id), parent, self._paper('pick_ticket_print_template'))

    def pick_ticket_pdf(self, order_id: int, parent=None) -> bool:
        return self.pick_ticket_print(order_id, parent)

    # Cost report
    def cost_report_preview(self, order_id: int, parent=None) -> bool:
        return self.cost_report_print(order_id, parent)

    def cost_report_print(self, order_id: int, parent=None) -> bool:
        self._require_print('cost_report_print', {'order_id': order_id})
        return printing_service.manufacturing_cost_report_print(self.cost_report_payload(order_id), parent, self._paper('cost_report_print_template'))

    def cost_report_pdf(self, order_id: int, parent=None) -> bool:
        return self.cost_report_print(order_id, parent)


manufacturing_printing_bridge = ManufacturingPrintingBridge()
