# -*- coding: utf-8 -*-
"""Settings gateway contract and factory.

Phase 16 moves persistent settings access out of core/services so settings
follow the same Service -> Gateway -> Local/Remote adapter boundary as the rest
of the client.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class SettingsGateway(ABC):
    @abstractmethod
    def is_remote(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, value: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def clear_cache(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_language(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_theme(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_currency_settings(self) -> Dict[str, Any]:
        raise NotImplementedError


def create_settings_gateway() -> SettingsGateway:
    from database.connection import DatabaseConnection

    db = DatabaseConnection()
    if db.is_remote():
        from gateways.remote.settings_gateway import RemoteSettingsGateway
        return RemoteSettingsGateway(db.get_rest_client())

    from gateways.local.settings_gateway import LocalSettingsGateway
    return LocalSettingsGateway()
