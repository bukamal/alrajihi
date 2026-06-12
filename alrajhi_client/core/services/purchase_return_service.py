# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from auth.session import UserSession
from core.services.audit_service import audit_service
from core.services.branch_service import branch_service
from core.services.cashbox_service import cashbox_service
from core.services.invoice_service import invoice_service
from core.services.warehouse_service import warehouse_service
from database.connection import DatabaseConnection


class PurchaseReturnException(Exception):
    pass


class PurchaseReturnService:
    def __init__(self):
        self.db = DatabaseConnection()

    def _conn(self):
        return self.db.get_connection()

    def _uid(self):
        uid = UserSession.get_current_user_id()
        if not uid:
            raise PurchaseReturnException('لا توجد جلسة مستخدم نشطة')
        return uid

    def next_return_no(self) -> str:
        if self.db.is_remote():
            return f"PR-{datetime.now().strftime('%Y')}-AUTO"
        uid = self._uid()
        year = datetime.now().strftime('%Y')
        prefix = f'PR-{year}-'
        row = self._conn().execute(
            "SELECT MAX(return_no) AS max_no FROM purchase_returns WHERE user_id=? AND return_no LIKE ?",
            (uid, prefix + '%')
        ).fetchone()
        max_no = row['max_no'] if row else None
        try:
            num = int(str(max_no).split('-')[-1]) + 1 if max_no else 1
        except Exception:
            num = 1
        return f'{prefix}{num:04d}'

    def list_returns(self, search: str | None = None, limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict], int]:
        if self.db.is_remote():
            return self.db.get_rest_client().get_purchase_returns(search=search, limit=limit, offset=offset)
        uid = self._uid()
        conn = self._conn()
        where = ["pr.user_id=?", "pr.deleted_at IS NULL"]
        params = [uid]
        if search:
            q = f'%{search}%'
            where.append("(pr.return_no LIKE ? OR inv.reference LIKE ? OR s.name LIKE ?)")
            params.extend([q, q, q])
        where_sql = ' AND '.join(where)
        total = conn.execute(f"SELECT COUNT(*) FROM purchase_returns pr LEFT JOIN invoices inv ON inv.id=pr.original_invoice_id LEFT JOIN suppliers s ON s.id=pr.supplier_id WHERE {where_sql}", params).fetchone()[0]
        sql = f"""
            SELECT pr.*, inv.reference AS invoice_reference, s.name AS supplier_name,
                   w.name AS warehouse_name, b.name AS branch_name
            FROM purchase_returns pr
            LEFT JOIN invoices inv ON inv.id=pr.original_invoice_id
            LEFT JOIN suppliers s ON s.id=pr.supplier_id
            LEFT JOIN warehouses w ON w.id=pr.warehouse_id
            LEFT JOIN branches b ON b.id=pr.branch_id
            WHERE {where_sql}
            ORDER BY pr.id DESC
        """
        if limit is not None:
            sql += ' LIMIT ?'; params.append(limit)
        if offset is not None:
            sql += ' OFFSET ?'; params.append(offset)
        return [dict(r) for r in conn.execute(sql, params).fetchall()], int(total or 0)

    def get(self, return_id: int) -> Optional[Dict]:
        if self.db.is_remote():
            return self.db.get_rest_client().get_purchase_return(return_id)
        row = self._conn().execute("SELECT * FROM purchase_returns WHERE id=?", (return_id,)).fetchone()
        if not row:
            return None
        ret = dict(row)
        ret['lines'] = [dict(x) for x in self._conn().execute("SELECT * FROM purchase_return_lines WHERE purchase_return_id=?", (return_id,)).fetchall()]
        return ret

    def purchase_invoices(self, search: str | None = None, limit: int = 200) -> List[Dict]:
        if self.db.is_remote():
            return self.db.get_rest_client().get_purchase_return_invoices(search=search, limit=limit)
        invoices, _ = invoice_service.list_invoices(search=search, inv_type='purchase', limit=limit, offset=0)
        return invoices

    def returned_qty(self, invoice_id: int, line_id: int | None = None, item_id: int | None = None) -> Decimal:
        if self.db.is_remote():
            return Decimal('0')
        conn = self._conn()
        if line_id:
            row = conn.execute("""
                SELECT COALESCE(SUM(CAST(prl.quantity_in_base AS REAL)),0) AS qty
                FROM purchase_return_lines prl
                JOIN purchase_returns pr ON pr.id=prl.purchase_return_id
                WHERE pr.original_invoice_id=? AND pr.deleted_at IS NULL AND prl.original_invoice_line_id=?
            """, (invoice_id, line_id)).fetchone()
        else:
            row = conn.execute("""
                SELECT COALESCE(SUM(CAST(prl.quantity_in_base AS REAL)),0) AS qty
                FROM purchase_return_lines prl
                JOIN purchase_returns pr ON pr.id=prl.purchase_return_id
                WHERE pr.original_invoice_id=? AND pr.deleted_at IS NULL AND prl.item_id=?
            """, (invoice_id, item_id)).fetchone()
        return Decimal(str(row['qty'] if row else 0))

    def invoice_returnable_lines(self, invoice_id: int) -> List[Dict]:
        if self.db.is_remote():
            return self.db.get_rest_client().get_purchase_returnable_lines(invoice_id)
        inv = invoice_service.get(invoice_id)
        if not inv or inv.get('type') != 'purchase':
            raise PurchaseReturnException('يجب اختيار فاتورة شراء صالحة')
        result = []
        wh_id = inv.get('warehouse_id') or warehouse_service.default_warehouse_id()
        for line in inv.get('lines') or []:
            purchased = Decimal(str(line.get('quantity_in_base') or line.get('quantity') or 0))
            returned = self.returned_qty(invoice_id, line.get('id'), line.get('item_id'))
            remaining = max(Decimal('0'), purchased - returned)
            available = Decimal(str(warehouse_service.available_qty(line.get('item_id'), wh_id) or 0))
            row = dict(line)
            row.update({'purchased_qty': str(purchased), 'returned_qty': str(returned), 'returnable_qty': str(remaining), 'warehouse_available': str(available)})
            result.append(row)
        return result

    def create_return(self, data: Dict) -> int:
        if self.db.is_remote():
            result = self.db.get_rest_client().create_purchase_return(data)
            return int((result or {}).get('id') or 0)
        uid = self._uid()
        invoice_id = int(data.get('original_invoice_id') or 0)
        inv = invoice_service.get(invoice_id)
        if not inv or inv.get('type') != 'purchase':
            raise PurchaseReturnException('يجب اختيار فاتورة شراء صالحة')
        lines_in = data.get('lines') or []
        if not lines_in:
            raise PurchaseReturnException('يجب اختيار بند واحد على الأقل للمرتجع')
        wh_id = data.get('warehouse_id') or inv.get('warehouse_id') or warehouse_service.default_warehouse_id()
        invoice_lines = {int(l.get('id')): l for l in (inv.get('lines') or []) if l.get('id')}
        prepared = []
        total = Decimal('0')
        for line in lines_in:
            orig_line_id = int(line.get('original_invoice_line_id') or 0)
            orig = invoice_lines.get(orig_line_id)
            if not orig:
                raise PurchaseReturnException('بند المرتجع غير موجود في فاتورة الشراء الأصلية')
            qty = Decimal(str(line.get('quantity') or 0))
            if qty <= 0:
                raise PurchaseReturnException('كمية المرتجع يجب أن تكون أكبر من صفر')
            purchased = Decimal(str(orig.get('quantity_in_base') or orig.get('quantity') or 0))
            already = self.returned_qty(invoice_id, orig_line_id, orig.get('item_id'))
            if qty > (purchased - already):
                raise PurchaseReturnException('كمية المرتجع أكبر من الكمية المتبقية القابلة للإرجاع')
            available = Decimal(str(warehouse_service.available_qty(orig.get('item_id'), wh_id) or 0))
            if qty > available:
                raise PurchaseReturnException('لا توجد كمية كافية في المستودع لإرجاع هذا البند')
            price = Decimal(str(orig.get('unit_price') or orig.get('price') or 0))
            cost = Decimal(str(orig.get('unit_cost') or price))
            amount = qty * price
            total += amount
            prepared.append({
                'original_invoice_line_id': orig_line_id,
                'item_id': orig.get('item_id'),
                'quantity': qty,
                'quantity_in_base': qty,
                'unit_price': price,
                'unit_cost': cost,
                'total': amount,
                'unit': orig.get('unit') or '',
                'cost_amount': qty * cost,
            })
        remaining_payable = max(Decimal('0'), Decimal(str(inv.get('total') or 0)) - Decimal(str(inv.get('paid') or 0)))
        requested = data.get('refund_amount')
        refund = max(Decimal('0'), total - min(total, remaining_payable)) if requested in (None, '') else Decimal(str(requested))
        if refund < 0 or refund > total:
            raise PurchaseReturnException('مبلغ الاسترداد يجب أن يكون بين صفر وإجمالي المرتجع')
        credit = total - refund
        branch_id = data.get('branch_id') or inv.get('branch_id') or branch_service.current_branch_id()
        cashbox_id = data.get('cashbox_id') or inv.get('cashbox_id')
        bank_account_id = data.get('bank_account_id') or inv.get('bank_account_id')
        payment_method = data.get('payment_method') or inv.get('payment_method') or 'cash'
        conn = self._conn()
        now = datetime.now().isoformat()
        ret_no = data.get('return_no') or self.next_return_no()
        cur = conn.execute("""
            INSERT INTO purchase_returns
            (user_id,return_no,original_invoice_id,supplier_id,date,total,refund_amount,credit_amount,
             warehouse_id,branch_id,cashbox_id,bank_account_id,payment_method,notes,status,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'active', ?)
        """, (uid, ret_no, invoice_id, inv.get('supplier_id'), data.get('date') or datetime.now().strftime('%Y-%m-%d'),
              str(total), str(refund), str(credit), wh_id, branch_id, cashbox_id, bank_account_id, payment_method,
              data.get('notes') or '', now))
        rid = cur.lastrowid
        for line in prepared:
            conn.execute("""
                INSERT INTO purchase_return_lines
                (purchase_return_id,original_invoice_line_id,item_id,quantity,unit_price,total,unit,quantity_in_base,unit_cost,cost_amount)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (rid, line['original_invoice_line_id'], line['item_id'], str(line['quantity']), str(line['unit_price']),
                  str(line['total']), line['unit'], str(line['quantity_in_base']), str(line['unit_cost']), str(line['cost_amount'])))
            self.db._record_inventory_movement(line['item_id'], 'purchase_return', line['quantity_in_base'], line['unit_cost'], rid)
            warehouse_service.record_movement(line['item_id'], wh_id, 'purchase_return_out', -abs(line['quantity_in_base']), line['unit_cost'], 'purchase_return', rid, 'مرتجع مشتريات من المستودع')
        if inv.get('supplier_id') and credit > 0:
            self.db._update_supplier_balance(inv.get('supplier_id'), -credit)
        if refund > 0:
            self.db._update_cash_balance(refund, add=True)
            cashbox_service.record_purchase_return_refund(rid, {'branch_id':branch_id,'cashbox_id':cashbox_id,'bank_account_id':bank_account_id,'payment_method':payment_method,'amount':refund,'date':data.get('date'),'description':'استرداد مرتجع مشتريات'})
        conn.commit()
        audit_service.log('CREATE', 'PURCHASE_RETURN', rid, new_values=self.get(rid), details='إنشاء مرتجع مشتريات')
        return rid

    def delete_return(self, return_id: int) -> None:
        if self.db.is_remote():
            self.db.get_rest_client().delete_purchase_return(return_id)
            return
        ret = self.get(return_id)
        if not ret or ret.get('deleted_at'):
            raise PurchaseReturnException('مرتجع المشتريات غير موجود')
        conn = self._conn()
        conn.execute("DELETE FROM inventory_movements WHERE reference_id=? AND movement_type='purchase_return'", (return_id,))
        warehouse_service.reverse_reference('purchase_return', return_id)
        credit = Decimal(str(ret.get('credit_amount') or 0))
        if ret.get('supplier_id') and credit > 0:
            self.db._update_supplier_balance(ret.get('supplier_id'), credit)
        refund = Decimal(str(ret.get('refund_amount') or 0))
        if refund > 0:
            self.db._update_cash_balance(refund, add=False)
            cashbox_service.reverse_reference('purchase_return', return_id)
        conn.execute("UPDATE purchase_returns SET deleted_at=datetime('now'), status='cancelled' WHERE id=?", (return_id,))
        conn.commit()
        audit_service.log('REVERSE', 'PURCHASE_RETURN', return_id, old_values=ret, details='إلغاء مرتجع مشتريات')


purchase_return_service = PurchaseReturnService()
