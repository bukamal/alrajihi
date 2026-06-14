# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QPushButton, QGroupBox, QLabel, QMessageBox, QTabWidget, QFileDialog,
    QSpinBox, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QDialogButtonBox, QScrollArea, QFrame, QPlainTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QSettings

from core.services.settings_service import settings_service
from core.services.backup_service import backup_service
from core.services.audit_service import audit_service
from core.services.system_service import system_service
from currency import currency
from auth.activation import activate_network, check_network_activation
from theme_manager import ThemeManager
from ui.design_system import DesignSystem
from utils import show_toast
from i18n.translator import translate, set_language, available_languages, normalize_language, qt_layout_direction
import requests
import os
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
        main.addWidget(self._create_header())

        self.tabs = QTabWidget()
        self.tabs.setObjectName('settingsTabs')
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self.create_appearance_tab(), '🎨 ' + translate('appearance'))
        self.tabs.addTab(self.create_company_tab(), '🏢 ' + translate('company'))
        self.tabs.addTab(self.create_printing_tab(), '🖨️ ' + translate('printing_tab'))
        self.tabs.addTab(self.create_pos_tab(), '🧾 ' + translate('pos_tab'))
        self.tabs.addTab(self.create_currency_tab(), '💰 ' + translate('currencies'))
        self.tabs.addTab(self.create_rates_tab(), '💱 ' + translate('exchange_rates'))
        self.tabs.addTab(self.create_network_tab(), '🌐 ' + translate('network'))
        self.tabs.addTab(self.create_backup_tab(), '💾 ' + translate('backup_data'))
        main.addWidget(self.tabs, 1)

        self._apply_local_style()
        # Phase 41: keep exactly one settings header inside this page.
        apply_modern_widget(self)
        self._ensure_single_settings_header()
        self.load_rates_table()


    def _ensure_single_settings_header(self):
        """Keep exactly one visible settings header inside the settings page."""
        layout = self.layout()
        if layout is None:
            return
        seen_settings_header = False
        for idx in reversed(range(layout.count())):
            item = layout.itemAt(idx)
            widget = item.widget() if item else None
            if widget is None:
                continue
            name = widget.objectName() or ''
            if name == 'ModernPageHeader':
                layout.removeWidget(widget)
                widget.deleteLater()
            elif name == 'settingsHeader':
                if seen_settings_header:
                    layout.removeWidget(widget)
                    widget.deleteLater()
                else:
                    seen_settings_header = True

    def _create_header(self):
        frame = QFrame()
        frame.setObjectName('settingsHeader')
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        texts = QVBoxLayout()
        title = QLabel(translate('settings_header_title'))
        title.setObjectName('settingsTitle')
        subtitle = QLabel(translate('settings_header_subtitle'))
        subtitle.setObjectName('settingsSubtitle')
        subtitle.setWordWrap(True)
        texts.addWidget(title)
        texts.addWidget(subtitle)
        layout.addLayout(texts, 1)
        self.settings_status = DesignSystem.status_pill(translate('ready'), 'success')
        layout.addWidget(self.settings_status, 0, Qt.AlignVCenter)
        return frame

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
        form.addRow(self._note(translate('language_settings_note'), 'info'))
        apply_btn = QPushButton(translate('apply_save_appearance'))
        apply_btn.setObjectName('primary')
        apply_btn.clicked.connect(self.save_appearance_settings)
        form.addRow(self._button_row(apply_btn))
        layout.addWidget(group)
        layout.addStretch()
        return scroll


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
        for printer in self.barcode_printer_manager.printers:
            self.barcode_default_printer.addItem(printer.name, printer.id)
        idx = self.barcode_default_printer.findData(cfg.get('barcode_default_printer', 'pdf:default'))
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
        self.rates_table = QTableWidget(); self.rates_table.setColumnCount(3); self.rates_table.setHorizontalHeaderLabels([translate('settings_rates_currency_col'), translate('settings_rates_rate_col'), translate('settings_rates_updated_col')])
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

    def create_backup_tab(self):
        scroll, layout = self._scroll_tab()
        group, form = self._form_card(translate('settings_backup_title'), translate('settings_backup_help'))
        self.backup_enabled = QCheckBox(translate('settings_backup_enable_auto')); form.addRow(self.backup_enabled)
        self.backup_interval = QSpinBox(); self.backup_interval.setRange(1, 24); self.backup_interval.setSuffix(' ' + translate('hour'))
        form.addRow(translate('settings_backup_every_label'), self.backup_interval)
        self.backup_folder = QLineEdit(); self.backup_folder.setPlaceholderText(translate('settings_backup_folder_placeholder'))
        browse_btn = QPushButton(translate('browse')); browse_btn.clicked.connect(self.browse_backup_folder)
        row = QHBoxLayout(); row.addWidget(self.backup_folder, 1); row.addWidget(browse_btn)
        form.addRow(translate('settings_backup_target_folder_label'), row)
        save_backup_btn = QPushButton(translate('settings_backup_save')); save_backup_btn.setObjectName('primary'); save_backup_btn.clicked.connect(self.save_backup_settings)
        form.addRow(self._button_row(save_backup_btn)); layout.addWidget(group)
        instant_group, instant_box = self._card(translate('settings_backup_instant_title'), translate('settings_backup_instant_help'))
        backup_now_btn = QPushButton(translate('settings_backup_create_now')); backup_now_btn.setObjectName('primary'); backup_now_btn.clicked.connect(self.create_backup_now)
        instant_box.addLayout(self._button_row(backup_now_btn)); layout.addWidget(instant_group)
        manage_group, manage_box = self._card(translate('settings_database_admin_title'), translate('settings_database_admin_help'))
        manage_layout = QHBoxLayout()
        self.export_btn = QPushButton(translate('settings_database_export')); self.export_btn.clicked.connect(self.export_database)
        self.import_btn = QPushButton(translate('settings_database_import')); self.import_btn.clicked.connect(self.import_database)
        self.reset_btn = QPushButton(translate('settings_database_reset')); self.reset_btn.setObjectName('danger'); self.reset_btn.clicked.connect(self.reset_database)
        manage_layout.addWidget(self.export_btn); manage_layout.addWidget(self.import_btn); manage_layout.addWidget(self.reset_btn)
        manage_box.addLayout(manage_layout); layout.addWidget(manage_group)
        layout.addStretch(); self.load_backup_settings(); return scroll


    def _refresh_language_texts(self):
        self.setLayoutDirection(qt_layout_direction(self._current_language))
        try:
            self.tabs.setTabText(0, '🎨 ' + translate('appearance'))
            self.tabs.setTabText(1, '🏢 ' + translate('company'))
            self.tabs.setTabText(2, '🖨️ ' + translate('printing_tab'))
            self.tabs.setTabText(3, '🧾 ' + translate('pos_tab'))
            self.tabs.setTabText(4, '💰 ' + translate('currencies'))
            self.tabs.setTabText(5, '💱 ' + translate('exchange_rates'))
            self.tabs.setTabText(6, '🌐 ' + translate('network'))
            self.tabs.setTabText(7, '💾 ' + translate('backup_data'))
        except Exception:
            pass

    def save_appearance_settings(self):
        theme = self.theme_combo.currentData() or 'light'
        lang = normalize_language(self.language_combo.currentData() if hasattr(self, 'language_combo') else self._current_language)
        settings_service.set_theme(theme)
        settings_service.set_language(lang)
        set_language(lang)
        self._current_language = lang
        self.setLayoutDirection(qt_layout_direction(lang))
        ThemeManager.apply_theme(theme, persist=True)
        self._refresh_language_texts()
        main_window = self.window()
        if hasattr(main_window, 'setLayoutDirection'):
            main_window.setLayoutDirection(qt_layout_direction(lang))
        if hasattr(main_window, 'setup_menus'):
            main_window.setup_menus()
        if hasattr(main_window, 'top_bar') and hasattr(main_window.top_bar, 'apply_styles'):
            try:
                main_window.top_bar.search_box.setPlaceholderText(translate('global_search_placeholder'))
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
            barcode_default_printer=self.barcode_default_printer.currentData() or 'pdf:default',
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
        info = {'name': self.company_name_edit.text().strip(), 'address': self.company_address_edit.text().strip(), 'phone': self.company_phone_edit.text().strip(), 'email': self.company_email_edit.text().strip(), 'tax_number': self.company_tax_number_edit.text().strip(), 'logo_path': self.company_logo_path_edit.text().strip() or default_logo}
        if not self.company_logo_path_edit.text().strip() and default_logo:
            self.company_logo_path_edit.setText(default_logo)
        
        audit_service.log('UPDATE', 'SETTINGS_COMPANY', None, new_values=info, details=translate('settings_company_audit_update'))
        save_company_info(info); show_toast(translate('settings_company_saved'), 'success', self)

    def browse_backup_folder(self):
        folder = QFileDialog.getExistingDirectory(self, translate('settings_backup_folder_placeholder'))
        if folder: self.backup_folder.setText(folder)

    def save_backup_settings(self):
        if backup_service.is_remote(): QMessageBox.warning(self, translate('warning'), translate('settings_backup_remote_save_blocked')); return
        settings = QSettings('Alrajhi', 'Accounting')
        old = {
            'backup/enabled': settings.value('backup/enabled', False, type=bool),
            'backup/interval_hours': settings.value('backup/interval_hours', 6, type=int),
            'backup/folder': settings.value('backup/folder', ''),
        }
        new = {
            'backup/enabled': self.backup_enabled.isChecked(),
            'backup/interval_hours': self.backup_interval.value(),
            'backup/folder': self.backup_folder.text(),
        }
        settings.setValue('backup/enabled', new['backup/enabled']); settings.setValue('backup/interval_hours', new['backup/interval_hours']); settings.setValue('backup/folder', new['backup/folder'])
        audit_service.log('UPDATE', 'SETTINGS_BACKUP', None, old_values=old, new_values=new, details=translate('settings_backup_audit_update'))
        show_toast(translate('settings_backup_saved'), 'success', self)

    def load_backup_settings(self):
        settings = QSettings('Alrajhi', 'Accounting')
        self.backup_enabled.setChecked(settings.value('backup/enabled', False, type=bool)); self.backup_interval.setValue(settings.value('backup/interval_hours', 6, type=int)); self.backup_folder.setText(settings.value('backup/folder', ''))

    def create_backup_now(self):
        if backup_service.is_remote(): QMessageBox.warning(self, translate('warning'), translate('settings_backup_remote_create_blocked')); return
        folder = self.backup_folder.text().strip()
        if not folder: QMessageBox.warning(self, translate('error'), translate('settings_backup_folder_required')); return
        try:
            result = backup_service.create_backup(folder); sep = chr(10)
            QMessageBox.information(self, translate('success'), translate('settings_backup_created_integrity', sep=sep, path=result['backup_path'], sha256=result['sha256']))
        except Exception as e: QMessageBox.critical(self, translate('error'), translate('settings_backup_failed', error=str(e)))

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
