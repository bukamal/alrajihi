# -*- coding: utf-8 -*-
from __future__ import annotations
from datetime import datetime
import json, tempfile, shutil, os, sqlite3
from pathlib import Path


class ProductionValidationService:
    """Phase 159 recovery/stress validation helpers.

    These are deterministic smoke tests intended to run locally without external
    infrastructure. Full concurrent-load testing still belongs in a dedicated CI
    or staging environment.
    """

    def _db(self):
        from database.connection import DatabaseConnection
        return DatabaseConnection()

    def ensure_schema(self, conn=None):
        owns = conn is None
        if owns:
            db = self._db()
            if db.is_remote():
                return
            conn = db.get_connection()
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
        if owns:
            conn.commit()

    def _record(self, run_type, status, summary, details):
        db = self._db()
        if db.is_remote():
            return
        conn = db.get_connection()
        self.ensure_schema(conn)
        conn.execute(
            'INSERT INTO validation_runs(run_type,status,summary,details,finished_at) VALUES (?,?,?,?,?)',
            (run_type, status, summary, json.dumps(details, ensure_ascii=False), datetime.now().isoformat(timespec='seconds'))
        )
        conn.commit()

    def validate_backup_restore(self):
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
            self._record('backup_restore', 'FAILED', 'database path not found', result)
            return result
        tmp = tempfile.mkdtemp(prefix='alrajhi_restore_')
        try:
            backup = os.path.join(tmp, 'backup.sqlite')
            shutil.copy2(path, backup)
            test_conn = sqlite3.connect(backup)
            integrity = test_conn.execute('PRAGMA integrity_check').fetchone()[0]
            tables = test_conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
            test_conn.close()
            status = 'PASSED' if integrity == 'ok' and tables > 0 else 'FAILED'
            result = {'status': status, 'integrity_check': integrity, 'tables': tables}
            self._record('backup_restore', status, 'Backup/restore validation completed', result)
            return result
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def run_stress_smoke(self, invoice_count=200):
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
            self._record('stress_smoke', 'PASSED', 'Stress smoke completed', result)
            return result
        except Exception as exc:
            result = {'status': 'FAILED', 'error': str(exc)}
            self._record('stress_smoke', 'FAILED', str(exc), result)
            return result


production_validation_service = ProductionValidationService()
