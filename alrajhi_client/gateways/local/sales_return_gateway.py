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
from core.services.inventory_service import inventory_service
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

    def _ensure_manual_return_schema(self) -> None:
        """Allow sales returns without an original invoice."""
        conn = self._conn()
        info = conn.execute("PRAGMA table_info(sales_returns)").fetchall()
        row = next((r for r in info if str(r['name'] if hasattr(r, 'keys') else r[1]) == 'original_invoice_id'), None)
        not_null = bool(row['notnull'] if row is not None and hasattr(row, 'keys') else (row[3] if row is not None else 0))
        if not not_null:
            return
        conn.execute('PRAGMA foreign_keys=OFF')
        conn.execute('ALTER TABLE sales_returns RENAME TO sales_returns_phase348_legacy')
        conn.execute("""
            CREATE TABLE sales_returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                return_no TEXT,
                original_invoice_id INTEGER,
                customer_id INTEGER,
                date TEXT,
                total TEXT DEFAULT '0',
                refund_amount TEXT DEFAULT '0',
                credit_amount TEXT DEFAULT '0',
                warehouse_id INTEGER,
                branch_id INTEGER,
                cashbox_id INTEGER,
                bank_account_id INTEGER,
                payment_method TEXT DEFAULT 'cash',
                notes TEXT,
                status TEXT DEFAULT 'active',
                deleted_at TEXT,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (original_invoice_id) REFERENCES invoices(id),
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        """)
        cols = [r['name'] if hasattr(r, 'keys') else r[1] for r in info]
        common = [c for c in cols if c in {
            'id','user_id','return_no','original_invoice_id','customer_id','date','total','refund_amount','credit_amount',
            'warehouse_id','branch_id','cashbox_id','bank_account_id','payment_method','notes','status','deleted_at','created_at'
        }]
        col_sql = ','.join(common)
        conn.execute(f"INSERT INTO sales_returns ({col_sql}) SELECT {col_sql} FROM sales_returns_phase348_legacy")
        conn.execute('DROP TABLE sales_returns_phase348_legacy')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_sales_returns_user ON sales_returns(user_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_sales_returns_invoice ON sales_returns(original_invoice_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_sales_returns_branch ON sales_returns(branch_id)')
        conn.execute('PRAGMA foreign_keys=ON')
        conn.commit()

    def _create_manual_return(self, data: Dict) -> int:
        uid = self._uid()
        lines_in = data.get('lines') or []
        if not lines_in:
            raise SalesReturnException('يجب إدخال بند واحد على الأقل للمرتجع')
        self._ensure_manual_return_schema()
        wh_id = data.get('warehouse_id') or warehouse_service.default_warehouse_id()
        branch_id = data.get('branch_id') or branch_service.current_branch_id()
        cashbox_id = data.get('cashbox_id')
        bank_account_id = data.get('bank_account_id')
        payment_method = data.get('payment_method') or 'cash'
        prepared = []
        total = Decimal('0')
        for line in lines_in:
            item_id = int(line.get('item_id') or 0)
            if not item_id:
                continue
            qty = Decimal(str(line.get('quantity') or 0))
            if qty <= 0:
                raise SalesReturnException('كمية المرتجع يجب أن تكون أكبر من صفر')
            factor = Decimal(str(line.get('conversion_factor') or 1))
            if factor <= 0:
                factor = Decimal('1')
            base_qty = Decimal(str(line.get('base_qty', line.get('quantity_in_base', qty * factor)) or 0))
            if base_qty <= 0:
                base_qty = qty * factor
            unit_price = Decimal(str(line.get('unit_price') or line.get('price') or 0))
            unit_cost = Decimal(str(line.get('unit_cost') or line.get('cost') or unit_price or 0))
            amount = Decimal(str(line.get('total') or (qty * unit_price)))
            total += amount
            prepared.append({
                'original_invoice_line_id': None,
                'item_id': item_id,
                'quantity': qty,
                'quantity_in_base': base_qty,
                'unit_price': unit_price,
                'unit_cost': unit_cost,
                'total': amount,
                'unit': line.get('unit') or '',
                'unit_id': line.get('unit_id'),
                'conversion_factor': factor,
                'cost_amount': base_qty * unit_cost,
                'variant_id': line.get('variant_id'),
                'variant_color': line.get('variant_color') or '',
                'variant_size': line.get('variant_size') or '',
                'variant_sku': line.get('variant_sku') or '',
                'barcode_scope': line.get('barcode_scope') or '',
                'matched_barcode': line.get('matched_barcode') or line.get('barcode') or '',
            })
        if not prepared:
            raise SalesReturnException('يجب إدخال بند واحد على الأقل للمرتجع')
        requested = data.get('refund_amount')
        refund = total if requested in (None, '') else Decimal(str(requested or 0))
        if refund < 0 or refund > total:
            raise SalesReturnException('مبلغ الرد النقدي يجب أن يكون بين صفر وإجمالي المرتجع')
        credit = total - refund
        conn = self._conn()
        now = datetime.now().isoformat()
        ret_no = data.get('return_no') or self.next_return_no()
        cur = conn.execute("""
            INSERT INTO sales_returns
            (user_id,return_no,original_invoice_id,customer_id,date,total,refund_amount,credit_amount,
             warehouse_id,branch_id,cashbox_id,bank_account_id,payment_method,notes,status,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'active', ?)
        """, (uid, ret_no, None, data.get('customer_id'), data.get('date') or datetime.now().strftime('%Y-%m-%d'),
              str(total), str(refund), str(credit), wh_id, branch_id, cashbox_id, bank_account_id, payment_method,
              data.get('notes') or '', now))
        rid = cur.lastrowid
        for line in prepared:
            conn.execute("""
                INSERT INTO sales_return_lines
                (sales_return_id,original_invoice_line_id,item_id,quantity,unit_price,total,unit,unit_id,conversion_factor,quantity_in_base,unit_cost,cost_amount)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (rid, None, line['item_id'], str(line['quantity']), str(line['unit_price']), str(line['total']),
                  line['unit'], line.get('unit_id'), str(line.get('conversion_factor') or 1), str(line['quantity_in_base']),
                  str(line['unit_cost']), str(line['cost_amount'])))
            variant_data = {k: line.get(k) for k in ('variant_id','variant_color','variant_size','variant_sku','barcode_scope','matched_barcode')}
            self.db._record_inventory_movement(line['item_id'], 'sales_return', line['quantity_in_base'], line['unit_cost'], rid)
            warehouse_service.record_movement(line['item_id'], wh_id, 'sales_return_in', line['quantity_in_base'], line['unit_cost'], 'sales_return', rid, 'مرتجع مبيعات يدوي إلى المستودع', **variant_data)
            inventory_service.record_ledger_entry(
                item_id=line['item_id'], warehouse_id=wh_id, movement_type='sales_return_in',
                direction='in', quantity=line['quantity_in_base'], unit_cost=line['unit_cost'],
                reference_type='sales_return', reference_id=rid, source_table='sales_returns',
                source_id=rid, notes='دفتر مخزون مرتجع بيع يدوي'
            )
        if data.get('customer_id') and credit > 0:
            self.db._update_customer_balance(data.get('customer_id'), -credit)
        if refund > 0:
            self.db._update_cash_balance(refund, add=False)
            try:
                cashbox_service.record_return_refund(rid, {'branch_id': branch_id, 'cashbox_id': cashbox_id,
                    'bank_account_id': bank_account_id, 'payment_method': payment_method, 'amount': refund,
                    'date': data.get('date'), 'description': f'رد مرتجع مبيعات يدوي {ret_no}'})
            except Exception:
                pass
        conn.commit()
        audit_service.log('CREATE', 'SALES_RETURN', rid, new_values=self.get(rid), details='إنشاء مرتجع مبيعات يدوي')
        return rid

    def _unit_factor_for_return(self, orig: Dict, line: Dict) -> Tuple[Decimal, str, Optional[int]]:
        """Resolve the selected return unit against item units; never trust client conversion blindly."""
        item_id = orig.get('item_id')
        orig_factor = Decimal(str(orig.get('conversion_factor') or 1))
        if orig_factor <= 0:
            orig_factor = Decimal('1')
        unit_id = line.get('unit_id')
        unit_name = str(line.get('unit') or orig.get('unit') or '').strip()
        conn = self._conn()
        if item_id and unit_id not in (None, ''):
            row = conn.execute("SELECT id, unit_name, conversion_factor FROM item_units WHERE id=? AND item_id=?", (unit_id, item_id)).fetchone()
            if not row:
                raise SalesReturnException('وحدة المرتجع لا تتبع المادة المحددة')
            factor = Decimal(str(row['conversion_factor'] or 1))
            if factor <= 0:
                raise SalesReturnException('معامل وحدة المرتجع غير صالح')
            return factor, str(row['unit_name'] or unit_name), int(row['id'])
        if item_id and unit_name:
            item = conn.execute("SELECT unit FROM items WHERE id=?", (item_id,)).fetchone()
            if item and str(item['unit'] or '').strip() == unit_name:
                return Decimal('1'), unit_name, None
            row = conn.execute("SELECT id, unit_name, conversion_factor FROM item_units WHERE item_id=? AND unit_name=?", (item_id, unit_name)).fetchone()
            if row:
                factor = Decimal(str(row['conversion_factor'] or 1))
                if factor <= 0:
                    raise SalesReturnException('معامل وحدة المرتجع غير صالح')
                return factor, str(row['unit_name'] or unit_name), int(row['id'])
        return orig_factor, unit_name, line.get('unit_id') if line.get('unit_id') not in (None, '') else orig.get('unit_id')

    def _return_unit_price(self, orig: Dict, factor: Decimal) -> Decimal:
        orig_factor = Decimal(str(orig.get('conversion_factor') or 1))
        if orig_factor <= 0:
            orig_factor = Decimal('1')
        return (Decimal(str(orig.get('unit_price') or orig.get('price') or 0)) / orig_factor) * factor

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
        ret['lines'] = [dict(x) for x in self._conn().execute("""
            SELECT rl.*, it.name AS item_name, it.barcode AS barcode, it.unit AS base_unit
            FROM sales_return_lines rl
            LEFT JOIN items it ON it.id = rl.item_id
            WHERE rl.sales_return_id=?
        """, (return_id,)).fetchall()]
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
            factor = Decimal(str(line.get('conversion_factor') or 1))
            if factor <= 0:
                factor = Decimal('1')
            sold_base = Decimal(str(line.get('quantity_in_base') or line.get('quantity') or 0))
            returned_base = self.returned_qty(invoice_id, line.get('id'), line.get('item_id'))
            remaining_base = max(Decimal('0'), sold_base - returned_base)
            row = dict(line)
            # Expose quantities in the same invoice/display unit, because unit_price
            # is also stored per invoice/display unit.  Keep *_base for validation.
            row.update({
                'sold_qty': str(sold_base / factor),
                'returned_qty': str(returned_base / factor),
                'returnable_qty': str(remaining_base / factor),
                'sold_qty_base': str(sold_base),
                'returned_qty_base': str(returned_base),
                'returnable_qty_base': str(remaining_base),
                'conversion_factor': str(factor),
                'invoice_currency': inv.get('original_currency') or 'USD',
                'invoice_exchange_rate_to_usd': inv.get('exchange_rate_to_usd') or 1,
                'line_currency': 'USD',
                'unit_price_usd': str(line.get('unit_price') or line.get('price') or 0),
            })
            result.append(row)
        return result

    def create_return(self, data: Dict) -> int:
        if self.db.is_remote():
            result = self.db.get_rest_client().create_sales_return(data)
            return int((result or {}).get('id') or 0)
        uid = self._uid()
        invoice_id = int(data.get('original_invoice_id') or 0)
        if not invoice_id:
            return self._create_manual_return(data)
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
            factor, unit_name, unit_id = self._unit_factor_for_return(orig, line)
            base_qty = qty * factor
            explicit_base = line.get('base_qty', line.get('quantity_in_base'))
            if explicit_base not in (None, ''):
                base_qty = Decimal(str(explicit_base or 0))
                if base_qty != qty * factor:
                    base_qty = qty * factor
            sold = Decimal(str(orig.get('quantity_in_base') or orig.get('quantity') or 0))
            already = self.returned_qty(invoice_id, orig_line_id, orig.get('item_id'))
            if base_qty > (sold - already):
                raise SalesReturnException('كمية المرتجع أكبر من الكمية المتبقية القابلة للإرجاع')
            price = self._return_unit_price(orig, factor)
            # Sales invoices may store unit_cost as the display selling price in legacy rows.
            # For a sales return, inventory must be re-entered at the original COGS,
            # derived from invoice_lines.cost_amount / quantity_in_base when available.
            orig_cost_amount = Decimal(str(orig.get('cost_amount') or 0))
            cost_per_base_unit = (orig_cost_amount / sold) if sold > 0 and orig_cost_amount > 0 else (Decimal(str(orig.get('unit_cost') or price)) / factor)
            amount = qty * price
            total += amount
            prepared.append({
                'original_invoice_line_id': orig_line_id,
                'item_id': orig.get('item_id'),
                'quantity': qty,
                'quantity_in_base': base_qty,
                'unit_price': price,
                'unit_cost': cost_per_base_unit,
                'total': amount,
                'unit': unit_name,
                'unit_id': unit_id,
                'conversion_factor': factor,
                'cost_amount': base_qty * cost_per_base_unit,
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
                (sales_return_id,original_invoice_line_id,item_id,quantity,unit_price,total,unit,unit_id,conversion_factor,quantity_in_base,unit_cost,cost_amount)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (rid, line['original_invoice_line_id'], line['item_id'], str(line['quantity']), str(line['unit_price']),
                  str(line['total']), line['unit'], line.get('unit_id'), str(line.get('conversion_factor') or 1), str(line['quantity_in_base']), str(line['unit_cost']), str(line['cost_amount'])))
            self.db._record_inventory_movement(line['item_id'], 'sales_return', line['quantity_in_base'], line['unit_cost'], rid)
            warehouse_service.record_movement(line['item_id'], wh_id, 'sales_return_in', line['quantity_in_base'], line['unit_cost'], 'sales_return', rid, 'إرجاع مبيعات إلى المستودع')
            inventory_service.record_ledger_entry(
                item_id=line['item_id'], warehouse_id=wh_id, movement_type='sales_return_in',
                direction='in', quantity=line['quantity_in_base'], unit_cost=line['unit_cost'],
                reference_type='sales_return', reference_id=rid, source_table='sales_returns',
                source_id=rid, notes='دفتر مخزون مرتجع بيع'
            )
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
        for line in ret.get('lines') or []:
            inventory_service.record_ledger_entry(
                item_id=line.get('item_id'), warehouse_id=ret.get('warehouse_id'), movement_type='sales_return_reversal',
                direction='out', quantity=line.get('quantity_in_base') or line.get('quantity') or 0,
                unit_cost=line.get('unit_cost') or 0, reference_type='sales_return',
                reference_id=return_id, source_table='sales_returns', source_id=return_id,
                notes='عكس دفتر مخزون مرتجع بيع'
            )
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


    def update_return(self, return_id: int, data: Dict) -> int:
        """Replace an active return through the same reversal/create pipeline."""
        if self.db.is_remote():
            result = self.db.get_rest_client().update_sales_return(return_id, data or {})
            return int((result or {}).get('id') or return_id)
        old = self.get(return_id)
        if not old or old.get('deleted_at'):
            raise SalesReturnException('المرتجع غير موجود أو ملغى')
        data = dict(data or {})
        data.setdefault('return_no', old.get('return_no'))
        data.setdefault('original_invoice_id', old.get('original_invoice_id'))
        self.delete_return(return_id)
        new_id = self.create_return(data)
        audit_service.log('UPDATE', 'SALES_RETURN', new_id, old_values=old, new_values=self.get(new_id), details='تعديل مرتجع عبر عكس وإعادة إنشاء محاسبي')
        return new_id
