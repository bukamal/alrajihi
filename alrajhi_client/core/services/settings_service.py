# -*- coding: utf-8 -*-
"""Settings application service.

This service centralizes access to persistent application settings so UI code no
longer instantiates SettingsRepository directly.  The repository remains the
single persistence adapter; this facade provides stable, explicit operations for
language, theme, and currency-related preferences.
"""
from __future__ import annotations

from typing import Any, Dict

from database.repositories.settings_repo import SettingsRepository
from core.services.audit_service import audit_service


class SettingsService:
    def __init__(self):
        self.repo = SettingsRepository()

    def get(self, key: str, default: Any = None) -> Any:
        return self.repo.get(key, default)

    def set(self, key: str, value: Any):
        self.repo.set(key, str(value))

    def clear_cache(self):
        self.repo.clear_cache()

    def get_language(self) -> str:
        return self.repo.get_language()

    def get_theme(self) -> str:
        theme = self.repo.get_theme()
        return theme if theme in ('light', 'dark') else 'light'

    def set_theme(self, theme: str):
        if theme not in ('light', 'dark'):
            theme = 'light'
        self.set('theme', theme)
        self.clear_cache()

    def get_currency_settings(self) -> Dict[str, Any]:
        return self.repo.get_currency_settings()

    def save_currency_settings(self, base_currency: str, display_currency: str,
                               decimals: int, number_format: str,
                               abbreviate_numbers: bool):
        self.set('base_currency', base_currency)
        self.set('display_currency', display_currency)
        self.set('currency_decimals', str(decimals))
        self.set('number_format', number_format)
        self.set('abbreviate_numbers', 'true' if abbreviate_numbers else 'false')
        self.clear_cache()

    def set_display_currency(self, currency_code: str):
        self.set('display_currency', currency_code)
        self.clear_cache()

    # ========== Printing settings ==========
    def get_printing_settings(self) -> Dict[str, Any]:
        return {
            'invoice_template': self.get('printing/invoice_template', 'a4'),
            'show_logo': self.get('printing/show_logo', 'true').lower() == 'true',
            'show_tax_number': self.get('printing/show_tax_number', 'true').lower() == 'true',
            'show_qr': self.get('printing/show_qr', 'true').lower() == 'true',
            'footer_text': self.get('printing/footer_text', 'شكراً لتعاملكم معنا'),
            'thermal_size': self.get('printing/thermal_size', '80mm'),
        }

    def save_printing_settings(self, invoice_template: str = 'a4', show_logo: bool = True,
                               show_tax_number: bool = True, show_qr: bool = True,
                               footer_text: str = '', thermal_size: str = '80mm'):
        self.set('printing/invoice_template', invoice_template or 'a4')
        self.set('printing/show_logo', 'true' if show_logo else 'false')
        self.set('printing/show_tax_number', 'true' if show_tax_number else 'false')
        self.set('printing/show_qr', 'true' if show_qr else 'false')
        self.set('printing/footer_text', footer_text or '')
        self.set('printing/thermal_size', thermal_size or '80mm')
        self.clear_cache()


settings_service = SettingsService()
