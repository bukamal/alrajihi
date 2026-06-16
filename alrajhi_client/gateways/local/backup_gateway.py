# -*- coding: utf-8 -*-
"""Local SQLite backup gateway adapter."""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import shutil
import sqlite3
from pathlib import Path
from typing import Dict

from database.connection import DatabaseConnection, DB_PATH
from gateways.backup_gateway import BackupGateway


class LocalBackupGateway(BackupGateway):
    APP_NAME = "alrajhi"
    SCHEMA_VERSION = 1

    def is_remote(self) -> bool:
        return False

    def _sha256(self, path: str) -> str:
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                h.update(chunk)
        return h.hexdigest()

    def _table_names(self, conn) -> set:
        """Return SQLite table names normalized to lower case.

        SQLite itself treats table names case-insensitively in normal queries,
        but sqlite_master preserves the original spelling. Older backups may
        contain names such as Inventory_movements, while application code uses
        inventory_movements. Validation must therefore be case-insensitive.
        """
        return {str(r[0]).lower() for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

    def _integrity_check(self, path: str) -> None:
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        conn = sqlite3.connect(path)
        try:
            result = conn.execute("PRAGMA integrity_check").fetchone()[0]
            if result != 'ok':
                raise RuntimeError(f"فشل فحص سلامة قاعدة البيانات: {result}")

            # Identity check only. Versioned/derived tables such as
            # inventory_movements or inventory_ledger are created by the schema
            # guard during startup/restore, so they must not make an otherwise
            # valid Alrajhi database unrecoverable.
            required_identity = {'users', 'items', 'invoices', 'vouchers'}
            tables = self._table_names(conn)
            missing = required_identity - tables
            if missing:
                raise RuntimeError("النسخة لا تبدو قاعدة الراجحي الصحيحة. جداول أساسية ناقصة: " + ', '.join(sorted(missing)))
        finally:
            conn.close()

    def _upgrade_schema_file(self, path: str) -> None:
        """Apply the idempotent schema guard to a database file before use."""
        conn = sqlite3.connect(path)
        try:
            from database.schema_manager import apply_common_schema
            apply_common_schema(conn)
            conn.commit()
        finally:
            conn.close()

    def create_backup(self, folder: str, prefix: str = 'alrajhi_backup') -> Dict[str, str]:
        folder_path = Path(folder).expanduser()
        folder_path.mkdir(parents=True, exist_ok=True)
        if not os.path.exists(DB_PATH):
            raise FileNotFoundError("لا توجد قاعدة بيانات محلية للنسخ الاحتياطي")

        # Ensure old live databases are upgraded before backup creation.
        # This prevents false failures such as a missing inventory_movements
        # table during reset/pre-restore backup creation.
        db = DatabaseConnection()
        try:
            conn = db.get_connection()
            if conn is not None:
                from database.schema_manager import apply_common_schema
                apply_common_schema(conn)
        finally:
            db.close()

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = str(folder_path / f"{prefix}_{timestamp}.db")
        meta_path = backup_path + '.json'

        src = sqlite3.connect(DB_PATH)
        dst = sqlite3.connect(backup_path)
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()

        self._integrity_check(backup_path)
        checksum = self._sha256(backup_path)
        metadata = {
            'app': self.APP_NAME,
            'created_at': datetime.datetime.now().isoformat(timespec='seconds'),
            'schema_version': self.SCHEMA_VERSION,
            'db_path': DB_PATH,
            'backup_file': os.path.basename(backup_path),
            'sha256': checksum,
            'size_bytes': os.path.getsize(backup_path),
        }
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        return {'backup_path': backup_path, 'metadata_path': meta_path, 'sha256': checksum}

    def validate_backup(self, backup_path: str) -> Dict[str, str]:
        self._integrity_check(backup_path)
        checksum = self._sha256(backup_path)
        meta_path = backup_path + '.json'
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                expected = metadata.get('sha256')
                if expected and expected != checksum:
                    raise RuntimeError("تغيّر ملف النسخة الاحتياطية: checksum غير مطابق")
            except json.JSONDecodeError:
                raise RuntimeError("ملف بيانات النسخة الاحتياطية تالف")
        return {'backup_path': backup_path, 'sha256': checksum, 'status': 'ok'}

    def restore_backup(self, backup_path: str, create_pre_restore_backup: bool = True) -> Dict[str, str]:
        validation = self.validate_backup(backup_path)
        db = DatabaseConnection()
        db.close()

        pre_restore = None
        if create_pre_restore_backup and os.path.exists(DB_PATH):
            folder = os.path.join(os.path.dirname(DB_PATH), 'pre_restore_backups')
            pre_restore = self.create_backup(folder, prefix='alrajhi_pre_restore')['backup_path']

        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        tmp_path = DB_PATH + '.restore_tmp'
        shutil.copy2(backup_path, tmp_path)
        self._integrity_check(tmp_path)
        self._upgrade_schema_file(tmp_path)
        self._integrity_check(tmp_path)
        os.replace(tmp_path, DB_PATH)

        return {'restored_from': backup_path, 'sha256': validation['sha256'], 'pre_restore_backup': pre_restore}

    def export_database(self, destination: str) -> Dict[str, str]:
        folder = os.path.dirname(destination) or '.'
        result = self.create_backup(folder, prefix='alrajhi_export')
        os.replace(result['backup_path'], destination)
        meta_src = result['metadata_path']
        meta_dst = destination + '.json'
        if os.path.exists(meta_src):
            os.replace(meta_src, meta_dst)
        result['backup_path'] = destination
        result['metadata_path'] = meta_dst
        return result


    def list_backups(self, folder: str, prefix: str = 'alrajhi_backup') -> Dict[str, object]:
        folder_path = Path(folder).expanduser()
        if not folder_path.exists():
            return {'folder': str(folder_path), 'backups': [], 'latest': None, 'count': 0}
        backups = []
        for path in sorted(folder_path.glob(f'{prefix}_*.db')):
            try:
                backups.append({
                    'path': str(path),
                    'filename': path.name,
                    'created_at': datetime.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec='seconds'),
                    'size_bytes': path.stat().st_size,
                    'metadata_path': str(path) + '.json' if os.path.exists(str(path) + '.json') else '',
                })
            except OSError:
                continue
        backups.sort(key=lambda item: item.get('created_at', ''), reverse=True)
        return {'folder': str(folder_path), 'backups': backups, 'latest': backups[0] if backups else None, 'count': len(backups)}

    def cleanup_old_backups(self, folder: str, keep_count: int, prefix: str = 'alrajhi_backup') -> Dict[str, object]:
        keep_count = max(1, int(keep_count or 1))
        info = self.list_backups(folder, prefix=prefix)
        removed = []
        for item in info.get('backups', [])[keep_count:]:
            path = item.get('path')
            if not path:
                continue
            try:
                os.remove(path)
                meta = path + '.json'
                if os.path.exists(meta):
                    os.remove(meta)
                removed.append(path)
            except OSError:
                continue
        return {'folder': info.get('folder'), 'kept': min(keep_count, info.get('count', 0)), 'removed': removed, 'removed_count': len(removed)}

    def reset_database(self) -> Dict[str, str]:
        from database.migrations import init_database

        db = DatabaseConnection()
        db.close()
        pre_reset = None
        if os.path.exists(DB_PATH):
            pre_reset = self.create_backup(
                os.path.join(os.path.dirname(DB_PATH), 'pre_reset_backups'),
                prefix='alrajhi_pre_reset',
            )['backup_path']
            os.remove(DB_PATH)
        init_database()
        return {'status': 'ok', 'pre_reset_backup': pre_reset}
