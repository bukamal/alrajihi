# -*- coding: utf-8 -*-
"""Point-of-sale service for fast barcode/touch sales.

The POS service remains a thin operational layer over normal sale invoices, but
Phase 175 routes barcode entry through the same exact barcode pipeline used by
transactions and materials.  Unit barcodes are now first-class POS inputs: a
barcode can resolve to a base material or to a specific selling unit with its own
conversion factor.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from core.services.audit_service import audit_service
from core.services.barcode_input_service import barcode_input_service
from core.services.branch_service import branch_service
from core.services.cashbox_service import cashbox_service
from core.services.invoice_service import invoice_service
from core.services.settings_service import settings_service
from core.services.pos_operation_policy import pos_operation_policy
from core.services.warehouse_service import warehouse_service
from currency import currency
from i18n import translate


class POSException(ValueError):
    """Raised for user-facing POS validation errors."""


@dataclass
class POSLine:
    item_id: int
    barcode: str
    name: str
    unit: str
    qty: Decimal
    unit_price_usd: Decimal
    available_qty: Decimal
    unit_id: Optional[int] = None
    conversion_factor: Decimal = Decimal('1')
    base_qty: Decimal = Decimal('0')
    barcode_scope: str = 'item'
    variant_id: Optional[int] = None
    variant_color: str = ''
    variant_size: str = ''
    variant_sku: str = ''

    @property
    def line_key(self) -> str:
        return f"{self.item_id}:{self.variant_id or ''}:{self.unit_id or ''}:{self.conversion_factor}"

    @property
    def total_usd(self) -> Decimal:
        return self.qty * self.unit_price_usd

    def as_invoice_line(self) -> Dict:
        return {
            'item_id': self.item_id,
            'quantity': self.qty,
            'unit': self.unit,
            'unit_id': self.unit_id,
            'conversion_factor': self.conversion_factor,
            'base_qty': self.base_qty or (self.qty * self.conversion_factor),
            'quantity_in_base': self.base_qty or (self.qty * self.conversion_factor),
            'unit_price': self.unit_price_usd,
            'total': self.total_usd,
            'description': 'POS',
            'barcode': self.barcode,
            'barcode_scope': self.barcode_scope,
            'variant_id': self.variant_id,
            'variant_color': self.variant_color,
            'variant_size': self.variant_size,
            'variant_sku': self.variant_sku,
            'matched_barcode': self.barcode,
        }

    def as_dict(self) -> Dict:
        return {
            'item_id': self.item_id,
            'barcode': self.barcode,
            'name': self.name,
            'unit': self.unit,
            'unit_id': self.unit_id,
            'conversion_factor': self.conversion_factor,
            'qty': self.qty,
            'base_qty': self.base_qty,
            'unit_price_usd': self.unit_price_usd,
            'available_qty': self.available_qty,
            'barcode_scope': self.barcode_scope,
            'variant_id': self.variant_id,
            'variant_color': self.variant_color,
            'variant_size': self.variant_size,
            'variant_sku': self.variant_sku,
            'total_usd': self.total_usd,
        }


@dataclass
class POSCart:
    lines: List[POSLine] = field(default_factory=list)
    warehouse_id: Optional[int] = None
    cashbox_id: Optional[int] = None
    shift_id: Optional[int] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec='seconds'))
    note: str = ''

    @property
    def total_usd(self) -> Decimal:
        total = Decimal('0')
        for line in self.lines:
            total += line.total_usd
        return total

    def as_dict(self) -> Dict:
        return {
            'created_at': self.created_at,
            'note': self.note,
            'warehouse_id': self.warehouse_id,
            'cashbox_id': self.cashbox_id,
            'shift_id': self.shift_id,
            'total_usd': self.total_usd,
            'lines': [line.as_dict() for line in self.lines],
        }


class POSService:
    def __init__(self):
        self.suspended_carts: List[POSCart] = []

    def new_cart(self, warehouse_id: int | None = None, cashbox_id: int | None = None, shift_id: int | None = None) -> POSCart:
        settings = settings_service.get_pos_settings()
        default_cashbox = cashbox_id or self._int_or_none(settings.get('default_cashbox_id'))
        default_cashbox = default_cashbox or cashbox_service.default_cashbox_id(branch_service.current_branch_id())
        default_warehouse = warehouse_id or self._int_or_none(settings.get('default_warehouse_id')) or warehouse_service.default_warehouse_id()
        shift = cashbox_service.current_open_shift(default_cashbox) if (default_cashbox and settings.get('use_shifts')) else None
        return POSCart(
            warehouse_id=default_warehouse,
            cashbox_id=default_cashbox,
            shift_id=shift_id or ((shift or {}).get('id') if shift else None),
        )

    def _int_or_none(self, value) -> Optional[int]:
        try:
            value = int(value)
            return value or None
        except Exception:
            return None

    def _decimal(self, value, default='0') -> Decimal:
        try:
            return Decimal(str(value if value is not None else default))
        except Exception:
            return Decimal(str(default))

    def _require_operation(self, operation: str) -> None:
        try:
            pos_operation_policy.require(operation)
        except PermissionError as exc:
            raise POSException(str(exc))

    def _matched_unit(self, item: Dict) -> Dict:
        matched = item.get('matched_unit') or {}
        return matched if isinstance(matched, dict) else {}

    def _unit_factor(self, item: Dict) -> Decimal:
        matched = self._matched_unit(item)
        factor = self._decimal(
            matched.get('conversion_factor')
            or item.get('conversion_factor')
            or 1,
            '1',
        )
        return factor if factor > 0 else Decimal('1')

    def _unit_id(self, item: Dict):
        matched = self._matched_unit(item)
        return matched.get('unit_id') or matched.get('id') or item.get('unit_id')

    def _unit_name(self, item: Dict) -> str:
        matched = self._matched_unit(item)
        return str(
            matched.get('unit_name')
            or matched.get('unit')
            or item.get('unit')
            or item.get('unit_name')
            or translate('unit_piece')
        )

    def _matched_barcode(self, item: Dict, raw_code: str) -> str:
        matched = self._matched_unit(item)
        return str(item.get('matched_barcode') or matched.get('barcode') or item.get('barcode') or raw_code or '').strip()

    def lookup_item(self, code: str, *, mode: str = 'auto') -> Dict:
        result = barcode_input_service.lookup_entry(code, mode=mode)
        if result.item:
            return result.item
        key = result.message_key or 'pos_item_not_found'
        if key == 'transaction_barcode_not_found':
            raise POSException(translate('pos_barcode_not_found', code=result.normalized))
        if key == 'transaction_search_ambiguous':
            raise POSException(translate('pos_search_ambiguous', text=result.normalized))
        if key in ('transaction_barcode_empty', 'transaction_search_empty'):
            raise POSException(translate('pos_scan_empty'))
        raise POSException(translate('pos_item_not_found', text=result.normalized or code))

    def _variant_info(self, item: Dict) -> Dict:
        matched = item.get('matched_variant') or {}
        if not isinstance(matched, dict):
            matched = {}
        return {
            'variant_id': self._int_or_none(matched.get('variant_id') or matched.get('id') or item.get('variant_id')),
            'variant_color': str(matched.get('color') or item.get('variant_color') or ''),
            'variant_size': str(matched.get('size') or item.get('variant_size') or ''),
            'variant_sku': str(matched.get('sku') or item.get('variant_sku') or ''),
        }

    def _line_base_qty_for_item(self, cart: POSCart, item_id: int, excluding: POSLine | None = None) -> Decimal:
        total = Decimal('0')
        for line in cart.lines:
            if line is excluding:
                continue
            if int(line.item_id) == int(item_id):
                total += line.base_qty or (line.qty * line.conversion_factor)
        return total

    def add_scan(self, cart: POSCart, code: str, qty: Decimal | int | str = Decimal('1'), *, mode: str = 'auto') -> POSLine:
        item = self.lookup_item(code, mode=mode)
        qty = self._decimal(qty, '1')
        if qty <= 0:
            raise POSException(translate('pos_qty_must_be_positive'))
        item_id = int(item['id'])
        factor = self._unit_factor(item)
        unit_id = self._unit_id(item)
        unit_name = self._unit_name(item)
        barcode = self._matched_barcode(item, code)
        variant_info = self._variant_info(item)
        barcode_scope = str(item.get('barcode_scope') or ('variant' if variant_info.get('variant_id') else ('unit' if self._matched_unit(item) else 'item')))
        warehouse_id = cart.warehouse_id or warehouse_service.default_warehouse_id()
        try:
            available_base = self._decimal(warehouse_service.available_qty(item_id, warehouse_id))
        except Exception:
            available_base = self._decimal(item.get('available', item.get('quantity', 0)))
        available_display = available_base / factor if factor else available_base
        base_price = self._decimal(item.get('selling_price', 0))
        unit_price = base_price * factor
        if unit_price < 0:
            raise POSException(translate('pos_invalid_sale_price'))
        is_service = item.get('item_type') == 'خدمة'
        line_base_qty = qty * factor
        existing = next((line for line in cart.lines if line.line_key == f"{item_id}:{variant_info.get('variant_id') or ''}:{unit_id or ''}:{factor}"), None)
        item_total_base = self._line_base_qty_for_item(cart, item_id, excluding=existing)
        new_base_total = item_total_base + line_base_qty + ((existing.base_qty or existing.qty * existing.conversion_factor) if existing else Decimal('0'))
        allow_negative = bool(settings_service.get_pos_settings().get('allow_negative_stock'))
        if not is_service and not allow_negative and new_base_total > available_base:
            raise POSException(translate('pos_insufficient_stock', item=item.get('name', ''), available=available_display))
        if existing:
            existing.qty += qty
            existing.base_qty = existing.qty * existing.conversion_factor
            existing.available_qty = available_display
            return existing
        line = POSLine(
            item_id=item_id,
            barcode=barcode,
            name=str(item.get('name') or ''),
            unit=unit_name,
            unit_id=self._int_or_none(unit_id),
            conversion_factor=factor,
            qty=qty,
            base_qty=line_base_qty,
            unit_price_usd=unit_price,
            available_qty=available_display,
            barcode_scope=barcode_scope,
            variant_id=variant_info.get('variant_id'),
            variant_color=variant_info.get('variant_color') or '',
            variant_size=variant_info.get('variant_size') or '',
            variant_sku=variant_info.get('variant_sku') or '',
        )
        cart.lines.append(line)
        return line

    def remove_line(self, cart: POSCart, item_id: int) -> None:
        self._require_operation(pos_operation_policy.OP_REMOVE_LINE)
        cart.lines = [line for line in cart.lines if int(line.item_id) != int(item_id)]

    def remove_line_at(self, cart: POSCart, row: int) -> None:
        self._require_operation(pos_operation_policy.OP_REMOVE_LINE)
        try:
            if 0 <= int(row) < len(cart.lines):
                cart.lines.pop(int(row))
        except Exception:
            pass

    def clear(self, cart: POSCart) -> None:
        self._require_operation(pos_operation_policy.OP_CLEAR_CART)
        cart.lines.clear()

    def suspend(self, cart: POSCart, note: str = '') -> int:
        self._require_operation(pos_operation_policy.OP_SUSPEND)
        if not cart.lines:
            raise POSException(translate('pos_cannot_suspend_empty'))
        cart.note = note or f"POS {datetime.now().strftime('%H:%M:%S')}"
        self.suspended_carts.append(cart)
        audit_service.log('POS_SUSPEND', 'POS_CART', None, new_values=cart.as_dict(), details='تعليق بيع سريع')
        return len(self.suspended_carts) - 1

    def resume(self, index: int) -> POSCart:
        self._require_operation(pos_operation_policy.OP_RESUME)
        try:
            cart = self.suspended_carts.pop(index)
        except Exception:
            raise POSException(translate('pos_suspended_cart_missing'))
        audit_service.log('POS_RESUME', 'POS_CART', None, new_values=cart.as_dict(), details='استرجاع بيع معلق')
        return cart

    def checkout(self, cart: POSCart, payment_method: str = 'cash', paid_usd: Decimal | None = None) -> int:
        self._require_operation(pos_operation_policy.OP_CHECKOUT)
        if not cart.lines:
            raise POSException(translate('pos_cannot_checkout_empty'))
        total = cart.total_usd
        if total <= 0:
            raise POSException(translate('pos_total_must_be_positive'))
        if paid_usd is None:
            paid_usd = total
        paid_usd = self._decimal(paid_usd, '0')
        if paid_usd < 0:
            raise POSException(translate('pos_paid_cannot_be_negative'))
        if paid_usd > total:
            paid_usd = total
        if settings_service.pos_shifts_enabled():
            shift = cashbox_service.current_open_shift(cart.cashbox_id)
            if not shift:
                raise POSException(translate('open_shift_before_checkout'))
            cart.shift_id = shift.get('id')
        else:
            cart.shift_id = None
        data = {
            'type': 'sale',
            'customer_id': None,
            'supplier_id': None,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'reference': invoice_service.next_reference('sale'),
            'notes': f"POS Fast Sale - {payment_method}",
            'total': total,
            'paid_amount': paid_usd,
            'lines': [line.as_invoice_line() for line in cart.lines],
            'exchange_rate_to_usd': float(currency.get_current_rate(currency.get_display_currency())),
            'original_currency': currency.get_display_currency(),
            'warehouse_id': cart.warehouse_id or warehouse_service.default_warehouse_id(),
            'branch_id': branch_service.current_branch_id(),
            'cashbox_id': cart.cashbox_id,
            'payment_method': payment_method,
            'shift_id': cart.shift_id,
        }
        invoice_id = invoice_service.create(data)
        if paid_usd > 0 and payment_method in ('cash', 'card'):
            cashbox_service.record_pos_sale(invoice_id, paid_usd, payment_method, data.get('branch_id'), cart.cashbox_id, cart.shift_id)
        audit_service.log('POS_CHECKOUT', 'SALE_INVOICE', invoice_id, new_values={**data, 'cart': cart.as_dict()}, details='إنهاء بيع سريع')
        return invoice_id


pos_service = POSService()
