# -*- coding: utf-8 -*-
"""Unified paid-feature activation dialog.

Phase 397: manufacturing, restaurant, cafe and apparel use the same guarded
activation flow as the network feature.  The dialog is deliberately small and
runtime-safe so it can be called from menu navigation without constructing the
full SettingsWidget.
"""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from auth.activation import activate_feature, check_feature_activation, normalize_feature_activation_id
from i18n.translator import qt_layout_direction, translate
from core.services.settings_service import settings_service
from theme_manager import ThemeManager
from ui.dialog_branding import apply_branded_dialog, brand_message_box


FEATURE_TITLE_KEYS = {
    'network': 'feature_activation_network',
    'manufacturing': 'feature_activation_manufacturing',
    'restaurant': 'feature_activation_restaurant',
    'cafe': 'feature_activation_cafe',
    'apparel': 'feature_activation_apparel',
}


class ModuleActivationDialog(QDialog):
    """Prompt for one optional feature license and store it encrypted."""

    def __init__(self, feature: str, title: str | None = None, reason: str | None = None, parent=None):
        super().__init__(parent)
        self.feature = normalize_feature_activation_id(feature)
        self.feature_label = title or translate(FEATURE_TITLE_KEYS.get(self.feature, 'module_activation_feature'))
        self.reason = reason or ''
        self.setWindowTitle(translate('module_activation_title', module=self.feature_label))
        self.setLayoutDirection(qt_layout_direction(settings_service.get_language()))
        self.setProperty('basitDialogSurface', True)
        self.setProperty('dialogKind', 'module_activation')
        self.resize(500, 250)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.help_label = QLabel(
            translate('module_activation_help', module=self.feature_label)
            + (f"\n\n{self.reason}" if self.reason else '')
        )
        self.help_label.setWordWrap(True)
        self.help_label.setAlignment(Qt.AlignVCenter)
        self.help_label.setObjectName('BasitDialogHelp')
        self.help_label.setProperty('dialogLabelRole', 'subtitle')
        layout.addWidget(self.help_label)

        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText(translate('module_activation_key'))
        self.key_edit.setEchoMode(QLineEdit.Password)
        self.key_edit.returnPressed.connect(self._activate)
        layout.addWidget(self.key_edit)

        self.show_key = QCheckBox(translate('module_activation_show_key'))
        self.show_key.toggled.connect(lambda checked: self.key_edit.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password))
        layout.addWidget(self.show_key)

        self.status_label = QLabel('')
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(f"color: {ThemeManager.get('danger')};")
        layout.addWidget(self.status_label)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.activate_button = self.button_box.button(QDialogButtonBox.Ok)
        if isinstance(self.activate_button, QPushButton):
            self.activate_button.setText(translate('module_activation_activate'))
            self.activate_button.setObjectName('primary')
            self.activate_button.setProperty('dialogActionRole', 'primary')
        cancel_button = self.button_box.button(QDialogButtonBox.Cancel)
        if isinstance(cancel_button, QPushButton):
            cancel_button.setText(translate('cancel'))
            cancel_button.setProperty('dialogActionRole', 'close')
        self.button_box.accepted.connect(self._activate)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        apply_branded_dialog(self, self.windowTitle(), role='module_activation')

    def _set_status(self, text: str, color_key: str = 'danger') -> None:
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {ThemeManager.get(color_key)};")

    def _activate(self) -> None:
        key = self.key_edit.text().strip()
        if not key:
            self._set_status(translate('module_activation_required'))
            self.key_edit.setFocus()
            return
        if self.activate_button is not None:
            self.activate_button.setEnabled(False)
        self._set_status(translate('module_activation_checking'), 'info')
        success, message = activate_feature(self.feature, key)
        if self.activate_button is not None:
            self.activate_button.setEnabled(True)
        if success:
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Information)
            box.setWindowTitle(translate('success'))
            box.setText(translate('module_activation_success', module=self.feature_label))
            brand_message_box(box, 'info')
            box.exec_()
            self.accept()
        else:
            self._set_status(translate('module_activation_failed', message=message))

    @classmethod
    def ensure_feature(cls, parent, feature: str, title: str | None = None, reason: str | None = None) -> bool:
        feature_id = normalize_feature_activation_id(feature)
        ok, message = check_feature_activation(feature_id)
        if ok:
            return True
        dialog = cls(feature_id, title=title, reason=reason or message, parent=parent)
        return dialog.exec() == QDialog.Accepted
