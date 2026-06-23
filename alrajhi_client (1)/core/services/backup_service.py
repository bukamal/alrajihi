# -*- coding: utf-8 -*-
"""Backup and restore service for local SQLite deployments.

Phase 13 routes persistence and filesystem backup internals through
BackupGateway.  The service remains the application-facing API and adds audit
logging around successful operations.
"""
from __future__ import annotations

from typing import Dict

from core.services.audit_service import audit_service
from gateways.backup_gateway import create_backup_gateway


class BackupService:
    def __init__(self):
        self._gateway = None

    def _get_gateway(self):
        if self._gateway is None:
            self._gateway = create_backup_gateway()
        return self._gateway

    def is_remote(self) -> bool:
        return self._get_gateway().is_remote()

    def create_backup(self, folder: str, prefix: str = 'alrajhi_backup') -> Dict[str, str]:
        result = self._get_gateway().create_backup(folder, prefix=prefix)
        audit_service.log('BACKUP_CREATE', 'DATABASE', None, new_values=result,
                          details=result.get('backup_path', ''), source='SYSTEM')
        return result

    def validate_backup(self, backup_path: str) -> Dict[str, str]:
        return self._get_gateway().validate_backup(backup_path)

    def restore_backup(self, backup_path: str, create_pre_restore_backup: bool = True) -> Dict[str, str]:
        payload = self._get_gateway().restore_backup(
            backup_path,
            create_pre_restore_backup=create_pre_restore_backup,
        )
        audit_service.log('BACKUP_RESTORE', 'DATABASE', None, new_values=payload,
                          details=backup_path, source='USER')
        return payload

    def export_database(self, destination: str) -> Dict[str, str]:
        result = self._get_gateway().export_database(destination)
        audit_service.log('BACKUP_EXPORT', 'DATABASE', None, new_values=result,
                          details=destination, source='USER')
        return result

    def reset_database(self) -> Dict[str, str]:
        result = self._get_gateway().reset_database()
        audit_service.log('DATABASE_RESET', 'DATABASE', None, new_values=result,
                          details='إعادة تهيئة قاعدة البيانات المحلية', source='USER')
        return result

    def list_backups(self, folder: str, prefix: str = 'alrajhi_backup') -> Dict[str, object]:
        return self._get_gateway().list_backups(folder, prefix=prefix)

    def cleanup_old_backups(self, folder: str, keep_count: int, prefix: str = 'alrajhi_backup') -> Dict[str, object]:
        result = self._get_gateway().cleanup_old_backups(folder, keep_count, prefix=prefix)
        audit_service.log('BACKUP_CLEANUP', 'DATABASE', None, new_values=result,
                          details=folder, source='USER')
        return result


backup_service = BackupService()
