# -*- coding: utf-8 -*-
"""Backup gateway contract and factory.

Phase 13 moves local SQLite backup/restore internals out of core/services.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict


class BackupGateway(ABC):
    @abstractmethod
    def is_remote(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def create_backup(self, folder: str, prefix: str = 'alrajhi_backup') -> Dict[str, str]:
        raise NotImplementedError

    @abstractmethod
    def validate_backup(self, backup_path: str) -> Dict[str, str]:
        raise NotImplementedError

    @abstractmethod
    def restore_backup(self, backup_path: str, create_pre_restore_backup: bool = True) -> Dict[str, str]:
        raise NotImplementedError

    @abstractmethod
    def export_database(self, destination: str) -> Dict[str, str]:
        raise NotImplementedError

    @abstractmethod
    def reset_database(self) -> Dict[str, str]:
        raise NotImplementedError


def create_backup_gateway() -> BackupGateway:
    from database.connection import DatabaseConnection

    db = DatabaseConnection()
    if db.is_remote():
        from gateways.remote.backup_gateway import RemoteBackupGateway
        return RemoteBackupGateway()

    from gateways.local.backup_gateway import LocalBackupGateway
    return LocalBackupGateway()
