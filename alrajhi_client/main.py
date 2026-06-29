#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import subprocess
import time
import requests
import tempfile
import threading
import socket
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer, QSettings, Qt
from PyQt5.QtGui import QFont, QIcon
from core.services.warehouse_service import warehouse_service
from core.services.system_service import system_service
from core.services.user_service import user_service
from auth.activation import check_activation, start_license_checker, stop_license_checker, check_network_activation
from views.splash_screen import ModernSplashScreen
from views.dialogs.activation_dialog import ActivationDialog
from views.dialogs.login_dialog import LoginDialog
from views.main_window import MainWindow
from ui.post_login_transition_overlay import PostLoginTransitionOverlay
from ui.main_shell_runtime_fit import show_main_window_runtime_fitted
from ui.modal_visual_event_filter import install_modal_visual_event_filter
from ui.dialog_branding import apply_modal_visual_template
from ui.visual_state import set_visual_state
from workspace.runtime.startup_timeline_profiler import StartupTimelineProfiler
from auth.session import UserSession
from utils import enable_auto_select_all, install_non_blocking_message_boxes
from theme_manager import ThemeManager
from brand_assets import app_icon
from offline_read import install_offline_exception_hook
from i18n import translate


_backup_stop_event = None
_backup_thread = None

def on_license_invalid():
    def show():
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(translate('phase233_allui_012'))
        msg.setText(translate('phase233_allui_013'))
        msg.exec()
        sys.exit(1)
    QTimer.singleShot(0, show)

def run_flask_server():
    """Start the optional embedded server as a controlled child process.

    Kept as a compatibility wrapper for older calls, but it no longer launches
    recursively or without lifecycle control.
    """
    ok, msg = system_service.start_server_process(main_file=os.path.abspath(__file__), port=system_service.get_server_port())
    print(("✅ " if ok else "❌ ") + msg)
    return ok

def wait_for_server(url, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(f"{url}/health", timeout=1)
            if resp.status_code == 200 and resp.json().get('status') == 'alive':
                return True
        except:
            pass
        time.sleep(0.5)
    return False


def periodic_backup_worker(interval_seconds, folder, db_path=None):
    global _backup_stop_event
    from core.services.backup_service import backup_service
    while not _backup_stop_event.is_set():
        time.sleep(interval_seconds)
        try:
            backup_service.create_backup(folder, prefix='alrajhi_auto_backup')
        except Exception as e:
            print(f"⚠️ فشل النسخ الاحتياطي الدوري: {e}")


def start_periodic_backup():
    global _backup_stop_event, _backup_thread
    if system_service.is_remote():
        print("⚠️ النسخ الاحتياطي الدوري معطل في وضع العميل")
        return None

    settings = QSettings("Alrajhi", "Accounting")
    enabled = settings.value("backup/enabled", False, type=bool)
    if not enabled:
        return None
    interval_hours = settings.value("backup/interval_hours", 6, type=int)
    folder = settings.value("backup/folder", "")
    if not folder:
        return None
    if not os.path.exists(folder):
        try:
            os.makedirs(folder)
        except Exception:
            return None
    if _backup_stop_event is not None:
        _backup_stop_event.set()
        if _backup_thread and _backup_thread.is_alive():
            _backup_thread.join(timeout=1)
    _backup_stop_event = threading.Event()
    _backup_thread = threading.Thread(
        target=periodic_backup_worker,
        args=(interval_hours * 3600, folder, None),
        daemon=True
    )
    _backup_thread.start()
    return _backup_thread

def test_server_connection(url):
    try:
        ok, _message, _info = system_service.server_diagnostics(url, timeout=3, require_routes=True)
        return ok
    except Exception:
        return False

def open_network_settings():
    """Open a safe local-only network settings dialog.

    This function is called specifically when the client cannot reach the
    configured server. It must not instantiate the full SettingsWidget because
    that widget reads application settings through settings_service; in client
    mode this routes to REST and can crash with:
    "Request queued due to no connection: /api/settings/theme".
    """
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QDialogButtonBox,
        QComboBox, QLineEdit, QLabel, QPushButton, QMessageBox, QSpinBox, QCheckBox
    )

    dialog = QDialog()
    dialog.setWindowTitle(translate('phase233_allui_005'))
    dialog.setLayoutDirection(Qt.RightToLeft)
    dialog.resize(520, 260)

    qsettings = QSettings("Alrajhi", "Accounting")

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(18, 18, 18, 18)
    layout.setSpacing(12)

    note = QLabel(translate('network_settings_connection_note'))
    note.setWordWrap(True)
    note.setProperty('visualRole', 'modal_help')
    note.setProperty('modalTone', 'warning')
    note.setProperty('modalLocalStylesSuppressed', True)
    layout.addWidget(note)

    form = QFormLayout()
    form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

    mode_combo = QComboBox()
    mode_combo.addItem(translate('phase233_allui_007'), "local")
    mode_combo.addItem(translate('phase233_allui_008'), "client")
    mode_combo.addItem(translate('phase233_allui_009'), "server")
    current_mode = qsettings.value("network/mode", "local")
    idx = mode_combo.findData(current_mode)
    mode_combo.setCurrentIndex(idx if idx >= 0 else 0)
    form.addRow(translate('network_mode_label'), mode_combo)

    server_url_edit = QLineEdit(qsettings.value("network/server_url", "http://localhost:8000"))
    server_url_edit.setPlaceholderText("10.98.199.132 أو http://10.98.199.132:8000")
    form.addRow(translate('server_address_label'), server_url_edit)

    server_port_spin = QSpinBox()
    server_port_spin.setRange(1024, 65535)
    server_port_spin.setValue(int(qsettings.value("server/port", system_service.default_port())))
    form.addRow(translate('local_server_port_label'), server_port_spin)

    auto_start_check = QCheckBox(translate('phase233_allui_010'))
    auto_start_check.setChecked(qsettings.value("server/auto_start", False, type=bool))
    form.addRow(auto_start_check)

    status = QLabel("")
    status.setWordWrap(True)
    form.addRow(translate('status_label'), status)

    layout.addLayout(form)

    def test_current_server():
        raw = server_url_edit.text().strip()
        url = system_service.normalize_server_url(raw, server_port_spin.value())
        server_url_edit.setText(url)
        ok, message, info = system_service.server_diagnostics(url, timeout=4, require_routes=True)
        if ok:
            status.setText(f"✅ {message}\n{url}")
            set_visual_state(status, 'success', weight='strong', size='caption', role='modal_status')
        else:
            status.setText(translate('server_test_failed_used_address', message=message, url=url))
            set_visual_state(status, 'danger', weight='strong', size='caption', role='modal_status')

    test_btn = QPushButton(translate('phase233_allui_011'))
    test_btn.clicked.connect(test_current_server)
    btn_row = QHBoxLayout()
    btn_row.addStretch()
    btn_row.addWidget(test_btn)
    layout.addLayout(btn_row)

    button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

    def save_and_accept():
        port = server_port_spin.value()
        qsettings.setValue("network/mode", mode_combo.currentData() or "local")
        qsettings.setValue("network/server_url", system_service.normalize_server_url(server_url_edit.text().strip(), port))
        qsettings.setValue("server/port", port)
        qsettings.setValue("server/auto_start", auto_start_check.isChecked())
        qsettings.sync()
        dialog.accept()

    button_box.accepted.connect(save_and_accept)
    button_box.rejected.connect(dialog.reject)
    layout.addWidget(button_box)
    apply_modal_visual_template(dialog, role='network_settings')
    return dialog.exec() == QDialog.Accepted

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--server':
        print("تشغيل خادم الراجحي للمحاسبة...")
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        server_root = os.path.join(project_root, 'alrajhi_server')
        # ضع مسار الخادم أولاً حتى لا تلتقط Python حزمة database الخاصة بالعميل.
        for path in (project_root, server_root):
            if path in sys.path:
                sys.path.remove(path)
        sys.path.insert(0, project_root)
        sys.path.insert(0, server_root)
        server_port = int(os.environ.get("ALRAJHI_SERVER_PORT", str(system_service.default_port())))
        if system_service.port_in_use(server_port):
            print(f"✅ الخادم يعمل مسبقاً على المنفذ {server_port}")
            return

        # Ensure the API server uses the same writable SQLite file as the desktop server UI.
        try:
            server_db_path = system_service.configure_server_database_path()
            print(f"ℹ️ مسار قاعدة بيانات الخادم: {server_db_path}")
        except Exception as exc:
            print(f"⚠️ تعذر ضبط مسار قاعدة بيانات الخادم الموحد: {exc}")
        system_service.ensure_server_database()
        from waitress import serve
        from alrajhi_server.app import app as server_app
        try:
            serve(server_app, host='0.0.0.0', port=server_port, threads=4)
        except OSError as e:
            if getattr(e, 'errno', None) == 98 or 'Address already in use' in str(e):
                print(f"✅ الخادم يعمل مسبقاً على المنفذ {server_port}")
                return
            raise
        return

    app = QApplication(sys.argv)
    install_offline_exception_hook(app)
    app.setWindowIcon(QIcon(app_icon()))
    install_non_blocking_message_boxes(app)
    app.setFont(QFont("Tajawal", 10))
    enable_auto_select_all(app)

    timeline = StartupTimelineProfiler()
    timeline.set_context(phase="435", runtime="qt")

    settings = QSettings("Alrajhi", "Accounting")

    mode = system_service.mode()
    timeline.set_context(mode=mode)
    timeline.mark("runtime_mode_resolved", f"mode={mode}", category="startup")
    server_url = system_service.normalize_server_url(system_service.server_url(), system_service.get_server_port())

    if mode in ("client", "server"):
        network_ok, network_msg = check_network_activation()
        if not network_ok:
            QMessageBox.critical(None, "تفعيل الشبكة مطلوب",
                                 f"{network_msg}\n\nسيتم تشغيل التطبيق في الوضع المحلي.")
            mode = "local"
            settings.setValue("network/mode", "local")
            system_service.set_mode("local")

    if mode == "server":
        # وضع الخادم يعني أن هذا الجهاز يستخدم قاعدة محلية ويمكنه اختيارياً
        # تشغيل خدمة API للأجهزة الأخرى. لا نشغّل الخادم تلقائياً إلا إذا
        # فعّل المستخدم ذلك صراحة من إعدادات الشبكة. هذا يمنع فتح التطبيق
        # لنفسه بشكل متكرر عند بدء التشغيل.
        os.environ['ALRAJHI_MODE'] = 'server'
        auto_start_server = settings.value("server/auto_start", False, type=bool)
        server_port = system_service.get_server_port()
        if auto_start_server:
            ok, msg = system_service.start_server_process(main_file=os.path.abspath(__file__), port=server_port)
            if not ok:
                QMessageBox.warning(
                    None,
                    "تنبيه الخادم",
                    f"تعذر تشغيل الخادم المحلي تلقائياً:\n{msg}\n\n"
                    "يمكن تشغيله أو إيقافه يدوياً من الإعدادات > الشبكة."
                )
        else:
            print("ℹ️ وضع الخادم مفعل، لكن التشغيل التلقائي للخادم معطل من الإعدادات.")
    elif mode == "client":
        os.environ['ALRAJHI_MODE'] = 'client'
        if not test_server_connection(server_url):
            QMessageBox.critical(None, "خطأ في الاتصال",
                                 f"لا يمكن الاتصال بالخادم المحدد:\n{server_url}\n\n"
                                 "سيتم فتح إعدادات الشبكة لتعديل العنوان.")
            if open_network_settings():
                QMessageBox.information(None, "تم الحفظ", "سيتم إعادة تشغيل التطبيق لتطبيق الإعدادات.")
            sys.exit(0)
    else:
        os.environ['ALRAJHI_MODE'] = 'local'

    ThemeManager.init_app(app)
    install_modal_visual_event_filter(app)

    splash = ModernSplashScreen()
    timeline.mark("prelogin_splash_created", "Branded pre-login splash created", category="startup")
    splash.set_progress(10, "جاري تهيئة قاعدة البيانات...")
    timeline.mark("database_bootstrap_started", "Preparing database and startup services", category="startup")
    # In client mode the source of truth is the remote server. Do not create or
    # bootstrap a local SQLite database, otherwise the UI may appear to use local
    # data and background services can mutate the wrong database.
    if not system_service.is_remote():
        system_service.ensure_local_database()
        try:
            warehouse_service.bootstrap()
        except Exception as e:
            print(f"Warehouse bootstrap warning: {e}")
    else:
        print(f"ℹ️ وضع العميل مفعل. مصدر البيانات: {system_service.data_source_label()}")

    timeline.mark("database_bootstrap_finished", "Database/bootstrap stage finished", category="startup")
    splash.set_progress(30, "التحقق من الترخيص...")
    timeline.mark("activation_check_started", "Checking activation/license", category="startup")
    activated, _ = check_activation()
    timeline.mark("activation_check_finished", "Activation/license check finished", category="startup")
    if not activated:
        old_splash = splash
        splash.hide()
        dlg = ActivationDialog(old_splash)
        if dlg.exec() != ActivationDialog.Accepted:
            old_splash.close()
            sys.exit(0)
        old_splash.close()
        old_splash.deleteLater()
        splash = ModernSplashScreen()
        splash.set_progress(30, "تم التفعيل...")

    start_license_checker(24, on_license_invalid)

    splash.set_progress(60, "تسجيل الدخول...")
    timeline.mark("login_dialog_open", "Opening LoginDialog", category="login")
    login = LoginDialog(splash)
    splash.hide()
    if login.exec() != LoginDialog.Accepted:
        timeline.mark("login_cancelled", "LoginDialog rejected by user", category="login")
        try:
            timeline.export()
        except Exception:
            pass
        stop_license_checker()
        sys.exit(0)

    timeline.mark("login_accepted", "Login accepted; starting post-login transition", category="login")
    post_login_overlay = PostLoginTransitionOverlay()
    post_login_overlay.update_step(15, translate('post_login_step_permissions'), translate('post_login_loading_detail'))
    post_login_overlay.show_transition()

    if UserSession.force_password_change():
        from views.dialogs.change_password_dialog import ChangePasswordDialog
        dlg = ChangePasswordDialog()
        if dlg.exec():
            UserSession.set_force_password_change(False)
        else:
            # لا نسمح بفتح النظام إذا كان الخادم يفرض تغيير كلمة المرور.
            # فتح الواجهة في هذه الحالة يؤدي إلى استدعاء DAOs محلية أثناء remote mode.
            UserSession.logout()
            try:
                post_login_overlay.close()
                timeline.mark("force_password_change_cancelled", "User did not complete password change", category="login")
                timeline.export()
            except Exception:
                pass
            stop_license_checker()
            sys.exit(0)

    post_login_overlay.update_step(35, translate('post_login_step_permissions'), "")
    timeline.mark("post_login_user_context_ready", "User session and password policy resolved", category="post_login")
    splash.set_progress(90, "جاري تحميل الواجهة...")
    post_login_overlay.update_step(65, translate('post_login_step_main_window'), translate('post_login_loading_detail'))
    timeline.mark("main_window_create_started", "Constructing MainWindow", category="post_login")
    window = MainWindow()
    timeline.mark("main_window_created", "MainWindow constructed", category="post_login")
    post_login_overlay.update_step(90, translate('post_login_step_dashboard'), "")
    splash.finish(window)
    runtime_fit_profile = show_main_window_runtime_fitted(window)
    timeline.set_context(main_shell_runtime_fit=runtime_fit_profile.as_dict())
    timeline.mark("main_window_shown", "MainWindow shown", category="post_login")
    try:
        post_login_overlay.finish_transition()
    except Exception:
        pass
    try:
        timeline.export()
    except Exception as e:
        print(f"⚠️ startup timeline export failed: {e}")

    backup_thread = start_periodic_backup()
    if backup_thread:
        window.backup_thread = backup_thread

    sys.exit(app.exec())

if __name__ == "__main__":
    main()


