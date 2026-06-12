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
from gateways.sales_return_gateway import SalesReturnGateway, SalesReturnException


class LocalSalesReturnGateway(SalesReturnGateway):
    def __init__(self):
        self.db = DatabaseConnection()

    def is_remote(self) -> bool:
        return False

    def _conn(self):
        return self.db.get_connection()

    def _uid(self):
        uid = UserSession.get_current_user_id()
        if not uid:
            raise SalesReturnException('لا توجد جلسة مستخدم نشطة')
        return uid

    def next_return_no(self) -> str:
        if self.db.is_remote():
            # الرقم النهائي يولده الخادم عند الحفظ؛ هذه قيمة عرض مؤقتة فقط.
            return f"SR-{datetime.now().strftime('%Y')}-AUTO"
        uid = self._uid()
        year = datetime.now().strftime('%Y')
        prefix = f'SR-{year}-'
        row = self._conn().execute(
            "SELECT MAX(return_no) AS max_no FROM sales_returns WHERE user_id=? AND return_no LIKE ?",
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
            return self.db.get_rest_client().get_sales_returns(search=search, limit=limit, offset=offset)
        uid = self._uid()
        conn = self._conn()
        where = ["sr.user_id=?", "sr.deleted_at IS NULL"]
        params = [uid]
        if search:
            q = f'%{search}%'
            where.append("(sr.return_no LIKE ? OR inv.reference LIKE ? OR c.name LIKE ?)")
            params.extend([q, q, q])
        where_sql = ' AND '.join(where)
        total = conn.execute(f"SELECT COUNT(*) FROM sales_returns sr LEFT JOIN invoices inv ON inv.id=sr.original_invoice_id LEFT JOIN customers c ON c.id=sr.customer_id WHERE {where_sql}", params).fetchone()[0]
        sql = f"""
            SELECT sr.*, inv.reference AS invoice_reference, c.name AS customer_name,
                   w.name AS warehouse_name, b.name AS branch_name
            FROM sales_returns sr
            LEFT JOIN invoices inv ON inv.id=sr.original_invoice_id
            LEFT JOIN customers c ON c.id=sr.customer_id
            LEFT JOIN warehouses w ON w.id=sr.warehouse_id
            LEFT JOIN branches b ON b.id=sr.branch_id
            WHERE {where_sql}
            ORDER BY sr.id DESC
        """
        if limit is not None:
            sql += ' LIMIT ?'; params.append(limit)
        if offset is not None:
            sql += ' OFFSET ?'; params.append(offset)
        return [dict(r) for r in conn.execute(sql, params).fetchall()], int(total or 0)

    def get(self, return_id: int) -> Optional[Dict]:
        if self.db.is_remote():
            return self.db.get_rest_client().get_sales_return(return_id)
        row = self._conn().execute("SELECT * FROM sales_returns WHERE id=?", (return_id,)).fetchone()
        if not row:
            return None
        ret = dict(row)
        ret['lines'] = [dict(x) for x in self._conn().execute("SELECT * FROM sales_return_lines WHERE sales_return_id=?", (return_id,)).fetchall()]
        return ret

    def sale_invoices(self, search: str | None = None, limit: int = 200) -> List[Dict]:
        if self.db.is_remote():
            return self.db.get_rest_client().get_sales_return_invoices(search=search, limit=limit)
        invoices, _ = invoice_service.list_invoices(search=search, inv_type='sale', limit=limit, offset=0)
        return invoices

    def returned_qty(self, invoice_id: int, line_id: int | None = None, item_id: int | None = None) -> Decimal:
        if self.db.is_remote():
            # في وضع الخادم تُحسب الكميات المرتجعة داخل endpoint الخاص ببنود الفاتورة.
            return Decimal('0')
        conn = self._conn()
        if line_id:
            row = conn.execute("""
                SELECT COALESCE(SUM(CAST(srl.quantity_in_base AS REAL)),0) AS qty
                FROM sales_return_lines srl
                JOIN sales_returns sr ON sr.id=srl.sales_return_id
                WHERE sr.original_invoice_id=? AND sr.deleted_at IS NULL AND srl.original_invoice_line_id=?
            """, (invoice_id, line_id)).fetchone()
        else:
            row = conn.execute("""
                SELECT COALESCE(SUM(CAST(srl.quantity_in_base AS REAL)),0) AS qty
                FROM sales_return_lines srl
                JOIN sales_returns sr ON sr.id=srl.sales_return_id
                WHERE sr.original_invoice_id=? AND sr.deleted_at IS NULL AND srl.item_id=?
            """, (invoice_id, item_id)).fetchone()
        return Decimal(str(row['qty'] if row else 0))

    def invoice_returnable_lines(self, invoice_id: int) -> List[Dict]:
        if self.db.is_remote():
            return self.db.get_rest_client().get_sales_returnable_lines(invoice_id)
        inv = invoice_service.get(invoice_id)
        if not inv or inv.get('type') != 'sale':
            raise SalesReturnException('يجب اختيار فاتورة بيع صالحة')
        result = []
        for line in inv.get('lines') or []:
            sold = Decimal(str(line.get('quantity_in_base') or line.get('quantity') or 0))
            returned = self.returned_qty(invoice_id, line.get('id'), line.get('item_id'))
            remaining = max(Decimal('0'), sold - returned)
            row = dict(line)
            row.update({'sold_qty': str(sold), 'returned_qty': str(returned), 'returnable_qty': str(remaining)})
            result.append(row)
        return result

    def create_return(self, data: Dict) -> int:
        if self.db.is_remote():
            result = self.db.get_rest_client().create_sales_return(data)
            return int((result or {}).get('id') or 0)
        uid = self._uid()
        invoice_id = int(data.get('original_invoice_id') or 0)
        inv = invoice_service.get(invoice_id)
        if not inv or inv.get('type') != 'sale':
            raise SalesReturnException('يجب اختيار فاتورة بيع صالحة')
        lines_in = data.get('lines') or []
        if not lines_in:
            raise SalesReturnException('يجب اختيار بند واحد على الأقل للمرتجع')
        invoice_lines = {int(l.get('id')): l for l in (inv.get('lines') or []) if l.get('id')}
        prepared = []
        total = Decimal('0')
        for line in lines_in:
            orig_line_id = int(line.get('original_invoice_line_id') or 0)
            orig = invoice_lines.get(orig_line_id)
            if not orig:
                raise SalesReturnException('بند المرتجع غير موجود في الفاتورة الأصلية')
            qty = Decimal(str(line.get('quantity') or 0))
            if qty <= 0:
                raise SalesReturnException('كمية المرتجع يجب أن تكون أكبر من صفر')
            sold = Decimal(str(orig.get('quantity_in_base') or orig.get('quantity') or 0))
            already = self.returned_qty(invoice_id, orig_line_id, orig.get('item_id'))
            if qty > (sold - already):
                raise SalesReturnException('كمية المرتجع أكبر من الكمية المتبقية القابلة للإرجاع')
            price = Decimal(str(orig.get('unit_price') or 0))
            cost = Decimal(str(orig.get('unit_cost') or 0))
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
        remaining_receivable = max(Decimal('0'), Decimal(str(inv.get('total') or 0)) - Decimal(str(inv.get('paid') or 0)))
        requested = data.get('refund_amount')
        refund = max(Decimal('0'), total - min(total, remaining_receivable)) if requested in (None, '') else Decimal(str(requested))
        if refund < 0 or refund > total:
            raise SalesReturnException('مبلغ الرد النقدي يجب أن يكون بين صفر وإجمالي المرتجع')
        credit = total - refund
        branch_id = data.get('branch_id') or inv.get('branch_id') or branch_service.current_branch_id()
        wh_id = data.get('warehouse_id') or inv.get('warehouse_id') or warehouse_service.default_warehouse_id()
        cashbox_id = data.get('cashbox_id') or inv.get('cashbox_id')
        bank_account_id = data.get('bank_account_id') or inv.get('bank_account_id')
        payment_method = data.get('payment_method') or inv.get('payment_method') or 'cash'
        conn = self._conn()
        now = datetime.now().isoformat()
        ret_no = data.get('return_no') or self.next_return_no()
        cur = conn.execute("""
            INSERT INTO sales_returns
            (user_id,return_no,original_invoice_id,customer_id,date,total,refund_amount,credit_amount,
             warehouse_id,branch_id,cashbox_id,bank_account_id,payment_method,notes,status,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'active', ?)
        """, (uid, ret_no, invoice_id, inv.get('customer_id'), data.get('date') or datetime.now().strftime('%Y-%m-%d'),
              str(total), str(refund), str(credit), wh_id, branch_id, cashbox_id, bank_account_id, payment_method,
              data.get('notes') or '', now))
        rid = cur.lastrowid
        for line in prepared:
            conn.execute("""
                INSERT INTO sales_return_lines
                (sales_return_id,original_invoice_line_id,item_id,quantity,unit_price,total,unit,quantity_in_base,unit_cost,cost_amount)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (rid, line['original_invoice_line_id'], line['item_id'], str(line['quantity']), str(line['unit_price']),
                  str(line['total']), line['unit'], str(line['quantity_in_base']), str(line['unit_cost']), str(line['cost_amount'])))
            self.db._record_inventory_movement(line['item_id'], 'sales_return', line['quantity_in_base'], line['unit_cost'], rid)
            warehouse_service.record_movement(line['item_id'], wh_id, 'sales_return_in', line['quantity_in_base'], line['unit_cost'], 'sales_return', rid, 'إرجاع مبيعات إلى المستودع')
        if inv.get('customer_id') and credit > 0:
            self.db._update_customer_balance(inv.get('customer_id'), -credit)
        if refund > 0:
            self.db._update_cash_balance(refund, add=False)
            try:
                cashbox_service.record_return_refund(rid, {'branch_id': branch_id, 'cashbox_id': cashbox_id,
                    'bank_account_id': bank_account_id, 'payment_method': payment_method, 'amount': refund,
                    'date': data.get('date'), 'description': f'رد مرتجع مبيعات {ret_no}'})
            except Exception:
                pass
        conn.commit()
        audit_service.log('CREATE', 'SALES_RETURN', rid, new_values=self.get(rid), details='إنشاء مرتجع مبيعات')
        return rid

    def delete_return(self, return_id: int) -> None:
        if self.db.is_remote():
            self.db.get_rest_client().delete_sales_return(return_id)
            return
        ret = self.get(return_id)
        if not ret or ret.get('deleted_at'):
            return
        conn = self._conn()
        item_ids = set()
        for line in ret.get('lines') or []:
            item_id = line.get('item_id')
            item_ids.add(item_id)
        conn.execute("DELETE FROM inventory_movements WHERE reference_id=? AND movement_type='sales_return'", (return_id,))
        for item_id in item_ids:
            self.db._update_item_quantity(item_id)
            self.db._recalculate_average_cost(item_id)
        warehouse_service.reverse_reference('sales_return', return_id)
        if ret.get('customer_id') and Decimal(str(ret.get('credit_amount') or 0)) > 0:
            self.db._update_customer_balance(ret.get('customer_id'), Decimal(str(ret.get('credit_amount'))))
        if Decimal(str(ret.get('refund_amount') or 0)) > 0:
            self.db._update_cash_balance(Decimal(str(ret.get('refund_amount'))), add=True)
        try:
            cashbox_service.reverse_reference('sales_return', return_id)
        except Exception:
            pass
        conn.execute("UPDATE sales_returns SET deleted_at=datetime('now'), status='cancelled' WHERE id=?", (return_id,))
        conn.commit()
        audit_service.log('REVERSE', 'SALES_RETURN', return_id, old_values=ret, details='إلغاء مرتجع مبيعات')

