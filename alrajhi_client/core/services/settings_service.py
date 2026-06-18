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

    def get_pos_settings(self) -> Dict[str, Any]:
        """Return the unified settings contract for the touch POS screen.

        POS must use the same barcode scanner settings, units/decimal policy,
        stock policy, printing settings, and profile-aware settings layer as
        invoices and materials.  UI code should not use QSettings directly.
        """
        units = self.get_units_settings()
        inventory = self.get_inventory_settings()
        printing = self.get_printing_settings()
        language = self.get_language_settings()
        profile = self.get_active_profile()
        density = str(self.get('pos/ui/density', 'touch') or 'touch').lower()
        if density not in ('compact', 'comfortable', 'touch'):
            density = 'touch'
        payment = self.get('pos/default_payment_method', self.get('transactions/default_payment_method', 'cash')) or 'cash'
        if payment not in ('cash', 'card', 'credit', 'bank_transfer'):
            payment = 'cash'
        return {
            'use_shifts': self.pos_shifts_enabled(),
            'ui_language': language.get('ui_language', self.get_language()),
            'print_language': language.get('print_language', self.print_language()),
            'quantity_decimals': int(units.get('quantity_decimals', 3) or 3),
            'price_decimals': int(units.get('price_decimals', 2) or 2),
            'rounding_method': units.get('rounding_method', 'HALF_UP') or 'HALF_UP',
            'allow_negative_stock': bool(inventory.get('allow_negative_stock', False)),
            'warn_on_stock_exceed': bool(inventory.get('warn_on_stock_exceed', True)),
            'default_warehouse_id': self.get('pos/default_warehouse_id', self.get('transactions/default_warehouse_id', self.get('warehouse/default_id', ''))),
            'default_cashbox_id': self.get('pos/default_cashbox_id', self.get('cashbox/default_id', '')),
            'default_payment_method': payment,
            'touch_density': density,
            'scan_mode': str(self.get('pos/barcode/scan_mode', 'exact') or 'exact').lower(),
            'auto_focus_scan': self.get_bool('pos/ui/auto_focus_scan', True),
            'receipt_paper': self.get('pos/receipt_paper', printing.get('thermal_size', '80mm')) or '80mm',
            'printing': printing,
            'barcode_scanner': {
                'prefix': self.get('barcode/scanner/prefix', '') or '',
                'suffix': self.get('barcode/scanner/suffix', '') or '',
                'min_length': int(self.get('barcode/scanner/min_length', '6') or 6),
                'numeric_exact': str(self.get('barcode/scanner/numeric_exact', 'true')).lower() == 'true',
            },
            'operations': {
                'allow_checkout': self.get_bool('pos/operations/allow_checkout', True),
                'allow_suspend': self.get_bool('pos/operations/allow_suspend', True),
                'allow_resume': self.get_bool('pos/operations/allow_resume', True),
                'allow_remove_line': self.get_bool('pos/operations/allow_remove_line', True),
                'allow_clear_cart': self.get_bool('pos/operations/allow_clear_cart', True),
                'allow_open_shift': self.get_bool('pos/operations/allow_open_shift', True),
                'allow_close_shift': self.get_bool('pos/operations/allow_close_shift', True),
                'allow_print_receipt': self.get_bool('pos/operations/allow_print_receipt', True),
                'confirm_clear_cart': self.get_bool('pos/operations/confirm_clear_cart', True),
                'confirm_partial_payment': self.get_bool('pos/operations/confirm_partial_payment', True),
            },
            'settings_profile_id': int((profile or {}).get('id') or 1),
        }

    def get_restaurant_settings(self) -> Dict[str, Any]:
        """Return the unified settings contract for Restaurant POS.

        Restaurant workflows must not hard-code touch density, barcode behavior,
        payment defaults, or operation availability. This mirrors POS settings
        while keeping restaurant-specific operations separate from normal POS.
        """
        units = self.get_units_settings()
        printing = self.get_printing_settings()
        language = self.get_language_settings()
        profile = self.get_active_profile()
        density = str(self.get('restaurant/ui/density', self.get('pos/ui/density', 'touch')) or 'touch').lower()
        if density not in ('compact', 'comfortable', 'touch'):
            density = 'touch'
        payment = self.get('restaurant/default_payment_method', self.get('pos/default_payment_method', self.get('transactions/default_payment_method', 'cash'))) or 'cash'
        if payment not in ('cash', 'card', 'credit', 'bank_transfer', 'bank'):
            payment = 'cash'
        return {
            'enabled': self.get_bool('restaurant/enabled', True),
            'ui_language': language.get('ui_language', self.get_language()),
            'print_language': language.get('print_language', self.print_language()),
            'quantity_decimals': int(units.get('quantity_decimals', 3) or 3),
            'price_decimals': int(units.get('price_decimals', 2) or 2),
            'rounding_method': units.get('rounding_method', 'HALF_UP') or 'HALF_UP',
            'touch_density': density,
            'default_payment_method': payment,
            'receipt_paper': self.get('restaurant/receipt_paper', printing.get('thermal_size', '80mm')) or '80mm',
            'kitchen_ticket_paper': self.get('restaurant/kitchen_ticket_paper', self.get('restaurant/receipt_paper', printing.get('thermal_size', '80mm'))) or '80mm',
            'printing': printing,
            'barcode_scanner': {
                'prefix': self.get('barcode/scanner/prefix', '') or '',
                'suffix': self.get('barcode/scanner/suffix', '') or '',
                'min_length': int(self.get('barcode/scanner/min_length', '6') or 6),
                'numeric_exact': str(self.get('barcode/scanner/numeric_exact', 'true')).lower() == 'true',
            },
            'operations': {
                'allow_use': self.get_bool('restaurant/operations/allow_use', True),
                'allow_open_session': self.get_bool('restaurant/operations/allow_open_session', True),
                'allow_add_line': self.get_bool('restaurant/operations/allow_add_line', True),
                'allow_send_kitchen': self.get_bool('restaurant/operations/allow_send_kitchen', True),
                'allow_adjust_bill': self.get_bool('restaurant/operations/allow_adjust_bill', True),
                'allow_record_payment': self.get_bool('restaurant/operations/allow_record_payment', True),
                'allow_checkout': self.get_bool('restaurant/operations/allow_checkout', True),
                'allow_update_kitchen_status': self.get_bool('restaurant/operations/allow_update_kitchen_status', True),
                'allow_print_receipt': self.get_bool('restaurant/operations/allow_print_receipt', True),
                'allow_print_kitchen_ticket': self.get_bool('restaurant/operations/allow_print_kitchen_ticket', True),
                'auto_print_kitchen_ticket': self.get_bool('restaurant/operations/auto_print_kitchen_ticket', False),
                'auto_print_receipt_after_checkout': self.get_bool('restaurant/operations/auto_print_receipt_after_checkout', False),
                'confirm_checkout': self.get_bool('restaurant/operations/confirm_checkout', True),
                'require_kitchen_before_checkout': self.get_bool('restaurant/operations/require_kitchen_before_checkout', False),
            },
            'settings_profile_id': int((profile or {}).get('id') or 1),
        }

    def save_pos_settings(self, use_shifts: bool = False, touch_density: str | None = None,
                          default_payment_method: str | None = None):
        old = self.get_pos_settings()
        self.set('pos/use_shifts', 'true' if use_shifts else 'false')
        if touch_density is not None:
            density = str(touch_density or 'touch').lower()
            if density not in ('compact', 'comfortable', 'touch'):
                density = 'touch'
            self.set('pos/ui/density', density)
        if default_payment_method is not None:
            self.set('pos/default_payment_method', default_payment_method or 'cash')
        self.clear_cache()
        audit_service.log('UPDATE', 'SETTINGS_POS', None, old_values=old, new_values=self.get_pos_settings(), details='تعديل إعدادات نقطة البيع')


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

    def get_branch_settings(self) -> Dict[str, Any]:
        """Return the unified branch-management settings contract.

        Branch screens/services use this profile-aware contract instead of
        direct settings reads so branch master data follows the same governance
        pattern as inventory, manufacturing, POS, and transactions.
        """
        language = self.get_language_settings()
        profile = self.get_active_profile()
        density = str(self.get('branches/ui/density', self.get('inventory/ui/density', 'comfortable')) or 'comfortable').lower()
        if density not in ('compact', 'comfortable', 'touch'):
            density = 'comfortable'
        return {
            'enabled': self.get_bool('branches/enabled', True),
            'ui_language': language.get('ui_language', self.get_language()),
            'print_language': language.get('print_language', self.print_language()),
            'touch_density': density,
            'operations': {
                'allow_use': self.get_bool('branches/operations/allow_use', True),
                'allow_create': self.get_bool('branches/operations/allow_create', True),
                'allow_edit': self.get_bool('branches/operations/allow_edit', True),
                'allow_archive': self.get_bool('branches/operations/allow_archive', True),
                'allow_set_default': self.get_bool('branches/operations/allow_set_default', True),
            },
            'settings_profile_id': int((profile or {}).get('id') or 1),
        }

    def get_finance_settings(self) -> Dict[str, Any]:
        """Return the unified finance/cash-bank settings contract."""
        language = self.get_language_settings()
        profile = self.get_active_profile()
        density = str(self.get('finance/ui/density', self.get('inventory/ui/density', 'comfortable')) or 'comfortable').lower()
        if density not in ('compact', 'comfortable', 'touch'):
            density = 'comfortable'
        return {
            'enabled': self.get_bool('finance/enabled', True),
            'ui_language': language.get('ui_language', self.get_language()),
            'print_language': language.get('print_language', self.print_language()),
            'touch_density': density,
            'operations': {
                'allow_use': self.get_bool('finance/operations/allow_use', True),
                'allow_cashbox_create': self.get_bool('finance/operations/allow_cashbox_create', True),
                'allow_cashbox_edit': self.get_bool('finance/operations/allow_cashbox_edit', True),
                'allow_cashbox_archive': self.get_bool('finance/operations/allow_cashbox_archive', True),
                'allow_bank_create': self.get_bool('finance/operations/allow_bank_create', True),
                'allow_bank_edit': self.get_bool('finance/operations/allow_bank_edit', True),
                'allow_bank_archive': self.get_bool('finance/operations/allow_bank_archive', True),
                'allow_movements_view': self.get_bool('finance/operations/allow_movements_view', True),
                'allow_shifts_view': self.get_bool('finance/operations/allow_shifts_view', True),
                'allow_voucher_create': self.get_bool('finance/operations/allow_voucher_create', True),
                'allow_voucher_edit': self.get_bool('finance/operations/allow_voucher_edit', True),
                'allow_voucher_delete': self.get_bool('finance/operations/allow_voucher_delete', True),
                'allow_voucher_print': self.get_bool('finance/operations/allow_voucher_print', True),
                'allow_voucher_view': self.get_bool('finance/operations/allow_voucher_view', True),
            },
            'settings_profile_id': int((profile or {}).get('id') or 1),
        }

    def get_inventory_settings(self) -> Dict[str, Any]:
        """Return the unified inventory/warehouse settings contract.

        Inventory and warehouse screens/services must use this profile-aware
        contract instead of direct QSettings/SettingsRepository reads.
        """
        language = self.get_language_settings()
        profile = self.get_active_profile()
        units = self.get_units_settings()
        stock_read_mode = self.get_inventory_stock_read_mode()
        cost_method = str(self.get('inventory/cost_method', 'AVERAGE') or 'AVERAGE').upper()
        if cost_method not in ('AVERAGE', 'FIFO', 'LIFO', 'STANDARD', 'LAST_PURCHASE'):
            cost_method = 'AVERAGE'
        density = str(self.get('inventory/ui/density', self.get('transactions/ui/density', 'comfortable')) or 'comfortable').lower()
        if density not in ('compact', 'comfortable', 'touch'):
            density = 'comfortable'
        return {
            'enabled': self.get_bool('inventory/enabled', True),
            'ui_language': language.get('ui_language', self.get_language()),
            'print_language': language.get('print_language', self.print_language()),
            'quantity_decimals': int(units.get('quantity_decimals', 3) or 3),
            'cost_decimals': int(units.get('price_decimals', 2) or 2),
            'rounding_method': units.get('rounding_method', 'HALF_UP') or 'HALF_UP',
            'touch_density': density,
            'allow_negative_stock': self.get_bool('inventory/allow_negative_stock', False),
            'warn_on_stock_exceed': self.get_bool('inventory/warn_on_stock_exceed', True),
            'default_reorder_level': self.get('inventory/default_reorder_level', '0'),
            'cost_method': cost_method,
            'auto_movements': self.get_bool('inventory/auto_movements', True),
            'stock_read_mode': stock_read_mode,
            'default_warehouse_id': self.get('inventory/default_warehouse_id', self.get('warehouse/default_id', '')),
            'print_template': self.get('inventory/print_template', self.get('printing/report_template', 'a4')),
            'operations': {
                'allow_use': self.get_bool('inventory/operations/allow_use', True),
                'allow_warehouse_create': self.get_bool('inventory/operations/allow_warehouse_create', True),
                'allow_warehouse_edit': self.get_bool('inventory/operations/allow_warehouse_edit', True),
                'allow_warehouse_archive': self.get_bool('inventory/operations/allow_warehouse_archive', True),
                'allow_balance_view': self.get_bool('inventory/operations/allow_balance_view', True),
                'allow_movement_view': self.get_bool('inventory/operations/allow_movement_view', True),
                'allow_direct_movement': self.get_bool('inventory/operations/allow_direct_movement', True),
                'allow_transfer_create': self.get_bool('inventory/operations/allow_transfer_create', True),
                'allow_transfer_cancel': self.get_bool('inventory/operations/allow_transfer_cancel', True),
                'allow_ledger_view': self.get_bool('inventory/operations/allow_ledger_view', True),
                'allow_ledger_backfill': self.get_bool('inventory/operations/allow_ledger_backfill', False),
                'allow_reconcile': self.get_bool('inventory/operations/allow_reconcile', True),
                'allow_print': self.get_bool('inventory/operations/allow_print', True),
                'confirm_transfer_cancel': self.get_bool('inventory/operations/confirm_transfer_cancel', True),
            },
            'settings_profile_id': int((profile or {}).get('id') or 1),
        }

    def get_units_settings(self) -> Dict[str, Any]:
        return {
            'default_sales_unit': self.get('units/default_sales_unit', self.get('units/default_sale_unit', '')) or '',
            'default_purchase_unit': self.get('units/default_purchase_unit', '') or '',
            'quantity_decimals': self.get_decimal_places('units/quantity_decimals', 3),
            'price_decimals': self.get_decimal_places('units/price_decimals', 2),
            'rounding_method': self.get('units/rounding_method', 'HALF_UP') or 'HALF_UP',
        }



    def get_party_settings(self) -> Dict[str, Any]:
        """Return settings contract for customer/supplier master-data screens."""
        language = self.get_language_settings()
        profile = self.get_active_profile()
        return {
            'enabled': self.get_bool('parties/enabled', True),
            'ui_language': language.get('ui_language', self.get_language()),
            'print_language': language.get('print_language', self.print_language()),
            'touch_density': self.get('parties/touch_density', self.get('ui/touch_density', 'comfortable')) or 'comfortable',
            'operations': {
                'allow_use': self.get_bool('parties/operations/allow_use', True),
                'allow_customer_view': self.get_bool('parties/operations/allow_customer_view', True),
                'allow_customer_create': self.get_bool('parties/operations/allow_customer_create', True),
                'allow_customer_edit': self.get_bool('parties/operations/allow_customer_edit', True),
                'allow_customer_delete': self.get_bool('parties/operations/allow_customer_delete', True),
                'allow_supplier_view': self.get_bool('parties/operations/allow_supplier_view', True),
                'allow_supplier_create': self.get_bool('parties/operations/allow_supplier_create', True),
                'allow_supplier_edit': self.get_bool('parties/operations/allow_supplier_edit', True),
                'allow_supplier_delete': self.get_bool('parties/operations/allow_supplier_delete', True),
            },
            'settings_profile_id': int((profile or {}).get('id') or 1),
        }


    def get_category_settings(self) -> Dict[str, Any]:
        """Return settings contract for material-category master data screens."""
        language = self.get_language_settings()
        profile = self.get_active_profile()
        return {
            'enabled': self.get_bool('categories/enabled', True),
            'ui_language': language.get('ui_language', self.get_language()),
            'print_language': language.get('print_language', self.print_language()),
            'touch_density': self.get('categories/touch_density', self.get('ui/touch_density', 'comfortable')) or 'comfortable',
            'operations': {
                'allow_use': self.get_bool('categories/operations/allow_use', True),
                'allow_create': self.get_bool('categories/operations/allow_create', True),
                'allow_edit': self.get_bool('categories/operations/allow_edit', True),
                'allow_archive': self.get_bool('categories/operations/allow_archive', True),
                'allow_restore': self.get_bool('categories/operations/allow_restore', True),
            },
            'settings_profile_id': int((profile or {}).get('id') or 1),
        }

    def get_material_settings(self) -> Dict[str, Any]:
        """Return the unified settings contract for material master-data screens.

        Material editors must not hard-code barcode defaults, label options,
        unit decimals, or inventory policy.  This contract is profile-aware
        through SettingsService.get() and intentionally reuses the existing
        printing/barcode settings.
        """
        printing = self.get_printing_settings()
        units = self.get_units_settings()
        inventory = self.get_inventory_settings()
        raw_sym = str(self.get('materials/barcode/default_symbology', self.get('items/barcode/default_symbology', 'EAN13')) or 'EAN13').upper()
        if raw_sym not in ('EAN13', 'CODE128'):
            raw_sym = 'EAN13'
        return {
            'default_barcode_symbology': raw_sym,
            'auto_generate_barcode_for_new_material': str(self.get('materials/barcode/auto_generate', self.get('items/barcode/auto_generate', 'true'))).lower() == 'true',
            'require_barcode_for_stock_items': str(self.get('materials/barcode/require_for_stock_items', self.get('items/barcode/require_for_stock_items', 'false'))).lower() == 'true',
            'allow_manual_barcode_edit': str(self.get('materials/barcode/allow_manual_edit', self.get('items/barcode/allow_manual_edit', 'true'))).lower() == 'true',
            'ean13_internal_prefix': self.get('materials/barcode/ean13_prefix', self.get('items/barcode/ean13_prefix', '290')) or '290',
            'code128_prefix': self.get('materials/barcode/code128_prefix', self.get('items/barcode/code128_prefix', 'ITM')) or 'ITM',
            'default_unit': self.get('materials/default_unit', self.get('items/default_unit', self.get('units/default_base_unit', 'قطعة'))) or 'قطعة',
            'default_item_type': self.get('materials/default_item_type', self.get('items/default_item_type', 'مخزون')) or 'مخزون',
            'quantity_decimals': int(units.get('quantity_decimals', 3) or 3),
            'price_decimals': int(units.get('price_decimals', 2) or 2),
            'rounding_method': units.get('rounding_method', 'HALF_UP') or 'HALF_UP',
            'default_reorder_level': inventory.get('default_reorder_level', '0'),
            'allow_negative_stock': bool(inventory.get('allow_negative_stock', False)),
            'prevent_opening_quantity_edit_after_activity': self.get_bool('materials/security/prevent_opening_quantity_edit_after_activity', self.get_bool('items/security/prevent_opening_quantity_edit_after_activity', True)),
            'hide_cost_for_non_admin': self.get_bool('materials/security/hide_cost_for_non_admin', self.get_bool('security/hide_item_cost_for_non_admin', self.get_bool('security/hide_profit_for_non_admin', False))),
            'require_unique_unit_names': self.get_bool('materials/units/require_unique_names', True),
            'require_unit_barcode_validation': self.get_bool('materials/units/validate_unit_barcodes', True),
            'allow_unit_barcode_duplicates': self.get_bool('materials/units/allow_barcode_duplicates', False),
            'barcode_label_options': {
                'label_size': printing.get('barcode_label_size', '50x30'),
                'symbology': printing.get('barcode_symbology', 'AUTO'),
                'copies': int(printing.get('barcode_copies', 1) or 1),
                'columns': int(printing.get('barcode_columns', 2) or 2),
                'show_company': bool(printing.get('barcode_show_company', True)),
                'show_logo': bool(printing.get('barcode_show_logo', True)),
                'show_qr': bool(printing.get('barcode_show_qr', True)),
                'show_name': bool(printing.get('barcode_show_name', True)),
                'show_price': bool(printing.get('barcode_show_price', True)),
                'show_barcode_text': bool(printing.get('barcode_show_text', True)),
            },
        }

    def get_transaction_settings(self, document_type: str = 'sales_invoice') -> Dict[str, Any]:
        """Return the unified settings contract for invoice-like transaction screens.

        UI code should not collect decimals, stock policy, default payment,
        printing language, barcode-scanner behavior, or profile data from
        scattered QSettings fragments.  This method centralizes that contract
        while remaining profile-aware through SettingsService.get().
        """
        inventory = self.get_inventory_settings()
        units = self.get_units_settings()
        printing = self.get_printing_settings()
        language = self.get_language_settings()
        profile = self.get_active_profile()
        return {
            'document_type': document_type or 'sales_invoice',
            'ui_language': language.get('ui_language', self.get_language()),
            'print_language': language.get('print_language', self.print_language()),
            'quantity_decimals': units.get('quantity_decimals', 3),
            'price_decimals': units.get('price_decimals', 2),
            'rounding_method': units.get('rounding_method', 'HALF_UP'),
            'allow_negative_stock': bool(inventory.get('allow_negative_stock', False)),
            'warn_on_stock_exceed': bool(inventory.get('warn_on_stock_exceed', True)),
            'default_warehouse_id': self.get('transactions/default_warehouse_id', self.get('warehouse/default_id', '')),
            'default_payment_method': self.get('transactions/default_payment_method', self.get('payment/default_method', 'cash')) or 'cash',
            'line_grid_default_preset': self.get(f'transactions/{document_type}/default_preset', self.get('transactions/default_preset', 'manager')) or 'manager',
            'line_grid_auto_responsive': str(self.get('transactions/grid/auto_responsive', 'true')).lower() == 'true',
            'show_profit': str(self.get('transactions/show_profit', 'true')).lower() == 'true',
            'show_cost': str(self.get('transactions/show_cost', 'true')).lower() == 'true',
            'print_template': printing.get('return_template') if 'return' in str(document_type) else printing.get('invoice_template'),
            'printing': printing,
            'barcode_scanner': {
                'prefix': self.get('barcode/scanner/prefix', '') or '',
                'suffix': self.get('barcode/scanner/suffix', '') or '',
                'min_length': int(self.get('barcode/scanner/min_length', '6') or 6),
                'numeric_exact': str(self.get('barcode/scanner/numeric_exact', 'true')).lower() == 'true',
            },
            'settings_profile_id': int((profile or {}).get('id') or 1),
        }



    def get_manufacturing_settings(self) -> Dict[str, Any]:
        """Return the unified settings contract for manufacturing workflows.

        Manufacturing tabs and services must not read QSettings directly. This
        contract centralizes warehouses, units, costing, barcode scanner,
        printing, language, operation switches, and active settings profile.
        """
        units = self.get_units_settings()
        inventory = self.get_inventory_settings()
        printing = self.get_printing_settings()
        language = self.get_language_settings()
        profile = self.get_active_profile()
        density = str(self.get('manufacturing/ui/density', self.get('transactions/ui/density', 'comfortable')) or 'comfortable').lower()
        if density not in ('compact', 'comfortable', 'touch'):
            density = 'comfortable'
        costing = str(self.get('manufacturing/costing_method', inventory.get('cost_method', 'AVERAGE')) or 'AVERAGE').upper()
        if costing not in ('AVERAGE', 'FIFO', 'LIFO', 'STANDARD', 'LAST_PURCHASE'):
            costing = 'AVERAGE'
        return {
            'enabled': self.get_bool('manufacturing/enabled', True),
            'ui_language': language.get('ui_language', self.get_language()),
            'print_language': language.get('print_language', self.print_language()),
            'quantity_decimals': int(units.get('quantity_decimals', 3) or 3),
            'cost_decimals': int(units.get('price_decimals', 2) or 2),
            'rounding_method': units.get('rounding_method', 'HALF_UP') or 'HALF_UP',
            'touch_density': density,
            'default_raw_warehouse_id': self.get('manufacturing/default_raw_warehouse_id', self.get('warehouse/default_id', '')),
            'default_output_warehouse_id': self.get('manufacturing/default_output_warehouse_id', self.get('warehouse/default_id', '')),
            'allow_negative_raw_consumption': self.get_bool('manufacturing/allow_negative_raw_consumption', inventory.get('allow_negative_stock', False)),
            'warn_when_material_shortage': self.get_bool('manufacturing/warn_when_material_shortage', True),
            'auto_reserve_on_order_create': self.get_bool('manufacturing/auto_reserve_on_order_create', False),
            'allow_partial_consumption': self.get_bool('manufacturing/allow_partial_consumption', True),
            'allow_over_consumption': self.get_bool('manufacturing/allow_over_consumption', False),
            'allow_reverse_completed_order': self.get_bool('manufacturing/allow_reverse_completed_order', True),
            'costing_method': costing,
            'bom_default_unit': self.get('manufacturing/bom_default_unit', units.get('default_purchase_unit', units.get('default_sales_unit', ''))) or '',
            'print_template': self.get('printing/manufacturing_template', printing.get('report_template', printing.get('default_paper', 'a4'))) or 'a4',
            'printing': printing,
            'barcode_scanner': {
                'prefix': self.get('barcode/scanner/prefix', '') or '',
                'suffix': self.get('barcode/scanner/suffix', '') or '',
                'min_length': int(self.get('barcode/scanner/min_length', '6') or 6),
                'numeric_exact': str(self.get('barcode/scanner/numeric_exact', 'true')).lower() == 'true',
            },
            'operations': {
                'allow_use': self.get_bool('manufacturing/operations/allow_use', True),
                'allow_bom_create': self.get_bool('manufacturing/operations/allow_bom_create', True),
                'allow_bom_edit': self.get_bool('manufacturing/operations/allow_bom_edit', True),
                'allow_bom_delete': self.get_bool('manufacturing/operations/allow_bom_delete', True),
                'allow_order_create': self.get_bool('manufacturing/operations/allow_order_create', True),
                'allow_order_start': self.get_bool('manufacturing/operations/allow_order_start', True),
                'allow_material_consume': self.get_bool('manufacturing/operations/allow_material_consume', True),
                'allow_output_complete': self.get_bool('manufacturing/operations/allow_output_complete', True),
                'allow_order_cancel': self.get_bool('manufacturing/operations/allow_order_cancel', True),
                'allow_order_delete': self.get_bool('manufacturing/operations/allow_order_delete', True),
                'allow_order_reverse': self.get_bool('manufacturing/operations/allow_order_reverse', True),
                'allow_consumption_delete': self.get_bool('manufacturing/operations/allow_consumption_delete', True),
                'allow_output_delete': self.get_bool('manufacturing/operations/allow_output_delete', True),
                'allow_print': self.get_bool('manufacturing/operations/allow_print', True),
                'confirm_reverse': self.get_bool('manufacturing/operations/confirm_reverse', True),
                'confirm_delete': self.get_bool('manufacturing/operations/confirm_delete', True),
            },
            'settings_profile_id': int((profile or {}).get('id') or 1),
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
            return self.gateway.audit_rows(limit)
        except AttributeError:
            return []
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


    # ========== User management settings (Phase 206) ==========
    def get_user_settings(self) -> Dict[str, Any]:
        """Return the unified user-management settings contract.

        User management controls access to all modules, so it must be governed
        centrally rather than left to legacy dialogs.
        """
        language = self.get_language_settings()
        profile = self.get_active_profile()
        density = str(self.get('users/ui/density', self.get('inventory/ui/density', 'comfortable')) or 'comfortable').lower()
        if density not in ('compact', 'comfortable', 'touch'):
            density = 'comfortable'
        return {
            'enabled': self.get_bool('users/enabled', True),
            'ui_language': language.get('ui_language', self.get_language()),
            'print_language': language.get('print_language', self.print_language()),
            'touch_density': density,
            'operations': {
                'allow_use': self.get_bool('users/operations/allow_use', True),
                'allow_create': self.get_bool('users/operations/allow_create', True),
                'allow_edit': self.get_bool('users/operations/allow_edit', True),
                'allow_delete': self.get_bool('users/operations/allow_delete', False),
                'allow_change_password': self.get_bool('users/operations/allow_change_password', True),
            },
            'settings_profile_id': int((profile or {}).get('id') or 1),
        }


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
        try:
            return self.gateway.export_settings_dict()
        except AttributeError:
            return {k: self.get(k, '') for k in []}
        except Exception:
            return {}

    def import_settings_dict(self, payload: Dict[str, Any]):
        try:
            if hasattr(self.gateway, 'import_settings_dict'):
                self.gateway.import_settings_dict(payload or {})
                self.clear_cache()
                return
        except Exception:
            pass
        for key, value in dict(payload or {}).items():
            self.set(str(key), value)
        self.clear_cache()


    # ========== Settings Profiles (Phase 148) ==========
    def _profile_conn(self):
        # Database connections belong behind the SettingsGateway boundary.
        return None

    def _profile_value(self, key: str, default: Any = None) -> Any:
        try:
            return self.gateway.profile_value(key, default)
        except AttributeError:
            return default
        except Exception:
            return default

    def list_profiles(self):
        try:
            return self.gateway.list_profiles()
        except AttributeError:
            return []
        except Exception:
            return []

    def get_active_profile(self) -> Dict[str, Any]:
        try:
            return self.gateway.get_active_profile()
        except AttributeError:
            return {'id': 1, 'name': 'Default', 'description': '', 'is_active': 1, 'settings_count': 0}
        except Exception:
            return {'id': 1, 'name': 'Default', 'description': '', 'is_active': 1, 'settings_count': 0}

    def create_profile(self, name: str, description: str = '') -> int:
        if not hasattr(self.gateway, 'create_profile'):
            raise RuntimeError('Profiles are available in local mode only')
        return int(self.gateway.create_profile(name, description))

    def set_active_profile(self, profile_id: int):
        if hasattr(self.gateway, 'set_active_profile'):
            self.gateway.set_active_profile(profile_id)
            self.clear_cache()

    def set_profile_value(self, profile_id: int, key: str, value: Any):
        if hasattr(self.gateway, 'set_profile_value'):
            self.gateway.set_profile_value(profile_id, key, value)

    def _log_profile_setting_change(self, profile_id: int, profile_name: str, key: str, old_value: Any, new_value: Any):
        if hasattr(self.gateway, 'log_profile_setting_change'):
            try:
                self.gateway.log_profile_setting_change(profile_id, profile_name, key, old_value, new_value)
            except Exception:
                pass

    def clone_profile(self, source_profile_id: int, new_name: str) -> int:
        if not hasattr(self.gateway, 'clone_profile'):
            raise RuntimeError('Profiles are available in local mode only')
        return int(self.gateway.clone_profile(source_profile_id, new_name))

    def export_profile_dict(self, profile_id: int | None = None) -> Dict[str, Any]:
        try:
            return self.gateway.export_profile_dict(profile_id)
        except AttributeError:
            return {}
        except Exception:
            return {}

    def import_profile_dict(self, payload: Dict[str, Any]) -> int:
        if not hasattr(self.gateway, 'import_profile_dict'):
            raise RuntimeError('Profiles are available in local mode only')
        return int(self.gateway.import_profile_dict(payload))

    def profile_health(self) -> Dict[str, Any]:
        try:
            return self.gateway.profile_health()
        except AttributeError:
            return {'active_profile': self.get_active_profile(), 'missing_settings': [], 'missing_count': 0}
        except Exception:
            return {'active_profile': self.get_active_profile(), 'missing_settings': [], 'missing_count': 0}


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
