# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, Iterable, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QCheckBox, QComboBox, QFormLayout, QFrame, QLabel, QLineEdit, QPushButton, QSpinBox, QTextEdit, QVBoxLayout, QWidget

from core.services.settings_service import settings_service
from i18n import qt_layout_direction, translate
from utils import show_toast
from workspace.documents import BaseDocumentTab
from workspace.documents.document_contract import descriptor_for

FieldSpec = Tuple[str, str, str]


class SettingsSectionForm(QFrame):
    """Reusable settings form panel bound to SettingsService keys."""

    def __init__(self, fields: Iterable[FieldSpec], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName('FormCard')
        self._widgets: Dict[str, QWidget] = {}
        form = QFormLayout(self)
        form.setLabelAlignment(Qt.AlignRight)
        for key, label_key, field_type in fields:
            widget = self._make_widget(key, field_type)
            self._widgets[key] = widget
            form.addRow(translate(label_key), widget)

    def _make_widget(self, key: str, field_type: str) -> QWidget:
        current = settings_service.get(key, '')
        if field_type == 'bool':
            w = QCheckBox()
            w.setChecked(str(current).lower() in ('1', 'true', 'yes', 'on'))
            return w
        if field_type.startswith('choice:'):
            w = QComboBox()
            for option in field_type.split(':', 1)[1].split('|'):
                w.addItem(option, option)
            idx = w.findData(str(current))
            if idx >= 0:
                w.setCurrentIndex(idx)
            return w
        if field_type == 'int':
            w = QSpinBox()
            w.setRange(0, 999999)
            try:
                w.setValue(int(current or 0))
            except Exception:
                w.setValue(0)
            return w
        if field_type == 'text':
            w = QTextEdit()
            w.setMaximumHeight(100)
            w.setPlainText(str(current or ''))
            return w
        w = QLineEdit()
        w.setText(str(current or ''))
        return w

    def values(self) -> Dict[str, str]:
        data: Dict[str, str] = {}
        for key, widget in self._widgets.items():
            if isinstance(widget, QCheckBox):
                data[key] = 'true' if widget.isChecked() else 'false'
            elif isinstance(widget, QComboBox):
                data[key] = str(widget.currentData())
            elif isinstance(widget, QSpinBox):
                data[key] = str(widget.value())
            elif isinstance(widget, QTextEdit):
                data[key] = widget.toPlainText().strip()
            elif isinstance(widget, QLineEdit):
                data[key] = widget.text().strip()
        return data

    def connect_changed(self, callback) -> None:
        for widget in self._widgets.values():
            if isinstance(widget, QCheckBox):
                widget.stateChanged.connect(lambda _state: callback())
            elif isinstance(widget, QComboBox):
                widget.currentIndexChanged.connect(lambda _index: callback())
            elif isinstance(widget, QSpinBox):
                widget.valueChanged.connect(lambda _value: callback())
            elif isinstance(widget, QTextEdit):
                widget.textChanged.connect(callback)
            elif isinstance(widget, QLineEdit):
                widget.textChanged.connect(lambda _text: callback())


class SettingsSectionDocumentTab(BaseDocumentTab):
    DOCUMENT_DESCRIPTOR = descriptor_for("settings_section")
    """Base document tab for settings sections.

    Settings are persisted through SettingsService only.  The tab can be opened
    independently in the workspace and participates in dirty-state/save flows.
    """

    section_key = 'settings.general'
    icon_name = 'fa5s.sliders-h'
    fields: Tuple[FieldSpec, ...] = ()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__('settings', document_id=None, parent=parent)
        self._build_ui()
        self.set_document_title(self.workspace_title())
        self.set_dirty(False)

    def workspace_title(self) -> str:
        return translate(self.section_key)

    def _build_ui(self) -> None:
        self.setLayoutDirection(qt_layout_direction())
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)
        header = QFrame(self)
        header.setObjectName('DocumentHeaderCard')
        h = QVBoxLayout(header)
        h.setContentsMargins(16, 12, 16, 12)
        title = QLabel(self.workspace_title())
        title.setObjectName('DocumentTitle')
        h.addWidget(title)
        hint = QLabel(translate('settings_document_hint'))
        hint.setWordWrap(True)
        h.addWidget(hint)
        save_btn = QPushButton(translate('save'))
        save_btn.setObjectName('primary')
        save_btn.clicked.connect(self.workspace_save)
        h.addWidget(save_btn, 0, Qt.AlignRight)
        root.addWidget(header)
        self.form = SettingsSectionForm(self.fields, self)
        self.form.connect_changed(lambda: self.set_dirty(True))
        root.addWidget(self.form)
        root.addStretch(1)
        self.setStyleSheet('''
            QFrame#DocumentHeaderCard, QFrame#FormCard { border: 1px solid palette(mid); border-radius: 14px; background: palette(base); }
            QLabel#DocumentTitle { font-size: 18px; font-weight: 900; }
            QLineEdit, QComboBox, QTextEdit, QSpinBox { min-height: 34px; padding: 5px 9px; }
            QPushButton#primary { font-weight: 900; padding: 8px 16px; }
        ''')

    def workspace_save(self) -> None:
        try:
            for key, value in self.form.values().items():
                settings_service.set(key, value)
            settings_service.clear_cache()
            self.set_dirty(False)
            self.saved.emit(self.section_key)
            show_toast(translate('settings_saved'), 'success', self)
        except Exception as exc:
            show_toast(str(exc), 'error', self)


class CompanySettingsTab(SettingsSectionDocumentTab):
    section_key = 'settings.company'
    fields = (
        ('company/name', 'company_name', 'string'),
        ('company/tax_number', 'tax_number', 'string'),
        ('company/address', 'address', 'text'),
        ('company/phone', 'phone', 'string'),
    )


class AccountingSettingsTab(SettingsSectionDocumentTab):
    section_key = 'settings.accounting'
    fields = (
        ('base_currency', 'base_currency', 'string'),
        ('display_currency', 'display_currency', 'string'),
        ('currency_decimals', 'currency_decimals', 'int'),
        ('number_format', 'number_format', 'choice:standard|western|arabic'),
        ('abbreviate_numbers', 'abbreviate_numbers', 'bool'),
    )


class TransactionsSettingsTab(SettingsSectionDocumentTab):
    section_key = 'settings.transactions'
    fields = (
        ('invoice/sales_prefix', 'invoice_sales_prefix', 'string'),
        ('invoice/purchase_prefix', 'invoice_purchase_prefix', 'string'),
        ('invoice/number_format', 'invoice_number_format', 'string'),
        ('invoice/auto_numbering', 'invoice_auto_numbering', 'bool'),
        ('transactions/default_warehouse_id', 'default_warehouse', 'string'),
        ('transactions/default_payment_method', 'default_payment_method', 'choice:cash|card|credit|bank_transfer'),
        ('transactions/grid/auto_responsive', 'transactions_grid_auto_responsive', 'bool'),
        ('transactions/show_profit', 'show_profit', 'bool'),
        ('transactions/show_cost', 'show_cost', 'bool'),
        ('transactions/default_preset', 'transactions_default_preset', 'choice:compact|cashier|manager'),
        ('barcode/scanner/min_length', 'barcode_scanner_min_length', 'int'),
    )


class MaterialsSettingsTab(SettingsSectionDocumentTab):
    section_key = 'settings.materials'
    fields = (
        ('materials/default_unit', 'default_unit', 'string'),
        ('materials/default_item_type', 'default_item_type', 'string'),
        ('materials/barcode/default_symbology', 'barcode_symbology', 'choice:EAN13|CODE128'),
        ('materials/barcode/auto_generate', 'barcode_auto_generate', 'bool'),
        ('materials/barcode/allow_manual_edit', 'barcode_allow_manual_edit', 'bool'),
        ('materials/barcode/ean13_prefix', 'barcode_ean13_prefix', 'string'),
        ('materials/units/require_unique_names', 'require_unique_unit_names', 'bool'),
        ('materials/units/validate_unit_barcodes', 'validate_unit_barcodes', 'bool'),
        ('materials/security/prevent_opening_quantity_edit_after_activity', 'prevent_opening_quantity_edit_after_activity', 'bool'),
    )


class PartiesSettingsTab(SettingsSectionDocumentTab):
    section_key = 'settings.parties'
    fields = (
        ('parties/default_credit_limit', 'default_credit_limit', 'string'),
        ('parties/ui/density', 'touch_density', 'choice:compact|comfortable|touch'),
        ('parties/operations/allow_create', 'allow_create', 'bool'),
        ('parties/operations/allow_edit', 'allow_edit', 'bool'),
        ('parties/operations/allow_archive', 'allow_archive', 'bool'),
        ('parties/operations/allow_statement_print', 'allow_statement_print', 'bool'),
    )


class FinanceSettingsTab(SettingsSectionDocumentTab):
    section_key = 'settings.finance'
    fields = (
        ('finance/enabled', 'enabled', 'bool'),
        ('finance/ui/density', 'touch_density', 'choice:compact|comfortable|touch'),
        ('finance/operations/allow_voucher_create', 'allow_voucher_create', 'bool'),
        ('finance/operations/allow_voucher_edit', 'allow_voucher_edit', 'bool'),
        ('finance/operations/allow_voucher_print', 'allow_voucher_print', 'bool'),
        ('finance/operations/allow_expense_create', 'allow_expense_create', 'bool'),
        ('finance/operations/allow_expense_print', 'allow_expense_print', 'bool'),
    )


class InventorySettingsTab(SettingsSectionDocumentTab):
    section_key = 'settings.inventory'
    fields = (
        ('inventory/default_warehouse_id', 'default_warehouse', 'string'),
        ('inventory/negative_stock_allowed', 'negative_stock_allowed', 'bool'),
        ('inventory/low_stock_alerts', 'low_stock_alerts', 'bool'),
        ('inventory/unit_conversion_strict', 'unit_conversion_strict', 'bool'),
    )


class BranchesSettingsTab(SettingsSectionDocumentTab):
    section_key = 'settings.branches'
    fields = (
        ('branches/enabled', 'enabled', 'bool'),
        ('branches/ui/density', 'touch_density', 'choice:compact|comfortable|touch'),
        ('branches/operations/allow_create', 'allow_create', 'bool'),
        ('branches/operations/allow_edit', 'allow_edit', 'bool'),
        ('branches/operations/allow_archive', 'allow_archive', 'bool'),
        ('branches/operations/allow_set_default', 'allow_set_default', 'bool'),
    )


class CategoriesSettingsTab(SettingsSectionDocumentTab):
    section_key = 'settings.categories'
    fields = (
        ('categories/enabled', 'enabled', 'bool'),
        ('categories/ui/density', 'touch_density', 'choice:compact|comfortable|touch'),
        ('categories/operations/allow_create', 'allow_create', 'bool'),
        ('categories/operations/allow_edit', 'allow_edit', 'bool'),
        ('categories/operations/allow_archive', 'allow_archive', 'bool'),
    )


class ManufacturingSettingsTab(SettingsSectionDocumentTab):
    section_key = 'settings.manufacturing'
    fields = (
        ('manufacturing/enabled', 'enabled', 'bool'),
        ('manufacturing/default_raw_warehouse_id', 'default_raw_warehouse', 'string'),
        ('manufacturing/default_output_warehouse_id', 'default_output_warehouse', 'string'),
        ('manufacturing/costing_method', 'costing_method', 'choice:AVERAGE|FIFO|LIFO|STANDARD|LAST_PURCHASE'),
        ('manufacturing/allow_negative_raw_consumption', 'allow_negative_raw_consumption', 'bool'),
        ('manufacturing/operations/allow_print', 'allow_print', 'bool'),
        ('manufacturing/operations/allow_order_cancel', 'allow_order_cancel', 'bool'),
    )


class ReportsSettingsTab(SettingsSectionDocumentTab):
    section_key = 'settings.reports'
    fields = (
        ('reports/enabled', 'enabled', 'bool'),
        ('language/report', 'report_language', 'choice:ar|en|de'),
        ('reports/default_export_format', 'default_export_format', 'choice:pdf|xlsx|csv|html'),
        ('reports/operations/allow_view', 'allow_view', 'bool'),
        ('reports/operations/allow_print', 'allow_print', 'bool'),
        ('reports/operations/allow_export', 'allow_export', 'bool'),
    )


class PosSettingsTab(SettingsSectionDocumentTab):
    section_key = 'settings.pos'
    fields = (
        ('pos/use_shifts', 'use_shifts', 'bool'),
        ('pos/ui/density', 'touch_density', 'choice:compact|comfortable|touch'),
        ('pos/default_warehouse_id', 'default_warehouse', 'string'),
        ('pos/default_cashbox_id', 'default_cashbox', 'string'),
        ('pos/default_payment_method', 'default_payment_method', 'choice:cash|card|credit|bank_transfer'),
        ('pos/receipt_paper', 'receipt_paper', 'choice:80mm|58mm'),
        ('pos/receipt_show_logo', 'pos_receipt_show_logo', 'bool'),
        ('pos/receipt_show_qr', 'pos_receipt_show_qr', 'bool'),
        ('pos/operations/allow_checkout', 'allow_checkout', 'bool'),
        ('pos/operations/allow_print_receipt', 'allow_print_receipt', 'bool'),
    )


class UsersSettingsTab(SettingsSectionDocumentTab):
    section_key = 'settings.users'
    fields = (
        ('users/enabled', 'enabled', 'bool'),
        ('users/ui/density', 'touch_density', 'choice:compact|comfortable|touch'),
        ('users/operations/allow_create', 'allow_create', 'bool'),
        ('users/operations/allow_edit', 'allow_edit', 'bool'),
        ('users/operations/allow_disable', 'allow_disable', 'bool'),
    )


class RestaurantSettingsTab(SettingsSectionDocumentTab):
    section_key = 'settings.restaurant'
    fields = (
        ('restaurant/enabled', 'enabled', 'bool'),
        ('restaurant/ui/density', 'touch_density', 'choice:compact|comfortable|touch'),
        ('restaurant/default_payment_method', 'default_payment_method', 'choice:cash|card|credit|bank_transfer|bank'),
        ('restaurant/receipt_paper', 'receipt_paper', 'choice:80mm|58mm'),
        ('restaurant/kitchen_ticket_paper', 'kitchen_ticket_paper', 'choice:80mm|58mm'),
        ('restaurant/session_summary_paper', 'session_summary_paper', 'choice:80mm|58mm'),
        ('restaurant/printing/receipt_printer', 'restaurant_receipt_printer', 'string'),
        ('restaurant/printing/kitchen_printer', 'restaurant_kitchen_printer', 'string'),
        ('restaurant/printing/session_summary_printer', 'restaurant_session_summary_printer', 'string'),
        ('restaurant/touch_mode', 'touch_mode', 'bool'),
        ('restaurant/ui/show_kitchen_panel', 'show_kitchen_panel', 'bool'),
        ('restaurant/ui/show_analytics_panel', 'show_analytics_panel', 'bool'),
        ('restaurant/ui/table_card_density', 'table_card_density', 'choice:compact|comfortable|touch'),
        ('restaurant/service_charge_percent', 'service_charge_percent', 'string'),
        ('restaurant/default_tax_percent', 'default_tax_percent', 'string'),
        ('restaurant/consume_inventory_on', 'consume_inventory_on', 'choice:checkout|served'),
        ('restaurant/operations/allow_checkout', 'allow_checkout', 'bool'),
        ('restaurant/operations/allow_print_receipt', 'allow_print_receipt', 'bool'),
        ('restaurant/operations/allow_print_kitchen_ticket', 'allow_print_kitchen_ticket', 'bool'),
        ('restaurant/operations/auto_print_kitchen_ticket', 'auto_print_kitchen_ticket', 'bool'),
        ('restaurant/operations/auto_print_receipt_after_checkout', 'auto_print_receipt_after_checkout', 'bool'),
        ('restaurant/operations/auto_print_session_summary_after_checkout', 'auto_print_session_summary_after_checkout', 'bool'),
    )


class CafeSettingsTab(SettingsSectionDocumentTab):
    section_key = 'settings.cafe'
    fields = (
        ('cafe/enabled', 'settings.cafe_enabled', 'bool'),
        ('cafe/auto_open_quick_order', 'settings.cafe_auto_open_quick_order', 'bool'),
        ('cafe/quick_order_type', 'restaurant.cafe_quick_order', 'choice:cafe_quick_order'),
        ('cafe/preparation_route', 'restaurant.cafe_preparation', 'choice:barista'),
        ('cafe/receipt_paper', 'receipt_paper', 'choice:80mm|58mm'),
        ('cafe/barista_ticket_paper', 'restaurant.cafe_print_barista_ticket', 'choice:80mm|58mm'),
        ('cafe/printing/receipt_printer', 'restaurant.cafe_print_receipt', 'string'),
        ('cafe/printing/barista_printer', 'restaurant.cafe_preparation', 'string'),
    )


class ApparelSettingsTab(SettingsSectionDocumentTab):
    section_key = 'settings.apparel'
    fields = (
        ('apparel/enabled', 'settings.apparel_enabled', 'bool'),
        ('apparel/default_size_set', 'apparel.default_size_set', 'string'),
        ('apparel/default_color_set', 'apparel.default_color_set', 'string'),
        ('apparel/barcode_required', 'apparel.barcode_required', 'bool'),
        ('apparel/ui/density', 'touch_density', 'choice:compact|comfortable|touch'),
    )


class PrintingSettingsTab(SettingsSectionDocumentTab):
    section_key = 'settings.printing'
    fields = (
        ('language/print', 'settings_print_language_label', 'choice:ar|en|de'),
        ('printing/invoice_template', 'invoice_template', 'choice:a4|thermal80|thermal58'),
        ('printing/report_template', 'report_template', 'choice:a4|compact|thermal80|thermal58'),
        ('printing/voucher_template', 'settings_print_voucher_template_label', 'choice:a4|thermal80|thermal58'),
        ('printing/return_template', 'settings_print_return_template_label', 'choice:a4|thermal80|thermal58'),
        ('printing/thermal_size', 'settings_print_thermal_size_label', 'choice:80mm|58mm'),
        ('printing/show_logo', 'show_logo', 'bool'),
        ('printing/show_company_name', 'settings_print_show_company_name', 'bool'),
        ('printing/show_address', 'settings_print_show_address', 'bool'),
        ('printing/show_phone', 'settings_print_show_phone', 'bool'),
        ('printing/show_email', 'settings_print_show_email', 'bool'),
        ('printing/show_tax_number', 'settings_print_show_tax', 'bool'),
        ('printing/show_commercial_register', 'settings_print_show_commercial_register', 'bool'),
        ('printing/show_website', 'settings_print_show_website', 'bool'),
        ('printing/show_qr', 'show_qr', 'bool'),
        ('printing/accent_color', 'settings_print_accent_color_label', 'string'),
        ('printing/font_family', 'settings_print_font_label', 'string'),
        ('printing/font_size', 'settings_print_font_size_label', 'choice:9.5pt|10pt|10.5pt|11pt|12pt'),
        ('printing/zebra_rows', 'settings_print_zebra_rows', 'bool'),
        ('printing/compact_tables', 'settings_print_compact_tables', 'bool'),
        ('printing/reverse_print_table_columns', 'settings_print_reverse_columns', 'bool'),
        ('printing/allow_emergency_fallback', 'settings_print_allow_emergency_fallback', 'bool'),
        ('printing/show_template_diagnostics', 'settings_print_show_template_diagnostics', 'bool'),
        ('printing/footer_text', 'footer_text', 'text'),
    )


class UISettingsTab(SettingsSectionDocumentTab):
    section_key = 'settings.ui'
    fields = (
        ('language', 'language', 'choice:ar|en|de'),
        ('theme', 'theme', 'choice:light|dark'),
        ('ui/touch_mode', 'touch_mode', 'bool'),
        ('ui/sidebar_collapsed', 'sidebar_collapsed', 'bool'),
    )


class SecuritySettingsTab(SettingsSectionDocumentTab):
    section_key = 'settings.security'
    fields = (
        ('security/password_min_length', 'password_min_length', 'int'),
        ('security/session_timeout_minutes', 'session_timeout_minutes', 'int'),
        ('security/audit_enabled', 'audit_enabled', 'bool'),
        ('security/require_admin_for_void', 'require_admin_for_void', 'bool'),
    )


SETTINGS_SECTION_TABS = {
    'company': CompanySettingsTab,
    'accounting': AccountingSettingsTab,
    'transactions': TransactionsSettingsTab,
    'materials': MaterialsSettingsTab,
    'categories': CategoriesSettingsTab,
    'parties': PartiesSettingsTab,
    'finance': FinanceSettingsTab,
    'inventory': InventorySettingsTab,
    'branches': BranchesSettingsTab,
    'manufacturing': ManufacturingSettingsTab,
    'reports': ReportsSettingsTab,
    'pos': PosSettingsTab,
    'restaurant': RestaurantSettingsTab,
    'cafe': CafeSettingsTab,
    'apparel': ApparelSettingsTab,
    'printing': PrintingSettingsTab,
    'users': UsersSettingsTab,
    'ui': UISettingsTab,
    'security': SecuritySettingsTab,
}
