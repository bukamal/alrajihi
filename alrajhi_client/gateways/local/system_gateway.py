# -*- coding: utf-8 -*-
"""Local runtime gateway implementation."""
from __future__ import annotations

from typing import Dict, List

from database.connection import DatabaseConnection
from gateways.system_gateway import SystemGateway


class LocalSystemGateway(SystemGateway):
    def _db(self) -> DatabaseConnection:
        return DatabaseConnection()

    def is_remote(self) -> bool:
        return self._db().is_remote()

    def mode(self) -> str:
        return getattr(self._db(), 'mode', 'local')

    def set_mode(self, mode: str) -> None:
        self._db().mode = mode

    def server_url(self) -> str:
        return getattr(self._db(), 'server_url', '')

    def data_source_label(self) -> str:
        db = self._db()
        if hasattr(db, 'data_source_label'):
            return db.data_source_label()
        return 'Remote API' if db.is_remote() else 'Local SQLite'

    def logout_remote(self) -> None:
        db = self._db()
        if not db.is_remote():
            return
        rest = db.get_rest_client()
        if rest:
            rest.logout()

    def debug_status(self) -> Dict:
        db = self._db()
        if db.is_remote() and db.get_rest_client():
            status = db.get_rest_client().debug_status()
            status['_mode'] = 'remote'
            return status
        if db.is_remote():
            return {'_mode': 'remote', 'error': 'no_rest_client'}
        return {'_mode': 'local', 'db_path': 'محلي SQLite', 'counts': {}}

    def request_log(self) -> List[Dict]:
        try:
            from database.connection_rest import get_request_log
            return get_request_log()
        except Exception:
            return []



    def _scalar(self, conn, sql, params=()):
        try:
            row = conn.execute(sql, params).fetchone()
            return row[0] if row else 0
        except Exception as exc:
            return f'ERROR: {exc}'

    def _table_exists(self, conn, table: str) -> bool:
        try:
            return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None
        except Exception:
            return False

    def integrity_checks(self) -> Dict[str, object]:
        db = self._db()
        if db.is_remote():
            return {'mode': 'remote', 'checks': [], 'risk_count': 0, 'summary': 'Remote diagnostics are limited to server debug status.'}
        conn = db.get_connection()
        checks = []
        scalar = lambda sql, params=(): self._scalar(conn, sql, params)
        checks.append({'code': 'negative_items_stock', 'label': 'مواد بمخزون سالب', 'value': scalar("SELECT COUNT(*) FROM items WHERE CAST(COALESCE(quantity,'0') AS REAL) < 0")})
        checks.append({'code': 'negative_warehouse_stock', 'label': 'أرصدة مستودعات سالبة', 'value': scalar("SELECT COUNT(*) FROM item_warehouse_balances WHERE CAST(COALESCE(quantity,'0') AS REAL) < 0")})
        checks.append({'code': 'invoices_without_lines', 'label': 'فواتير بلا أسطر', 'value': scalar("SELECT COUNT(*) FROM (SELECT i.id FROM invoices i LEFT JOIN invoice_lines l ON l.invoice_id=i.id WHERE i.deleted_at IS NULL GROUP BY i.id HAVING COUNT(l.id)=0)")})
        checks.append({'code': 'orphan_invoice_lines', 'label': 'أسطر فواتير بلا فاتورة', 'value': scalar("SELECT COUNT(*) FROM invoice_lines l LEFT JOIN invoices i ON i.id=l.invoice_id WHERE i.id IS NULL")})
        checks.append({'code': 'missing_invoice_customers', 'label': 'فواتير بيع بعميل مفقود', 'value': scalar("SELECT COUNT(*) FROM invoices i LEFT JOIN customers c ON c.id=i.customer_id WHERE i.type='sale' AND i.customer_id IS NOT NULL AND c.id IS NULL")})
        checks.append({'code': 'missing_invoice_suppliers', 'label': 'فواتير شراء بمورد مفقود', 'value': scalar("SELECT COUNT(*) FROM invoices i LEFT JOIN suppliers s ON s.id=i.supplier_id WHERE i.type='purchase' AND i.supplier_id IS NOT NULL AND s.id IS NULL")})
        checks.append({'code': 'broken_bom_components', 'label': 'مكونات BOM مكسورة', 'value': scalar("SELECT COUNT(*) FROM bom_components bc LEFT JOIN items i ON i.id=bc.component_item_id WHERE i.id IS NULL")})
        checks.append({'code': 'settings_audit_rows', 'label': 'سجل تغييرات الإعدادات', 'value': scalar("SELECT COUNT(*) FROM settings_audit")})
        checks.append({'code': 'security_denied_events', 'label': 'عمليات مرفوضة بالصلاحيات', 'value': scalar("SELECT COUNT(*) FROM security_events WHERE allowed=0")})
        for code, label, sql in [
            ('approval_pending_count', 'طلبات اعتماد معلقة', "SELECT COUNT(*) FROM approval_requests WHERE status='PENDING'"),
            ('journal_entries_count', 'القيود اليومية', "SELECT COUNT(*) FROM journal_entries"),
            ('unposted_accounting_invoices', 'فواتير مرحلة بلا قيد محاسبي', "SELECT COUNT(*) FROM invoices i WHERE COALESCE(i.workflow_status,'DRAFT')='POSTED' AND i.deleted_at IS NULL AND NOT EXISTS (SELECT 1 FROM journal_entries j WHERE j.source_type='INVOICE' AND j.source_id=i.id)"),
        ]:
            checks.append({'code': code, 'label': label, 'value': scalar(sql)})
        checks.append({'code': 'branches_count', 'label': 'عدد الفروع النشطة', 'value': scalar("SELECT COUNT(*) FROM branches WHERE deleted_at IS NULL AND COALESCE(is_active,1)=1")})
        checks.append({'code': 'warehouses_without_branch', 'label': 'مستودعات بلا فرع', 'value': scalar("SELECT COUNT(*) FROM warehouses WHERE deleted_at IS NULL AND branch_id IS NULL")})
        checks.append({'code': 'invoices_without_branch', 'label': 'فواتير بلا فرع', 'value': scalar("SELECT COUNT(*) FROM invoices WHERE deleted_at IS NULL AND branch_id IS NULL")})
        checks.append({'code': 'returns_without_branch', 'label': 'مرتجعات بلا فرع', 'value': scalar("SELECT (SELECT COUNT(*) FROM sales_returns WHERE branch_id IS NULL) + (SELECT COUNT(*) FROM purchase_returns WHERE branch_id IS NULL)")})
        checks.append({'code': 'sqlite_quick_check', 'label': 'SQLite quick_check', 'value': scalar('PRAGMA quick_check')})
        risk_count = sum(1 for c in checks if c.get('code') != 'sqlite_quick_check' and isinstance(c.get('value'), int) and c.get('value', 0) > 0)
        quick = next((c.get('value') for c in checks if c.get('code') == 'sqlite_quick_check'), None)
        if quick not in (None, 'ok'):
            risk_count += 1
        return {'mode': 'local', 'checks': checks, 'risk_count': risk_count, 'summary': f'{risk_count} risk indicators'}

    def local_diagnostics_snapshot(self) -> Dict[str, object]:
        import os
        db = self._db()
        snapshot = {'mode': 'remote' if db.is_remote() else 'local', 'table_counts': {}, 'required_tables': {}, 'consistency': {}, 'db_path': None, 'db_size_mb': None}
        if db.is_remote():
            snapshot['remote_status'] = self.debug_status()
            return snapshot
        conn = db.get_connection()
        try:
            db_path = conn.execute('PRAGMA database_list').fetchone()[2]
            snapshot['db_path'] = db_path
            if db_path and os.path.exists(db_path):
                snapshot['db_size_mb'] = round(os.path.getsize(db_path) / (1024 * 1024), 2)
        except Exception as exc:
            snapshot['db_path_error'] = str(exc)
        table_map = [
            ('customers', 'عدد العملاء'), ('suppliers', 'عدد الموردين'), ('items', 'عدد المواد'),
            ('invoices', 'عدد الفواتير'), ('purchase_invoices', 'عدد فواتير الشراء'),
            ('sales_returns', 'عدد مرتجعات المبيعات'), ('purchase_returns', 'عدد مرتجعات الشراء'),
            ('production_orders', 'عدد أوامر التصنيع'), ('branches', 'عدد الفروع'), ('warehouses', 'عدد المستودعات'), ('settings', 'عدد الإعدادات'),
        ]
        for table, label in table_map:
            snapshot['table_counts'][table] = {'label': label, 'value': self._scalar(conn, f'SELECT COUNT(*) FROM {table}')}
        try:
            existing = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        except Exception:
            existing = set()
        for table in ['settings', 'items', 'customers', 'suppliers', 'invoices', 'inventory_ledger', 'audit_log']:
            snapshot['required_tables'][table] = table in existing
        snapshot['consistency']['negative_items_stock'] = self._scalar(conn, "SELECT COUNT(*) FROM items WHERE CAST(COALESCE(quantity, '0') AS REAL) < 0")
        snapshot['consistency']['orphan_invoice_lines'] = self._scalar(conn, "SELECT COUNT(*) FROM invoice_lines ii LEFT JOIN invoices i ON i.id = ii.invoice_id WHERE i.id IS NULL")
        snapshot['consistency']['sqlite_quick_check'] = self._scalar(conn, 'PRAGMA quick_check')
        return snapshot



    def _ensure_security_event_table(self, conn) -> None:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                action TEXT,
                role TEXT,
                username TEXT,
                allowed INTEGER NOT NULL DEFAULT 0,
                reason TEXT,
                context TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_security_events_time ON security_events(created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_security_events_action ON security_events(action, role)")

    def log_security_event(self, event_type: str, action: str = '', allowed: bool = False, reason: str = '', context: str = '', role: str | None = None, username: str = '') -> None:
        try:
            from datetime import datetime
            db = self._db()
            if db.is_remote():
                return
            conn = db.get_connection()
            self._ensure_security_event_table(conn)
            conn.execute("""
                INSERT INTO security_events(event_type, action, role, username, allowed, reason, context, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(event_type or 'SECURITY'), str(action or ''), str(role or ''),
                  str(username or ''), 1 if allowed else 0, str(reason or ''), str(context or ''),
                  datetime.now().isoformat(timespec='seconds')))
            conn.commit()
        except Exception:
            pass

    def security_events(self, limit: int = 200) -> List[Dict]:
        try:
            db = self._db()
            if db.is_remote():
                return []
            conn = db.get_connection()
            self._ensure_security_event_table(conn)
            rows = conn.execute("SELECT * FROM security_events ORDER BY id DESC LIMIT ?", (int(limit or 200),)).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def denied_security_events_count(self) -> int:
        try:
            db = self._db()
            if db.is_remote():
                return 0
            conn = db.get_connection()
            self._ensure_security_event_table(conn)
            return int(conn.execute("SELECT COUNT(*) FROM security_events WHERE allowed=0").fetchone()[0])
        except Exception:
            return 0

    def run_health_checks(self) -> Dict[str, object]:
        """Run local enterprise health checks behind the system gateway boundary."""
        from datetime import datetime
        import json
        db = self._db()
        if db.is_remote():
            return {'overall': 'UNKNOWN', 'checks': [{'key':'database','status':'UNKNOWN','message':'Remote mode'}]}
        conn = db.get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS system_health_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_key TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                details TEXT,
                checked_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        checks = []

        def add(key, status, message, details=None):
            checks.append({'key': key, 'status': status, 'message': message, 'details': details or {}})
            try:
                conn.execute(
                    'INSERT INTO system_health_checks(check_key,status,message,details,checked_at) VALUES (?,?,?,?,?)',
                    (key, status, message, json.dumps(details or {}, ensure_ascii=False), datetime.now().isoformat(timespec='seconds'))
                )
            except Exception:
                pass

        def count(sql, params=()):
            try:
                return int(conn.execute(sql, params).fetchone()[0] or 0)
            except Exception:
                return -1

        required_tables = ['users','invoices','invoice_lines','approval_requests','approval_steps','accounts','journal_entries','journal_lines','roles','permissions']
        missing = []
        for table in required_tables:
            ok = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
            if not ok:
                missing.append(table)
        add('database_schema', 'GREEN' if not missing else 'RED', 'Schema OK' if not missing else 'Missing tables', {'missing': missing})

        pending = count("SELECT COUNT(*) FROM approval_requests WHERE status='PENDING'")
        add('pending_approvals', 'GREEN' if pending == 0 else 'YELLOW', f'{pending} pending approval request(s)', {'count': pending})

        unposted = count("SELECT COUNT(*) FROM invoices WHERE COALESCE(workflow_status,'DRAFT')='APPROVED'")
        add('unposted_documents', 'GREEN' if unposted == 0 else 'YELLOW', f'{unposted} approved but unposted invoice(s)', {'count': unposted})

        sec = count("SELECT COUNT(*) FROM security_events WHERE created_at >= datetime('now','-7 days')") if self._table_exists(conn, 'security_events') else 0
        add('security_events_7d', 'GREEN' if sec == 0 else 'YELLOW', f'{sec} security event(s) in last 7 days', {'count': sec})

        try:
            rows = conn.execute("""
                SELECT je.id, COALESCE(SUM(CAST(jl.debit AS REAL)),0) d, COALESCE(SUM(CAST(jl.credit AS REAL)),0) c
                FROM journal_entries je LEFT JOIN journal_lines jl ON jl.journal_entry_id=je.id
                GROUP BY je.id HAVING ABS(d-c) > 0.005
            """).fetchall()
            imbalance = len(rows)
        except Exception:
            imbalance = -1
        add('journal_balance', 'GREEN' if imbalance == 0 else 'RED', f'{imbalance} imbalanced journal(s)', {'count': imbalance})

        overall = 'GREEN'
        if any(c['status'] == 'RED' for c in checks):
            overall = 'RED'
        elif any(c['status'] == 'YELLOW' for c in checks):
            overall = 'YELLOW'
        try:
            conn.commit()
        except Exception:
            pass
        return {'overall': overall, 'checked_at': datetime.now().isoformat(timespec='seconds'), 'checks': checks}


    def _ensure_validation_runs_table(self, conn) -> None:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS validation_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_type TEXT NOT NULL,
                status TEXT NOT NULL,
                summary TEXT,
                details TEXT,
                started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                finished_at TEXT
            )
        """)

    def record_validation_run(self, run_type: str, status: str, summary: str, details: dict) -> None:
        import json
        from datetime import datetime
        db = self._db()
        if db.is_remote():
            return
        conn = db.get_connection()
        self._ensure_validation_runs_table(conn)
        conn.execute(
            'INSERT INTO validation_runs(run_type,status,summary,details,finished_at) VALUES (?,?,?,?,?)',
            (str(run_type), str(status), str(summary), json.dumps(details or {}, ensure_ascii=False), datetime.now().isoformat(timespec='seconds'))
        )
        conn.commit()

    def validate_backup_restore(self) -> Dict[str, object]:
        import os
        import shutil
        import sqlite3
        import tempfile

        db = self._db()
        if db.is_remote():
            return {'status': 'SKIPPED', 'reason': 'remote mode'}
        conn = db.get_connection()
        path = getattr(db, 'db_path', None)
        try:
            from database.connection import DB_PATH
            path = path or DB_PATH
        except Exception:
            pass
        if not path or not os.path.exists(path):
            result = {'status': 'FAILED', 'reason': 'database path not found'}
            self.record_validation_run('backup_restore', 'FAILED', 'database path not found', result)
            return result
        tmp = tempfile.mkdtemp(prefix='alrajhi_restore_')
        try:
            backup = os.path.join(tmp, 'backup.sqlite')
            shutil.copy2(path, backup)
            test_conn = sqlite3.connect(backup)
            try:
                integrity = test_conn.execute('PRAGMA integrity_check').fetchone()[0]
                tables = test_conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
            finally:
                test_conn.close()
            status = 'PASSED' if integrity == 'ok' and tables > 0 else 'FAILED'
            result = {'status': status, 'integrity_check': integrity, 'tables': tables}
            self.record_validation_run('backup_restore', status, 'Backup/restore validation completed', result)
            return result
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def run_stress_smoke(self, invoice_count: int = 200) -> Dict[str, object]:
        from datetime import datetime

        db = self._db()
        if db.is_remote():
            return {'status': 'SKIPPED', 'reason': 'remote mode'}
        conn = db.get_connection()
        started = datetime.now()
        try:
            conn.execute('CREATE TABLE IF NOT EXISTS stress_probe(id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, amount TEXT, created_at TEXT)')
            for i in range(int(invoice_count)):
                conn.execute('INSERT INTO stress_probe(ref, amount, created_at) VALUES (?,?,?)', (f'STRESS-{i}', str(i), datetime.now().isoformat(timespec='seconds')))
            total = conn.execute('SELECT COUNT(*) FROM stress_probe').fetchone()[0]
            conn.commit()
            elapsed = (datetime.now() - started).total_seconds()
            result = {'status': 'PASSED', 'inserted': int(invoice_count), 'total_probe_rows': total, 'elapsed_seconds': elapsed}
            self.record_validation_run('stress_smoke', 'PASSED', 'Stress smoke completed', result)
            return result
        except Exception as exc:
            result = {'status': 'FAILED', 'error': str(exc)}
            self.record_validation_run('stress_smoke', 'FAILED', str(exc), result)
            return result

    def ensure_local_database(self) -> None:
        from database import ensure_db
        ensure_db()

    def configure_server_database_path(self) -> str:
        import os
        if os.name == 'nt':
            base = os.environ.get('APPDATA') or os.environ.get('LOCALAPPDATA') or os.path.expanduser('~\\AppData\\Roaming')
            client_db_path = os.path.join(base, 'Alrajhi', 'alrajhi_data.db')
        else:
            client_db_path = os.path.expanduser('~/.alrajhi/alrajhi_data.db')
        os.environ.setdefault('ALRAJHI_SERVER_DB_PATH', client_db_path)
        return os.environ.get('ALRAJHI_SERVER_DB_PATH', client_db_path)

    def ensure_server_database(self) -> None:
        self.configure_server_database_path()
        from alrajhi_server.database.migrations import ensure_db as ensure_db_remote
        ensure_db_remote()

    def _server_control(self):
        from core import server_control
        return server_control

    def default_port(self) -> int:
        return self._server_control().DEFAULT_PORT

    def get_server_port(self) -> int:
        return self._server_control().get_server_port()

    def normalize_server_url(self, address=None, port=None, default_scheme: str = "http") -> str:
        return self._server_control().normalize_server_url(address, port, default_scheme)

    def server_diagnostics(self, url=None, timeout: float = 3.0, require_routes: bool = True):
        return self._server_control().server_diagnostics(url, timeout=timeout, require_routes=require_routes)

    def health_check(self, url=None, timeout: float = 2.0, require_routes: bool = True) -> bool:
        return self._server_control().health_check(url, timeout=timeout, require_routes=require_routes)

    def port_in_use(self, port: int, host: str = "127.0.0.1") -> bool:
        return self._server_control().port_in_use(port, host=host)

    def start_server_process(self, main_file=None, port=None):
        return self._server_control().start_server_process(main_file=main_file, port=port)

    def stop_server_process(self):
        return self._server_control().stop_server_process()

    def restart_server_process(self, main_file=None, port=None):
        return self._server_control().restart_server_process(main_file=main_file, port=port)

    def server_status(self):
        return self._server_control().server_status()

    def get_server_runtime_info(self):
        return self._server_control().get_server_runtime_info()

    def open_server_data_dir(self):
        return self._server_control().open_server_data_dir()

    def backup_server_database(self):
        return self._server_control().backup_server_database()
