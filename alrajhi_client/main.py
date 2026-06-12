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
from PyQt5.QtGui import QFont
from database import ensure_db
from core.services.warehouse_service import warehouse_service
from auth.activation import check_activation, start_license_checker, stop_license_checker, check_network_activation
from views.splash_screen import ModernSplashScreen
from views.dialogs.activation_dialog import ActivationDialog
from views.dialogs.login_dialog import LoginDialog
from views.main_window import MainWindow
from auth.session import UserSession
from utils import enable_auto_select_all, install_non_blocking_message_boxes
from theme_manager import ThemeManager

_backup_stop_event = None
_backup_thread = None

def on_license_invalid():
    def show():
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("ترخيص منتهي")
        msg.setText("انتهت صلاحية الترخيص.\nسيتم إغلاق التطبيق.")
        msg.exec()
        sys.exit(1)
    QTimer.singleShot(0, show)

def run_flask_server():
    """Start the embedded server once.

    In server mode the desktop client launches a background process with
    ``--server``.  Without these guards a packaged executable can recursively
    open itself when the child process reads the saved "server" mode again, or
    crash when port 8000 is already occupied.
    """
    server_port = 8000
    if port_in_use(server_port):
        print(f"✅ الخادم يعمل مسبقاً على المنفذ {server_port}")
        return True

    error_log = os.path.join(tempfile.gettempdir(), "alrajhi_subprocess_error.log")
    try:
        exe_path = sys.executable
        cmd = [exe_path, os.path.abspath(__file__), '--server']
        env = os.environ.copy()
        env['ALRAJHI_SERVER_CHILD'] = '1'
        env['ALRAJHI_MODE'] = 'server'

        if sys.platform == 'win32':
            subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW, env=env)
        else:
            subprocess.Popen(cmd, env=env)
        return True
    except Exception as e:
        with open(error_log, "w", encoding='utf-8') as f:
            f.write(str(e))
        def show_error():
            QMessageBox.critical(None, "خطأ في الخادم",
                                 f"فشل بدء خادم Flask.\nتم تسجيل الخطأ في:\n{error_log}")
        QTimer.singleShot(0, show_error)
        return False

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


def port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Return True when a TCP port is already occupied.

    Used before starting the embedded Waitress server so the desktop
    client does not crash with OSError: [Errno 98] Address already in use.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex((host, int(port))) == 0
    except Exception:
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
    from database.connection import DatabaseConnection
    db = DatabaseConnection()
    if db.is_remote():
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
        resp = requests.get(f"{url}/health", timeout=3)
        return resp.status_code == 200 and resp.json().get("status") == "alive"
    except:
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
        QComboBox, QLineEdit, QLabel, QPushButton, QMessageBox
    )

    dialog = QDialog()
    dialog.setWindowTitle("إعدادات الشبكة")
    dialog.setLayoutDirection(Qt.RightToLeft)
    dialog.resize(520, 260)

    qsettings = QSettings("Alrajhi", "Accounting")

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(18, 18, 18, 18)
    layout.setSpacing(12)

    note = QLabel(
        "لا يمكن الاتصال بالخادم الحالي. عدّل وضع التشغيل أو عنوان الخادم هنا. "
        "هذه النافذة تستخدم إعدادات محلية فقط ولا تحتاج إلى اتصال بالخادم."
    )
    note.setWordWrap(True)
    note.setStyleSheet(
        "QLabel { background:#fff7ed; color:#9a3412; border:1px solid #fed7aa; "
        "border-radius:8px; padding:10px; }"
    )
    layout.addWidget(note)

    form = QFormLayout()
    form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

    mode_combo = QComboBox()
    mode_combo.addItem("محلي (بدون شبكة)", "local")
    mode_combo.addItem("عميل (اتصال بخادم)", "client")
    mode_combo.addItem("خادم (تشغيل خدمة)", "server")
    current_mode = qsettings.value("network/mode", "local")
    idx = mode_combo.findData(current_mode)
    mode_combo.setCurrentIndex(idx if idx >= 0 else 0)
    form.addRow("وضع التشغيل:", mode_combo)

    server_url_edit = QLineEdit(qsettings.value("network/server_url", "http://localhost:8000"))
    server_url_edit.setPlaceholderText("http://192.168.1.100:8000")
    form.addRow("عنوان الخادم:", server_url_edit)

    status = QLabel("")
    status.setWordWrap(True)
    form.addRow("الحالة:", status)

    layout.addLayout(form)

    def test_current_server():
        url = server_url_edit.text().strip().rstrip('/')
        if not url:
            status.setText("يرجى إدخال عنوان الخادم.")
            status.setStyleSheet("color:#b91c1c;")
            return
        if test_server_connection(url):
            status.setText("✅ الاتصال بالخادم ناجح.")
            status.setStyleSheet("color:#15803d;")
        else:
            status.setText("❌ لا يمكن الاتصال بهذا العنوان.")
            status.setStyleSheet("color:#b91c1c;")

    test_btn = QPushButton("اختبار الاتصال")
    test_btn.clicked.connect(test_current_server)
    btn_row = QHBoxLayout()
    btn_row.addStretch()
    btn_row.addWidget(test_btn)
    layout.addLayout(btn_row)

    button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

    def save_and_accept():
        qsettings.setValue("network/mode", mode_combo.currentData() or "local")
        qsettings.setValue("network/server_url", server_url_edit.text().strip() or "http://localhost:8000")
        dialog.accept()

    button_box.accepted.connect(save_and_accept)
    button_box.rejected.connect(dialog.reject)
    layout.addWidget(button_box)
    return dialog.exec() == QDialog.Accepted

def main():
    if ('--server' in sys.argv) or (os.environ.get('ALRAJHI_SERVER_CHILD') == '1'):
        print("تشغيل خادم الراجحي للمحاسبة...")
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        server_root = os.path.join(project_root, 'alrajhi_server')
        # ضع مسار الخادم أولاً حتى لا تلتقط Python حزمة database الخاصة بالعميل.
        for path in (project_root, server_root):
            if path in sys.path:
                sys.path.remove(path)
        sys.path.insert(0, project_root)
        sys.path.insert(0, server_root)
        server_port = 8000
        if port_in_use(server_port):
            print(f"✅ الخادم يعمل مسبقاً على المنفذ {server_port}")
            return

        from database.migrations import ensure_db as ensure_db_remote
        ensure_db_remote()
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
    install_non_blocking_message_boxes(app)
    app.setFont(QFont("Tajawal", 10))
    enable_auto_select_all(app)

    settings = QSettings("Alrajhi", "Accounting")

    from database.connection import DatabaseConnection
    db_conn = DatabaseConnection()
    mode = db_conn.mode
    server_url = db_conn.server_url

    if mode in ("client", "server"):
        network_ok, network_msg = check_network_activation()
        if not network_ok:
            QMessageBox.critical(None, "تفعيل الشبكة مطلوب",
                                 f"{network_msg}\n\nسيتم تشغيل التطبيق في الوضع المحلي.")
            mode = "local"
            settings.setValue("network/mode", "local")
            db_conn.mode = "local"

    if mode == "server":
        os.environ['ALRAJHI_MODE'] = 'server'
        if not port_in_use(8000):
            if not run_flask_server():
                QMessageBox.critical(None, "خطأ", "فشل بدء الخادم الداخلي.")
                sys.exit(1)
            if not wait_for_server("http://localhost:8000"):
                QMessageBox.critical(None, "خطأ", "فشل بدء الخادم الداخلي. تحقق من المنفذ 8000 أو جدار الحماية.")
                sys.exit(1)
            QMessageBox.information(None, "خادم", "تم بدء الخادم بنجاح. يمكن للأجهزة الأخرى الاتصال به.")
        else:
            print("✅ الخادم يعمل مسبقاً، سيتم فتح العميل دون تشغيل نسخة جديدة.")
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

    splash = ModernSplashScreen()
    splash.set_progress(10, "جاري تهيئة قاعدة البيانات...")
    ensure_db()
    try:
        warehouse_service.bootstrap()
    except Exception as e:
        print(f"Warehouse bootstrap warning: {e}")

    splash.set_progress(30, "التحقق من الترخيص...")
    activated, _ = check_activation()
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
    login = LoginDialog(splash)
    splash.hide()
    if login.exec() != LoginDialog.Accepted:
        stop_license_checker()
        sys.exit(0)

    if UserSession.force_password_change():
        from views.dialogs.change_password_dialog import ChangePasswordDialog
        from database import UserRepository
        dlg = ChangePasswordDialog()
        if dlg.exec():
            repo = UserRepository()
            repo.set_force_password_change(UserSession.get_current()['id'], False)
            UserSession.set_force_password_change(False)
        else:
            # لا نسمح بفتح النظام إذا كان الخادم يفرض تغيير كلمة المرور.
            # فتح الواجهة في هذه الحالة يؤدي إلى استدعاء DAOs محلية أثناء remote mode.
            UserSession.logout()
            stop_license_checker()
            sys.exit(0)

    splash.set_progress(90, "جاري تحميل الواجهة...")
    window = MainWindow()
    splash.finish(window)
    window.show()

    backup_thread = start_periodic_backup()
    if backup_thread:
        window.backup_thread = backup_thread

    sys.exit(app.exec())

if __name__ == "__main__":
    main()


