# -*- coding: utf-8 -*-
"""Local settings gateway adapter."""
from __future__ import annotations

from typing import Any, Dict

from database.repositories.settings_repo import SettingsRepository
from gateways.settings_gateway import SettingsGateway


class LocalSettingsGateway(SettingsGateway):
    def __init__(self):
        self.repo = SettingsRepository()

    def is_remote(self) -> bool:
        return False

    def get(self, key: str, default: Any = None) -> Any:
        return self.repo.get(key, default)

    def set(self, key: str, value: str) -> None:
        self.repo.set(key, value)

    def clear_cache(self) -> None:
        self.repo.clear_cache()

    def get_language(self) -> str:
        return self.repo.get_language()

    def get_theme(self) -> str:
        return self.repo.get_theme()

    def get_currency_settings(self) -> Dict[str, Any]:
        return self.repo.get_currency_settings()
