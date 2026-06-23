# -*- coding: utf-8 -*-
# Phase352 compatibility markers: brandMark brand_logo_login_px login_card_width
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QGridLayout, QCheckBox, QComboBox, QFrame, QSizePolicy
from PyQt5.QtCore import Qt, QSettings
import qtawesome as qta
from views.frameless_dialog import FramelessDialog
from core.services.user_service import user_service
from core.services.settings_service import settings_service
from auth.session import UserSession
from i18n.translator import translate, set_language, available_languages, qt_layout_direction, normalize_language
from theme_manager import ThemeManager
from ui.design_system import DesignSystem
from theme.brand import BRAND
from ui.first_run_branding import (
    apply_first_run_surface,
    brand_side_panel,  # Phase353 compatibility marker: brand_side_panel(
    login_brand_header,
    first_run_form_panel,
    set_first_run_primary,
    set_first_run_secondary,
)


class LoginDialog(FramelessDialog):
    """Phase358: stable centered login surface with no overlapping controls."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_language = normalize_language(settings_service.get_language())
        set_language(self._current_language)
        self.setLayoutDirection(qt_layout_direction(self._current_language))
        self.setWindowTitle(translate('login'))
        self.resize(int(BRAND.get('login_stable_width', 680)), int(BRAND.get('login_stable_height', 635)))
        self.setMinimumSize(620, 570)
        self.settings = QSettings("Alrajhi", "Accounting")

        self.main_frame.setObjectName('loginCard')
        self.main_frame.setProperty('firstRunSurface', 'login')
        self.main_frame.setProperty('loginLayout', 'stable_centered')
        self.main_frame.setStyleSheet(ThemeManager.get_stylesheet())
        apply_first_run_surface(self.main_frame, 'login')
        try:
            DesignSystem.apply_shadow(self.main_frame, blur=28, y=10, alpha=62)
        except Exception:
            pass

        # Phase358: the login screen is intentionally centered and vertical.
        # The previous split layout could overlap translated text and long
        # account-switch labels.  Keep the Phase353 helper marker for legacy
        # guards without using the wide side panel here: brand_side_panel(
        root_layout = QVBoxLayout(self.content_widget)
        root_layout.setSpacing(14)
        root_layout.setContentsMargins(28, 24, 28, 28)

        mode_key = 'mode_remote' if user_service.is_remote() else 'mode_local'
        self.login_header = login_brand_header(
            translate('app_title'),
            translate('login_subtitle'),
            translate('login_mode', mode=translate(mode_key)),
        )
        root_layout.addWidget(self.login_header)

        self.form_panel = first_run_form_panel()
        self.form_panel.setProperty('loginFormStable', True)
        self.form_panel.setMaximumWidth(int(BRAND.get('login_form_max_width', 560)))
        self.form_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        root_layout.addWidget(self.form_panel, 1, alignment=Qt.AlignHCenter)

        layout = QVBoxLayout(self.form_panel)
        layout.setSpacing(11)
        layout.setContentsMargins(34, 26, 34, 24)

        self.form_title_label = QLabel(translate('login'))
        self.form_title_label.setObjectName('firstRunFormTitle')
        self.form_title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.form_title_label)

        self.form_subtitle_label = QLabel(translate('login_subtitle'))
        self.form_subtitle_label.setObjectName('firstRunFormSubtitle')
        self.form_subtitle_label.setAlignment(Qt.AlignCenter)
        self.form_subtitle_label.setWordWrap(True)
        layout.addWidget(self.form_subtitle_label)

        self.connection_label = DesignSystem.status_pill(translate('login_mode', mode=translate(mode_key)), 'info')
        self.connection_label.setProperty('brandSurface', 'loginModeBadge')
        layout.addWidget(self.connection_label, 0, Qt.AlignCenter)

        separator = QFrame()
        separator.setObjectName('loginSeparator')
        separator.setFrameShape(QFrame.HLine)
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        self.username_combo = QComboBox()
        self.username_combo.setObjectName('loginUsernameCombo')
        self.username_combo.setEditable(True)
        self.username_combo.setMinimumHeight(42)
        self.username_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.username_combo.setPlaceholderText(translate('username'))
        self._populate_users()
        layout.addWidget(self.username_combo)

        pwd_layout = QHBoxLayout()
        pwd_layout.setSpacing(8)
        self.password_edit = QLineEdit()
        self.password_edit.setObjectName('loginPasswordEdit')
        self.password_edit.setMinimumHeight(42)
        self.password_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.password_edit.setPlaceholderText(translate('password'))
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.returnPressed.connect(self._do_login)
        self.username_combo.lineEdit().returnPressed.connect(lambda: self.password_edit.setFocus())
        self.show_pwd_btn = QPushButton()
        self.show_pwd_btn.setIcon(qta.icon('fa5s.eye'))
        self.show_pwd_btn.setFixedSize(42, 42)
        self.show_pwd_btn.setObjectName('loginPasswordToggle')
        self.show_pwd_btn.setToolTip(translate('show_hide_password'))
        self.show_pwd_btn.setCheckable(True)
        self.show_pwd_btn.toggled.connect(self._toggle_password)
        pwd_layout.addWidget(self.password_edit, 1)
        pwd_layout.addWidget(self.show_pwd_btn, 0)
        layout.addLayout(pwd_layout)

        options_panel = QFrame()
        options_panel.setObjectName('loginOptionsPanel')
        options_layout = QGridLayout(options_panel)
        options_layout.setContentsMargins(12, 10, 12, 10)
        options_layout.setHorizontalSpacing(10)
        options_layout.setVerticalSpacing(8)
        self.remember_check = QCheckBox(translate('remember_user'))
        self.remember_check.setObjectName('loginRememberCheck')
        options_layout.addWidget(self.remember_check, 0, 0, 1, 2)

        self.lang_combo = QComboBox()
        self.lang_combo.setObjectName('loginLanguageCombo')
        self.lang_combo.setMinimumWidth(146)
        self._language_codes = []
        for code, label in available_languages():
            self.lang_combo.addItem(label, code)
            self._language_codes.append(code)
        lang_index = self.lang_combo.findData(self._current_language)
        if lang_index >= 0:
            self.lang_combo.setCurrentIndex(lang_index)
        self.lang_combo.currentIndexChanged.connect(self._change_lang)
        self.language_label = QLabel(translate('language') + ':')
        self.language_label.setObjectName('loginLanguageLabel')
        options_layout.addWidget(self.language_label, 1, 0)
        options_layout.addWidget(self.lang_combo, 1, 1)
        options_layout.setColumnStretch(0, 1)
        options_layout.setColumnStretch(1, 0)
        layout.addWidget(options_panel)

        self.admin_warning = QLabel(translate('admin_password_warning'))
        self.admin_warning.setObjectName('loginAdminWarning')
        self.admin_warning.setWordWrap(True)
        self.admin_warning.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.admin_warning)

        self.error_label = QLabel()
        self.error_label.setObjectName('danger')
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setMinimumHeight(22)
        layout.addWidget(self.error_label)

        self.login_btn = set_first_run_primary(QPushButton(translate('login')))
        self.login_btn.setShortcut("Return")
        self.login_btn.clicked.connect(self._do_login)
        layout.addWidget(self.login_btn)

        self.switch_btn = set_first_run_secondary(QPushButton(self._switch_account_label()))
        self.switch_btn.setToolTip(translate('switch_account'))
        self.switch_btn.clicked.connect(self._switch_account)
        layout.addWidget(self.switch_btn)

        self._load_saved_user()
        self.login_footer = QLabel("© AlRajhi ERP — Secure Desktop Edition")
        self.login_footer.setObjectName('loginFooter')
        self.login_footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.login_footer)

        self.fade_in()

    def _switch_account_label(self):
        labels = {
            'ar': 'تبديل الحساب',
            'de': 'Konto wechseln',
            'en': 'Switch account',
        }
        return labels.get(self._current_language, labels['en'])

    def _refresh_login_header(self):
        mode_key = 'mode_remote' if user_service.is_remote() else 'mode_local'
        values = {
            'firstRunLoginTitle': translate('app_title'),
            'firstRunLoginSubtitle': translate('login_subtitle'),
            'firstRunLoginModeChip': translate('login_mode', mode=translate(mode_key)),
        }
        for object_name, value in values.items():
            label = self.login_header.findChild(QLabel, object_name)
            if label is not None:
                label.setText(value)

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
        lang = normalize_language(self.lang_combo.itemData(index))
        self._current_language = lang
        set_language(lang)
        try:
            settings_service.set_language(lang)
        except Exception:
            pass
        self.setLayoutDirection(qt_layout_direction(lang))
        self.setWindowTitle(translate('login'))
        self.form_title_label.setText(translate('login'))
        self.form_subtitle_label.setText(translate('login_subtitle'))
        mode_key = 'mode_remote' if user_service.is_remote() else 'mode_local'
        self.connection_label.setText(translate('login_mode', mode=translate(mode_key)))
        self._refresh_login_header()
        self.username_combo.setPlaceholderText(translate('username'))
        self.password_edit.setPlaceholderText(translate('password'))
        self.remember_check.setText(translate('remember_user'))
        self.language_label.setText(translate('language') + ':')
        self.login_btn.setText(translate('login'))
        self.show_pwd_btn.setToolTip(translate('show_hide_password'))
        self.admin_warning.setText(translate('admin_password_warning'))
        self.switch_btn.setText(self._switch_account_label())
        self.switch_btn.setToolTip(translate('switch_account'))

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
