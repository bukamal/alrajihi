# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QFormLayout, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout, QMessageBox, QLabel, QCheckBox
from PyQt5.QtCore import Qt
from views.frameless_dialog import FramelessDialog
from core.services.user_service import user_service
from auth.session import UserSession
from i18n import translate, qt_layout_direction
from theme_manager import ThemeManager
from views.widgets.modern_ui import apply_modern_dialog
from ui.dialog_branding import apply_modal_visual_template
from ui.visual_state import set_visual_state


class ChangePasswordDialog(FramelessDialog):
    def __init__(self, parent=None, user_id=None):
        super().__init__(parent)
        self.setLayoutDirection(qt_layout_direction())
        self.user_id = user_id or (UserSession.get_current()['id'] if UserSession.get_current() else None)
        self.setWindowTitle(translate('change_password'))
        self.resize(470, 430)
        layout = QVBoxLayout(self.content_widget)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 22, 24, 24)

        title = QLabel(translate('change_password'))
        title.setAlignment(Qt.AlignCenter)
        title.setProperty('visualRole', 'modal_title')
        title.setProperty('modalLocalStylesSuppressed', True)
        layout.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        self.old_edit = QLineEdit()
        self.old_edit.setEchoMode(QLineEdit.Password)
        form.addRow(translate('old_password') + ":", self.old_edit)
        self.new_edit = QLineEdit()
        self.new_edit.setEchoMode(QLineEdit.Password)
        self.new_edit.textChanged.connect(self._update_strength)
        form.addRow(translate('new_password') + ":", self.new_edit)
        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.Password)
        self.confirm_edit.returnPressed.connect(self.save)
        form.addRow(translate('confirm_password') + ":", self.confirm_edit)
        layout.addLayout(form)

        self.show_passwords = QCheckBox(translate('show_passwords'))
        self.show_passwords.toggled.connect(self._toggle_passwords)
        layout.addWidget(self.show_passwords)

        self.strength_label = QLabel(translate('password_strength_empty'))
        self.strength_label.setAlignment(Qt.AlignCenter)
        set_visual_state(self.strength_label, 'muted', size='caption', role='modal_status')
        layout.addWidget(self.strength_label)

        hint = QLabel(translate('password_hint'))
        hint.setWordWrap(True)
        hint.setAlignment(Qt.AlignCenter)
        hint.setProperty('visualRole', 'modal_help')
        hint.setProperty('modalLocalStylesSuppressed', True)
        layout.addWidget(hint)

        btns = QHBoxLayout()
        btns.setDirection(QHBoxLayout.RightToLeft)
        save_btn = QPushButton(translate('save'))
        save_btn.setObjectName("primary")
        save_btn.setShortcut("Ctrl+S")
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton(translate('cancel'))
        cancel_btn.setShortcut("Esc")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)
        apply_modal_visual_template(self, role='change_password')
        self.fade_in()

    def _toggle_passwords(self, checked):
        mode = QLineEdit.Normal if checked else QLineEdit.Password
        self.old_edit.setEchoMode(mode)
        self.new_edit.setEchoMode(mode)
        self.confirm_edit.setEchoMode(mode)

    def _score_password(self, password):
        score = 0
        if len(password) >= 8:
            score += 1
        if any(ch.isdigit() for ch in password):
            score += 1
        if any(ch.isalpha() for ch in password):
            score += 1
        if any(not ch.isalnum() for ch in password):
            score += 1
        if password.lower() in {'admin123', 'password', '12345678', '123456'}:
            score = 0
        return score

    def _update_strength(self, text):
        score = self._score_password(text)
        labels = {
            0: (translate('password_strength_very_weak'), 'danger'),
            1: (translate('password_strength_weak'), 'danger'),
            2: (translate('password_strength_medium'), 'warning'),
            3: (translate('password_strength_good'), 'info'),
            4: (translate('password_strength_strong'), 'success'),
        }
        label, color = labels.get(score, labels[0])
        self.strength_label.setText(translate('password_strength_value', value=label))
        set_visual_state(self.strength_label, color, weight='strong', size='caption', role='modal_status')

    def save(self):
        old = self.old_edit.text()
        new = self.new_edit.text()
        confirm = self.confirm_edit.text()
        if not old or not new or not confirm:
            QMessageBox.warning(self, translate('error'), translate('all_fields_required'))
            return
        if new != confirm:
            QMessageBox.warning(self, translate('error'), translate('passwords_do_not_match'))
            return
        if self._score_password(new) < 2:
            QMessageBox.warning(self, translate('error'), translate('password_too_weak'))
            return
        if user_service.change_password(self.user_id, old, new):
            QMessageBox.information(self, translate('success'), translate('password_changed'))
            self.accept()
        else:
            QMessageBox.warning(self, translate('error'), translate('current_password_incorrect'))
