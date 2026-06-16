# -*- coding: utf-8 -*-
"""Remote backup gateway adapter."""
from __future__ import annotations

from typing import Dict

from gateways.backup_gateway import BackupGateway


class RemoteBackupGateway(BackupGateway):
    def is_remote(self) -> bool:
        return True

    def _raise_remote(self):
        raise RuntimeError("لا يمكن تنفيذ النسخ الاحتياطي أو الاستعادة من جهاز عميل.")

    def create_backup(self, folder: str, prefix: str = 'alrajhi_backup') -> Dict[str, str]:
        self._raise_remote()

    def validate_backup(self, backup_path: str) -> Dict[str, str]:
        self._raise_remote()

    def restore_backup(self, backup_path: str, create_pre_restore_backup: bool = True) -> Dict[str, str]:
        self._raise_remote()

    def export_database(self, destination: str) -> Dict[str, str]:
        self._raise_remote()

    def reset_database(self) -> Dict[str, str]:
        self._raise_remote()

    def list_backups(self, folder: str, prefix: str = 'alrajhi_backup') -> Dict[str, object]:
        self._raise_remote()

    def cleanup_old_backups(self, folder: str, keep_count: int, prefix: str = 'alrajhi_backup') -> Dict[str, object]:
        self._raise_remote()
