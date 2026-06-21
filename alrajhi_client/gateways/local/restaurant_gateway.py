# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from database.connection import DatabaseConnection
from gateways.restaurant_gateway import RestaurantGateway
try:  # normal client runtime where alrajhi_client is on sys.path
    from features.restaurant.restaurant_order_state import (
        db_table_status_for,
        derive_order_state,
        derive_table_state,
        kitchen_state_from_lines,
        line_counts,
    )
    from features.restaurant.kitchen_display_state import ACTIVE_KITCHEN_STATUSES, sort_kitchen_tickets
    from features.restaurant.restaurant_inventory_recipe_policy import (
        MANUFACTURING_BOM_SOURCE,
        RESTAURANT_CONSUME_MOVEMENT_TYPE,
        RESTAURANT_RECIPE_SOURCE,
        consumption_source_key,
        movement_note,
        required_component_quantity,
    )
    from features.restaurant.restaurant_payment_split_policy import (
        cap_payment,
        line_amount,
        normalize_payment_method,
        remaining_amount,
        require_payment_ready,
        split_bill_summary,
        split_status,
    )
except ModuleNotFoundError:  # direct file-load tests or external import paths
    from alrajhi_client.features.restaurant.restaurant_order_state import (
        db_table_status_for,
        derive_order_state,
        derive_table_state,
        kitchen_state_from_lines,
        line_counts,
    )
    from alrajhi_client.features.restaurant.kitchen_display_state import ACTIVE_KITCHEN_STATUSES, sort_kitchen_tickets
    from alrajhi_client.features.restaurant.restaurant_inventory_recipe_policy import (
        MANUFACTURING_BOM_SOURCE,
        RESTAURANT_CONSUME_MOVEMENT_TYPE,
        RESTAURANT_RECIPE_SOURCE,
        consumption_source_key,
        movement_note,
        required_component_quantity,
    )
    from alrajhi_client.features.restaurant.restaurant_payment_split_policy import (
        cap_payment,
        line_amount,
        normalize_payment_method,
        remaining_amount,
        require_payment_ready,
        split_bill_summary,
        split_status,
    )


class LocalRestaurantGateway(RestaurantGateway):
    def is_remote(self) -> bool:
        return False

    """Local SQLite adapter for restaurant tables/sessions/KOT."""

    def __init__(self):
        self.db = DatabaseConnection()

    def _conn(self):
        return self.db.get_connection()

    def _ensure_schema(self) -> None:
        conn = self._conn()
        conn.executescript(
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
            "ALTER TABLE restaurant_sessions ADD COLUMN order_state TEXT",
            "ALTER TABLE restaurant_sessions ADD COLUMN kitchen_state TEXT",
            "ALTER TABLE restaurant_sessions ADD COLUMN payment_state TEXT",
            "ALTER TABLE restaurant_sessions ADD COLUMN last_state_at TEXT",
        ):
            try:
                conn.execute(ddl)
            except Exception:
                pass
        conn.commit()

    def _ensure_delivery_takeaway_schema(self) -> None:
        self._ensure_schema()
        conn = self._conn()
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
                conn.execute(ddl)
            except Exception:
                pass
        conn.executescript(
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
        conn.commit()

    def _seed_default_tables_if_empty(self) -> None:
        """Create a safe default table map before the touch UI can open a table.

        Phase 21 rendered placeholder buttons when the database had no rows.
        Those placeholders emitted ids 1..12 although no restaurant_tables rows
        existed yet, so opening one could violate the restaurant_sessions.table_id
        foreign key. Persisting the default tables at the gateway boundary keeps
        the UI honest and makes first-click operation safe.
        """
        conn = self._conn()
        count = conn.execute("SELECT COUNT(*) AS c FROM restaurant_tables").fetchone()["c"]
        if int(count or 0) > 0:
            return
        now = datetime.datetime.now().isoformat(timespec="seconds")
        for index in range(1, 13):
            conn.execute(
                "INSERT INTO restaurant_tables(name, zone, seats, status, is_active, created_at, updated_at) VALUES (?, ?, 4, 'free', 1, ?, ?)",
                (f"Table {index}", "Main", now, now),
            )
        conn.commit()

    def list_tables(self) -> list[dict[str, Any]]:
        self._ensure_table_operations_schema()
        self._seed_default_tables_if_empty()
        rows = self._conn().execute(
            """
            SELECT t.*, s.id AS active_session_id, s.guests AS active_guests, s.opened_at AS active_opened_at,
                   s.order_state AS active_order_state, s.kitchen_state AS active_kitchen_state,
                   s.payment_state AS active_payment_state
            FROM restaurant_tables t
            LEFT JOIN restaurant_sessions s ON s.table_id=t.id AND s.status='open'
            WHERE t.is_active=1
            ORDER BY COALESCE(t.zone, ''), t.id
            """
        ).fetchall()
        payloads: list[dict[str, Any]] = []
        for row in rows:
            table = dict(row)
            session_id = table.get("active_session_id")
            if session_id:
                state_payload = self._session_state_payload(int(session_id), base_table_status=table.get("status"))
                table.update({
                    "active_order_state": state_payload["order_state"],
                    "active_kitchen_status": state_payload["table_state"],
                    "active_kitchen_state": state_payload["kitchen_state"],
                    "active_total": state_payload["balance"].get("total"),
                    "active_paid": state_payload["balance"].get("paid"),
                    "active_remaining": state_payload["balance"].get("remaining"),
                    "payment_pending": state_payload["table_state"] == "payment",
                    "line_counts": state_payload["line_counts"],
                })
                if state_payload["table_state"] in {"kitchen", "ready", "payment"}:
                    table["ui_status"] = state_payload["table_state"]
                try:
                    opened = datetime.datetime.fromisoformat(str(table.get("active_opened_at") or ""))
                    table["elapsed_minutes"] = max(0, int((datetime.datetime.now() - opened).total_seconds() // 60))
                except Exception:
                    table["elapsed_minutes"] = None
            if not session_id:
                try:
                    reservation = self._active_reservation_for_table(int(table.get("id") or 0))
                    if reservation:
                        res = dict(reservation)
                        table.update({
                            "active_reservation_id": res.get("id"),
                            "active_reservation_customer": res.get("customer_name"),
                            "active_reservation_phone": res.get("phone"),
                            "active_reservation_guests": res.get("guests"),
                            "active_reserved_at": res.get("reserved_at"),
                            "reservation_status": res.get("status"),
                            "ui_status": "reserved",
                        })
                except Exception:
                    pass
            payloads.append(table)
        return payloads

    def _session_balance_payload(self, session_id: int) -> dict[str, Any]:
        total = self._session_total(int(session_id))
        paid = self._session_paid(int(session_id))
        remaining = total - paid
        if remaining < Decimal("0"):
            remaining = Decimal("0")
        return {
            "total": str(total),
            "paid": str(paid),
            "remaining": str(remaining),
            "is_fully_paid": paid >= total and total > Decimal("0"),
        }

    def _session_state_payload(self, session_id: int, base_table_status: Any = "occupied") -> dict[str, Any]:
        session_row = self._conn().execute("SELECT status FROM restaurant_sessions WHERE id=?", (int(session_id),)).fetchone()
        session_status = session_row["status"] if session_row else "closed"
        lines = self._list_session_lines(int(session_id))
        balance = self._session_balance_payload(int(session_id))
        kitchen_state = kitchen_state_from_lines(lines)
        order_state = derive_order_state(lines, balance, session_status=session_status)
        table_state = derive_table_state(lines, balance, session_status=session_status, base_table_status=base_table_status)
        return {
            "session_id": int(session_id),
            "session_status": session_status,
            "kitchen_state": kitchen_state,
            "order_state": order_state,
            "table_state": table_state,
            "db_table_status": db_table_status_for(table_state, base_table_status),
            "balance": balance,
            "line_counts": line_counts(lines),
        }

    def _sync_session_table_state(self, session_id: int, conn=None) -> dict[str, Any]:
        conn = conn or self._conn()
        session = conn.execute("SELECT table_id, status FROM restaurant_sessions WHERE id=?", (int(session_id),)).fetchone()
        if not session:
            return {}
        table = conn.execute("SELECT status FROM restaurant_tables WHERE id=?", (int(session["table_id"]),)).fetchone()
        base_status = table["status"] if table else "occupied"
        state = self._session_state_payload(int(session_id), base_table_status=base_status)
        now = datetime.datetime.now().isoformat(timespec="seconds")
        conn.execute(
            "UPDATE restaurant_sessions SET order_state=?, kitchen_state=?, payment_state=?, last_state_at=? WHERE id=?",
            (state["order_state"], state["kitchen_state"], state["table_state"], now, int(session_id)),
        )
        conn.execute(
            "UPDATE restaurant_tables SET status=?, updated_at=? WHERE id=?",
            (state["db_table_status"], now, int(session["table_id"])),
        )
        return state

    def upsert_table(self, name: str, zone: str = "", seats: int = 4, table_id: int | None = None) -> dict[str, Any]:
        self._ensure_schema()
        now = datetime.datetime.now().isoformat(timespec="seconds")
        conn = self._conn()
        seats = max(1, int(seats or 1))
        if table_id:
            conn.execute("UPDATE restaurant_tables SET name=?, zone=?, seats=?, updated_at=? WHERE id=?", (name, zone, seats, now, int(table_id)))
            new_id = int(table_id)
        else:
            cur = conn.execute(
                "INSERT INTO restaurant_tables(name, zone, seats, status, is_active, created_at, updated_at) VALUES (?, ?, ?, 'free', 1, ?, ?)",
                (name, zone, seats, now, now),
            )
            new_id = int(cur.lastrowid)
        conn.commit()
        return self._get_table(new_id)

    def _get_table(self, table_id: int) -> dict[str, Any]:
        row = self._conn().execute("SELECT * FROM restaurant_tables WHERE id=?", (int(table_id),)).fetchone()
        if not row:
            raise ValueError("Restaurant table not found")
        return dict(row)

    def open_table(self, table_id: int, guests: int = 1, waiter_id: str | None = None, notes: str = "") -> dict[str, Any]:
        self._ensure_table_operations_schema()
        conn = self._conn()
        table_id = int(table_id)
        table = conn.execute("SELECT id FROM restaurant_tables WHERE id=? AND is_active=1", (table_id,)).fetchone()
        if not table:
            raise ValueError("Restaurant table not found; refresh the table map and try again")
        existing = conn.execute("SELECT * FROM restaurant_sessions WHERE table_id=? AND status='open' LIMIT 1", (table_id,)).fetchone()
        if existing:
            return dict(existing)
        now = datetime.datetime.now().isoformat(timespec="seconds")
        cur = conn.execute(
            "INSERT INTO restaurant_sessions(table_id, waiter_id, guests, status, opened_at, notes) VALUES (?, ?, ?, 'open', ?, ?)",
            (table_id, waiter_id, max(1, int(guests or 1)), now, notes or ""),
        )
        session_id = int(cur.lastrowid)
        conn.execute("UPDATE restaurant_tables SET status='occupied', updated_at=? WHERE id=?", (now, table_id))
        self._seat_reserved_table_if_needed(table_id, session_id=session_id, conn=conn)
        self._record_table_operation("open_table", session_id=session_id, target_table_id=table_id, notes=notes or "", conn=conn)
        conn.commit()
        return self.get_session(session_id)

    def get_session(self, session_id: int) -> dict[str, Any]:
        self._ensure_schema()
        row = self._conn().execute("""
            SELECT s.*, t.name AS table_name
            FROM restaurant_sessions s
            LEFT JOIN restaurant_tables t ON t.id=s.table_id
            WHERE s.id=?
            """, (int(session_id),)).fetchone()
        if not row:
            raise ValueError("Restaurant session not found")
        payload = dict(row)
        payload["lines"] = self.list_session_lines(session_id)
        try:
            state = self._session_state_payload(int(session_id), base_table_status="occupied")
            payload["order_state"] = state["order_state"]
            payload["kitchen_state"] = state["kitchen_state"]
            payload["table_state"] = state["table_state"]
            payload["line_counts"] = state["line_counts"]
            payload["payment_pending"] = state["table_state"] == "payment"
        except Exception:
            pass
        return payload

    def add_order_line(
        self,
        session_id: int,
        item_name: str,
        item_id: int | None = None,
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
        self._ensure_waiter_workflow_schema()
        now = datetime.datetime.now().isoformat(timespec="seconds")
        cur = self._conn().execute(
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
        self._conn().execute("UPDATE restaurant_sessions SET modification_count=COALESCE(modification_count, 0)+1, last_activity_at=? WHERE id=?", (now, int(session_id)))
        self._conn().execute("INSERT INTO restaurant_service_events(session_id, event_type, line_id, notes, created_at) VALUES (?, 'order_line_added', ?, ?, ?)", (int(session_id), int(cur.lastrowid), notes or "", now))
        self._sync_session_table_state(int(session_id), self._conn())
        self._conn().commit()
        return self._get_order_line(int(cur.lastrowid))

    def _get_order_line(self, line_id: int) -> dict[str, Any]:
        row = self._conn().execute("SELECT * FROM restaurant_order_lines WHERE id=?", (int(line_id),)).fetchone()
        if not row:
            raise ValueError("Restaurant order line not found")
        return dict(row)

    def _list_session_lines(self, session_id: int) -> list[dict[str, Any]]:
        rows = self._conn().execute("SELECT * FROM restaurant_order_lines WHERE session_id=? ORDER BY id", (int(session_id),)).fetchall()
        return [dict(row) for row in rows]

    def _kitchen_line_notes(self, line: dict[str, Any]) -> str:
        base = str((line or {}).get("notes") or "").strip()
        modifiers = str((line or {}).get("kitchen_modifier_notes") or "").strip()
        if base and modifiers and modifiers not in base:
            return f"{base} | {modifiers}"
        return base or modifiers

    def send_to_kitchen(self, session_id: int, notes: str = "") -> dict[str, Any]:
        self._ensure_kitchen_station_schema()
        conn = self._conn()
        session_id = int(session_id)
        raw_lines = conn.execute("SELECT * FROM restaurant_order_lines WHERE session_id=? AND kitchen_status='new' ORDER BY id", (session_id,)).fetchall()
        if not raw_lines:
            return {"tickets": [], "ticket": None, "lines": [], "message": "no_new_lines"}
        lines = [self.get_order_line(int(row["id"])) for row in raw_lines]
        grouped: dict[int | None, list[dict[str, Any]]] = {}
        station_payloads: dict[int | None, dict[str, Any]] = {}
        for line in lines:
            station = self._station_for_order_line(line)
            station_id = station.get("id")
            grouped.setdefault(station_id, []).append(line)
            station_payloads[station_id] = station
        now = datetime.datetime.now().isoformat(timespec="seconds")
        tickets = []
        for station_id, station_lines in grouped.items():
            cur = conn.execute(
                "INSERT INTO kitchen_tickets(session_id, station_id, status, sent_at, notes) VALUES (?, ?, 'sent', ?, ?)",
                (session_id, station_id, now, notes or ""),
            )
            ticket_id = int(cur.lastrowid)
            for line in station_lines:
                conn.execute(
                    "INSERT INTO kitchen_ticket_lines(ticket_id, order_line_id, station_id, item_name, quantity, notes) VALUES (?, ?, ?, ?, ?, ?)",
                    (ticket_id, int(line["id"]), station_id, line.get("item_name"), line.get("quantity"), self._kitchen_line_notes(line)),
                )
                conn.execute("UPDATE restaurant_order_lines SET kitchen_station_id=?, kitchen_status='sent' WHERE id=?", (station_id, int(line["id"])))
            ticket = conn.execute("SELECT * FROM kitchen_tickets WHERE id=?", (ticket_id,)).fetchone()
            payload = dict(ticket) if ticket else {}
            payload["station"] = station_payloads.get(station_id)
            payload["line_count"] = len(station_lines)
            tickets.append(payload)
        self._sync_session_table_state(session_id, conn)
        conn.commit()
        return {"tickets": tickets, "ticket": tickets[0] if tickets else None, "lines": lines}


    def _status_counts(self, session_id: int) -> dict[str, int]:
        rows = self._conn().execute(
            "SELECT kitchen_status, COUNT(*) AS c FROM restaurant_order_lines WHERE session_id=? GROUP BY kitchen_status",
            (int(session_id),),
        ).fetchall()
        return {str(row["kitchen_status"] or "new"): int(row["c"] or 0) for row in rows}

    def update_line_status(self, line_id: int, status: str) -> dict[str, Any]:
        self._ensure_schema()
        allowed = {"new", "sent", "preparing", "ready", "served", "cancelled"}
        status = str(status or "").strip().lower()
        if status not in allowed:
            raise ValueError("Invalid restaurant line status")
        conn = self._conn()
        line = self._get_order_line(int(line_id))
        conn.execute("UPDATE restaurant_order_lines SET kitchen_status=? WHERE id=?", (status, int(line_id)))
        self._sync_session_table_state(int(line["session_id"]), conn)
        if status == "cancelled":
            session = self.get_session(int(line["session_id"]))
            now_event = datetime.datetime.now().isoformat(timespec="seconds")
            conn.execute("UPDATE restaurant_tables SET status='occupied', updated_at=? WHERE id=?", (now_event, int(session["table_id"])))
            conn.execute("UPDATE restaurant_sessions SET cancelled_line_count=COALESCE(cancelled_line_count, 0)+1, modification_count=COALESCE(modification_count, 0)+1, last_activity_at=? WHERE id=?", (now_event, int(line["session_id"])))
            conn.execute("INSERT INTO restaurant_service_events(session_id, event_type, line_id, notes, created_at) VALUES (?, 'line_cancelled', ?, '', ?)", (int(line["session_id"]), int(line_id), now_event))
        conn.commit()
        return self._get_order_line(int(line_id))

    def mark_payment_pending(self, session_id: int) -> dict[str, Any]:
        self._ensure_schema()
        conn = self._conn()
        session = self.get_session(int(session_id))
        if session.get("status") != "open":
            raise ValueError("Restaurant session is not open")
        counts = self._status_counts(int(session_id))
        total_lines = sum(counts.values())
        if total_lines <= 0:
            raise ValueError("Cannot request payment for an empty table")
        if counts.get("new", 0) > 0:
            raise ValueError("Send new order lines to kitchen before requesting payment")
        now = datetime.datetime.now().isoformat(timespec="seconds")
        conn.execute("UPDATE restaurant_tables SET status='payment', updated_at=? WHERE id=?", (now, int(session["table_id"])))
        self._sync_session_table_state(int(session_id), conn)
        conn.execute("UPDATE restaurant_tables SET status='payment', updated_at=? WHERE id=?", (now, int(session["table_id"])))
        conn.commit()
        updated = self.get_session(int(session_id))
        updated["payment_pending"] = True
        return updated


    def list_menu_items(self, search: str = "", category_id: int | None = None, limit: int = 48) -> list[dict[str, Any]]:
        """Return touch POS menu candidates from the existing item catalog.

        The restaurant UI must not query items directly.  This keeps product
        discovery behind the restaurant gateway while reusing the current ERP
        catalog and prices.
        """
        self._ensure_schema()
        conn = self._conn()
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
            rows = conn.execute(sql, params).fetchall()
        except Exception:
            return []
        return [dict(row) for row in rows]


    def _decimal(self, value: Any, default: str = "0") -> Decimal:
        try:
            return Decimal(str(value if value not in (None, "") else default))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal(default)

    def _current_user_id(self) -> str:
        try:
            from auth.session import UserSession
            user_id = UserSession.get_current_user_id()
            if user_id:
                return str(user_id)
        except Exception:
            pass
        return "restaurant"

    def _next_restaurant_reference(self, conn) -> str:
        prefix = "RST-"
        row = conn.execute("SELECT MAX(reference) AS ref FROM invoices WHERE reference LIKE ?", (prefix + "%",)).fetchone()
        ref = row["ref"] if row else None
        try:
            import re
            match = re.search(r"(\d+)$", str(ref or ""))
            number = int(match.group(1)) + 1 if match else 1
        except Exception:
            number = 1
        return f"{prefix}{number:05d}"



    def _get_session_adjustments(self, session_id: int) -> dict[str, Any]:
        self._ensure_schema()
        row = self._conn().execute(
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
        self._ensure_schema()
        session = self.get_session(int(session_id))
        if session.get("status") != "open":
            raise ValueError("Restaurant session is not open")
        discount = self._decimal(discount_amount, "0")
        service_charge = self._decimal(service_charge_amount, "0")
        tax = self._decimal(tax_amount, "0")
        if min(discount, service_charge, tax) < Decimal("0"):
            raise ValueError("Restaurant adjustments cannot be negative")
        subtotal = self._session_subtotal(int(session_id))
        if discount > subtotal:
            discount = subtotal
        now = datetime.datetime.now().isoformat(timespec="seconds")
        self._conn().execute(
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
        self._sync_session_table_state(int(session_id), self._conn())
        self._conn().commit()
        return self.session_balance(int(session_id))

    def _session_subtotal(self, session_id: int) -> Decimal:
        billable = [line for line in self._list_session_lines(int(session_id)) if (line.get("kitchen_status") or "new") != "cancelled"]
        return sum((self._decimal(line.get("quantity"), "0") * self._decimal(line.get("unit_price"), "0") for line in billable), Decimal("0"))

    def _session_total(self, session_id: int) -> Decimal:
        subtotal = self._session_subtotal(int(session_id))
        adjustments = self._get_session_adjustments(int(session_id))
        discount = self._decimal(adjustments.get("discount_amount"), "0")
        service_charge = self._decimal(adjustments.get("service_charge_amount"), "0")
        tax = self._decimal(adjustments.get("tax_amount"), "0")
        total = subtotal - discount + service_charge + tax
        return total if total > Decimal("0") else Decimal("0")

    def _session_paid(self, session_id: int) -> Decimal:
        rows = self._conn().execute(
            "SELECT amount FROM restaurant_payments WHERE session_id=? AND status='posted'",
            (int(session_id),),
        ).fetchall()
        return sum((self._decimal(row["amount"], "0") for row in rows), Decimal("0"))

    def session_balance(self, session_id: int) -> dict[str, Any]:
        self._ensure_schema()
        session = self.get_session(int(session_id))
        total = self._session_total(int(session_id))
        paid = self._session_paid(int(session_id))
        remaining = total - paid
        if remaining < Decimal("0"):
            remaining = Decimal("0")
        payments = self._conn().execute(
            "SELECT * FROM restaurant_payments WHERE session_id=? ORDER BY id",
            (int(session_id),),
        ).fetchall()
        adjustments = self._get_session_adjustments(int(session_id))
        subtotal = self._session_subtotal(int(session_id))
        split_bills: list[dict[str, Any]] = []
        try:
            split_bills = self.list_split_bills(int(session_id))
        except Exception:
            split_bills = []
        return {
            "session_id": int(session_id),
            "table_id": session.get("table_id"),
            "table_name": session.get("table_name"),
            "subtotal": str(subtotal),
            "discount_amount": str(self._decimal(adjustments.get("discount_amount"), "0")),
            "service_charge_amount": str(self._decimal(adjustments.get("service_charge_amount"), "0")),
            "tax_amount": str(self._decimal(adjustments.get("tax_amount"), "0")),
            "adjustment_notes": adjustments.get("notes") or "",
            "total": str(total),
            "paid": str(paid),
            "remaining": str(remaining),
            "is_fully_paid": paid >= total and total > Decimal("0"),
            "payments": [dict(row) for row in payments],
            "split_bills": split_bills,
            "split_bill_count": len(split_bills),
        }

    def record_payment(self, session_id: int, amount: Any, payment_method: str = "cash", notes: str = "") -> dict[str, Any]:
        self._ensure_schema()
        conn = self._conn()
        session = self.get_session(int(session_id))
        if session.get("status") != "open":
            raise ValueError("Restaurant session is not open")
        require_payment_ready(session.get("lines") or self._list_session_lines(int(session_id)))
        balance = self.session_balance(int(session_id))
        remaining = self._decimal(balance.get("remaining"), "0")
        amount_value = cap_payment(amount, remaining)
        now = datetime.datetime.now().isoformat(timespec="seconds")
        method = normalize_payment_method(payment_method)
        cur = conn.execute(
            "INSERT INTO restaurant_payments(session_id, invoice_id, amount, payment_method, status, notes, created_at) VALUES (?, NULL, ?, ?, 'posted', ?, ?)",
            (int(session_id), str(amount_value), method, notes or "", now),
        )
        self._sync_session_table_state(int(session_id), conn)
        conn.commit()
        payload = self.session_balance(int(session_id))
        payload["payment_id"] = int(cur.lastrowid)
        payload["applied_amount"] = str(amount_value)
        payload["payment_method"] = method
        return payload

    def _checkout_lines(self, session_id: int) -> list[dict[str, Any]]:
        lines = self._list_session_lines(int(session_id))
        require_payment_ready(lines)
        return [line for line in lines if (line.get("kitchen_status") or "new") != "cancelled"]

    def checkout_session(self, session_id: int, paid_amount: Any | None = None, payment_method: str = "cash") -> dict[str, Any]:
        """Convert an open restaurant session into a real sales invoice.

        The restaurant workflow remains separate while ordering is active. This
        method is the commercial closing point: it creates an invoice, links it
        back to the session, marks served lines, and frees the table in one
        transaction.
        """
        self._ensure_schema()
        conn = self._conn()
        session = self.get_session(int(session_id))
        if session.get("status") != "open":
            raise ValueError("Restaurant session is not open")
        billable = self._checkout_lines(int(session_id))
        total = self._session_total(int(session_id))
        adjustments = self._get_session_adjustments(int(session_id))
        existing_paid = self._session_paid(int(session_id))
        extra_paid = self._decimal(paid_amount, "0") if paid_amount is not None else Decimal("0")
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
        reference = self._next_restaurant_reference(conn)
        cur = conn.execute(
            """
            INSERT INTO invoices (user_id, type, date, reference, notes, total, paid, status, workflow_status, original_currency, payment_method)
            VALUES (?, 'sale', ?, ?, ?, ?, ?, 'active', 'POSTED', 'USD', ?)
            """,
            (
                self._current_user_id(),
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
            conn.execute(
                "INSERT INTO restaurant_payments(session_id, invoice_id, amount, payment_method, status, notes, created_at) VALUES (?, ?, ?, ?, 'posted', ?, ?)",
                (int(session_id), invoice_id, str(extra_paid), payment_method or "cash", "checkout", now_ts),
            )
        conn.execute("UPDATE restaurant_payments SET invoice_id=? WHERE session_id=? AND invoice_id IS NULL", (invoice_id, int(session_id)))
        for line in billable:
            quantity = self._decimal(line.get("quantity"), "0")
            unit_price = self._decimal(line.get("unit_price"), "0")
            line_total = quantity * unit_price
            item_id = line.get("item_id")
            conn.execute(
                """
                INSERT INTO invoice_lines (invoice_id, item_id, description, quantity, unit_price, total, unit, quantity_in_base, unit_cost, cost_amount, conversion_factor)
                VALUES (?, ?, ?, ?, ?, ?, '', ?, ?, '0', 1.0)
                """,
                (
                    invoice_id,
                    item_id,
                    line.get("item_name") or "Restaurant item",
                    str(quantity),
                    str(unit_price),
                    str(line_total),
                    str(quantity),
                    str(unit_price),
                ),
            )
        discount = self._decimal(adjustments.get("discount_amount"), "0")
        service_charge = self._decimal(adjustments.get("service_charge_amount"), "0")
        tax = self._decimal(adjustments.get("tax_amount"), "0")
        adjustment_lines = [
            ("Restaurant discount", -discount),
            ("Restaurant service charge", service_charge),
            ("Restaurant tax", tax),
        ]
        for description, amount in adjustment_lines:
            if amount == Decimal("0"):
                continue
            conn.execute(
                """
                INSERT INTO invoice_lines (invoice_id, item_id, description, quantity, unit_price, total, unit, quantity_in_base, unit_cost, cost_amount, conversion_factor)
                VALUES (?, NULL, ?, '1', ?, ?, '', '1', ?, '0', 1.0)
                """,
                (invoice_id, description, str(amount), str(amount), str(amount)),
            )
        conn.execute("UPDATE restaurant_order_lines SET kitchen_status='served' WHERE session_id=? AND kitchen_status IN ('sent','preparing','ready')", (int(session_id),))
        conn.execute("UPDATE restaurant_sessions SET status='closed', closed_at=?, invoice_id=? WHERE id=?", (now_ts, invoice_id, int(session_id)))
        conn.execute("UPDATE restaurant_tables SET status='free', updated_at=? WHERE id=?", (now_ts, int(session["table_id"])))
        conn.commit()
        closed = self.get_session(int(session_id))
        closed["invoice_id"] = invoice_id
        closed["invoice_reference"] = reference
        closed["invoice_total"] = str(total)
        closed["paid_amount"] = str(paid)
        return closed


    def list_kitchen_tickets(self, status: str = "active", limit: int = 50, station_id: int | None = None, order_type: str | None = None) -> list[dict[str, Any]]:
        self._ensure_kitchen_station_schema()
        conn = self._conn()
        limit = max(1, min(int(limit or 50), 200))
        status = str(status or "active").strip().lower()
        order_type_expr = "COALESCE(s.order_type, 'dine_in')" if self._table_has_column("restaurant_sessions", "order_type") else "'dine_in'"
        where = []
        params: list[Any] = []
        if status in {"active", "open", ""}:
            where.append("kt.status IN ({})".format(",".join("?" for _ in ACTIVE_KITCHEN_STATUSES)))
            params.extend(ACTIVE_KITCHEN_STATUSES)
        elif status != "all":
            where.append("kt.status=?")
            params.append(status)
        if station_id is not None:
            where.append("kt.station_id=?")
            params.append(int(station_id))
        if order_type:
            where.append(f"{order_type_expr}=?")
            params.append(str(order_type))
        where_sql = "WHERE " + " AND ".join(where) if where else ""
        # Fetch a little extra, then apply the deterministic KDS sorting policy in Python.
        params.append(min(limit * 3, 200))
        rows = conn.execute(
            f"""
            SELECT kt.*, s.table_id, {order_type_expr} AS order_type, t.name AS table_name, st.name AS station_name, st.code AS station_code,
                   COUNT(ktl.id) AS line_count
            FROM kitchen_tickets kt
            LEFT JOIN restaurant_sessions s ON s.id=kt.session_id
            LEFT JOIN restaurant_tables t ON t.id=s.table_id
            LEFT JOIN restaurant_kitchen_stations st ON st.id=kt.station_id
            LEFT JOIN kitchen_ticket_lines ktl ON ktl.ticket_id=kt.id
            {where_sql}
            GROUP BY kt.id
            ORDER BY COALESCE(kt.sent_at, '') ASC, kt.id ASC
            LIMIT ?
            """,
            params,
        ).fetchall()
        return sort_kitchen_tickets([dict(row) for row in rows])[:limit]



    def get_kitchen_ticket(self, ticket_id: int) -> dict[str, Any]:
        self._ensure_kitchen_station_schema()
        conn = self._conn()
        order_type_expr = "COALESCE(s.order_type, 'dine_in')" if self._table_has_column("restaurant_sessions", "order_type") else "'dine_in'"
        row = conn.execute(
            f"""
            SELECT kt.*, s.table_id, {order_type_expr} AS order_type, t.name AS table_name, st.name AS station_name, st.code AS station_code
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
        lines = conn.execute(
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
        self._ensure_schema()
        allowed = {"sent", "preparing", "ready", "served", "cancelled"}
        status = str(status or "").strip().lower()
        if status not in allowed:
            raise ValueError("Invalid kitchen ticket status")
        conn = self._conn()
        ticket = self.get_kitchen_ticket(int(ticket_id))
        now = datetime.datetime.now().isoformat(timespec="seconds")
        timestamp_column = {"preparing": "preparing_at", "ready": "ready_at", "served": "served_at", "cancelled": "cancelled_at"}.get(status)
        if timestamp_column:
            conn.execute(f"UPDATE kitchen_tickets SET status=?, {timestamp_column}=COALESCE({timestamp_column}, ?) WHERE id=?", (status, now, int(ticket_id)))
        else:
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
        self._sync_session_table_state(int(ticket["session_id"]), conn)
        conn.commit()
        return self.get_kitchen_ticket(int(ticket_id))

    def close_session(self, session_id: int, invoice_id: int | None = None) -> dict[str, Any]:
        # Backward-compatible administrative close used by older tests/plugins.
        # The operational UI uses checkout_session(), which still blocks unpaid
        # tables.  This method only prevents closing while unsent kitchen lines
        # exist, matching the legacy lifecycle guard.
        self._ensure_schema()
        conn = self._conn()
        session = self.get_session(int(session_id))
        if session.get("status") != "open":
            raise ValueError("Restaurant session is not open")
        counts = self._status_counts(int(session_id))
        if counts.get("new", 0) > 0:
            raise ValueError("Cannot close table while new order lines have not been sent to kitchen")
        now = datetime.datetime.now().isoformat(timespec="seconds")
        conn.execute("UPDATE restaurant_order_lines SET kitchen_status='served' WHERE session_id=? AND kitchen_status IN ('sent','preparing','ready')", (int(session_id),))
        conn.execute("UPDATE restaurant_sessions SET status='closed', closed_at=?, invoice_id=? WHERE id=?", (now, invoice_id, int(session_id)))
        conn.execute("UPDATE restaurant_tables SET status='free', updated_at=? WHERE id=?", (now, int(session["table_id"])))
        conn.commit()
        return self.get_session(int(session_id))


    def _ensure_table_operations_schema(self) -> None:
        self._ensure_schema()
        conn = self._conn()
        conn.execute("""
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
                seated_at TEXT,
                FOREIGN KEY(table_id) REFERENCES restaurant_tables(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS restaurant_table_operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT NOT NULL,
                session_id INTEGER,
                source_table_id INTEGER,
                target_table_id INTEGER,
                reservation_id INTEGER,
                line_ids TEXT,
                notes TEXT,
                created_at TEXT NOT NULL
            )
        """)
        for ddl in (
            "ALTER TABLE restaurant_reservations ADD COLUMN seated_at TEXT",
            "ALTER TABLE restaurant_table_operations ADD COLUMN reservation_id INTEGER",
            "ALTER TABLE restaurant_table_operations ADD COLUMN line_ids TEXT",
        ):
            try:
                conn.execute(ddl)
            except Exception:
                pass
        conn.commit()

    def _record_table_operation(self, operation: str, session_id: int | None = None, source_table_id: int | None = None, target_table_id: int | None = None, reservation_id: int | None = None, line_ids: list[int] | None = None, notes: str = "", conn=None) -> None:
        self._ensure_table_operations_schema()
        conn = conn or self._conn()
        now = datetime.datetime.now().isoformat(timespec="seconds")
        conn.execute(
            "INSERT INTO restaurant_table_operations(operation, session_id, source_table_id, target_table_id, reservation_id, line_ids, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (str(operation or "").strip().lower(), session_id, source_table_id, target_table_id, reservation_id, ",".join(str(int(x)) for x in (line_ids or [])), notes or "", now),
        )

    def _active_reservation_for_table(self, table_id: int, conn=None):
        conn = conn or self._conn()
        return conn.execute(
            "SELECT * FROM restaurant_reservations WHERE table_id=? AND status='reserved' ORDER BY reserved_at, id LIMIT 1",
            (int(table_id),),
        ).fetchone()

    def _seat_reserved_table_if_needed(self, table_id: int, session_id: int | None = None, conn=None) -> int | None:
        self._ensure_table_operations_schema()
        conn = conn or self._conn()
        reservation = self._active_reservation_for_table(int(table_id), conn)
        if not reservation:
            return None
        now = datetime.datetime.now().isoformat(timespec="seconds")
        reservation_id = int(reservation["id"])
        conn.execute("UPDATE restaurant_reservations SET status='seated', seated_at=? WHERE id=?", (now, reservation_id))
        self._record_table_operation("seat_reservation", session_id=session_id, target_table_id=int(table_id), reservation_id=reservation_id, notes="reservation seated", conn=conn)
        return reservation_id

    def reserve_table(self, table_id: int, customer_name: str = "", phone: str = "", reserved_at: str = "", guests: int = 1, notes: str = "") -> dict[str, Any]:
        self._ensure_table_operations_schema()
        conn = self._conn()
        self._get_table(int(table_id))
        active = conn.execute("SELECT id FROM restaurant_sessions WHERE table_id=? AND status='open' LIMIT 1", (int(table_id),)).fetchone()
        if active:
            raise ValueError("Cannot reserve an occupied restaurant table")
        existing_reservation = self._active_reservation_for_table(int(table_id), conn)
        if existing_reservation:
            raise ValueError("Restaurant table already has an active reservation")
        now = datetime.datetime.now().isoformat(timespec="seconds")
        cur = conn.execute(
            "INSERT INTO restaurant_reservations(table_id, customer_name, phone, guests, reserved_at, status, notes, created_at) VALUES (?, ?, ?, ?, ?, 'reserved', ?, ?)",
            (int(table_id), customer_name or '', phone or '', max(1, int(guests or 1)), reserved_at or now, notes or '', now),
        )
        reservation_id = int(cur.lastrowid)
        conn.execute("UPDATE restaurant_tables SET status='reserved', updated_at=? WHERE id=?", (now, int(table_id)))
        self._record_table_operation("reserve_table", source_table_id=int(table_id), reservation_id=reservation_id, notes=notes or "", conn=conn)
        conn.commit()
        row = conn.execute("SELECT * FROM restaurant_reservations WHERE id=?", (reservation_id,)).fetchone()
        return dict(row) if row else {}

    def cancel_reservation(self, reservation_id: int) -> dict[str, Any]:
        self._ensure_table_operations_schema()
        conn = self._conn()
        row = conn.execute("SELECT * FROM restaurant_reservations WHERE id=?", (int(reservation_id),)).fetchone()
        if not row:
            raise ValueError("Restaurant reservation not found")
        now = datetime.datetime.now().isoformat(timespec="seconds")
        conn.execute("UPDATE restaurant_reservations SET status='cancelled', cancelled_at=? WHERE id=?", (now, int(reservation_id)))
        active = conn.execute("SELECT id FROM restaurant_sessions WHERE table_id=? AND status='open' LIMIT 1", (int(row['table_id']),)).fetchone()
        if not active:
            conn.execute("UPDATE restaurant_tables SET status='free', updated_at=? WHERE id=?", (now, int(row['table_id'])))
        self._record_table_operation("cancel_reservation", source_table_id=int(row['table_id']), reservation_id=int(reservation_id), conn=conn)
        conn.commit()
        result = conn.execute("SELECT * FROM restaurant_reservations WHERE id=?", (int(reservation_id),)).fetchone()
        return dict(result) if result else {}

    def transfer_session(self, session_id: int, target_table_id: int) -> dict[str, Any]:
        self._ensure_table_operations_schema()
        conn = self._conn()
        session = self.get_session(int(session_id))
        if session.get('status') != 'open':
            raise ValueError("Restaurant session is not open")
        self._get_table(int(target_table_id))
        active_target = conn.execute("SELECT id FROM restaurant_sessions WHERE table_id=? AND status='open' LIMIT 1", (int(target_table_id),)).fetchone()
        if active_target:
            raise ValueError("Target restaurant table is already occupied")
        now = datetime.datetime.now().isoformat(timespec="seconds")
        old_table_id = int(session['table_id'])
        conn.execute("UPDATE restaurant_sessions SET table_id=? WHERE id=?", (int(target_table_id), int(session_id)))
        conn.execute("UPDATE restaurant_tables SET status='free', updated_at=? WHERE id=?", (now, old_table_id))
        conn.execute("UPDATE restaurant_tables SET status='occupied', updated_at=? WHERE id=?", (now, int(target_table_id)))
        self._seat_reserved_table_if_needed(int(target_table_id), session_id=int(session_id), conn=conn)
        self._sync_session_table_state(int(session_id), conn)
        self._record_table_operation("transfer_session", session_id=int(session_id), source_table_id=old_table_id, target_table_id=int(target_table_id), conn=conn)
        conn.commit()
        payload = self.get_session(int(session_id))
        payload['transferred_from_table_id'] = old_table_id
        payload['transferred_to_table_id'] = int(target_table_id)
        return payload

    def merge_sessions(self, source_session_id: int, target_session_id: int) -> dict[str, Any]:
        self._ensure_table_operations_schema()
        if int(source_session_id) == int(target_session_id):
            raise ValueError("Cannot merge a restaurant session into itself")
        conn = self._conn()
        source = self.get_session(int(source_session_id))
        target = self.get_session(int(target_session_id))
        if source.get('status') != 'open' or target.get('status') != 'open':
            raise ValueError("Both restaurant sessions must be open before merge")
        now = datetime.datetime.now().isoformat(timespec="seconds")
        conn.execute("UPDATE restaurant_order_lines SET session_id=? WHERE session_id=?", (int(target_session_id), int(source_session_id)))
        conn.execute("UPDATE kitchen_tickets SET session_id=? WHERE session_id=?", (int(target_session_id), int(source_session_id)))
        conn.execute("UPDATE restaurant_payments SET session_id=? WHERE session_id=?", (int(target_session_id), int(source_session_id)))
        conn.execute("UPDATE restaurant_sessions SET status='merged', closed_at=? WHERE id=?", (now, int(source_session_id)))
        conn.execute("UPDATE restaurant_tables SET status='free', updated_at=? WHERE id=?", (now, int(source['table_id'])))
        conn.execute("UPDATE restaurant_tables SET status='occupied', updated_at=? WHERE id=?", (now, int(target['table_id'])))
        self._sync_session_table_state(int(target_session_id), conn)
        self._record_table_operation("merge_sessions", session_id=int(target_session_id), source_table_id=int(source['table_id']), target_table_id=int(target['table_id']), notes=f"source_session={int(source_session_id)}", conn=conn)
        conn.commit()
        payload = self.get_session(int(target_session_id))
        payload['merged_source_session_id'] = int(source_session_id)
        return payload

    def split_lines_to_table(self, session_id: int, line_ids: list[int], target_table_id: int, guests: int = 1, notes: str = "") -> dict[str, Any]:
        self._ensure_table_operations_schema()
        conn = self._conn()
        source = self.get_session(int(session_id))
        if source.get('status') != 'open':
            raise ValueError("Restaurant session is not open")
        ids = [int(x) for x in (line_ids or [])]
        if not ids:
            raise ValueError("Select at least one restaurant order line to split")
        placeholders = ','.join('?' for _ in ids)
        rows = conn.execute(f"SELECT id FROM restaurant_order_lines WHERE session_id=? AND id IN ({placeholders})", [int(session_id), *ids]).fetchall()
        if len(rows) != len(set(ids)):
            raise ValueError("One or more selected order lines do not belong to this restaurant session")
        active_target = conn.execute("SELECT * FROM restaurant_sessions WHERE table_id=? AND status='open' LIMIT 1", (int(target_table_id),)).fetchone()
        if active_target:
            target_session_id = int(active_target['id'])
        else:
            target_session_id = int(self.open_table(int(target_table_id), guests=max(1, int(guests or 1)), notes=notes or 'split')['id'])
        conn.execute(f"UPDATE restaurant_order_lines SET session_id=? WHERE id IN ({placeholders})", [target_session_id, *ids])
        self._seat_reserved_table_if_needed(int(target_table_id), session_id=target_session_id, conn=conn)
        self._sync_session_table_state(int(session_id), conn)
        self._sync_session_table_state(int(target_session_id), conn)
        self._record_table_operation("split_lines_to_table", session_id=int(session_id), source_table_id=int(source['table_id']), target_table_id=int(target_table_id), line_ids=ids, notes=notes or "", conn=conn)
        conn.commit()
        return {
            'source_session': self.get_session(int(session_id)),
            'target_session': self.get_session(target_session_id),
            'moved_line_ids': ids,
        }

    def _ensure_waiter_workflow_schema(self) -> None:
        self._ensure_table_operations_schema()
        conn = self._conn()
        for ddl in (
            "ALTER TABLE restaurant_sessions ADD COLUMN service_started_at TEXT",
            "ALTER TABLE restaurant_sessions ADD COLUMN last_activity_at TEXT",
            "ALTER TABLE restaurant_sessions ADD COLUMN waiter_call_at TEXT",
            "ALTER TABLE restaurant_sessions ADD COLUMN waiter_call_status TEXT",
            "ALTER TABLE restaurant_sessions ADD COLUMN modification_count INTEGER DEFAULT 0",
            "ALTER TABLE restaurant_sessions ADD COLUMN cancelled_line_count INTEGER DEFAULT 0",
        ):
            try:
                conn.execute(ddl)
            except Exception:
                pass
        conn.execute("""
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
        conn.commit()

    def _record_service_event(self, session_id: int, event_type: str, waiter_id: str | None = None, line_id: int | None = None, notes: str = "") -> None:
        self._ensure_waiter_workflow_schema()
        now = datetime.datetime.now().isoformat(timespec="seconds")
        self._conn().execute(
            "INSERT INTO restaurant_service_events(session_id, event_type, waiter_id, line_id, notes, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (int(session_id), event_type, waiter_id, line_id, notes or "", now),
        )
        self._conn().execute("UPDATE restaurant_sessions SET last_activity_at=? WHERE id=?", (now, int(session_id)))
        self._conn().commit()

    def assign_waiter(self, session_id: int, waiter_id: str, notes: str = "") -> dict[str, Any]:
        self._ensure_waiter_workflow_schema()
        session = self.get_session(int(session_id))
        if session.get("status") != "open":
            raise ValueError("Restaurant session is not open")
        waiter_id = str(waiter_id or "").strip()
        if not waiter_id:
            raise ValueError("Waiter id is required")
        now = datetime.datetime.now().isoformat(timespec="seconds")
        conn = self._conn()
        conn.execute(
            "UPDATE restaurant_sessions SET waiter_id=?, service_started_at=COALESCE(service_started_at, ?), last_activity_at=? WHERE id=?",
            (waiter_id, now, now, int(session_id)),
        )
        conn.execute(
            "INSERT INTO restaurant_service_events(session_id, event_type, waiter_id, notes, created_at) VALUES (?, 'waiter_assigned', ?, ?, ?)",
            (int(session_id), waiter_id, notes or "", now),
        )
        conn.commit()
        return self.get_session(int(session_id))

    def call_waiter(self, session_id: int, notes: str = "") -> dict[str, Any]:
        self._ensure_waiter_workflow_schema()
        session = self.get_session(int(session_id))
        if session.get("status") != "open":
            raise ValueError("Restaurant session is not open")
        now = datetime.datetime.now().isoformat(timespec="seconds")
        conn = self._conn()
        conn.execute(
            "UPDATE restaurant_sessions SET waiter_call_at=?, waiter_call_status='open', last_activity_at=? WHERE id=?",
            (now, now, int(session_id)),
        )
        conn.execute(
            "INSERT INTO restaurant_service_events(session_id, event_type, waiter_id, notes, created_at) VALUES (?, 'waiter_called', ?, ?, ?)",
            (int(session_id), session.get("waiter_id"), notes or "", now),
        )
        conn.commit()
        payload = self.get_session(int(session_id))
        payload["waiter_call_pending"] = True
        return payload

    def resolve_waiter_call(self, session_id: int, notes: str = "") -> dict[str, Any]:
        self._ensure_waiter_workflow_schema()
        session = self.get_session(int(session_id))
        now = datetime.datetime.now().isoformat(timespec="seconds")
        conn = self._conn()
        conn.execute(
            "UPDATE restaurant_sessions SET waiter_call_status='resolved', last_activity_at=? WHERE id=?",
            (now, int(session_id)),
        )
        conn.execute(
            "INSERT INTO restaurant_service_events(session_id, event_type, waiter_id, notes, created_at) VALUES (?, 'waiter_call_resolved', ?, ?, ?)",
            (int(session_id), session.get("waiter_id"), notes or "", now),
        )
        conn.commit()
        return self.get_session(int(session_id))



    def _ensure_kitchen_station_schema(self) -> None:
        self._ensure_waiter_workflow_schema()
        conn = self._conn()
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
            "ALTER TABLE kitchen_tickets ADD COLUMN priority INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE kitchen_tickets ADD COLUMN preparing_at TEXT",
            "ALTER TABLE kitchen_tickets ADD COLUMN ready_at TEXT",
            "ALTER TABLE kitchen_tickets ADD COLUMN served_at TEXT",
            "ALTER TABLE kitchen_tickets ADD COLUMN cancelled_at TEXT",
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
        self._ensure_kitchen_station_schema()
        where = "" if include_inactive else "WHERE is_active=1"
        rows = self._conn().execute(
            f"SELECT * FROM restaurant_kitchen_stations {where} ORDER BY sort_order, id"
        ).fetchall()
        return [dict(row) for row in rows]

    def upsert_kitchen_station(self, name: str, code: str = "", sort_order: int = 0, station_id: int | None = None, is_active: bool = True) -> dict[str, Any]:
        self._ensure_kitchen_station_schema()
        name = str(name or "").strip()
        if not name:
            raise ValueError("Kitchen station name is required")
        code = str(code or name).strip().lower().replace(" ", "_")
        now = datetime.datetime.now().isoformat(timespec="seconds")
        conn = self._conn()
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
        self._ensure_kitchen_station_schema()
        conn = self._conn()
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

    def _station_for_order_line(self, line: dict[str, Any]) -> dict[str, Any]:
        self._ensure_kitchen_station_schema()
        conn = self._conn()
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
        self._ensure_waiter_workflow_schema()
        session = self.get_session(int(session_id))
        rows = self._conn().execute(
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
        self._ensure_kitchen_station_schema()
        self._ensure_waiter_workflow_schema()
        db = self._conn()
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
        total_payments = sum((self._decimal(row["amount"], "0") for row in payment_rows), Decimal("0"))
        by_payment_method: dict[str, Decimal] = {}
        for row in payment_rows:
            method = str(row["payment_method"] or "cash")
            by_payment_method[method] = by_payment_method.get(method, Decimal("0")) + self._decimal(row["amount"], "0")

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



    def restaurant_shift_report(self, start_datetime: str = "", end_datetime: str = "", cashier_id: str = "") -> dict[str, Any]:
        """Return a manager-facing restaurant shift report with close blockers."""
        self._ensure_split_printer_schema()
        db = self._conn()
        start = str(start_datetime or "").strip()
        end = str(end_datetime or "").strip()
        cashier = str(cashier_id or "").strip()

        def _between(column: str, params: list[Any]) -> str:
            clauses: list[str] = []
            if start:
                clauses.append(f"{column} >= ?")
                params.append(start)
            if end:
                clauses.append(f"{column} <= ?")
                params.append(end)
            return (" AND " + " AND ".join(clauses)) if clauses else ""

        session_params: list[Any] = []
        session_filter = _between("s.opened_at", session_params)
        session_rows = db.execute(
            f"""
            SELECT s.*, t.name AS table_name
            FROM restaurant_sessions s
            LEFT JOIN restaurant_tables t ON t.id=s.table_id
            WHERE 1=1 {session_filter}
            ORDER BY s.opened_at, s.id
            """,
            session_params,
        ).fetchall()
        sessions = [dict(row) for row in session_rows]
        total_sessions = len(sessions)
        closed_sessions = sum(1 for row in sessions if str(row.get("status") or "open") == "closed")
        open_sessions_raw = [row for row in sessions if str(row.get("status") or "open") == "open"]

        open_sessions: list[dict[str, Any]] = []
        gross_sales = Decimal("0")
        unpaid_open_balance = Decimal("0")
        unpaid_open_count = 0
        for row in sessions:
            try:
                balance = self.session_balance(int(row["id"]))
            except Exception:
                balance = {"total": "0", "paid": "0", "remaining": "0", "is_fully_paid": False}
            gross_sales += self._decimal(balance.get("total"), "0")
            if str(row.get("status") or "open") == "open":
                remaining = self._decimal(balance.get("remaining"), "0")
                if remaining > Decimal("0"):
                    unpaid_open_balance += remaining
                    unpaid_open_count += 1
                open_sessions.append({
                    "session_id": int(row.get("id") or 0),
                    "table_id": row.get("table_id"),
                    "table_name": row.get("table_name") or "",
                    "waiter_id": row.get("waiter_id") or "",
                    "opened_at": row.get("opened_at") or "",
                    "order_type": row.get("order_type") or "dine_in",
                    "total": str(self._decimal(balance.get("total"), "0")),
                    "paid": str(self._decimal(balance.get("paid"), "0")),
                    "remaining": str(remaining),
                })

        payment_params: list[Any] = []
        payment_filter = _between("created_at", payment_params)
        if cashier:
            payment_filter += " AND COALESCE(notes, '') LIKE ?"
            payment_params.append(f"%{cashier}%")
        payment_rows = db.execute(
            f"SELECT amount, payment_method FROM restaurant_payments WHERE status='posted' {payment_filter}",
            payment_params,
        ).fetchall()
        payment_methods: dict[str, Decimal] = {}
        for row in payment_rows:
            method = str(row["payment_method"] or "cash")
            payment_methods[method] = payment_methods.get(method, Decimal("0")) + self._decimal(row["amount"], "0")
        payments_total = sum(payment_methods.values(), Decimal("0"))

        item_params: list[Any] = []
        item_filter = _between("s.opened_at", item_params)
        item_rows = db.execute(
            f"""
            SELECT l.item_id, l.item_name,
                   SUM(CAST(COALESCE(NULLIF(l.quantity, ''), '0') AS REAL)) AS quantity,
                   SUM(CAST(COALESCE(NULLIF(l.quantity, ''), '0') AS REAL) * CAST(COALESCE(NULLIF(l.unit_price, ''), '0') AS REAL)) AS sales
            FROM restaurant_order_lines l
            JOIN restaurant_sessions s ON s.id=l.session_id
            WHERE COALESCE(l.kitchen_status, 'new') <> 'cancelled' {item_filter}
            GROUP BY l.item_id, l.item_name
            ORDER BY sales DESC, quantity DESC
            LIMIT 10
            """,
            item_params,
        ).fetchall()

        cancel_params: list[Any] = []
        cancel_filter = _between("s.opened_at", cancel_params)
        cancel_row = db.execute(
            f"""
            SELECT COALESCE(SUM(COALESCE(s.cancelled_line_count, 0)), 0) AS cancellations,
                   COALESCE(SUM(COALESCE(s.modification_count, 0)), 0) AS modifications,
                   SUM(CASE WHEN COALESCE(l.kitchen_status, 'new')='cancelled' THEN 1 ELSE 0 END) AS cancelled_lines_by_status
            FROM restaurant_sessions s
            LEFT JOIN restaurant_order_lines l ON l.session_id=s.id
            WHERE 1=1 {cancel_filter}
            """,
            cancel_params,
        ).fetchone()

        def _scalar(sql: str, params: tuple[Any, ...] = ()) -> int:
            try:
                row = db.execute(sql, params).fetchone()
                if row is None:
                    return 0
                return int(row[0] or 0)
            except Exception:
                return 0

        active_kitchen_tickets = _scalar("SELECT COUNT(*) FROM kitchen_tickets WHERE COALESCE(status, 'sent') IN ('sent','preparing','ready')")
        queued_print_jobs = _scalar("SELECT COUNT(*) FROM restaurant_print_jobs WHERE COALESCE(status, 'queued')='queued'")
        controls_values = {
            "open_sessions": len(open_sessions_raw),
            "unpaid_open_sessions": unpaid_open_count,
            "active_kitchen_tickets": active_kitchen_tickets,
            "queued_print_jobs": queued_print_jobs,
        }
        blockers = [key for key, value in controls_values.items() if int(value or 0) > 0]
        return {
            "period": {"start_datetime": start, "end_datetime": end, "cashier_id": cashier},
            "summary": {
                "total_sessions": total_sessions,
                "closed_sessions": closed_sessions,
                "open_sessions": len(open_sessions_raw),
                "gross_sales": str(gross_sales),
                "payments_total": str(payments_total),
                "cash_total": str(payment_methods.get("cash", Decimal("0"))),
                "card_total": str(payment_methods.get("card", Decimal("0"))),
                "unpaid_open_balance": str(unpaid_open_balance),
                "cancellations": int((cancel_row or {})["cancellations"] or 0),
                "modifications": int((cancel_row or {})["modifications"] or 0),
                "cancelled_lines_by_status": int((cancel_row or {})["cancelled_lines_by_status"] or 0),
            },
            "payment_methods": {key: str(value) for key, value in sorted(payment_methods.items())},
            "open_sessions": open_sessions,
            "top_items": [dict(row) for row in item_rows],
            "operational_controls": {**controls_values, "blockers": blockers, "can_close_shift": not blockers},
        }

    def cafe_shift_report(self, start_datetime: str = "", end_datetime: str = "", cashier_id: str = "") -> dict[str, Any]:
        """Return cafe-only shift report without creating a separate cafe engine."""
        self._ensure_split_printer_schema()
        self._ensure_restaurant_inventory_consumption_schema()
        db = self._conn()
        start = str(start_datetime or "").strip()
        end = str(end_datetime or "").strip()
        cashier = str(cashier_id or "").strip()

        def _between(column: str, params: list[Any]) -> str:
            clauses: list[str] = []
            if start:
                clauses.append(f"{column} >= ?")
                params.append(start)
            if end:
                clauses.append(f"{column} <= ?")
                params.append(end)
            return (" AND " + " AND ".join(clauses)) if clauses else ""

        session_params: list[Any] = []
        session_filter = _between("s.opened_at", session_params)
        session_rows = db.execute(
            f"""
            SELECT s.*, t.name AS table_name
            FROM restaurant_sessions s
            LEFT JOIN restaurant_tables t ON t.id=s.table_id
            WHERE COALESCE(s.order_type, 'dine_in')='cafe_quick_order' {session_filter}
            ORDER BY s.opened_at, s.id
            """,
            session_params,
        ).fetchall()
        sessions = [dict(row) for row in session_rows]
        total_orders = len(sessions)
        closed_orders = sum(1 for row in sessions if str(row.get("status") or "open") == "closed")
        open_orders_raw = [row for row in sessions if str(row.get("status") or "open") == "open"]

        open_orders: list[dict[str, Any]] = []
        gross_sales = Decimal("0")
        unpaid_open_balance = Decimal("0")
        unpaid_open_count = 0
        for row in sessions:
            try:
                balance = self.session_balance(int(row["id"]))
            except Exception:
                balance = {"total": "0", "paid": "0", "remaining": "0", "is_fully_paid": False}
            gross_sales += self._decimal(balance.get("total"), "0")
            if str(row.get("status") or "open") == "open":
                remaining = self._decimal(balance.get("remaining"), "0")
                if remaining > Decimal("0"):
                    unpaid_open_balance += remaining
                    unpaid_open_count += 1
                open_orders.append({
                    "session_id": int(row.get("id") or 0),
                    "opened_at": row.get("opened_at") or "",
                    "customer_name": row.get("customer_name") or "",
                    "phone": row.get("phone") or "",
                    "total": str(self._decimal(balance.get("total"), "0")),
                    "paid": str(self._decimal(balance.get("paid"), "0")),
                    "remaining": str(remaining),
                })

        payment_params: list[Any] = []
        payment_filter = _between("p.created_at", payment_params)
        if cashier:
            payment_filter += " AND COALESCE(p.notes, '') LIKE ?"
            payment_params.append(f"%{cashier}%")
        payment_rows = db.execute(
            f"""
            SELECT p.amount, p.payment_method
            FROM restaurant_payments p
            JOIN restaurant_sessions s ON s.id=p.session_id
            WHERE p.status='posted' AND COALESCE(s.order_type, 'dine_in')='cafe_quick_order' {payment_filter}
            """,
            payment_params,
        ).fetchall()
        payment_methods: dict[str, Decimal] = {}
        for row in payment_rows:
            method = str(row["payment_method"] or "cash")
            payment_methods[method] = payment_methods.get(method, Decimal("0")) + self._decimal(row["amount"], "0")
        payments_total = sum(payment_methods.values(), Decimal("0"))

        item_params: list[Any] = []
        item_filter = _between("s.opened_at", item_params)
        top_drinks = db.execute(
            f"""
            SELECT l.item_id, l.item_name,
                   CAST(SUM(CAST(COALESCE(NULLIF(l.quantity, ''), '0') AS REAL)) AS TEXT) AS quantity,
                   CAST(SUM(CAST(COALESCE(NULLIF(l.quantity, ''), '0') AS REAL) * CAST(COALESCE(NULLIF(l.unit_price, ''), '0') AS REAL)) AS TEXT) AS sales
            FROM restaurant_order_lines l
            JOIN restaurant_sessions s ON s.id=l.session_id
            WHERE COALESCE(s.order_type, 'dine_in')='cafe_quick_order'
              AND COALESCE(l.kitchen_status, 'new') <> 'cancelled' {item_filter}
            GROUP BY l.item_id, l.item_name
            ORDER BY CAST(sales AS REAL) DESC, CAST(quantity AS REAL) DESC
            LIMIT 10
            """,
            item_params,
        ).fetchall()

        modifier_params: list[Any] = []
        modifier_filter = _between("s.opened_at", modifier_params)
        top_modifiers = db.execute(
            f"""
            SELECT COALESCE(NULLIF(m.action, ''), 'add') AS action,
                   m.name,
                   CAST(SUM(CAST(COALESCE(NULLIF(m.quantity, ''), '1') AS REAL)) AS TEXT) AS quantity,
                   CAST(SUM(CAST(COALESCE(NULLIF(m.price_delta, ''), '0') AS REAL) * CAST(COALESCE(NULLIF(m.quantity, ''), '1') AS REAL)) AS TEXT) AS sales_delta
            FROM restaurant_order_line_modifiers m
            JOIN restaurant_order_lines l ON l.id=m.line_id
            JOIN restaurant_sessions s ON s.id=l.session_id
            WHERE COALESCE(s.order_type, 'dine_in')='cafe_quick_order'
              AND COALESCE(l.kitchen_status, 'new') <> 'cancelled' {modifier_filter}
            GROUP BY COALESCE(NULLIF(m.action, ''), 'add'), m.name
            ORDER BY SUM(CAST(COALESCE(NULLIF(m.quantity, ''), '1') AS REAL)) DESC, SUM(CAST(COALESCE(NULLIF(m.price_delta, ''), '0') AS REAL) * CAST(COALESCE(NULLIF(m.quantity, ''), '1') AS REAL)) DESC
            LIMIT 12
            """,
            modifier_params,
        ).fetchall()

        consumption_params: list[Any] = []
        consumption_filter = _between("c.created_at", consumption_params)
        consumption_rows = db.execute(
            f"""
            SELECT c.component_item_id, c.component_name, c.unit,
                   CAST(SUM(CAST(COALESCE(NULLIF(c.quantity, ''), '0') AS REAL)) AS TEXT) AS quantity,
                   CAST(SUM(CAST(COALESCE(NULLIF(c.quantity, ''), '0') AS REAL) * CAST(COALESCE(NULLIF(c.unit_cost, ''), '0') AS REAL)) AS TEXT) AS cost_amount
            FROM restaurant_inventory_consumption c
            JOIN restaurant_sessions s ON s.id=c.session_id
            WHERE COALESCE(s.order_type, 'dine_in')='cafe_quick_order' {consumption_filter}
            GROUP BY c.component_item_id, c.component_name, c.unit
            ORDER BY CAST(quantity AS REAL) DESC, c.component_name
            LIMIT 20
            """,
            consumption_params,
        ).fetchall()
        inventory_consumption = [dict(row) for row in consumption_rows]

        low_stock_alerts: list[dict[str, Any]] = []
        if self._table_has_column("items", "reorder_level"):
            consumed_ids = [row.get("component_item_id") for row in inventory_consumption if row.get("component_item_id") not in (None, "")]
            if consumed_ids:
                placeholders = ",".join("?" for _ in consumed_ids)
                try:
                    low_rows = db.execute(
                        f"""
                        SELECT id, name, unit,
                               CAST(COALESCE(NULLIF(quantity, ''), '0') AS TEXT) AS quantity,
                               CAST(COALESCE(NULLIF(reorder_level, ''), '0') AS TEXT) AS reorder_level
                        FROM items
                        WHERE id IN ({placeholders})
                          AND CAST(COALESCE(NULLIF(reorder_level, ''), '0') AS REAL) > 0
                          AND CAST(COALESCE(NULLIF(quantity, ''), '0') AS REAL) <= CAST(COALESCE(NULLIF(reorder_level, ''), '0') AS REAL)
                        ORDER BY name COLLATE NOCASE
                        LIMIT 20
                        """,
                        tuple(int(x) for x in consumed_ids),
                    ).fetchall()
                    low_stock_alerts = [dict(row) for row in low_rows]
                except Exception:
                    low_stock_alerts = []

        cancel_params: list[Any] = []
        cancel_filter = _between("s.opened_at", cancel_params)
        cancel_row = db.execute(
            f"""
            SELECT COALESCE(SUM(COALESCE(s.cancelled_line_count, 0)), 0) AS cancellations,
                   COALESCE(SUM(COALESCE(s.modification_count, 0)), 0) AS modifications,
                   SUM(CASE WHEN COALESCE(l.kitchen_status, 'new')='cancelled' THEN 1 ELSE 0 END) AS cancelled_lines_by_status
            FROM restaurant_sessions s
            LEFT JOIN restaurant_order_lines l ON l.session_id=s.id
            WHERE COALESCE(s.order_type, 'dine_in')='cafe_quick_order' {cancel_filter}
            """,
            cancel_params,
        ).fetchone()

        def _scalar(sql: str, params: tuple[Any, ...] = ()) -> int:
            try:
                row = db.execute(sql, params).fetchone()
                if row is None:
                    return 0
                return int(row[0] or 0)
            except Exception:
                return 0

        active_barista_tickets = _scalar(
            """
            SELECT COUNT(*)
            FROM kitchen_tickets kt
            JOIN restaurant_sessions s ON s.id=kt.session_id
            WHERE COALESCE(s.order_type, 'dine_in')='cafe_quick_order'
              AND COALESCE(kt.status, 'sent') IN ('sent','preparing','ready')
            """
        )
        queued_print_jobs = _scalar(
            """
            SELECT COUNT(*)
            FROM restaurant_print_jobs pj
            JOIN restaurant_sessions s ON s.id=pj.session_id
            WHERE COALESCE(s.order_type, 'dine_in')='cafe_quick_order'
              AND COALESCE(pj.status, 'queued')='queued'
            """
        )
        controls_values = {
            "open_orders": len(open_orders_raw),
            "unpaid_open_orders": unpaid_open_count,
            "active_barista_tickets": active_barista_tickets,
            "queued_print_jobs": queued_print_jobs,
        }
        blockers = [key for key, value in controls_values.items() if int(value or 0) > 0]
        return {
            "period": {"start_datetime": start, "end_datetime": end, "cashier_id": cashier, "order_type": "cafe_quick_order"},
            "summary": {
                "total_orders": total_orders,
                "closed_orders": closed_orders,
                "open_orders": len(open_orders_raw),
                "gross_sales": str(gross_sales),
                "payments_total": str(payments_total),
                "cash_total": str(payment_methods.get("cash", Decimal("0"))),
                "card_total": str(payment_methods.get("card", Decimal("0"))),
                "unpaid_open_balance": str(unpaid_open_balance),
                "cancellations": int((cancel_row or {})["cancellations"] or 0),
                "modifications": int((cancel_row or {})["modifications"] or 0),
                "cancelled_lines_by_status": int((cancel_row or {})["cancelled_lines_by_status"] or 0),
                "low_stock_alerts": len(low_stock_alerts),
            },
            "payment_methods": {key: str(value) for key, value in sorted(payment_methods.items())},
            "open_orders": open_orders,
            "top_drinks": [dict(row) for row in top_drinks],
            "top_modifiers": [dict(row) for row in top_modifiers],
            "inventory_consumption": inventory_consumption,
            "low_stock_alerts": low_stock_alerts,
            "operational_controls": {**controls_values, "blockers": blockers, "can_close_shift": not blockers},
        }




    # Phase 35: takeaway and delivery orders
    def create_takeaway_order(self, customer_name: str = "", phone: str = "", notes: str = "") -> dict[str, Any]:
        self._ensure_delivery_takeaway_schema()
        now = datetime.datetime.now().isoformat(timespec="seconds")
        cur = self._conn().execute(
            "INSERT INTO restaurant_sessions(table_id, waiter_id, guests, status, opened_at, notes, order_type, customer_name, phone, delivery_status) VALUES (?, NULL, 1, 'open', ?, ?, 'takeaway', ?, ?, 'pending')",
            (self._ensure_virtual_table('Takeaway'), now, notes or '', customer_name or '', phone or ''),
        )
        self._conn().commit()
        return self.get_session(int(cur.lastrowid))

    def create_cafe_quick_order(self, customer_name: str = "", phone: str = "", notes: str = "") -> dict[str, Any]:
        self._ensure_delivery_takeaway_schema()
        now = datetime.datetime.now().isoformat(timespec="seconds")
        table_id = self._ensure_virtual_table('Cafe', is_active=False)
        cur = self._conn().execute(
            "INSERT INTO restaurant_sessions(table_id, waiter_id, guests, status, opened_at, notes, order_type, customer_name, phone, delivery_status) VALUES (?, NULL, 1, 'open', ?, ?, 'cafe_quick_order', ?, ?, 'pending')",
            (table_id, now, notes or 'cafe_quick_order', customer_name or '', phone or ''),
        )
        self._conn().commit()
        return self.get_session(int(cur.lastrowid))

    def create_delivery_order(self, customer_name: str = "", phone: str = "", address: str = "", delivery_fee: Any = "0", driver_id: str = "", notes: str = "") -> dict[str, Any]:
        self._ensure_delivery_takeaway_schema()
        now = datetime.datetime.now().isoformat(timespec="seconds")
        cur = self._conn().execute(
            "INSERT INTO restaurant_sessions(table_id, waiter_id, guests, status, opened_at, notes, order_type, customer_name, phone, delivery_address, delivery_fee, delivery_status, driver_id) VALUES (?, NULL, 1, 'open', ?, ?, 'delivery', ?, ?, ?, ?, 'pending', ?)",
            (self._ensure_virtual_table('Delivery'), now, notes or '', customer_name or '', phone or '', address or '', str(delivery_fee or '0'), driver_id or ''),
        )
        sid = int(cur.lastrowid)
        self._conn().execute("INSERT INTO restaurant_delivery_events(session_id, status, driver_id, notes, created_at) VALUES (?, 'pending', ?, ?, ?)", (sid, driver_id or '', notes or '', now))
        self._conn().commit()
        return self.get_session(sid)

    def _ensure_virtual_table(self, name: str, is_active: bool = True) -> int:
        self._ensure_schema()
        row = self._conn().execute("SELECT id FROM restaurant_tables WHERE name=?", (name,)).fetchone()
        if row:
            return int(row['id'])
        now = datetime.datetime.now().isoformat(timespec="seconds")
        cur = self._conn().execute(
            "INSERT INTO restaurant_tables(name, zone, seats, status, is_active, created_at, updated_at) VALUES (?, 'Virtual', 1, 'occupied', ?, ?, ?)",
            (name, 1 if is_active else 0, now, now),
        )
        return int(cur.lastrowid)

    def update_delivery_status(self, session_id: int, status: str, driver_id: str = "", notes: str = "") -> dict[str, Any]:
        self._ensure_delivery_takeaway_schema()
        allowed = {'pending', 'accepted', 'preparing', 'ready', 'out_for_delivery', 'delivered', 'cancelled'}
        if status not in allowed:
            raise ValueError('Invalid delivery status')
        now = datetime.datetime.now().isoformat(timespec="seconds")
        self._conn().execute("UPDATE restaurant_sessions SET delivery_status=?, driver_id=COALESCE(NULLIF(?, ''), driver_id) WHERE id=?", (status, driver_id or '', int(session_id)))
        self._conn().execute("INSERT INTO restaurant_delivery_events(session_id, status, driver_id, notes, created_at) VALUES (?, ?, ?, ?, ?)", (int(session_id), status, driver_id or '', notes or '', now))
        self._conn().commit()
        return self.get_session(int(session_id))

    def list_restaurant_orders(self, order_type: str = "", status: str = "open", limit: int = 100) -> list[dict[str, Any]]:
        self._ensure_delivery_takeaway_schema()
        params = []
        where = []
        if status:
            where.append('s.status=?'); params.append(status)
        if order_type:
            where.append("COALESCE(s.order_type, 'dine_in')=?"); params.append(order_type)
        sql_where = ('WHERE ' + ' AND '.join(where)) if where else ''
        params.append(int(limit or 100))
        rows = self._conn().execute(f"SELECT s.*, t.name AS table_name FROM restaurant_sessions s LEFT JOIN restaurant_tables t ON t.id=s.table_id {sql_where} ORDER BY s.id DESC LIMIT ?", params).fetchall()
        return [dict(row) for row in rows]


    # Phase 34: modifiers + recipe integration
    def _ensure_modifier_recipe_schema(self) -> None:
        self._ensure_kitchen_station_schema()
        conn = self._conn()
        conn.executescript("""
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
        conn.commit()

    def upsert_modifier_group(self, item_id: int | None, name: str, min_selected: int = 0, max_selected: int = 1, is_required: bool = False, group_id: int | None = None) -> dict[str, Any]:
        self._ensure_modifier_recipe_schema()
        name = str(name or '').strip()
        if not name:
            raise ValueError('Modifier group name is required')
        now = datetime.datetime.now().isoformat(timespec='seconds')
        conn = self._conn()
        if group_id:
            conn.execute('UPDATE restaurant_modifier_groups SET item_id=?, name=?, min_selected=?, max_selected=?, is_required=?, updated_at=? WHERE id=?', (item_id, name, int(min_selected or 0), int(max_selected or 1), 1 if is_required else 0, now, int(group_id)))
            new_id = int(group_id)
        else:
            cur = conn.execute('INSERT INTO restaurant_modifier_groups(item_id, name, min_selected, max_selected, is_required, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 1, ?, ?)', (item_id, name, int(min_selected or 0), int(max_selected or 1), 1 if is_required else 0, now, now))
            new_id = int(cur.lastrowid)
        conn.commit()
        return self.get_modifier_group(new_id)

    def get_modifier_group(self, group_id: int) -> dict[str, Any]:
        self._ensure_modifier_recipe_schema()
        row = self._conn().execute('SELECT * FROM restaurant_modifier_groups WHERE id=?', (int(group_id),)).fetchone()
        if not row:
            raise ValueError('Modifier group not found')
        payload = dict(row)
        payload['options'] = self.list_modifier_options(int(group_id))
        return payload

    def list_modifier_groups(self, item_id: int | None = None, include_inactive: bool = False) -> list[dict[str, Any]]:
        self._ensure_modifier_recipe_schema()
        where = [] if include_inactive else ['is_active=1']
        params: list[Any] = []
        if item_id is not None:
            where.append('(item_id=? OR item_id IS NULL)')
            params.append(int(item_id))
        sql_where = 'WHERE ' + ' AND '.join(where) if where else ''
        rows = self._conn().execute(f'SELECT * FROM restaurant_modifier_groups {sql_where} ORDER BY item_id IS NOT NULL DESC, id', params).fetchall()
        result = []
        for row in rows:
            payload = dict(row)
            payload['options'] = self.list_modifier_options(int(row['id']))
            result.append(payload)
        return result

    def upsert_modifier_option(self, group_id: int, name: str, price_delta: Any = '0', item_id: int | None = None, kitchen_label: str = '', is_default: bool = False, option_id: int | None = None) -> dict[str, Any]:
        self._ensure_modifier_recipe_schema()
        name = str(name or '').strip()
        if not name:
            raise ValueError('Modifier option name is required')
        price = self._decimal(price_delta, '0')
        now = datetime.datetime.now().isoformat(timespec='seconds')
        conn = self._conn()
        if option_id:
            conn.execute('UPDATE restaurant_modifier_options SET group_id=?, name=?, price_delta=?, item_id=?, kitchen_label=?, is_default=?, updated_at=? WHERE id=?', (int(group_id), name, str(price), item_id, kitchen_label or name, 1 if is_default else 0, now, int(option_id)))
            new_id = int(option_id)
        else:
            cur = conn.execute('INSERT INTO restaurant_modifier_options(group_id, name, price_delta, item_id, kitchen_label, is_default, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)', (int(group_id), name, str(price), item_id, kitchen_label or name, 1 if is_default else 0, now, now))
            new_id = int(cur.lastrowid)
        conn.commit()
        return self.get_modifier_option(new_id)

    def get_modifier_option(self, option_id: int) -> dict[str, Any]:
        self._ensure_modifier_recipe_schema()
        row = self._conn().execute('SELECT * FROM restaurant_modifier_options WHERE id=?', (int(option_id),)).fetchone()
        if not row:
            raise ValueError('Modifier option not found')
        return dict(row)

    def list_modifier_options(self, group_id: int) -> list[dict[str, Any]]:
        self._ensure_modifier_recipe_schema()
        rows = self._conn().execute('SELECT * FROM restaurant_modifier_options WHERE group_id=? AND is_active=1 ORDER BY id', (int(group_id),)).fetchall()
        return [dict(row) for row in rows]

    def add_order_line_modifier(self, line_id: int, option_id: int | None = None, name: str = '', price_delta: Any = '0', quantity: Any = '1', action: str = 'add', group_id: int | None = None, kitchen_label: str = '') -> dict[str, Any]:
        self._ensure_modifier_recipe_schema()
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
        cur = self._conn().execute('INSERT INTO restaurant_order_line_modifiers(line_id, group_id, option_id, name, price_delta, quantity, action, kitchen_label, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (int(line_id), group_id, option_id, name, str(self._decimal(price_delta, '0')), str(self._decimal(quantity, '1')), action, kitchen_label or name, now))
        self._conn().commit()
        return self.get_order_line_modifier(int(cur.lastrowid))

    def get_order_line_modifier(self, modifier_id: int) -> dict[str, Any]:
        self._ensure_modifier_recipe_schema()
        row = self._conn().execute('SELECT * FROM restaurant_order_line_modifiers WHERE id=?', (int(modifier_id),)).fetchone()
        if not row:
            raise ValueError('Order line modifier not found')
        return dict(row)

    def list_line_modifiers(self, line_id: int) -> list[dict[str, Any]]:
        self._ensure_modifier_recipe_schema()
        rows = self._conn().execute('SELECT * FROM restaurant_order_line_modifiers WHERE line_id=? ORDER BY id', (int(line_id),)).fetchall()
        return [dict(row) for row in rows]

    def _line_modifier_total(self, line_id: int) -> Decimal:
        total = Decimal('0')
        for modifier in self.list_line_modifiers(int(line_id)):
            if (modifier.get('action') or 'add') in {'remove', 'note'}:
                continue
            total += self._decimal(modifier.get('price_delta'), '0') * self._decimal(modifier.get('quantity'), '1')
        return total

    def get_order_line(self, line_id: int) -> dict[str, Any]:
        self._ensure_modifier_recipe_schema()
        row = self._conn().execute('SELECT * FROM restaurant_order_lines WHERE id=?', (int(line_id),)).fetchone()
        if not row:
            raise ValueError('Restaurant order line not found')
        payload = dict(row)
        modifiers = self.list_line_modifiers(int(line_id))
        base = self._decimal(payload.get('quantity'), '0') * self._decimal(payload.get('unit_price'), '0')
        modifier_total = self._line_modifier_total(int(line_id))
        payload['modifiers'] = modifiers
        payload['modifier_total'] = str(modifier_total)
        payload['line_total'] = str(base + modifier_total)
        payload['kitchen_modifier_notes'] = ', '.join([str(m.get('kitchen_label') or m.get('name')) for m in modifiers])
        return payload

    def list_session_lines(self, session_id: int) -> list[dict[str, Any]]:
        self._ensure_modifier_recipe_schema()
        rows = self._conn().execute('SELECT id FROM restaurant_order_lines WHERE session_id=? ORDER BY id', (int(session_id),)).fetchall()
        return [self.get_order_line(int(row['id'])) for row in rows]

    def _session_subtotal(self, session_id: int) -> Decimal:
        billable = [line for line in self.list_session_lines(int(session_id)) if (line.get('kitchen_status') or 'new') != 'cancelled']
        return sum((self._decimal(line.get('line_total'), '0') for line in billable), Decimal('0'))

    def upsert_recipe(self, item_id: int, name: str = '', yield_quantity: Any = '1', lines: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        self._ensure_modifier_recipe_schema()
        conn = self._conn()
        now = datetime.datetime.now().isoformat(timespec='seconds')
        row = conn.execute('SELECT id FROM restaurant_recipes WHERE item_id=?', (int(item_id),)).fetchone()
        if row:
            recipe_id = int(row['id'])
            conn.execute('UPDATE restaurant_recipes SET name=?, yield_quantity=?, is_active=1, updated_at=? WHERE id=?', (name or f'Item {item_id}', str(self._decimal(yield_quantity, '1')), now, recipe_id))
            conn.execute('DELETE FROM restaurant_recipe_lines WHERE recipe_id=?', (recipe_id,))
        else:
            cur = conn.execute('INSERT INTO restaurant_recipes(item_id, name, yield_quantity, is_active, updated_at) VALUES (?, ?, ?, 1, ?)', (int(item_id), name or f'Item {item_id}', str(self._decimal(yield_quantity, '1')), now))
            recipe_id = int(cur.lastrowid)
        for line in lines or []:
            component_name = str(line.get('component_name') or line.get('name') or '').strip()
            if not component_name:
                continue
            conn.execute('INSERT INTO restaurant_recipe_lines(recipe_id, component_item_id, component_name, quantity, unit, unit_cost) VALUES (?, ?, ?, ?, ?, ?)', (recipe_id, line.get('component_item_id'), component_name, str(self._decimal(line.get('quantity'), '0')), line.get('unit') or '', str(self._decimal(line.get('unit_cost'), '0'))))
        conn.commit()
        return self.get_recipe_by_item(int(item_id))

    def get_recipe_by_item(self, item_id: int) -> dict[str, Any]:
        self._ensure_modifier_recipe_schema()
        row = self._conn().execute('SELECT * FROM restaurant_recipes WHERE item_id=? AND is_active=1', (int(item_id),)).fetchone()
        if not row:
            return {'item_id': int(item_id), 'lines': [], 'is_configured': False}
        payload = dict(row)
        rows = self._conn().execute('SELECT * FROM restaurant_recipe_lines WHERE recipe_id=? ORDER BY id', (int(row['id']),)).fetchall()
        payload['lines'] = [dict(line) for line in rows]
        payload['is_configured'] = True
        return payload

    def _table_has_column(self, table_name: str, column_name: str) -> bool:
        try:
            rows = self._conn().execute(f"PRAGMA table_info({table_name})").fetchall()
            return any(str(row["name"]) == column_name for row in rows)
        except Exception:
            return False

    def _table_exists(self, table_name: str) -> bool:
        try:
            row = self._conn().execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            ).fetchone()
            return bool(row)
        except Exception:
            return False

    def _ensure_restaurant_inventory_consumption_schema(self) -> None:
        self._ensure_modifier_recipe_schema()
        conn = self._conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS inventory_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                user_id TEXT,
                movement_type TEXT NOT NULL,
                quantity TEXT NOT NULL DEFAULT '0',
                unit_cost TEXT NOT NULL DEFAULT '0',
                reference_id INTEGER,
                movement_date TEXT
            );
        """)
        for ddl in (
            "ALTER TABLE restaurant_inventory_consumption ADD COLUMN source_type TEXT NOT NULL DEFAULT 'restaurant_recipe'",
            "ALTER TABLE restaurant_inventory_consumption ADD COLUMN movement_id INTEGER",
            "ALTER TABLE restaurant_inventory_consumption ADD COLUMN unit_cost TEXT NOT NULL DEFAULT '0'",
            "ALTER TABLE restaurant_inventory_consumption ADD COLUMN warehouse_id INTEGER",
        ):
            try:
                conn.execute(ddl)
            except Exception:
                pass
        conn.commit()

    def _restaurant_recipe_components_for_line(self, line: dict[str, Any]) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
        """Resolve restaurant-specific recipe first, then manufacturing BOM fallback."""
        item_id = line.get("item_id")
        if not item_id:
            return RESTAURANT_RECIPE_SOURCE, {}, []
        recipe = self.get_recipe_by_item(int(item_id))
        if recipe.get("is_configured") and recipe.get("lines"):
            return RESTAURANT_RECIPE_SOURCE, recipe, [
                {
                    "id": component.get("id"),
                    "component_item_id": component.get("component_item_id"),
                    "component_name": component.get("component_name"),
                    "quantity": component.get("quantity"),
                    "unit": component.get("unit") or "",
                    "unit_cost": component.get("unit_cost") or "0",
                    "conversion_factor": "1",
                    "waste_percent": "0",
                }
                for component in recipe.get("lines") or []
            ]
        bom = self._get_manufacturing_bom_for_restaurant_item(int(item_id))
        if bom.get("is_configured") and bom.get("lines"):
            return MANUFACTURING_BOM_SOURCE, bom, bom.get("lines") or []
        return RESTAURANT_RECIPE_SOURCE, {}, []

    def _get_manufacturing_bom_for_restaurant_item(self, item_id: int) -> dict[str, Any]:
        conn = self._conn()
        if not (self._table_exists("bom") and self._table_exists("bom_lines")):
            return {"item_id": int(item_id), "lines": [], "is_configured": False}
        params: list[Any] = [int(item_id)]
        where = "product_id=?"
        if self._table_has_column("bom", "user_id"):
            where += " AND user_id=?"
            params.append(self._current_user_id())
        try:
            row = conn.execute(f"SELECT * FROM bom WHERE {where} ORDER BY id DESC LIMIT 1", params).fetchone()
        except Exception:
            return {"item_id": int(item_id), "lines": [], "is_configured": False}
        if not row:
            return {"item_id": int(item_id), "lines": [], "is_configured": False}
        bom = dict(row)
        try:
            rows = conn.execute(
                """
                SELECT bl.id, bl.item_id AS component_item_id,
                       COALESCE(i.name, 'Component') AS component_name,
                       bl.quantity, COALESCE(i.unit, '') AS unit,
                       CAST(COALESCE(bl.conversion_factor, 1) AS TEXT) AS conversion_factor,
                       CAST(COALESCE(bl.waste_percent, 0) AS TEXT) AS waste_percent,
                       CAST(COALESCE(i.average_cost, i.purchase_price, 0) AS TEXT) AS unit_cost
                FROM bom_lines bl
                LEFT JOIN items i ON i.id=bl.item_id
                WHERE bl.bom_id=?
                ORDER BY bl.id
                """,
                (int(bom["id"]),),
            ).fetchall()
        except Exception:
            rows = []
        bom["lines"] = [dict(row) for row in rows]
        bom["is_configured"] = bool(bom["lines"])
        return bom

    def _post_restaurant_component_movement(
        self,
        component_item_id: Any,
        quantity: Decimal,
        unit_cost: Any,
        invoice_id: int | None,
        source_type: str,
        session_id: int,
        order_line_id: int,
    ) -> int | None:
        if not component_item_id or quantity <= Decimal("0"):
            return None
        conn = self._conn()
        now = datetime.datetime.now().isoformat(timespec="seconds")
        movement_unit_cost = self._decimal(unit_cost, "0")
        cur = conn.execute(
            """
            INSERT INTO inventory_movements(item_id, user_id, movement_type, quantity, unit_cost, reference_id, movement_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(component_item_id),
                self._current_user_id(),
                RESTAURANT_CONSUME_MOVEMENT_TYPE,
                str(quantity),
                str(movement_unit_cost),
                invoice_id,
                now,
            ),
        )
        # Operational stock remains quantity-column based in this project.  The
        # movement row gives auditability; the direct decrement keeps the current
        # stock view correct even for old databases without opening movements.
        conn.execute(
            "UPDATE items SET quantity = CAST(COALESCE(NULLIF(quantity, ''), '0') AS REAL) - ? WHERE id=?",
            (float(quantity), int(component_item_id)),
        )
        return int(cur.lastrowid)

    def consume_session_recipes(self, session_id: int, invoice_id: int | None = None) -> dict[str, Any]:
        self._ensure_restaurant_inventory_consumption_schema()
        conn = self._conn()
        now = datetime.datetime.now().isoformat(timespec="seconds")
        consumed: list[dict[str, Any]] = []
        skipped_without_recipe = 0
        for line in self.list_session_lines(int(session_id)):
            if (line.get("kitchen_status") or "new") == "cancelled" or not line.get("item_id"):
                continue
            source_type, recipe_payload, components = self._restaurant_recipe_components_for_line(line)
            if not components:
                skipped_without_recipe += 1
                continue
            sold_qty = self._decimal(line.get("base_qty") or line.get("quantity"), "0")
            recipe_yield = recipe_payload.get("yield_quantity") or recipe_payload.get("quantity") or "1"
            for component in components:
                consume_qty = required_component_quantity(
                    sold_qty,
                    component.get("quantity"),
                    recipe_yield,
                    component.get("conversion_factor") or "1",
                    component.get("waste_percent") or "0",
                )
                if consume_qty <= Decimal("0"):
                    continue
                source_key = consumption_source_key(source_type, int(session_id), int(line["id"]), component.get("id"))
                try:
                    cur = conn.execute(
                        """
                        INSERT INTO restaurant_inventory_consumption(
                            session_id, order_line_id, invoice_id, item_id, component_item_id,
                            component_name, quantity, unit, source_key, created_at,
                            source_type, unit_cost
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            int(session_id),
                            int(line["id"]),
                            invoice_id,
                            line.get("item_id"),
                            component.get("component_item_id"),
                            component.get("component_name") or "Component",
                            str(consume_qty),
                            component.get("unit") or "",
                            source_key,
                            now,
                            source_type,
                            str(self._decimal(component.get("unit_cost"), "0")),
                        ),
                    )
                except Exception:
                    continue
                movement_id = self._post_restaurant_component_movement(
                    component.get("component_item_id"),
                    consume_qty,
                    component.get("unit_cost") or "0",
                    invoice_id,
                    source_type,
                    int(session_id),
                    int(line["id"]),
                )
                try:
                    if movement_id:
                        conn.execute("UPDATE restaurant_inventory_consumption SET movement_id=? WHERE id=?", (movement_id, int(cur.lastrowid)))
                except Exception:
                    pass
                consumed.append(
                    {
                        "line_id": int(line["id"]),
                        "item_id": line.get("item_id"),
                        "source_type": source_type,
                        "component_item_id": component.get("component_item_id"),
                        "component_name": component.get("component_name") or "Component",
                        "quantity": str(consume_qty),
                        "unit": component.get("unit") or "",
                        "movement_id": movement_id,
                    }
                )
        conn.commit()
        by_source: dict[str, int] = {}
        for row in consumed:
            by_source[row["source_type"]] = by_source.get(row["source_type"], 0) + 1
        return {
            "session_id": int(session_id),
            "invoice_id": invoice_id,
            "consumed": consumed,
            "count": len(consumed),
            "by_source": by_source,
            "skipped_without_recipe": skipped_without_recipe,
        }

    def checkout_session(self, session_id: int, paid_amount: Any | None = None, payment_method: str = "cash") -> dict[str, Any]:
        self._ensure_modifier_recipe_schema()
        conn = self._conn()
        session = self.get_session(int(session_id))
        if session.get("status") != "open":
            raise ValueError("Restaurant session is not open")
        billable = self._checkout_lines(int(session_id))
        total = self._session_total(int(session_id))
        adjustments = self._get_session_adjustments(int(session_id))
        existing_paid = self._session_paid(int(session_id))
        extra_paid = self._decimal(paid_amount, "0") if paid_amount is not None else Decimal("0")
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
        reference = self._next_restaurant_reference(conn)
        cur = conn.execute(
            """
            INSERT INTO invoices (user_id, type, date, reference, notes, total, paid, status, workflow_status, original_currency, payment_method)
            VALUES (?, 'sale', ?, ?, ?, ?, ?, 'active', 'POSTED', 'USD', ?)
            """,
            (self._current_user_id(), now_date, reference, f"Restaurant table {session.get('table_name') or session.get('table_id')} / session {session_id}", str(total), str(paid), payment_method or "cash"),
        )
        invoice_id = int(cur.lastrowid)
        if extra_paid > Decimal("0"):
            conn.execute(
                "INSERT INTO restaurant_payments(session_id, invoice_id, amount, payment_method, status, notes, created_at) VALUES (?, ?, ?, ?, 'posted', ?, ?)",
                (int(session_id), invoice_id, str(extra_paid), payment_method or "cash", "checkout", now_ts),
            )
        conn.execute("UPDATE restaurant_payments SET invoice_id=? WHERE session_id=? AND invoice_id IS NULL", (invoice_id, int(session_id)))
        for line in billable:
            quantity = self._decimal(line.get("quantity"), "0")
            unit_price = self._decimal(line.get("unit_price"), "0")
            line_total = self._decimal(line.get("line_total"), "0")
            description = line.get("item_name") or "Restaurant item"
            if line.get("modifiers"):
                modifier_text = "; ".join([f"{m.get('action', 'add')} {m.get('name')}" for m in line.get("modifiers") or []])
                description = f"{description} ({modifier_text})"
            conn.execute(
                """
                INSERT INTO invoice_lines (invoice_id, item_id, description, quantity, unit_price, total, unit, quantity_in_base, unit_cost, cost_amount, conversion_factor)
                VALUES (?, ?, ?, ?, ?, ?, '', ?, ?, '0', 1.0)
                """,
                (invoice_id, line.get("item_id"), description, str(quantity), str(unit_price), str(line_total), str(quantity), str(unit_price)),
            )
        discount = self._decimal(adjustments.get("discount_amount"), "0")
        service_charge = self._decimal(adjustments.get("service_charge_amount"), "0")
        tax = self._decimal(adjustments.get("tax_amount"), "0")
        for description, amount in [("Restaurant discount", -discount), ("Restaurant service charge", service_charge), ("Restaurant tax", tax)]:
            if amount == Decimal("0"):
                continue
            conn.execute(
                """
                INSERT INTO invoice_lines (invoice_id, item_id, description, quantity, unit_price, total, unit, quantity_in_base, unit_cost, cost_amount, conversion_factor)
                VALUES (?, NULL, ?, '1', ?, ?, '', '1', ?, '0', 1.0)
                """,
                (invoice_id, description, str(amount), str(amount), str(amount)),
            )
        consumption = self.consume_session_recipes(int(session_id), invoice_id=invoice_id)
        conn.execute("UPDATE restaurant_order_lines SET kitchen_status='served' WHERE session_id=? AND kitchen_status IN ('sent','preparing','ready')", (int(session_id),))
        conn.execute("UPDATE restaurant_sessions SET status='closed', closed_at=?, invoice_id=? WHERE id=?", (now_ts, invoice_id, int(session_id)))
        conn.execute("UPDATE restaurant_tables SET status='free', updated_at=? WHERE id=?", (now_ts, int(session["table_id"])))
        conn.commit()
        closed = self.get_session(int(session_id))
        closed["invoice_id"] = invoice_id
        closed["invoice_reference"] = reference
        closed["invoice_total"] = str(total)
        closed["paid_amount"] = str(paid)
        closed["recipe_consumption"] = consumption
        return closed

    def _checkout_lines(self, session_id: int) -> list[dict[str, Any]]:
        lines = self.list_session_lines(int(session_id))
        billable = [line for line in lines if (line.get("kitchen_status") or "new") != "cancelled"]
        if not billable:
            raise ValueError("Cannot checkout an empty restaurant session")
        if any((line.get("kitchen_status") or "new") == "new" for line in billable):
            raise ValueError("Send new order lines to kitchen before checkout")
        return billable

    # Phase 36: advanced split bill + printer routing
    def _ensure_split_printer_schema(self) -> None:
        self._ensure_modifier_recipe_schema()
        conn = self._conn()
        conn.executescript("""
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
        conn.commit()

    def create_split_bills(self, session_id: int, splits: list[dict[str, Any]], notes: str = "") -> dict[str, Any]:
        self._ensure_split_printer_schema()
        session = self.get_session(int(session_id))
        if session.get('status') != 'open':
            raise ValueError('Restaurant session must be open to split bill')
        require_payment_ready(session.get('lines') or self._list_session_lines(int(session_id)))
        if not splits:
            raise ValueError('At least one split bill is required')
        conn = self._conn()
        lines = {int(line['id']): line for line in self.list_session_lines(int(session_id)) if (line.get('kitchen_status') or 'new') != 'cancelled'}
        existing_rows = conn.execute(
            """SELECT sbl.order_line_id
               FROM restaurant_split_bill_lines sbl
               JOIN restaurant_split_bills sb ON sb.id=sbl.split_bill_id
               WHERE sb.session_id=? AND sb.status IN ('open','paid')""",
            (int(session_id),),
        ).fetchall()
        already_split = {int(row['order_line_id']) for row in existing_rows}
        now = datetime.datetime.now().isoformat(timespec='seconds')
        created: list[dict[str, Any]] = []
        seen: set[int] = set()
        for idx, split in enumerate(splits, start=1):
            line_ids = [int(x) for x in (split.get('line_ids') or [])]
            if not line_ids:
                raise ValueError('Each split bill needs at least one order line')
            if any(line_id not in lines for line_id in line_ids):
                raise ValueError('Split contains order lines outside this session')
            if any(line_id in seen for line_id in line_ids):
                raise ValueError('Order line cannot be assigned twice')
            if any(line_id in already_split for line_id in line_ids):
                raise ValueError('Order line already belongs to an existing split bill')
            seen.update(line_ids)
            subtotal = sum((line_amount(lines[line_id]) for line_id in line_ids), Decimal('0'))
            paid = self._decimal(split.get('paid_amount'), '0')
            if paid < Decimal('0'):
                raise ValueError('Split bill payment cannot be negative')
            if paid > subtotal:
                paid = subtotal
            status = split_status(subtotal, paid)
            method = normalize_payment_method(split.get('payment_method') or ('split' if paid > Decimal('0') else ''))
            cur = conn.execute(
                "INSERT INTO restaurant_split_bills(session_id, guest_label, subtotal, paid_amount, payment_method, status, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (int(session_id), split.get('guest_label') or f'Guest {idx}', str(subtotal), str(paid), method if paid > Decimal('0') else '', status, notes or split.get('notes') or '', now, now),
            )
            split_id = int(cur.lastrowid)
            for line_id in line_ids:
                line = lines[line_id]
                amount = line_amount(line)
                conn.execute(
                    "INSERT INTO restaurant_split_bill_lines(split_bill_id, order_line_id, quantity, amount) VALUES (?, ?, ?, ?)",
                    (split_id, line_id, str(line.get('quantity') or '1'), str(amount)),
                )
            if paid > Decimal('0'):
                conn.execute(
                    "INSERT INTO restaurant_payments(session_id, amount, payment_method, status, notes, created_at) VALUES (?, ?, ?, 'posted', ?, ?)",
                    (int(session_id), str(paid), method or 'split', f'split_bill:{split_id}', now),
                )
            summary = split_bill_summary(subtotal, paid)
            created.append({'id': split_id, 'guest_label': split.get('guest_label') or f'Guest {idx}', 'subtotal': str(subtotal), 'paid_amount': str(paid), 'remaining_amount': summary['remaining_amount'], 'status': status, 'line_ids': line_ids})
        self._sync_session_table_state(int(session_id), conn)
        conn.commit()
        return {'session_id': int(session_id), 'split_bills': self.list_split_bills(int(session_id)), 'created': created, 'balance': self.session_balance(int(session_id))}

    def list_split_bills(self, session_id: int) -> list[dict[str, Any]]:
        self._ensure_split_printer_schema()
        conn = self._conn()
        bills = conn.execute("SELECT * FROM restaurant_split_bills WHERE session_id=? ORDER BY id", (int(session_id),)).fetchall()
        payload = []
        for bill in bills:
            item = dict(bill)
            rows = conn.execute("SELECT sbl.*, rol.item_name, rol.notes, rol.kitchen_status FROM restaurant_split_bill_lines sbl LEFT JOIN restaurant_order_lines rol ON rol.id=sbl.order_line_id WHERE sbl.split_bill_id=? ORDER BY sbl.id", (int(item['id']),)).fetchall()
            item['lines'] = [dict(row) for row in rows]
            item.update(split_bill_summary(item.get('subtotal'), item.get('paid_amount')))
            payload.append(item)
        return payload

    def pay_split_bill(self, split_bill_id: int, amount: Any, payment_method: str = "cash", notes: str = "") -> dict[str, Any]:
        self._ensure_split_printer_schema()
        conn = self._conn()
        bill = conn.execute("SELECT * FROM restaurant_split_bills WHERE id=?", (int(split_bill_id),)).fetchone()
        if not bill:
            raise ValueError('Split bill not found')
        subtotal = self._decimal(bill['subtotal'], '0')
        current_paid = self._decimal(bill['paid_amount'], '0')
        outstanding = remaining_amount(subtotal, current_paid)
        amount_dec = cap_payment(amount, outstanding)
        paid = current_paid + amount_dec
        if paid > subtotal:
            paid = subtotal
        status = split_status(subtotal, paid)
        method = normalize_payment_method(payment_method)
        now = datetime.datetime.now().isoformat(timespec='seconds')
        conn.execute("UPDATE restaurant_split_bills SET paid_amount=?, payment_method=?, status=?, notes=?, updated_at=? WHERE id=?", (str(paid), method, status, notes or bill['notes'] or '', now, int(split_bill_id)))
        conn.execute("INSERT INTO restaurant_payments(session_id, amount, payment_method, status, notes, created_at) VALUES (?, ?, ?, 'posted', ?, ?)", (int(bill['session_id']), str(amount_dec), method, f'split_bill:{int(split_bill_id)} {notes or ""}'.strip(), now))
        self._sync_session_table_state(int(bill['session_id']), conn)
        conn.commit()
        return {'split_bill_id': int(split_bill_id), 'status': status, 'paid_amount': str(paid), 'applied_amount': str(amount_dec), 'remaining_amount': str(remaining_amount(subtotal, paid)), 'session_balance': self.session_balance(int(bill['session_id']))}

    def upsert_printer(self, name: str, printer_type: str = "kitchen", device_uri: str = "", printer_id: int | None = None, is_active: bool = True) -> dict[str, Any]:
        self._ensure_split_printer_schema()
        conn = self._conn()
        now = datetime.datetime.now().isoformat(timespec='seconds')
        if printer_id:
            conn.execute("UPDATE restaurant_printers SET name=?, printer_type=?, device_uri=?, is_active=?, updated_at=? WHERE id=?", (name, printer_type or 'kitchen', device_uri or '', 1 if is_active else 0, now, int(printer_id)))
            new_id = int(printer_id)
        else:
            cur = conn.execute("INSERT INTO restaurant_printers(name, printer_type, device_uri, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)", (name, printer_type or 'kitchen', device_uri or '', 1 if is_active else 0, now, now))
            new_id = int(cur.lastrowid)
        conn.commit()
        return dict(conn.execute("SELECT * FROM restaurant_printers WHERE id=?", (new_id,)).fetchone())

    def list_printers(self, include_inactive: bool = False) -> list[dict[str, Any]]:
        self._ensure_split_printer_schema()
        where = '' if include_inactive else 'WHERE is_active=1'
        rows = self._conn().execute(f"SELECT * FROM restaurant_printers {where} ORDER BY printer_type, name").fetchall()
        return [dict(row) for row in rows]

    def assign_station_printer(self, station_id: int, printer_id: int) -> dict[str, Any]:
        self._ensure_split_printer_schema()
        now = datetime.datetime.now().isoformat(timespec='seconds')
        self._conn().execute("INSERT INTO restaurant_station_printers(station_id, printer_id, updated_at) VALUES (?, ?, ?) ON CONFLICT(station_id) DO UPDATE SET printer_id=excluded.printer_id, updated_at=excluded.updated_at", (int(station_id), int(printer_id), now))
        self._conn().commit()
        return {'station_id': int(station_id), 'printer_id': int(printer_id)}

    def queue_ticket_print(self, ticket_id: int, job_type: str = "kot") -> dict[str, Any]:
        self._ensure_split_printer_schema()
        ticket = self.get_kitchen_ticket(int(ticket_id))
        station_id = ticket.get('station_id')
        conn = self._conn()
        printer = None
        if station_id:
            printer = conn.execute("SELECT p.* FROM restaurant_station_printers sp LEFT JOIN restaurant_printers p ON p.id=sp.printer_id WHERE sp.station_id=? AND p.is_active=1", (int(station_id),)).fetchone()
        if printer is None:
            printer = conn.execute("SELECT * FROM restaurant_printers WHERE is_active=1 ORDER BY id LIMIT 1").fetchone()
        now = datetime.datetime.now().isoformat(timespec='seconds')
        cur = conn.execute("INSERT INTO restaurant_print_jobs(ticket_id, session_id, station_id, printer_id, job_type, status, payload, created_at) VALUES (?, ?, ?, ?, ?, 'queued', ?, ?)", (int(ticket_id), ticket.get('session_id'), station_id, int(printer['id']) if printer else None, job_type or 'kot', str(ticket), now))
        conn.commit()
        return {'job_id': int(cur.lastrowid), 'ticket_id': int(ticket_id), 'printer': dict(printer) if printer else None, 'status': 'queued'}

    def mark_print_job_done(self, job_id: int) -> dict[str, Any]:
        self._ensure_split_printer_schema()
        conn = self._conn()
        row = conn.execute("SELECT * FROM restaurant_print_jobs WHERE id=?", (int(job_id),)).fetchone()
        if not row:
            raise ValueError('Print job not found')
        now = datetime.datetime.now().isoformat(timespec='seconds')
        conn.execute("UPDATE restaurant_print_jobs SET status='printed', printed_at=? WHERE id=?", (now, int(job_id)))
        if row['ticket_id']:
            conn.execute("UPDATE kitchen_tickets SET printed_at=COALESCE(printed_at, ?) WHERE id=?", (now, int(row['ticket_id'])))
        conn.commit()
        return dict(conn.execute("SELECT * FROM restaurant_print_jobs WHERE id=?", (int(job_id),)).fetchone())


    # Phase 37: production readiness diagnostics
    def restaurant_production_readiness(self) -> dict[str, Any]:
        self._ensure_split_printer_schema()
        self._ensure_modifier_recipe_schema()
        try:
            self._ensure_delivery_takeaway_schema()
        except AttributeError:
            pass
        self._seed_default_tables_if_empty()
        conn = self._conn()
        required_tables = [
            "restaurant_tables", "restaurant_sessions", "restaurant_order_lines",
            "kitchen_tickets", "kitchen_ticket_lines", "restaurant_payments",
            "restaurant_session_adjustments", "restaurant_reservations",
            "restaurant_service_events", "restaurant_kitchen_stations",
            "restaurant_menu_station_map", "restaurant_modifier_groups",
            "restaurant_modifier_options", "restaurant_order_line_modifiers",
            "restaurant_recipes", "restaurant_recipe_lines",
            "restaurant_inventory_consumption",
            "restaurant_delivery_events", "restaurant_split_bills",
            "restaurant_split_bill_lines", "restaurant_printers",
            "restaurant_station_printers", "restaurant_print_jobs",
        ]
        existing = {str(row["name"]) for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        missing = [name for name in required_tables if name not in existing]
        def scalar(sql: str) -> int:
            try:
                row = conn.execute(sql).fetchone()
                return int((row[0] if row else 0) or 0)
            except Exception:
                return 0
        diagnostics = {
            "missing_tables": missing,
            "dangling_sessions": scalar("SELECT COUNT(*) FROM restaurant_sessions s LEFT JOIN restaurant_tables t ON t.id=s.table_id WHERE t.id IS NULL"),
            "dangling_order_lines": scalar("SELECT COUNT(*) FROM restaurant_order_lines l LEFT JOIN restaurant_sessions s ON s.id=l.session_id WHERE s.id IS NULL"),
            "dangling_kitchen_lines": scalar("SELECT COUNT(*) FROM kitchen_ticket_lines ktl LEFT JOIN kitchen_tickets kt ON kt.id=ktl.ticket_id LEFT JOIN restaurant_order_lines rol ON rol.id=ktl.order_line_id WHERE kt.id IS NULL OR rol.id IS NULL"),
            "open_sessions": scalar("SELECT COUNT(*) FROM restaurant_sessions WHERE status='open'"),
            "new_unsent_lines": scalar("SELECT COUNT(*) FROM restaurant_order_lines WHERE COALESCE(kitchen_status, 'new')='new'"),
            "queued_print_jobs": scalar("SELECT COUNT(*) FROM restaurant_print_jobs WHERE status='queued'"),
            "pending_delivery_orders": scalar("SELECT COUNT(*) FROM restaurant_sessions WHERE COALESCE(order_type, 'dine_in')='delivery' AND COALESCE(delivery_status, 'pending') NOT IN ('delivered','cancelled') AND status NOT IN ('closed','cancelled')"),
            "pending_takeaway_orders": scalar("SELECT COUNT(*) FROM restaurant_sessions WHERE COALESCE(order_type, 'dine_in')='takeaway' AND COALESCE(delivery_status, 'pending') NOT IN ('picked_up','delivered','cancelled') AND status NOT IN ('closed','cancelled')"),
            "pending_cafe_orders": scalar("SELECT COUNT(*) FROM restaurant_sessions WHERE COALESCE(order_type, 'dine_in')='cafe_quick_order' AND status NOT IN ('closed','cancelled')"),
        }
        blocking = bool(missing or diagnostics["dangling_sessions"] or diagnostics["dangling_order_lines"] or diagnostics["dangling_kitchen_lines"])
        warnings = []
        if diagnostics["new_unsent_lines"]:
            warnings.append("There are unsent restaurant order lines")
        if diagnostics["queued_print_jobs"]:
            warnings.append("There are queued restaurant print jobs")
        if diagnostics["pending_delivery_orders"] or diagnostics["pending_takeaway_orders"]:
            warnings.append("There are pending delivery/takeaway orders")
        if diagnostics.get("pending_cafe_orders"):
            warnings.append("There are pending cafe quick orders")
        return {"ready": not blocking, "blocking": blocking, "warnings": warnings, "diagnostics": diagnostics, "required_tables": required_tables}

