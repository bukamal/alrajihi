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


    def _ensure_schema(self):
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS inventory_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                warehouse_id INTEGER,
                movement_type TEXT NOT NULL,
                direction TEXT NOT NULL CHECK(direction IN ('in','out','neutral')),
                quantity TEXT NOT NULL,
                unit_cost TEXT,
                total_cost TEXT,
                reference_type TEXT,
                reference_id INTEGER,
                source_table TEXT,
                source_id INTEGER,
                notes TEXT,
                movement_date TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        try:
            self.db.execute("CREATE INDEX IF NOT EXISTS idx_inventory_ledger_ref ON inventory_ledger(reference_type, reference_id)")
            self.db.execute("CREATE INDEX IF NOT EXISTS idx_inventory_ledger_item_date ON inventory_ledger(item_id, movement_date)")
        except Exception:
            pass
        self.db.commit()

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
        self._ensure_schema()
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


    def reconciliation_report(self, item_id=None, warehouse_id=None, tolerance='0'):
        """Diagnostic-only comparison between operational stock and shadow ledger.

        Returns mismatches for two scopes:
        - item: items.quantity versus all ledger entries for the item.
        - warehouse: item_warehouse_balances.quantity versus ledger entries for
          the same item/warehouse.
        """
        uid = UserSession.get_current_user_id()
        tol = Decimal(str(tolerance or '0'))
        mismatches = []
        checked = 0

        def dec(value):
            return Decimal(str(value if value not in (None, '') else '0'))

        item_sql = ["""
            SELECT i.id AS item_id, i.name AS item_name,
                   CAST(COALESCE(i.quantity, '0') AS REAL) AS operational_quantity,
                   COALESCE(SUM(CASE
                       WHEN l.direction='in' THEN CAST(l.quantity AS REAL)
                       WHEN l.direction='out' THEN -CAST(l.quantity AS REAL)
                       ELSE 0 END), 0) AS ledger_quantity
            FROM items i
            LEFT JOIN inventory_ledger l ON l.user_id=i.user_id AND l.item_id=i.id
            WHERE i.user_id=? AND i.deleted_at IS NULL
        """]
        params = [uid]
        if item_id is not None:
            item_sql.append("AND i.id=?")
            params.append(item_id)
        item_sql.append("GROUP BY i.id, i.name, i.quantity ORDER BY i.name")
        for row in self.db.execute(' '.join(item_sql), tuple(params)).fetchall():
            checked += 1
            op = dec(row['operational_quantity'])
            led = dec(row['ledger_quantity'])
            diff = op - led
            if abs(diff) > tol:
                mismatches.append({
                    'scope': 'item',
                    'item_id': row['item_id'],
                    'item_name': row['item_name'],
                    'warehouse_id': None,
                    'warehouse_name': None,
                    'operational_quantity': str(op),
                    'ledger_quantity': str(led),
                    'difference': str(diff),
                })

        wh_sql = ["""
            SELECT b.item_id, i.name AS item_name, b.warehouse_id, w.name AS warehouse_name,
                   CAST(COALESCE(b.quantity, '0') AS REAL) AS operational_quantity,
                   COALESCE(SUM(CASE
                       WHEN l.direction='in' THEN CAST(l.quantity AS REAL)
                       WHEN l.direction='out' THEN -CAST(l.quantity AS REAL)
                       ELSE 0 END), 0) AS ledger_quantity
            FROM item_warehouse_balances b
            JOIN items i ON i.id=b.item_id AND i.user_id=b.user_id
            JOIN warehouses w ON w.id=b.warehouse_id AND w.user_id=b.user_id
            LEFT JOIN inventory_ledger l ON l.user_id=b.user_id AND l.item_id=b.item_id AND l.warehouse_id=b.warehouse_id
            WHERE b.user_id=?
        """]
        params = [uid]
        if item_id is not None:
            wh_sql.append("AND b.item_id=?")
            params.append(item_id)
        if warehouse_id is not None:
            wh_sql.append("AND b.warehouse_id=?")
            params.append(warehouse_id)
        wh_sql.append("GROUP BY b.item_id, i.name, b.warehouse_id, w.name, b.quantity ORDER BY i.name, w.name")
        for row in self.db.execute(' '.join(wh_sql), tuple(params)).fetchall():
            checked += 1
            op = dec(row['operational_quantity'])
            led = dec(row['ledger_quantity'])
            diff = op - led
            if abs(diff) > tol:
                mismatches.append({
                    'scope': 'warehouse',
                    'item_id': row['item_id'],
                    'item_name': row['item_name'],
                    'warehouse_id': row['warehouse_id'],
                    'warehouse_name': row['warehouse_name'],
                    'operational_quantity': str(op),
                    'ledger_quantity': str(led),
                    'difference': str(diff),
                })

        return {
            'checked': checked,
            'mismatch_count': len(mismatches),
            'mismatches': mismatches,
            'diagnostic_only': True,
            'note': 'Phase 27 compares operational stock with the shadow ledger; it does not change stock.',
        }


    def dual_read_report(self, item_id=None, warehouse_id=None, tolerance='0', include_matches=True):
        """Dual-read operational stock and shadow ledger balances.

        Phase 31 diagnostic-only. It returns both values side by side and never
        changes stock quantities. This is a preparatory step before any future
        authoritative-ledger switch.
        """
        uid = UserSession.get_current_user_id()
        tol = Decimal(str(tolerance or '0'))
        include_matches = bool(include_matches)

        def dec(value):
            return Decimal(str(value if value not in (None, '') else '0'))

        rows = []
        checked = matched = mismatched = 0

        item_sql = ["""
            SELECT i.id AS item_id, i.name AS item_name,
                   CAST(COALESCE(i.quantity, '0') AS REAL) AS operational_quantity,
                   COALESCE(SUM(CASE
                       WHEN l.direction='in' THEN CAST(l.quantity AS REAL)
                       WHEN l.direction='out' THEN -CAST(l.quantity AS REAL)
                       ELSE 0 END), 0) AS ledger_quantity
            FROM items i
            LEFT JOIN inventory_ledger l ON l.user_id=i.user_id AND l.item_id=i.id
            WHERE i.user_id=? AND i.deleted_at IS NULL
        """]
        params = [uid]
        if item_id is not None:
            item_sql.append("AND i.id=?")
            params.append(item_id)
        item_sql.append("GROUP BY i.id, i.name, i.quantity ORDER BY i.name")
        for row in self.db.execute(' '.join(item_sql), tuple(params)).fetchall():
            checked += 1
            op = dec(row['operational_quantity'])
            led = dec(row['ledger_quantity'])
            diff = op - led
            ok = abs(diff) <= tol
            matched += 1 if ok else 0
            mismatched += 0 if ok else 1
            if include_matches or not ok:
                rows.append({
                    'scope': 'item',
                    'item_id': row['item_id'],
                    'item_name': row['item_name'],
                    'warehouse_id': None,
                    'warehouse_name': None,
                    'operational_quantity': str(op),
                    'ledger_quantity': str(led),
                    'difference': str(diff),
                    'matches': ok,
                    'read_source': 'dual',
                })

        wh_sql = ["""
            SELECT b.item_id, i.name AS item_name, b.warehouse_id, w.name AS warehouse_name,
                   CAST(COALESCE(b.quantity, '0') AS REAL) AS operational_quantity,
                   COALESCE(SUM(CASE
                       WHEN l.direction='in' THEN CAST(l.quantity AS REAL)
                       WHEN l.direction='out' THEN -CAST(l.quantity AS REAL)
                       ELSE 0 END), 0) AS ledger_quantity
            FROM item_warehouse_balances b
            JOIN items i ON i.id=b.item_id AND i.user_id=b.user_id
            JOIN warehouses w ON w.id=b.warehouse_id AND w.user_id=b.user_id
            LEFT JOIN inventory_ledger l ON l.user_id=b.user_id AND l.item_id=b.item_id AND l.warehouse_id=b.warehouse_id
            WHERE b.user_id=?
        """]
        params = [uid]
        if item_id is not None:
            wh_sql.append("AND b.item_id=?")
            params.append(item_id)
        if warehouse_id is not None:
            wh_sql.append("AND b.warehouse_id=?")
            params.append(warehouse_id)
        wh_sql.append("GROUP BY b.item_id, i.name, b.warehouse_id, w.name, b.quantity ORDER BY i.name, w.name")
        for row in self.db.execute(' '.join(wh_sql), tuple(params)).fetchall():
            checked += 1
            op = dec(row['operational_quantity'])
            led = dec(row['ledger_quantity'])
            diff = op - led
            ok = abs(diff) <= tol
            matched += 1 if ok else 0
            mismatched += 0 if ok else 1
            if include_matches or not ok:
                rows.append({
                    'scope': 'warehouse',
                    'item_id': row['item_id'],
                    'item_name': row['item_name'],
                    'warehouse_id': row['warehouse_id'],
                    'warehouse_name': row['warehouse_name'],
                    'operational_quantity': str(op),
                    'ledger_quantity': str(led),
                    'difference': str(diff),
                    'matches': ok,
                    'read_source': 'dual',
                })

        return {
            'mode': 'dual_read',
            'authoritative_source': 'operational_stock',
            'ledger_authoritative': False,
            'checked': checked,
            'matched': matched,
            'mismatched': mismatched,
            'rows': rows,
            'diagnostic_only': True,
            'note': 'Phase 31 reads operational stock and ledger balances side by side; it does not change stock.',
        }


    def backfill_from_inventory_movements(self, dry_run=True, item_id=None, clear_existing=False):
        """Backfill shadow ledger from legacy inventory_movements.

        Phase 28 is migration-preparation only. It creates item-level ledger rows
        with warehouse_id=NULL and source_table='inventory_movements'. The method
        is idempotent by default: existing ledger rows for the same source row are
        skipped unless clear_existing=True is explicitly requested.
        """
        uid = UserSession.get_current_user_id()
        if not uid:
            return {'dry_run': bool(dry_run), 'inserted': 0, 'skipped': 0, 'scanned': 0, 'source': 'inventory_movements'}
        if clear_existing and not dry_run:
            sql = "DELETE FROM inventory_ledger WHERE user_id=? AND source_table='inventory_movements'"
            params = [uid]
            if item_id is not None:
                sql += " AND item_id=?"
                params.append(item_id)
            self.db.execute(sql, tuple(params))
        sql = ["""
            SELECT id, item_id, movement_type, quantity, unit_cost, reference_id, movement_date
            FROM inventory_movements
            WHERE user_id=?
        """]
        params = [uid]
        if item_id is not None:
            sql.append("AND item_id=?")
            params.append(item_id)
        sql.append("ORDER BY id")
        rows = self.db.execute(' '.join(sql), tuple(params)).fetchall()
        scanned = inserted = skipped = 0
        preview = []
        for row in rows:
            scanned += 1
            source_id = row['id']
            exists = self.db.execute(
                """SELECT id FROM inventory_ledger
                   WHERE user_id=? AND source_table='inventory_movements' AND source_id=? LIMIT 1""",
                (uid, source_id)
            ).fetchone()
            if exists:
                skipped += 1
                continue
            movement_type = row['movement_type']
            direction = 'in' if movement_type in ('opening','purchase','adjustment','production_out','sales_return','consumption_reverse') else 'out' if movement_type in ('sale','production_consume','purchase_return') else 'neutral'
            payload = {
                'item_id': row['item_id'],
                'movement_type': f'legacy_{movement_type}',
                'direction': direction,
                'quantity': str(row['quantity'] or '0'),
                'unit_cost': row['unit_cost'],
                'warehouse_id': None,
                'reference_type': movement_type,
                'reference_id': row['reference_id'],
                'source_table': 'inventory_movements',
                'source_id': source_id,
                'notes': 'Phase 28 legacy inventory movement backfill',
                'movement_date': row['movement_date'],
            }
            if dry_run:
                if len(preview) < 20:
                    preview.append(payload)
            else:
                self.record_entry(**payload)
            inserted += 1
        if not dry_run:
            self.db.commit()
        return {
            'dry_run': bool(dry_run),
            'source': 'inventory_movements',
            'scanned': scanned,
            'inserted': inserted,
            'skipped': skipped,
            'preview': preview,
            'destructive': False,
            'note': 'Phase 28 backfills item-level shadow ledger rows only; it does not change stock quantities.',
        }



    def backfill_from_warehouse_movements(self, dry_run=True, item_id=None, warehouse_id=None, clear_existing=False):
        """Backfill warehouse-level shadow ledger from legacy warehouse_movements.

        Phase 29 is migration-preparation only. It creates warehouse-level ledger
        rows with source_table='warehouse_movements'. Quantities in
        warehouse_movements are signed, so ledger stores the absolute quantity
        and derives direction from the sign.
        """
        uid = UserSession.get_current_user_id()
        if not uid:
            return {'dry_run': bool(dry_run), 'inserted': 0, 'skipped': 0, 'scanned': 0, 'source': 'warehouse_movements'}
        if clear_existing and not dry_run:
            sql = "DELETE FROM inventory_ledger WHERE user_id=? AND source_table='warehouse_movements'"
            params = [uid]
            if item_id is not None:
                sql += " AND item_id=?"
                params.append(item_id)
            if warehouse_id is not None:
                sql += " AND warehouse_id=?"
                params.append(warehouse_id)
            self.db.execute(sql, tuple(params))
        sql = ["""
            SELECT id, item_id, warehouse_id, movement_type, quantity, unit_cost,
                   reference_type, reference_id, notes, movement_date
            FROM warehouse_movements
            WHERE user_id=?
        """]
        params = [uid]
        if item_id is not None:
            sql.append("AND item_id=?")
            params.append(item_id)
        if warehouse_id is not None:
            sql.append("AND warehouse_id=?")
            params.append(warehouse_id)
        sql.append("ORDER BY id")
        rows = self.db.execute(' '.join(sql), tuple(params)).fetchall()
        scanned = inserted = skipped = 0
        preview = []
        for row in rows:
            scanned += 1
            source_id = row['id']
            exists = self.db.execute(
                """SELECT id FROM inventory_ledger
                   WHERE user_id=? AND source_table='warehouse_movements' AND source_id=? LIMIT 1""",
                (uid, source_id)
            ).fetchone()
            if exists:
                skipped += 1
                continue
            qty = Decimal(str(row['quantity'] or '0'))
            if qty == 0:
                skipped += 1
                continue
            direction = 'in' if qty > 0 else 'out'
            movement_type = row['movement_type']
            payload = {
                'item_id': row['item_id'],
                'movement_type': f'legacy_warehouse_{movement_type}',
                'direction': direction,
                'quantity': str(abs(qty)),
                'unit_cost': row['unit_cost'],
                'warehouse_id': row['warehouse_id'],
                'reference_type': row['reference_type'] or movement_type,
                'reference_id': row['reference_id'],
                'source_table': 'warehouse_movements',
                'source_id': source_id,
                'notes': row['notes'] or 'Phase 29 legacy warehouse movement backfill',
                'movement_date': row['movement_date'],
            }
            if dry_run:
                if len(preview) < 20:
                    preview.append(payload)
            else:
                self.record_entry(**payload)
            inserted += 1
        if not dry_run:
            self.db.commit()
        return {
            'dry_run': bool(dry_run),
            'source': 'warehouse_movements',
            'scanned': scanned,
            'inserted': inserted,
            'skipped': skipped,
            'preview': preview,
            'destructive': False,
            'note': 'Phase 29 backfills warehouse-level shadow ledger rows only; it does not change stock quantities.',
        }

    def backfill_ledger(self, dry_run=True, item_id=None, warehouse_id=None,
                        clear_existing=False, include_item_movements=True,
                        include_warehouse_movements=True):
        """Run all supported non-destructive ledger backfills.

        Transfers are already represented by warehouse_movements as transfer_out /
        transfer_in rows, so this method does not create separate transfer rows
        from warehouse_transfers to avoid double posting.
        """
        results = []
        totals = {'scanned': 0, 'inserted': 0, 'skipped': 0}
        if include_item_movements:
            r = self.backfill_from_inventory_movements(
                dry_run=dry_run, item_id=item_id, clear_existing=clear_existing
            )
            results.append(r)
        if include_warehouse_movements:
            r = self.backfill_from_warehouse_movements(
                dry_run=dry_run, item_id=item_id, warehouse_id=warehouse_id,
                clear_existing=clear_existing
            )
            results.append(r)
        for r in results:
            for key in totals:
                totals[key] += int(r.get(key) or 0)
        return {
            'dry_run': bool(dry_run),
            'sources': [r.get('source') for r in results],
            'results': results,
            **totals,
            'destructive': False,
            'note': 'Phase 29 backfills item-level and warehouse-level shadow ledger rows only. Transfers are covered through warehouse_movements.',
        }


    def snapshot_balance(self, item_id=None, warehouse_id=None):
        """Return ledger aggregate balances without changing stock.

        Phase 30 diagnostic-only snapshot.  It is intentionally read-only and
        is used to decide whether the shadow ledger is ready to become the
        authoritative stock source in a later phase.
        """
        uid = UserSession.get_current_user_id()
        sql = ["""
            SELECT l.item_id, i.name AS item_name, l.warehouse_id, w.name AS warehouse_name,
                   SUM(CASE
                       WHEN l.direction='in' THEN CAST(l.quantity AS REAL)
                       WHEN l.direction='out' THEN -CAST(l.quantity AS REAL)
                       ELSE 0 END) AS ledger_quantity,
                   COUNT(*) AS entry_count
            FROM inventory_ledger l
            LEFT JOIN items i ON i.id=l.item_id AND i.user_id=l.user_id
            LEFT JOIN warehouses w ON w.id=l.warehouse_id AND w.user_id=l.user_id
            WHERE l.user_id=?
        """]
        params = [uid]
        if item_id is not None:
            sql.append("AND l.item_id=?")
            params.append(item_id)
        if warehouse_id is not None:
            sql.append("AND l.warehouse_id=?")
            params.append(warehouse_id)
        sql.append("GROUP BY l.item_id, i.name, l.warehouse_id, w.name ORDER BY i.name, w.name")
        rows = self.db.execute(' '.join(sql), tuple(params)).fetchall()
        return {
            'mode': 'snapshot',
            'authoritative_source': 'operational_stock',
            'ledger_authoritative': False,
            'rows': [
                {
                    'item_id': row['item_id'],
                    'item_name': row['item_name'],
                    'warehouse_id': row['warehouse_id'],
                    'warehouse_name': row['warehouse_name'],
                    'ledger_quantity': str(Decimal(str(row['ledger_quantity'] or '0'))),
                    'entry_count': int(row['entry_count'] or 0),
                }
                for row in rows
            ],
            'diagnostic_only': True,
            'note': 'Phase 30 ledger snapshot is read-only and does not change operational stock.',
        }

    def integrity_check(self, item_id=None, warehouse_id=None):
        """Run read-only integrity checks on the shadow inventory ledger."""
        uid = UserSession.get_current_user_id()
        params = [uid]
        filters = ["l.user_id=?"]
        if item_id is not None:
            filters.append("l.item_id=?")
            params.append(item_id)
        if warehouse_id is not None:
            filters.append("l.warehouse_id=?")
            params.append(warehouse_id)
        where = " AND ".join(filters)

        def one(sql, extra=()):
            row = self.db.execute(sql, tuple(params) + tuple(extra)).fetchone()
            return int(row[0] or 0) if row else 0

        invalid_direction = one(f"""
            SELECT COUNT(*) FROM inventory_ledger l
            WHERE {where} AND COALESCE(l.direction,'') NOT IN ('in','out','neutral')
        """)
        non_positive_quantity = one(f"""
            SELECT COUNT(*) FROM inventory_ledger l
            WHERE {where} AND CAST(COALESCE(l.quantity,'0') AS REAL) < 0
        """)
        orphan_items = one(f"""
            SELECT COUNT(*) FROM inventory_ledger l
            LEFT JOIN items i ON i.id=l.item_id AND i.user_id=l.user_id
            WHERE {where} AND i.id IS NULL
        """)
        orphan_warehouses = one(f"""
            SELECT COUNT(*) FROM inventory_ledger l
            LEFT JOIN warehouses w ON w.id=l.warehouse_id AND w.user_id=l.user_id
            WHERE {where} AND l.warehouse_id IS NOT NULL AND w.id IS NULL
        """)
        duplicate_sources = one(f"""
            SELECT COUNT(*) FROM (
                SELECT l.source_table, l.source_id, l.item_id, l.warehouse_id,
                       l.movement_type, l.direction, COUNT(*) AS cnt
                FROM inventory_ledger l
                WHERE {where} AND l.source_table IS NOT NULL AND l.source_id IS NOT NULL
                GROUP BY l.source_table, l.source_id, l.item_id, l.warehouse_id,
                         l.movement_type, l.direction
                HAVING cnt > 1
            ) x
        """)
        negative_balances = one(f"""
            SELECT COUNT(*) FROM (
                SELECT l.item_id, l.warehouse_id,
                       SUM(CASE WHEN l.direction='in' THEN CAST(l.quantity AS REAL)
                                WHEN l.direction='out' THEN -CAST(l.quantity AS REAL)
                                ELSE 0 END) AS bal
                FROM inventory_ledger l
                WHERE {where}
                GROUP BY l.item_id, l.warehouse_id
                HAVING bal < 0
            ) x
        """)

        issues = {
            'invalid_direction': invalid_direction,
            'negative_quantity_rows': non_positive_quantity,
            'orphan_items': orphan_items,
            'orphan_warehouses': orphan_warehouses,
            'duplicate_source_rows': duplicate_sources,
            'negative_ledger_balances': negative_balances,
        }
        issue_count = sum(issues.values())
        return {
            'mode': 'integrity_check',
            'ok': issue_count == 0,
            'issue_count': issue_count,
            'issues': issues,
            'diagnostic_only': True,
            'note': 'Phase 30 integrity check is read-only; it does not change stock or ledger rows.',
        }

    def health_report(self, item_id=None, warehouse_id=None, tolerance='0'):
        """Combined Phase 30 readiness report for shadow-ledger adoption."""
        integrity = self.integrity_check(item_id=item_id, warehouse_id=warehouse_id)
        reconciliation = self.reconciliation_report(item_id=item_id, warehouse_id=warehouse_id, tolerance=tolerance)
        snapshot = self.snapshot_balance(item_id=item_id, warehouse_id=warehouse_id)
        ready = bool(integrity.get('ok')) and int(reconciliation.get('mismatch_count') or 0) == 0
        return {
            'mode': 'health',
            'ready_for_authoritative_ledger': ready,
            'ledger_authoritative': False,
            'authoritative_source': 'operational_stock',
            'integrity': integrity,
            'reconciliation_summary': {
                'checked': reconciliation.get('checked', 0),
                'mismatch_count': reconciliation.get('mismatch_count', 0),
            },
            'snapshot_summary': {
                'rows': len(snapshot.get('rows', [])),
            },
            'diagnostic_only': True,
            'note': 'Phase 30 health report is a gate before any future authoritative-ledger switch.',
        }


    def readiness_gate(self, item_id=None, warehouse_id=None, tolerance='0'):
        """Return a conservative decision gate for switching inventory reads to ledger.

        Phase 33 is read-only. It combines health, dual-read and snapshot data
        into a single operational decision object. It never changes stock, never
        marks the ledger authoritative, and defaults to a hard block whenever
        any mismatch or integrity issue exists.
        """
        health = self.health_report(item_id=item_id, warehouse_id=warehouse_id, tolerance=tolerance)
        dual = self.dual_read_report(item_id=item_id, warehouse_id=warehouse_id, tolerance=tolerance, include_matches=False)
        snapshot = self.snapshot_balance(item_id=item_id, warehouse_id=warehouse_id)

        issue_count = int((health.get('integrity') or {}).get('issue_count') or 0)
        mismatch_count = int((health.get('reconciliation_summary') or {}).get('mismatch_count') or 0)
        dual_mismatched = int(dual.get('mismatched') or 0)
        checked = int(dual.get('checked') or 0)

        blockers = []
        warnings = []
        if issue_count:
            blockers.append('ledger_integrity_issues')
        if mismatch_count:
            blockers.append('operational_vs_ledger_mismatches')
        if dual_mismatched:
            blockers.append('dual_read_mismatches')
        if checked == 0:
            warnings.append('no_stock_rows_checked')
        if not snapshot.get('rows'):
            warnings.append('empty_ledger_snapshot')

        safe_for_dual_read = issue_count == 0
        safe_for_authoritative_read = issue_count == 0 and mismatch_count == 0 and dual_mismatched == 0 and checked > 0

        return {
            'mode': 'readiness_gate',
            'phase': 33,
            'authoritative_source': 'operational_stock',
            'ledger_authoritative': False,
            'safe_for_dual_read': safe_for_dual_read,
            'safe_for_authoritative_read': safe_for_authoritative_read,
            'recommendation': 'keep_operational_stock' if not safe_for_authoritative_read else 'eligible_for_controlled_ledger_read_trial',
            'blockers': blockers,
            'warnings': warnings,
            'summary': {
                'integrity_issue_count': issue_count,
                'reconciliation_mismatch_count': mismatch_count,
                'dual_read_checked': checked,
                'dual_read_mismatched': dual_mismatched,
                'snapshot_rows': len(snapshot.get('rows', [])),
            },
            'health': health,
            'dual_read_summary': {
                'checked': dual.get('checked', 0),
                'matched': dual.get('matched', 0),
                'mismatched': dual.get('mismatched', 0),
                'rows': dual.get('rows', []),
            },
            'diagnostic_only': True,
            'note': 'Phase 33 readiness gate is read-only. It does not switch inventory reads to ledger.',
        }



    def controlled_read_balance(self, item_id=None, warehouse_id=None, mode='operational', tolerance='0'):
        """Controlled read switch for Phase 34.

        The default and fallback source is operational stock.  Ledger balances
        are selected only in ledger_trial / ledger_authoritative modes and only
        when the Phase 33 readiness gate reports safe_for_authoritative_read.
        This method is read-only and never updates stock quantities.
        """
        requested_mode = (mode or 'operational').strip().lower()
        if requested_mode not in {'operational', 'dual', 'ledger_trial', 'ledger_authoritative'}:
            requested_mode = 'operational'
        readiness = self.readiness_gate(item_id=item_id, warehouse_id=warehouse_id, tolerance=tolerance)
        dual = self.dual_read_report(item_id=item_id, warehouse_id=warehouse_id, tolerance=tolerance, include_matches=True)
        safe = bool(readiness.get('safe_for_authoritative_read'))
        selected_source = 'ledger' if requested_mode in {'ledger_trial', 'ledger_authoritative'} and safe else 'operational_stock'
        rows = []
        for row in dual.get('rows', []):
            selected_qty = row.get('ledger_quantity') if selected_source == 'ledger' else row.get('operational_quantity')
            out = dict(row)
            out.update({
                'selected_quantity': selected_qty,
                'selected_source': selected_source,
                'requested_mode': requested_mode,
            })
            rows.append(out)
        return {
            'mode': 'controlled_read',
            'phase': 34,
            'requested_mode': requested_mode,
            'selected_source': selected_source,
            'ledger_selected': selected_source == 'ledger',
            'authoritative_source': selected_source,
            'ledger_authoritative': selected_source == 'ledger',
            'safe_for_ledger_read': safe,
            'fallback_reason': None if selected_source == 'ledger' else ('requested_operational' if requested_mode == 'operational' else 'readiness_gate_blocked'),
            'readiness_summary': readiness.get('summary', {}),
            'blockers': readiness.get('blockers', []),
            'warnings': readiness.get('warnings', []),
            'rows': rows,
            'read_only': True,
            'note': 'Phase 34 can select ledger for reads only when readiness allows it; operational stock remains the default fallback.',
        }

    def _normalize(self, row):
        for key in ('quantity', 'unit_cost', 'total_cost'):
            if key in row and row[key] not in (None, ''):
                row[key] = Decimal(str(row[key]))
        return row


inventory_ledger_dao = InventoryLedgerDAO()
