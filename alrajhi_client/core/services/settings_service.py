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

    def set_language(self, language: str):
        if language not in ('ar', 'en', 'de', 'fr'):
            language = 'ar'
        old = {'language': self.get_language()}
        self.set('language', language)
        self.clear_cache()
        audit_service.log('UPDATE', 'SETTINGS_LANGUAGE', None, old_values=old, new_values={'language': language}, details='تعديل لغة النظام')


    def get_theme(self) -> str:
        theme = self.repo.get_theme()
        return theme if theme in ('light', 'dark') else 'light'

    def set_theme(self, theme: str):
        if theme not in ('light', 'dark'):
            theme = 'light'
        old = {'theme': self.get_theme()}
        self.set('theme', theme)
        self.clear_cache()
        audit_service.log('UPDATE', 'SETTINGS_APPEARANCE', None, old_values=old, new_values={'theme': theme}, details='تعديل مظهر البرنامج')

    def get_currency_settings(self) -> Dict[str, Any]:
        return self.repo.get_currency_settings()

    def save_currency_settings(self, base_currency: str, display_currency: str,
                               decimals: int, number_format: str,
                               abbreviate_numbers: bool):
        old = self.get_currency_settings()
        new = {
            'base_currency': base_currency,
            'display_currency': display_currency,
            'currency_decimals': str(decimals),
            'number_format': number_format,
            'abbreviate_numbers': bool(abbreviate_numbers),
        }
        self.set('base_currency', base_currency)
        self.set('display_currency', display_currency)
        self.set('currency_decimals', str(decimals))
        self.set('number_format', number_format)
        self.set('abbreviate_numbers', 'true' if abbreviate_numbers else 'false')
        self.clear_cache()
        audit_service.log('UPDATE', 'SETTINGS_CURRENCY', None, old_values=old, new_values=new, details='تعديل إعدادات العملة')

    def set_display_currency(self, currency_code: str):
        old = {'display_currency': self.get('display_currency', None)}
        self.set('display_currency', currency_code)
        self.clear_cache()
        audit_service.log('UPDATE', 'SETTINGS_CURRENCY', None, old_values=old, new_values={'display_currency': currency_code}, details='تغيير عملة العرض')

    # ========== Printing settings ==========
    def get_printing_settings(self) -> Dict[str, Any]:
        return {
            'invoice_template': self.get('printing/invoice_template', 'a4'),
            'report_template': self.get('printing/report_template', 'a4'),
            'voucher_template': self.get('printing/voucher_template', 'a4'),
            'return_template': self.get('printing/return_template', 'a4'),
            'default_paper': self.get('printing/default_paper', 'a4'),
            'show_logo': self.get('printing/show_logo', 'true').lower() == 'true',
            'show_tax_number': self.get('printing/show_tax_number', 'true').lower() == 'true',
            'show_qr': self.get('printing/show_qr', 'true').lower() == 'true',
            'footer_text': self.get('printing/footer_text', 'شكراً لتعاملكم معنا'),
            'thermal_size': self.get('printing/thermal_size', '80mm'),
            'font_family': self.get('printing/font_family', 'Tajawal, Arial, DejaVu Sans, sans-serif'),
            'print_font_size': self.get('printing/font_size', '10.5pt'),
            'accent_color': self.get('printing/accent_color', '#1d4ed8'),
            'zebra_rows': self.get('printing/zebra_rows', 'true').lower() == 'true',
            'compact_tables': self.get('printing/compact_tables', 'false').lower() == 'true',
            'template_language': self.get('printing/template_language', 'auto'),
        }

    def save_printing_settings(self, invoice_template: str = 'a4', show_logo: bool = True,
                               show_tax_number: bool = True, show_qr: bool = True,
                               footer_text: str = '', thermal_size: str = '80mm',
                               report_template: str = 'a4', voucher_template: str = 'a4',
                               return_template: str = 'a4', font_family: str = '',
                               font_size: str = '10.5pt', accent_color: str = '#1d4ed8',
                               zebra_rows: bool = True, compact_tables: bool = False, template_language: str = 'auto'):
        old = self.get_printing_settings()
        new = {
            'invoice_template': invoice_template or 'a4',
            'report_template': report_template or 'a4',
            'voucher_template': voucher_template or 'a4',
            'return_template': return_template or 'a4',
            'default_paper': invoice_template or 'a4',
            'show_logo': bool(show_logo),
            'show_tax_number': bool(show_tax_number),
            'show_qr': bool(show_qr),
            'footer_text': footer_text or '',
            'thermal_size': thermal_size or '80mm',
            'font_family': font_family or 'Tajawal, Arial, DejaVu Sans, sans-serif',
            'font_size': font_size or '10.5pt',
            'accent_color': accent_color or '#1d4ed8',
            'zebra_rows': bool(zebra_rows),
            'compact_tables': bool(compact_tables),
            'template_language': template_language or 'auto',
        }
        self.set('printing/invoice_template', new['invoice_template'])
        self.set('printing/report_template', new['report_template'])
        self.set('printing/voucher_template', new['voucher_template'])
        self.set('printing/return_template', new['return_template'])
        self.set('printing/default_paper', new['default_paper'])
        self.set('printing/show_logo', 'true' if show_logo else 'false')
        self.set('printing/show_tax_number', 'true' if show_tax_number else 'false')
        self.set('printing/show_qr', 'true' if show_qr else 'false')
        self.set('printing/footer_text', new['footer_text'])
        self.set('printing/thermal_size', new['thermal_size'])
        self.set('printing/font_family', new['font_family'])
        self.set('printing/font_size', new['font_size'])
        self.set('printing/accent_color', new['accent_color'])
        self.set('printing/zebra_rows', 'true' if zebra_rows else 'false')
        self.set('printing/compact_tables', 'true' if compact_tables else 'false')
        self.set('printing/template_language', new['template_language'])
        self.clear_cache()
        audit_service.log('UPDATE', 'SETTINGS_PRINTING', None, old_values=old, new_values=new, details='تعديل إعدادات الطباعة')


    # ========== POS settings ==========
    def pos_shifts_enabled(self) -> bool:
        """Return whether POS cashier shifts are required. Default is disabled."""
        return str(self.get('pos/use_shifts', 'false')).lower() == 'true'

    def save_pos_settings(self, use_shifts: bool = False):
        old = {'pos/use_shifts': self.pos_shifts_enabled()}
        self.set('pos/use_shifts', 'true' if use_shifts else 'false')
        self.clear_cache()
        audit_service.log('UPDATE', 'SETTINGS_POS', None, old_values=old, new_values={'pos/use_shifts': bool(use_shifts)}, details='تعديل إعدادات نقطة البيع')

settings_service = SettingsService()
