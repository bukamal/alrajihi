# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, Iterable, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QCheckBox, QComboBox, QFormLayout, QFrame, QLabel, QLineEdit, QPushButton, QSpinBox, QTextEdit, QVBoxLayout, QWidget

from core.services.settings_service import settings_service
from i18n import qt_layout_direction, translate
from utils import show_toast
from workspace.documents import BaseDocumentTab

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


class InventorySettingsTab(SettingsSectionDocumentTab):
    section_key = 'settings.inventory'
    fields = (
        ('inventory/default_warehouse_id', 'default_warehouse', 'string'),
        ('inventory/negative_stock_allowed', 'negative_stock_allowed', 'bool'),
        ('inventory/low_stock_alerts', 'low_stock_alerts', 'bool'),
        ('inventory/unit_conversion_strict', 'unit_conversion_strict', 'bool'),
    )


class RestaurantSettingsTab(SettingsSectionDocumentTab):
    section_key = 'settings.restaurant'
    fields = (
        ('restaurant/touch_mode', 'touch_mode', 'bool'),
        ('restaurant/service_charge_percent', 'service_charge_percent', 'string'),
        ('restaurant/default_tax_percent', 'default_tax_percent', 'string'),
        ('restaurant/consume_inventory_on', 'consume_inventory_on', 'choice:checkout|served'),
    )


class PrintingSettingsTab(SettingsSectionDocumentTab):
    section_key = 'settings.printing'
    fields = (
        ('printing/invoice_template', 'invoice_template', 'choice:a4|thermal'),
        ('printing/report_template', 'report_template', 'choice:a4|compact'),
        ('printing/show_logo', 'show_logo', 'bool'),
        ('printing/show_qr', 'show_qr', 'bool'),
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
    'inventory': InventorySettingsTab,
    'restaurant': RestaurantSettingsTab,
    'printing': PrintingSettingsTab,
    'ui': UISettingsTab,
    'security': SecuritySettingsTab,
}
