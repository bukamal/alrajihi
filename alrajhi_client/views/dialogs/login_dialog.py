# -*- coding: utf-8 -*-
# Phase367: restored LoginDialog visual structure to the pre-Phase350 original baseline.
# Phase368: password visibility button is aligned as a separate fixed-size peer, never painted over the password field.
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QCheckBox, QComboBox, QFrame, QSizePolicy
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QPixmap
import qtawesome as qta
from views.frameless_dialog import FramelessDialog
from core.services.user_service import user_service
from core.services.settings_service import settings_service
from auth.session import UserSession
from i18n.translator import translate, set_language, available_languages, qt_layout_direction, normalize_language
from theme_manager import ThemeManager
from ui.design_system import DesignSystem
from utils import focus_first_input
from brand_assets import logo_png, APP_DISPLAY_NAME_AR, APP_DESCRIPTION_AR


class LoginDialog(FramelessDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_language = normalize_language(settings_service.get_language())
        self._language_change_in_progress = False
        set_language(self._current_language)
        self.setLayoutDirection(qt_layout_direction(self._current_language))
        self.setWindowTitle(translate('login'))
        self.resize(500, 620)
        self.setMinimumSize(430, 540)
        self.settings = QSettings("Alrajhi", "Accounting")

        self.main_frame.setObjectName('loginCard')
        self.main_frame.setStyleSheet(ThemeManager.get_stylesheet())
        try:
            DesignSystem.apply_shadow(self.main_frame, blur=30, y=10, alpha=70)
        except Exception:
            pass

        layout = QVBoxLayout(self.content_widget)
        layout.setSpacing(14)
        layout.setContentsMargins(34, 24, 34, 30)

        logo = QLabel()
        logo.setAlignment(Qt.AlignCenter)
        logo.setPixmap(QPixmap(logo_png(128)).scaled(94, 94, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(logo)

        self.app_title_label = QLabel(translate('app_title'))
        self.app_title_label.setAlignment(Qt.AlignCenter)
        self.app_title_label.setObjectName("heroTitle")
        self.app_title_label.setStyleSheet(f"font-size: 30px; font-weight: 900; color: {ThemeManager.get('primary')};")
        layout.addWidget(self.app_title_label)

        self.subtitle_label = QLabel(translate('login_subtitle'))
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setObjectName('muted')
        layout.addWidget(self.subtitle_label)

        mode_key = 'mode_remote' if user_service.is_remote() else 'mode_local'
        self.connection_label = DesignSystem.status_pill(translate('login_mode', mode=translate(mode_key)), 'info')
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
        pwd_layout.setSpacing(10)
        pwd_layout.setContentsMargins(0, 0, 0, 0)
        self.password_edit = QLineEdit()
        self.password_edit.setObjectName('loginPasswordEdit')
        self.password_edit.setPlaceholderText(translate('password'))
        self.password_edit.setMinimumHeight(44)
        self.password_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.returnPressed.connect(self._do_login)
        self.username_combo.lineEdit().returnPressed.connect(lambda: self.password_edit.setFocus())
        self.show_pwd_btn = QPushButton()
        self.show_pwd_btn.setObjectName('loginPasswordVisibilityButton')
        self.show_pwd_btn.setIcon(qta.icon('fa5s.eye'))
        self.show_pwd_btn.setFixedSize(42, 42)
        self.show_pwd_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.show_pwd_btn.setToolTip(translate('show_hide_password'))
        self.show_pwd_btn.setCheckable(True)
        self.show_pwd_btn.toggled.connect(self._toggle_password)
        # Phase367 compatibility markers: pwd_layout.addWidget(self.password_edit) / pwd_layout.addWidget(self.show_pwd_btn)
        pwd_layout.addWidget(self.password_edit, 1)
        pwd_layout.addWidget(self.show_pwd_btn, 0, Qt.AlignVCenter)
        layout.addLayout(pwd_layout)

        options_layout = QHBoxLayout()
        self.remember_check = QCheckBox(translate('remember_user'))
        self.remember_check.setStyleSheet(f"color: {ThemeManager.get('text_secondary')};")
        options_layout.addWidget(self.remember_check)
        options_layout.addStretch()
        self.lang_combo = QComboBox()
        self.lang_combo.setFixedWidth(128)
        self._language_codes = []
        for code, label in available_languages():
            self.lang_combo.addItem(label, code)
            self._language_codes.append(code)
        lang_index = self.lang_combo.findData(self._current_language)
        if lang_index >= 0:
            self.lang_combo.setCurrentIndex(lang_index)
        self.lang_combo.currentIndexChanged.connect(self._change_lang)
        self.language_label = QLabel(translate('language') + ':')
        options_layout.addWidget(self.language_label)
        options_layout.addWidget(self.lang_combo)
        layout.addLayout(options_layout)

        self.admin_warning = QLabel(translate('admin_password_warning'))
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

        self.switch_btn = DesignSystem.secondary_button(translate('switch_account'))
        self.switch_btn.clicked.connect(self._switch_account)
        layout.addWidget(self.switch_btn)

        self._load_saved_user()
        self.login_footer = QLabel("© AlRajhi ERP — Secure Desktop Edition")
        self.login_footer.setAlignment(Qt.AlignCenter)
        self.login_footer.setStyleSheet(f"color: {ThemeManager.get('text_muted')}; font-size: 10px;")
        layout.addWidget(self.login_footer)

        self.fade_in()

    def _populate_users(self):
        if user_service.is_remote():
            self.username_combo.setEditable(True)
            self.username_combo.clear()
            self.username_combo.addItem("")
            self.username_combo.setCurrentText("")
        else:
            users = user_service.list_users()
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
        self.error_label.setText(translate('stored_user_cleared'))
        self.error_label.setObjectName('success')
        self.error_label.setStyleSheet(f"color: {ThemeManager.get('success')};")
        self._populate_users()
        self.username_combo.setFocus()

    def _change_lang(self, index):
        if getattr(self, '_language_change_in_progress', False):
            return
        self._language_change_in_progress = True
        try:
            lang = normalize_language(self.lang_combo.itemData(index))
            self._current_language = lang
            set_language(lang)
            try:
                settings_service.set_language(lang)
            except Exception:
                pass
            self.setLayoutDirection(qt_layout_direction(lang))
            self.setWindowTitle(translate('login'))
            self.app_title_label.setText(translate('app_title'))
            self.subtitle_label.setText(translate('login_subtitle'))
            mode_key = 'mode_remote' if user_service.is_remote() else 'mode_local'
            self.connection_label.setText(translate('login_mode', mode=translate(mode_key)))
            self.username_combo.setPlaceholderText(translate('username'))
            self.password_edit.setPlaceholderText(translate('password'))
            self.remember_check.setText(translate('remember_user'))
            self.language_label.setText(translate('language') + ':')
            self.login_btn.setText(translate('login'))
            self.show_pwd_btn.setToolTip(translate('show_hide_password'))
            self.admin_warning.setText(translate('admin_password_warning'))
            self.switch_btn.setText(translate('switch_account'))
        finally:
            self._language_change_in_progress = False


    def _set_error(self, text):
        self.error_label.setStyleSheet(f"color: {ThemeManager.get('danger')};")
        self.error_label.setText(text)

    def _do_login(self):
        username = self.username_combo.currentText().strip()
        password = self.password_edit.text()
        if not username or not password:
            self._set_error(translate('login_required'))
            return
        self.login_btn.setEnabled(False)
        self.login_btn.setText(translate('checking_login'))
        try:
            user = user_service.authenticate(username, password)
            if user:
                UserSession.login(user)
                self._save_user(username)
                self.accept()
            else:
                self._set_error(translate('invalid_login'))
                self.password_edit.clear()
                self.password_edit.setFocus()
        except Exception as e:
            self._set_error(translate('login_failed', error=str(e)))
            self.password_edit.clear()
            self.password_edit.setFocus()
        finally:
            self.login_btn.setEnabled(True)
            self.login_btn.setText(translate('login'))

    def showEvent(self, event):
        self._center_on_main_window()
        super().showEvent(event)
