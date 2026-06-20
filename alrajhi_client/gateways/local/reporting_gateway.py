# -*- coding: utf-8 -*-
"""Local reporting gateway adapter."""
from __future__ import annotations

from typing import Any, Dict, List

from database.dao.reporting_dao import ReportingDAO
from gateways.reporting_gateway import ReportingGateway


class LocalReportingGateway(ReportingGateway):
    def __init__(self):
        self._dao = ReportingDAO()

    def _effective_branch_id(self, branch_id=None):
        try:
            from core.services.permission_service import permission_service
            return permission_service.effective_branch_id(branch_id)
        except Exception:
            return branch_id

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
        """Net profit from non-duplicated sales, returns, COGS and expenses."""
        try:
            from decimal import Decimal
            from database.connection import DatabaseConnection
            from auth.session import UserSession
            db = DatabaseConnection(); uid = UserSession.get_current_user_id()
            if not uid:
                return {}
            tables = {str(r[0]).lower() for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            def _date(col, start=None, end=None):
                sql = '' ; params = []
                if start:
                    sql += f" AND date({col}) >= date(?)"; params.append(start)
                if end:
                    sql += f" AND date({col}) <= date(?)"; params.append(end)
                return sql, params
            def _sum(sql, params):
                try:
                    row = db.execute(sql, tuple(params)).fetchone()
                    return Decimal(str(row[0] if row and row[0] is not None else '0'))
                except Exception:
                    return Decimal('0')
            eff_branch = self._effective_branch_id(branch_id)
            branch_sql = " AND branch_id = ?" if eff_branch else ""
            branch_params = [eff_branch] if eff_branch else []
            dsql, dparams = _date('date', start_date, end_date)
            sales = _sum("SELECT CAST(COALESCE(SUM(CAST(total AS REAL)),0) AS TEXT) FROM invoices WHERE user_id=? AND type='sale' AND deleted_at IS NULL" + branch_sql + dsql, [uid] + branch_params + dparams) if 'invoices' in tables else Decimal('0')
            purchases = _sum("SELECT CAST(COALESCE(SUM(CAST(total AS REAL)),0) AS TEXT) FROM invoices WHERE user_id=? AND type='purchase' AND deleted_at IS NULL" + branch_sql + dsql, [uid] + branch_params + dparams) if 'invoices' in tables else Decimal('0')
            cost_dsql, cost_dparams = _date('inv.date', start_date, end_date)
            cogs = _sum("""SELECT CAST(COALESCE(SUM(CAST(COALESCE(il.cost_amount,0) AS REAL)),0) AS TEXT)
                           FROM invoice_lines il JOIN invoices inv ON inv.id=il.invoice_id
                           WHERE inv.user_id=? AND inv.type='sale' AND inv.deleted_at IS NULL""" + (" AND inv.branch_id=?" if eff_branch else "") + cost_dsql, [uid] + branch_params + cost_dparams) if {'invoices','invoice_lines'} <= tables else Decimal('0')
            sr = _sum("SELECT CAST(COALESCE(SUM(CAST(total AS REAL)),0) AS TEXT) FROM sales_returns WHERE user_id=? AND deleted_at IS NULL" + branch_sql + dsql, [uid] + branch_params + dparams) if 'sales_returns' in tables else Decimal('0')
            pr = _sum("SELECT CAST(COALESCE(SUM(CAST(total AS REAL)),0) AS TEXT) FROM purchase_returns WHERE user_id=? AND deleted_at IS NULL" + branch_sql + dsql, [uid] + branch_params + dparams) if 'purchase_returns' in tables else Decimal('0')
            exp_v = _sum("SELECT CAST(COALESCE(SUM(CAST(amount AS REAL)),0) AS TEXT) FROM vouchers WHERE user_id=? AND type='expense'" + branch_sql + dsql, [uid] + branch_params + dparams) if 'vouchers' in tables else Decimal('0')
            expense_date_sql, expense_date_params = _date('expense_date', start_date, end_date)
            exp_t = _sum("SELECT CAST(COALESCE(SUM(CAST(amount AS REAL)),0) AS TEXT) FROM expenses WHERE user_id=?" + expense_date_sql, [uid] + expense_date_params) if 'expenses' in tables else Decimal('0')
            expenses = exp_v + exp_t
            net_sales = sales - sr
            gross_profit = net_sales - cogs
            net_profit = gross_profit - expenses
            return {'sales': sales, 'purchases': purchases, 'sales_returns': sr, 'purchase_returns': pr, 'net_sales': net_sales, 'cogs': cogs, 'gross_profit': gross_profit, 'expenses': expenses, 'net_profit': net_profit}
        except Exception:
            return {}

    def manufacturing_orders_report(self, start_date: str | None = None, end_date: str | None = None, status: str | None = None, limit: int = 2000) -> List[Dict]:
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
            cost_col = 'actual_cost' if 'actual_cost' in cols else ('total_cost' if 'total_cost' in cols else None)
            qty_col = 'planned_qty' if 'planned_qty' in cols else ('quantity' if 'quantity' in cols else ('qty' if 'qty' in cols else None))
            qty_expr = f"CAST(po.{qty_col} AS TEXT)" if qty_col else "'0'"
            cost_expr = f"CAST(po.{cost_col} AS TEXT)" if cost_col else "'0'"
            status_expr = 'po.status' if 'status' in cols else "''"
            sql=f"SELECT po.id, po.{date_col} AS date, {product_expr}, {qty_expr} AS quantity, {cost_expr} AS actual_cost, {status_expr} AS status FROM production_orders po {joins} WHERE po.user_id=?"
            params=[uid]
            if date_col!='id' and start_date: sql += f" AND date(po.{date_col}) >= date(?)"; params.append(start_date)
            if date_col!='id' and end_date: sql += f" AND date(po.{date_col}) <= date(?)"; params.append(end_date)
            if status and 'status' in cols:
                sql += " AND po.status = ?"; params.append(status)
            sql += f" ORDER BY po.{date_col}, po.id LIMIT ?"; params.append(limit)
            return [dict(r) for r in db.execute(sql, tuple(params)).fetchall()]
        except Exception:
            return []

    def product_cost_report(self, search: str | None = None, limit: int = 1000, branch_id: int | None = None, item_id: int | None = None) -> List[Dict]:
        """Product cost report from item cost plus BOM/component cost when available."""
        try:
            from decimal import Decimal
            from database.connection import DatabaseConnection
            from auth.session import UserSession
            db = DatabaseConnection(); uid = UserSession.get_current_user_id()
            tables = {str(r[0]).lower() for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            if not uid or 'items' not in tables:
                return []
            item_cols = {str(r[1]).lower() for r in db.execute("PRAGMA table_info(items)").fetchall()}
            cost_sources = [c for c in ("i.average_cost", "i.purchase_price", "i.cost_price") if c.split(".", 1)[1] in item_cols]
            unit_cost_expr = "COALESCE(" + ", ".join(cost_sources + ["0"]) + ")"
            selling_expr = "COALESCE(" + ("i.selling_price" if "selling_price" in item_cols else "0") + ", 0)"
            deleted_filter = " AND i.deleted_at IS NULL" if "deleted_at" in item_cols else ""
            params=[uid]
            sql=f"""
                SELECT i.id, i.name, COALESCE(i.barcode,'') AS barcode,
                       CAST({unit_cost_expr} AS TEXT) AS unit_cost,
                       CAST({selling_expr} AS TEXT) AS selling_price
                FROM items i WHERE i.user_id=?{deleted_filter}
            """
            if item_id:
                sql += " AND i.id=?"; params.append(item_id)
            if search:
                sql += " AND (i.name LIKE ? OR COALESCE(i.barcode,'') LIKE ?)"; params.extend([f'%{search}%', f'%{search}%'])
            sql += " ORDER BY i.name LIMIT ?"; params.append(limit)
            rows=[]
            bom_table = 'bom' if 'bom' in tables else ('boms' if 'boms' in tables else None)
            bom_line_table = 'bom_lines' if 'bom_lines' in tables else None
            for r in db.execute(sql, tuple(params)).fetchall():
                d=dict(r)
                item_cost=Decimal(str(d.get('unit_cost') or 0))
                selling=Decimal(str(d.get('selling_price') or 0))
                components=0; bom_cost=Decimal('0')
                if bom_table and bom_line_table:
                    try:
                        brow=db.execute(f"""
                            SELECT COUNT(*) AS cnt,
                                   CAST(COALESCE(SUM(CAST(COALESCE(bl.base_qty, bl.quantity, 0) AS REAL) * CAST({unit_cost_expr} AS REAL)),0) AS TEXT) AS cost
                            FROM {bom_table} b
                            JOIN {bom_line_table} bl ON bl.bom_id = b.id
                            LEFT JOIN items i ON i.id = bl.item_id
                            WHERE b.product_id=?
                        """, (d.get('id'),)).fetchone()
                        if brow:
                            bd=dict(brow); components=int(bd.get('cnt') or 0); bom_cost=Decimal(str(bd.get('cost') or 0))
                    except Exception:
                        pass
                final_cost = bom_cost if bom_cost > 0 else item_cost
                margin = selling - final_cost
                rows.append({**d, 'components_count': components, 'bom_cost': bom_cost, 'final_cost': final_cost, 'margin': margin})
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

    def _accounting_tables(self):
        db, tables = self._db_tables()
        if not db:
            return db, tables, None, None, None
        entry_table = 'accounting_entries' if 'accounting_entries' in tables else ('journal_entries' if 'journal_entries' in tables else None)
        if 'accounting_entry_lines' in tables:
            line_table, join_col = 'accounting_entry_lines', 'entry_id'
        elif 'journal_entry_lines' in tables:
            line_table, join_col = 'journal_entry_lines', 'entry_id'
        elif 'journal_lines' in tables:
            line_table, join_col = 'journal_lines', 'journal_entry_id'
        else:
            line_table, join_col = None, None
        return db, tables, entry_table, line_table, join_col

    def _table_columns(self, db, table):
        try:
            return {str(r[1]).lower() for r in db.execute(f"PRAGMA table_info({table})").fetchall()}
        except Exception:
            return set()

    def _entry_expr(self, db, entry_table, alias, candidates, fallback="''"):
        cols = self._table_columns(db, entry_table) if db and entry_table else set()
        present = [f"{alias}.{col}" for col in candidates if col in cols]
        if not present:
            return fallback
        return present[0] if len(present) == 1 else 'COALESCE(' + ','.join(present) + ')'

    def _entry_date_expr(self, table_alias='e'):
        return f"COALESCE({table_alias}.entry_date,{table_alias}.date,{table_alias}.created_at)"

    def general_ledger_report(self, account_id: int | None = None,
                              start_date: str | None = None, end_date: str | None = None,
                              limit: int = 5000) -> List[Dict]:
        """General ledger by account with opening and running balance.

        Phase 282 supports both accounting_entry_lines.entry_id and the actual
        journal_lines.journal_entry_id schema. It never requires accounts.user_id.
        """
        try:
            from decimal import Decimal
            db, tables, entry_table, line_table, join_col = self._accounting_tables()
            if not db or not entry_table or not line_table or 'accounts' not in tables:
                return []
            date_expr = self._entry_expr(db, entry_table, 'e', ('entry_date', 'date', 'created_at'), 'e.id')
            account_filter = " AND l.account_id = ?" if account_id else ""
            opening = {}
            if start_date:
                params = []
                if account_id: params.append(account_id)
                params.append(start_date)
                sql = f"""
                    SELECT l.account_id, CAST(COALESCE(SUM(CAST(l.debit AS REAL)),0) AS TEXT) AS debit,
                           CAST(COALESCE(SUM(CAST(l.credit AS REAL)),0) AS TEXT) AS credit
                    FROM {line_table} l
                    JOIN {entry_table} e ON e.id = l.{join_col}
                    WHERE 1=1 {account_filter} AND date({date_expr}) < date(?)
                    GROUP BY l.account_id
                """
                for r in db.execute(sql, tuple(params)).fetchall():
                    d=dict(r); opening[d.get('account_id')] = Decimal(str(d.get('debit') or 0)) - Decimal(str(d.get('credit') or 0))
            params = []
            if account_id: params.append(account_id)
            date_filter = ""
            if start_date:
                date_filter += f" AND date({date_expr}) >= date(?)"; params.append(start_date)
            if end_date:
                date_filter += f" AND date({date_expr}) <= date(?)"; params.append(end_date)
            params.append(limit)
            sql = f"""
                SELECT e.id AS entry_id, {date_expr} AS entry_date,
                       {self._entry_expr(db, entry_table, 'e', ('reference', 'reference_no', 'entry_no', 'source_reference'), "''")} AS reference,
                       {self._entry_expr(db, entry_table, 'e', ('description', 'notes'), "''")} AS description,
                       l.account_id, COALESCE(a.code,'') AS account_code, COALESCE(a.name,'') AS account_name,
                       CAST(COALESCE(l.debit,0) AS TEXT) AS debit,
                       CAST(COALESCE(l.credit,0) AS TEXT) AS credit
                FROM {line_table} l
                JOIN {entry_table} e ON e.id = l.{join_col}
                LEFT JOIN accounts a ON a.id = l.account_id
                WHERE 1=1 {account_filter} {date_filter}
                ORDER BY l.account_id, date({date_expr}), e.id, l.id
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
        """Trial balance with movement and closing balances."""
        try:
            from decimal import Decimal
            db, tables, entry_table, line_table, join_col = self._accounting_tables()
            if not db or 'accounts' not in tables:
                return {'rows': [], 'total_debit': Decimal('0'), 'total_credit': Decimal('0'), 'balanced': True, 'difference': Decimal('0')}
            if not entry_table or not line_table:
                rows = self.trial_balance()
                td=sum((Decimal(str(r.get('debit') or r.get('debit_total') or 0)) for r in rows), Decimal('0'))
                tc=sum((Decimal(str(r.get('credit') or r.get('credit_total') or 0)) for r in rows), Decimal('0'))
                return {'rows': rows, 'total_debit': td, 'total_credit': tc, 'balanced': td == tc, 'difference': td - tc}
            date_expr = self._entry_expr(db, entry_table, 'e', ('entry_date', 'date', 'created_at'), 'e.id')
            params=[]
            date_filter=''
            if start_date:
                date_filter += f' AND date({date_expr}) >= date(?)'; params.append(start_date)
            if end_date:
                date_filter += f' AND date({date_expr}) <= date(?)'; params.append(end_date)
            sql=f"""
                SELECT a.id, COALESCE(a.code,'') AS code, COALESCE(a.name,'') AS account_name,
                       CAST(COALESCE(SUM(CAST(l.debit AS REAL)),0) AS TEXT) AS debit,
                       CAST(COALESCE(SUM(CAST(l.credit AS REAL)),0) AS TEXT) AS credit
                FROM accounts a
                LEFT JOIN {line_table} l ON l.account_id = a.id
                LEFT JOIN {entry_table} e ON e.id = l.{join_col} {date_filter}
                GROUP BY a.id
                HAVING CAST(debit AS REAL) <> 0 OR CAST(credit AS REAL) <> 0
                ORDER BY a.code, a.name
            """
            rows=[]; td=Decimal('0'); tc=Decimal('0')
            for r in db.execute(sql, tuple(params)).fetchall():
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
            balance_table = 'item_warehouse_balances' if 'item_warehouse_balances' in tables else ('warehouse_stock' if 'warehouse_stock' in tables else None)
            if kind == 'reorder':
                if balance_table:
                    qty_col = 'quantity' if balance_table == 'item_warehouse_balances' else 'quantity'
                    sql=f"""
                        SELECT i.id, i.name, COALESCE(i.barcode,'') AS barcode, COALESCE(w.name,'') AS warehouse_name,
                               CAST(COALESCE(ws.{qty_col},0) AS TEXT) AS quantity,
                               CAST(COALESCE(i.min_stock, i.reorder_level, 0) AS TEXT) AS min_stock
                        FROM items i
                        LEFT JOIN {balance_table} ws ON ws.item_id=i.id
                        LEFT JOIN warehouses w ON w.id=ws.warehouse_id
                        WHERE i.user_id=? AND CAST(COALESCE(ws.{qty_col},0) AS REAL) <= CAST(COALESCE(i.min_stock, i.reorder_level, 0) AS REAL)
                          AND CAST(COALESCE(i.min_stock, i.reorder_level, 0) AS REAL) > 0
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
                date_filter=''; params=[]
                if start_date: date_filter+=' AND date(inv.date) >= date(?)'; params.append(start_date)
                if end_date: date_filter+=' AND date(inv.date) <= date(?)'; params.append(end_date)
                eff_branch = self._effective_branch_id(branch_id)
                if eff_branch: date_filter+=' AND inv.branch_id = ?'; params.append(eff_branch)
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
                exec_params = params + [uid]
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
                        except Exception:
                            days_without=None
                    rows.append({**d, 'qty': qty, 'sales_value': sales, 'cost_value': cost, 'profit': profit, 'days_without_movement': days_without})
            return rows
        except Exception:
            return []

    def is_remote(self) -> bool:
        return False
