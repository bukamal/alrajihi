# -*- coding: utf-8 -*-
from __future__ import annotations
from decimal import Decimal
from typing import Dict, List, Optional
from core.compat import records
from core.services.audit_service import audit_service
from core.services.branch_service import branch_service
from database.dao.cashbox_dao import cashbox_dao

class CashboxService:
    def bootstrap(self): cashbox_dao.bootstrap_defaults()
    def cashboxes(self, include_archived=False)->List[Dict]: return records(cashbox_dao.get_cashboxes(include_archived),'cashboxes')
    def bank_accounts(self, include_archived=False)->List[Dict]: return records(cashbox_dao.get_bank_accounts(include_archived),'bank_accounts')
    def default_cashbox_id(self, branch_id=None)->Optional[int]: self.bootstrap(); return cashbox_dao.default_cashbox_id(branch_id or branch_service.current_branch_id())
    def add_cashbox(self,data):
        cid=cashbox_dao.add_cashbox(data); audit_service.log('CREATE','CASHBOX',cid,new_values=data,details='إنشاء صندوق'); return cid
    def update_cashbox(self,cid,data):
        old=cashbox_dao.get_cashbox(cid); cashbox_dao.update_cashbox(cid,data); audit_service.log('UPDATE','CASHBOX',cid,old_values=old,new_values=cashbox_dao.get_cashbox(cid),details='تعديل صندوق')
    def archive_cashbox(self,cid):
        old=cashbox_dao.get_cashbox(cid); cashbox_dao.archive_cashbox(cid); audit_service.log('SOFT_DELETE','CASHBOX',cid,old_values=old,details='أرشفة صندوق')
    def add_bank_account(self,data):
        bid=cashbox_dao.add_bank_account(data); audit_service.log('CREATE','BANK_ACCOUNT',bid,new_values=data,details='إنشاء حساب بنكي'); return bid
    def update_bank_account(self,bid,data):
        old=cashbox_dao.get_bank_account(bid); cashbox_dao.update_bank_account(bid,data); audit_service.log('UPDATE','BANK_ACCOUNT',bid,old_values=old,new_values=cashbox_dao.get_bank_account(bid),details='تعديل حساب بنكي')
    def archive_bank_account(self,bid):
        old=cashbox_dao.get_bank_account(bid); cashbox_dao.archive_bank_account(bid); audit_service.log('SOFT_DELETE','BANK_ACCOUNT',bid,old_values=old,details='أرشفة حساب بنكي')
    def movements(self,limit=200,cashbox_id=None,bank_account_id=None)->List[Dict]: return records(cashbox_dao.movements(limit=limit,cashbox_id=cashbox_id,bank_account_id=bank_account_id),'movements')
    def prepare_voucher_payload(self,data):
        payload=dict(data or {}); payload['payment_method']=payload.get('payment_method') or 'cash'
        if payload['payment_method']=='bank': payload['cashbox_id']=None
        else:
            payload['bank_account_id']=None
            if not payload.get('cashbox_id'): payload['cashbox_id']=self.default_cashbox_id(payload.get('branch_id'))
        return payload
    def record_voucher(self,voucher_id:int,voucher:Dict):
        v=self.prepare_voucher_payload(voucher); amount=Decimal(str(v.get('amount') or 0)); signed=abs(amount) if v.get('type')=='receipt' else -abs(amount)
        cashbox_dao.delete_reference_movements('voucher',voucher_id)
        cashbox_dao.record_movement({'branch_id':v.get('branch_id'),'cashbox_id':v.get('cashbox_id'),'bank_account_id':v.get('bank_account_id'),'movement_type':v.get('type'),'amount':signed,'direction':'in' if signed>=0 else 'out','reference_type':'voucher','reference_id':voucher_id,'description':v.get('description') or v.get('reference') or 'سند مالي','movement_date':v.get('date')})
    def reverse_voucher(self,voucher_id:int): cashbox_dao.delete_reference_movements('voucher',voucher_id)


    def record_return_refund(self, return_id:int, data:Dict):
        v=self.prepare_voucher_payload(data)
        amount=Decimal(str(v.get('amount') or 0))
        if amount <= 0:
            return None
        cashbox_dao.delete_reference_movements('sales_return', return_id)
        return cashbox_dao.record_movement({'branch_id':v.get('branch_id'),'cashbox_id':v.get('cashbox_id'),'bank_account_id':v.get('bank_account_id'),'movement_type':'sales_return_refund','amount':-abs(amount),'direction':'out','reference_type':'sales_return','reference_id':return_id,'description':v.get('description') or 'رد مرتجع مبيعات','movement_date':v.get('date')})


    def record_purchase_return_refund(self, return_id:int, data:Dict):
        v=self.prepare_voucher_payload(data)
        amount=Decimal(str(v.get('amount') or 0))
        if amount <= 0:
            return None
        cashbox_dao.delete_reference_movements('purchase_return', return_id)
        return cashbox_dao.record_movement({'branch_id':v.get('branch_id'),'cashbox_id':v.get('cashbox_id'),'bank_account_id':v.get('bank_account_id'),'movement_type':'purchase_return_refund','amount':abs(amount),'direction':'in','reference_type':'purchase_return','reference_id':return_id,'description':v.get('description') or 'استرداد مرتجع مشتريات','movement_date':v.get('date')})

    def reverse_reference(self, reference_type, reference_id):
        return cashbox_dao.delete_reference_movements(reference_type, reference_id)

    def current_open_shift(self, cashbox_id=None):
        return cashbox_dao.current_open_shift(cashbox_id)

    def shifts(self, limit=100, status=None):
        return records(cashbox_dao.shifts(limit,status),'shifts')

    def open_shift(self, data):
        sid=cashbox_dao.open_shift(data)
        audit_service.log('POS_SHIFT_OPEN','POS_SHIFT',sid,new_values=data,details='فتح وردية كاشير')
        return sid

    def shift_summary(self, shift_id):
        return cashbox_dao.shift_summary(shift_id)

    def close_shift(self, shift_id, actual_amount, notes=''):
        old=cashbox_dao.shift_summary(shift_id)
        summary=cashbox_dao.close_shift(shift_id,actual_amount,notes)
        audit_service.log('POS_SHIFT_CLOSE','POS_SHIFT',shift_id,old_values=old,new_values=summary,details='إغلاق وردية كاشير')
        return summary

    def record_pos_sale(self, invoice_id:int, amount, payment_method='cash', branch_id=None, cashbox_id=None, shift_id=None):
        signed=Decimal(str(amount or 0))
        if signed <= 0:
            return None
        method = payment_method or 'cash'
        movement_type = 'pos_sale_card' if method == 'card' else 'pos_sale_cash'
        return cashbox_dao.record_movement({'branch_id':branch_id,'cashbox_id':cashbox_id,'bank_account_id':None,'movement_type':movement_type,'amount':signed,'direction':'in','shift_id':shift_id,'reference_type':'pos_invoice','reference_id':invoice_id,'description':'بيع سريع POS','movement_date':None})

cashbox_service=CashboxService()
