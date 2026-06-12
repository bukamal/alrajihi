# -*- coding: utf-8 -*-
"""Remote settings gateway adapter."""
from __future__ import annotations

from typing import Any, Dict

from gateways.settings_gateway import SettingsGateway


class RemoteSettingsGateway(SettingsGateway):
    def __init__(self, client):
        self.client = client
        self._cache: Dict[str, Any] = {}

    def is_remote(self) -> bool:
        return True

    def get(self, key: str, default: Any = None) -> Any:
        if key in self._cache:
            value = self._cache[key]
        else:
            value = self.client.get_setting(key)
            self._cache[key] = value
        return default if value is None else value

    def set(self, key: str, value: str) -> None:
        self.client.set_setting(key, value)
        self._cache.pop(key, None)

    def clear_cache(self) -> None:
        self._cache.clear()

    def get_language(self) -> str:
        return self.get('language', 'ar')

    def get_theme(self) -> str:
        return self.get('theme', 'light')

    def get_currency_settings(self) -> Dict[str, Any]:
        return {
            'symbol': self.get('currency_symbol', '$'),
            'decimals': int(self.get('currency_decimals', '2')),
            'format': self.get('number_format', 'western'),
        }
