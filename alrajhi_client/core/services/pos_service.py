# -*- coding: utf-8 -*-
"""Point-of-sale service for fast barcode sales.

The POS UI is intentionally thin: it scans barcodes, displays a cart, and calls
this service to validate stock, calculate totals, and post the final sale as a
normal sale invoice.  This keeps POS accounting consistent with the existing
invoice/inventory pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from core.services.product_service import product_service
from core.services.invoice_service import invoice_service
from core.services.audit_service import audit_service
from core.services.warehouse_service import warehouse_service
from core.services.branch_service import branch_service
from core.services.cashbox_service import cashbox_service
from currency import currency


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

    @property
    def total_usd(self) -> Decimal:
        return self.qty * self.unit_price_usd

    def as_invoice_line(self) -> Dict:
        return {
            'item_id': self.item_id,
            'quantity': self.qty,
            'unit': self.unit,
            'conversion_factor': Decimal('1'),
            'base_qty': self.qty,
            'unit_price': self.unit_price_usd,
            'total': self.total_usd,
            'description': 'POS'
        }

    def as_dict(self) -> Dict:
        return {
            'item_id': self.item_id,
            'barcode': self.barcode,
            'name': self.name,
            'unit': self.unit,
            'qty': self.qty,
            'unit_price_usd': self.unit_price_usd,
            'available_qty': self.available_qty,
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
            'total_usd': self.total_usd,
            'lines': [line.as_dict() for line in self.lines],
        }


class POSService:
    def __init__(self):
        self.suspended_carts: List[POSCart] = []

    def new_cart(self, warehouse_id: int | None = None, cashbox_id: int | None = None, shift_id: int | None = None) -> POSCart:
        cashbox_id = cashbox_id or cashbox_service.default_cashbox_id(branch_service.current_branch_id())
        shift = cashbox_service.current_open_shift(cashbox_id) if cashbox_id else None
        return POSCart(warehouse_id=warehouse_id or warehouse_service.default_warehouse_id(), cashbox_id=cashbox_id, shift_id=shift_id or ((shift or {}).get('id') if shift else None))

    def _decimal(self, value, default='0') -> Decimal:
        try:
            return Decimal(str(value if value is not None else default))
        except Exception:
            return Decimal(str(default))

    def lookup_item(self, code: str) -> Dict:
        code = str(code or '').strip()
        if not code:
            raise POSException('أدخل أو امسح باركود المادة')
        item = product_service.item_by_barcode(code)
        if not item:
            matches = product_service.items(search=code, limit=10)
            if len(matches) == 1:
                item = matches[0]
        if not item:
            raise POSException(f"لم يتم العثور على مادة بالباركود: {code}")
        if item.get('item_type') == 'خدمة':
            # Services can still be sold, but do not have stock restrictions.
            return item
        return item

    def add_scan(self, cart: POSCart, code: str, qty: Decimal | int | str = Decimal('1')) -> POSLine:
        item = self.lookup_item(code)
        qty = self._decimal(qty, '1')
        if qty <= 0:
            raise POSException('الكمية يجب أن تكون أكبر من صفر')
        item_id = int(item['id'])
        barcode = str(item.get('barcode') or code).strip()
        warehouse_id = cart.warehouse_id or warehouse_service.default_warehouse_id()
        try:
            available = self._decimal(warehouse_service.available_qty(item_id, warehouse_id))
        except Exception:
            available = self._decimal(item.get('available', item.get('quantity', 0)))
        price = self._decimal(item.get('selling_price', 0))
        if price < 0:
            raise POSException('سعر البيع غير صالح')
        is_service = item.get('item_type') == 'خدمة'
        existing = next((line for line in cart.lines if line.item_id == item_id), None)
        new_qty = qty + (existing.qty if existing else Decimal('0'))
        if not is_service and new_qty > available:
            raise POSException(f"المخزون غير كافٍ للمادة {item.get('name', '')}. المتاح: {available}")
        if existing:
            existing.qty = new_qty
            return existing
        line = POSLine(
            item_id=item_id,
            barcode=barcode,
            name=str(item.get('name') or ''),
            unit=str(item.get('unit') or 'قطعة'),
            qty=qty,
            unit_price_usd=price,
            available_qty=available,
        )
        cart.lines.append(line)
        return line

    def remove_line(self, cart: POSCart, item_id: int) -> None:
        cart.lines = [line for line in cart.lines if line.item_id != int(item_id)]

    def clear(self, cart: POSCart) -> None:
        cart.lines.clear()

    def suspend(self, cart: POSCart, note: str = '') -> int:
        if not cart.lines:
            raise POSException('لا يمكن تعليق سلة فارغة')
        cart.note = note or f"POS {datetime.now().strftime('%H:%M:%S')}"
        self.suspended_carts.append(cart)
        audit_service.log('POS_SUSPEND', 'POS_CART', None, new_values=cart.as_dict(), details='تعليق بيع سريع')
        return len(self.suspended_carts) - 1

    def resume(self, index: int) -> POSCart:
        try:
            cart = self.suspended_carts.pop(index)
        except Exception:
            raise POSException('البيع المعلق غير موجود')
        audit_service.log('POS_RESUME', 'POS_CART', None, new_values=cart.as_dict(), details='استرجاع بيع معلق')
        return cart

    def checkout(self, cart: POSCart, payment_method: str = 'cash', paid_usd: Decimal | None = None) -> int:
        if not cart.lines:
            raise POSException('لا يمكن إنهاء بيع بدون مواد')
        total = cart.total_usd
        if total <= 0:
            raise POSException('إجمالي البيع يجب أن يكون أكبر من صفر')
        if paid_usd is None:
            paid_usd = total
        paid_usd = self._decimal(paid_usd, '0')
        if paid_usd < 0:
            raise POSException('المدفوع لا يمكن أن يكون سالبًا')
        if paid_usd > total:
            paid_usd = total
        shift = cashbox_service.current_open_shift(cart.cashbox_id)
        if not shift:
            raise POSException('لا يمكن البيع من POS بدون وردية مفتوحة. افتح وردية أولاً.')
        cart.shift_id = shift.get('id')
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
