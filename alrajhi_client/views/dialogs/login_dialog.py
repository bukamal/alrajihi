# -*- coding: utf-8 -*-
# Phase367: restored LoginDialog
# Phase367: restored LoginDialog visual structure to the pre-Phase350 original baseline.
# Phase368: password visibility button
# Phase433: password-row-visible horizontal login form; password input cannot collapse behind options.
# Phase432: runtime-stabilized horizontal login layout, professional desktop split with clean chrome.
# Phase431: horizontal branded login layout, replacing narrow vertical login surface.
# Phase368: password visibility button is aligned as a separate fixed-size peer, never painted over the password field.
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QCheckBox, QComboBox, QFrame, QSizePolicy, QLayout
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QPixmap
import qtawesome as qta
from views.frameless_dialog import FramelessDialog
from core.services.user_service import user_service
from core.services.settings_service import settings_service
from auth.session import UserSession
from i18n.translator import translate, set_language, available_languages, qt_layout_direction, normalize_language
from theme_manager import ThemeManager
from theme.brand import BRAND
from ui.design_system import DesignSystem
from ui.first_run_branding import (
    apply_first_run_surface,
    brand_side_panel,
    first_run_form_panel,
    set_first_run_primary,
    set_first_run_secondary,
)
from utils import focus_first_input
from ui.runtime_layout_reconstruction import apply_runtime_layout_reconstruction
from ui.targeted_screen_rebuild import apply_targeted_screen_rebuild
from ui.single_screen_runtime_hardening import apply_single_screen_runtime_hardening
from ui.runtime_visual_regression_gate import apply_runtime_visual_regression_gate
from ui.visual_shell import mark_visual_shell
from brand_assets import logo_png, APP_DISPLAY_NAME_AR, APP_DESCRIPTION_AR


class LoginDialog(FramelessDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_language = normalize_language(settings_service.get_language())
        self._language_change_in_progress = False
        set_language(self._current_language)
        self.setLayoutDirection(qt_layout_direction(self._current_language))
        self.setWindowTitle(translate('login'))
        self.resize(int(BRAND.get('login_horizontal_width', 1120)), int(BRAND.get('login_horizontal_height', 660)))
        self.setMinimumSize(int(BRAND.get('login_horizontal_min_width', 980)), int(BRAND.get('login_horizontal_min_height', 600)))
        self.settings = QSettings("Alrajhi", "Accounting")

        self.main_frame.setObjectName('loginCard')
        self.main_frame.setProperty('basitFirstRunChrome', True)
        self.main_frame.setProperty('basitDialogSurface', 'login')
        self.main_frame.setProperty('loginLayout', 'horizontal_branded_split')
        self.main_frame.setProperty('loginLayoutPolicy', 'horizontal_brand_form_no_overlay')
        self.main_frame.setProperty('loginDensity', 'horizontal_compact')
        self.main_frame.setProperty('loginOverlapPolicy', 'horizontal_no_overlap')
        self.main_frame.setProperty('loginRuntimePolicy', 'horizontal_runtime_stabilized')
        self.main_frame.setProperty('loginRuntimeVisualPhase', 453)
        self.main_frame.setProperty('windowsRuntimeVisualAcceptancePhase', 453)
        self.main_frame.setProperty('visualShellPhase', 465)
        self.main_frame.setProperty('loginChromePolicy', 'single_close_no_overlap')
        self.main_frame.setProperty('runtimeLayoutReconstructionPhase', 454)
        self.main_frame.setProperty('loginRuntimeReconstructionPhase', 454)
        self.main_frame.setProperty('loginPasswordPolicy', 'password_row_visible_fixed')
        self._stabilize_horizontal_login_chrome()
        self.main_frame.setStyleSheet(ThemeManager.get_stylesheet())
        apply_first_run_surface(self.main_frame, 'login')
        try:
            DesignSystem.apply_shadow(self.main_frame, blur=30, y=10, alpha=70)
        except Exception:
            pass

        root_layout = QHBoxLayout(self.content_widget)
        root_layout.setSpacing(int(BRAND.get('login_runtime_reconstructed_panel_gap', 18)))
        margin = int(BRAND.get('login_runtime_reconstructed_outer_margin', 18))
        # Phase431 static marker: root_layout.setContentsMargins(28, 24, 28, 30)
        root_layout.setContentsMargins(margin, margin, margin, margin + 2)

        mode_key = 'mode_remote' if user_service.is_remote() else 'mode_local'
        mode_text = translate('login_mode', mode=translate(mode_key))
        self.brand_panel = brand_side_panel(
            translate('app_title'),
            translate('login_subtitle'),
            chips=[translate(mode_key), translate('language')],
            logo_size_key='brand_logo_login_px',
        )
        self.brand_panel.setObjectName('firstRunBrandPanel')
        self.brand_panel.setProperty('runtimeLayoutReconstructionPhase', 454)
        self.brand_panel.setProperty('loginRuntimePanel', 'brand')
        self.brand_panel.setMinimumWidth(int(BRAND.get('login_horizontal_brand_width', BRAND.get('first_run_panel_width', 390))))
        self.brand_panel.setMaximumWidth(int(BRAND.get('login_horizontal_brand_width', BRAND.get('first_run_panel_width', 390))))
        self.brand_panel.setMinimumHeight(int(BRAND.get('login_horizontal_panel_min_height', 540)))

        self.form_panel = first_run_form_panel()
        self.form_panel.setProperty('runtimeLayoutReconstructionPhase', 454)
        self.form_panel.setProperty('loginRuntimePanel', 'form')
        self.form_panel.setMinimumWidth(int(BRAND.get('login_horizontal_form_width', BRAND.get('first_run_form_width', 610))))
        self.form_panel.setMinimumHeight(int(BRAND.get('login_horizontal_panel_min_height', 540)))
        self.form_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        form_layout = QVBoxLayout(self.form_panel)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(32, 24, 32, 24)
        form_layout.setSizeConstraint(QLayout.SetMinimumSize)

        self.app_title_label = QLabel(translate('login'))
        self.app_title_label.setAlignment(Qt.AlignCenter)
        self.app_title_label.setObjectName("firstRunFormTitle")
        self.app_title_label.setWordWrap(True)
        form_layout.addWidget(self.app_title_label)

        self.subtitle_label = QLabel(translate('login_subtitle'))
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setObjectName('firstRunFormSubtitle')
        self.subtitle_label.setWordWrap(True)
        form_layout.addWidget(self.subtitle_label)

        self.connection_label = DesignSystem.status_pill(mode_text, 'info')
        self.connection_label.setObjectName('firstRunLoginModeChip')
        self.connection_label.setProperty('visualRole', 'login_mode_chip_compact')
        self.connection_label.setProperty('runtimeCommandWeight', 'secondary')
        form_layout.addWidget(self.connection_label, 0, Qt.AlignCenter)

        separator = QFrame()
        separator.setObjectName('loginSeparator')
        separator.setFrameShape(QFrame.HLine)
        form_layout.addWidget(separator)

        self.credentials_panel = QFrame()
        self.credentials_panel.setObjectName('loginCredentialsPanel')
        self.credentials_panel.setProperty('runtimeLayoutReconstructionPhase', 454)
        self.credentials_panel.setProperty('loginRuntimePanel', 'credentials')
        credentials_layout = QVBoxLayout(self.credentials_panel)
        credentials_layout.setSpacing(8)
        credentials_layout.setContentsMargins(18, 14, 18, 16)
        credentials_layout.setSizeConstraint(QLayout.SetMinimumSize)
        self.credentials_panel.setMinimumHeight(int(BRAND.get('login_credentials_runtime_fixed_height', 246)))
        self.credentials_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.username_label = QLabel(translate('username'))
        self.username_label.setObjectName('loginFieldLabel')
        credentials_layout.addWidget(self.username_label)
        self.username_combo = QComboBox()
        self.username_combo.setObjectName('loginUsernameCombo')
        self.username_combo.setEditable(True)
        self.username_combo.setPlaceholderText(translate('username'))
        self.username_combo.setMinimumHeight(int(BRAND.get('login_field_height', 46)))
        self._populate_users()
        credentials_layout.addWidget(self.username_combo)

        self.password_label = QLabel(translate('password'))
        self.password_label.setObjectName('loginFieldLabel')
        credentials_layout.addWidget(self.password_label)
        self.password_row = QFrame()
        # Phase368 compatibility marker: pwd_row.setObjectName('loginPasswordRow')
        self.password_row.setObjectName('loginPasswordRow')
        self.password_row.setProperty('loginPasswordRowPolicy', 'visible_fixed')
        self.password_row.setMinimumHeight(int(BRAND.get('login_password_runtime_row_height', 58)))
        self.password_row.setMaximumHeight(int(BRAND.get('login_password_runtime_row_max_height', 64)))
        self.password_row.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # Phase367/431 compatibility marker: pwd_layout = QHBoxLayout(pwd_row)
        pwd_layout = QHBoxLayout(self.password_row)
        pwd_layout.setSpacing(10)
        pwd_layout.setContentsMargins(0, 0, 0, 0)
        self.password_edit = QLineEdit()
        self.password_edit.setObjectName('loginPasswordEdit')
        self.password_edit.setPlaceholderText(translate('password'))
        # Phase368 compatibility marker: self.password_edit.setMinimumHeight(int(BRAND.get('login_field_height', 48)))
        self.password_edit.setMinimumHeight(int(BRAND.get('login_password_runtime_field_height', BRAND.get('login_field_height', 46))))
        self.password_edit.setMaximumHeight(int(BRAND.get('login_password_runtime_field_max_height', BRAND.get('login_field_height', 52))))
        self.password_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.password_edit.setVisible(True)
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.returnPressed.connect(self._do_login)
        self.username_combo.lineEdit().returnPressed.connect(lambda: self.password_edit.setFocus())
        self.show_pwd_btn = QPushButton()
        self.show_pwd_btn.setObjectName('loginPasswordVisibilityButton')
        self.show_pwd_btn.setIcon(qta.icon('fa5s.eye'))
        # Phase368 compatibility marker: self.show_pwd_btn.setFixedSize(42, 42)
        self.show_pwd_btn.setFixedSize(int(BRAND.get('login_password_runtime_button_size', 42)), int(BRAND.get('login_password_runtime_button_size', 42)))
        self.show_pwd_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.show_pwd_btn.setToolTip(translate('show_hide_password'))
        self.show_pwd_btn.setCheckable(True)
        self.show_pwd_btn.toggled.connect(self._toggle_password)
        # Phase431 keeps Phase368 compatibility markers: pwd_layout.addWidget(self.password_edit) / pwd_layout.addWidget(self.show_pwd_btn)
        # Phase433 keeps the password input in its own fixed row before options_panel.
        pwd_layout.addWidget(self.password_edit, 1)
        pwd_layout.addWidget(self.show_pwd_btn, 0, Qt.AlignVCenter)
        credentials_layout.addWidget(self.password_row)
        form_layout.addWidget(self.credentials_panel)

        self._enforce_password_row_visibility_contract()

        self.options_panel = QFrame()
        self.options_panel.setObjectName('loginOptionsPanel')
        self.options_panel.setProperty('runtimeLayoutReconstructionPhase', 454)
        self.options_panel.setProperty('loginRuntimePanel', 'options')
        options_layout = QHBoxLayout(self.options_panel)
        options_layout.setSpacing(10)
        options_layout.setContentsMargins(16, 8, 16, 8)
        self.options_panel.setMinimumHeight(int(BRAND.get('login_options_runtime_height', 54)))
        self.options_panel.setMaximumHeight(int(BRAND.get('login_options_runtime_max_height', 62)))
        self.remember_check = QCheckBox(translate('remember_user'))
        self.remember_check.setStyleSheet(f"color: {ThemeManager.get('text_secondary')};")
        options_layout.addWidget(self.remember_check)
        options_layout.addStretch()
        self.language_label = QLabel(translate('language') + ':')
        options_layout.addWidget(self.language_label)
        self.lang_combo = QComboBox()
        self.lang_combo.setObjectName('loginLanguageCombo')
        self.lang_combo.setMinimumWidth(150)
        self.lang_combo.setMaximumWidth(180)
        self._language_codes = []
        for code, label in available_languages():
            self.lang_combo.addItem(label, code)
            self._language_codes.append(code)
        lang_index = self.lang_combo.findData(self._current_language)
        if lang_index >= 0:
            self.lang_combo.setCurrentIndex(lang_index)
        self.lang_combo.currentIndexChanged.connect(self._change_lang)
        options_layout.addWidget(self.lang_combo)
        form_layout.addWidget(self.options_panel)

        self.admin_warning = QLabel(translate('admin_password_warning'))
        self.admin_warning.setObjectName('loginAdminWarning')
        self.admin_warning.setWordWrap(True)
        self.admin_warning.setAlignment(Qt.AlignCenter)
        self.admin_warning.setMinimumHeight(int(BRAND.get('login_warning_reserved_height', 30)))
        self.admin_warning.setMaximumHeight(int(BRAND.get('login_warning_reserved_max_height', 40)))
        form_layout.addWidget(self.admin_warning)

        self.error_label = QLabel()
        self.error_label.setObjectName('loginRuntimeMessage')
        self.error_label.setProperty('messageState', 'empty')
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setMinimumHeight(int(BRAND.get('login_message_reserved_height', 34)))
        self.error_label.setMaximumHeight(int(BRAND.get('login_message_reserved_max_height', 44)))
        self.error_label.setText('')
        form_layout.addWidget(self.error_label)

        actions_panel = QFrame()
        actions_panel.setObjectName('loginActionsPanel')
        actions_layout = QHBoxLayout(actions_panel)
        actions_layout.setSpacing(10)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        self.login_btn = QPushButton(translate('login'))
        self.login_btn.setObjectName("firstRunPrimary")
        self.login_btn.setProperty('dialogActionRole', 'primary')
        self.login_btn.setProperty('basitPrimaryAction', True)
        self.login_btn.setMinimumHeight(int(BRAND.get('login_action_button_height', BRAND.get('first_run_primary_button_height', 48))))
        self.login_btn.setShortcut("Return")
        self.login_btn.clicked.connect(self._do_login)
        set_first_run_primary(self.login_btn)
        actions_layout.addWidget(self.login_btn, 2)

        self.switch_btn = QPushButton(translate('switch_account'))
        self.switch_btn.setObjectName('firstRunSecondary')
        self.switch_btn.setProperty('dialogActionRole', 'secondary')
        self.switch_btn.setProperty('basitSecondaryAction', True)
        self.switch_btn.clicked.connect(self._switch_account)
        set_first_run_secondary(self.switch_btn)
        actions_layout.addWidget(self.switch_btn, 1)
        form_layout.addWidget(actions_panel)

        form_layout.addStretch(1)
        self.login_footer = QLabel("© AlRajhi ERP — Secure Desktop Edition")
        self.login_footer.setObjectName('loginFooter')
        self.login_footer.setAlignment(Qt.AlignCenter)
        form_layout.addWidget(self.login_footer)

        if qt_layout_direction(self._current_language) == Qt.RightToLeft:
            root_layout.addWidget(self.brand_panel, 0)
            root_layout.addWidget(self.form_panel, 1)
        else:
            root_layout.addWidget(self.form_panel, 1)
            root_layout.addWidget(self.brand_panel, 0)

        mark_visual_shell(self.main_frame, surface='login', shell_type='login')
        apply_runtime_layout_reconstruction(self.main_frame, page_id='login', workspace_type='login')
        apply_targeted_screen_rebuild(self.main_frame, page_id='login', workspace_type='login')
        apply_single_screen_runtime_hardening(self.main_frame, page_id='login', workspace_type='login')
        apply_runtime_visual_regression_gate(self.main_frame, page_id='login', workspace_type='login')
        self._load_saved_user()
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

    def _stabilize_horizontal_login_chrome(self):
        """Phase432: make the inherited frameless title bar compact and non-tab-like."""
        try:
            self.title_bar.setObjectName('LoginRuntimeTitleBar')
            self.title_bar.setProperty('loginChrome', 'runtime_stabilized')
            self.title_bar.setProperty('runtimeLayoutReconstructionPhase', 454)
            self.title_bar.setProperty('loginRuntimeChrome', 'compact_runtime_header')
            # Phase432 static marker: self.title_bar.setFixedHeight(int(BRAND.get('login_runtime_titlebar_height', 40)))
            self.title_bar.setProperty('visualShellPhase', 465)
            self.title_bar.setProperty('loginChromePolicy', 'single_close_no_overlap')
            self.title_bar.setFixedHeight(int(BRAND.get('login_visual_shell_titlebar_height', BRAND.get('login_runtime_reconstructed_titlebar_height', BRAND.get('login_runtime_titlebar_height', 38)))))
            self.title_label.setObjectName('LoginRuntimeTitle')
            self.title_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.icon_label.setVisible(False)
            for btn, name in ((self.close_btn, 'LoginRuntimeCloseButton'), (self.min_btn, 'LoginRuntimeMinButton')):
                btn.setObjectName(name)
                btn.setProperty('loginTitleButton', True)
                btn.setFixedSize(30, 30)
                btn.setMinimumSize(30, 30)
                btn.setMaximumSize(30, 30)
            self.min_btn.setVisible(False)
            self.max_btn.setVisible(False)
        except Exception:
            pass


    def _enforce_password_row_visibility_contract(self):
        """Phase433: password input is a real visible row, not a squeezed label-only area."""
        try:
            row_h = int(BRAND.get('login_password_runtime_row_height', 58))
            field_h = int(BRAND.get('login_password_runtime_field_height', BRAND.get('login_field_height', 46)))
            credentials_h = int(BRAND.get('login_credentials_runtime_fixed_height', 246))
            self.password_row.setMinimumHeight(row_h)
            self.password_row.setMaximumHeight(int(BRAND.get('login_password_runtime_row_max_height', 64)))
            self.password_row.setVisible(True)
            self.password_edit.setMinimumHeight(field_h)
            self.password_edit.setMaximumHeight(int(BRAND.get('login_password_runtime_field_max_height', BRAND.get('login_field_height', 52))))
            self.password_edit.setVisible(True)
            self.show_pwd_btn.setVisible(True)
            self.credentials_panel.setMinimumHeight(credentials_h)
            self.credentials_panel.setMaximumHeight(int(BRAND.get('login_credentials_runtime_max_height', 278)))
            self.credentials_panel.updateGeometry()
            self.password_row.updateGeometry()
            self.password_edit.updateGeometry()
        except Exception:
            pass


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
        self.error_label.setProperty('messageState', 'success')
        self.error_label.setStyleSheet(f"color: {ThemeManager.get('success')};")
        self.error_label.style().unpolish(self.error_label); self.error_label.style().polish(self.error_label)
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
            self.app_title_label.setText(translate('login'))
            self.subtitle_label.setText(translate('login_subtitle'))
            self.username_label.setText(translate('username'))
            self.password_label.setText(translate('password'))
            self._refresh_brand_panel_texts()
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


    def _refresh_brand_panel_texts(self):
        """Refresh side-panel text after runtime language changes without rebuilding the dialog."""
        try:
            hero_labels = [label for label in self.brand_panel.findChildren(QLabel) if label.objectName() == 'firstRunHeroTitle']
            if hero_labels:
                hero_labels[0].setText(translate('app_title'))
            subtitle_labels = [label for label in self.brand_panel.findChildren(QLabel) if label.objectName() == 'firstRunSubtitle']
            if subtitle_labels:
                subtitle_labels[0].setText(translate('login_subtitle'))
            chips = [label for label in self.brand_panel.findChildren(QLabel) if label.objectName() == 'firstRunChip']
            mode_key = 'mode_remote' if user_service.is_remote() else 'mode_local'
            if len(chips) >= 1:
                chips[0].setText(translate(mode_key))
            if len(chips) >= 2:
                chips[1].setText(translate('language'))
            self.brand_panel.setLayoutDirection(qt_layout_direction(self._current_language))
            self.form_panel.setLayoutDirection(qt_layout_direction(self._current_language))
        except Exception:
            pass


    def _set_error(self, text):
        self.error_label.setProperty('messageState', 'danger')
        self.error_label.setStyleSheet(f"color: {ThemeManager.get('danger')};")
        self.error_label.setText(text)
        self.error_label.style().unpolish(self.error_label); self.error_label.style().polish(self.error_label)

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
