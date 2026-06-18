# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal
from typing import Dict, List, Optional

from core.services.audit_service import audit_service
from core.services.branch_service import branch_service
from gateways.cashbox_gateway import create_cashbox_gateway


class CashboxService:
    def __init__(self):
        self.gateway = create_cashbox_gateway()

    def _finance_policy(self):
        from core.services.finance_operation_policy import finance_operation_policy
        return finance_operation_policy

    def _require_finance_operation(self, operation: str, context: str = '', payload=None):
        return self._finance_policy().require(operation, context=context, payload=payload or {})

    def pos_shifts_enabled(self):
        try:
            from core.services.settings_service import settings_service
            return settings_service.pos_shifts_enabled()
        except Exception:
            return False

    def bootstrap(self):
        self.gateway.bootstrap()

    def cashboxes(self, include_archived=False) -> List[Dict]:
        self._require_finance_operation(self._finance_policy().OP_USE, context='CashboxService.cashboxes')
        return self.gateway.cashboxes(include_archived=include_archived)

    def cashbox_by_id(self, cashbox_id: int) -> Optional[Dict]:
        self._require_finance_operation(self._finance_policy().OP_USE, context='CashboxService.cashbox_by_id', payload={'cashbox_id': cashbox_id})
        return self.gateway.get_cashbox(cashbox_id)

    def bank_accounts(self, include_archived=False) -> List[Dict]:
        self._require_finance_operation(self._finance_policy().OP_USE, context='CashboxService.bank_accounts')
        return self.gateway.bank_accounts(include_archived=include_archived)

    def bank_account_by_id(self, bank_account_id: int) -> Optional[Dict]:
        self._require_finance_operation(self._finance_policy().OP_USE, context='CashboxService.bank_account_by_id', payload={'bank_account_id': bank_account_id})
        return self.gateway.get_bank_account(bank_account_id)

    def default_cashbox_id(self, branch_id=None) -> Optional[int]:
        self.bootstrap()
        return self.gateway.default_cashbox_id(branch_id or branch_service.current_branch_id())

    def add_cashbox(self, data):
        self._require_finance_operation(self._finance_policy().OP_CASHBOX_CREATE, context='CashboxService.add_cashbox', payload=data)
        cid = self.gateway.add_cashbox(data)
        audit_service.log('CREATE', 'CASHBOX', cid, new_values=data, details='إنشاء صندوق')
        return cid

    def update_cashbox(self, cid, data):
        self._require_finance_operation(self._finance_policy().OP_CASHBOX_EDIT, context='CashboxService.update_cashbox', payload={'id': cid, **(data or {})})
        old = self.gateway.get_cashbox(cid)
        self.gateway.update_cashbox(cid, data)
        audit_service.log('UPDATE', 'CASHBOX', cid, old_values=old, new_values=self.gateway.get_cashbox(cid), details='تعديل صندوق')

    def archive_cashbox(self, cid):
        self._require_finance_operation(self._finance_policy().OP_CASHBOX_ARCHIVE, context='CashboxService.archive_cashbox', payload={'id': cid})
        old = self.gateway.get_cashbox(cid)
        self.gateway.archive_cashbox(cid)
        audit_service.log('SOFT_DELETE', 'CASHBOX', cid, old_values=old, details='أرشفة صندوق')

    def add_bank_account(self, data):
        self._require_finance_operation(self._finance_policy().OP_BANK_CREATE, context='CashboxService.add_bank_account', payload=data)
        bid = self.gateway.add_bank_account(data)
        audit_service.log('CREATE', 'BANK_ACCOUNT', bid, new_values=data, details='إنشاء حساب بنكي')
        return bid

    def update_bank_account(self, bid, data):
        self._require_finance_operation(self._finance_policy().OP_BANK_EDIT, context='CashboxService.update_bank_account', payload={'id': bid, **(data or {})})
        old = self.gateway.get_bank_account(bid)
        self.gateway.update_bank_account(bid, data)
        audit_service.log('UPDATE', 'BANK_ACCOUNT', bid, old_values=old, new_values=self.gateway.get_bank_account(bid), details='تعديل حساب بنكي')

    def archive_bank_account(self, bid):
        self._require_finance_operation(self._finance_policy().OP_BANK_ARCHIVE, context='CashboxService.archive_bank_account', payload={'id': bid})
        old = self.gateway.get_bank_account(bid)
        self.gateway.archive_bank_account(bid)
        audit_service.log('SOFT_DELETE', 'BANK_ACCOUNT', bid, old_values=old, details='أرشفة حساب بنكي')

    def movements(self, limit=200, cashbox_id=None, bank_account_id=None) -> List[Dict]:
        self._require_finance_operation(self._finance_policy().OP_MOVEMENTS_VIEW, context='CashboxService.movements')
        return self.gateway.movements(limit=limit, cashbox_id=cashbox_id, bank_account_id=bank_account_id)

    def prepare_voucher_payload(self, data):
        payload = dict(data or {})
        payload['payment_method'] = payload.get('payment_method') or 'cash'
        if payload['payment_method'] == 'bank':
            payload['cashbox_id'] = None
        else:
            payload['bank_account_id'] = None
            if not payload.get('cashbox_id'):
                payload['cashbox_id'] = self.default_cashbox_id(payload.get('branch_id'))
        return payload

    def record_voucher(self, voucher_id: int, voucher: Dict):
        v = self.prepare_voucher_payload(voucher)
        amount = Decimal(str(v.get('amount') or 0))
        signed = abs(amount) if v.get('type') == 'receipt' else -abs(amount)
        self.gateway.delete_reference_movements('voucher', voucher_id)
        self.gateway.record_movement({
            'branch_id': v.get('branch_id'),
            'cashbox_id': v.get('cashbox_id'),
            'bank_account_id': v.get('bank_account_id'),
            'movement_type': v.get('type'),
            'amount': signed,
            'direction': 'in' if signed >= 0 else 'out',
            'reference_type': 'voucher',
            'reference_id': voucher_id,
            'description': v.get('description') or v.get('reference') or 'سند مالي',
            'movement_date': v.get('date'),
        })

    def reverse_voucher(self, voucher_id: int):
        return self.gateway.delete_reference_movements('voucher', voucher_id)

    def record_return_refund(self, return_id: int, data: Dict):
        v = self.prepare_voucher_payload(data)
        amount = Decimal(str(v.get('amount') or 0))
        if amount <= 0:
            return None
        self.gateway.delete_reference_movements('sales_return', return_id)
        return self.gateway.record_movement({
            'branch_id': v.get('branch_id'),
            'cashbox_id': v.get('cashbox_id'),
            'bank_account_id': v.get('bank_account_id'),
            'movement_type': 'sales_return_refund',
            'amount': -abs(amount),
            'direction': 'out',
            'reference_type': 'sales_return',
            'reference_id': return_id,
            'description': v.get('description') or 'رد مرتجع مبيعات',
            'movement_date': v.get('date'),
        })

    def record_purchase_return_refund(self, return_id: int, data: Dict):
        v = self.prepare_voucher_payload(data)
        amount = Decimal(str(v.get('amount') or 0))
        if amount <= 0:
            return None
        self.gateway.delete_reference_movements('purchase_return', return_id)
        return self.gateway.record_movement({
            'branch_id': v.get('branch_id'),
            'cashbox_id': v.get('cashbox_id'),
            'bank_account_id': v.get('bank_account_id'),
            'movement_type': 'purchase_return_refund',
            'amount': abs(amount),
            'direction': 'in',
            'reference_type': 'purchase_return',
            'reference_id': return_id,
            'description': v.get('description') or 'استرداد مرتجع مشتريات',
            'movement_date': v.get('date'),
        })

    def reverse_reference(self, reference_type, reference_id):
        return self.gateway.delete_reference_movements(reference_type, reference_id)

    def current_open_shift(self, cashbox_id=None):
        if not self.pos_shifts_enabled():
            return None
        try:
            return self.gateway.current_open_shift(cashbox_id)
        except Exception as exc:
            print(f"⚠️ تعذر التحقق من الوردية المفتوحة من الخادم: {exc}")
            return None

    def shifts(self, limit=100, status=None):
        self._require_finance_operation(self._finance_policy().OP_SHIFTS_VIEW, context='CashboxService.shifts')
        return self.gateway.shifts(limit=limit, status=status)

    def open_shift(self, data):
        if not self.pos_shifts_enabled():
            raise ValueError('نظام الورديات معطل من الإعدادات')
        sid = self.gateway.open_shift(data)
        audit_service.log('POS_SHIFT_OPEN', 'POS_SHIFT', sid, new_values=data, details='فتح وردية كاشير')
        return sid

    def shift_summary(self, shift_id):
        if not self.pos_shifts_enabled():
            raise ValueError('نظام الورديات معطل من الإعدادات')
        return self.gateway.shift_summary(shift_id)

    def close_shift(self, shift_id, actual_amount, notes=''):
        if not self.pos_shifts_enabled():
            raise ValueError('نظام الورديات معطل من الإعدادات')
        old = self.gateway.shift_summary(shift_id)
        summary = self.gateway.close_shift(shift_id, actual_amount, notes)
        audit_service.log('POS_SHIFT_CLOSE', 'POS_SHIFT', shift_id, old_values=old, new_values=summary, details='إغلاق وردية كاشير')
        return summary

    def record_pos_sale(self, invoice_id: int, amount, payment_method='cash', branch_id=None, cashbox_id=None, shift_id=None):
        signed = Decimal(str(amount or 0))
        if signed <= 0:
            return None
        # Queued invoices are returned as negative ids by RestClient.  Do not
        # send a standalone cash movement while offline; the queued invoice
        # payload contains payment data and must be replayed atomically by the
        # server.
        try:
            if int(invoice_id or 0) < 0:
                return None
        except Exception:
            pass
        method = payment_method or 'cash'
        movement_type = 'pos_sale_card' if method == 'card' else 'pos_sale_cash'
        try:
            return self.gateway.record_movement({
            'branch_id': branch_id,
            'cashbox_id': cashbox_id,
            'bank_account_id': None,
            'movement_type': movement_type,
            'amount': signed,
            'direction': 'in',
            'shift_id': shift_id,
            'reference_type': 'pos_invoice',
            'reference_id': invoice_id,
            'description': 'بيع سريع POS',
            'movement_date': None,
        })
        except Exception as exc:
            print(f"⚠️ تعذر تسجيل حركة POS النقدية؛ لن يتم إسقاط عملية البيع: {exc}")
            return None


cashbox_service = CashboxService()
