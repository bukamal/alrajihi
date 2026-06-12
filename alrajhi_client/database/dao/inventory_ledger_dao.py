# -*- coding: utf-8 -*-
"""Append-only inventory ledger DAO.

Phase 22 introduces this DAO as a non-destructive parallel ledger. It does not
replace legacy inventory_movements or item_warehouse_balances yet.
"""
from __future__ import annotations

from decimal import Decimal
import datetime

from auth.session import UserSession
from database.connection import DatabaseConnection


class InventoryLedgerDAO:
    def __init__(self):
        self.db = DatabaseConnection()

    def list_entries(self, item_id=None, warehouse_id=None, reference_type=None, reference_id=None, limit=200):
        uid = UserSession.get_current_user_id()
        sql = ["SELECT * FROM inventory_ledger WHERE user_id = ?"]
        params = [uid]
        if item_id is not None:
            sql.append("AND item_id = ?")
            params.append(item_id)
        if warehouse_id is not None:
            sql.append("AND warehouse_id = ?")
            params.append(warehouse_id)
        if reference_type is not None:
            sql.append("AND reference_type = ?")
            params.append(reference_type)
        if reference_id is not None:
            sql.append("AND reference_id = ?")
            params.append(reference_id)
        sql.append("ORDER BY movement_date DESC, id DESC LIMIT ?")
        params.append(int(limit or 200))
        rows = self.db.execute(" ".join(sql), tuple(params)).fetchall()
        return [self._normalize(dict(row)) for row in rows]

    def record_entry(self, item_id, movement_type, direction, quantity, unit_cost=None,
                     warehouse_id=None, reference_type=None, reference_id=None,
                     source_table=None, source_id=None, notes=None, movement_date=None):
        uid = UserSession.get_current_user_id()
        if not uid:
            return None
        if direction not in {'in', 'out', 'neutral'}:
            raise ValueError("direction must be one of: in, out, neutral")
        qty = Decimal(str(quantity or '0'))
        cost = Decimal(str(unit_cost or '0'))
        total_cost = qty * cost if unit_cost is not None else None
        now = movement_date or datetime.datetime.now().isoformat()
        cur = self.db.execute("""
            INSERT INTO inventory_ledger (
                user_id, item_id, warehouse_id, movement_type, direction, quantity,
                unit_cost, total_cost, reference_type, reference_id, source_table,
                source_id, notes, movement_date
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            uid, item_id, warehouse_id, movement_type, direction, str(qty),
            str(cost) if unit_cost is not None else None,
            str(total_cost) if total_cost is not None else None,
            reference_type, reference_id, source_table, source_id, notes, now
        ))
        self.db.commit()
        return cur.lastrowid if hasattr(cur, 'lastrowid') else None

    def item_balance_from_ledger(self, item_id, warehouse_id=None):
        uid = UserSession.get_current_user_id()
        sql = ["""SELECT SUM(CASE
                    WHEN direction='in' THEN CAST(quantity AS REAL)
                    WHEN direction='out' THEN -CAST(quantity AS REAL)
                    ELSE 0 END) AS qty
               FROM inventory_ledger
               WHERE user_id=? AND item_id=?"""]
        params = [uid, item_id]
        if warehouse_id is not None:
            sql.append("AND warehouse_id=?")
            params.append(warehouse_id)
        row = self.db.execute(" ".join(sql), tuple(params)).fetchone()
        return Decimal(str(row[0])) if row and row[0] is not None else Decimal('0')

    def _normalize(self, row):
        for key in ('quantity', 'unit_cost', 'total_cost'):
            if key in row and row[key] not in (None, ''):
                row[key] = Decimal(str(row[key]))
        return row


inventory_ledger_dao = InventoryLedgerDAO()
