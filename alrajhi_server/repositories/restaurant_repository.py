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
                notes TEXT,
                kitchen_status TEXT DEFAULT 'new',
                created_at TEXT,
                FOREIGN KEY(session_id) REFERENCES restaurant_sessions(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS kitchen_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
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
                amount TEXT NOT NULL DEFAULT '0',
                payment_method TEXT NOT NULL DEFAULT 'cash',
                status TEXT NOT NULL DEFAULT 'posted',
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES restaurant_sessions(id) ON DELETE CASCADE
            );
            """
        )
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

    def upsert_table(self, name: str, zone: str = "", seats: int = 4, table_id: int | None = None) -> dict[str, Any]:
        self.ensure_schema()
        now = datetime.datetime.now().isoformat(timespec="seconds")
        db = get_db()
        seats = max(1, int(seats or 1))
        if table_id:
            db.execute(
                "UPDATE restaurant_tables SET name=?, zone=?, seats=?, updated_at=? WHERE id=?",
                (name, zone, seats, now, int(table_id)),
            )
            new_id = int(table_id)
        else:
            cur = db.execute(
                "INSERT INTO restaurant_tables(name, zone, seats, status, is_active, created_at, updated_at) VALUES (?, ?, ?, 'free', 1, ?, ?)",
                (name, zone, seats, now, now),
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

    def open_table(self, table_id: int, waiter_id: str | None = None, guests: int = 1, notes: str = "") -> dict[str, Any]:
        self.ensure_schema()
        db = get_db()
        table_id = int(table_id)
        table = db.execute("SELECT id FROM restaurant_tables WHERE id=? AND is_active=1", (table_id,)).fetchone()
        if not table:
            raise ValueError("Restaurant table not found; refresh the table map and try again")
        existing = db.execute(
            "SELECT * FROM restaurant_sessions WHERE table_id=? AND status='open' LIMIT 1", (table_id,)
        ).fetchone()
        if existing:
            return dict(existing)
        now = datetime.datetime.now().isoformat(timespec="seconds")
        cur = db.execute(
            "INSERT INTO restaurant_sessions(table_id, waiter_id, guests, status, opened_at, notes) VALUES (?, ?, ?, 'open', ?, ?)",
            (table_id, waiter_id, max(1, int(guests or 1)), now, notes or ""),
        )
        db.execute("UPDATE restaurant_tables SET status='occupied', updated_at=? WHERE id=?", (now, table_id))
        db.commit()
        return self.get_session(int(cur.lastrowid))

    def get_session(self, session_id: int) -> dict[str, Any]:
        self.ensure_schema()
        row = get_db().execute("""
            SELECT s.*, t.name AS table_name
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
            where.append("(name LIKE ? OR barcode LIKE ?)")
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

    def add_order_line(self, session_id: int, item_id: int | None, item_name: str, quantity: Any = "1", unit_price: Any = "0", notes: str = "") -> dict[str, Any]:
        self.ensure_waiter_workflow_schema()
        now = datetime.datetime.now().isoformat(timespec="seconds")
        cur = get_db().execute(
            "INSERT INTO restaurant_order_lines(session_id, item_id, item_name, quantity, unit_price, notes, kitchen_status, created_at) VALUES (?, ?, ?, ?, ?, ?, 'new', ?)",
            (int(session_id), item_id, item_name, str(quantity), str(unit_price), notes or "", now),
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
                "INSERT INTO kitchen_tickets(session_id, station_id, status, sent_at, notes) VALUES (?, ?, 'sent', ?, ?)",
                (session_id, station_id, now, notes or ""),
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


    def session_total(self, session_id: int) -> Decimal:
        billable = [line for line in self.list_session_lines(int(session_id)) if (line.get("kitchen_status") or "new") != "cancelled"]
        return sum((self.decimal_value(line.get("quantity"), "0") * self.decimal_value(line.get("unit_price"), "0") for line in billable), Decimal("0"))

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
        return {
            "session_id": int(session_id),
            "table_id": session.get("table_id"),
            "table_name": session.get("table_name"),
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
            "INSERT INTO restaurant_payments(session_id, invoice_id, amount, payment_method, status, notes, created_at) VALUES (?, NULL, ?, ?, 'posted', ?, ?)",
            (int(session_id), str(amount_value), payment_method or "cash", notes or "", now),
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
        total = sum((self.decimal_value(line.get("quantity"), "0") * self.decimal_value(line.get("unit_price"), "0") for line in lines), Decimal("0"))
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
            INSERT INTO invoices (user_id, type, date, reference, notes, total, paid, status, workflow_status, original_currency, payment_method)
            VALUES (?, 'sale', ?, ?, ?, ?, ?, 'active', 'POSTED', 'USD', ?)
            """,
            (
                str(user_id or "restaurant"),
                now_date,
                reference,
                f"Restaurant table {session.get('table_name') or session.get('table_id')} / session {session_id}",
                str(total),
                str(paid),
                payment_method or "cash",
            ),
        )
        invoice_id = int(cur.lastrowid)
        if extra_paid > Decimal("0"):
            db.execute(
                "INSERT INTO restaurant_payments(session_id, invoice_id, amount, payment_method, status, notes, created_at) VALUES (?, ?, ?, ?, 'posted', ?, ?)",
                (int(session_id), invoice_id, str(extra_paid), payment_method or "cash", "checkout", now_ts),
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
            SELECT kt.*, s.table_id, t.name AS table_name, st.name AS station_name, st.code AS station_code,
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
            SELECT kt.*, s.table_id, t.name AS table_name, st.name AS station_name, st.code AS station_code
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
            "INSERT INTO restaurant_reservations(table_id, customer_name, phone, guests, reserved_at, status, notes, created_at) VALUES (?, ?, ?, ?, ?, 'reserved', ?, ?)",
            (int(table_id), customer_name or '', phone or '', max(1, int(guests or 1)), reserved_at or now, notes or '', now),
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


def get_restaurant_repository() -> RestaurantRepository:
    return RestaurantRepository()
