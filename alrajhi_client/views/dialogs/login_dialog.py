# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QCheckBox, QComboBox, QFrame
from PyQt5.QtCore import Qt, QSettings
import qtawesome as qta
from views.frameless_dialog import FramelessDialog
from database import UserRepository
from database.connection import DatabaseConnection
from auth.session import UserSession
from i18n.translator import translate, set_language, available_languages, direction
from theme_manager import ThemeManager
from ui.design_system import DesignSystem
from utils import focus_first_input


class LoginDialog(FramelessDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        saved_lang = self.settings.value('language', None) if hasattr(self, 'settings') else None
        self.setLayoutDirection(Qt.RightToLeft)
        self.setWindowTitle(translate('login'))
        self.resize(500, 620)
        self.setMinimumSize(430, 540)
        self.settings = QSettings("Alrajhi", "Accounting")
        saved_lang = self.settings.value("language", "ar")
        set_language(saved_lang)
        self.setLayoutDirection(Qt.RightToLeft if direction(saved_lang) == "rtl" else Qt.LeftToRight)
        self.setWindowTitle(translate("login"))
        self.user_repo = UserRepository()
        self.db_conn = DatabaseConnection()

        self.main_frame.setObjectName('loginCard')
        self.main_frame.setStyleSheet(ThemeManager.get_stylesheet())
        try:
            DesignSystem.apply_shadow(self.main_frame, blur=30, y=10, alpha=70)
        except Exception:
            pass

        layout = QVBoxLayout(self.content_widget)
        layout.setSpacing(14)
        layout.setContentsMargins(34, 24, 34, 30)

        logo = QLabel("🏢 " + translate("app_title"))
        logo.setAlignment(Qt.AlignCenter)
        logo.setObjectName("heroTitle")
        logo.setStyleSheet(f"font-size: 31px; font-weight: 800; color: {ThemeManager.get('primary')};")
        layout.addWidget(logo)

        subtitle = QLabel(translate("secure_login_subtitle"))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setObjectName('muted')
        layout.addWidget(subtitle)

        mode = translate("remote_mode") if self.db_conn.is_remote() else translate("local_mode")
        self.connection_label = DesignSystem.status_pill(f"{translate('connection_mode')}: {mode}", 'info')
        layout.addWidget(self.connection_label)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"background-color: {ThemeManager.get('border')}; max-height: 1px;")
        layout.addWidget(separator)

        self.username_combo = QComboBox()
        self.username_combo.setEditable(True)
        self.username_combo.setPlaceholderText(translate('username'))
        self._populate_users()
        layout.addWidget(self.username_combo)

        pwd_layout = QHBoxLayout()
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText(translate('password'))
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.returnPressed.connect(self._do_login)
        self.username_combo.lineEdit().returnPressed.connect(lambda: self.password_edit.setFocus())
        self.show_pwd_btn = QPushButton()
        self.show_pwd_btn.setIcon(qta.icon('fa5s.eye'))
        self.show_pwd_btn.setFixedSize(42, 42)
        self.show_pwd_btn.setToolTip(translate("show_hide_password"))
        self.show_pwd_btn.setCheckable(True)
        self.show_pwd_btn.toggled.connect(self._toggle_password)
        pwd_layout.addWidget(self.password_edit)
        pwd_layout.addWidget(self.show_pwd_btn)
        layout.addLayout(pwd_layout)

        options_layout = QHBoxLayout()
        self.remember_check = QCheckBox(translate("remember_user"))
        self.remember_check.setStyleSheet(f"color: {ThemeManager.get('text_secondary')};")
        options_layout.addWidget(self.remember_check)
        options_layout.addStretch()
        self.lang_combo = QComboBox()
        self._lang_codes = list(available_languages().keys())
        self.lang_combo.addItems([available_languages()[c] for c in self._lang_codes])
        idx = self._lang_codes.index(saved_lang) if saved_lang in self._lang_codes else 0
        self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.setFixedWidth(125)
        self.lang_combo.currentIndexChanged.connect(self._change_lang)
        options_layout.addWidget(QLabel(translate("language") + ":"))
        options_layout.addWidget(self.lang_combo)
        layout.addLayout(options_layout)

        self.admin_warning = QLabel("⚠️ " + translate("admin_default_warning"))
        self.admin_warning.setWordWrap(True)
        self.admin_warning.setAlignment(Qt.AlignCenter)
        self.admin_warning.setStyleSheet(f"color: {ThemeManager.get('warning')}; font-size: 12px;")
        layout.addWidget(self.admin_warning)

        self.error_label = QLabel()
        self.error_label.setObjectName('danger')
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)
        layout.addSpacing(4)

        self.login_btn = QPushButton(translate('login'))
        self.login_btn.setObjectName("primary")
        self.login_btn.setMinimumHeight(45)
        self.login_btn.setShortcut("Return")
        self.login_btn.clicked.connect(self._do_login)
        layout.addWidget(self.login_btn)

        switch_btn = DesignSystem.secondary_button("🔄 " + translate("switch_account"))
        switch_btn.clicked.connect(self._switch_account)
        layout.addWidget(switch_btn)

        self._load_saved_user()
        login_footer = QLabel("© Alrajhi Accounting — Secure Desktop Edition")
        login_footer.setAlignment(Qt.AlignCenter)
        login_footer.setStyleSheet(f"color: {ThemeManager.get('text_muted')}; font-size: 10px;")
        layout.addWidget(login_footer)

        self.fade_in()

    def _populate_users(self):
        if self.db_conn.is_remote():
            self.username_combo.setEditable(True)
            self.username_combo.clear()
            self.username_combo.addItem("")
            self.username_combo.setCurrentText("")
        else:
            users = self.user_repo.get_all()
            self.username_combo.clear()
            for u in users:
                if isinstance(u, dict):
                    self.username_combo.addItem(u.get('username', ''))
                else:
                    self.username_combo.addItem(getattr(u, 'username', ''))

    def _toggle_password(self, checked):
        self.password_edit.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        self.show_pwd_btn.setIcon(qta.icon('fa5s.eye-slash' if checked else 'fa5s.eye'))

    def _load_saved_user(self):
        saved = self.settings.value("login/username", "")
        if saved:
            self.username_combo.setEditText(saved)
            self.remember_check.setChecked(True)
            self.password_edit.setFocus()
        else:
            self.username_combo.setFocus()

    def _save_user(self, username):
        if self.remember_check.isChecked():
            self.settings.setValue("login/username", username)
        else:
            self.settings.remove("login/username")

    def _switch_account(self):
        self.settings.remove("login/username")
        self.username_combo.setEditText("")
        self.password_edit.clear()
        self.remember_check.setChecked(False)
        self.error_label.setText(translate("saved_user_cleared"))
        self.error_label.setObjectName('success')
        self.error_label.setStyleSheet(f"color: {ThemeManager.get('success')};")
        self._populate_users()
        self.username_combo.setFocus()

    def _change_lang(self, index):
        lang = self._lang_codes[index] if hasattr(self, '_lang_codes') and 0 <= index < len(self._lang_codes) else 'ar'
        set_language(lang)
        self.settings.setValue('language', lang)
        self.setLayoutDirection(Qt.RightToLeft if direction(lang) == 'rtl' else Qt.LeftToRight)
        self.setWindowTitle(translate('login'))
        self.username_combo.setPlaceholderText(translate('username'))
        self.password_edit.setPlaceholderText(translate('password'))
        self.remember_check.setText(translate('remember_user'))
        self.show_pwd_btn.setToolTip(translate('show_hide_password'))
        self.login_btn.setText(translate('login'))

    def _set_error(self, text):
        self.error_label.setStyleSheet(f"color: {ThemeManager.get('danger')};")
        self.error_label.setText(text)

    def _do_login(self):
        username = self.username_combo.currentText().strip()
        password = self.password_edit.text()
        if not username or not password:
            self._set_error(translate("missing_login_fields"))
            return
        self.login_btn.setEnabled(False)
        self.login_btn.setText(translate("verifying"))
        try:
            if self.db_conn.is_remote():
                rest_client = self.db_conn.get_rest_client()
                user = rest_client.login(username, password)
            else:
                user = self.user_repo.authenticate(username, password)
            if user:
                UserSession.login(user)
                self._save_user(username)
                self.accept()
            else:
                self._set_error(translate("invalid_login"))
                self.password_edit.clear()
                self.password_edit.setFocus()
        except Exception as e:
            self._set_error(f"{translate('login_failed')}: {str(e)}")
            self.password_edit.clear()
            self.password_edit.setFocus()
        finally:
            self.login_btn.setEnabled(True)
            self.login_btn.setText(translate('login'))

    def showEvent(self, event):
        self._center_on_main_window()
        super().showEvent(event)
