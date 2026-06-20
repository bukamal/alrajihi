from __future__ import annotations

import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from alrajhi_server.database.connection import get_db


class RestaurantRepository:
    """Restaurant vertical repository: tables, open sessions, order lines, and KOT.

    This module deliberately owns SQL for the restaurant vertical. HTTP/API layers
    call methods only, keeping SQL behind the repository boundary.
    """

    def ensure_schema(self) -> None:
        db = get_db()
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS restaurant_tables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                zone TEXT,
                seats INTEGER DEFAULT 4,
                status TEXT NOT NULL DEFAULT 'free',
                is_active INTEGER NOT NULL DEFAULT 1,
                branch_id INTEGER,
                created_at TEXT,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS restaurant_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id INTEGER NOT NULL,
                waiter_id TEXT,
                guests INTEGER DEFAULT 1,
                status TEXT NOT NULL DEFAULT 'open',
                opened_at TEXT NOT NULL,
                closed_at TEXT,
                invoice_id INTEGER,
                branch_id INTEGER,
                notes TEXT,
                FOREIGN KEY(table_id) REFERENCES restaurant_tables(id)
            );
            CREATE TABLE IF NOT EXISTS restaurant_order_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                item_id INTEGER,
                item_name TEXT,
                quantity TEXT DEFAULT '1',
                unit_price TEXT DEFAULT '0',
                unit_id INTEGER,
                unit TEXT,
                conversion_factor TEXT DEFAULT '1',
                base_qty TEXT DEFAULT '1',
                barcode_scope TEXT,
                matched_barcode TEXT,
                notes TEXT,
                kitchen_status TEXT DEFAULT 'new',
                created_at TEXT,
                FOREIGN KEY(session_id) REFERENCES restaurant_sessions(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS kitchen_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                branch_id INTEGER,
                status TEXT DEFAULT 'sent',
                sent_at TEXT NOT NULL,
                printed_at TEXT,
                notes TEXT,
                FOREIGN KEY(session_id) REFERENCES restaurant_sessions(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS kitchen_ticket_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                order_line_id INTEGER NOT NULL,
                item_name TEXT,
                quantity TEXT DEFAULT '1',
                notes TEXT,
                FOREIGN KEY(ticket_id) REFERENCES kitchen_tickets(id) ON DELETE CASCADE,
                FOREIGN KEY(order_line_id) REFERENCES restaurant_order_lines(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS restaurant_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                invoice_id INTEGER,
                branch_id INTEGER,
                amount TEXT NOT NULL DEFAULT '0',
                payment_method TEXT NOT NULL DEFAULT 'cash',
                status TEXT NOT NULL DEFAULT 'posted',
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES restaurant_sessions(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS restaurant_session_adjustments (
                session_id INTEGER PRIMARY KEY,
                discount_amount TEXT NOT NULL DEFAULT '0',
                service_charge_amount TEXT NOT NULL DEFAULT '0',
                tax_amount TEXT NOT NULL DEFAULT '0',
                notes TEXT,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES restaurant_sessions(id) ON DELETE CASCADE
            );
            """
        )
        for ddl in (
            "ALTER TABLE restaurant_order_lines ADD COLUMN unit_id INTEGER",
            "ALTER TABLE restaurant_order_lines ADD COLUMN unit TEXT",
            "ALTER TABLE restaurant_order_lines ADD COLUMN conversion_factor TEXT DEFAULT '1'",
            "ALTER TABLE restaurant_order_lines ADD COLUMN base_qty TEXT DEFAULT '1'",
            "ALTER TABLE restaurant_order_lines ADD COLUMN barcode_scope TEXT",
            "ALTER TABLE restaurant_order_lines ADD COLUMN matched_barcode TEXT",
            "ALTER TABLE restaurant_tables ADD COLUMN branch_id INTEGER",
            "ALTER TABLE restaurant_sessions ADD COLUMN branch_id INTEGER",
            "ALTER TABLE kitchen_tickets ADD COLUMN branch_id INTEGER",
            "ALTER TABLE restaurant_payments ADD COLUMN branch_id INTEGER",
        ):
            try:
                db.execute(ddl)
            except Exception:
                pass
        db.commit()

    def seed_default_tables_if_empty(self) -> None:
        """Persist default restaurant tables before first touch interaction.

        This prevents sessions from being opened against placeholder table ids
        that are not present in restaurant_tables when SQLite foreign keys are
        enabled.
        """
        db = get_db()
        count = db.execute("SELECT COUNT(*) AS c FROM restaurant_tables").fetchone()["c"]
        if int(count or 0) > 0:
            return
        now = datetime.datetime.now().isoformat(timespec="seconds")
        for index in range(1, 13):
            db.execute(
                "INSERT INTO restaurant_tables(name, zone, seats, status, is_active, created_at, updated_at) VALUES (?, ?, 4, 'free', 1, ?, ?)",
                (f"Table {index}", "Main", now, now),
            )
        for ddl in (
            "ALTER TABLE restaurant_order_lines ADD COLUMN unit_id INTEGER",
            "ALTER TABLE restaurant_order_lines ADD COLUMN unit TEXT",
            "ALTER TABLE restaurant_order_lines ADD COLUMN conversion_factor TEXT DEFAULT '1'",
            "ALTER TABLE restaurant_order_lines ADD COLUMN base_qty TEXT DEFAULT '1'",
            "ALTER TABLE restaurant_order_lines ADD COLUMN barcode_scope TEXT",
            "ALTER TABLE restaurant_order_lines ADD COLUMN matched_barcode TEXT",
        ):
            try:
                db.execute(ddl)
            except Exception:
                pass
        db.commit()

    def list_tables(self, include_inactive: bool = False) -> list[dict[str, Any]]:
        self.ensure_schema()
        self.seed_default_tables_if_empty()
        where = "" if include_inactive else "WHERE t.is_active=1"
        rows = get_db().execute(
            f"""
            SELECT t.*, s.id AS active_session_id, s.guests AS active_guests, s.opened_at AS active_opened_at
            FROM restaurant_tables t
            LEFT JOIN restaurant_sessions s ON s.table_id=t.id AND s.status='open'
            {where}
            ORDER BY COALESCE(t.zone, ''), t.id
            """
        ).fetchall()
        return [dict(row) for row in rows]

    def upsert_table(self, name: str, zone: str = "", seats: int = 4, table_id: int | None = None, branch_id: int | None = None) -> dict[str, Any]:
        self.ensure_schema()
        now = datetime.datetime.now().isoformat(timespec="seconds")
        db = get_db()
        seats = max(1, int(seats or 1))
        if table_id:
            db.execute(
                "UPDATE restaurant_tables SET name=?, zone=?, seats=?, branch_id=COALESCE(?, branch_id), updated_at=? WHERE id=?",
                (name, zone, seats, branch_id, now, int(table_id)),
            )
            new_id = int(table_id)
        else:
            cur = db.execute(
                "INSERT INTO restaurant_tables(name, zone, seats, status, is_active, branch_id, created_at, updated_at) VALUES (?, ?, ?, 'free', 1, ?, ?, ?)",
                (name, zone, seats, branch_id, now, now),
            )
            new_id = int(cur.lastrowid)
        db.commit()
        return self.get_table(new_id)

    def get_table(self, table_id: int) -> dict[str, Any]:
        self.ensure_schema()
        row = get_db().execute("SELECT * FROM restaurant_tables WHERE id=?", (int(table_id),)).fetchone()
        if not row:
            raise ValueError("Restaurant table not found")
        return dict(row)

    def open_table(self, table_id: int, waiter_id: str | None = None, guests: int = 1, notes: str = "", branch_id: int | None = None) -> dict[str, Any]:
        self.ensure_schema()
        db = get_db()
        table_id = int(table_id)
        table = db.execute("SELECT id, branch_id FROM restaurant_tables WHERE id=? AND is_active=1", (table_id,)).fetchone()
        if not table:
            raise ValueError("Restaurant table not found; refresh the table map and try again")
        existing = db.execute(
            "SELECT * FROM restaurant_sessions WHERE table_id=? AND status='open' LIMIT 1", (table_id,)
        ).fetchone()
        if existing:
            return dict(existing)
        now = datetime.datetime.now().isoformat(timespec="seconds")
        cur = db.execute(
            "INSERT INTO restaurant_sessions(table_id, waiter_id, guests, status, opened_at, branch_id, notes) VALUES (?, ?, ?, 'open', ?, ?, ?)",
            (table_id, waiter_id, max(1, int(guests or 1)), now, branch_id if branch_id is not None else table['branch_id'], notes or ""),
        )
        db.execute("UPDATE restaurant_tables SET status='occupied', updated_at=? WHERE id=?", (now, table_id))
        db.commit()
        return self.get_session(int(cur.lastrowid))

    def get_session(self, session_id: int) -> dict[str, Any]:
        self.ensure_schema()
        row = get_db().execute("""
            SELECT s.*, COALESCE(s.branch_id, t.branch_id) AS branch_id, t.name AS table_name
            FROM restaurant_sessions s
            LEFT JOIN restaurant_tables t ON t.id=s.table_id
            WHERE s.id=?
            """, (int(session_id),)).fetchone()
        if not row:
            raise ValueError("Restaurant session not found")
        return dict(row)


    def list_menu_items(self, search: str = "", category_id: int | None = None, limit: int = 48) -> list[dict[str, Any]]:
        """Return menu/product cards from the canonical ERP item catalog."""
        self.ensure_schema()
        db = get_db()
        limit = max(1, min(int(limit or 48), 96))
        where = ["COALESCE(deleted_at, '') = ''"]
        params: list[Any] = []
        if search:
            where.append("(LOWER(COALESCE(name, '')) LIKE LOWER(?) OR LOWER(COALESCE(barcode, '')) LIKE LOWER(?))")
            like = f"%{search}%"
            params.extend([like, like])
        if category_id is not None:
            where.append("category_id = ?")
            params.append(int(category_id))
        sql = f"""
            SELECT id, name, category_id, selling_price, unit, barcode, quantity
            FROM items
            WHERE {' AND '.join(where)}
            ORDER BY name COLLATE NOCASE
            LIMIT ?
        """
        params.append(limit)
        try:
            rows = db.execute(sql, params).fetchall()
        except Exception:
            return []
        return [dict(row) for row in rows]

    def add_order_line(
        self,
        session_id: int,
        item_id: int | None,
        item_name: str,
        quantity: Any = "1",
        unit_price: Any = "0",
        notes: str = "",
        unit_id: int | None = None,
        unit: str = "",
        conversion_factor: Any = "1",
        base_qty: Any | None = None,
        barcode_scope: str = "",
        matched_barcode: str = "",
    ) -> dict[str, Any]:
        self.ensure_waiter_workflow_schema()
        now = datetime.datetime.now().isoformat(timespec="seconds")
        cur = get_db().execute(
            """INSERT INTO restaurant_order_lines(
                session_id, item_id, item_name, quantity, unit_price, unit_id, unit,
                conversion_factor, base_qty, barcode_scope, matched_barcode,
                notes, kitchen_status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?)""",
            (
                int(session_id), item_id, item_name, str(quantity), str(unit_price),
                unit_id, unit or "", str(conversion_factor or "1"),
                str(base_qty if base_qty not in (None, "") else quantity),
                barcode_scope or "", matched_barcode or "", notes or "", now,
            ),
        )
        get_db().execute("UPDATE restaurant_sessions SET modification_count=COALESCE(modification_count, 0)+1, last_activity_at=? WHERE id=?", (now, int(session_id)))
        get_db().execute("INSERT INTO restaurant_service_events(session_id, event_type, line_id, notes, created_at) VALUES (?, 'order_line_added', ?, ?, ?)", (int(session_id), int(cur.lastrowid), notes or "", now))
        get_db().commit()
        return self.get_order_line(int(cur.lastrowid))

    def get_order_line(self, line_id: int) -> dict[str, Any]:
        self.ensure_schema()
        row = get_db().execute("SELECT * FROM restaurant_order_lines WHERE id=?", (int(line_id),)).fetchone()
        if not row:
            raise ValueError("Restaurant order line not found")
        return dict(row)

    def list_session_lines(self, session_id: int) -> list[dict[str, Any]]:
        self.ensure_schema()
        rows = get_db().execute(
            "SELECT * FROM restaurant_order_lines WHERE session_id=? ORDER BY id", (int(session_id),)
        ).fetchall()
        return [dict(row) for row in rows]

    def send_to_kitchen(self, session_id: int, notes: str = "") -> dict[str, Any]:
        self.ensure_kitchen_station_schema()
        db = get_db()
        session_id = int(session_id)
        raw_lines = db.execute("SELECT * FROM restaurant_order_lines WHERE session_id=? AND kitchen_status='new' ORDER BY id", (session_id,)).fetchall()
        if not raw_lines:
            return {"tickets": [], "ticket": None, "lines": [], "message": "no_new_lines"}
        lines = [dict(row) for row in raw_lines]
        grouped: dict[int | None, list[dict[str, Any]]] = {}
        station_payloads: dict[int | None, dict[str, Any]] = {}
        for line in lines:
            station = self.station_for_order_line(line)
            station_id = station.get("id")
            grouped.setdefault(station_id, []).append(line)
            station_payloads[station_id] = station
        now = datetime.datetime.now().isoformat(timespec="seconds")
        tickets = []
        for station_id, station_lines in grouped.items():
            cur = db.execute(
                "INSERT INTO kitchen_tickets(session_id, station_id, branch_id, status, sent_at, notes) VALUES (?, ?, (SELECT branch_id FROM restaurant_sessions WHERE id=?), 'sent', ?, ?)",
                (session_id, station_id, session_id, now, notes or ""),
            )
            ticket_id = int(cur.lastrowid)
            for line in station_lines:
                db.execute(
                    "INSERT INTO kitchen_ticket_lines(ticket_id, order_line_id, station_id, item_name, quantity, notes) VALUES (?, ?, ?, ?, ?, ?)",
                    (ticket_id, int(line["id"]), station_id, line.get("item_name"), line.get("quantity"), line.get("notes")),
                )
                db.execute("UPDATE restaurant_order_lines SET kitchen_station_id=?, kitchen_status='sent' WHERE id=?", (station_id, int(line["id"])))
            ticket = db.execute("SELECT * FROM kitchen_tickets WHERE id=?", (ticket_id,)).fetchone()
            payload = dict(ticket) if ticket else {}
            payload["station"] = station_payloads.get(station_id)
            payload["line_count"] = len(station_lines)
            tickets.append(payload)
        db.commit()
        return {"tickets": tickets, "ticket": tickets[0] if tickets else None, "lines": lines}


    def get_ticket(self, ticket_id: int) -> dict[str, Any]:
        self.ensure_schema()
        row = get_db().execute("SELECT * FROM kitchen_tickets WHERE id=?", (int(ticket_id),)).fetchone()
        if not row:
            raise ValueError("Kitchen ticket not found")
        return dict(row)


    def status_counts(self, session_id: int) -> dict[str, int]:
        self.ensure_schema()
        rows = get_db().execute(
            "SELECT kitchen_status, COUNT(*) AS c FROM restaurant_order_lines WHERE session_id=? GROUP BY kitchen_status",
            (int(session_id),),
        ).fetchall()
        return {str(row["kitchen_status"] or "new"): int(row["c"] or 0) for row in rows}

    def update_line_status(self, line_id: int, status: str) -> dict[str, Any]:
        self.ensure_schema()
        allowed = {"new", "sent", "preparing", "ready", "served", "cancelled"}
        status = str(status or "").strip().lower()
        if status not in allowed:
            raise ValueError("Invalid restaurant line status")
        line = self.get_order_line(int(line_id))
        db = get_db()
        db.execute("UPDATE restaurant_order_lines SET kitchen_status=? WHERE id=?", (status, int(line_id)))
        if status == "cancelled":
            session = self.get_session(int(line["session_id"]))
            now_event = datetime.datetime.now().isoformat(timespec="seconds")
            db.execute("UPDATE restaurant_tables SET status='occupied', updated_at=? WHERE id=?", (now_event, int(session["table_id"])))
            db.execute("UPDATE restaurant_sessions SET cancelled_line_count=COALESCE(cancelled_line_count, 0)+1, modification_count=COALESCE(modification_count, 0)+1, last_activity_at=? WHERE id=?", (now_event, int(line["session_id"])))
            db.execute("INSERT INTO restaurant_service_events(session_id, event_type, line_id, notes, created_at) VALUES (?, 'line_cancelled', ?, '', ?)", (int(line["session_id"]), int(line_id), now_event))
        db.commit()
        return self.get_order_line(int(line_id))

    def mark_payment_pending(self, session_id: int) -> dict[str, Any]:
        self.ensure_schema()
        db = get_db()
        session = self.get_session(int(session_id))
        if session.get("status") != "open":
            raise ValueError("Restaurant session is not open")
        counts = self.status_counts(int(session_id))
        if sum(counts.values()) <= 0:
            raise ValueError("Cannot request payment for an empty table")
        if counts.get("new", 0) > 0:
            raise ValueError("Send new order lines to kitchen before requesting payment")
        now = datetime.datetime.now().isoformat(timespec="seconds")
        db.execute("UPDATE restaurant_tables SET status='payment', updated_at=? WHERE id=?", (now, int(session["table_id"])))
        db.commit()
        payload = self.get_session(int(session_id))
        payload["payment_pending"] = True
        return payload


    def decimal_value(self, value: Any, default: str = "0") -> Decimal:
        try:
            return Decimal(str(value if value not in (None, "") else default))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal(default)

    def next_restaurant_reference(self) -> str:
        db = get_db()
        prefix = "RST-"
        row = db.execute("SELECT MAX(reference) AS ref FROM invoices WHERE reference LIKE ?", (prefix + "%",)).fetchone()
        ref = row["ref"] if row else None
        try:
            import re
            match = re.search(r"(\d+)$", str(ref or ""))
            number = int(match.group(1)) + 1 if match else 1
        except Exception:
            number = 1
        return f"{prefix}{number:05d}"



    def get_session_adjustments(self, session_id: int) -> dict[str, Any]:
        self.ensure_schema()
        row = get_db().execute(
            "SELECT * FROM restaurant_session_adjustments WHERE session_id=?",
            (int(session_id),),
        ).fetchone()
        if not row:
            return {
                "session_id": int(session_id),
                "discount_amount": "0",
                "service_charge_amount": "0",
                "tax_amount": "0",
                "notes": "",
            }
        return dict(row)

    def set_session_adjustments(self, session_id: int, discount_amount: Any = "0", service_charge_amount: Any = "0", tax_amount: Any = "0", notes: str = "") -> dict[str, Any]:
        self.ensure_schema()
        session = self.get_session(int(session_id))
        if session.get("status") != "open":
            raise ValueError("Restaurant session is not open")
        discount = self.decimal_value(discount_amount, "0")
        service_charge = self.decimal_value(service_charge_amount, "0")
        tax = self.decimal_value(tax_amount, "0")
        if min(discount, service_charge, tax) < Decimal("0"):
            raise ValueError("Restaurant adjustments cannot be negative")
        subtotal = self.session_subtotal(int(session_id))
        if discount > subtotal:
            discount = subtotal
        now = datetime.datetime.now().isoformat(timespec="seconds")
        get_db().execute(
            """
            INSERT INTO restaurant_session_adjustments(session_id, discount_amount, service_charge_amount, tax_amount, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                discount_amount=excluded.discount_amount,
                service_charge_amount=excluded.service_charge_amount,
                tax_amount=excluded.tax_amount,
                notes=excluded.notes,
                updated_at=excluded.updated_at
            """,
            (int(session_id), str(discount), str(service_charge), str(tax), notes or "", now),
        )
        get_db().commit()
        return self.session_balance(int(session_id))

    def session_subtotal(self, session_id: int) -> Decimal:
        billable = [line for line in self.list_session_lines(int(session_id)) if (line.get("kitchen_status") or "new") != "cancelled"]
        return sum((self.decimal_value(line.get("quantity"), "0") * self.decimal_value(line.get("unit_price"), "0") for line in billable), Decimal("0"))

    def session_total(self, session_id: int) -> Decimal:
        subtotal = self.session_subtotal(int(session_id))
        adjustments = self.get_session_adjustments(int(session_id))
        discount = self.decimal_value(adjustments.get("discount_amount"), "0")
        service_charge = self.decimal_value(adjustments.get("service_charge_amount"), "0")
        tax = self.decimal_value(adjustments.get("tax_amount"), "0")
        total = subtotal - discount + service_charge + tax
        return total if total > Decimal("0") else Decimal("0")

    def session_paid(self, session_id: int) -> Decimal:
        self.ensure_schema()
        rows = get_db().execute(
            "SELECT amount FROM restaurant_payments WHERE session_id=? AND status='posted'",
            (int(session_id),),
        ).fetchall()
        return sum((self.decimal_value(row["amount"], "0") for row in rows), Decimal("0"))

    def session_balance(self, session_id: int) -> dict[str, Any]:
        self.ensure_schema()
        session = self.get_session(int(session_id))
        total = self.session_total(int(session_id))
        paid = self.session_paid(int(session_id))
        remaining = total - paid
        if remaining < Decimal("0"):
            remaining = Decimal("0")
        payments = get_db().execute(
            "SELECT * FROM restaurant_payments WHERE session_id=? ORDER BY id",
            (int(session_id),),
        ).fetchall()
        adjustments = self.get_session_adjustments(int(session_id))
        subtotal = self.session_subtotal(int(session_id))
        return {
            "session_id": int(session_id),
            "table_id": session.get("table_id"),
            "table_name": session.get("table_name"),
            "subtotal": str(subtotal),
            "discount_amount": str(self.decimal_value(adjustments.get("discount_amount"), "0")),
            "service_charge_amount": str(self.decimal_value(adjustments.get("service_charge_amount"), "0")),
            "tax_amount": str(self.decimal_value(adjustments.get("tax_amount"), "0")),
            "adjustment_notes": adjustments.get("notes") or "",
            "total": str(total),
            "paid": str(paid),
            "remaining": str(remaining),
            "is_fully_paid": paid >= total and total > Decimal("0"),
            "payments": [dict(row) for row in payments],
        }

    def record_payment(self, session_id: int, amount: Any, payment_method: str = "cash", notes: str = "") -> dict[str, Any]:
        self.ensure_schema()
        db = get_db()
        session = self.get_session(int(session_id))
        if session.get("status") != "open":
            raise ValueError("Restaurant session is not open")
        counts = self.status_counts(int(session_id))
        if sum(counts.values()) <= 0:
            raise ValueError("Cannot record payment for an empty table")
        if counts.get("new", 0) > 0:
            raise ValueError("Send new order lines to kitchen before recording payment")
        amount_value = self.decimal_value(amount, "0")
        if amount_value <= Decimal("0"):
            raise ValueError("Payment amount must be greater than zero")
        balance = self.session_balance(int(session_id))
        remaining = self.decimal_value(balance.get("remaining"), "0")
        if amount_value > remaining:
            amount_value = remaining
        if amount_value <= Decimal("0"):
            raise ValueError("Restaurant session is already fully paid")
        now = datetime.datetime.now().isoformat(timespec="seconds")
        cur = db.execute(
            "INSERT INTO restaurant_payments(session_id, invoice_id, branch_id, amount, payment_method, status, notes, created_at) VALUES (?, NULL, (SELECT branch_id FROM restaurant_sessions WHERE id=?), ?, ?, 'posted', ?, ?)",
            (int(session_id), int(session_id), str(amount_value), payment_method or "cash", notes or "", now),
        )
        db.execute("UPDATE restaurant_tables SET status='payment', updated_at=? WHERE id=?", (now, int(session["table_id"])))
        db.commit()
        payload = self.session_balance(int(session_id))
        payload["payment_id"] = int(cur.lastrowid)
        return payload

    def checkout_session(self, session_id: int, user_id: str, paid_amount: Any | None = None, payment_method: str = "cash") -> dict[str, Any]:
        """Create a posted sales invoice from a restaurant session and close it."""
        self.ensure_schema()
        db = get_db()
        session = self.get_session(int(session_id))
        if session.get("status") != "open":
            raise ValueError("Restaurant session is not open")
        counts = self.status_counts(int(session_id))
        if counts.get("new", 0) > 0:
            raise ValueError("Send new order lines to kitchen before checkout")
        lines = [line for line in self.list_session_lines(int(session_id)) if (line.get("kitchen_status") or "new") != "cancelled"]
        if not lines:
            raise ValueError("Cannot checkout an empty restaurant session")
        total = self.session_total(int(session_id))
        adjustments = self.get_session_adjustments(int(session_id))
        existing_paid = self.session_paid(int(session_id))
        extra_paid = self.decimal_value(paid_amount, "0") if paid_amount is not None else Decimal("0")
        if extra_paid < Decimal("0"):
            raise ValueError("Paid amount cannot be negative")
        if existing_paid == Decimal("0") and paid_amount is None:
            extra_paid = total
        paid = existing_paid + extra_paid
        if paid < total:
            raise ValueError("Cannot checkout before the restaurant session is fully paid")
        if paid > total:
            paid = total
        now_date = datetime.date.today().isoformat()
        now_ts = datetime.datetime.now().isoformat(timespec="seconds")
        reference = self.next_restaurant_reference()
        cur = db.execute(
            """
            INSERT INTO invoices (user_id, type, date, reference, notes, total, paid, status, workflow_status, original_currency, payment_method, branch_id)
            VALUES (?, 'sale', ?, ?, ?, ?, ?, 'active', 'POSTED', 'USD', ?, ?)
            """,
            (
                str(user_id or "restaurant"),
                now_date,
                reference,
                f"Restaurant table {session.get('table_name') or session.get('table_id')} / session {session_id}",
                str(total),
                str(paid),
                payment_method or "cash",
                session.get('branch_id'),
            ),
        )
        invoice_id = int(cur.lastrowid)
        if extra_paid > Decimal("0"):
            db.execute(
                "INSERT INTO restaurant_payments(session_id, invoice_id, branch_id, amount, payment_method, status, notes, created_at) VALUES (?, ?, (SELECT branch_id FROM restaurant_sessions WHERE id=?), ?, ?, 'posted', ?, ?)",
                (int(session_id), invoice_id, int(session_id), str(extra_paid), payment_method or "cash", "checkout", now_ts),
            )
        db.execute("UPDATE restaurant_payments SET invoice_id=? WHERE session_id=? AND invoice_id IS NULL", (invoice_id, int(session_id)))
        for line in lines:
            quantity = self.decimal_value(line.get("quantity"), "0")
            unit_price = self.decimal_value(line.get("unit_price"), "0")
            line_total = quantity * unit_price
            db.execute(
                """
                INSERT INTO invoice_lines (invoice_id, item_id, description, quantity, unit_price, total, unit, quantity_in_base, unit_cost, cost_amount, conversion_factor)
                VALUES (?, ?, ?, ?, ?, ?, '', ?, ?, '0', 1.0)
                """,
                (
                    invoice_id,
                    line.get("item_id"),
                    line.get("item_name") or "Restaurant item",
                    str(quantity),
                    str(unit_price),
                    str(line_total),
                    str(quantity),
                    str(unit_price),
                ),
            )
        discount = self.decimal_value(adjustments.get("discount_amount"), "0")
        service_charge = self.decimal_value(adjustments.get("service_charge_amount"), "0")
        tax = self.decimal_value(adjustments.get("tax_amount"), "0")
        adjustment_lines = [
            ("Restaurant discount", -discount),
            ("Restaurant service charge", service_charge),
            ("Restaurant tax", tax),
        ]
        for description, amount in adjustment_lines:
            if amount == Decimal("0"):
                continue
            db.execute(
                """
                INSERT INTO invoice_lines (invoice_id, item_id, description, quantity, unit_price, total, unit, quantity_in_base, unit_cost, cost_amount, conversion_factor)
                VALUES (?, NULL, ?, '1', ?, ?, '', '1', ?, '0', 1.0)
                """,
                (invoice_id, description, str(amount), str(amount), str(amount)),
            )
        db.execute("UPDATE restaurant_order_lines SET kitchen_status='served' WHERE session_id=? AND kitchen_status IN ('sent','preparing','ready')", (int(session_id),))
        db.execute("UPDATE restaurant_sessions SET status='closed', closed_at=?, invoice_id=? WHERE id=?", (now_ts, invoice_id, int(session_id)))
        db.execute("UPDATE restaurant_tables SET status='free', updated_at=? WHERE id=?", (now_ts, int(session["table_id"])))
        db.commit()
        payload = self.get_session(int(session_id))
        payload["invoice_id"] = invoice_id
        payload["invoice_reference"] = reference
        payload["invoice_total"] = str(total)
        payload["paid_amount"] = str(paid)
        return payload


    def list_kitchen_tickets(self, status: str = "sent", limit: int = 50, station_id: int | None = None) -> list[dict[str, Any]]:
        self.ensure_kitchen_station_schema()
        db = get_db()
        limit = max(1, min(int(limit or 50), 200))
        status = str(status or "sent").strip().lower()
        where = []
        params: list[Any] = []
        if status and status != "all":
            where.append("kt.status=?")
            params.append(status)
        if station_id is not None:
            where.append("kt.station_id=?")
            params.append(int(station_id))
        where_sql = "WHERE " + " AND ".join(where) if where else ""
        params.append(limit)
        rows = db.execute(
            f"""
            SELECT kt.*, COALESCE(kt.branch_id, s.branch_id, t.branch_id) AS branch_id, s.table_id, t.name AS table_name, st.name AS station_name, st.code AS station_code,
                   COUNT(ktl.id) AS line_count
            FROM kitchen_tickets kt
            LEFT JOIN restaurant_sessions s ON s.id=kt.session_id
            LEFT JOIN restaurant_tables t ON t.id=s.table_id
            LEFT JOIN restaurant_kitchen_stations st ON st.id=kt.station_id
            LEFT JOIN kitchen_ticket_lines ktl ON ktl.ticket_id=kt.id
            {where_sql}
            GROUP BY kt.id
            ORDER BY kt.id DESC
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [dict(row) for row in rows]


    def get_kitchen_ticket(self, ticket_id: int) -> dict[str, Any]:
        self.ensure_kitchen_station_schema()
        db = get_db()
        row = db.execute(
            """
            SELECT kt.*, COALESCE(kt.branch_id, s.branch_id, t.branch_id) AS branch_id, s.table_id, t.name AS table_name, st.name AS station_name, st.code AS station_code
            FROM kitchen_tickets kt
            LEFT JOIN restaurant_sessions s ON s.id=kt.session_id
            LEFT JOIN restaurant_tables t ON t.id=s.table_id
            LEFT JOIN restaurant_kitchen_stations st ON st.id=kt.station_id
            WHERE kt.id=?
            """,
            (int(ticket_id),),
        ).fetchone()
        if not row:
            raise ValueError("Kitchen ticket not found")
        lines = db.execute(
            """
            SELECT ktl.*, rol.kitchen_status, rol.unit_price, st.name AS station_name, st.code AS station_code
            FROM kitchen_ticket_lines ktl
            LEFT JOIN restaurant_order_lines rol ON rol.id=ktl.order_line_id
            LEFT JOIN restaurant_kitchen_stations st ON st.id=ktl.station_id
            WHERE ktl.ticket_id=?
            ORDER BY ktl.id
            """,
            (int(ticket_id),),
        ).fetchall()
        payload = dict(row)
        payload["lines"] = [dict(line) for line in lines]
        return payload


    def update_kitchen_ticket_status(self, ticket_id: int, status: str) -> dict[str, Any]:
        self.ensure_schema()
        allowed = {"sent", "preparing", "ready", "served", "cancelled"}
        status = str(status or "").strip().lower()
        if status not in allowed:
            raise ValueError("Invalid kitchen ticket status")
        conn = get_db()
        ticket = self.get_kitchen_ticket(int(ticket_id))
        now = datetime.datetime.now().isoformat(timespec="seconds")
        conn.execute("UPDATE kitchen_tickets SET status=? WHERE id=?", (status, int(ticket_id)))
        if status in {"preparing", "ready", "served", "cancelled"}:
            conn.execute(
                """
                UPDATE restaurant_order_lines
                SET kitchen_status=?
                WHERE id IN (SELECT order_line_id FROM kitchen_ticket_lines WHERE ticket_id=?)
                """,
                (status, int(ticket_id)),
            )
        if status == "served":
            conn.execute("UPDATE kitchen_tickets SET printed_at=COALESCE(printed_at, ?) WHERE id=?", (now, int(ticket_id)))
        conn.commit()
        return self.get_kitchen_ticket(int(ticket_id))

    def close_session(self, session_id: int, invoice_id: int | None = None) -> dict[str, Any]:
        self.ensure_schema()
        db = get_db()
        session = self.get_session(int(session_id))
        if session.get("status") != "open":
            raise ValueError("Restaurant session is not open")
        counts = self.status_counts(int(session_id))
        if counts.get("new", 0) > 0:
            raise ValueError("Cannot close table while new order lines have not been sent to kitchen")
        now = datetime.datetime.now().isoformat(timespec="seconds")
        db.execute("UPDATE restaurant_order_lines SET kitchen_status='served' WHERE session_id=? AND kitchen_status IN ('sent','preparing','ready')", (int(session_id),))
        db.execute(
            "UPDATE restaurant_sessions SET status='closed', closed_at=?, invoice_id=? WHERE id=?",
            (now, invoice_id, int(session_id)),
        )
        db.execute("UPDATE restaurant_tables SET status='free', updated_at=? WHERE id=?", (now, int(session["table_id"])))
        db.commit()
        return self.get_session(int(session_id))


    def ensure_table_operations_schema(self) -> None:
        self.ensure_schema()
        db = get_db()
        db.execute("""
            CREATE TABLE IF NOT EXISTS restaurant_reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id INTEGER NOT NULL,
                branch_id INTEGER,
                customer_name TEXT,
                phone TEXT,
                guests INTEGER DEFAULT 1,
                reserved_at TEXT,
                status TEXT NOT NULL DEFAULT 'reserved',
                notes TEXT,
                created_at TEXT NOT NULL,
                cancelled_at TEXT,
                FOREIGN KEY(table_id) REFERENCES restaurant_tables(id)
            )
        """)
        for ddl in (
            "ALTER TABLE restaurant_reservations ADD COLUMN branch_id INTEGER",
        ):
            try:
                db.execute(ddl)
            except Exception:
                pass
        db.commit()

    def reserve_table(self, table_id: int, customer_name: str = "", phone: str = "", reserved_at: str = "", guests: int = 1, notes: str = "") -> dict[str, Any]:
        self.ensure_table_operations_schema()
        db = get_db()
        table = self.get_table(int(table_id))
        active = db.execute("SELECT id FROM restaurant_sessions WHERE table_id=? AND status='open' LIMIT 1", (int(table_id),)).fetchone()
        if active:
            raise ValueError("Cannot reserve an occupied restaurant table")
        now = datetime.datetime.now().isoformat(timespec="seconds")
        cur = db.execute(
            "INSERT INTO restaurant_reservations(table_id, branch_id, customer_name, phone, guests, reserved_at, status, notes, created_at) VALUES (?, (SELECT branch_id FROM restaurant_tables WHERE id=?), ?, ?, ?, ?, 'reserved', ?, ?)",
            (int(table_id), int(table_id), customer_name or '', phone or '', max(1, int(guests or 1)), reserved_at or now, notes or '', now),
        )
        db.execute("UPDATE restaurant_tables SET status='reserved', updated_at=? WHERE id=?", (now, int(table_id)))
        db.commit()
        reservation = db.execute("SELECT * FROM restaurant_reservations WHERE id=?", (int(cur.lastrowid),)).fetchone()
        return dict(reservation) if reservation else {}

    def cancel_reservation(self, reservation_id: int) -> dict[str, Any]:
        self.ensure_table_operations_schema()
        db = get_db()
        row = db.execute("SELECT * FROM restaurant_reservations WHERE id=?", (int(reservation_id),)).fetchone()
        if not row:
            raise ValueError("Restaurant reservation not found")
        now = datetime.datetime.now().isoformat(timespec="seconds")
        db.execute("UPDATE restaurant_reservations SET status='cancelled', cancelled_at=? WHERE id=?", (now, int(reservation_id)))
        active = db.execute("SELECT id FROM restaurant_sessions WHERE table_id=? AND status='open' LIMIT 1", (int(row['table_id']),)).fetchone()
        if not active:
            db.execute("UPDATE restaurant_tables SET status='free', updated_at=? WHERE id=?", (now, int(row['table_id'])))
        db.commit()
        result = db.execute("SELECT * FROM restaurant_reservations WHERE id=?", (int(reservation_id),)).fetchone()
        return dict(result) if result else {}

    def transfer_session(self, session_id: int, target_table_id: int) -> dict[str, Any]:
        self.ensure_table_operations_schema()
        db = get_db()
        session = self.get_session(int(session_id))
        if session.get('status') != 'open':
            raise ValueError("Restaurant session is not open")
        target = self.get_table(int(target_table_id))
        active_target = db.execute("SELECT id FROM restaurant_sessions WHERE table_id=? AND status='open' LIMIT 1", (int(target_table_id),)).fetchone()
        if active_target:
            raise ValueError("Target restaurant table is already occupied")
        now = datetime.datetime.now().isoformat(timespec="seconds")
        old_table_id = int(session['table_id'])
        db.execute("UPDATE restaurant_sessions SET table_id=? WHERE id=?", (int(target_table_id), int(session_id)))
        db.execute("UPDATE restaurant_tables SET status='free', updated_at=? WHERE id=?", (now, old_table_id))
        db.execute("UPDATE restaurant_tables SET status='occupied', updated_at=? WHERE id=?", (now, int(target_table_id)))
        db.commit()
        payload = self.get_session(int(session_id))
        payload['transferred_from_table_id'] = old_table_id
        payload['transferred_to_table_id'] = int(target_table_id)
        return payload

    def merge_sessions(self, source_session_id: int, target_session_id: int) -> dict[str, Any]:
        self.ensure_table_operations_schema()
        if int(source_session_id) == int(target_session_id):
            raise ValueError("Cannot merge a restaurant session into itself")
        db = get_db()
        source = self.get_session(int(source_session_id))
        target = self.get_session(int(target_session_id))
        if source.get('status') != 'open' or target.get('status') != 'open':
            raise ValueError("Both restaurant sessions must be open before merge")
        now = datetime.datetime.now().isoformat(timespec="seconds")
        db.execute("UPDATE restaurant_order_lines SET session_id=? WHERE session_id=?", (int(target_session_id), int(source_session_id)))
        db.execute("UPDATE kitchen_tickets SET session_id=? WHERE session_id=?", (int(target_session_id), int(source_session_id)))
        db.execute("UPDATE restaurant_payments SET session_id=? WHERE session_id=?", (int(target_session_id), int(source_session_id)))
        db.execute("UPDATE restaurant_sessions SET status='merged', closed_at=? WHERE id=?", (now, int(source_session_id)))
        db.execute("UPDATE restaurant_tables SET status='free', updated_at=? WHERE id=?", (now, int(source['table_id'])))
        db.execute("UPDATE restaurant_tables SET status='occupied', updated_at=? WHERE id=?", (now, int(target['table_id'])))
        db.commit()
        payload = self.get_session(int(target_session_id))
        payload['lines'] = self.list_session_lines(int(target_session_id))
        payload['merged_source_session_id'] = int(source_session_id)
        return payload

    def split_lines_to_table(self, session_id: int, line_ids: list[int], target_table_id: int, guests: int = 1, notes: str = "") -> dict[str, Any]:
        self.ensure_table_operations_schema()
        db = get_db()
        source = self.get_session(int(session_id))
        if source.get('status') != 'open':
            raise ValueError("Restaurant session is not open")
        ids = [int(x) for x in (line_ids or [])]
        if not ids:
            raise ValueError("Select at least one restaurant order line to split")
        placeholders = ','.join('?' for _ in ids)
        rows = db.execute(f"SELECT id FROM restaurant_order_lines WHERE session_id=? AND id IN ({placeholders})", [int(session_id), *ids]).fetchall()
        if len(rows) != len(set(ids)):
            raise ValueError("One or more selected order lines do not belong to this restaurant session")
        active_target = db.execute("SELECT * FROM restaurant_sessions WHERE table_id=? AND status='open' LIMIT 1", (int(target_table_id),)).fetchone()
        if active_target:
            target_session_id = int(active_target['id'])
        else:
            target_session_id = int(self.open_table(int(target_table_id), guests=max(1, int(guests or 1)), notes=notes or 'split')['id'])
        db.execute(f"UPDATE restaurant_order_lines SET session_id=? WHERE id IN ({placeholders})", [target_session_id, *ids])
        db.commit()
        return {
            'source_session': {**self.get_session(int(session_id)), 'lines': self.list_session_lines(int(session_id))},
            'target_session': {**self.get_session(target_session_id), 'lines': self.list_session_lines(target_session_id)},
            'moved_line_ids': ids,
        }


    def ensure_waiter_workflow_schema(self) -> None:
        self.ensure_table_operations_schema()
        db = get_db()
        for ddl in (
            "ALTER TABLE restaurant_sessions ADD COLUMN service_started_at TEXT",
            "ALTER TABLE restaurant_sessions ADD COLUMN last_activity_at TEXT",
            "ALTER TABLE restaurant_sessions ADD COLUMN waiter_call_at TEXT",
            "ALTER TABLE restaurant_sessions ADD COLUMN waiter_call_status TEXT",
            "ALTER TABLE restaurant_sessions ADD COLUMN modification_count INTEGER DEFAULT 0",
            "ALTER TABLE restaurant_sessions ADD COLUMN cancelled_line_count INTEGER DEFAULT 0",
        ):
            try:
                db.execute(ddl)
            except Exception:
                pass
        db.execute("""
            CREATE TABLE IF NOT EXISTS restaurant_service_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                waiter_id TEXT,
                line_id INTEGER,
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES restaurant_sessions(id) ON DELETE CASCADE
            )
        """)
        db.commit()

    def _record_service_event(self, session_id: int, event_type: str, waiter_id: str | None = None, line_id: int | None = None, notes: str = "") -> None:
        self.ensure_waiter_workflow_schema()
        now = datetime.datetime.now().isoformat(timespec="seconds")
        get_db().execute(
            "INSERT INTO restaurant_service_events(session_id, event_type, waiter_id, line_id, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (int(session_id), event_type, waiter_id, line_id, notes or "", now),
        )
        get_db().execute("UPDATE restaurant_sessions SET last_activity_at=? WHERE id=?", (now, int(session_id)))
        get_db().commit()

    def assign_waiter(self, session_id: int, waiter_id: str, notes: str = "") -> dict[str, Any]:
        self.ensure_waiter_workflow_schema()
        session = self.get_session(int(session_id))
        if session.get("status") != "open":
            raise ValueError("Restaurant session is not open")
        waiter_id = str(waiter_id or "").strip()
        if not waiter_id:
            raise ValueError("Waiter id is required")
        now = datetime.datetime.now().isoformat(timespec="seconds")
        db = get_db()
        db.execute(
            "UPDATE restaurant_sessions SET waiter_id=?, service_started_at=COALESCE(service_started_at, ?), last_activity_at=? WHERE id=?",
            (waiter_id, now, now, int(session_id)),
        )
        db.execute(
            "INSERT INTO restaurant_service_events(session_id, event_type, waiter_id, notes, created_at) VALUES (?, 'waiter_assigned', ?, ?, ?)",
            (int(session_id), waiter_id, notes or "", now),
        )
        db.commit()
        return self.get_session(int(session_id))

    def call_waiter(self, session_id: int, notes: str = "") -> dict[str, Any]:
        self.ensure_waiter_workflow_schema()
        session = self.get_session(int(session_id))
        if session.get("status") != "open":
            raise ValueError("Restaurant session is not open")
        now = datetime.datetime.now().isoformat(timespec="seconds")
        db = get_db()
        db.execute(
            "UPDATE restaurant_sessions SET waiter_call_at=?, waiter_call_status='open', last_activity_at=? WHERE id=?",
            (now, now, int(session_id)),
        )
        db.execute(
            "INSERT INTO restaurant_service_events(session_id, event_type, waiter_id, notes, created_at) VALUES (?, 'waiter_called', ?, ?, ?)",
            (int(session_id), session.get("waiter_id"), notes or "", now),
        )
        db.commit()
        payload = self.get_session(int(session_id))
        payload["waiter_call_pending"] = True
        return payload

    def resolve_waiter_call(self, session_id: int, notes: str = "") -> dict[str, Any]:
        self.ensure_waiter_workflow_schema()
        session = self.get_session(int(session_id))
        now = datetime.datetime.now().isoformat(timespec="seconds")
        db = get_db()
        db.execute(
            "UPDATE restaurant_sessions SET waiter_call_status='resolved', last_activity_at=? WHERE id=?",
            (now, int(session_id)),
        )
        db.execute(
            "INSERT INTO restaurant_service_events(session_id, event_type, waiter_id, notes, created_at) VALUES (?, 'waiter_call_resolved', ?, ?, ?)",
            (int(session_id), session.get("waiter_id"), notes or "", now),
        )
        db.commit()
        return self.get_session(int(session_id))



    def ensure_kitchen_station_schema(self) -> None:
        self.ensure_waiter_workflow_schema()
        conn = get_db()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS restaurant_kitchen_stations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS restaurant_menu_station_map (
                item_id INTEGER PRIMARY KEY,
                station_id INTEGER NOT NULL,
                updated_at TEXT,
                FOREIGN KEY(station_id) REFERENCES restaurant_kitchen_stations(id)
            );
        """)
        for ddl in (
            "ALTER TABLE kitchen_tickets ADD COLUMN station_id INTEGER",
            "ALTER TABLE kitchen_ticket_lines ADD COLUMN station_id INTEGER",
            "ALTER TABLE restaurant_order_lines ADD COLUMN kitchen_station_id INTEGER",
        ):
            try:
                conn.execute(ddl)
            except Exception:
                pass
        now = datetime.datetime.now().isoformat(timespec="seconds")
        defaults = [("bar", "Bar", 10), ("grill", "Grill", 20), ("hot", "Hot Kitchen", 30), ("dessert", "Dessert", 40)]
        for code, name, order in defaults:
            conn.execute(
                "INSERT OR IGNORE INTO restaurant_kitchen_stations(code, name, sort_order, is_active, created_at, updated_at) VALUES (?, ?, ?, 1, ?, ?)",
                (code, name, order, now, now),
            )
        conn.commit()

    def list_kitchen_stations(self, include_inactive: bool = False) -> list[dict[str, Any]]:
        self.ensure_kitchen_station_schema()
        where = "" if include_inactive else "WHERE is_active=1"
        rows = get_db().execute(
            f"SELECT * FROM restaurant_kitchen_stations {where} ORDER BY sort_order, id"
        ).fetchall()
        return [dict(row) for row in rows]

    def upsert_kitchen_station(self, name: str, code: str = "", sort_order: int = 0, station_id: int | None = None, is_active: bool = True) -> dict[str, Any]:
        self.ensure_kitchen_station_schema()
        name = str(name or "").strip()
        if not name:
            raise ValueError("Kitchen station name is required")
        code = str(code or name).strip().lower().replace(" ", "_")
        now = datetime.datetime.now().isoformat(timespec="seconds")
        conn = get_db()
        if station_id:
            conn.execute(
                "UPDATE restaurant_kitchen_stations SET code=?, name=?, sort_order=?, is_active=?, updated_at=? WHERE id=?",
                (code, name, int(sort_order or 0), 1 if is_active else 0, now, int(station_id)),
            )
            new_id = int(station_id)
        else:
            cur = conn.execute(
                "INSERT INTO restaurant_kitchen_stations(code, name, sort_order, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (code, name, int(sort_order or 0), 1 if is_active else 0, now, now),
            )
            new_id = int(cur.lastrowid)
        conn.commit()
        row = conn.execute("SELECT * FROM restaurant_kitchen_stations WHERE id=?", (new_id,)).fetchone()
        return dict(row) if row else {}

    def assign_menu_item_station(self, item_id: int, station_id: int) -> dict[str, Any]:
        self.ensure_kitchen_station_schema()
        conn = get_db()
        station = conn.execute("SELECT * FROM restaurant_kitchen_stations WHERE id=? AND is_active=1", (int(station_id),)).fetchone()
        if not station:
            raise ValueError("Kitchen station not found")
        now = datetime.datetime.now().isoformat(timespec="seconds")
        conn.execute(
            "INSERT INTO restaurant_menu_station_map(item_id, station_id, updated_at) VALUES (?, ?, ?) ON CONFLICT(item_id) DO UPDATE SET station_id=excluded.station_id, updated_at=excluded.updated_at",
            (int(item_id), int(station_id), now),
        )
        conn.commit()
        return {"item_id": int(item_id), "station_id": int(station_id), "station": dict(station)}

    def station_for_order_line(self, line: dict[str, Any]) -> dict[str, Any]:
        self.ensure_kitchen_station_schema()
        conn = get_db()
        station = None
        if line.get("item_id"):
            station = conn.execute(
                """
                SELECT s.* FROM restaurant_menu_station_map m
                JOIN restaurant_kitchen_stations s ON s.id=m.station_id
                WHERE m.item_id=? AND s.is_active=1
                """,
                (int(line["item_id"]),),
            ).fetchone()
        if not station:
            station = conn.execute(
                "SELECT * FROM restaurant_kitchen_stations WHERE code='hot' AND is_active=1 LIMIT 1"
            ).fetchone()
        if not station:
            station = conn.execute("SELECT * FROM restaurant_kitchen_stations WHERE is_active=1 ORDER BY sort_order, id LIMIT 1").fetchone()
        return dict(station) if station else {"id": None, "name": "Kitchen"}

    def waiter_session_summary(self, session_id: int) -> dict[str, Any]:
        self.ensure_waiter_workflow_schema()
        session = self.get_session(int(session_id))
        rows = get_db().execute(
            "SELECT event_type, COUNT(*) AS c FROM restaurant_service_events WHERE session_id=? GROUP BY event_type",
            (int(session_id),),
        ).fetchall()
        event_counts = {str(row["event_type"]): int(row["c"] or 0) for row in rows}
        opened_at = session.get("opened_at")
        minutes_open = 0
        try:
            opened = datetime.datetime.fromisoformat(str(opened_at))
            minutes_open = int((datetime.datetime.now() - opened).total_seconds() // 60)
        except Exception:
            minutes_open = 0
        return {
            "session_id": int(session_id),
            "table_id": session.get("table_id"),
            "table_name": session.get("table_name"),
            "waiter_id": session.get("waiter_id"),
            "minutes_open": minutes_open,
            "modification_count": int(session.get("modification_count") or 0),
            "cancelled_line_count": int(session.get("cancelled_line_count") or 0),
            "waiter_call_status": session.get("waiter_call_status") or "none",
            "event_counts": event_counts,
        }


    def restaurant_analytics(self, start_date: str = "", end_date: str = "") -> dict[str, Any]:
        """Read-only restaurant operational analytics.

        SQL remains inside the repository boundary. HTTP/services receive only a
        semantic payload: sales, table usage, waiter performance, kitchen load,
        and top menu items.
        """
        self.ensure_kitchen_station_schema()
        self.ensure_waiter_workflow_schema()
        db = get_db()
        start = str(start_date or "").strip()
        end = str(end_date or "").strip()

        def _between(column: str, params: list[Any]) -> str:
            clauses: list[str] = []
            if start:
                clauses.append(f"{column} >= ?")
                params.append(start)
            if end:
                clauses.append(f"{column} <= ?")
                params.append(end)
            return (" AND " + " AND ".join(clauses)) if clauses else ""

        table_counts = db.execute(
            "SELECT status, COUNT(*) AS c FROM restaurant_tables WHERE is_active=1 GROUP BY status"
        ).fetchall()
        table_status = {str(row["status"] or "free"): int(row["c"] or 0) for row in table_counts}

        session_params: list[Any] = []
        session_date_filter = _between("opened_at", session_params)
        session_row = db.execute(
            f"SELECT COUNT(*) AS total_sessions, SUM(CASE WHEN status='open' THEN 1 ELSE 0 END) AS open_sessions FROM restaurant_sessions WHERE 1=1 {session_date_filter}",
            session_params,
        ).fetchone()

        payment_params: list[Any] = []
        payment_date_filter = _between("created_at", payment_params)
        payment_rows = db.execute(
            f"SELECT amount, payment_method FROM restaurant_payments WHERE status='posted' {payment_date_filter}",
            payment_params,
        ).fetchall()
        total_payments = sum((self.decimal_value(row["amount"], "0") for row in payment_rows), Decimal("0"))
        by_payment_method: dict[str, Decimal] = {}
        for row in payment_rows:
            method = str(row["payment_method"] or "cash")
            by_payment_method[method] = by_payment_method.get(method, Decimal("0")) + self.decimal_value(row["amount"], "0")

        item_params: list[Any] = []
        item_date_filter = _between("s.opened_at", item_params)
        item_rows = db.execute(
            f"""
            SELECT l.item_name, SUM(CAST(COALESCE(NULLIF(l.quantity, ''), '0') AS REAL)) AS quantity,
                   SUM(CAST(COALESCE(NULLIF(l.quantity, ''), '0') AS REAL) * CAST(COALESCE(NULLIF(l.unit_price, ''), '0') AS REAL)) AS sales
            FROM restaurant_order_lines l
            JOIN restaurant_sessions s ON s.id=l.session_id
            WHERE COALESCE(l.kitchen_status, 'new') <> 'cancelled' {item_date_filter}
            GROUP BY l.item_name
            ORDER BY sales DESC, quantity DESC
            LIMIT 10
            """,
            item_params,
        ).fetchall()

        table_params: list[Any] = []
        table_date_filter = _between("s.opened_at", table_params)
        table_rows = db.execute(
            f"""
            SELECT t.id AS table_id, t.name AS table_name, COUNT(s.id) AS sessions,
                   SUM(CASE WHEN s.status='open' THEN 1 ELSE 0 END) AS open_sessions
            FROM restaurant_tables t
            LEFT JOIN restaurant_sessions s ON s.table_id=t.id {table_date_filter}
            WHERE t.is_active=1
            GROUP BY t.id, t.name
            ORDER BY sessions DESC, t.id
            LIMIT 10
            """,
            table_params,
        ).fetchall()

        waiter_params: list[Any] = []
        waiter_date_filter = _between("s.opened_at", waiter_params)
        waiter_rows = db.execute(
            f"""
            SELECT COALESCE(NULLIF(s.waiter_id, ''), 'unassigned') AS waiter_id,
                   COUNT(DISTINCT s.id) AS sessions,
                   COALESCE(SUM(s.modification_count), 0) AS modifications,
                   COALESCE(SUM(s.cancelled_line_count), 0) AS cancellations,
                   COUNT(l.id) AS lines
            FROM restaurant_sessions s
            LEFT JOIN restaurant_order_lines l ON l.session_id=s.id
            WHERE 1=1 {waiter_date_filter}
            GROUP BY COALESCE(NULLIF(s.waiter_id, ''), 'unassigned')
            ORDER BY sessions DESC, lines DESC
            LIMIT 10
            """,
            waiter_params,
        ).fetchall()

        kitchen_params: list[Any] = []
        kitchen_date_filter = _between("kt.sent_at", kitchen_params)
        kitchen_rows = db.execute(
            f"""
            SELECT COALESCE(st.code, 'unassigned') AS station_code,
                   COALESCE(st.name, 'Unassigned') AS station_name,
                   COUNT(DISTINCT kt.id) AS tickets,
                   COUNT(ktl.id) AS lines,
                   SUM(CASE WHEN kt.status='ready' THEN 1 ELSE 0 END) AS ready_tickets,
                   SUM(CASE WHEN kt.status='cancelled' THEN 1 ELSE 0 END) AS cancelled_tickets
            FROM kitchen_tickets kt
            LEFT JOIN restaurant_kitchen_stations st ON st.id=kt.station_id
            LEFT JOIN kitchen_ticket_lines ktl ON ktl.ticket_id=kt.id
            WHERE 1=1 {kitchen_date_filter}
            GROUP BY COALESCE(st.code, 'unassigned'), COALESCE(st.name, 'Unassigned')
            ORDER BY tickets DESC, lines DESC
            LIMIT 10
            """,
            kitchen_params,
        ).fetchall()

        return {
            "period": {"start_date": start, "end_date": end},
            "summary": {
                "total_sessions": int((session_row or {})["total_sessions"] or 0),
                "open_sessions": int((session_row or {})["open_sessions"] or 0),
                "table_status": table_status,
                "payments_total": str(total_payments),
                "payment_methods": {k: str(v) for k, v in by_payment_method.items()},
            },
            "top_items": [dict(row) for row in item_rows],
            "table_usage": [dict(row) for row in table_rows],
            "waiter_performance": [dict(row) for row in waiter_rows],
            "kitchen_performance": [dict(row) for row in kitchen_rows],
        }



    # ------------------------------------------------------------------
    # Phase 34: restaurant modifiers + recipe/consumption integration
    # ------------------------------------------------------------------
    def ensure_modifier_recipe_schema(self) -> None:
        self.ensure_kitchen_station_schema()
        db = get_db()
        db.executescript("""
            CREATE TABLE IF NOT EXISTS restaurant_modifier_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                name TEXT NOT NULL,
                min_selected INTEGER NOT NULL DEFAULT 0,
                max_selected INTEGER NOT NULL DEFAULT 1,
                is_required INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS restaurant_modifier_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                price_delta TEXT NOT NULL DEFAULT '0',
                item_id INTEGER,
                kitchen_label TEXT,
                is_default INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY(group_id) REFERENCES restaurant_modifier_groups(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS restaurant_order_line_modifiers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                line_id INTEGER NOT NULL,
                group_id INTEGER,
                option_id INTEGER,
                name TEXT NOT NULL,
                price_delta TEXT NOT NULL DEFAULT '0',
                quantity TEXT NOT NULL DEFAULT '1',
                action TEXT NOT NULL DEFAULT 'add',
                kitchen_label TEXT,
                created_at TEXT,
                FOREIGN KEY(line_id) REFERENCES restaurant_order_lines(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS restaurant_recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL UNIQUE,
                name TEXT,
                yield_quantity TEXT NOT NULL DEFAULT '1',
                is_active INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS restaurant_recipe_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                component_item_id INTEGER,
                component_name TEXT NOT NULL,
                quantity TEXT NOT NULL DEFAULT '0',
                unit TEXT,
                unit_cost TEXT NOT NULL DEFAULT '0',
                FOREIGN KEY(recipe_id) REFERENCES restaurant_recipes(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS restaurant_inventory_consumption (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                order_line_id INTEGER NOT NULL,
                invoice_id INTEGER,
                item_id INTEGER,
                component_item_id INTEGER,
                component_name TEXT NOT NULL,
                quantity TEXT NOT NULL DEFAULT '0',
                unit TEXT,
                source_key TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            );
        """)
        db.commit()

    def upsert_modifier_group(self, item_id: int | None, name: str, min_selected: int = 0, max_selected: int = 1, is_required: bool = False, group_id: int | None = None) -> dict[str, Any]:
        self.ensure_modifier_recipe_schema()
        name = str(name or '').strip()
        if not name:
            raise ValueError('Modifier group name is required')
        now = datetime.datetime.now().isoformat(timespec='seconds')
        db = get_db()
        if group_id:
            db.execute(
                'UPDATE restaurant_modifier_groups SET item_id=?, name=?, min_selected=?, max_selected=?, is_required=?, updated_at=? WHERE id=?',
                (item_id, name, int(min_selected or 0), int(max_selected or 1), 1 if is_required else 0, now, int(group_id)),
            )
            new_id = int(group_id)
        else:
            cur = db.execute(
                'INSERT INTO restaurant_modifier_groups(item_id, name, min_selected, max_selected, is_required, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 1, ?, ?)',
                (item_id, name, int(min_selected or 0), int(max_selected or 1), 1 if is_required else 0, now, now),
            )
            new_id = int(cur.lastrowid)
        db.commit()
        return self.get_modifier_group(new_id)

    def get_modifier_group(self, group_id: int) -> dict[str, Any]:
        self.ensure_modifier_recipe_schema()
        row = get_db().execute('SELECT * FROM restaurant_modifier_groups WHERE id=?', (int(group_id),)).fetchone()
        if not row:
            raise ValueError('Modifier group not found')
        payload = dict(row)
        payload['options'] = self.list_modifier_options(int(group_id))
        return payload

    def list_modifier_groups(self, item_id: int | None = None, include_inactive: bool = False) -> list[dict[str, Any]]:
        self.ensure_modifier_recipe_schema()
        where = [] if include_inactive else ['is_active=1']
        params: list[Any] = []
        if item_id is not None:
            where.append('(item_id=? OR item_id IS NULL)')
            params.append(int(item_id))
        sql_where = 'WHERE ' + ' AND '.join(where) if where else ''
        rows = get_db().execute(f'SELECT * FROM restaurant_modifier_groups {sql_where} ORDER BY item_id IS NOT NULL DESC, id', params).fetchall()
        result = []
        for row in rows:
            payload = dict(row)
            payload['options'] = self.list_modifier_options(int(row['id']))
            result.append(payload)
        return result

    def upsert_modifier_option(self, group_id: int, name: str, price_delta: Any = '0', item_id: int | None = None, kitchen_label: str = '', is_default: bool = False, option_id: int | None = None) -> dict[str, Any]:
        self.ensure_modifier_recipe_schema()
        name = str(name or '').strip()
        if not name:
            raise ValueError('Modifier option name is required')
        price = self.decimal_value(price_delta, '0')
        now = datetime.datetime.now().isoformat(timespec='seconds')
        db = get_db()
        if option_id:
            db.execute(
                'UPDATE restaurant_modifier_options SET group_id=?, name=?, price_delta=?, item_id=?, kitchen_label=?, is_default=?, updated_at=? WHERE id=?',
                (int(group_id), name, str(price), item_id, kitchen_label or name, 1 if is_default else 0, now, int(option_id)),
            )
            new_id = int(option_id)
        else:
            cur = db.execute(
                'INSERT INTO restaurant_modifier_options(group_id, name, price_delta, item_id, kitchen_label, is_default, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)',
                (int(group_id), name, str(price), item_id, kitchen_label or name, 1 if is_default else 0, now, now),
            )
            new_id = int(cur.lastrowid)
        db.commit()
        return self.get_modifier_option(new_id)

    def get_modifier_option(self, option_id: int) -> dict[str, Any]:
        self.ensure_modifier_recipe_schema()
        row = get_db().execute('SELECT * FROM restaurant_modifier_options WHERE id=?', (int(option_id),)).fetchone()
        if not row:
            raise ValueError('Modifier option not found')
        return dict(row)

    def list_modifier_options(self, group_id: int) -> list[dict[str, Any]]:
        self.ensure_modifier_recipe_schema()
        rows = get_db().execute('SELECT * FROM restaurant_modifier_options WHERE group_id=? AND is_active=1 ORDER BY id', (int(group_id),)).fetchall()
        return [dict(row) for row in rows]

    def add_order_line_modifier(self, line_id: int, option_id: int | None = None, name: str = '', price_delta: Any = '0', quantity: Any = '1', action: str = 'add', group_id: int | None = None, kitchen_label: str = '') -> dict[str, Any]:
        self.ensure_modifier_recipe_schema()
        self.get_order_line(int(line_id))
        option = self.get_modifier_option(int(option_id)) if option_id else None
        if option:
            group_id = group_id or option.get('group_id')
            name = name or option.get('name') or ''
            price_delta = option.get('price_delta', price_delta)
            kitchen_label = kitchen_label or option.get('kitchen_label') or name
        name = str(name or '').strip()
        if not name:
            raise ValueError('Modifier name is required')
        action = str(action or 'add').strip().lower()
        if action not in {'add', 'remove', 'note', 'size'}:
            action = 'add'
        now = datetime.datetime.now().isoformat(timespec='seconds')
        cur = get_db().execute(
            'INSERT INTO restaurant_order_line_modifiers(line_id, group_id, option_id, name, price_delta, quantity, action, kitchen_label, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (int(line_id), group_id, option_id, name, str(self.decimal_value(price_delta, '0')), str(self.decimal_value(quantity, '1')), action, kitchen_label or name, now),
        )
        get_db().commit()
        return self.get_order_line_modifier(int(cur.lastrowid))

    def get_order_line_modifier(self, modifier_id: int) -> dict[str, Any]:
        self.ensure_modifier_recipe_schema()
        row = get_db().execute('SELECT * FROM restaurant_order_line_modifiers WHERE id=?', (int(modifier_id),)).fetchone()
        if not row:
            raise ValueError('Order line modifier not found')
        return dict(row)

    def list_line_modifiers(self, line_id: int) -> list[dict[str, Any]]:
        self.ensure_modifier_recipe_schema()
        rows = get_db().execute('SELECT * FROM restaurant_order_line_modifiers WHERE line_id=? ORDER BY id', (int(line_id),)).fetchall()
        return [dict(row) for row in rows]

    def line_modifier_total(self, line_id: int) -> Decimal:
        total = Decimal('0')
        for modifier in self.list_line_modifiers(int(line_id)):
            if (modifier.get('action') or 'add') in {'remove', 'note'}:
                continue
            total += self.decimal_value(modifier.get('price_delta'), '0') * self.decimal_value(modifier.get('quantity'), '1')
        return total

    def get_order_line(self, line_id: int) -> dict[str, Any]:
        self.ensure_modifier_recipe_schema()
        row = get_db().execute('SELECT * FROM restaurant_order_lines WHERE id=?', (int(line_id),)).fetchone()
        if not row:
            raise ValueError('Restaurant order line not found')
        payload = dict(row)
        modifiers = self.list_line_modifiers(int(line_id))
        qty = self.decimal_value(payload.get('quantity'), '0')
        base = qty * self.decimal_value(payload.get('unit_price'), '0')
        modifier_total = self.line_modifier_total(int(line_id))
        payload['modifiers'] = modifiers
        payload['modifier_total'] = str(modifier_total)
        payload['line_total'] = str(base + modifier_total)
        if modifiers:
            labels = []
            for mod in modifiers:
                sign = '-' if (mod.get('action') == 'remove') else '+' if self.decimal_value(mod.get('price_delta'), '0') > 0 else ''
                labels.append(f"{sign}{mod.get('kitchen_label') or mod.get('name')}")
            payload['kitchen_modifier_notes'] = ', '.join(labels)
        else:
            payload['kitchen_modifier_notes'] = ''
        return payload

    def list_session_lines(self, session_id: int) -> list[dict[str, Any]]:
        self.ensure_modifier_recipe_schema()
        rows = get_db().execute('SELECT id FROM restaurant_order_lines WHERE session_id=? ORDER BY id', (int(session_id),)).fetchall()
        return [self.get_order_line(int(row['id'])) for row in rows]

    def session_subtotal(self, session_id: int) -> Decimal:
        billable = [line for line in self.list_session_lines(int(session_id)) if (line.get('kitchen_status') or 'new') != 'cancelled']
        return sum((self.decimal_value(line.get('line_total'), '0') for line in billable), Decimal('0'))

    def upsert_recipe(self, item_id: int, name: str = '', yield_quantity: Any = '1', lines: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        self.ensure_modifier_recipe_schema()
        db = get_db()
        now = datetime.datetime.now().isoformat(timespec='seconds')
        row = db.execute('SELECT id FROM restaurant_recipes WHERE item_id=?', (int(item_id),)).fetchone()
        if row:
            recipe_id = int(row['id'])
            db.execute('UPDATE restaurant_recipes SET name=?, yield_quantity=?, is_active=1, updated_at=? WHERE id=?', (name or f'Item {item_id}', str(self.decimal_value(yield_quantity, '1')), now, recipe_id))
            db.execute('DELETE FROM restaurant_recipe_lines WHERE recipe_id=?', (recipe_id,))
        else:
            cur = db.execute('INSERT INTO restaurant_recipes(item_id, name, yield_quantity, is_active, updated_at) VALUES (?, ?, ?, 1, ?)', (int(item_id), name or f'Item {item_id}', str(self.decimal_value(yield_quantity, '1')), now))
            recipe_id = int(cur.lastrowid)
        for line in lines or []:
            component_name = str(line.get('component_name') or line.get('name') or '').strip()
            if not component_name:
                continue
            db.execute(
                'INSERT INTO restaurant_recipe_lines(recipe_id, component_item_id, component_name, quantity, unit, unit_cost) VALUES (?, ?, ?, ?, ?, ?)',
                (recipe_id, line.get('component_item_id'), component_name, str(self.decimal_value(line.get('quantity'), '0')), line.get('unit') or '', str(self.decimal_value(line.get('unit_cost'), '0'))),
            )
        db.commit()
        return self.get_recipe_by_item(int(item_id))

    def get_recipe_by_item(self, item_id: int) -> dict[str, Any]:
        self.ensure_modifier_recipe_schema()
        row = get_db().execute('SELECT * FROM restaurant_recipes WHERE item_id=? AND is_active=1', (int(item_id),)).fetchone()
        if not row:
            return {'item_id': int(item_id), 'lines': [], 'is_configured': False}
        payload = dict(row)
        rows = get_db().execute('SELECT * FROM restaurant_recipe_lines WHERE recipe_id=? ORDER BY id', (int(row['id']),)).fetchall()
        payload['lines'] = [dict(line) for line in rows]
        payload['is_configured'] = True
        return payload

    def consume_session_recipes(self, session_id: int, invoice_id: int | None = None) -> dict[str, Any]:
        self.ensure_modifier_recipe_schema()
        db = get_db()
        now = datetime.datetime.now().isoformat(timespec='seconds')
        consumed: list[dict[str, Any]] = []
        for line in self.list_session_lines(int(session_id)):
            if (line.get('kitchen_status') or 'new') == 'cancelled' or not line.get('item_id'):
                continue
            recipe = self.get_recipe_by_item(int(line['item_id']))
            if not recipe.get('is_configured'):
                continue
            yield_qty = self.decimal_value(recipe.get('yield_quantity'), '1') or Decimal('1')
            sold_qty = self.decimal_value(line.get('quantity'), '0')
            for component in recipe.get('lines') or []:
                per_recipe = self.decimal_value(component.get('quantity'), '0')
                consume_qty = (sold_qty * per_recipe) / yield_qty
                source_key = f"restaurant:{int(session_id)}:{int(line['id'])}:{component.get('id')}"
                try:
                    db.execute(
                        'INSERT INTO restaurant_inventory_consumption(session_id, order_line_id, invoice_id, item_id, component_item_id, component_name, quantity, unit, source_key, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                        (int(session_id), int(line['id']), invoice_id, line.get('item_id'), component.get('component_item_id'), component.get('component_name'), str(consume_qty), component.get('unit') or '', source_key, now),
                    )
                except Exception:
                    continue
                if component.get('component_item_id'):
                    try:
                        db.execute('UPDATE items SET quantity = CAST(COALESCE(NULLIF(quantity, \'\'), \'0\') AS REAL) - ? WHERE id=?', (float(consume_qty), int(component['component_item_id'])))
                    except Exception:
                        pass
                consumed.append({'line_id': int(line['id']), 'component_name': component.get('component_name'), 'quantity': str(consume_qty), 'unit': component.get('unit') or ''})
        db.commit()
        return {'session_id': int(session_id), 'invoice_id': invoice_id, 'consumed': consumed, 'count': len(consumed)}

    def checkout_session(self, session_id: int, user_id: str, paid_amount: Any | None = None, payment_method: str = 'cash') -> dict[str, Any]:
        """Create a posted sales invoice from a restaurant session, post recipe consumption once, and close it."""
        self.ensure_modifier_recipe_schema()
        db = get_db()
        session = self.get_session(int(session_id))
        if session.get('status') != 'open':
            raise ValueError('Restaurant session is not open')
        counts = self.status_counts(int(session_id))
        if counts.get('new', 0) > 0:
            raise ValueError('Send new order lines to kitchen before checkout')
        lines = [line for line in self.list_session_lines(int(session_id)) if (line.get('kitchen_status') or 'new') != 'cancelled']
        if not lines:
            raise ValueError('Cannot checkout an empty restaurant session')
        total = self.session_total(int(session_id))
        adjustments = self.get_session_adjustments(int(session_id))
        existing_paid = self.session_paid(int(session_id))
        extra_paid = self.decimal_value(paid_amount, '0') if paid_amount is not None else Decimal('0')
        if extra_paid < Decimal('0'):
            raise ValueError('Paid amount cannot be negative')
        if existing_paid == Decimal('0') and paid_amount is None:
            extra_paid = total
        paid = existing_paid + extra_paid
        if paid < total:
            raise ValueError('Cannot checkout before the restaurant session is fully paid')
        if paid > total:
            paid = total
        now_date = datetime.date.today().isoformat()
        now_ts = datetime.datetime.now().isoformat(timespec='seconds')
        reference = self.next_restaurant_reference()
        cur = db.execute(
            """
            INSERT INTO invoices (user_id, type, date, reference, notes, total, paid, status, workflow_status, original_currency, payment_method, branch_id)
            VALUES (?, 'sale', ?, ?, ?, ?, ?, 'active', 'POSTED', 'USD', ?, ?)
            """,
            (str(user_id or 'restaurant'), now_date, reference, f"Restaurant table {session.get('table_name') or session.get('table_id')} / session {session_id}", str(total), str(paid), payment_method or 'cash'),
        )
        invoice_id = int(cur.lastrowid)
        if extra_paid > Decimal('0'):
            db.execute(
                "INSERT INTO restaurant_payments(session_id, invoice_id, branch_id, amount, payment_method, status, notes, created_at) VALUES (?, ?, (SELECT branch_id FROM restaurant_sessions WHERE id=?), ?, ?, 'posted', ?, ?)",
                (int(session_id), invoice_id, int(session_id), str(extra_paid), payment_method or 'cash', 'checkout', now_ts),
            )
        db.execute('UPDATE restaurant_payments SET invoice_id=? WHERE session_id=? AND invoice_id IS NULL', (invoice_id, int(session_id)))
        for line in lines:
            quantity = self.decimal_value(line.get('quantity'), '0')
            unit_price = self.decimal_value(line.get('unit_price'), '0')
            line_total = self.decimal_value(line.get('line_total'), '0')
            description = line.get('item_name') or 'Restaurant item'
            if line.get('modifiers'):
                modifier_text = '; '.join([f"{m.get('action','add')} {m.get('name')}" for m in line.get('modifiers') or []])
                description = f"{description} ({modifier_text})"
            db.execute(
                """
                INSERT INTO invoice_lines (invoice_id, item_id, description, quantity, unit_price, total, unit, quantity_in_base, unit_cost, cost_amount, conversion_factor)
                VALUES (?, ?, ?, ?, ?, ?, '', ?, ?, '0', 1.0)
                """,
                (invoice_id, line.get('item_id'), description, str(quantity), str(unit_price), str(line_total), str(quantity), str(unit_price)),
            )
        discount = self.decimal_value(adjustments.get('discount_amount'), '0')
        service_charge = self.decimal_value(adjustments.get('service_charge_amount'), '0')
        tax = self.decimal_value(adjustments.get('tax_amount'), '0')
        for description, amount in [('Restaurant discount', -discount), ('Restaurant service charge', service_charge), ('Restaurant tax', tax)]:
            if amount == Decimal('0'):
                continue
            db.execute(
                """
                INSERT INTO invoice_lines (invoice_id, item_id, description, quantity, unit_price, total, unit, quantity_in_base, unit_cost, cost_amount, conversion_factor)
                VALUES (?, NULL, ?, '1', ?, ?, '', '1', ?, '0', 1.0)
                """,
                (invoice_id, description, str(amount), str(amount), str(amount)),
            )
        consumption = self.consume_session_recipes(int(session_id), invoice_id=invoice_id)
        db.execute("UPDATE restaurant_order_lines SET kitchen_status='served' WHERE session_id=? AND kitchen_status IN ('sent','preparing','ready')", (int(session_id),))
        db.execute('UPDATE restaurant_sessions SET status=\'closed\', closed_at=?, invoice_id=? WHERE id=?', (now_ts, invoice_id, int(session_id)))
        db.execute('UPDATE restaurant_tables SET status=\'free\', updated_at=? WHERE id=?', (now_ts, int(session['table_id'])))
        db.commit()
        payload = self.get_session(int(session_id))
        payload['invoice_id'] = invoice_id
        payload['invoice_reference'] = reference
        payload['invoice_total'] = str(total)
        payload['paid_amount'] = str(paid)
        payload['recipe_consumption'] = consumption
        return payload


    # Phase 35: takeaway/delivery workflow
    def ensure_delivery_takeaway_schema(self) -> None:
        self.ensure_schema()
        db = get_db()
        for ddl in (
            "ALTER TABLE restaurant_sessions ADD COLUMN order_type TEXT NOT NULL DEFAULT 'dine_in'",
            "ALTER TABLE restaurant_sessions ADD COLUMN customer_name TEXT",
            "ALTER TABLE restaurant_sessions ADD COLUMN phone TEXT",
            "ALTER TABLE restaurant_sessions ADD COLUMN delivery_address TEXT",
            "ALTER TABLE restaurant_sessions ADD COLUMN delivery_fee TEXT NOT NULL DEFAULT '0'",
            "ALTER TABLE restaurant_sessions ADD COLUMN delivery_status TEXT",
            "ALTER TABLE restaurant_sessions ADD COLUMN driver_id TEXT",
            "ALTER TABLE restaurant_sessions ADD COLUMN promised_at TEXT",
        ):
            try:
                db.execute(ddl)
            except Exception:
                pass
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS restaurant_delivery_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                driver_id TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES restaurant_sessions(id) ON DELETE CASCADE
            );
            """
        )
        db.commit()

    def ensure_virtual_table(self, name: str, branch_id: int | None = None) -> int:
        self.ensure_schema()
        db = get_db()
        row = db.execute('SELECT id FROM restaurant_tables WHERE name=?', (name,)).fetchone()
        if row:
            return int(row['id'])
        now = datetime.datetime.now().isoformat(timespec='seconds')
        cur = db.execute("INSERT INTO restaurant_tables(name, zone, seats, status, is_active, branch_id, created_at, updated_at) VALUES (?, 'Virtual', 1, 'occupied', 1, ?, ?, ?)", (name, branch_id, now, now))
        db.commit()
        return int(cur.lastrowid)

    def create_takeaway_order(self, customer_name: str = '', phone: str = '', notes: str = '', branch_id: int | None = None) -> dict[str, Any]:
        self.ensure_delivery_takeaway_schema()
        db = get_db()
        now = datetime.datetime.now().isoformat(timespec='seconds')
        table_id = self.ensure_virtual_table('Takeaway', branch_id)
        cur = db.execute(
            "INSERT INTO restaurant_sessions(table_id, waiter_id, guests, status, opened_at, branch_id, notes, order_type, customer_name, phone, delivery_status) VALUES (?, NULL, 1, 'open', ?, ?, ?, 'takeaway', ?, ?, 'pending')",
            (table_id, now, branch_id, notes or '', customer_name or '', phone or ''),
        )
        db.commit()
        return self.get_session(int(cur.lastrowid))

    def create_delivery_order(self, customer_name: str = '', phone: str = '', address: str = '', delivery_fee: Any = '0', driver_id: str = '', notes: str = '', branch_id: int | None = None) -> dict[str, Any]:
        self.ensure_delivery_takeaway_schema()
        db = get_db()
        now = datetime.datetime.now().isoformat(timespec='seconds')
        table_id = self.ensure_virtual_table('Delivery', branch_id)
        fee = str(self.decimal_value(delivery_fee, '0'))
        cur = db.execute(
            "INSERT INTO restaurant_sessions(table_id, waiter_id, guests, status, opened_at, branch_id, notes, order_type, customer_name, phone, delivery_address, delivery_fee, delivery_status, driver_id) VALUES (?, NULL, 1, 'open', ?, ?, ?, 'delivery', ?, ?, ?, ?, 'pending', ?)",
            (table_id, now, branch_id, notes or '', customer_name or '', phone or '', address or '', fee, driver_id or ''),
        )
        session_id = int(cur.lastrowid)
        db.execute("INSERT INTO restaurant_delivery_events(session_id, status, driver_id, notes, created_at) VALUES (?, 'pending', ?, ?, ?)", (session_id, driver_id or '', notes or '', now))
        db.commit()
        return self.get_session(session_id)

    def update_delivery_status(self, session_id: int, status: str, driver_id: str = '', notes: str = '') -> dict[str, Any]:
        self.ensure_delivery_takeaway_schema()
        allowed = {'pending', 'accepted', 'preparing', 'ready', 'out_for_delivery', 'delivered', 'cancelled'}
        if status not in allowed:
            raise ValueError('Invalid delivery status')
        db = get_db()
        row = db.execute("SELECT order_type FROM restaurant_sessions WHERE id=?", (int(session_id),)).fetchone()
        if not row:
            raise ValueError('Restaurant session not found')
        if (row['order_type'] or 'dine_in') not in {'delivery', 'takeaway'}:
            raise ValueError('Delivery status is only valid for takeaway/delivery orders')
        now = datetime.datetime.now().isoformat(timespec='seconds')
        db.execute("UPDATE restaurant_sessions SET delivery_status=?, driver_id=COALESCE(NULLIF(?, ''), driver_id) WHERE id=?", (status, driver_id or '', int(session_id)))
        db.execute("INSERT INTO restaurant_delivery_events(session_id, status, driver_id, notes, created_at) VALUES (?, ?, ?, ?, ?)", (int(session_id), status, driver_id or '', notes or '', now))
        db.commit()
        return self.get_session(int(session_id))

    def list_restaurant_orders(self, order_type: str = '', status: str = 'open', limit: int = 100) -> list[dict[str, Any]]:
        self.ensure_delivery_takeaway_schema()
        where = []
        params: list[Any] = []
        if status:
            where.append('s.status=?')
            params.append(status)
        if order_type:
            where.append("COALESCE(s.order_type, 'dine_in')=?")
            params.append(order_type)
        sql_where = ('WHERE ' + ' AND '.join(where)) if where else ''
        params.append(max(1, int(limit or 100)))
        rows = get_db().execute(
            f"SELECT s.*, COALESCE(s.branch_id, t.branch_id) AS branch_id, t.name AS table_name FROM restaurant_sessions s LEFT JOIN restaurant_tables t ON t.id=s.table_id {sql_where} ORDER BY s.id DESC LIMIT ?",
            params,
        ).fetchall()
        return [dict(row) for row in rows]


    # Phase 36: advanced split bill + printer routing
    def ensure_split_printer_schema(self) -> None:
        self.ensure_modifier_recipe_schema()
        db = get_db()
        db.executescript("""
            CREATE TABLE IF NOT EXISTS restaurant_split_bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                guest_label TEXT,
                subtotal TEXT NOT NULL DEFAULT '0',
                paid_amount TEXT NOT NULL DEFAULT '0',
                payment_method TEXT,
                status TEXT NOT NULL DEFAULT 'open',
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES restaurant_sessions(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS restaurant_split_bill_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                split_bill_id INTEGER NOT NULL,
                order_line_id INTEGER NOT NULL,
                quantity TEXT NOT NULL DEFAULT '1',
                amount TEXT NOT NULL DEFAULT '0',
                FOREIGN KEY(split_bill_id) REFERENCES restaurant_split_bills(id) ON DELETE CASCADE,
                FOREIGN KEY(order_line_id) REFERENCES restaurant_order_lines(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS restaurant_printers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                printer_type TEXT NOT NULL DEFAULT 'kitchen',
                device_uri TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS restaurant_station_printers (
                station_id INTEGER PRIMARY KEY,
                printer_id INTEGER NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(printer_id) REFERENCES restaurant_printers(id)
            );
            CREATE TABLE IF NOT EXISTS restaurant_print_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER,
                session_id INTEGER,
                station_id INTEGER,
                printer_id INTEGER,
                job_type TEXT NOT NULL DEFAULT 'kot',
                status TEXT NOT NULL DEFAULT 'queued',
                payload TEXT,
                created_at TEXT NOT NULL,
                printed_at TEXT,
                FOREIGN KEY(ticket_id) REFERENCES kitchen_tickets(id) ON DELETE CASCADE
            );
        """)
        db.commit()

    def create_split_bills(self, session_id: int, splits: list[dict[str, Any]], notes: str = "") -> dict[str, Any]:
        self.ensure_split_printer_schema()
        session = self.get_session(int(session_id))
        if session.get('status') != 'open':
            raise ValueError('Restaurant session must be open to split bill')
        if not splits:
            raise ValueError('At least one split bill is required')
        db = get_db()
        lines = {int(line['id']): line for line in self.list_session_lines(int(session_id)) if (line.get('kitchen_status') or 'new') != 'cancelled'}
        now = datetime.datetime.now().isoformat(timespec='seconds')
        created: list[dict[str, Any]] = []
        seen: set[int] = set()
        for idx, split in enumerate(splits, start=1):
            line_ids = [int(x) for x in (split.get('line_ids') or [])]
            if not line_ids:
                raise ValueError('Each split bill needs at least one order line')
            missing = [line_id for line_id in line_ids if line_id not in lines]
            if missing:
                raise ValueError('Split contains order lines outside this session')
            duplicate = [line_id for line_id in line_ids if line_id in seen]
            if duplicate:
                raise ValueError('Order line cannot be assigned to more than one split bill')
            seen.update(line_ids)
            subtotal = sum((self.decimal_value(lines[line_id].get('line_total') or (self.decimal_value(lines[line_id].get('quantity')) * self.decimal_value(lines[line_id].get('unit_price'))), '0') for line_id in line_ids), Decimal('0'))
            paid = self.decimal_value(split.get('paid_amount'), '0')
            status = 'paid' if paid >= subtotal and subtotal > Decimal('0') else 'open'
            cur = db.execute(
                "INSERT INTO restaurant_split_bills(session_id, guest_label, subtotal, paid_amount, payment_method, status, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (int(session_id), split.get('guest_label') or f'Guest {idx}', str(subtotal), str(paid), split.get('payment_method') or '', status, notes or split.get('notes') or '', now, now),
            )
            split_id = int(cur.lastrowid)
            for line_id in line_ids:
                line = lines[line_id]
                amount = self.decimal_value(line.get('line_total') or (self.decimal_value(line.get('quantity')) * self.decimal_value(line.get('unit_price'))), '0')
                db.execute(
                    "INSERT INTO restaurant_split_bill_lines(split_bill_id, order_line_id, quantity, amount) VALUES (?, ?, ?, ?)",
                    (split_id, line_id, str(line.get('quantity') or '1'), str(amount)),
                )
            if paid > Decimal('0'):
                db.execute(
                    "INSERT INTO restaurant_payments(session_id, amount, payment_method, status, notes, created_at) VALUES (?, ?, ?, 'posted', ?, ?)",
                    (int(session_id), str(paid), split.get('payment_method') or 'split', f"split_bill:{split_id}", now),
                )
            created.append({'id': split_id, 'guest_label': split.get('guest_label') or f'Guest {idx}', 'subtotal': str(subtotal), 'paid_amount': str(paid), 'status': status, 'line_ids': line_ids})
        db.commit()
        return {'session_id': int(session_id), 'split_bills': self.list_split_bills(int(session_id)), 'created': created, 'balance': self.session_balance(int(session_id))}

    def list_split_bills(self, session_id: int) -> list[dict[str, Any]]:
        self.ensure_split_printer_schema()
        db = get_db()
        bills = db.execute("SELECT * FROM restaurant_split_bills WHERE session_id=? ORDER BY id", (int(session_id),)).fetchall()
        payload: list[dict[str, Any]] = []
        for bill in bills:
            item = dict(bill)
            rows = db.execute(
                """
                SELECT sbl.*, rol.item_name, rol.notes, rol.kitchen_status
                FROM restaurant_split_bill_lines sbl
                LEFT JOIN restaurant_order_lines rol ON rol.id=sbl.order_line_id
                WHERE sbl.split_bill_id=? ORDER BY sbl.id
                """,
                (int(item['id']),),
            ).fetchall()
            item['lines'] = [dict(row) for row in rows]
            payload.append(item)
        return payload

    def pay_split_bill(self, split_bill_id: int, amount: Any, payment_method: str = 'cash', notes: str = '') -> dict[str, Any]:
        self.ensure_split_printer_schema()
        db = get_db()
        bill = db.execute("SELECT * FROM restaurant_split_bills WHERE id=?", (int(split_bill_id),)).fetchone()
        if not bill:
            raise ValueError('Split bill not found')
        amount_dec = self.decimal_value(amount, '0')
        if amount_dec <= Decimal('0'):
            raise ValueError('Payment amount must be positive')
        paid = self.decimal_value(bill['paid_amount'], '0') + amount_dec
        subtotal = self.decimal_value(bill['subtotal'], '0')
        status = 'paid' if paid >= subtotal and subtotal > Decimal('0') else 'open'
        now = datetime.datetime.now().isoformat(timespec='seconds')
        db.execute("UPDATE restaurant_split_bills SET paid_amount=?, payment_method=?, status=?, notes=?, updated_at=? WHERE id=?", (str(paid), payment_method or 'cash', status, notes or bill['notes'] or '', now, int(split_bill_id)))
        db.execute("INSERT INTO restaurant_payments(session_id, amount, payment_method, status, notes, created_at) VALUES (?, ?, ?, 'posted', ?, ?)", (int(bill['session_id']), str(amount_dec), payment_method or 'cash', f'split_bill:{int(split_bill_id)} {notes or ""}'.strip(), now))
        db.commit()
        return {'split_bill_id': int(split_bill_id), 'status': status, 'paid_amount': str(paid), 'session_balance': self.session_balance(int(bill['session_id']))}

    def upsert_printer(self, name: str, printer_type: str = 'kitchen', device_uri: str = '', printer_id: int | None = None, is_active: bool = True) -> dict[str, Any]:
        self.ensure_split_printer_schema()
        db = get_db()
        now = datetime.datetime.now().isoformat(timespec='seconds')
        if printer_id:
            db.execute("UPDATE restaurant_printers SET name=?, printer_type=?, device_uri=?, is_active=?, updated_at=? WHERE id=?", (name, printer_type or 'kitchen', device_uri or '', 1 if is_active else 0, now, int(printer_id)))
            new_id = int(printer_id)
        else:
            cur = db.execute("INSERT INTO restaurant_printers(name, printer_type, device_uri, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)", (name, printer_type or 'kitchen', device_uri or '', 1 if is_active else 0, now, now))
            new_id = int(cur.lastrowid)
        db.commit()
        return self.get_printer(new_id)

    def get_printer(self, printer_id: int) -> dict[str, Any]:
        self.ensure_split_printer_schema()
        row = get_db().execute("SELECT * FROM restaurant_printers WHERE id=?", (int(printer_id),)).fetchone()
        if not row:
            raise ValueError('Printer not found')
        return dict(row)

    def list_printers(self, include_inactive: bool = False) -> list[dict[str, Any]]:
        self.ensure_split_printer_schema()
        where = '' if include_inactive else 'WHERE is_active=1'
        rows = get_db().execute(f"SELECT * FROM restaurant_printers {where} ORDER BY printer_type, name").fetchall()
        return [dict(row) for row in rows]

    def assign_station_printer(self, station_id: int, printer_id: int) -> dict[str, Any]:
        self.ensure_split_printer_schema()
        self.get_printer(int(printer_id))
        now = datetime.datetime.now().isoformat(timespec='seconds')
        db = get_db()
        db.execute("INSERT INTO restaurant_station_printers(station_id, printer_id, updated_at) VALUES (?, ?, ?) ON CONFLICT(station_id) DO UPDATE SET printer_id=excluded.printer_id, updated_at=excluded.updated_at", (int(station_id), int(printer_id), now))
        db.commit()
        return {'station_id': int(station_id), 'printer_id': int(printer_id)}

    def queue_ticket_print(self, ticket_id: int, job_type: str = 'kot') -> dict[str, Any]:
        self.ensure_split_printer_schema()
        ticket = self.get_kitchen_ticket(int(ticket_id))
        station_id = ticket.get('station_id')
        db = get_db()
        printer = None
        if station_id:
            printer = db.execute("SELECT p.* FROM restaurant_station_printers sp LEFT JOIN restaurant_printers p ON p.id=sp.printer_id WHERE sp.station_id=? AND p.is_active=1", (int(station_id),)).fetchone()
        if printer is None:
            printer = db.execute("SELECT * FROM restaurant_printers WHERE is_active=1 ORDER BY id LIMIT 1").fetchone()
        now = datetime.datetime.now().isoformat(timespec='seconds')
        cur = db.execute(
            "INSERT INTO restaurant_print_jobs(ticket_id, session_id, station_id, printer_id, job_type, status, payload, created_at) VALUES (?, ?, ?, ?, ?, 'queued', ?, ?)",
            (int(ticket_id), ticket.get('session_id'), station_id, int(printer['id']) if printer else None, job_type or 'kot', str(ticket), now),
        )
        db.commit()
        return {'job_id': int(cur.lastrowid), 'ticket_id': int(ticket_id), 'printer': dict(printer) if printer else None, 'status': 'queued'}

    def mark_print_job_done(self, job_id: int) -> dict[str, Any]:
        self.ensure_split_printer_schema()
        db = get_db()
        row = db.execute("SELECT * FROM restaurant_print_jobs WHERE id=?", (int(job_id),)).fetchone()
        if not row:
            raise ValueError('Print job not found')
        now = datetime.datetime.now().isoformat(timespec='seconds')
        db.execute("UPDATE restaurant_print_jobs SET status='printed', printed_at=? WHERE id=?", (now, int(job_id)))
        if row['ticket_id']:
            db.execute("UPDATE kitchen_tickets SET printed_at=COALESCE(printed_at, ?) WHERE id=?", (now, int(row['ticket_id'])))
        db.commit()
        return dict(db.execute("SELECT * FROM restaurant_print_jobs WHERE id=?", (int(job_id),)).fetchone())



    # ------------------------------------------------------------------
    # Phase 37: restaurant production readiness guardrails
    # ------------------------------------------------------------------
    def restaurant_production_readiness(self) -> dict[str, Any]:
        """Return operational readiness diagnostics for the restaurant vertical.

        This is intentionally read-only. It verifies schema presence, dangling
        workflow references, unpaid/open work, queued print jobs, and pending
        delivery/takeaway orders so production checks can fail before a build is
        shipped with silent restaurant data hazards.
        """
        self.ensure_split_printer_schema()
        self.ensure_modifier_recipe_schema()
        try:
            self.ensure_delivery_takeaway_schema()
        except AttributeError:
            pass
        self.seed_default_tables_if_empty()
        db = get_db()
        required_tables = [
            "restaurant_tables",
            "restaurant_sessions",
            "restaurant_order_lines",
            "kitchen_tickets",
            "kitchen_ticket_lines",
            "restaurant_payments",
            "restaurant_session_adjustments",
            "restaurant_reservations",
            "restaurant_service_events",
            "restaurant_kitchen_stations",
            "restaurant_item_kitchen_stations",
            "restaurant_modifier_groups",
            "restaurant_modifier_options",
            "restaurant_order_line_modifiers",
            "restaurant_recipes",
            "restaurant_recipe_lines",
            "restaurant_inventory_consumption",
            "restaurant_orders",
            "restaurant_delivery_events",
            "restaurant_split_bills",
            "restaurant_split_bill_lines",
            "restaurant_printers",
            "restaurant_station_printers",
            "restaurant_print_jobs",
        ]
        existing = {
            str(row["name"])
            for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'restaurant_%' OR name IN ('kitchen_tickets','kitchen_ticket_lines')"
            ).fetchall()
        }
        missing = [name for name in required_tables if name not in existing]

        def scalar(sql: str, params: tuple[Any, ...] = ()) -> int:
            try:
                row = db.execute(sql, params).fetchone()
                if row is None:
                    return 0
                value = row[0]
                return int(value or 0)
            except Exception:
                return 0

        diagnostics = {
            "missing_tables": missing,
            "dangling_sessions": scalar("""
                SELECT COUNT(*) FROM restaurant_sessions s
                LEFT JOIN restaurant_tables t ON t.id=s.table_id
                WHERE t.id IS NULL
            """),
            "dangling_order_lines": scalar("""
                SELECT COUNT(*) FROM restaurant_order_lines l
                LEFT JOIN restaurant_sessions s ON s.id=l.session_id
                WHERE s.id IS NULL
            """),
            "dangling_kitchen_lines": scalar("""
                SELECT COUNT(*) FROM kitchen_ticket_lines ktl
                LEFT JOIN kitchen_tickets kt ON kt.id=ktl.ticket_id
                LEFT JOIN restaurant_order_lines rol ON rol.id=ktl.order_line_id
                WHERE kt.id IS NULL OR rol.id IS NULL
            """),
            "open_sessions": scalar("SELECT COUNT(*) FROM restaurant_sessions WHERE status='open'"),
            "new_unsent_lines": scalar("SELECT COUNT(*) FROM restaurant_order_lines WHERE COALESCE(kitchen_status, 'new')='new'"),
            "queued_print_jobs": scalar("SELECT COUNT(*) FROM restaurant_print_jobs WHERE status='queued'"),
            "pending_delivery_orders": scalar("SELECT COUNT(*) FROM restaurant_orders WHERE order_type='delivery' AND status NOT IN ('closed','cancelled','delivered')"),
            "pending_takeaway_orders": scalar("SELECT COUNT(*) FROM restaurant_orders WHERE order_type='takeaway' AND status NOT IN ('closed','cancelled','picked_up')"),
        }
        blocking = bool(missing or diagnostics["dangling_sessions"] or diagnostics["dangling_order_lines"] or diagnostics["dangling_kitchen_lines"])
        warnings = []
        if diagnostics["new_unsent_lines"]:
            warnings.append("There are unsent restaurant order lines")
        if diagnostics["queued_print_jobs"]:
            warnings.append("There are queued restaurant print jobs")
        if diagnostics["pending_delivery_orders"] or diagnostics["pending_takeaway_orders"]:
            warnings.append("There are pending delivery/takeaway orders")
        return {
            "ready": not blocking,
            "blocking": blocking,
            "warnings": warnings,
            "diagnostics": diagnostics,
            "required_tables": required_tables,
        }


def get_restaurant_repository() -> RestaurantRepository:
    return RestaurantRepository()
