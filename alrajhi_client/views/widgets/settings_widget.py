# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QPushButton, QGroupBox, QLabel, QMessageBox, QTabWidget, QFileDialog,
    QSpinBox, QCheckBox, QTableWidgetItem, QHeaderView,
    QDialog, QDialogButtonBox, QScrollArea, QFrame, QPlainTextEdit, QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QSettings

from core.services.settings_service import settings_service
from core.services.backup_service import backup_service
from core.services.audit_service import audit_service
from core.services.system_service import system_service
from core.services.branch_service import branch_service
from currency import currency
from auth.activation import activate_network, check_network_activation
from theme_manager import ThemeManager
from ui.design_system import DesignSystem
from ui.editable_smart_grid import EditableSmartGrid
from utils import show_toast
from i18n.translator import translate, set_language, available_languages, normalize_language, qt_layout_direction
import requests
import os
import json
from views.widgets.modern_ui import apply_modern_widget, apply_modern_dialog


class SettingsWidget(QWidget):
    currency_settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_language = normalize_language(settings_service.get_language())
        set_language(self._current_language)
        self.setLayoutDirection(qt_layout_direction(self._current_language))
        self.settings = settings_service
        self.setObjectName('settingsWidget')

        main = QVBoxLayout(self)
        main.setContentsMargins(18, 18, 18, 18)
        main.setSpacing(14)
        # Phase118: no top explanatory/header card; tabs start directly.

        self.tabs = QTabWidget()
        self.tabs.setObjectName('settingsTabs')
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self.create_appearance_tab(), '🎨 ' + translate('appearance'))
        self.tabs.addTab(self.create_language_settings_tab(), translate('phase233_ui_037'))
        self.tabs.addTab(self.create_profiles_tab(), translate('phase233_ui_038'))
        self.tabs.addTab(self.create_contracts_tab(), '⚙️ ' + translate('settings_contracts_tab'))
        self.tabs.addTab(self.create_company_tab(), '🏢 ' + translate('company'))
        self.tabs.addTab(self.create_invoice_settings_tab(), translate('phase233_ui_039'))
        self.tabs.addTab(self.create_units_settings_tab(), translate('phase233_ui_040'))
        self.tabs.addTab(self.create_returns_settings_tab(), translate('phase233_ui_041'))
        self.tabs.addTab(self.create_inventory_settings_tab(), translate('phase233_ui_042'))
        self.tabs.addTab(self.create_manufacturing_settings_tab(), translate('phase233_ui_043'))
        self.tabs.addTab(self.create_reports_settings_tab(), translate('phase233_ui_044'))
        self.tabs.addTab(self.create_printing_tab(), '🖨️ ' + translate('printing_tab'))
        self.tabs.addTab(self.create_pos_tab(), '🧾 ' + translate('pos_tab'))
        self.tabs.addTab(self.create_currency_tab(), '💰 ' + translate('currencies'))
        self.tabs.addTab(self.create_rates_tab(), '💱 ' + translate('exchange_rates'))
        self.tabs.addTab(self.create_network_tab(), '🌐 ' + translate('network'))
        self.tabs.addTab(self.create_security_tab(), translate('phase233_ui_045'))
        self.tabs.addTab(self.create_workflow_tab(), translate('phase233_ui_046'))
        self.tabs.addTab(self.create_settings_audit_tab(), translate('phase233_ui_047'))
        self.tabs.addTab(self.create_security_events_tab(), translate('phase233_ui_048'))
        self.tabs.addTab(self.create_backup_tab(), '💾 ' + translate('backup_data'))
        self.tabs.addTab(self.create_diagnostics_tab(), translate('phase233_ui_049'))
        main.addWidget(self.tabs, 1)

        self._apply_local_style()
        # Phase118: modern styling without page header cards.
        apply_modern_widget(self)
        self.load_rates_table()


    # Phase118: settings page has no top explanatory/header card.

    def _scroll_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 12, 8, 18)
        layout.setSpacing(14)
        scroll.setWidget(container)
        return scroll, layout

    def _card(self, title, subtitle=None):
        group = QGroupBox(title)
        group.setObjectName('settingsCard')
        box = QVBoxLayout(group)
        box.setContentsMargins(16, 18, 16, 16)
        box.setSpacing(10)
        if subtitle:
            desc = QLabel(subtitle)
            desc.setObjectName('settingsHelp')
            desc.setWordWrap(True)
            box.addWidget(desc)
        return group, box

    def _form_card(self, title, subtitle=None):
        group, box = self._card(title, subtitle)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(12)
        box.addLayout(form)
        return group, form

    def _button_row(self, *buttons):
        row = QHBoxLayout()
        row.addStretch()
        for btn in buttons:
            btn.setMinimumHeight(38)
            row.addWidget(btn)
        return row

    def _note(self, text, tone='info'):
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setObjectName(f'note_{tone}')
        return lbl

    def _apply_local_style(self):
        c = ThemeManager.colors()
        self.setStyleSheet(self.styleSheet() + f"""
            QFrame#settingsHeader {{ background-color: {c['brand_soft']}; border: 1px solid {c['border']}; border-radius: 16px; }}
            QLabel#settingsTitle {{ font-size: 24px; font-weight: 900; color: {c['primary']}; }}
            QLabel#settingsSubtitle, QLabel#settingsHelp {{ color: {c['text_secondary']}; font-size: 12px; }}
            QTabWidget#settingsTabs::pane {{ border: 1px solid {c['border']}; border-radius: 14px; background: {c['bg_window']}; }}
            QTabWidget#settingsTabs QWidget {{ background: {c['bg_window']}; color: {c['text_primary']}; }}
            QTabBar::tab {{ min-height: 34px; padding: 8px 14px; margin: 2px; border-radius: 10px; background: {c['bg_panel']}; color: {c['text_secondary']}; border: 1px solid {c['border']}; font-weight: 700; }}
            QTabBar::tab:selected {{ background: {c['primary']}; color: white; font-weight: 900; }}
            QTableWidget, QTableView {{ background: {c['bg_table']}; alternate-background-color: {c['bg_table_alt']}; color: {c['text_primary']}; border: 1px solid {c['border']}; border-radius: 12px; selection-background-color: {c['selection_bg']}; selection-color: {c['selection_text']}; }}
            QHeaderView::section {{ background: {c['header_bg']}; color: {c['header_text']}; padding: 8px; border: none; font-weight: 800; }}
            QGroupBox#settingsCard {{ border: 1px solid {c['border']}; border-radius: 14px; margin-top: 12px; padding-top: 12px; background: {c['card_bg']}; color: {c['text_primary']}; font-weight: bold; }}
            QGroupBox#settingsCard::title {{ subcontrol-origin: margin; right: 14px; padding: 0 8px; color: {c['primary']}; background: {c['card_bg']}; }}
            QLabel#note_warning {{ background: {c['warning_soft']}; border: 1px solid {c['warning']}; color: {c['warning']}; border-radius: 10px; padding: 10px; }}
            QLabel#note_info {{ background: {c['info_soft']}; border: 1px solid {c['info']}; color: {c['primary']}; border-radius: 10px; padding: 10px; }}
        """)

    def create_appearance_tab(self):
        scroll, layout = self._scroll_tab()
        group, form = self._form_card(translate('appearance_settings'), translate('appearance_help'))
        self.theme_combo = QComboBox()
        self.theme_combo.addItem(translate('light_theme'), 'light')
        self.theme_combo.addItem(translate('dark_theme'), 'dark')
        current_theme = settings_service.get_theme()
        self.theme_combo.setCurrentIndex(1 if current_theme == 'dark' else 0)
        form.addRow(translate('theme_label'), self.theme_combo)
        self.language_combo = QComboBox()
        for code, label in available_languages():
            self.language_combo.addItem(label, code)
        lang_index = self.language_combo.findData(self._current_language)
        if lang_index >= 0:
            self.language_combo.setCurrentIndex(lang_index)
        form.addRow(translate('language_label'), self.language_combo)
        self.ui_font_size = QSpinBox(); self.ui_font_size.setRange(9, 22); self.ui_font_size.setValue(int(settings_service.get('ui/font_size', '12') or 12))
        form.addRow('حجم الخط', self.ui_font_size)
        self.ui_row_height = QSpinBox(); self.ui_row_height.setRange(24, 80); self.ui_row_height.setValue(int(settings_service.get('ui/row_height', '36') or 36))
        form.addRow('حجم الصفوف', self.ui_row_height)
        # Phase 228: global top search is removed from the shell.
        self.ui_default_page = QLineEdit(settings_service.get('ui/default_page', 'dashboard'))
        form.addRow('الصفحة الافتراضية عند التشغيل', self.ui_default_page)
        self.ui_remember_last_tab = QCheckBox(translate('phase233_ui_050'))
        self.ui_remember_last_tab.setChecked(self._bool_setting('ui/remember_last_tab', 'true'))
        form.addRow(self.ui_remember_last_tab)
        form.addRow(self._note(translate('language_settings_note'), 'info'))
        apply_btn = QPushButton(translate('apply_save_appearance'))
        apply_btn.setObjectName('primary')
        apply_btn.clicked.connect(self.save_appearance_settings)
        form.addRow(self._button_row(apply_btn))
        layout.addWidget(group)
        layout.addStretch()
        return scroll



    def _language_combo(self, current='ar'):
        combo = QComboBox()
        for code, label in available_languages():
            combo.addItem(label, code)
        idx = combo.findData(normalize_language(current or 'ar'))
        if idx >= 0:
            combo.setCurrentIndex(idx)
        return combo

    def create_language_settings_tab(self):
        scroll, layout = self._scroll_tab()
        group, form = self._form_card('إعدادات اللغات', 'فصل لغة الواجهة عن لغة الطباعة والتقارير حتى لا يتغير إخراج PDF والتقارير مع واجهة المستخدم بالضرورة.')
        langs = settings_service.get_language_settings()
        self.lang_ui_combo = self._language_combo(langs.get('ui_language', self._current_language))
        form.addRow('لغة الواجهة', self.lang_ui_combo)
        self.lang_print_combo = self._language_combo(langs.get('print_language', self._current_language))
        form.addRow('لغة الطباعة / PDF', self.lang_print_combo)
        self.lang_report_combo = self._language_combo(langs.get('report_language', self._current_language))
        form.addRow('لغة التقارير', self.lang_report_combo)
        form.addRow(self._note('يمكن ضبط الواجهة بالعربية والطباعة أو التقارير بالإنجليزية/الألمانية بشكل مستقل.', 'info'))
        save_btn = QPushButton(translate('phase233_ui_051'))
        save_btn.setObjectName('primary')
        save_btn.clicked.connect(self.save_language_settings)
        form.addRow(self._button_row(save_btn))
        layout.addWidget(group)
        layout.addStretch()
        return scroll

    def save_language_settings(self):
        ui = normalize_language(self.lang_ui_combo.currentData() or self._current_language)
        pr = normalize_language(self.lang_print_combo.currentData() or ui)
        rp = normalize_language(self.lang_report_combo.currentData() or ui)
        settings_service.save_language_settings(ui, pr, rp)
        set_language(ui)
        self._current_language = ui
        self.setLayoutDirection(qt_layout_direction(ui))
        self._refresh_language_texts()
        main_window = self.window()
        if hasattr(main_window, 'setLayoutDirection'):
            main_window.setLayoutDirection(qt_layout_direction(ui))
        show_toast('تم حفظ إعدادات اللغات', 'success', self)

    def create_pos_tab(self):
        scroll, layout = self._scroll_tab()
        group, form = self._form_card(translate('settings_pos_title'), translate('settings_pos_help'))
        self.pos_use_shifts_check = QCheckBox(translate('settings_pos_enable_shifts'))
        self.pos_use_shifts_check.setChecked(settings_service.pos_shifts_enabled())
        form.addRow('', self.pos_use_shifts_check)
        form.addRow(self._note(translate('settings_pos_default_note'), 'info'))
        save_btn = QPushButton(translate('settings_pos_save'))
        save_btn.setObjectName('primary')
        save_btn.clicked.connect(self.save_pos_settings)
        form.addRow(self._button_row(save_btn))
        layout.addWidget(group)
        layout.addStretch()
        return scroll

    def save_pos_settings(self):
        try:
            settings_service.save_pos_settings(self.pos_use_shifts_check.isChecked())
            show_toast(translate('settings_pos_saved'), 'success', self)
        except Exception as e:
            QMessageBox.warning(self, translate('error'), str(e))

    def create_company_tab(self):
        scroll, layout = self._scroll_tab()
        group, form = self._form_card(translate('settings_company_title'), translate('settings_company_help'))
        from config import get_company_info
        info = get_company_info()
        self.company_name_edit = QLineEdit(info.get('name', ''))
        form.addRow(translate('settings_company_name_label'), self.company_name_edit)
        self.company_address_edit = QLineEdit(info.get('address', ''))
        form.addRow(translate('settings_company_address_label'), self.company_address_edit)
        self.company_phone_edit = QLineEdit(info.get('phone', ''))
        form.addRow(translate('settings_company_phone_label'), self.company_phone_edit)
        self.company_email_edit = QLineEdit(info.get('email', ''))
        form.addRow(translate('settings_company_email_label'), self.company_email_edit)
        self.company_tax_number_edit = QLineEdit(info.get('tax_number', ''))
        form.addRow(translate('settings_company_tax_label'), self.company_tax_number_edit)
        self.company_commercial_register_edit = QLineEdit(info.get('commercial_register', ''))
        form.addRow('السجل التجاري', self.company_commercial_register_edit)
        self.company_website_edit = QLineEdit(info.get('website', ''))
        form.addRow('موقع الويب', self.company_website_edit)
        self.company_logo_path_edit = QLineEdit(info.get('logo_path', ''))
        logo_btn = QPushButton(translate('settings_company_choose_logo'))
        logo_btn.clicked.connect(self.browse_logo)
        logo_row = QHBoxLayout()
        logo_row.addWidget(self.company_logo_path_edit, 1)
        logo_row.addWidget(logo_btn)
        form.addRow(translate('settings_company_logo_label'), logo_row)
        save_company_btn = QPushButton(translate('settings_company_save'))
        save_company_btn.setObjectName('primary')
        save_company_btn.clicked.connect(self.save_company_info)
        form.addRow(self._button_row(save_company_btn))
        layout.addWidget(group)
        layout.addStretch()
        return scroll


    # ========== Phase215: consolidated settings contracts ==========
    def _make_bool_row(self, form, attr_name, key, label_key, default=True):
        widget = QCheckBox(translate(label_key))
        widget.setChecked(self._bool_setting(key, 'true' if default else 'false'))
        setattr(self, attr_name, widget)
        form.addRow('', widget)
        return widget

    def _make_density_row(self, form, attr_name, key, default='comfortable'):
        combo = QComboBox()
        combo.addItem(translate('density_compact'), 'compact')
        combo.addItem(translate('density_comfortable'), 'comfortable')
        combo.addItem(translate('density_touch'), 'touch')
        idx = combo.findData(settings_service.get(key, default) or default)
        combo.setCurrentIndex(max(0, idx))
        setattr(self, attr_name, combo)
        form.addRow(translate('settings_touch_density'), combo)
        return combo

    def _make_payment_row(self, form, attr_name, key, default='cash'):
        combo = QComboBox()
        combo.addItem(translate('cash'), 'cash')
        combo.addItem(translate('card'), 'card')
        combo.addItem(translate('bank_transfer'), 'bank_transfer')
        combo.addItem(translate('credit'), 'credit')
        idx = combo.findData(settings_service.get(key, default) or default)
        combo.setCurrentIndex(max(0, idx))
        setattr(self, attr_name, combo)
        form.addRow(translate('settings_default_payment_method'), combo)
        return combo

    def create_contracts_tab(self):
        scroll, layout = self._scroll_tab()
        intro_group, intro_box = self._card(translate('settings_contracts_title'), translate('settings_contracts_help'))
        profile = settings_service.get_active_profile() or {}
        intro_box.addWidget(self._note(translate('settings_contracts_profile_note', profile=profile.get('name') or profile.get('id') or 'default'), 'info'))
        layout.addWidget(intro_group)

        modules_group, form = self._form_card(translate('settings_modules_title'), translate('settings_modules_help'))
        self._make_bool_row(form, 'contract_restaurant_enabled', 'restaurant/enabled', 'settings_module_restaurant', True)
        self._make_bool_row(form, 'contract_manufacturing_enabled', 'manufacturing/enabled', 'settings_module_manufacturing', True)
        self._make_bool_row(form, 'contract_inventory_enabled', 'inventory/enabled', 'settings_module_inventory', True)
        self._make_bool_row(form, 'contract_finance_enabled', 'finance/enabled', 'settings_module_finance', True)
        self._make_bool_row(form, 'contract_reports_enabled', 'reports/enabled', 'settings_module_reports', True)
        self._make_bool_row(form, 'contract_users_enabled', 'users/enabled', 'settings_module_users', True)
        self._make_bool_row(form, 'contract_parties_enabled', 'parties/enabled', 'settings_module_parties', True)
        self._make_bool_row(form, 'contract_categories_enabled', 'categories/enabled', 'settings_module_categories', True)
        self._make_bool_row(form, 'contract_branches_enabled', 'branches/enabled', 'settings_module_branches', True)
        layout.addWidget(modules_group)

        pos_group, pform = self._form_card(translate('settings_pos_contract_title'), translate('settings_pos_contract_help'))
        self._make_density_row(pform, 'contract_pos_density', 'pos/ui/density', 'touch')
        self._make_payment_row(pform, 'contract_pos_payment', 'pos/default_payment_method', 'cash')
        self._make_bool_row(pform, 'contract_pos_checkout', 'pos/operations/allow_checkout', 'settings_operation_pos_checkout', True)
        self._make_bool_row(pform, 'contract_pos_suspend', 'pos/operations/allow_suspend', 'settings_operation_pos_suspend', True)
        self._make_bool_row(pform, 'contract_pos_print', 'pos/operations/allow_print_receipt', 'settings_operation_pos_print', True)
        layout.addWidget(pos_group)

        restaurant_group, rform = self._form_card(translate('settings_restaurant_contract_title'), translate('settings_restaurant_contract_help'))
        self._make_density_row(rform, 'contract_restaurant_density', 'restaurant/ui/density', 'touch')
        self._make_payment_row(rform, 'contract_restaurant_payment', 'restaurant/default_payment_method', 'cash')
        self._make_bool_row(rform, 'contract_restaurant_checkout', 'restaurant/operations/allow_checkout', 'settings_operation_restaurant_checkout', True)
        self._make_bool_row(rform, 'contract_restaurant_kitchen', 'restaurant/operations/allow_send_kitchen', 'settings_operation_restaurant_kitchen', True)
        self._make_bool_row(rform, 'contract_restaurant_print_receipt', 'restaurant/operations/allow_print_receipt', 'settings_operation_restaurant_print_receipt', True)
        self._make_bool_row(rform, 'contract_restaurant_print_kitchen', 'restaurant/operations/allow_print_kitchen_ticket', 'settings_operation_restaurant_print_kitchen', True)
        layout.addWidget(restaurant_group)

        operations_group, oform = self._form_card(translate('settings_operations_title'), translate('settings_operations_help'))
        self._make_bool_row(oform, 'contract_inventory_transfer', 'inventory/operations/allow_transfer_create', 'settings_operation_inventory_transfer', True)
        self._make_bool_row(oform, 'contract_inventory_print', 'inventory/operations/allow_print', 'settings_operation_inventory_print', True)
        self._make_bool_row(oform, 'contract_manufacturing_print', 'manufacturing/operations/allow_print', 'settings_operation_manufacturing_print', True)
        self._make_bool_row(oform, 'contract_reports_export', 'reports/operations/allow_export', 'settings_operation_reports_export', True)
        self._make_bool_row(oform, 'contract_finance_expense', 'finance/operations/allow_expense_create', 'settings_operation_finance_expense', True)
        self._make_bool_row(oform, 'contract_finance_voucher', 'finance/operations/allow_voucher_create', 'settings_operation_finance_voucher', True)
        layout.addWidget(operations_group)

        barcode_group, bform = self._form_card(translate('settings_barcode_contract_title'), translate('settings_barcode_contract_help'))
        self.contract_barcode_min_length = QSpinBox(); self.contract_barcode_min_length.setRange(1, 64); self.contract_barcode_min_length.setValue(int(settings_service.get('barcode/scanner/min_length', '6') or 6))
        bform.addRow(translate('settings_barcode_min_length'), self.contract_barcode_min_length)
        self.contract_barcode_numeric_exact = QCheckBox(translate('settings_barcode_numeric_exact'))
        self.contract_barcode_numeric_exact.setChecked(self._bool_setting('barcode/scanner/numeric_exact', 'true'))
        bform.addRow('', self.contract_barcode_numeric_exact)
        self.contract_barcode_auto_generate = QCheckBox(translate('settings_barcode_auto_generate_material'))
        self.contract_barcode_auto_generate.setChecked(self._bool_setting('materials/barcode/auto_generate', 'true'))
        bform.addRow('', self.contract_barcode_auto_generate)
        self.contract_barcode_symbology = QComboBox(); self.contract_barcode_symbology.addItems(['EAN13', 'CODE128'])
        self.contract_barcode_symbology.setCurrentText(settings_service.get('materials/barcode/default_symbology', 'EAN13') or 'EAN13')
        bform.addRow(translate('settings_default_barcode_symbology'), self.contract_barcode_symbology)
        layout.addWidget(barcode_group)

        save_btn = QPushButton(translate('settings_contracts_save'))
        save_btn.setObjectName('primary')
        save_btn.clicked.connect(self.save_contracts_settings)
        row = QHBoxLayout(); row.addStretch(); row.addWidget(save_btn)
        layout.addLayout(row)
        layout.addStretch()
        return scroll

    def save_contracts_settings(self):
        mapping = {
            'restaurant/enabled': self.contract_restaurant_enabled.isChecked(),
            'manufacturing/enabled': self.contract_manufacturing_enabled.isChecked(),
            'inventory/enabled': self.contract_inventory_enabled.isChecked(),
            'finance/enabled': self.contract_finance_enabled.isChecked(),
            'reports/enabled': self.contract_reports_enabled.isChecked(),
            'users/enabled': self.contract_users_enabled.isChecked(),
            'parties/enabled': self.contract_parties_enabled.isChecked(),
            'categories/enabled': self.contract_categories_enabled.isChecked(),
            'branches/enabled': self.contract_branches_enabled.isChecked(),
            'pos/operations/allow_checkout': self.contract_pos_checkout.isChecked(),
            'pos/operations/allow_suspend': self.contract_pos_suspend.isChecked(),
            'pos/operations/allow_print_receipt': self.contract_pos_print.isChecked(),
            'restaurant/operations/allow_checkout': self.contract_restaurant_checkout.isChecked(),
            'restaurant/operations/allow_send_kitchen': self.contract_restaurant_kitchen.isChecked(),
            'restaurant/operations/allow_print_receipt': self.contract_restaurant_print_receipt.isChecked(),
            'restaurant/operations/allow_print_kitchen_ticket': self.contract_restaurant_print_kitchen.isChecked(),
            'inventory/operations/allow_transfer_create': self.contract_inventory_transfer.isChecked(),
            'inventory/operations/allow_print': self.contract_inventory_print.isChecked(),
            'manufacturing/operations/allow_print': self.contract_manufacturing_print.isChecked(),
            'reports/operations/allow_export': self.contract_reports_export.isChecked(),
            'finance/operations/allow_expense_create': self.contract_finance_expense.isChecked(),
            'finance/operations/allow_voucher_create': self.contract_finance_voucher.isChecked(),
            'barcode/scanner/numeric_exact': self.contract_barcode_numeric_exact.isChecked(),
            'materials/barcode/auto_generate': self.contract_barcode_auto_generate.isChecked(),
        }
        for key, value in mapping.items():
            self._set_bool_setting(key, value)
        settings_service.set('pos/ui/density', self.contract_pos_density.currentData())
        settings_service.set('restaurant/ui/density', self.contract_restaurant_density.currentData())
        settings_service.set('pos/default_payment_method', self.contract_pos_payment.currentData())
        settings_service.set('restaurant/default_payment_method', self.contract_restaurant_payment.currentData())
        settings_service.set('barcode/scanner/min_length', str(self.contract_barcode_min_length.value()))
        settings_service.set('materials/barcode/default_symbology', self.contract_barcode_symbology.currentText())
        settings_service.clear_cache()
        audit_service.log('UPDATE', 'SETTINGS_CONTRACTS', None, details='تعديل إعدادات العقود الموحدة')
        show_toast(translate('settings_contracts_saved'), 'success', self)


    # ========== Professional ERP settings tabs ==========
    def _bool_setting(self, key, default='false'):
        return str(settings_service.get(key, default)).lower() == 'true'

    def _set_bool_setting(self, key, value):
        settings_service.set(key, 'true' if value else 'false')

    def create_invoice_settings_tab(self):
        scroll, layout = self._scroll_tab()
        sales_group, form = self._form_card('إعدادات فواتير المبيعات', 'ترقيم الفواتير وسلوك المخزون والكلفة والربح داخل شاشة البيع.')
        self.sales_prefix_edit = QLineEdit(settings_service.get('invoice/sales_prefix', 'SAL-'))
        form.addRow('بادئة رقم المبيعات', self.sales_prefix_edit)
        self.sales_auto_numbering = QCheckBox(translate('phase233_ui_052'))
        self.sales_auto_numbering.setChecked(self._bool_setting('invoice/auto_numbering', 'true'))
        form.addRow(self.sales_auto_numbering)
        self.sales_show_profit = QCheckBox(translate('phase233_ui_053'))
        self.sales_show_profit.setChecked(self._bool_setting('invoice/show_profit', 'false'))
        form.addRow(self.sales_show_profit)
        self.sales_show_cost = QCheckBox(translate('phase233_ui_054'))
        self.sales_show_cost.setChecked(self._bool_setting('invoice/show_cost', 'false'))
        form.addRow(self.sales_show_cost)
        self.sales_warn_stock = QCheckBox(translate('phase233_ui_055'))
        self.sales_warn_stock.setChecked(self._bool_setting('invoice/warn_stock_exceeded', 'true'))
        form.addRow(self.sales_warn_stock)
        self.sales_round_prices = QCheckBox(translate('phase233_ui_056'))
        self.sales_round_prices.setChecked(self._bool_setting('invoice/round_prices', 'true'))
        form.addRow(self.sales_round_prices)
        layout.addWidget(sales_group)

        purchase_group, pform = self._form_card('إعدادات فواتير المشتريات', 'سياسات تسعير الشراء والتكلفة المستخدمة لاحقًا في المخزون والتقارير.')
        self.purchase_prefix_edit = QLineEdit(settings_service.get('invoice/purchase_prefix', 'PUR-'))
        pform.addRow('بادئة رقم المشتريات', self.purchase_prefix_edit)
        self.purchase_last_price = QCheckBox(translate('phase233_ui_057'))
        self.purchase_last_price.setChecked(self._bool_setting('purchase/use_last_purchase_price', 'true'))
        pform.addRow(self.purchase_last_price)
        self.purchase_avg_cost = QCheckBox(translate('phase233_ui_058'))
        self.purchase_avg_cost.setChecked(self._bool_setting('purchase/use_average_cost', 'true'))
        pform.addRow(self.purchase_avg_cost)
        save_btn = QPushButton(translate('phase233_ui_059'))
        save_btn.setObjectName('primary')
        save_btn.clicked.connect(self.save_invoice_settings)
        pform.addRow(self._button_row(save_btn))
        layout.addWidget(purchase_group)
        layout.addStretch()
        return scroll

    def save_invoice_settings(self):
        settings_service.set('invoice/sales_prefix', self.sales_prefix_edit.text().strip() or 'SAL-')
        settings_service.set('invoice/purchase_prefix', self.purchase_prefix_edit.text().strip() or 'PUR-')
        self._set_bool_setting('invoice/auto_numbering', self.sales_auto_numbering.isChecked())
        self._set_bool_setting('invoice/show_profit', self.sales_show_profit.isChecked())
        self._set_bool_setting('invoice/show_cost', self.sales_show_cost.isChecked())
        self._set_bool_setting('invoice/warn_stock_exceeded', self.sales_warn_stock.isChecked())
        self._set_bool_setting('invoice/round_prices', self.sales_round_prices.isChecked())
        self._set_bool_setting('purchase/use_last_purchase_price', self.purchase_last_price.isChecked())
        self._set_bool_setting('purchase/use_average_cost', self.purchase_avg_cost.isChecked())
        settings_service.clear_cache()
        audit_service.log('UPDATE', 'SETTINGS_INVOICES', None, details='تعديل إعدادات الفواتير')
        show_toast('تم حفظ إعدادات الفواتير', 'success', self)

    def create_units_settings_tab(self):
        scroll, layout = self._scroll_tab()
        group, form = self._form_card('إعدادات الوحدات', 'القيم الافتراضية لضبط البيع والشراء ودقة الأرقام.')
        self.default_sale_unit = QLineEdit(settings_service.get_units_settings().get('default_sales_unit') or 'قطعة')
        form.addRow('الوحدة الافتراضية للبيع', self.default_sale_unit)
        self.default_purchase_unit = QLineEdit(settings_service.get('units/default_purchase_unit', 'قطعة'))
        form.addRow('الوحدة الافتراضية للشراء', self.default_purchase_unit)
        self.quantity_decimals = QSpinBox(); self.quantity_decimals.setRange(0, 6); self.quantity_decimals.setValue(int(settings_service.get('units/quantity_decimals', '2') or 2))
        form.addRow('منازل عشرية للكميات', self.quantity_decimals)
        self.price_decimals = QSpinBox(); self.price_decimals.setRange(0, 6); self.price_decimals.setValue(int(settings_service.get('units/price_decimals', '2') or 2))
        form.addRow('منازل عشرية للأسعار', self.price_decimals)
        self.rounding_method = QComboBox(); self.rounding_method.addItems(['HALF_UP', 'FLOOR', 'CEIL'])
        self.rounding_method.setCurrentText(settings_service.get('units/rounding_method', 'HALF_UP'))
        form.addRow('طريقة التقريب', self.rounding_method)
        save_btn = QPushButton(translate('phase233_ui_060')); save_btn.setObjectName('primary'); save_btn.clicked.connect(self.save_units_settings)
        form.addRow(self._button_row(save_btn))
        layout.addWidget(group); layout.addStretch(); return scroll

    def save_units_settings(self):
        settings_service.save_units_settings(
            self.default_sale_unit.text().strip() or 'قطعة',
            self.default_purchase_unit.text().strip() or 'قطعة',
            self.quantity_decimals.value(),
            self.price_decimals.value(),
            self.rounding_method.currentText(),
        )
        show_toast('تم حفظ إعدادات الوحدات', 'success', self)

    def create_returns_settings_tab(self):
        scroll, layout = self._scroll_tab()
        group, form = self._form_card('إعدادات المرتجعات', 'ضوابط قبول المرتجع وأثره على المخزون والسندات.')
        self.allow_return_without_invoice = QCheckBox(translate('phase233_ui_061'))
        self.allow_return_without_invoice.setChecked(self._bool_setting('returns/allow_without_invoice', 'false'))
        form.addRow(self.allow_return_without_invoice)
        self.return_max_days = QSpinBox(); self.return_max_days.setRange(0, 3650); self.return_max_days.setValue(int(settings_service.get('returns/max_days', '30') or 30))
        form.addRow('أقصى مدة للمرتجع/يوم', self.return_max_days)
        self.return_auto_voucher = QCheckBox(translate('phase233_ui_062'))
        self.return_auto_voucher.setChecked(self._bool_setting('returns/auto_voucher', 'true'))
        form.addRow(self.return_auto_voucher)
        self.return_update_stock = QCheckBox(translate('phase233_ui_063'))
        self.return_update_stock.setChecked(self._bool_setting('returns/update_stock_immediately', 'true'))
        form.addRow(self.return_update_stock)
        self.return_prevent_exceed = QCheckBox(translate('phase233_ui_064'))
        self.return_prevent_exceed.setChecked(self._bool_setting('returns/prevent_quantity_exceed', 'true'))
        form.addRow(self.return_prevent_exceed)
        save_btn = QPushButton(translate('phase233_ui_065')); save_btn.setObjectName('primary'); save_btn.clicked.connect(self.save_returns_settings)
        form.addRow(self._button_row(save_btn)); layout.addWidget(group); layout.addStretch(); return scroll

    def save_returns_settings(self):
        self._set_bool_setting('returns/allow_without_invoice', self.allow_return_without_invoice.isChecked())
        settings_service.set('returns/max_days', self.return_max_days.value())
        self._set_bool_setting('returns/auto_voucher', self.return_auto_voucher.isChecked())
        self._set_bool_setting('returns/update_stock_immediately', self.return_update_stock.isChecked())
        self._set_bool_setting('returns/prevent_quantity_exceed', self.return_prevent_exceed.isChecked())
        settings_service.clear_cache(); audit_service.log('UPDATE', 'SETTINGS_RETURNS', None, details='تعديل إعدادات المرتجعات')
        show_toast('تم حفظ إعدادات المرتجعات', 'success', self)

    def create_inventory_settings_tab(self):
        scroll, layout = self._scroll_tab()
        group, form = self._form_card('إعدادات المخزون', 'السياسات العامة للمخزون والتقييم وحركات المخزون.')
        self.inv_allow_negative = QCheckBox(translate('phase233_ui_066'))
        self.inv_allow_negative.setChecked(self._bool_setting('inventory/allow_negative_stock', 'false'))
        form.addRow(self.inv_allow_negative)
        self.inv_reorder = QSpinBox(); self.inv_reorder.setRange(0, 100000000); self.inv_reorder.setValue(int(float(settings_service.get('inventory/default_reorder_level', '0') or 0)))
        form.addRow('حد إعادة الطلب الافتراضي', self.inv_reorder)
        self.inv_cost_method = QComboBox(); self.inv_cost_method.addItems(['AVERAGE', 'FIFO'])
        self.inv_cost_method.setCurrentText(settings_service.get('inventory/cost_method', 'AVERAGE'))
        form.addRow('طريقة تقييم المخزون', self.inv_cost_method)
        self.inv_auto_movements = QCheckBox(translate('phase233_ui_067'))
        self.inv_auto_movements.setChecked(self._bool_setting('inventory/auto_movements', 'true'))
        form.addRow(self.inv_auto_movements)
        save_btn = QPushButton(translate('phase233_ui_068')); save_btn.setObjectName('primary'); save_btn.clicked.connect(self.save_inventory_settings)
        form.addRow(self._button_row(save_btn)); layout.addWidget(group); layout.addStretch(); return scroll

    def save_inventory_settings(self):
        self._set_bool_setting('inventory/allow_negative_stock', self.inv_allow_negative.isChecked())
        settings_service.set('inventory/default_reorder_level', self.inv_reorder.value())
        settings_service.set('inventory/cost_method', self.inv_cost_method.currentText())
        self._set_bool_setting('inventory/auto_movements', self.inv_auto_movements.isChecked())
        settings_service.clear_cache(); audit_service.log('UPDATE', 'SETTINGS_INVENTORY', None, details='تعديل إعدادات المخزون')
        show_toast('تم حفظ إعدادات المخزون', 'success', self)

    def create_manufacturing_settings_tab(self):
        scroll, layout = self._scroll_tab()
        group, form = self._form_card('إعدادات التصنيع', 'سياسات التكلفة والمواد عند إنشاء أوامر التصنيع.')
        self.mfg_auto_entries = QCheckBox(translate('phase233_ui_069'))
        self.mfg_auto_entries.setChecked(self._bool_setting('manufacturing/auto_entries', 'false'))
        form.addRow(self.mfg_auto_entries)
        self.mfg_cost_method = QComboBox(); self.mfg_cost_method.addItem(translate('phase233_ui_070'), 'MATERIALS_ONLY'); self.mfg_cost_method.addItem(translate('phase233_ui_071'), 'MATERIALS_PLUS_OVERHEAD')
        idx = self.mfg_cost_method.findData(settings_service.get('manufacturing/cost_method', 'MATERIALS_ONLY'))
        self.mfg_cost_method.setCurrentIndex(max(0, idx))
        form.addRow('طريقة التكلفة', self.mfg_cost_method)
        self.mfg_allow_overproduction = QCheckBox(translate('phase233_ui_072'))
        self.mfg_allow_overproduction.setChecked(self._bool_setting('manufacturing/allow_overproduction', 'false'))
        form.addRow(self.mfg_allow_overproduction)
        self.mfg_allow_shortage = QCheckBox(translate('phase233_ui_073'))
        self.mfg_allow_shortage.setChecked(self._bool_setting('manufacturing/allow_material_shortage', 'false'))
        form.addRow(self.mfg_allow_shortage)
        save_btn = QPushButton(translate('phase233_ui_074')); save_btn.setObjectName('primary'); save_btn.clicked.connect(self.save_manufacturing_settings)
        form.addRow(self._button_row(save_btn)); layout.addWidget(group); layout.addStretch(); return scroll

    def save_manufacturing_settings(self):
        self._set_bool_setting('manufacturing/auto_entries', self.mfg_auto_entries.isChecked())
        settings_service.set('manufacturing/cost_method', self.mfg_cost_method.currentData())
        self._set_bool_setting('manufacturing/allow_overproduction', self.mfg_allow_overproduction.isChecked())
        self._set_bool_setting('manufacturing/allow_material_shortage', self.mfg_allow_shortage.isChecked())
        settings_service.clear_cache(); audit_service.log('UPDATE', 'SETTINGS_MANUFACTURING', None, details='تعديل إعدادات التصنيع')
        show_toast('تم حفظ إعدادات التصنيع', 'success', self)

    def create_reports_settings_tab(self):
        scroll, layout = self._scroll_tab()
        group, form = self._form_card('إعدادات التقارير', 'سلوك الفلاتر والتصدير والعدد الافتراضي للسجلات.')
        self.reports_default_limit = QSpinBox(); self.reports_default_limit.setRange(10, 100000); self.reports_default_limit.setValue(int(settings_service.get('reports/default_limit', '100') or 100))
        form.addRow('عدد السجلات الافتراضي', self.reports_default_limit)
        self.reports_save_filters = QCheckBox(translate('phase233_ui_075'))
        self.reports_save_filters.setChecked(self._bool_setting('reports/save_last_filters', 'true'))
        form.addRow(self.reports_save_filters)
        self.reports_open_last = QCheckBox(translate('phase233_ui_076'))
        self.reports_open_last.setChecked(self._bool_setting('reports/open_last_report', 'false'))
        form.addRow(self.reports_open_last)
        self.reports_excel = QCheckBox(translate('phase233_ui_077'))
        self.reports_excel.setChecked(self._bool_setting('reports/export_excel', 'true'))
        form.addRow(self.reports_excel)
        self.reports_pdf = QCheckBox(translate('phase233_ui_078'))
        self.reports_pdf.setChecked(self._bool_setting('reports/export_pdf', 'true'))
        form.addRow(self.reports_pdf)
        save_btn = QPushButton(translate('phase233_ui_079')); save_btn.setObjectName('primary'); save_btn.clicked.connect(self.save_reports_settings)
        form.addRow(self._button_row(save_btn)); layout.addWidget(group); layout.addStretch(); return scroll

    def save_reports_settings(self):
        settings_service.set('reports/default_limit', self.reports_default_limit.value())
        self._set_bool_setting('reports/save_last_filters', self.reports_save_filters.isChecked())
        self._set_bool_setting('reports/open_last_report', self.reports_open_last.isChecked())
        self._set_bool_setting('reports/export_excel', self.reports_excel.isChecked())
        self._set_bool_setting('reports/export_pdf', self.reports_pdf.isChecked())
        settings_service.clear_cache(); audit_service.log('UPDATE', 'SETTINGS_REPORTS', None, details='تعديل إعدادات التقارير')
        show_toast('تم حفظ إعدادات التقارير', 'success', self)

    def create_printing_tab(self):
        scroll, layout = self._scroll_tab()
        cfg = settings_service.get_printing_settings()

        templates_group, form = self._form_card(translate('settings_print_templates_title'), translate('settings_print_templates_help'))
        self.print_invoice_template = QComboBox()
        self.print_invoice_template.addItem(translate('settings_print_template_a4'), 'a4')
        self.print_invoice_template.addItem(translate('settings_print_template_thermal80'), 'thermal80')
        self.print_invoice_template.addItem(translate('settings_print_template_thermal58'), 'thermal58')
        idx = self.print_invoice_template.findData(cfg.get('invoice_template', 'a4'))
        self.print_invoice_template.setCurrentIndex(max(0, idx))
        form.addRow(translate('settings_print_invoice_template_label'), self.print_invoice_template)

        self.print_report_template = QComboBox()
        self.print_report_template.addItem(translate('settings_print_template_a4'), 'a4')
        self.print_report_template.addItem(translate('settings_print_template_thermal80'), 'thermal80')
        self.print_report_template.addItem(translate('settings_print_template_thermal58'), 'thermal58')
        idx = self.print_report_template.findData(cfg.get('report_template', 'a4'))
        self.print_report_template.setCurrentIndex(max(0, idx))
        form.addRow(translate('settings_print_report_template_label'), self.print_report_template)

        self.print_voucher_template = QComboBox()
        self.print_voucher_template.addItem(translate('settings_print_template_a4'), 'a4')
        self.print_voucher_template.addItem(translate('settings_print_template_thermal80'), 'thermal80')
        self.print_voucher_template.addItem(translate('settings_print_template_thermal58'), 'thermal58')
        idx = self.print_voucher_template.findData(cfg.get('voucher_template', 'a4'))
        self.print_voucher_template.setCurrentIndex(max(0, idx))
        form.addRow(translate('settings_print_voucher_template_label'), self.print_voucher_template)

        self.print_return_template = QComboBox()
        self.print_return_template.addItem(translate('settings_print_template_a4'), 'a4')
        self.print_return_template.addItem(translate('settings_print_template_thermal80'), 'thermal80')
        self.print_return_template.addItem(translate('settings_print_template_thermal58'), 'thermal58')
        idx = self.print_return_template.findData(cfg.get('return_template', cfg.get('invoice_template', 'a4')))
        self.print_return_template.setCurrentIndex(max(0, idx))
        form.addRow(translate('settings_print_return_template_label'), self.print_return_template)

        self.print_thermal_size = QComboBox()
        self.print_thermal_size.addItems(['80mm', '58mm'])
        self.print_thermal_size.setCurrentText(cfg.get('thermal_size', '80mm'))
        form.addRow(translate('settings_print_thermal_size_label'), self.print_thermal_size)
        layout.addWidget(templates_group)

        barcode_group, barcode_form = self._form_card(translate('settings_barcode_print_title'), translate('settings_barcode_print_help'))
        from printer_manager import PrinterManager
        self.barcode_printer_manager = PrinterManager()
        self.barcode_printer_manager.load_default_printer()
        self.barcode_default_printer = QComboBox()
        self.barcode_default_printer.addItem(translate('phase235_system_print_dialog'), '')
        for printer in self.barcode_printer_manager.printers:
            if getattr(printer.type, 'value', '') in {'pdf', 'image'}:
                continue
            self.barcode_default_printer.addItem(printer.name, printer.id)
        idx = self.barcode_default_printer.findData(cfg.get('barcode_default_printer', ''))
        if idx >= 0:
            self.barcode_default_printer.setCurrentIndex(idx)
        barcode_form.addRow(translate('settings_barcode_default_printer_label'), self.barcode_default_printer)

        self.barcode_label_size = QComboBox()
        self.barcode_label_size.addItems(['40x30', '50x30', '60x40', '80mm'])
        self.barcode_label_size.setCurrentText(cfg.get('barcode_label_size', '50x30'))
        barcode_form.addRow(translate('settings_barcode_label_size_label'), self.barcode_label_size)

        self.barcode_symbology = QComboBox()
        self.barcode_symbology.addItems(['AUTO', 'EAN13', 'CODE128'])
        self.barcode_symbology.setCurrentText(cfg.get('barcode_symbology', 'AUTO'))
        barcode_form.addRow(translate('settings_barcode_symbology_label'), self.barcode_symbology)

        self.barcode_copies = QSpinBox()
        self.barcode_copies.setRange(1, 100)
        self.barcode_copies.setValue(int(cfg.get('barcode_copies', 1) or 1))
        barcode_form.addRow(translate('settings_barcode_copies_label'), self.barcode_copies)

        self.barcode_columns = QSpinBox()
        self.barcode_columns.setRange(1, 4)
        self.barcode_columns.setValue(int(cfg.get('barcode_columns', 2) or 2))
        barcode_form.addRow(translate('settings_barcode_columns_label'), self.barcode_columns)

        self.barcode_show_company = QCheckBox(translate('settings_barcode_show_company'))
        self.barcode_show_company.setChecked(bool(cfg.get('barcode_show_company', True)))
        barcode_form.addRow(self.barcode_show_company)
        self.barcode_show_logo = QCheckBox(translate('settings_barcode_show_logo'))
        self.barcode_show_logo.setChecked(bool(cfg.get('barcode_show_logo', cfg.get('show_logo', True))))
        barcode_form.addRow(self.barcode_show_logo)
        self.barcode_show_qr = QCheckBox(translate('settings_barcode_show_qr'))
        self.barcode_show_qr.setChecked(bool(cfg.get('barcode_show_qr', True)))
        barcode_form.addRow(self.barcode_show_qr)
        self.barcode_show_name = QCheckBox(translate('settings_barcode_show_name'))
        self.barcode_show_name.setChecked(bool(cfg.get('barcode_show_name', True)))
        barcode_form.addRow(self.barcode_show_name)
        self.barcode_show_price = QCheckBox(translate('settings_barcode_show_price'))
        self.barcode_show_price.setChecked(bool(cfg.get('barcode_show_price', True)))
        barcode_form.addRow(self.barcode_show_price)
        self.barcode_show_text = QCheckBox(translate('settings_barcode_show_text'))
        self.barcode_show_text.setChecked(bool(cfg.get('barcode_show_text', True)))
        barcode_form.addRow(self.barcode_show_text)
        layout.addWidget(barcode_group)

        identity_group, identity_form = self._form_card(translate('settings_print_identity_title'), translate('settings_print_identity_help'))
        self.print_show_logo = QCheckBox(translate('settings_print_show_logo'))
        self.print_show_logo.setChecked(bool(cfg.get('show_logo', True)))
        identity_form.addRow(self.print_show_logo)

        self.print_show_tax = QCheckBox(translate('settings_print_show_tax'))
        self.print_show_tax.setChecked(bool(cfg.get('show_tax_number', True)))
        identity_form.addRow(self.print_show_tax)

        self.print_show_qr = QCheckBox(translate('settings_print_show_qr'))
        self.print_show_qr.setChecked(bool(cfg.get('show_qr', True)))
        identity_form.addRow(self.print_show_qr)

        self.print_accent_color = QLineEdit(cfg.get('accent_color', '#1d4ed8'))
        self.print_accent_color.setPlaceholderText('#1d4ed8')
        identity_form.addRow(translate('settings_print_accent_color_label'), self.print_accent_color)

        self.print_font_family = QLineEdit(cfg.get('font_family', 'Tajawal, Arial, DejaVu Sans, sans-serif'))
        identity_form.addRow(translate('settings_print_font_label'), self.print_font_family)

        self.print_font_size = QComboBox()
        self.print_font_size.addItems(['9.5pt', '10pt', '10.5pt', '11pt', '12pt'])
        self.print_font_size.setCurrentText(cfg.get('print_font_size', '10.5pt'))
        identity_form.addRow(translate('settings_print_font_size_label'), self.print_font_size)

        self.print_zebra_rows = QCheckBox(translate('settings_print_zebra_rows'))
        self.print_zebra_rows.setChecked(bool(cfg.get('zebra_rows', True)))
        identity_form.addRow(self.print_zebra_rows)

        self.print_compact_tables = QCheckBox(translate('settings_print_compact_tables'))
        self.print_compact_tables.setChecked(bool(cfg.get('compact_tables', False)))
        identity_form.addRow(self.print_compact_tables)

        self.print_footer = QLineEdit(cfg.get('footer_text', ''))
        self.print_footer.setPlaceholderText(translate('settings_print_footer_placeholder'))
        identity_form.addRow(translate('settings_print_footer_label'), self.print_footer)
        layout.addWidget(identity_group)

        actions_group, actions_box = self._card(translate('settings_print_actions_title'), translate('settings_print_actions_help'))
        save_btn = QPushButton(translate('settings_print_save'))
        save_btn.setObjectName('primary')
        save_btn.clicked.connect(self.save_printing_settings)
        actions_box.addLayout(self._button_row(save_btn))
        layout.addWidget(actions_group)
        layout.addStretch()
        return scroll

    def create_currency_tab(self):
        scroll, layout = self._scroll_tab()
        group, form = self._form_card(translate('settings_currency_title'), translate('settings_currency_help'))
        self.base_curr = QComboBox(); self.base_curr.addItems(['USD', 'SAR', 'SYP', 'EUR', 'GBP', 'AED', 'QAR', 'KWD', 'OMR']); self.base_curr.setCurrentText(currency.get_base_currency())
        form.addRow(translate('settings_currency_base_label'), self.base_curr)
        self.display_curr = QComboBox(); self.display_curr.addItems(['USD', 'SAR', 'SYP', 'EUR', 'GBP', 'AED', 'QAR', 'KWD', 'OMR']); self.display_curr.setCurrentText(currency.get_display_currency())
        form.addRow(translate('settings_currency_display_label'), self.display_curr)
        self.decimals = QSpinBox(); self.decimals.setRange(0, 2); self.decimals.setValue(currency.get_currency_decimals())
        form.addRow(translate('settings_currency_decimals_label'), self.decimals)
        self.format_combo = QComboBox(); self.format_combo.addItems([translate('settings_currency_format_western'), translate('settings_currency_format_eastern')])
        current = self.settings.get('number_format', 'western')
        self.format_combo.setCurrentIndex(0 if current == 'western' else 1)
        form.addRow(translate('settings_currency_number_format_label'), self.format_combo)
        self.abbreviate_check = QCheckBox(translate('settings_currency_abbreviate')); self.abbreviate_check.setChecked(currency.abbreviate_numbers())
        form.addRow(self.abbreviate_check)
        save_btn = QPushButton(translate('settings_currency_save')); save_btn.setObjectName('primary'); save_btn.clicked.connect(self.save_currency_settings)
        form.addRow(self._button_row(save_btn))
        layout.addWidget(group); layout.addStretch(); return scroll

    def create_rates_tab(self):
        scroll, layout = self._scroll_tab()
        group, box = self._card(translate('settings_rates_title'), translate('settings_rates_help'))
        self.rates_table = EditableSmartGrid(identity='settings.rates'); self.rates_table.setColumnCount(3); self.rates_table.setHorizontalHeaderLabels([translate('settings_rates_currency_col'), translate('settings_rates_rate_col'), translate('settings_rates_updated_col')])
        self.rates_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.rates_table.setAlternatingRowColors(True); self.rates_table.setMinimumHeight(320)
        box.addWidget(self.rates_table)
        refresh_btn = QPushButton(translate('settings_rates_fetch_online')); refresh_btn.clicked.connect(self.fetch_online_rates)
        save_btn = QPushButton(translate('settings_rates_save')); save_btn.setObjectName('primary'); save_btn.clicked.connect(self.save_currency_settings)
        box.addLayout(self._button_row(refresh_btn, save_btn))
        layout.addWidget(group); layout.addStretch(); return scroll

    def create_network_tab(self):
        scroll, layout = self._scroll_tab()
        group, form = self._form_card(
            translate('settings_network_title'),
            translate('settings_network_help')
        )
        self.mode_combo = QComboBox(); self.mode_combo.addItems([translate('settings_network_mode_local'), translate('settings_network_mode_client'), translate('settings_network_mode_server')])
        settings = QSettings('Alrajhi', 'Accounting')
        current_mode = settings.value('network/mode', 'local')
        self.mode_combo.setCurrentIndex({'local': 0, 'client': 1, 'server': 2}.get(current_mode, 0))
        form.addRow(translate('settings_network_mode_label'), self.mode_combo)

        self.server_url_edit = QLineEdit(settings.value('network/server_url', 'http://localhost:8000'))
        self.server_url_edit.setPlaceholderText(translate('settings_network_server_placeholder'))
        form.addRow(translate('settings_network_server_url_label'), self.server_url_edit)

        self.server_port_spin = QSpinBox(); self.server_port_spin.setRange(1024, 65535); self.server_port_spin.setValue(int(settings.value('server/port', 8000)))
        form.addRow(translate('settings_network_server_port_label'), self.server_port_spin)

        self.server_auto_start_check = QCheckBox(translate('settings_network_autostart_server'))
        self.server_auto_start_check.setChecked(settings.value('server/auto_start', False, type=bool))
        form.addRow(self.server_auto_start_check)

        self.server_status_label = QLabel('')
        self.server_status_label.setWordWrap(True)
        form.addRow(translate('settings_network_server_status_label'), self.server_status_label)

        server_group, server_box = self._card(
            translate('settings_network_server_admin_title'),
            translate('settings_network_server_admin_help')
        )
        server_grid = QFormLayout()
        self.server_pid_label = QLabel('-')
        self.server_uptime_label = QLabel('-')
        self.server_db_path_label = QLabel('-')
        self.server_backup_path_label = QLabel('-')
        for lbl in (self.server_pid_label, self.server_uptime_label, self.server_db_path_label, self.server_backup_path_label):
            lbl.setWordWrap(True)
        server_grid.addRow('PID:', self.server_pid_label)
        server_grid.addRow(translate('settings_network_uptime_label'), self.server_uptime_label)
        server_grid.addRow(translate('settings_network_server_db_label'), self.server_db_path_label)
        server_grid.addRow(translate('settings_network_backup_dir_label'), self.server_backup_path_label)
        server_box.addLayout(server_grid)
        start_btn = QPushButton(translate('settings_network_start_server')); start_btn.clicked.connect(self.start_local_server_now)
        stop_btn = QPushButton(translate('settings_network_stop_server')); stop_btn.clicked.connect(self.stop_local_server_now)
        restart_btn = QPushButton(translate('settings_network_restart_server')); restart_btn.clicked.connect(self.restart_local_server_now)
        refresh_btn = QPushButton(translate('settings_network_refresh_status')); refresh_btn.clicked.connect(self.refresh_server_status)
        backup_btn = QPushButton(translate('settings_network_backup_server_db')); backup_btn.clicked.connect(self.backup_local_server_database)
        open_dir_btn = QPushButton(translate('settings_network_open_data_dir')); open_dir_btn.clicked.connect(self.open_local_server_data_dir)
        test_btn = QPushButton(translate('settings_network_test_connection')); test_btn.clicked.connect(self.test_network_connection)
        server_box.addLayout(self._button_row(start_btn, stop_btn, restart_btn, refresh_btn))
        server_box.addLayout(self._button_row(backup_btn, open_dir_btn, test_btn))
        layout.addWidget(server_group)

        center_group, center_layout = self._card(translate('settings_network_center_title'), translate('settings_network_center_help'))
        grid = QFormLayout()
        self.net_connection_label = QLabel(translate('settings_network_not_checked'))
        self.net_latency_label = QLabel('-')
        self.net_api_label = QLabel('-')
        self.net_routes_label = QLabel('-')
        self.net_db_label = QLabel('-')
        self.net_counts_label = QLabel('-')
        self.net_missing_label = QLabel('-')
        for lbl in (self.net_connection_label, self.net_latency_label, self.net_api_label, self.net_routes_label, self.net_db_label, self.net_counts_label, self.net_missing_label):
            lbl.setWordWrap(True)
        grid.addRow(translate('settings_network_connection_status_label'), self.net_connection_label)
        grid.addRow(translate('settings_network_latency_label'), self.net_latency_label)
        grid.addRow(translate('settings_network_api_version_label'), self.net_api_label)
        grid.addRow(translate('settings_network_route_count_label'), self.net_routes_label)
        grid.addRow(translate('settings_network_database_label'), self.net_db_label)
        grid.addRow(translate('settings_network_quick_counts_label'), self.net_counts_label)
        grid.addRow(translate('settings_network_missing_routes_label'), self.net_missing_label)
        center_layout.addLayout(grid)
        refresh_center_btn = QPushButton(translate('settings_network_check_now')); refresh_center_btn.clicked.connect(self.refresh_network_center)
        log_btn = QPushButton(translate('settings_network_show_request_log')); log_btn.clicked.connect(self.show_network_request_log)
        center_layout.addLayout(self._button_row(refresh_center_btn, log_btn))
        layout.addWidget(center_group)

        form.addRow(self._note(
            translate('settings_network_server_note'),
            'info'
        ))

        network_ok, network_msg = check_network_activation()
        if not network_ok:
            form.addRow(self._note(translate('settings_network_activation_required_warning', message=network_msg), 'warning'))
            activate_btn = QPushButton(translate('settings_network_activate')); activate_btn.clicked.connect(self.activate_network_dialog)
            form.addRow(self._button_row(activate_btn))
        save_btn = QPushButton(translate('settings_network_save')); save_btn.setObjectName('primary'); save_btn.clicked.connect(self.save_network_settings)
        form.addRow(self._button_row(save_btn))
        layout.addWidget(group); layout.addStretch(); self.refresh_server_status(); self.refresh_network_center(); return scroll


    def create_profiles_tab(self):
        scroll, layout = self._scroll_tab()
        group, box = self._card('ملفات الإعدادات Profiles', 'تسمح بإنشاء أكثر من مجموعة إعدادات: افتراضي، تجزئة، جملة، تصنيع، أو اختبار. الملف النشط يملك أولوية عند قراءة الإعدادات.')

        self.profiles_table = EditableSmartGrid(0, 5, identity='settings.profiles')
        self.profiles_table.setHorizontalHeaderLabels(['ID', 'الاسم', 'الوصف', 'نشط', 'عدد الإعدادات'])
        self.profiles_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.profiles_table.setAlternatingRowColors(True)
        box.addWidget(self.profiles_table)

        self.profile_status_label = QLabel('')
        self.profile_status_label.setWordWrap(True)
        box.addWidget(self.profile_status_label)

        row = QHBoxLayout()
        self.profile_name = QLineEdit(); self.profile_name.setPlaceholderText('اسم الملف: Retail / Wholesale / Factory')
        self.profile_desc = QLineEdit(); self.profile_desc.setPlaceholderText('وصف اختياري')
        row.addWidget(self.profile_name, 2); row.addWidget(self.profile_desc, 3)
        box.addLayout(row)

        create_btn = QPushButton(translate('phase233_ui_080'))
        create_btn.clicked.connect(self.create_settings_profile)
        activate_btn = QPushButton(translate('phase233_ui_081'))
        activate_btn.setObjectName('primary')
        activate_btn.clicked.connect(self.activate_selected_profile)
        clone_btn = QPushButton(translate('phase233_ui_082'))
        clone_btn.clicked.connect(self.clone_selected_profile)
        export_btn = QPushButton(translate('phase233_ui_083'))
        export_btn.clicked.connect(self.export_selected_profile)
        import_btn = QPushButton(translate('phase233_ui_084'))
        import_btn.clicked.connect(self.import_settings_profile)
        refresh_btn = QPushButton(translate('phase233_ui_085'))
        refresh_btn.clicked.connect(self.refresh_profiles)
        box.addLayout(self._button_row(refresh_btn, import_btn, export_btn, clone_btn, activate_btn, create_btn))

        layout.addWidget(group)
        layout.addStretch()
        self.refresh_profiles()
        return scroll

    def _selected_profile_id(self):
        table = getattr(self, 'profiles_table', None)
        if table is None or table.currentRow() < 0:
            return None
        item = table.item(table.currentRow(), 0)
        try:
            return int(item.text()) if item else None
        except Exception:
            return None

    def refresh_profiles(self):
        rows = settings_service.list_profiles()
        self.profiles_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            values = [row.get('id', ''), row.get('name', ''), row.get('description', ''), 'نعم' if int(row.get('is_active') or 0) else 'لا', row.get('settings_count', 0)]
            for c, val in enumerate(values):
                item = QTableWidgetItem(str(val if val is not None else ''))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.profiles_table.setItem(r, c, item)
        health = settings_service.profile_health()
        active = health.get('active_profile') or {}
        missing = health.get('missing_settings') or []
        self.profile_status_label.setText(
            translate('settings_profile_status', name=active.get('name', 'Default'), count=active.get('settings_count', 0), missing=len(missing))
        )

    def create_settings_profile(self):
        name = self.profile_name.text().strip()
        if not name:
            QMessageBox.warning(self, translate('warning'), translate('settings_profile_name_required'))
            return
        try:
            settings_service.create_profile(name, self.profile_desc.text().strip())
            self.profile_name.clear(); self.profile_desc.clear()
            self.refresh_profiles()
            show_toast(self, 'تم إنشاء ملف الإعدادات')
        except Exception as exc:
            QMessageBox.critical(self, 'خطأ', str(exc))

    def activate_selected_profile(self):
        profile_id = self._selected_profile_id()
        if not profile_id:
            QMessageBox.warning(self, 'تنبيه', 'اختر ملفاً من الجدول.')
            return
        try:
            settings_service.set_active_profile(profile_id)
            self.refresh_profiles()
            QMessageBox.information(self, 'تم', 'تم تفعيل ملف الإعدادات. قد تحتاج بعض الشاشات إلى إعادة فتح لتقرأ القيم الجديدة.')
        except Exception as exc:
            QMessageBox.critical(self, 'خطأ', str(exc))

    def clone_selected_profile(self):
        profile_id = self._selected_profile_id()
        if not profile_id:
            QMessageBox.warning(self, 'تنبيه', 'اختر ملفاً لنسخه.')
            return
        name, ok = QInputDialog.getText(self, 'نسخ ملف إعدادات', 'اسم الملف الجديد:')
        if not ok or not name.strip():
            return
        try:
            settings_service.clone_profile(profile_id, name.strip())
            self.refresh_profiles()
            show_toast(self, 'تم نسخ ملف الإعدادات')
        except Exception as exc:
            QMessageBox.critical(self, 'خطأ', str(exc))

    def export_selected_profile(self):
        profile_id = self._selected_profile_id() or int((settings_service.get_active_profile() or {}).get('id') or 1)
        path, _ = QFileDialog.getSaveFileName(self, 'تصدير ملف الإعدادات', 'settings_profile.json', 'JSON (*.json)')
        if not path:
            return
        try:
            payload = settings_service.export_profile_dict(profile_id)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, 'تم', 'تم تصدير ملف الإعدادات بنجاح.')
        except Exception as exc:
            QMessageBox.critical(self, 'خطأ', str(exc))

    def import_settings_profile(self):
        path, _ = QFileDialog.getOpenFileName(self, 'استيراد ملف إعدادات', '', 'JSON (*.json)')
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                payload = json.load(f)
            settings_service.import_profile_dict(payload)
            self.refresh_profiles()
            QMessageBox.information(self, 'تم', 'تم استيراد ملف الإعدادات.')
        except Exception as exc:
            QMessageBox.critical(self, 'خطأ', str(exc))

    def create_security_tab(self):
        scroll, layout = self._scroll_tab()
        group, form = self._form_card('إعدادات المستخدمين والصلاحيات', 'سياسات تشغيلية عامة تُقرأ وقت التنفيذ عبر PermissionService. المدير admin يبقى مستثنى افتراضيًا.')
        cfg = settings_service.get_security_settings()
        self.sec_hide_profit = QCheckBox(translate('phase233_ui_087'))
        self.sec_hide_profit.setChecked(bool(cfg.get('hide_profit_for_non_admin')))
        form.addRow(self.sec_hide_profit)
        self.sec_prevent_delete = QCheckBox(translate('phase233_ui_088'))
        self.sec_prevent_delete.setChecked(bool(cfg.get('prevent_delete_for_non_admin')))
        form.addRow(self.sec_prevent_delete)
        self.sec_prevent_invoice_edit = QCheckBox(translate('phase233_ui_089'))
        self.sec_prevent_invoice_edit.setChecked(bool(cfg.get('prevent_invoice_edit_for_non_admin')))
        form.addRow(self.sec_prevent_invoice_edit)
        self.sec_prevent_return_edit = QCheckBox(translate('phase233_ui_090'))
        self.sec_prevent_return_edit.setChecked(bool(cfg.get('prevent_return_edit_for_non_admin')))
        form.addRow(self.sec_prevent_return_edit)
        self.sec_reports_admin_only = QCheckBox(translate('phase233_ui_091'))
        self.sec_reports_admin_only.setChecked(bool(cfg.get('restrict_reports_to_admin')))
        form.addRow(self.sec_reports_admin_only)
        self.sec_report_export_admin_only = QCheckBox(translate('phase233_ui_092'))
        self.sec_report_export_admin_only.setChecked(bool(cfg.get('restrict_report_export_to_admin')))
        form.addRow(self.sec_report_export_admin_only)
        self.sec_blocked_report_roles = QLineEdit(str(cfg.get('blocked_report_roles') or ''))
        self.sec_blocked_report_roles.setPlaceholderText('مثال: cashier,viewer')
        form.addRow('أدوار ممنوعة من التقارير', self.sec_blocked_report_roles)
        form.addRow(self._note('هذه المرحلة تؤسس طبقة سياسة مركزية. ربط كل زر حذف/تعديل في الشاشات سيتم تدريجيًا باستدعاء permission_service.can(...).', 'info'))
        save_btn = QPushButton(translate('phase233_ui_093'))
        save_btn.setObjectName('primary')
        save_btn.clicked.connect(self.save_security_settings)
        form.addRow(self._button_row(save_btn))
        layout.addWidget(group)
        layout.addStretch()
        return scroll

    def save_security_settings(self):
        settings_service.save_security_settings(
            hide_profit_for_non_admin=self.sec_hide_profit.isChecked(),
            prevent_delete_for_non_admin=self.sec_prevent_delete.isChecked(),
            prevent_invoice_edit_for_non_admin=self.sec_prevent_invoice_edit.isChecked(),
            prevent_return_edit_for_non_admin=self.sec_prevent_return_edit.isChecked(),
            restrict_reports_to_admin=self.sec_reports_admin_only.isChecked(),
            restrict_report_export_to_admin=self.sec_report_export_admin_only.isChecked(),
            blocked_report_roles=self.sec_blocked_report_roles.text().strip(),
        )
        show_toast('تم حفظ إعدادات الصلاحيات', 'success', self)


    def create_workflow_tab(self):
        scroll, layout = self._scroll_tab()
        group, form = self._form_card('سياسات سير العمل', 'تحدد متى يسمح النظام بتعديل أو حذف الفواتير حسب حالة المستند، مع حدود اعتماد للمبيعات والمشتريات.')
        self.workflow_enabled_cb = QCheckBox(translate('phase233_ui_094'))
        self.workflow_approval_required_cb = QCheckBox(translate('phase233_ui_095'))
        form.addRow('تشغيل Workflow', self.workflow_enabled_cb)
        form.addRow('الاعتماد قبل الترحيل', self.workflow_approval_required_cb)
        self.workflow_sales_threshold = QLineEdit()
        self.workflow_purchase_threshold = QLineEdit()
        form.addRow('حد اعتماد المبيعات', self.workflow_sales_threshold)
        form.addRow('حد اعتماد المشتريات', self.workflow_purchase_threshold)

        self.workflow_checks = {}
        for status, label in [
            ('draft', 'Draft / مسودة'),
            ('submitted', 'Submitted / مرسلة'),
            ('approved', 'Approved / معتمدة'),
            ('posted', 'Posted / مرحلة'),
            ('cancelled', 'Cancelled / ملغاة'),
        ]:
            edit_cb = QCheckBox(translate('phase233_ui_110'))
            delete_cb = QCheckBox(translate('phase233_ui_111'))
            row = QHBoxLayout(); row.addWidget(edit_cb); row.addWidget(delete_cb); row.addStretch()
            form.addRow(label, row)
            self.workflow_checks[status] = (edit_cb, delete_cb)
        save_btn = QPushButton(translate('phase233_ui_096'))
        save_btn.clicked.connect(self.save_workflow_settings)
        layout.addWidget(group)
        layout.addLayout(self._button_row(save_btn))
        layout.addStretch()
        self.load_workflow_settings()
        return scroll

    def load_workflow_settings(self):
        try:
            self.workflow_enabled_cb.setChecked(settings_service.get_bool('workflow/enabled', False))
            self.workflow_approval_required_cb.setChecked(settings_service.get_bool('workflow/approval_required', False))
            self.workflow_sales_threshold.setText(str(settings_service.get('workflow/sales_approval_threshold', '0') or '0'))
            self.workflow_purchase_threshold.setText(str(settings_service.get('workflow/purchase_approval_threshold', '0') or '0'))
            defaults_edit = {'draft': True, 'submitted': True, 'approved': False, 'posted': False, 'cancelled': False}
            defaults_delete = dict(defaults_edit)
            for status, (edit_cb, delete_cb) in self.workflow_checks.items():
                edit_cb.setChecked(settings_service.get_bool(f'workflow/allow_edit_{status}', defaults_edit.get(status, False)))
                delete_cb.setChecked(settings_service.get_bool(f'workflow/allow_delete_{status}', defaults_delete.get(status, False)))
        except Exception as exc:
            QMessageBox.warning(self, 'خطأ', f'تعذر تحميل سياسات سير العمل: {exc}')

    def save_workflow_settings(self):
        try:
            settings_service.set('workflow/enabled', 'true' if self.workflow_enabled_cb.isChecked() else 'false')
            settings_service.set('workflow/approval_required', 'true' if self.workflow_approval_required_cb.isChecked() else 'false')
            settings_service.set('workflow/sales_approval_threshold', self.workflow_sales_threshold.text().strip() or '0')
            settings_service.set('workflow/purchase_approval_threshold', self.workflow_purchase_threshold.text().strip() or '0')
            for status, (edit_cb, delete_cb) in self.workflow_checks.items():
                settings_service.set(f'workflow/allow_edit_{status}', 'true' if edit_cb.isChecked() else 'false')
                settings_service.set(f'workflow/allow_delete_{status}', 'true' if delete_cb.isChecked() else 'false')
            settings_service.clear_cache()
            QMessageBox.information(self, 'تم', 'تم حفظ سياسات سير العمل.')
        except Exception as exc:
            QMessageBox.critical(self, 'خطأ', f'تعذر حفظ سياسات سير العمل: {exc}')

    def create_settings_audit_tab(self):
        scroll, layout = self._scroll_tab()
        group, box = self._card('سجل تغييرات الإعدادات', 'يعرض آخر تغييرات جدول settings_audit مع أدوات تصدير/استيراد الإعدادات للدعم الفني.')
        self.settings_audit_table = EditableSmartGrid(0, 5, identity='settings.audit')
        self.settings_audit_table.setHorizontalHeaderLabels(['الوقت', 'المفتاح', 'القيمة السابقة', 'القيمة الجديدة', 'المصدر'])
        self.settings_audit_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.settings_audit_table.setAlternatingRowColors(True)
        box.addWidget(self.settings_audit_table)
        refresh_btn = QPushButton(translate('phase233_ui_097'))
        refresh_btn.clicked.connect(self.refresh_settings_audit)
        export_btn = QPushButton(translate('phase233_ui_098'))
        export_btn.clicked.connect(self.export_settings_json)
        import_btn = QPushButton(translate('phase233_ui_099'))
        import_btn.clicked.connect(self.import_settings_json)
        box.addLayout(self._button_row(import_btn, export_btn, refresh_btn))
        layout.addWidget(group)
        layout.addStretch()
        self.refresh_settings_audit()
        return scroll

    def refresh_settings_audit(self):
        rows = settings_service.audit_rows(200)
        self.settings_audit_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            values = [row.get('changed_at', ''), row.get('setting_key', ''), row.get('old_value', ''), row.get('new_value', ''), row.get('source', '')]
            for c, val in enumerate(values):
                item = QTableWidgetItem(str(val if val is not None else ''))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.settings_audit_table.setItem(r, c, item)

    def export_settings_json(self):
        path, _ = QFileDialog.getSaveFileName(self, 'تصدير الإعدادات', 'settings_export.json', 'JSON Files (*.json)')
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as fh:
                json.dump(settings_service.export_settings_dict(), fh, ensure_ascii=False, indent=2)
            show_toast('تم تصدير الإعدادات', 'success', self)
        except Exception as exc:
            QMessageBox.critical(self, 'فشل التصدير', str(exc))

    def import_settings_json(self):
        path, _ = QFileDialog.getOpenFileName(self, 'استيراد الإعدادات', '', 'JSON Files (*.json)')
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as fh:
                payload = json.load(fh)
            count = settings_service.import_settings_dict(payload)
            self.refresh_settings_audit()
            show_toast(f'تم استيراد {count} إعداد', 'success', self)
        except Exception as exc:
            QMessageBox.critical(self, 'فشل الاستيراد', str(exc))

    def create_security_events_tab(self):
        scroll, layout = self._scroll_tab()
        group, box = self._card('سجل الصلاحيات والأمان', 'يعرض العمليات التي منعتها سياسات الصلاحيات: حذف، تعديل فواتير، تعديل مرتجعات، عرض/تصدير تقارير.')
        self.security_events_table = EditableSmartGrid(0, 6, identity='settings.security_events')
        self.security_events_table.setHorizontalHeaderLabels(['الوقت', 'الحدث', 'الإجراء', 'الدور', 'المستخدم', 'السبب'])
        self.security_events_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.security_events_table.setAlternatingRowColors(True)
        box.addWidget(self.security_events_table)
        self.security_events_summary = QLabel('')
        self.security_events_summary.setWordWrap(True)
        box.addWidget(self.security_events_summary)
        refresh_btn = QPushButton(translate('phase233_ui_100'))
        refresh_btn.clicked.connect(self.refresh_security_events)
        box.addLayout(self._button_row(refresh_btn))
        layout.addWidget(group)
        layout.addStretch()
        self.refresh_security_events()
        return scroll

    def refresh_security_events(self):
        rows = settings_service.security_event_rows(300)
        self.security_events_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            values = [row.get('created_at', ''), row.get('event_type', ''), row.get('action', ''), row.get('role', ''), row.get('username', ''), row.get('reason', '')]
            for c, val in enumerate(values):
                item = QTableWidgetItem(str(val if val is not None else ''))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.security_events_table.setItem(r, c, item)
        self.security_events_summary.setText(translate('settings_security_events_summary', count=len(rows), denied=settings_service.security_denied_count()))


    def create_backup_tab(self):
        scroll, layout = self._scroll_tab()
        group, form = self._form_card(translate('settings_backup_title'), translate('settings_backup_help'))
        self.backup_enabled = QCheckBox(translate('settings_backup_enable_auto'))
        form.addRow(self.backup_enabled)

        self.backup_frequency = QComboBox()
        self.backup_frequency.addItem(translate('phase233_ui_102'), 'manual')
        self.backup_frequency.addItem(translate('phase233_ui_103'), 'daily')
        self.backup_frequency.addItem(translate('phase233_ui_104'), 'weekly')
        self.backup_frequency.addItem(translate('phase233_ui_105'), 'interval')
        form.addRow('التكرار', self.backup_frequency)

        self.backup_interval = QSpinBox(); self.backup_interval.setRange(1, 168); self.backup_interval.setSuffix(' ' + translate('hour'))
        form.addRow(translate('settings_backup_every_label'), self.backup_interval)

        self.backup_retention = QSpinBox(); self.backup_retention.setRange(1, 365); self.backup_retention.setSuffix(' نسخة')
        form.addRow('عدد النسخ المحتفظ بها', self.backup_retention)

        self.backup_create_on_exit = QCheckBox(translate('phase233_ui_106'))
        form.addRow(self.backup_create_on_exit)

        self.backup_folder = QLineEdit(); self.backup_folder.setPlaceholderText(translate('settings_backup_folder_placeholder'))
        browse_btn = QPushButton(translate('browse')); browse_btn.clicked.connect(self.browse_backup_folder)
        row = QHBoxLayout(); row.addWidget(self.backup_folder, 1); row.addWidget(browse_btn)
        form.addRow(translate('settings_backup_target_folder_label'), row)

        self.backup_status_label = QLabel('')
        self.backup_status_label.setWordWrap(True)
        form.addRow('آخر نسخة', self.backup_status_label)

        save_backup_btn = QPushButton(translate('settings_backup_save')); save_backup_btn.setObjectName('primary'); save_backup_btn.clicked.connect(self.save_backup_settings)
        form.addRow(self._button_row(save_backup_btn)); layout.addWidget(group)

        instant_group, instant_box = self._card(translate('settings_backup_instant_title'), translate('settings_backup_instant_help'))
        backup_now_btn = QPushButton(translate('settings_backup_create_now')); backup_now_btn.setObjectName('primary'); backup_now_btn.clicked.connect(self.create_backup_now)
        cleanup_btn = QPushButton(translate('phase233_ui_107')); cleanup_btn.clicked.connect(self.cleanup_old_backups)
        refresh_btn = QPushButton(translate('phase233_ui_108')); refresh_btn.clicked.connect(self.refresh_backup_status)
        instant_box.addLayout(self._button_row(refresh_btn, cleanup_btn, backup_now_btn)); layout.addWidget(instant_group)

        manage_group, manage_box = self._card(translate('settings_database_admin_title'), translate('settings_database_admin_help'))
        manage_layout = QHBoxLayout()
        self.export_btn = QPushButton(translate('settings_database_export')); self.export_btn.clicked.connect(self.export_database)
        self.import_btn = QPushButton(translate('settings_database_import')); self.import_btn.clicked.connect(self.import_database)
        self.reset_btn = QPushButton(translate('settings_database_reset')); self.reset_btn.setObjectName('danger'); self.reset_btn.clicked.connect(self.reset_database)
        manage_layout.addWidget(self.export_btn); manage_layout.addWidget(self.import_btn); manage_layout.addWidget(self.reset_btn)
        manage_box.addLayout(manage_layout); layout.addWidget(manage_group)
        layout.addStretch(); self.load_backup_settings(); self.refresh_backup_status(); return scroll


    def create_diagnostics_tab(self):
        scroll, layout = self._scroll_tab()
        group, box = self._card('تشخيص النظام', 'فحص سريع لصحة قاعدة البيانات والجداول الأساسية والإحصاءات التشغيلية.')
        self.diagnostics_text = QPlainTextEdit()
        self.diagnostics_text.setReadOnly(True)
        self.diagnostics_text.setMinimumHeight(420)
        box.addWidget(self.diagnostics_text)
        refresh_btn = QPushButton(translate('phase233_ui_109'))
        refresh_btn.setObjectName('primary')
        refresh_btn.clicked.connect(self.refresh_diagnostics)
        box.addLayout(self._button_row(refresh_btn))
        layout.addWidget(group)
        layout.addStretch()
        self.refresh_diagnostics()
        return scroll

    def refresh_diagnostics(self):
        lines = []
        try:
            snapshot = system_service.local_diagnostics_snapshot()
            is_remote = snapshot.get('mode') == 'remote'
            lines.append('وضع الاتصال: ' + ('Remote API' if is_remote else 'Local SQLite'))
            lines.append('مصدر البيانات: ' + system_service.data_source_label())
            try:
                phealth = settings_service.profile_health()
                prof = phealth.get('active_profile') or {}
                lines.append('')
                lines.append('ملف الإعدادات النشط:')
                lines.append('- الاسم: ' + str(prof.get('name', 'Default')))
                lines.append('- عدد إعدادات الملف: ' + str(prof.get('settings_count', 0)))
                missing = phealth.get('missing_settings') or []
                lines.append('- إعدادات ناقصة: ' + (', '.join(missing) if missing else 'لا يوجد'))
            except Exception as exc:
                lines.append('- فحص ملفات الإعدادات: فشل (' + str(exc) + ')')
            try:
                branch_service.bootstrap()
                bdiag = branch_service.diagnostics()
                lines.append('')
                lines.append('الفروع:')
                lines.append('- الفرع الحالي/الافتراضي: ' + (branch_service.branch_name(branch_service.default_branch_id()) or 'غير محدد'))
                for check in bdiag.get('checks', []):
                    lines.append(f"- {check.get('label')}: {check.get('value')}")
            except Exception as exc:
                lines.append('- فحص الفروع: فشل (' + str(exc) + ')')
            try:
                bcfg = settings_service.get_backup_settings()
                lines.append('')
                lines.append('النسخ الاحتياطي:')
                lines.append('- مفعل: ' + ('نعم' if bcfg.get('enabled') else 'لا'))
                lines.append('- التكرار: ' + str(bcfg.get('frequency')))
                lines.append('- مسار النسخ: ' + (bcfg.get('folder') or 'غير محدد'))
                lines.append('- الاحتفاظ: ' + str(bcfg.get('retention_count')) + ' نسخة')
                if bcfg.get('folder') and not backup_service.is_remote():
                    binfo = backup_service.list_backups(bcfg.get('folder'))
                    latest = binfo.get('latest')
                    lines.append('- عدد النسخ الموجودة: ' + str(binfo.get('count', 0)))
                    lines.append('- آخر نسخة: ' + (latest.get('created_at') + ' / ' + latest.get('filename') if latest else 'لا يوجد'))
            except Exception as exc:
                lines.append('- فحص النسخ الاحتياطي: فشل (' + str(exc) + ')')
            if not is_remote:
                if snapshot.get('db_path'):
                    lines.append('مسار قاعدة البيانات: ' + str(snapshot.get('db_path')))
                if snapshot.get('db_size_mb') is not None:
                    lines.append('حجم قاعدة البيانات: %.2f MB' % float(snapshot.get('db_size_mb')))
                lines.append('')
                lines.append('الإحصاءات:')
                for item in (snapshot.get('table_counts') or {}).values():
                    lines.append(f"- {item.get('label')}: {item.get('value')}")
                lines.append('')
                lines.append('فحص الجداول الأساسية:')
                for table, exists in (snapshot.get('required_tables') or {}).items():
                    lines.append(f'- {table}: ' + ('OK' if exists else 'MISSING'))
                lines.append('')
                lines.append('فحص الاتساق:')
                consistency = snapshot.get('consistency') or {}
                lines.append(f"- مواد بمخزون سالب: {consistency.get('negative_items_stock', 'غير قابل للفحص')}")
                lines.append(f"- أسطر فواتير بلا فاتورة: {consistency.get('orphan_invoice_lines', 'غير قابل للفحص')}")
                lines.append(f"- PRAGMA quick_check: {consistency.get('sqlite_quick_check', 'غير قابل للفحص')}")
                try:
                    integrity = system_service.integrity_checks()
                    lines.append('')
                    lines.append('فحص الاتساق المتقدم:')
                    lines.append('- مجموع المخاطر: ' + str(integrity.get('risk_count', 0)))
                    for check in integrity.get('checks', []):
                        lines.append(f"- {check.get('label')}: {check.get('value')}")
                    audit = settings_service.audit_rows(10)
                    lines.append('')
                    lines.append('آخر تغييرات الإعدادات:')
                    if audit:
                        for row in audit[:10]:
                            lines.append(f"- {row.get('changed_at')} | {row.get('setting_key')} | {row.get('old_value')} -> {row.get('new_value')}")
                    else:
                        lines.append('- لا يوجد سجل تغييرات بعد')
                except Exception as exc:
                    lines.append('- فحص الاتساق المتقدم: فشل (' + str(exc) + ')')
            else:
                lines.append('حالة الخادم: ' + str(snapshot.get('remote_status') or system_service.debug_status()))
        except Exception as exc:
            lines.append('فشل التشخيص: ' + str(exc))
        self.diagnostics_text.setPlainText('\n'.join(lines))



    def _refresh_language_texts(self):
        self.setLayoutDirection(qt_layout_direction(self._current_language))
        try:
            labels = [
                '🎨 ' + translate('appearance'),
                translate('phase233_ui_037'),
                '🏢 ' + translate('company'),
                translate('phase233_ui_039'),
                translate('phase233_ui_040'),
                translate('phase233_ui_041'),
                translate('phase233_ui_042'),
                translate('phase233_ui_043'),
                translate('phase233_ui_044'),
                '🖨️ ' + translate('printing_tab'),
                '🧾 ' + translate('pos_tab'),
                '💰 ' + translate('currencies'),
                '💱 ' + translate('exchange_rates'),
                '🌐 ' + translate('network'),
                translate('phase233_ui_045'),
                translate('phase233_ui_047'),
                translate('phase233_ui_048'),
                '💾 ' + translate('backup_data'),
                translate('phase233_ui_049'),
            ]
            for i, label in enumerate(labels):
                if i < self.tabs.count():
                    self.tabs.setTabText(i, label)
        except Exception:
            pass

    def save_appearance_settings(self):
        theme = self.theme_combo.currentData() or 'light'
        lang = normalize_language(self.language_combo.currentData() if hasattr(self, 'language_combo') else self._current_language)
        settings_service.set_theme(theme)
        langs = settings_service.get_language_settings()
        settings_service.save_language_settings(lang, langs.get('print_language', lang), langs.get('report_language', lang))
        set_language(lang)
        self._current_language = lang
        self.setLayoutDirection(qt_layout_direction(lang))
        settings_service.set('ui/font_size', self.ui_font_size.value())
        settings_service.set('ui/row_height', self.ui_row_height.value())
        self._set_bool_setting('ui/show_global_search', False)
        settings_service.set('ui/default_page', self.ui_default_page.text().strip() or 'dashboard')
        self._set_bool_setting('ui/remember_last_tab', self.ui_remember_last_tab.isChecked())
        settings_service.clear_cache()
        ThemeManager.apply_theme(theme, persist=True)
        self._refresh_language_texts()
        main_window = self.window()
        if hasattr(main_window, 'setLayoutDirection'):
            main_window.setLayoutDirection(qt_layout_direction(lang))
        if hasattr(main_window, 'setup_menus'):
            main_window.setup_menus()
        if hasattr(main_window, 'top_bar') and hasattr(main_window.top_bar, 'apply_styles'):
            try:
                box = getattr(main_window.top_bar, 'search_box', None)
                if box is not None:
                    box.setPlaceholderText(translate('global_search_placeholder'))
                main_window.top_bar.alert_btn.setText('')
                main_window.top_bar.alert_btn.setToolTip(translate('alerts'))
                main_window.top_bar.theme_btn.setText('')
                main_window.top_bar.theme_btn.setToolTip(translate('toggle_theme'))
                if hasattr(main_window.top_bar, 'screenshot_btn'):
                    main_window.top_bar.screenshot_btn.setText('')
                    main_window.top_bar.screenshot_btn.setToolTip(translate('export_screenshot'))
            except Exception:
                pass
            main_window.top_bar.apply_styles()
        for page in getattr(main_window, 'pages', {}).values():
            if hasattr(page, 'setLayoutDirection'):
                page.setLayoutDirection(qt_layout_direction(lang))
            if hasattr(page, 'apply_theme_colors'):
                page.apply_theme_colors()
        show_toast(translate('language_saved'), 'success', self)

    def save_printing_settings(self):
        settings_service.save_printing_settings(
            invoice_template=self.print_invoice_template.currentData() or 'a4',
            report_template=self.print_report_template.currentData() or 'a4',
            voucher_template=self.print_voucher_template.currentData() or 'a4',
            return_template=self.print_return_template.currentData() or 'a4',
            show_logo=self.print_show_logo.isChecked(),
            show_tax_number=self.print_show_tax.isChecked(),
            show_qr=self.print_show_qr.isChecked(),
            footer_text=self.print_footer.text().strip(),
            thermal_size=self.print_thermal_size.currentText(),
            font_family=self.print_font_family.text().strip(),
            font_size=self.print_font_size.currentText(),
            accent_color=self.print_accent_color.text().strip(),
            zebra_rows=self.print_zebra_rows.isChecked(),
            compact_tables=self.print_compact_tables.isChecked(),
            barcode_default_printer=self.barcode_default_printer.currentData() or '',
            barcode_label_size=self.barcode_label_size.currentText(),
            barcode_symbology=self.barcode_symbology.currentText(),
            barcode_copies=self.barcode_copies.value(),
            barcode_columns=self.barcode_columns.value(),
            barcode_show_company=self.barcode_show_company.isChecked(),
            barcode_show_logo=self.barcode_show_logo.isChecked(),
            barcode_show_qr=self.barcode_show_qr.isChecked(),
            barcode_show_name=self.barcode_show_name.isChecked(),
            barcode_show_price=self.barcode_show_price.isChecked(),
            barcode_show_text=self.barcode_show_text.isChecked(),
        )
        show_toast(translate('settings_print_saved'), 'success', self)

    def browse_logo(self):
        filename, _ = QFileDialog.getOpenFileName(self, translate('settings_company_choose_logo_dialog'), '', 'Images (*.png *.jpg *.jpeg *.bmp)')
        if filename: self.company_logo_path_edit.setText(filename)

    def save_company_info(self):
        from config import save_company_info
        
        try:
            from brand_assets import logo_png
            default_logo = logo_png(512)
        except Exception:
            default_logo = ''
        info = {'name': self.company_name_edit.text().strip(), 'address': self.company_address_edit.text().strip(), 'phone': self.company_phone_edit.text().strip(), 'email': self.company_email_edit.text().strip(), 'tax_number': self.company_tax_number_edit.text().strip(), 'commercial_register': self.company_commercial_register_edit.text().strip(), 'website': self.company_website_edit.text().strip(), 'logo_path': self.company_logo_path_edit.text().strip() or default_logo}
        if not self.company_logo_path_edit.text().strip() and default_logo:
            self.company_logo_path_edit.setText(default_logo)
        
        settings_service.save_company_info(info); show_toast(translate('settings_company_saved'), 'success', self)

    def browse_backup_folder(self):
        folder = QFileDialog.getExistingDirectory(self, translate('settings_backup_folder_placeholder'))
        if folder: self.backup_folder.setText(folder)

    def save_backup_settings(self):
        if backup_service.is_remote(): QMessageBox.warning(self, translate('warning'), translate('settings_backup_remote_save_blocked')); return
        try:
            settings_service.save_backup_settings(
                enabled=self.backup_enabled.isChecked(),
                frequency=self.backup_frequency.currentData() or 'daily',
                interval_hours=self.backup_interval.value(),
                folder=self.backup_folder.text().strip(),
                retention_count=self.backup_retention.value(),
                create_on_exit=self.backup_create_on_exit.isChecked(),
            )
            show_toast(translate('settings_backup_saved'), 'success', self)
            self.refresh_backup_status()
        except Exception as exc:
            QMessageBox.critical(self, translate('error'), str(exc))


    def load_backup_settings(self):
        cfg = settings_service.get_backup_settings()
        self.backup_enabled.setChecked(bool(cfg.get('enabled', False)))
        idx = self.backup_frequency.findData(cfg.get('frequency', 'daily'))
        self.backup_frequency.setCurrentIndex(idx if idx >= 0 else 1)
        self.backup_interval.setValue(int(cfg.get('interval_hours', 6) or 6))
        self.backup_folder.setText(cfg.get('folder', '') or '')
        self.backup_retention.setValue(int(cfg.get('retention_count', 10) or 10))
        self.backup_create_on_exit.setChecked(bool(cfg.get('create_on_exit', False)))

    def refresh_backup_status(self):
        try:
            folder = self.backup_folder.text().strip()
            if backup_service.is_remote():
                self.backup_status_label.setText(translate('phase233_ui_112'))
                return
            if not folder:
                self.backup_status_label.setText(translate('phase233_ui_113'))
                return
            info = backup_service.list_backups(folder)
            latest = info.get('latest')
            if latest:
                size_mb = float(latest.get('size_bytes', 0) or 0) / (1024 * 1024)
                self.backup_status_label.setText(translate('settings_backup_latest_summary', filename=latest.get('filename'), created=latest.get('created_at'), size=f'{size_mb:.2f}', count=info.get('count', 0)))
            else:
                self.backup_status_label.setText(translate('phase233_ui_115'))
        except Exception as exc:
            self.backup_status_label.setText(translate('settings_backup_status_failed', error=exc))


    def create_backup_now(self):
        if backup_service.is_remote(): QMessageBox.warning(self, translate('warning'), translate('settings_backup_remote_create_blocked')); return
        folder = self.backup_folder.text().strip()
        if not folder: QMessageBox.warning(self, translate('error'), translate('settings_backup_folder_required')); return
        try:
            result = backup_service.create_backup(folder); sep = chr(10)
            try:
                backup_service.cleanup_old_backups(folder, self.backup_retention.value())
            except Exception:
                pass
            self.refresh_backup_status()
            QMessageBox.information(self, translate('success'), translate('settings_backup_created_integrity', sep=sep, path=result['backup_path'], sha256=result['sha256']))
        except Exception as e: QMessageBox.critical(self, translate('error'), translate('settings_backup_failed', error=str(e)))

    def cleanup_old_backups(self):
        if backup_service.is_remote(): QMessageBox.warning(self, translate('warning'), translate('settings_backup_remote_create_blocked')); return
        folder = self.backup_folder.text().strip()
        if not folder: QMessageBox.warning(self, translate('error'), translate('settings_backup_folder_required')); return
        try:
            result = backup_service.cleanup_old_backups(folder, self.backup_retention.value())
            self.refresh_backup_status()
            QMessageBox.information(self, translate('success'), f"تم حذف {result.get('removed_count', 0)} نسخة قديمة.")
        except Exception as e:
            QMessageBox.critical(self, translate('error'), str(e))

    def export_database(self):
        if backup_service.is_remote(): QMessageBox.warning(self, translate('warning'), translate('settings_db_remote_export_blocked')); return
        filename, _ = QFileDialog.getSaveFileName(self, translate('settings_database_export'), 'alrajhi_backup.db', 'SQLite (*.db)')
        if filename:
            try:
                result = backup_service.export_database(filename); QMessageBox.information(self, translate('success'), translate('settings_export_success_integrity', path=result['backup_path']))
            except Exception as e: QMessageBox.critical(self, translate('error'), translate('settings_export_failed', error=str(e)))

    def import_database(self):
        if backup_service.is_remote(): QMessageBox.warning(self, translate('warning'), translate('settings_db_remote_import_blocked')); return
        filename, _ = QFileDialog.getOpenFileName(self, translate('settings_database_import'), '', 'SQLite (*.db)')
        if filename:
            try: backup_service.validate_backup(filename)
            except Exception as e: QMessageBox.critical(self, translate('error'), translate('settings_invalid_backup_file', error=str(e))); return
            reply = QMessageBox.question(self, translate('confirm'), translate('settings_db_import_confirm'), QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    result = backup_service.restore_backup(filename, create_pre_restore_backup=True); sep = chr(10); msg = translate('settings_import_success_restart')
                    if result.get('pre_restore_backup'): msg += translate('settings_pre_restore_backup_line', sep=sep, path=result['pre_restore_backup'])
                    QMessageBox.information(self, translate('success'), msg)
                except Exception as e: QMessageBox.critical(self, translate('error'), translate('settings_import_failed', error=str(e)))

    def reset_database(self):
        if backup_service.is_remote(): QMessageBox.warning(self, translate('warning'), translate('settings_db_remote_reset_blocked')); return
        reply = QMessageBox.question(self, translate('danger_confirm'), translate('settings_db_reset_confirm'), QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                result = backup_service.reset_database()
                msg = translate('settings_database_reset_done')
                pre_reset = result.get('pre_reset_backup')
                if pre_reset: msg += translate('settings_pre_reset_backup_line', path=pre_reset)
                QMessageBox.information(self, translate('success'), msg)
            except Exception as e: QMessageBox.critical(self, translate('error'), translate('settings_reset_failed', error=str(e)))

    def load_rates_table(self):
        rates = currency.get_all_currencies(); self.rates_table.setRowCount(len(rates))
        for row, r in enumerate(rates):
            self.rates_table.setItem(row, 0, QTableWidgetItem(r['currency_code']))
            rate_item = QTableWidgetItem(f"{float(r['rate_to_usd']):.4f}"); rate_item.setFlags(rate_item.flags() | Qt.ItemIsEditable)
            self.rates_table.setItem(row, 1, rate_item); self.rates_table.setItem(row, 2, QTableWidgetItem(r['updated_at'][:19] if r.get('updated_at') else ''))

    def save_currency_settings(self):
        base_curr = self.base_curr.currentText(); display_curr = self.display_curr.currentText(); decimals = self.decimals.value(); fmt = 'western' if self.format_combo.currentIndex() == 0 else 'arabic'; abbrev_bool = self.abbreviate_check.isChecked()
        old_currency = self.settings.get_currency_settings()
        for row in range(self.rates_table.rowCount()):
            code_item = self.rates_table.item(row, 0); rate_item = self.rates_table.item(row, 1)
            if not code_item or not rate_item: continue
            code = code_item.text(); rate_text = rate_item.text(); clean_rate_text = rate_text.replace(',', '').replace(' ', '').strip()
            try: currency.update_rate(code, float(clean_rate_text))
            except ValueError: QMessageBox.warning(self, translate('error'), translate('settings_invalid_currency_rate', code=code, rate=rate_text)); return
        rates_payload = []
        for row in range(self.rates_table.rowCount()):
            code_item = self.rates_table.item(row, 0); rate_item = self.rates_table.item(row, 1)
            if code_item and rate_item:
                rates_payload.append({'currency_code': code_item.text(), 'rate': rate_item.text()})
        self.settings.save_currency_settings(base_curr, display_curr, decimals, fmt, abbrev_bool)
        audit_service.log('UPDATE', 'CURRENCY_RATES', None, old_values=old_currency, new_values={'rates': rates_payload}, details=translate('settings_rates_audit_update'))
        QMessageBox.information(self, translate('success'), translate('settings_currency_rates_saved')); self.currency_settings_changed.emit()
        main_window = self.window()
        if hasattr(main_window, 'pages') and 'dashboard' in main_window.pages and hasattr(main_window.pages['dashboard'], 'reload_from_settings'): main_window.pages['dashboard'].reload_from_settings()

    def fetch_online_rates(self):
        try:
            resp = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=10)
            if resp.status_code == 200:
                rates = resp.json().get('rates', {})
                for row in range(self.rates_table.rowCount()):
                    code = self.rates_table.item(row, 0).text()
                    if code in rates: self.rates_table.item(row, 1).setText(f"{rates[code]:.4f}")
                QMessageBox.information(self, translate('success'), translate('settings_rates_updated_online'))
            else: QMessageBox.warning(self, translate('error'), translate('server_connection_failed'))
        except Exception as e: QMessageBox.warning(self, translate('error'), translate('error_with_message', error=str(e)))

    def activate_network_dialog(self):
        dialog = QDialog(self); dialog.setWindowTitle(translate('settings_network_activation_title')); dialog.setLayoutDirection(Qt.RightToLeft); dialog.resize(460, 220)
        layout = QVBoxLayout(dialog); layout.addWidget(self._note(translate('settings_network_activation_help'), 'info'))
        key_edit = QLineEdit(); key_edit.setEchoMode(QLineEdit.Password); key_edit.setPlaceholderText(translate('settings_network_activation_key')); layout.addWidget(key_edit)
        status_label = QLabel(); status_label.setStyleSheet(f"color: {ThemeManager.get('danger')};"); layout.addWidget(status_label)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self._do_activate_network(key_edit.text().strip(), status_label, dialog)); button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box); dialog.exec()

    def _do_activate_network(self, key, status_label, dialog):
        if not key: status_label.setText(translate('settings_network_activation_required')); return
        success, msg = activate_network(key)
        if success:
            audit_service.log('ACTIVATE', 'NETWORK', None, new_values={'activated': True}, details=translate('settings_network_activation_audit'))
            QMessageBox.information(self, translate('success'), translate('settings_network_activated')); dialog.accept()
        else: status_label.setText(translate('failed_with_message', message=msg))

    def refresh_server_status(self):
        if not hasattr(self, 'server_status_label'):
            return
        info = system_service.get_server_runtime_info()
        running = bool(info.get('running'))
        msg = str(info.get('message') or '')
        self.server_status_label.setText(('✅ ' if running else '⚪ ') + msg)
        self.server_status_label.setStyleSheet(f"color: {ThemeManager.get('success') if running else ThemeManager.get('text_secondary')};")
        if hasattr(self, 'server_pid_label'):
            self.server_pid_label.setText(str(info.get('pid') or '-'))
            self.server_uptime_label.setText(str(info.get('uptime') or '-'))
            self.server_db_path_label.setText(str(info.get('db_path') or '-'))
            self.server_backup_path_label.setText(str(info.get('backup_dir') or '-'))

    def start_local_server_now(self):
        settings = QSettings('Alrajhi', 'Accounting')
        settings.setValue('server/port', self.server_port_spin.value())
        settings.sync()
        ok, msg = system_service.start_server_process(port=self.server_port_spin.value())
        QMessageBox.information(self, translate('settings_network_start_server_title') if ok else translate('settings_network_start_server_failed'), msg)
        self.refresh_server_status()

    def stop_local_server_now(self):
        ok, msg = system_service.stop_server_process()
        QMessageBox.information(self, translate('settings_network_stop_server_title') if ok else translate('settings_network_stop_server_failed'), msg)
        self.refresh_server_status()

    def restart_local_server_now(self):
        ok, msg = system_service.restart_server_process(port=self.server_port_spin.value())
        QMessageBox.information(self, translate('settings_network_restart_server_title') if ok else translate('settings_network_restart_server_failed'), msg)
        self.refresh_server_status()

    def backup_local_server_database(self):
        ok, msg = system_service.backup_server_database()
        QMessageBox.information(self, translate('settings_network_backup_server_db') if ok else translate('settings_network_backup_failed'), msg)
        self.refresh_server_status()

    def open_local_server_data_dir(self):
        ok, msg = system_service.open_server_data_dir()
        if not ok:
            QMessageBox.warning(self, translate('settings_network_open_data_dir_title'), msg)
        self.refresh_server_status()

    def test_network_connection(self):
        raw = self.server_url_edit.text().strip()
        port = self.server_port_spin.value()
        url = system_service.normalize_server_url(raw, port)
        ok, message, info = system_service.server_diagnostics(url, timeout=4, require_routes=True)
        self.server_url_edit.setText(url)
        details = translate('settings_network_test_details', url=url, message=message)
        if hasattr(self, 'refresh_network_center'):
            self.refresh_network_center()
        if ok:
            QMessageBox.information(self, translate('settings_network_test_connection'), translate('settings_network_test_success', details=details))
        else:
            QMessageBox.warning(self, translate('settings_network_test_connection'), translate('settings_network_test_failed', details=details))


    def refresh_network_center(self):
        """Refresh the Network Control Center without requiring a restart."""
        if not hasattr(self, 'net_connection_label'):
            return
        raw = self.server_url_edit.text().strip() if hasattr(self, 'server_url_edit') else ''
        port = self.server_port_spin.value() if hasattr(self, 'server_port_spin') else 8000
        url = system_service.normalize_server_url(raw, port)
        ok, message, info = system_service.server_diagnostics(url, timeout=4, require_routes=True)
        self.net_connection_label.setText((translate('settings_network_connected') if ok else translate('settings_network_not_compatible')) + f"\n{message}")
        self.net_connection_label.setStyleSheet(f"color: {ThemeManager.get('success') if ok else ThemeManager.get('danger')};")
        latency = info.get('latency_ms')
        routes_latency = info.get('routes_latency_ms')
        latency_text = f"/health: {latency} ms" if latency is not None else '-'
        if routes_latency is not None:
            latency_text += f" | /api/routes: {routes_latency} ms"
        self.net_latency_label.setText(latency_text)
        self.net_api_label.setText(str(info.get('api_version') or '-'))
        self.net_routes_label.setText(str(info.get('route_count') or '-'))
        missing = info.get('missing_routes') or []
        self.net_missing_label.setText(translate('none') if not missing else '\n'.join(missing))
        # Authenticated database/source diagnostics.  It may fail before login or
        # if the saved token is invalid; this must never break the settings page.
        try:
            status = system_service.debug_status()
            mode = status.get('_mode')
            if mode == 'remote' and not status.get('error'):
                self.net_db_label.setText(status.get('db_path') or '-')
                counts = status.get('counts') or {}
                quick = []
                for key, label in [('items', translate('items')), ('customers', translate('customers')), ('invoices', translate('invoices')), ('users', translate('users'))]:
                    value = counts.get(key, '-')
                    if isinstance(value, dict):
                        value = translate('error')
                    quick.append(f"{label}: {value}")
                self.net_counts_label.setText(' | '.join(quick))
            elif mode == 'remote':
                self.net_db_label.setText(translate('settings_network_remote_no_client'))
                self.net_counts_label.setText('-')
            else:
                self.net_db_label.setText(translate('settings_network_local_sqlite'))
                self.net_counts_label.setText('-')
        except Exception as exc:
            self.net_db_label.setText(translate('settings_network_db_diagnostics_failed', error=exc))
            self.net_counts_label.setText('-')

    def show_network_request_log(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(translate('settings_network_request_log_title'))
        dialog.setLayoutDirection(Qt.RightToLeft)
        dialog.resize(780, 520)
        layout = QVBoxLayout(dialog)
        text = QPlainTextEdit()
        text.setReadOnly(True)
        try:
            rows = system_service.request_log()
            if not rows:
                content = translate('settings_network_no_requests')
            else:
                lines = []
                for r in rows[-120:]:
                    ok = '✓' if r.get('ok') else '✗'
                    status = r.get('status') if r.get('status') is not None else '-'
                    ms = r.get('elapsed_ms') if r.get('elapsed_ms') is not None else '-'
                    line = f"{r.get('time','')} {ok} {r.get('method','')} {r.get('endpoint','')} [{status}] {ms}ms"
                    if r.get('error'):
                        line += f"\n    {r.get('error')}"
                    lines.append(line)
                content = '\n'.join(lines)
        except Exception as exc:
            content = translate('settings_network_request_log_read_failed', error=exc)
        text.setPlainText(content)
        layout.addWidget(text)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(dialog.reject)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        dialog.exec()

    def save_network_settings(self):
        mode = {0: 'local', 1: 'client', 2: 'server'}[self.mode_combo.currentIndex()]
        settings = QSettings('Alrajhi', 'Accounting')
        old = {
            'network/mode': settings.value('network/mode', 'local'),
            'network/server_url': settings.value('network/server_url', ''),
            'server/port': settings.value('server/port', 8000),
            'server/auto_start': settings.value('server/auto_start', False, type=bool),
        }
        port = self.server_port_spin.value() if hasattr(self, 'server_port_spin') else 8000
        url = system_service.normalize_server_url(self.server_url_edit.text().strip(), port)
        new = {
            'network/mode': mode,
            'network/server_url': url,
            'server/port': port,
            'server/auto_start': self.server_auto_start_check.isChecked() if hasattr(self, 'server_auto_start_check') else False,
        }
        settings.setValue('network/mode', mode)
        settings.setValue('network/server_url', url)
        settings.setValue('server/port', port)
        settings.setValue('server/auto_start', new['server/auto_start'])
        settings.sync()
        audit_service.log('UPDATE', 'SETTINGS_NETWORK', None, old_values=old, new_values=new, details=translate('settings_network_audit_update'))
        QMessageBox.information(self, translate('saved'), translate('settings_network_saved'))
        self.refresh_server_status()
