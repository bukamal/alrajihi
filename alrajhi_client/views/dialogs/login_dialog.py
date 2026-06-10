# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QCheckBox, QComboBox, QFrame
from PyQt5.QtCore import Qt, QSettings
import qtawesome as qta
from views.frameless_dialog import FramelessDialog
from database import UserRepository
from database.connection import DatabaseConnection
from auth.session import UserSession
from i18n.translator import translate, set_language
from theme_manager import ThemeManager
from ui.design_system import DesignSystem


class LoginDialog(FramelessDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setWindowTitle(translate('login'))
        self.resize(500, 620)
        self.setMinimumSize(430, 540)
        self.settings = QSettings("Alrajhi", "Accounting")
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

        logo = QLabel("🏢 الراجحي للمحاسبة")
        logo.setAlignment(Qt.AlignCenter)
        logo.setObjectName("heroTitle")
        logo.setStyleSheet(f"font-size: 31px; font-weight: 800; color: {ThemeManager.get('primary')};")
        layout.addWidget(logo)

        subtitle = QLabel("تسجيل دخول آمن إلى النظام")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setObjectName('muted')
        layout.addWidget(subtitle)

        mode = "متصل بخادم" if self.db_conn.is_remote() else "محلي"
        self.connection_label = DesignSystem.status_pill(f"وضع التشغيل: {mode}", 'info')
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
        self.show_pwd_btn.setToolTip("إظهار/إخفاء كلمة المرور")
        self.show_pwd_btn.setCheckable(True)
        self.show_pwd_btn.toggled.connect(self._toggle_password)
        pwd_layout.addWidget(self.password_edit)
        pwd_layout.addWidget(self.show_pwd_btn)
        layout.addLayout(pwd_layout)

        options_layout = QHBoxLayout()
        self.remember_check = QCheckBox("تذكر المستخدم")
        self.remember_check.setStyleSheet(f"color: {ThemeManager.get('text_secondary')};")
        options_layout.addWidget(self.remember_check)
        options_layout.addStretch()
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["العربية", "English", "Français"])
        self.lang_combo.setFixedWidth(112)
        self.lang_combo.currentIndexChanged.connect(self._change_lang)
        options_layout.addWidget(QLabel("اللغة:"))
        options_layout.addWidget(self.lang_combo)
        layout.addLayout(options_layout)

        self.admin_warning = QLabel("⚠️ عند أول تشغيل: غيّر كلمة مرور admin الافتراضية فورًا.")
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

        switch_btn = DesignSystem.secondary_button("🔄 تبديل الحساب / مسح المستخدم المحفوظ")
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
        self.error_label.setText("تم مسح اسم المستخدم المخزن")
        self.error_label.setObjectName('success')
        self.error_label.setStyleSheet(f"color: {ThemeManager.get('success')};")
        self._populate_users()
        self.username_combo.setFocus()

    def _change_lang(self, index):
        lang_map = {0: 'ar', 1: 'en', 2: 'fr'}
        set_language(lang_map[index])
        self.setWindowTitle(translate('login'))
        self.username_combo.setPlaceholderText(translate('username'))
        self.password_edit.setPlaceholderText(translate('password'))
        self.remember_check.setText("تذكر المستخدم")
        self.login_btn.setText(translate('login'))

    def _set_error(self, text):
        self.error_label.setStyleSheet(f"color: {ThemeManager.get('danger')};")
        self.error_label.setText(text)

    def _do_login(self):
        username = self.username_combo.currentText().strip()
        password = self.password_edit.text()
        if not username or not password:
            self._set_error("يرجى إدخال اسم المستخدم وكلمة المرور")
            return
        self.login_btn.setEnabled(False)
        self.login_btn.setText("جاري التحقق...")
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
                self._set_error("اسم المستخدم أو كلمة المرور غير صحيحة")
                self.password_edit.clear()
                self.password_edit.setFocus()
        except Exception as e:
            self._set_error(f"فشل تسجيل الدخول: {str(e)}")
            self.password_edit.clear()
            self.password_edit.setFocus()
        finally:
            self.login_btn.setEnabled(True)
            self.login_btn.setText(translate('login'))

    def showEvent(self, event):
        self._center_on_main_window()
        super().showEvent(event)
