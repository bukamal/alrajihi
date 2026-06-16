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
        # Phase 148: active Settings Profile overrides the global setting when a
        # profile value exists. Fallback remains the legacy settings table.
        prof_value = self._profile_value(key, None)
        if prof_value is not None:
            return prof_value
        return self.gateway.get(key, default)

    def set(self, key: str, value: Any):
        value = '' if value is None else str(value)
        # Phase 148: Default profile writes to the legacy settings table. A
        # non-default active profile writes an override into settings_profile_values
        # so profiles remain isolated.
        try:
            profile = self.get_active_profile()
            if profile and int(profile.get('id') or 0) != 1:
                old_value = self.get(key, None)
                self.set_profile_value(int(profile['id']), key, value)
                self._log_profile_setting_change(int(profile['id']), str(profile.get('name') or ''), key, old_value, value)
                self.clear_cache()
                return
        except Exception:
            pass
        self.gateway.set(key, value)

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


    # ========== Backup settings ==========
    def get_backup_settings(self) -> Dict[str, Any]:
        return {
            'enabled': str(self.get('backup/enabled', 'false')).lower() == 'true',
            'frequency': str(self.get('backup/frequency', 'daily') or 'daily'),
            'interval_hours': int(self.get('backup/interval_hours', '6') or 6),
            'folder': self.get('backup/folder', '') or '',
            'retention_count': int(self.get('backup/retention_count', '10') or 10),
            'create_on_exit': str(self.get('backup/create_on_exit', 'false')).lower() == 'true',
        }

    def save_backup_settings(self, enabled: bool = False, frequency: str = 'daily',
                             interval_hours: int = 6, folder: str = '',
                             retention_count: int = 10, create_on_exit: bool = False):
        if frequency not in ('manual', 'daily', 'weekly', 'interval'):
            frequency = 'daily'
        old = self.get_backup_settings()
        new = {
            'enabled': bool(enabled),
            'frequency': frequency,
            'interval_hours': max(1, min(168, int(interval_hours or 6))),
            'folder': folder or '',
            'retention_count': max(1, min(365, int(retention_count or 10))),
            'create_on_exit': bool(create_on_exit),
        }
        self.set('backup/enabled', 'true' if new['enabled'] else 'false')
        self.set('backup/frequency', new['frequency'])
        self.set('backup/interval_hours', str(new['interval_hours']))
        self.set('backup/folder', new['folder'])
        self.set('backup/retention_count', str(new['retention_count']))
        self.set('backup/create_on_exit', 'true' if new['create_on_exit'] else 'false')
        self.clear_cache()
        audit_service.log('UPDATE', 'SETTINGS_BACKUP', None, old_values=old, new_values=new, details='تعديل إعدادات النسخ الاحتياطي')


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


    # ========== Runtime integration helpers (Phase 144) ==========
    def get_bool(self, key: str, default: bool = False) -> bool:
        value = self.get(key, 'true' if default else 'false')
        return str(value).strip().lower() in ('1', 'true', 'yes', 'on', 'y', 'نعم')

    def get_int(self, key: str, default: int = 0, minimum: int | None = None, maximum: int | None = None) -> int:
        try:
            value = int(float(str(self.get(key, default))))
        except Exception:
            value = int(default)
        if minimum is not None:
            value = max(minimum, value)
        if maximum is not None:
            value = min(maximum, value)
        return value

    def get_decimal_places(self, key: str, default: int = 2) -> int:
        return self.get_int(key, default, minimum=0, maximum=6)

    def get_invoice_settings(self) -> Dict[str, Any]:
        return {
            'sales_prefix': self.get('invoice/sales_prefix', 'SAL-') or 'SAL-',
            'purchase_prefix': self.get('invoice/purchase_prefix', 'PUR-') or 'PUR-',
            'number_format': self.get('invoice/number_format', '{PREFIX}{00000}') or '{PREFIX}{00000}',
            'auto_numbering': self.get_bool('invoice/auto_numbering', True),
            'show_profit': self.get_bool('invoice/show_profit', False),
            'show_cost': self.get_bool('invoice/show_cost', False),
            'round_prices': self.get_bool('invoice/round_prices', True),
            'price_decimals': self.get_decimal_places('units/price_decimals', 2),
            'quantity_decimals': self.get_decimal_places('units/quantity_decimals', 3),
        }

    def invoice_prefix(self, inv_type: str) -> str:
        return self.get('invoice/sales_prefix', 'SAL-') if inv_type == 'sale' else self.get('invoice/purchase_prefix', 'PUR-')

    def get_inventory_settings(self) -> Dict[str, Any]:
        return {
            'allow_negative_stock': self.get_bool('inventory/allow_negative_stock', False),
            'warn_on_stock_exceed': self.get_bool('inventory/warn_on_stock_exceed', True),
            'default_reorder_level': self.get('inventory/default_reorder_level', '0'),
            'cost_method': str(self.get('inventory/cost_method', 'AVERAGE') or 'AVERAGE').upper(),
            'auto_movements': self.get_bool('inventory/auto_movements', True),
        }

    def get_units_settings(self) -> Dict[str, Any]:
        return {
            'default_sales_unit': self.get('units/default_sales_unit', self.get('units/default_sale_unit', '')) or '',
            'default_purchase_unit': self.get('units/default_purchase_unit', '') or '',
            'quantity_decimals': self.get_decimal_places('units/quantity_decimals', 3),
            'price_decimals': self.get_decimal_places('units/price_decimals', 2),
            'rounding_method': self.get('units/rounding_method', 'HALF_UP') or 'HALF_UP',
        }

    def get_language_settings(self) -> Dict[str, str]:
        from i18n.translator import normalize_language
        ui_lang = normalize_language(self.get('language', 'ar'))
        return {
            'ui_language': ui_lang,
            'print_language': normalize_language(self.get('language/print', ui_lang)),
            'report_language': normalize_language(self.get('language/report', ui_lang)),
        }

    def save_language_settings(self, ui_language: str = 'ar', print_language: str | None = None, report_language: str | None = None):
        from i18n.translator import normalize_language
        old = self.get_language_settings()
        ui = normalize_language(ui_language)
        pr = normalize_language(print_language or ui)
        rp = normalize_language(report_language or ui)
        self.set('language', ui)
        self.set('language/print', pr)
        self.set('language/report', rp)
        self.clear_cache()
        audit_service.log('UPDATE', 'SETTINGS_LANGUAGE', None, old_values=old, new_values={'ui_language': ui, 'print_language': pr, 'report_language': rp}, details='تعديل إعدادات اللغات')

    def company_info(self) -> Dict[str, Any]:
        return {
            'name': self.get('company/name', self.get('company_name', '')),
            'logo': self.get('company/logo', self.get('company_logo', self.get('company/logo_path', ''))),
            'commercial_register': self.get('company/commercial_register', ''),
            'tax_number': self.get('company/tax_number', self.get('tax_number', '')),
            'address': self.get('company/address', self.get('company_address', '')),
            'phone': self.get('company/phone', self.get('company_phone', '')),
            'email': self.get('company/email', self.get('company_email', '')),
            'website': self.get('company/website', ''),
        }

    def audit_rows(self, limit: int = 100):
        try:
            from database.connection import DatabaseConnection
            db = DatabaseConnection()
            if db.is_remote():
                return []
            conn = db.get_connection()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT NOT NULL, old_value TEXT, new_value TEXT,
                    changed_by TEXT, changed_at TEXT NOT NULL, source TEXT DEFAULT 'SettingsService'
                )
            """)
            rows = conn.execute("SELECT * FROM settings_audit ORDER BY id DESC LIMIT ?", (int(limit or 100),)).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []


    # ========== Runtime localization/unit helpers (Phase 145) ==========
    def print_language(self) -> str:
        """Language used by printable HTML/PDF documents, independent from UI."""
        return self.get_language_settings().get('print_language', self.get_language())

    def report_language(self) -> str:
        """Language used by reports, independent from UI."""
        return self.get_language_settings().get('report_language', self.get_language())

    def quantity_decimals(self) -> int:
        return self.get_units_settings().get('quantity_decimals', 3)

    def price_decimals(self) -> int:
        return self.get_units_settings().get('price_decimals', 2)

    def format_quantity(self, value: Any) -> str:
        try:
            return f"{float(value):.{self.quantity_decimals()}f}"
        except Exception:
            return str(value if value is not None else '')

    def format_price(self, value: Any) -> str:
        try:
            return f"{float(value):.{self.price_decimals()}f}"
        except Exception:
            return str(value if value is not None else '')

    def save_units_settings(self, default_sales_unit: str = '', default_purchase_unit: str = '',
                            quantity_decimals: int = 3, price_decimals: int = 2,
                            rounding_method: str = 'HALF_UP'):
        old = self.get_units_settings()
        new = {
            'default_sales_unit': default_sales_unit or 'قطعة',
            'default_purchase_unit': default_purchase_unit or 'قطعة',
            'quantity_decimals': min(max(0, int(quantity_decimals or 0)), 6),
            'price_decimals': min(max(0, int(price_decimals or 0)), 6),
            'rounding_method': (rounding_method or 'HALF_UP').upper(),
        }
        # Persist both historical and canonical keys for backward compatibility.
        self.set('units/default_sales_unit', new['default_sales_unit'])
        self.set('units/default_sale_unit', new['default_sales_unit'])
        self.set('units/default_purchase_unit', new['default_purchase_unit'])
        self.set('units/quantity_decimals', str(new['quantity_decimals']))
        self.set('units/price_decimals', str(new['price_decimals']))
        self.set('units/rounding_method', new['rounding_method'])
        self.clear_cache()
        audit_service.log('UPDATE', 'SETTINGS_UNITS', None, old_values=old, new_values=new, details='تعديل إعدادات الوحدات')

    def save_company_info(self, info: Dict[str, Any]):
        """Persist company identity to config and settings so printing/reports use one source."""
        info = dict(info or {})
        old = self.company_info()
        mapping = {
            'name': 'company/name',
            'address': 'company/address',
            'phone': 'company/phone',
            'email': 'company/email',
            'tax_number': 'company/tax_number',
            'commercial_register': 'company/commercial_register',
            'website': 'company/website',
            'logo_path': 'company/logo',
            'logo': 'company/logo',
        }
        for src, key in mapping.items():
            if src in info:
                self.set(key, info.get(src, '') or '')
        try:
            from config import save_company_info as _save_company_info
            _save_company_info(info)
        except Exception:
            pass
        self.clear_cache()
        audit_service.log('UPDATE', 'SETTINGS_COMPANY', None, old_values=old, new_values=self.company_info(), details='تعديل بيانات الشركة')


    # ========== Security/Governance settings (Phase 146) ==========
    def get_security_settings(self) -> Dict[str, Any]:
        return {
            'hide_profit_for_non_admin': self.get_bool('security/hide_profit_for_non_admin', False),
            'prevent_delete_for_non_admin': self.get_bool('security/prevent_delete_for_non_admin', False),
            'prevent_invoice_edit_for_non_admin': self.get_bool('security/prevent_invoice_edit_for_non_admin', False),
            'prevent_return_edit_for_non_admin': self.get_bool('security/prevent_return_edit_for_non_admin', False),
            'restrict_reports_to_admin': self.get_bool('security/restrict_reports_to_admin', False),
            'restrict_report_export_to_admin': self.get_bool('security/restrict_report_export_to_admin', False),
            'blocked_report_roles': self.get('security/blocked_report_roles', '') or '',
        }

    def save_security_settings(self, hide_profit_for_non_admin: bool = False,
                               prevent_delete_for_non_admin: bool = False,
                               prevent_invoice_edit_for_non_admin: bool = False,
                               prevent_return_edit_for_non_admin: bool = False,
                               restrict_reports_to_admin: bool = False,
                               restrict_report_export_to_admin: bool = False,
                               blocked_report_roles: str = ''):
        old = self.get_security_settings()
        roles = ','.join([r.strip().lower() for r in str(blocked_report_roles or '').split(',') if r.strip()])
        new = {
            'hide_profit_for_non_admin': bool(hide_profit_for_non_admin),
            'prevent_delete_for_non_admin': bool(prevent_delete_for_non_admin),
            'prevent_invoice_edit_for_non_admin': bool(prevent_invoice_edit_for_non_admin),
            'prevent_return_edit_for_non_admin': bool(prevent_return_edit_for_non_admin),
            'restrict_reports_to_admin': bool(restrict_reports_to_admin),
            'restrict_report_export_to_admin': bool(restrict_report_export_to_admin),
            'blocked_report_roles': roles,
        }
        for key, val in new.items():
            self.set('security/' + key, 'true' if isinstance(val, bool) and val else ('false' if isinstance(val, bool) else val))
        self.clear_cache()
        audit_service.log('UPDATE', 'SETTINGS_SECURITY', None, old_values=old, new_values=new, details='تعديل إعدادات الصلاحيات')

    def export_settings_dict(self) -> Dict[str, Any]:
        """Return all local settings as a dictionary for support/backup purposes."""
        try:
            from database.connection import DatabaseConnection
            db = DatabaseConnection()
            if db.is_remote():
                return {}
            conn = db.get_connection()
            rows = conn.execute('SELECT key, value, category, updated_at FROM settings ORDER BY key').fetchall()
            return {row['key']: {'value': row['value'], 'category': row['category'], 'updated_at': row['updated_at']} for row in rows}
        except Exception:
            return {}

    def import_settings_dict(self, payload: Dict[str, Any]) -> int:
        """Import settings exported by export_settings_dict. Returns changed row count."""
        count = 0
        for key, item in dict(payload or {}).items():
            if not key:
                continue
            value = item.get('value') if isinstance(item, dict) else item
            self.set(str(key), '' if value is None else str(value))
            count += 1
        self.clear_cache()
        audit_service.log('IMPORT', 'SETTINGS', None, details=f'استيراد إعدادات ({count})')
        return count


    # ========== Settings Profiles (Phase 148) ==========
    def _profile_conn(self):
        from database.connection import DatabaseConnection
        db = DatabaseConnection()
        if db.is_remote():
            return None
        conn = db.get_connection()
        now_sql = "datetime('now')"
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                is_active INTEGER NOT NULL DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings_profile_values (
                profile_id INTEGER NOT NULL,
                setting_key TEXT NOT NULL,
                setting_value TEXT,
                updated_at TEXT,
                PRIMARY KEY (profile_id, setting_key),
                FOREIGN KEY(profile_id) REFERENCES settings_profiles(id) ON DELETE CASCADE
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_settings_profile_values_key ON settings_profile_values(setting_key)")
        conn.execute("""
            INSERT OR IGNORE INTO settings_profiles(id, name, description, is_active, created_at, updated_at)
            VALUES (1, 'Default', 'ملف الإعدادات الافتراضي', 1, datetime('now'), datetime('now'))
        """)
        active_count = conn.execute("SELECT COUNT(*) FROM settings_profiles WHERE is_active=1").fetchone()[0]
        if not active_count:
            conn.execute("UPDATE settings_profiles SET is_active=1 WHERE id=(SELECT MIN(id) FROM settings_profiles)")
        conn.commit()
        return conn

    def _profile_value(self, key: str, default: Any = None) -> Any:
        try:
            conn = self._profile_conn()
            if conn is None:
                return default
            row = conn.execute("SELECT id FROM settings_profiles WHERE is_active=1 LIMIT 1").fetchone()
            if not row:
                return default
            profile_id = int(row['id'])
            if profile_id == 1:
                return default
            val = conn.execute(
                "SELECT setting_value FROM settings_profile_values WHERE profile_id=? AND setting_key=?",
                (profile_id, key),
            ).fetchone()
            return val['setting_value'] if val else default
        except Exception:
            return default

    def list_profiles(self):
        try:
            conn = self._profile_conn()
            if conn is None:
                return []
            rows = conn.execute("""
                SELECT p.*, COUNT(v.setting_key) AS settings_count
                FROM settings_profiles p
                LEFT JOIN settings_profile_values v ON v.profile_id = p.id
                GROUP BY p.id
                ORDER BY p.is_active DESC, p.id ASC
            """).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def get_active_profile(self) -> Dict[str, Any]:
        try:
            conn = self._profile_conn()
            if conn is None:
                return {'id': 1, 'name': 'Default', 'description': '', 'is_active': 1, 'settings_count': 0}
            row = conn.execute("""
                SELECT p.*, COUNT(v.setting_key) AS settings_count
                FROM settings_profiles p
                LEFT JOIN settings_profile_values v ON v.profile_id = p.id
                WHERE p.is_active=1
                GROUP BY p.id
                LIMIT 1
            """).fetchone()
            return dict(row) if row else {'id': 1, 'name': 'Default', 'description': '', 'is_active': 1, 'settings_count': 0}
        except Exception:
            return {'id': 1, 'name': 'Default', 'description': '', 'is_active': 1, 'settings_count': 0}

    def create_profile(self, name: str, description: str = '') -> int:
        name = str(name or '').strip()
        if not name:
            raise ValueError('Profile name is required')
        conn = self._profile_conn()
        if conn is None:
            raise RuntimeError('Profiles are available in local mode only')
        now = __import__('datetime').datetime.now().isoformat(timespec='seconds')
        cur = conn.execute(
            "INSERT INTO settings_profiles(name, description, is_active, created_at, updated_at) VALUES (?, ?, 0, ?, ?)",
            (name, description or '', now, now),
        )
        conn.commit()
        audit_service.log('CREATE', 'SETTINGS_PROFILE', cur.lastrowid, details=f'إنشاء ملف إعدادات: {name}')
        return int(cur.lastrowid)

    def set_active_profile(self, profile_id: int):
        conn = self._profile_conn()
        if conn is None:
            return
        profile_id = int(profile_id)
        row = conn.execute("SELECT id, name FROM settings_profiles WHERE id=?", (profile_id,)).fetchone()
        if not row:
            raise ValueError('Profile not found')
        old = self.get_active_profile()
        conn.execute("UPDATE settings_profiles SET is_active=0")
        conn.execute("UPDATE settings_profiles SET is_active=1, updated_at=datetime('now') WHERE id=?", (profile_id,))
        conn.commit()
        self.clear_cache()
        audit_service.log('UPDATE', 'SETTINGS_PROFILE_ACTIVE', profile_id, old_values=old, new_values=dict(row), details=f'تفعيل ملف إعدادات: {row["name"]}')

    def set_profile_value(self, profile_id: int, key: str, value: Any):
        conn = self._profile_conn()
        if conn is None:
            return
        conn.execute("""
            INSERT OR REPLACE INTO settings_profile_values(profile_id, setting_key, setting_value, updated_at)
            VALUES (?, ?, ?, datetime('now'))
        """, (int(profile_id), str(key), '' if value is None else str(value)))
        conn.commit()

    def _log_profile_setting_change(self, profile_id: int, profile_name: str, key: str, old_value: Any, new_value: Any):
        try:
            conn = self._profile_conn()
            if conn is None or str(old_value) == str(new_value):
                return
            now = __import__('datetime').datetime.now().isoformat(timespec='seconds')
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT NOT NULL, old_value TEXT, new_value TEXT,
                    changed_by TEXT, changed_at TEXT NOT NULL, source TEXT DEFAULT 'SettingsService'
                )
            """)
            conn.execute("""
                INSERT INTO settings_audit(setting_key, old_value, new_value, changed_by, changed_at, source)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (f'profile:{profile_name}:{key}', old_value, new_value, None, now, 'SettingsProfile'))
            conn.commit()
        except Exception:
            pass

    def clone_profile(self, source_profile_id: int, new_name: str) -> int:
        source_profile_id = int(source_profile_id or 1)
        conn = self._profile_conn()
        if conn is None:
            raise RuntimeError('Profiles are available in local mode only')
        src = conn.execute("SELECT * FROM settings_profiles WHERE id=?", (source_profile_id,)).fetchone()
        if not src:
            raise ValueError('Source profile not found')
        new_id = self.create_profile(new_name, f"نسخة من {src['name']}")
        rows = conn.execute("SELECT setting_key, setting_value FROM settings_profile_values WHERE profile_id=?", (source_profile_id,)).fetchall()
        if not rows:
            rows = conn.execute("SELECT key AS setting_key, value AS setting_value FROM settings").fetchall()
        for row in rows:
            self.set_profile_value(new_id, row['setting_key'], row['setting_value'])
        audit_service.log('CREATE', 'SETTINGS_PROFILE_CLONE', new_id, details=f'نسخ ملف إعدادات من {src["name"]} إلى {new_name}')
        return new_id

    def export_profile_dict(self, profile_id: int | None = None) -> Dict[str, Any]:
        conn = self._profile_conn()
        if conn is None:
            return {}
        if profile_id is None:
            profile_id = int(self.get_active_profile().get('id') or 1)
        profile = conn.execute("SELECT * FROM settings_profiles WHERE id=?", (int(profile_id),)).fetchone()
        if not profile:
            return {}
        values = conn.execute("SELECT setting_key, setting_value FROM settings_profile_values WHERE profile_id=? ORDER BY setting_key", (int(profile_id),)).fetchall()
        if not values:
            values = conn.execute("SELECT key AS setting_key, value AS setting_value FROM settings ORDER BY key").fetchall()
        return {
            'profile': {k: profile[k] for k in profile.keys()},
            'settings': {r['setting_key']: r['setting_value'] for r in values},
        }

    def import_profile_dict(self, payload: Dict[str, Any]) -> int:
        payload = dict(payload or {})
        profile_data = dict(payload.get('profile') or {})
        settings = dict(payload.get('settings') or {})
        name = str(profile_data.get('name') or 'Imported Profile').strip()
        base = name
        conn = self._profile_conn()
        if conn is None:
            raise RuntimeError('Profiles are available in local mode only')
        i = 1
        while conn.execute("SELECT 1 FROM settings_profiles WHERE name=?", (name,)).fetchone():
            i += 1
            name = f'{base} ({i})'
        profile_id = self.create_profile(name, profile_data.get('description') or 'Imported profile')
        for key, value in settings.items():
            self.set_profile_value(profile_id, key, value)
        audit_service.log('IMPORT', 'SETTINGS_PROFILE', profile_id, details=f'استيراد ملف إعدادات: {name}')
        return profile_id

    def profile_health(self) -> Dict[str, Any]:
        active = self.get_active_profile()
        required = [
            'company/name', 'invoice/sales_prefix', 'invoice/purchase_prefix',
            'inventory/allow_negative_stock', 'units/quantity_decimals',
            'units/price_decimals', 'language', 'language/print', 'language/report',
            'backup/enabled', 'security/prevent_delete_for_non_admin'
        ]
        missing = []
        try:
            conn = self._profile_conn()
            if conn is not None:
                for key in required:
                    has_global = conn.execute('SELECT 1 FROM settings WHERE key=?', (key,)).fetchone() is not None
                    has_profile = conn.execute('SELECT 1 FROM settings_profile_values WHERE profile_id=? AND setting_key=?', (int(active.get('id') or 1), key)).fetchone() is not None
                    if not has_global and not has_profile:
                        missing.append(key)
        except Exception:
            pass
        return {'active_profile': active, 'missing_settings': missing, 'missing_count': len(missing)}


    def security_event_rows(self, limit: int = 200):
        """Return recent permission/security events for the Settings governance tab."""
        try:
            from core.services.permission_service import permission_service
            return permission_service.security_events(limit)
        except Exception:
            return []

    def security_denied_count(self) -> int:
        try:
            from core.services.permission_service import permission_service
            return permission_service.denied_events_count()
        except Exception:
            return 0


settings_service = SettingsService()
