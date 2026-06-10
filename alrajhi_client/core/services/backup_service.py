# -*- coding: utf-8 -*-
"""Backup and restore service for local SQLite deployments.

The service uses SQLite's online backup API instead of raw file copying while
connections may be open.  It also writes a metadata sidecar and validates backups
with PRAGMA integrity_check before restore.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import shutil
import sqlite3
from pathlib import Path
from typing import Dict, Optional

from database.connection import DatabaseConnection, DB_PATH
from core.services.audit_service import audit_service


class BackupService:
    APP_NAME = "alrajhi"
    SCHEMA_VERSION = 1

    def is_remote(self) -> bool:
        return DatabaseConnection().is_remote()

    def _ensure_local(self) -> None:
        if self.is_remote():
            raise RuntimeError("لا يمكن تنفيذ النسخ الاحتياطي أو الاستعادة من جهاز عميل.")

    def _sha256(self, path: str) -> str:
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                h.update(chunk)
        return h.hexdigest()

    def _integrity_check(self, path: str) -> None:
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        conn = sqlite3.connect(path)
        try:
            result = conn.execute("PRAGMA integrity_check").fetchone()[0]
            if result != 'ok':
                raise RuntimeError(f"فشل فحص سلامة قاعدة البيانات: {result}")
            required = {'users', 'items', 'invoices', 'vouchers', 'inventory_movements'}
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            missing = required - tables
            if missing:
                raise RuntimeError("النسخة لا تبدو قاعدة الراجحي الصحيحة. جداول ناقصة: " + ', '.join(sorted(missing)))
        finally:
            conn.close()

    def create_backup(self, folder: str, prefix: str = 'alrajhi_backup') -> Dict[str, str]:
        self._ensure_local()
        folder_path = Path(folder).expanduser()
        folder_path.mkdir(parents=True, exist_ok=True)
        if not os.path.exists(DB_PATH):
            raise FileNotFoundError("لا توجد قاعدة بيانات محلية للنسخ الاحتياطي")

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

        audit_service.log('BACKUP_CREATE', 'DATABASE', None, new_values=metadata, details=backup_path, source='SYSTEM')
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
        self._ensure_local()
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
        os.replace(tmp_path, DB_PATH)

        payload = {'restored_from': backup_path, 'sha256': validation['sha256'], 'pre_restore_backup': pre_restore}
        audit_service.log('BACKUP_RESTORE', 'DATABASE', None, new_values=payload, details=backup_path, source='USER')
        return payload

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
        audit_service.log('BACKUP_EXPORT', 'DATABASE', None, new_values=result, details=destination, source='USER')
        return result


backup_service = BackupService()
