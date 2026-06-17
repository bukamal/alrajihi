# -*- coding: utf-8 -*-
"""Local reporting gateway adapter."""
from __future__ import annotations

from typing import Any, Dict, List

from database.dao.reporting_dao import ReportingDAO
from gateways.reporting_gateway import ReportingGateway


class LocalReportingGateway(ReportingGateway):
    def __init__(self):
        self._dao = ReportingDAO()

    def summary(self, start_date: str | None = None, end_date: str | None = None) -> Dict[str, Any]:
        result = self._dao.get_summary_filtered(start_date, end_date) if (start_date or end_date) else self._dao.get_summary()
        return result if isinstance(result, dict) else {}

    def income_statement(self, start_date: str | None = None, end_date: str | None = None) -> Dict[str, Any]:
        result = self._dao.get_income_statement_filtered(start_date, end_date)
        return result if isinstance(result, dict) else {}

    def balance_sheet(self, start_date: str | None = None, end_date: str | None = None) -> Dict[str, Any]:
        result = self._dao.get_balance_sheet_filtered(start_date, end_date)
        return result if isinstance(result, dict) else {}

    def customer_statement(self, customer_id: int, start_date: str | None = None, end_date: str | None = None) -> List[Dict[str, Any]]:
        result = self._dao.get_customer_statement(customer_id, start_date, end_date)
        return result if isinstance(result, list) else []

    def supplier_statement(self, supplier_id: int, start_date: str | None = None, end_date: str | None = None) -> List[Dict[str, Any]]:
        result = self._dao.get_supplier_statement(supplier_id, start_date, end_date)
        return result if isinstance(result, list) else []

    def customer_balances(self) -> List[Dict[str, Any]]:
        result = self._dao.get_customer_balances()
        return result if isinstance(result, list) else []

    def supplier_balances(self) -> List[Dict[str, Any]]:
        result = self._dao.get_supplier_balances()
        return result if isinstance(result, list) else []

    def customer_aging(self, as_of_date: str | None = None) -> List[Dict[str, Any]]:
        result = self._dao.get_customer_aging(as_of_date)
        return result if isinstance(result, list) else []

    def supplier_aging(self, as_of_date: str | None = None) -> List[Dict[str, Any]]:
        result = self._dao.get_supplier_aging(as_of_date)
        return result if isinstance(result, list) else []

    def trial_balance(self) -> List[Dict[str, Any]]:
        result = self._dao.get_trial_balance()
        return result if isinstance(result, list) else []

    def item_movement_report(self, item_id: int | None = None, warehouse_id: int | None = None,
                             start_date: str | None = None, end_date: str | None = None,
                             limit: int = 2000, branch_id: int | None = None) -> List[Dict]:
        """Chronological item movement ledger with running balance in base unit.

        Uses inventory_ledger first because it is the normalized stock audit trail.
        Falls back to inventory_movements for older databases. The UI must not
        recompute stock direction rules independently.
        """
        try:
            from decimal import Decimal
            from database.connection import DatabaseConnection
            from auth.session import UserSession
            db = DatabaseConnection()
            uid = UserSession.get_current_user_id()
            if not uid:
                return []
            tables = {str(r[0]).lower() for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            rows: List[Dict] = []
            if 'inventory_ledger' in tables:
                sql = """
                    SELECT il.id, il.movement_date, il.item_id, i.name AS item_name,
                           COALESCE(i.barcode, '') AS barcode,
                           il.warehouse_id, COALESCE(w.name, '') AS warehouse_name,
                           w.branch_id, COALESCE(b.name, '') AS branch_name,
                           il.movement_type, il.direction,
                           CAST(il.quantity AS TEXT) AS quantity,
                           CAST(il.unit_cost AS TEXT) AS unit_cost,
                           CAST(il.total_cost AS TEXT) AS total_cost,
                           il.reference_type, il.reference_id, il.notes
                    FROM inventory_ledger il
                    LEFT JOIN items i ON i.id = il.item_id
                    LEFT JOIN warehouses w ON w.id = il.warehouse_id
                    LEFT JOIN branches b ON b.id = w.branch_id
                    WHERE il.user_id = ?
                """
                params = [uid]
                if item_id:
                    sql += " AND il.item_id = ?"
                    params.append(item_id)
                if warehouse_id:
                    sql += " AND il.warehouse_id = ?"
                    params.append(warehouse_id)
                eff_branch = self._effective_branch_id(branch_id)
                if eff_branch:
                    sql += " AND w.branch_id = ?"
                    params.append(eff_branch)
                if start_date:
                    sql += " AND date(il.movement_date) >= date(?)"
                    params.append(start_date)
                if end_date:
                    sql += " AND date(il.movement_date) <= date(?)"
                    params.append(end_date)
                sql += " ORDER BY il.movement_date, il.id LIMIT ?"
                params.append(limit)
                raw = [dict(r) for r in db.execute(sql, tuple(params)).fetchall()]
                running_by_key = {}
                for r in raw:
                    qty = Decimal(str(r.get('quantity') or '0'))
                    direction = (r.get('direction') or '').lower()
                    inbound = qty if direction == 'in' else Decimal('0')
                    outbound = qty if direction == 'out' else Decimal('0')
                    key = (r.get('item_id'), r.get('warehouse_id'))
                    running_by_key[key] = running_by_key.get(key, Decimal('0')) + inbound - outbound
                    unit_cost = Decimal(str(r.get('unit_cost') or '0'))
                    total_cost = Decimal(str(r.get('total_cost') or (qty * unit_cost)))
                    rows.append({**r, 'in_qty': inbound, 'out_qty': outbound, 'balance_qty': running_by_key[key], 'unit_cost': unit_cost, 'total_cost': total_cost})
                return rows

            if 'inventory_movements' in tables:
                sql = """
                    SELECT im.id, im.movement_date, im.item_id, i.name AS item_name,
                           COALESCE(i.barcode, '') AS barcode,
                           NULL AS warehouse_id, '' AS warehouse_name, NULL AS branch_id, '' AS branch_name,
                           im.movement_type, CAST(im.quantity AS TEXT) AS quantity,
                           CAST(im.unit_cost AS TEXT) AS unit_cost,
                           im.reference_id, '' AS reference_type, '' AS notes
                    FROM inventory_movements im
                    LEFT JOIN items i ON i.id = im.item_id
                    WHERE im.user_id = ?
                """
                params = [uid]
                if item_id:
                    sql += " AND im.item_id = ?"
                    params.append(item_id)
                if start_date:
                    sql += " AND date(im.movement_date) >= date(?)"
                    params.append(start_date)
                if end_date:
                    sql += " AND date(im.movement_date) <= date(?)"
                    params.append(end_date)
                sql += " ORDER BY im.movement_date, im.id LIMIT ?"
                params.append(limit)
                raw = [dict(r) for r in db.execute(sql, tuple(params)).fetchall()]
                running_by_item = {}
                for r in raw:
                    qty = Decimal(str(r.get('quantity') or '0'))
                    mtype = (r.get('movement_type') or '').lower()
                    is_out = any(k in mtype for k in ('out', 'sale', 'consume')) and 'return' not in mtype and 'in' not in mtype
                    inbound = Decimal('0') if is_out else qty
                    outbound = qty if is_out else Decimal('0')
                    key = r.get('item_id')
                    running_by_item[key] = running_by_item.get(key, Decimal('0')) + inbound - outbound
                    unit_cost = Decimal(str(r.get('unit_cost') or '0'))
                    rows.append({**r, 'direction': 'out' if is_out else 'in', 'in_qty': inbound, 'out_qty': outbound, 'balance_qty': running_by_item[key], 'total_cost': qty * unit_cost})
                return rows
            return []
        except Exception:
            return []

    def invoice_profit_report(self, start_date: str | None = None, end_date: str | None = None,
                              customer_id: int | None = None, limit: int = 2000, branch_id: int | None = None) -> List[Dict]:
        """Invoice profitability using stored line cost, not current item cost."""
        try:
            from decimal import Decimal
            from database.connection import DatabaseConnection
            from auth.session import UserSession
            db = DatabaseConnection()
            uid = UserSession.get_current_user_id()
            if not uid:
                return []
            sql = """
                SELECT inv.id, inv.reference, inv.date, inv.customer_id, COALESCE(c.name, '') AS customer_name,
                       inv.branch_id, COALESCE(b.name, '') AS branch_name,
                       CAST(inv.total AS TEXT) AS invoice_total,
                       CAST(COALESCE(SUM(CAST(il.cost_amount AS REAL)), 0) AS TEXT) AS cost_total
                FROM invoices inv
                LEFT JOIN customers c ON c.id = inv.customer_id
                LEFT JOIN branches b ON b.id = inv.branch_id
                LEFT JOIN invoice_lines il ON il.invoice_id = inv.id
                WHERE inv.user_id = ? AND inv.type = 'sale' AND inv.deleted_at IS NULL
            """
            params = [uid]
            if start_date:
                sql += " AND date(inv.date) >= date(?)"
                params.append(start_date)
            if end_date:
                sql += " AND date(inv.date) <= date(?)"
                params.append(end_date)
            if customer_id:
                sql += " AND inv.customer_id = ?"
                params.append(customer_id)
            eff_branch = self._effective_branch_id(branch_id)
            if eff_branch:
                sql += " AND inv.branch_id = ?"
                params.append(eff_branch)
            sql += " GROUP BY inv.id ORDER BY inv.date, inv.id LIMIT ?"
            params.append(limit)
            rows = []
            for r in db.execute(sql, tuple(params)).fetchall():
                d = dict(r)
                total = Decimal(str(d.get('invoice_total') or '0'))
                cost = Decimal(str(d.get('cost_total') or '0'))
                profit = total - cost
                margin = (profit / total * Decimal('100')) if total else Decimal('0')
                rows.append({**d, 'cost_total': cost, 'profit': profit, 'profit_margin': margin})
            return rows
        except Exception:
            return []

    def net_profit_report(self, start_date: str | None = None, end_date: str | None = None, branch_id: int | None = None) -> Dict:
        """Net profit from posted business documents: sales - sales returns - COGS."""
        try:
            from decimal import Decimal
            from database.connection import DatabaseConnection
            from auth.session import UserSession
            db = DatabaseConnection(); uid = UserSession.get_current_user_id()
            if not uid: return {}
            params = [uid]
            date_filter = ""
            if start_date:
                date_filter += " AND date(inv.date) >= date(?)"; params.append(start_date)
            if end_date:
                date_filter += " AND date(inv.date) <= date(?)"; params.append(end_date)
            eff_branch = self._effective_branch_id(branch_id)
            if eff_branch:
                date_filter += " AND inv.branch_id = ?"; params.append(eff_branch)
            sales = Decimal('0'); sales_cost = Decimal('0')
            if 'invoices' in {str(r[0]).lower() for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}:
                row = db.execute(f"""
                    SELECT CAST(COALESCE(SUM(CAST(inv.total AS REAL)),0) AS TEXT) AS total,
                           CAST(COALESCE(SUM(CAST(il.cost_amount AS REAL)),0) AS TEXT) AS cost
                    FROM invoices inv
                    LEFT JOIN invoice_lines il ON il.invoice_id = inv.id
                    WHERE inv.user_id=? AND inv.type='sale' AND inv.deleted_at IS NULL {date_filter}
                """, tuple(params)).fetchone()
                if row:
                    d=dict(row); sales=Decimal(str(d.get('total') or 0)); sales_cost=Decimal(str(d.get('cost') or 0))
            returns = Decimal('0')
            tables = {str(r[0]).lower() for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            if 'returns' in tables:
                rparams=[uid]
                rf=""
                if start_date: rf += " AND date(date) >= date(?)"; rparams.append(start_date)
                if end_date: rf += " AND date(date) <= date(?)"; rparams.append(end_date)
                row=db.execute(f"SELECT CAST(COALESCE(SUM(CAST(total AS REAL)),0) AS TEXT) AS total FROM returns WHERE user_id=? AND type IN ('sale','sales','sales_return') {rf}", tuple(rparams)).fetchone()
                returns=Decimal(str(dict(row).get('total') if row else 0 or 0))
            net_sales = sales - returns
            gross_profit = net_sales - sales_cost
            return {'sales': sales, 'sales_returns': returns, 'net_sales': net_sales, 'cogs': sales_cost, 'net_profit': gross_profit}
        except Exception:
            return {}

    def manufacturing_orders_report(self, start_date: str | None = None, end_date: str | None = None, limit: int = 2000) -> List[Dict]:
        """Manufacturing order status and actual cost report, defensive across schema variants."""
        try:
            from database.connection import DatabaseConnection
            from auth.session import UserSession
            db=DatabaseConnection(); uid=UserSession.get_current_user_id()
            tables={str(r[0]).lower() for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            if not uid or 'production_orders' not in tables: return []
            cols={str(r[1]).lower() for r in db.execute("PRAGMA table_info(production_orders)").fetchall()}
            date_col = 'created_at' if 'created_at' in cols else ('date' if 'date' in cols else 'id')
            product_expr = 'i.name AS product_name' if 'items' in tables else "'' AS product_name"
            joins = 'LEFT JOIN items i ON i.id = po.product_id' if 'items' in tables and 'product_id' in cols else ''
            cost_col = 'actual_cost' if 'actual_cost' in cols else ('total_cost' if 'total_cost' in cols else '0')
            qty_col = 'quantity' if 'quantity' in cols else ('qty' if 'qty' in cols else '0')
            status_expr = 'po.status' if 'status' in cols else "''"
            sql=f"SELECT po.id, po.{date_col} AS date, {product_expr}, CAST(po.{qty_col} AS TEXT) AS quantity, CAST(po.{cost_col} AS TEXT) AS actual_cost, {status_expr} AS status FROM production_orders po {joins} WHERE po.user_id=?"
            params=[uid]
            if date_col!='id' and start_date: sql += f" AND date(po.{date_col}) >= date(?)"; params.append(start_date)
            if date_col!='id' and end_date: sql += f" AND date(po.{date_col}) <= date(?)"; params.append(end_date)
            sql += f" ORDER BY po.{date_col}, po.id LIMIT ?"; params.append(limit)
            return [dict(r) for r in db.execute(sql, tuple(params)).fetchall()]
        except Exception:
            return []

    def product_cost_report(self, item_id: int | None = None, limit: int = 2000) -> List[Dict]:
        """Product cost report based on item average/purchase cost and optional BOM components."""
        try:
            from decimal import Decimal
            from database.connection import DatabaseConnection
            from auth.session import UserSession
            db=DatabaseConnection(); uid=UserSession.get_current_user_id()
            tables={str(r[0]).lower() for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            if not uid or 'items' not in tables: return []
            params=[uid]
            sql="""
                SELECT i.id, i.name, COALESCE(i.barcode,'') AS barcode,
                       CAST(COALESCE(i.average_cost, i.purchase_price, 0) AS TEXT) AS unit_cost
                FROM items i WHERE i.user_id=?
            """
            if item_id: sql += " AND i.id=?"; params.append(item_id)
            sql += " ORDER BY i.name LIMIT ?"; params.append(limit)
            rows=[]
            for r in db.execute(sql, tuple(params)).fetchall():
                d=dict(r); cost=Decimal(str(d.get('unit_cost') or 0)); components=0; bom_cost=Decimal('0')
                if 'bom_lines' in tables:
                    try:
                        brow=db.execute("SELECT COUNT(*) AS cnt, CAST(COALESCE(SUM(CAST(quantity AS REAL)*CAST(unit_cost AS REAL)),0) AS TEXT) AS cost FROM bom_lines WHERE product_id=?", (d.get('id'),)).fetchone()
                        bd=dict(brow); components=int(bd.get('cnt') or 0); bom_cost=Decimal(str(bd.get('cost') or 0))
                    except Exception: pass
                rows.append({**d, 'components_count': components, 'bom_cost': bom_cost, 'final_cost': bom_cost if bom_cost > 0 else cost})
            return rows
        except Exception:
            return []

    def _db_tables(self):
        try:
            from database.connection import DatabaseConnection
            db = DatabaseConnection()
            return db, {str(r[0]).lower() for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        except Exception:
            return None, set()

    def _current_user_id(self):
        try:
            from auth.session import UserSession
            return UserSession.get_current_user_id()
        except Exception:
            return None

    def general_ledger_report(self, account_id: int | None = None,
                              start_date: str | None = None, end_date: str | None = None,
                              limit: int = 5000) -> List[Dict]:
        """General ledger by account with opening and running balance.

        Reads accounting_entries/accounting_entry_lines when available and
        remains defensive across older local schemas.  No UI-side accounting
        formulas are used here.
        """
        try:
            from decimal import Decimal
            db, tables = self._db_tables(); uid = self._current_user_id()
            if not db or not uid:
                return []
            entry_table = 'accounting_entries' if 'accounting_entries' in tables else ('journal_entries' if 'journal_entries' in tables else None)
            line_table = 'accounting_entry_lines' if 'accounting_entry_lines' in tables else ('journal_entry_lines' if 'journal_entry_lines' in tables else None)
            if not entry_table or not line_table or 'accounts' not in tables:
                return []
            account_filter = " AND l.account_id = ?" if account_id else ""
            opening = {}
            if start_date:
                params = [uid]
                if account_id: params.append(account_id)
                params.append(start_date)
                sql = f"""
                    SELECT l.account_id, CAST(COALESCE(SUM(CAST(l.debit AS REAL)),0) AS TEXT) AS debit,
                           CAST(COALESCE(SUM(CAST(l.credit AS REAL)),0) AS TEXT) AS credit
                    FROM {line_table} l
                    JOIN {entry_table} e ON e.id = l.entry_id
                    WHERE e.user_id = ? {account_filter} AND date(COALESCE(e.entry_date,e.date,e.created_at)) < date(?)
                    GROUP BY l.account_id
                """
                for r in db.execute(sql, tuple(params)).fetchall():
                    d=dict(r); opening[d.get('account_id')] = Decimal(str(d.get('debit') or 0)) - Decimal(str(d.get('credit') or 0))
            params = [uid]
            if account_id: params.append(account_id)
            date_filter = ""
            if start_date:
                date_filter += " AND date(COALESCE(e.entry_date,e.date,e.created_at)) >= date(?)"; params.append(start_date)
            if end_date:
                date_filter += " AND date(COALESCE(e.entry_date,e.date,e.created_at)) <= date(?)"; params.append(end_date)
            params.append(limit)
            sql = f"""
                SELECT e.id AS entry_id, COALESCE(e.entry_date,e.date,e.created_at) AS entry_date,
                       COALESCE(e.reference,e.reference_no,e.source_reference,'') AS reference,
                       COALESCE(e.description,e.notes,'') AS description,
                       l.account_id, COALESCE(a.code,'') AS account_code, COALESCE(a.name,'') AS account_name,
                       CAST(COALESCE(l.debit,0) AS TEXT) AS debit,
                       CAST(COALESCE(l.credit,0) AS TEXT) AS credit
                FROM {line_table} l
                JOIN {entry_table} e ON e.id = l.entry_id
                LEFT JOIN accounts a ON a.id = l.account_id
                WHERE e.user_id = ? {account_filter} {date_filter}
                ORDER BY l.account_id, date(COALESCE(e.entry_date,e.date,e.created_at)), e.id, l.id
                LIMIT ?
            """
            running = dict(opening)
            rows=[]
            for r in db.execute(sql, tuple(params)).fetchall():
                d=dict(r); aid=d.get('account_id')
                debit=Decimal(str(d.get('debit') or 0)); credit=Decimal(str(d.get('credit') or 0))
                if aid not in running: running[aid]=Decimal('0')
                running[aid] += debit - credit
                rows.append({**d, 'debit': debit, 'credit': credit, 'balance': running[aid], 'opening_balance': opening.get(aid, Decimal('0'))})
            return rows
        except Exception:
            return []

    def full_trial_balance_report(self, start_date: str | None = None, end_date: str | None = None) -> Dict:
        """Trial balance with opening, movement and closing balances."""
        try:
            from decimal import Decimal
            db, tables = self._db_tables(); uid = self._current_user_id()
            if not db or not uid or 'accounts' not in tables:
                return {'rows': [], 'total_debit': Decimal('0'), 'total_credit': Decimal('0'), 'balanced': True, 'difference': Decimal('0')}
            entry_table = 'accounting_entries' if 'accounting_entries' in tables else ('journal_entries' if 'journal_entries' in tables else None)
            line_table = 'accounting_entry_lines' if 'accounting_entry_lines' in tables else ('journal_entry_lines' if 'journal_entry_lines' in tables else None)
            if not entry_table or not line_table:
                rows = self.trial_balance()
                td=sum((Decimal(str(r.get('debit') or r.get('debit_total') or 0)) for r in rows), Decimal('0'))
                tc=sum((Decimal(str(r.get('credit') or r.get('credit_total') or 0)) for r in rows), Decimal('0'))
                return {'rows': rows, 'total_debit': td, 'total_credit': tc, 'balanced': td == tc, 'difference': td - tc}
            params=[uid]
            date_filter=''
            if start_date: date_filter += ' AND date(COALESCE(e.entry_date,e.date,e.created_at)) >= date(?)'; params.append(start_date)
            if end_date: date_filter += ' AND date(COALESCE(e.entry_date,e.date,e.created_at)) <= date(?)'; params.append(end_date)
            sql=f"""
                SELECT a.id, COALESCE(a.code,'') AS code, COALESCE(a.name,'') AS account_name,
                       CAST(COALESCE(SUM(CAST(l.debit AS REAL)),0) AS TEXT) AS debit,
                       CAST(COALESCE(SUM(CAST(l.credit AS REAL)),0) AS TEXT) AS credit
                FROM accounts a
                LEFT JOIN {line_table} l ON l.account_id = a.id
                LEFT JOIN {entry_table} e ON e.id = l.entry_id AND e.user_id = ? {date_filter}
                WHERE a.user_id = ? OR a.user_id IS NULL
                GROUP BY a.id
                HAVING debit <> '0' OR credit <> '0'
                ORDER BY a.code, a.name
            """
            # user id is needed twice because date filter belongs to JOIN.
            rows=[]; td=Decimal('0'); tc=Decimal('0')
            for r in db.execute(sql, tuple(params+[uid])).fetchall():
                d=dict(r); debit=Decimal(str(d.get('debit') or 0)); credit=Decimal(str(d.get('credit') or 0))
                td += debit; tc += credit
                rows.append({**d, 'debit': debit, 'credit': credit, 'balance': debit-credit})
            return {'rows': rows, 'total_debit': td, 'total_credit': tc, 'balanced': td == tc, 'difference': td - tc}
        except Exception:
            return {'rows': [], 'total_debit': 0, 'total_credit': 0, 'balanced': False, 'difference': 0}

    def smart_items_report(self, kind: str, start_date: str | None = None, end_date: str | None = None,
                           warehouse_id: int | None = None, limit: int = 500, branch_id: int | None = None) -> List[Dict]:
        """Inventory intelligence reports: slow, top, low, reorder."""
        try:
            from decimal import Decimal
            from datetime import date
            db, tables = self._db_tables(); uid = self._current_user_id()
            if not db or not uid or 'items' not in tables:
                return []
            rows=[]
            if kind == 'reorder':
                if 'warehouse_stock' in tables:
                    sql="""
                        SELECT i.id, i.name, COALESCE(i.barcode,'') AS barcode, COALESCE(w.name,'') AS warehouse_name,
                               CAST(COALESCE(ws.quantity,0) AS TEXT) AS quantity,
                               CAST(COALESCE(i.min_stock, i.reorder_level, 0) AS TEXT) AS min_stock
                        FROM items i
                        LEFT JOIN warehouse_stock ws ON ws.item_id=i.id
                        LEFT JOIN warehouses w ON w.id=ws.warehouse_id
                        WHERE i.user_id=? AND CAST(COALESCE(ws.quantity,0) AS REAL) <= CAST(COALESCE(i.min_stock, i.reorder_level, 0) AS REAL)
                    """
                    params=[uid]
                    if warehouse_id: sql += ' AND ws.warehouse_id=?'; params.append(warehouse_id)
                    eff_branch = self._effective_branch_id(branch_id)
                    if eff_branch: sql += ' AND w.branch_id=?'; params.append(eff_branch)
                    sql += ' ORDER BY i.name LIMIT ?'; params.append(limit)
                    for r in db.execute(sql, tuple(params)).fetchall():
                        d=dict(r); qty=Decimal(str(d.get('quantity') or 0)); mn=Decimal(str(d.get('min_stock') or 0))
                        rows.append({**d, 'shortage': max(mn-qty, Decimal('0'))})
                return rows
            # Sales aggregation from invoice_lines.
            if 'invoice_lines' in tables and 'invoices' in tables:
                date_filter=''; params=[uid]
                if start_date: date_filter+=' AND date(inv.date) >= date(?)'; params.append(start_date)
                if end_date: date_filter+=' AND date(inv.date) <= date(?)'; params.append(end_date)
                eff_branch = self._effective_branch_id(branch_id)
                if eff_branch: date_filter+=' AND inv.branch_id = ?'; params.append(eff_branch)
                order = 'qty DESC' if kind == 'top' else 'qty ASC'
                sql=f"""
                    SELECT i.id, i.name, COALESCE(i.barcode,'') AS barcode,
                           CAST(COALESCE(SUM(CAST(il.quantity AS REAL) * CAST(COALESCE(il.conversion_factor,1) AS REAL)),0) AS TEXT) AS qty,
                           CAST(COALESCE(SUM(CAST(il.total AS REAL)),0) AS TEXT) AS sales_value,
                           MAX(inv.date) AS last_sale_date,
                           CAST(COALESCE(SUM(CAST(COALESCE(il.cost_amount,0) AS REAL)),0) AS TEXT) AS cost_value
                    FROM items i
                    LEFT JOIN invoice_lines il ON il.item_id=i.id
                    LEFT JOIN invoices inv ON inv.id=il.invoice_id AND inv.type='sale' AND inv.deleted_at IS NULL {date_filter}
                    WHERE i.user_id=?
                    GROUP BY i.id
                """
                # uid must be last because date_filter params belong to join before WHERE.
                exec_params = params[1:] + [uid]
                if kind in ('top','low'):
                    sql += f" ORDER BY CAST(qty AS REAL) {'DESC' if kind=='top' else 'ASC'}, i.name LIMIT ?"
                    exec_params.append(limit)
                else:
                    sql += ' ORDER BY last_sale_date IS NOT NULL, last_sale_date, i.name LIMIT ?'
                    exec_params.append(limit)
                for r in db.execute(sql, tuple(exec_params)).fetchall():
                    d=dict(r); qty=Decimal(str(d.get('qty') or 0)); sales=Decimal(str(d.get('sales_value') or 0)); cost=Decimal(str(d.get('cost_value') or 0))
                    profit=sales-cost
                    days_without=None
                    if d.get('last_sale_date'):
                        try:
                            days_without=(date.today()-date.fromisoformat(str(d.get('last_sale_date'))[:10])).days
                        except Exception: days_without=None
                    rows.append({**d, 'qty': qty, 'sales_value': sales, 'cost_value': cost, 'profit': profit, 'days_without_movement': days_without})
            return rows
        except Exception:
            return []

    def is_remote(self) -> bool:
        return False
