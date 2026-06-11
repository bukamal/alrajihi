# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QFormLayout, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout, QMessageBox, QLabel, QCheckBox
from PyQt5.QtCore import Qt
from views.frameless_dialog import FramelessDialog
from database import UserRepository
from auth.session import UserSession
from i18n.translator import translate
from theme_manager import ThemeManager
from views.widgets.modern_ui import apply_modern_dialog


class ChangePasswordDialog(FramelessDialog):
    def __init__(self, parent=None, user_id=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.user_id = user_id or (UserSession.get_current()['id'] if UserSession.get_current() else None)
        self.setWindowTitle(translate('change_password'))
        self.resize(470, 430)
        layout = QVBoxLayout(self.content_widget)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 22, 24, 24)

        title = QLabel("تغيير كلمة المرور")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {ThemeManager.get('primary')};")
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

        self.show_passwords = QCheckBox("إظهار كلمات المرور")
        self.show_passwords.toggled.connect(self._toggle_passwords)
        layout.addWidget(self.show_passwords)

        self.strength_label = QLabel("قوة كلمة المرور: —")
        self.strength_label.setAlignment(Qt.AlignCenter)
        self.strength_label.setStyleSheet(f"color: {ThemeManager.get('text_muted')};")
        layout.addWidget(self.strength_label)

        hint = QLabel("استخدم 8 أحرف على الأقل مع أرقام وحروف. تجنب admin123 وكلمات المرور الشائعة.")
        hint.setWordWrap(True)
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(f"color: {ThemeManager.get('text_muted')}; font-size: 12px;")
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
            0: ("ضعيفة جدًا", 'danger'),
            1: ("ضعيفة", 'danger'),
            2: ("متوسطة", 'warning'),
            3: ("جيدة", 'info'),
            4: ("قوية", 'success'),
        }
        label, color = labels.get(score, labels[0])
        self.strength_label.setText(f"قوة كلمة المرور: {label}")
        self.strength_label.setStyleSheet(f"color: {ThemeManager.get(color)};")

    def save(self):
        old = self.old_edit.text()
        new = self.new_edit.text()
        confirm = self.confirm_edit.text()
        if not old or not new or not confirm:
            QMessageBox.warning(self, translate('error'), "جميع الحقول مطلوبة")
            return
        if new != confirm:
            QMessageBox.warning(self, translate('error'), "كلمتا المرور غير متطابقتين")
            return
        if self._score_password(new) < 2:
            QMessageBox.warning(self, translate('error'), "كلمة المرور ضعيفة جدًا")
            return
        repo = UserRepository()
        if repo.change_password(self.user_id, old, new):
            QMessageBox.information(self, translate('success'), "تم تغيير كلمة المرور")
            self.accept()
        else:
            QMessageBox.warning(self, translate('error'), "كلمة المرور الحالية غير صحيحة")
