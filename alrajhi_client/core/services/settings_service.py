# -*- coding: utf-8 -*-
"""Settings application service.

This service centralizes access to persistent application settings so UI code no
longer instantiates SettingsRepository directly.  The repository remains the
single persistence adapter; this facade provides stable, explicit operations for
language, theme, and currency-related preferences.
"""
from __future__ import annotations

from typing import Any, Dict

from gateways.settings_gateway import create_settings_gateway
from core.services.audit_service import audit_service


class SettingsService:
    def __init__(self):
        self.gateway = create_settings_gateway()

    def get(self, key: str, default: Any = None) -> Any:
        return self.gateway.get(key, default)

    def set(self, key: str, value: Any):
        self.gateway.set(key, str(value))

    def clear_cache(self):
        self.gateway.clear_cache()

    def get_language(self) -> str:
        from i18n.translator import normalize_language
        return normalize_language(self.gateway.get_language())

    def set_language(self, language: str):
        from i18n.translator import normalize_language
        language = normalize_language(language)
        old = {'language': self.get_language()}
        self.set('language', language)
        self.clear_cache()
        audit_service.log('UPDATE', 'SETTINGS_LANGUAGE', None, old_values=old, new_values={'language': language}, details='تعديل لغة البرنامج')

    def get_theme(self) -> str:
        theme = self.gateway.get_theme()
        return theme if theme in ('light', 'dark') else 'light'

    def set_theme(self, theme: str):
        if theme not in ('light', 'dark'):
            theme = 'light'
        old = {'theme': self.get_theme()}
        self.set('theme', theme)
        self.clear_cache()
        audit_service.log('UPDATE', 'SETTINGS_APPEARANCE', None, old_values=old, new_values={'theme': theme}, details='تعديل مظهر البرنامج')

    def get_currency_settings(self) -> Dict[str, Any]:
        return self.gateway.get_currency_settings()

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
            'barcode_default_printer': self.get('printing/barcode/default_printer', 'pdf:default'),
            'barcode_label_size': self.get('printing/barcode/label_size', '50x30'),
            'barcode_symbology': self.get('printing/barcode/symbology', 'AUTO'),
            'barcode_copies': int(self.get('printing/barcode/copies', '1') or 1),
            'barcode_columns': int(self.get('printing/barcode/columns', '2') or 2),
            'barcode_show_company': self.get('printing/barcode/show_company', 'true').lower() == 'true',
            'barcode_show_logo': self.get('printing/barcode/show_logo', self.get('printing/show_logo', 'true')).lower() == 'true',
            'barcode_show_qr': self.get('printing/barcode/show_qr', 'true').lower() == 'true',
            'barcode_show_name': self.get('printing/barcode/show_name', 'true').lower() == 'true',
            'barcode_show_price': self.get('printing/barcode/show_price', 'true').lower() == 'true',
            'barcode_show_text': self.get('printing/barcode/show_text', 'true').lower() == 'true',
        }

    def save_printing_settings(self, invoice_template: str = 'a4', show_logo: bool = True,
                               show_tax_number: bool = True, show_qr: bool = True,
                               footer_text: str = '', thermal_size: str = '80mm',
                               report_template: str = 'a4', voucher_template: str = 'a4',
                               return_template: str = 'a4', font_family: str = '',
                               font_size: str = '10.5pt', accent_color: str = '#1d4ed8',
                               zebra_rows: bool = True, compact_tables: bool = False,
                               barcode_default_printer: str = 'pdf:default', barcode_label_size: str = '50x30',
                               barcode_symbology: str = 'AUTO', barcode_copies: int = 1,
                               barcode_columns: int = 2, barcode_show_company: bool = True,
                               barcode_show_logo: bool = True, barcode_show_qr: bool = True,
                               barcode_show_name: bool = True, barcode_show_price: bool = True,
                               barcode_show_text: bool = True):
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
            'barcode_default_printer': barcode_default_printer or 'pdf:default',
            'barcode_label_size': barcode_label_size or '50x30',
            'barcode_symbology': (barcode_symbology or 'AUTO').upper(),
            'barcode_copies': max(1, int(barcode_copies or 1)),
            'barcode_columns': min(max(1, int(barcode_columns or 2)), 4),
            'barcode_show_company': bool(barcode_show_company),
            'barcode_show_logo': bool(barcode_show_logo),
            'barcode_show_qr': bool(barcode_show_qr),
            'barcode_show_name': bool(barcode_show_name),
            'barcode_show_price': bool(barcode_show_price),
            'barcode_show_text': bool(barcode_show_text),
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
        self.set('printing/barcode/default_printer', new['barcode_default_printer'])
        self.set('printing/barcode/label_size', new['barcode_label_size'])
        self.set('printing/barcode/symbology', new['barcode_symbology'])
        self.set('printing/barcode/copies', str(new['barcode_copies']))
        self.set('printing/barcode/columns', str(new['barcode_columns']))
        self.set('printing/barcode/show_company', 'true' if new['barcode_show_company'] else 'false')
        self.set('printing/barcode/show_logo', 'true' if new['barcode_show_logo'] else 'false')
        self.set('printing/barcode/show_qr', 'true' if new['barcode_show_qr'] else 'false')
        self.set('printing/barcode/show_name', 'true' if new['barcode_show_name'] else 'false')
        self.set('printing/barcode/show_price', 'true' if new['barcode_show_price'] else 'false')
        self.set('printing/barcode/show_text', 'true' if new['barcode_show_text'] else 'false')
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


    # ========== Inventory read mode settings ==========
    def get_inventory_stock_read_mode(self) -> str:
        mode = str(self.get('inventory/stock_read_mode', 'operational') or 'operational').lower()
        return mode if mode in ('operational', 'dual', 'ledger_trial', 'ledger_authoritative') else 'operational'

    def set_inventory_stock_read_mode(self, mode: str):
        mode = str(mode or 'operational').lower()
        if mode not in ('operational', 'dual', 'ledger_trial', 'ledger_authoritative'):
            mode = 'operational'
        old = {'inventory/stock_read_mode': self.get_inventory_stock_read_mode()}
        self.set('inventory/stock_read_mode', mode)
        self.clear_cache()
        audit_service.log('UPDATE', 'SETTINGS_INVENTORY', None, old_values=old, new_values={'inventory/stock_read_mode': mode}, details='تعديل مصدر قراءة المخزون')


settings_service = SettingsService()
