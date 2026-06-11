# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QPushButton, QLabel, QFrame, QMessageBox, QApplication, QMenuBar, QAction, QShortcut, QMenu
from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation, QTimer
from PyQt5.QtGui import QIcon, QKeySequence
import qtawesome as qta
from auth.session import UserSession
from theme_manager import ThemeManager
from views.widgets.dashboard_widget import DashboardWidget
from views.widgets.items_widget import ItemsWidget
from views.widgets.invoices_widget import SalesInvoicesWidget, PurchaseInvoicesWidget
from views.widgets.pos_widget import POSWidget
from views.widgets.manufacturing_widget import ManufacturingWidget
from views.widgets.customers_widget import CustomersWidget
from views.widgets.suppliers_widget import SuppliersWidget
from views.widgets.vouchers_widget import VouchersWidget
from views.widgets.reports_widget import ReportsWidget
from views.widgets.settings_widget import SettingsWidget
from views.widgets.users_widget import UsersWidget
from views.widgets.categories_widget import CategoriesWidget
from views.widgets.warehouses_widget import WarehousesWidget
from views.widgets.branches_widget import BranchesWidget
from views.widgets.cashboxes_widget import CashboxesWidget
from views.widgets.returns_widget import ReturnsWidget, PurchaseReturnsWidget
from views.widgets.audit_log_widget import AuditLogWidget
from views.dialogs.change_password_dialog import ChangePasswordDialog
from views.dialogs.login_dialog import LoginDialog
from views.modern_topbar import ModernTopBar
from i18n.translator import translate, set_language, direction
from core.services.settings_service import settings_service

PAGE_META = {
    'dashboard': ('لوحة التحكم', 'الرئيسية'),
    'pos': ('نقطة البيع POS', 'الرئيسية > المبيعات > نقطة البيع'),
    'sales_invoices': ('فواتير البيع', 'الرئيسية > المبيعات > فواتير البيع'),
    'purchase_invoices': ('فواتير الشراء', 'الرئيسية > المشتريات > فواتير الشراء'),
    'items': ('المواد والمخزون', 'الرئيسية > المخزون > المواد'),
    'categories': ('التصنيفات', 'الرئيسية > المخزون > التصنيفات'),
    'warehouses': ('المستودعات', 'الرئيسية > المخزون > المستودعات'),
    'branches': ('الفروع', 'الرئيسية > الإدارة > الفروع'),
    'cashboxes': ('الصناديق والبنوك', 'الرئيسية > المالية > الصناديق والبنوك'),
    'customers': ('العملاء', 'الرئيسية > المبيعات > العملاء'),
    'suppliers': ('الموردون', 'الرئيسية > المشتريات > الموردون'),
    'vouchers': ('السندات', 'الرئيسية > المالية > السندات'),
    'returns': ('مرتجعات المبيعات', 'الرئيسية > المبيعات > مرتجعات المبيعات'),
    'purchase_returns': ('مرتجعات المشتريات', 'الرئيسية > المشتريات > مرتجعات المشتريات'),
    'manufacturing': ('التصنيع', 'الرئيسية > التصنيع'),
    'reports': ('التقارير', 'الرئيسية > التقارير'),
    'settings': ('الإعدادات', 'الرئيسية > النظام > الإعدادات'),
    'users': ('المستخدمون', 'الرئيسية > النظام > المستخدمون'),
    'audit_log': ('سجل التدقيق', 'الرئيسية > النظام > سجل التدقيق'),
}

NAV_GROUP_BY_PAGE = {
    'dashboard': 'الرئيسية',
    'pos': 'المبيعات',
    'sales_invoices': 'المبيعات',
    'purchase_invoices': 'المشتريات',
    'customers': 'المبيعات',
    'suppliers': 'المشتريات',
    'vouchers': 'المبيعات',
    'returns': 'المبيعات',
    'purchase_returns': 'المشتريات',
    'items': 'المخزون',
    'categories': 'المخزون',
    'warehouses': 'المخزون',
    'branches': 'الإدارة',
    'cashboxes': 'المبيعات',
    'manufacturing': 'التصنيع',
    'reports': 'التقارير',
    'settings': 'الإدارة',
    'users': 'المستخدمين',
    'audit_log': 'المستخدمين',
}

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setMinimumSize(1200, 700)
        self.resize(1400, 900)
        self.drag_pos = None

        lang = settings_service.get_language()
        set_language(lang)
        self.setLayoutDirection(Qt.RightToLeft if direction(lang) == "rtl" else Qt.LeftToRight)
        theme = settings_service.get_theme()
        ThemeManager.apply_theme(theme)

        self.setup_ui()
        self.setup_menus()
        self.setup_topbar_buttons()
        self.setup_shell_state()
        self.setup_shortcuts()
        self.setup_offline_queue()
        self.switch_page('dashboard')

    def setup_ui(self):
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(46)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(15, 0, 10, 0)

        icon_label = QLabel("🏢")
        icon_label.setFixedSize(24, 24)
        title_layout.addWidget(icon_label)
        self.title_label = QLabel("الراجحي للمحاسبة")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        self.close_btn = QPushButton()
        self.close_btn.setIcon(qta.icon('fa5s.times'))
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.clicked.connect(self.close_app)
        title_layout.addWidget(self.close_btn)

        self.max_btn = QPushButton()
        self.max_btn.setIcon(qta.icon('fa5s.window-maximize'))
        self.max_btn.setFixedSize(32, 32)
        self.max_btn.clicked.connect(self.toggle_maximize)
        title_layout.addWidget(self.max_btn)

        self.min_btn = QPushButton()
        self.min_btn.setIcon(qta.icon('fa5s.window-minimize'))
        self.min_btn.setFixedSize(32, 32)
        self.min_btn.clicked.connect(self.showMinimized)
        title_layout.addWidget(self.min_btn)

        main_layout.addWidget(self.title_bar)

        self.menu_bar = QMenuBar()
        self.menu_bar.setStyleSheet("QMenuBar { background-color: palette(window); border-bottom: 1px solid palette(mid); }")
        self.menu_bar.setFixedHeight(30)
        main_layout.addWidget(self.menu_bar)

        self.top_bar = ModernTopBar(self)
        main_layout.addWidget(self.top_bar)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        self.pages = {}
        self.init_pages()

        self.title_bar.mousePressEvent = self._mouse_press
        self.title_bar.mouseMoveEvent = self._mouse_move
        self.title_bar.mouseReleaseEvent = self._mouse_release

    def init_pages(self):
        self.pages['dashboard'] = DashboardWidget(self)
        self.pages['items'] = ItemsWidget(self)
        # Sales and purchases are intentionally separate MainWindow pages.
        # Do not instantiate the legacy combined InvoicesWidget here.
        self.pages['sales_invoices'] = SalesInvoicesWidget(self)
        self.pages['purchase_invoices'] = PurchaseInvoicesWidget(self)
        self.pages['pos'] = POSWidget(self)
        self.pages['manufacturing'] = ManufacturingWidget(self)
        self.pages['customers'] = CustomersWidget(self)
        self.pages['suppliers'] = SuppliersWidget(self)
        self.pages['vouchers'] = VouchersWidget(self)
        self.pages['returns'] = ReturnsWidget(self)
        self.pages['purchase_returns'] = PurchaseReturnsWidget(self)
        self.pages['reports'] = ReportsWidget(self)
        self.pages['settings'] = SettingsWidget(self)
        self.pages['users'] = UsersWidget(self)
        self.pages['categories'] = CategoriesWidget(self)
        self.pages['warehouses'] = WarehousesWidget(self)
        self.pages['branches'] = BranchesWidget(self)
        self.pages['cashboxes'] = CashboxesWidget(self)
        self.pages['audit_log'] = AuditLogWidget(self)

        for page in self.pages.values():
            self.stack.addWidget(page)

    def setup_menus(self):
        file_menu = self.menu_bar.addMenu(qta.icon('fa5s.file-alt'), " " + translate("file"))
        logout_action = QAction(qta.icon('fa5s.sign-out-alt'), translate("logout"), self)
        logout_action.setShortcut(QKeySequence("Ctrl+Q"))
        logout_action.triggered.connect(self.logout)
        file_menu.addAction(logout_action)
        file_menu.addSeparator()
        exit_action = QAction(qta.icon('fa5s.times-circle'), translate("exit"), self)
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.triggered.connect(self.close_app)
        file_menu.addAction(exit_action)

        view_menu = self.menu_bar.addMenu(qta.icon('fa5s.eye'), " " + translate("view"))
        toggle_title_action = QAction(qta.icon('fa5s.window-maximize'), translate("show_title_bar"), self)
        toggle_title_action.setCheckable(True)
        toggle_title_action.setChecked(True)
        toggle_title_action.triggered.connect(self.toggle_title_bar)
        view_menu.addAction(toggle_title_action)
        view_menu.addSeparator()
        touch_action = QAction(qta.icon('fa5s.hand-peace'), translate("touch_mode"), self)
        touch_action.setCheckable(True)
        touch_action.setChecked(False)
        touch_action.triggered.connect(self.toggle_touch_mode)
        view_menu.addAction(touch_action)

        theme_menu = self.menu_bar.addMenu(qta.icon('fa5s.palette'), " " + translate("themes"))
        themes = [(translate("light"), "light"), (translate("dark"), "dark")]
        for name, theme_id in themes:
            action = QAction(name, self)
            action.triggered.connect(lambda checked, t=theme_id: self.change_theme(t))
            theme_menu.addAction(action)

        help_menu = self.menu_bar.addMenu(qta.icon('fa5s.question-circle'), " " + translate("help"))
        about_action = QAction(qta.icon('fa5s.info-circle'), translate("about"), self)
        about_action.setShortcut(QKeySequence("F1"))
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_topbar_buttons(self):
        self.top_bar.add_button(translate("dashboard"), "tachometer-alt", lambda: self.switch_page('dashboard'), show_text=False)
        self.top_bar.add_menu_button(translate("sales"), "shopping-cart", [
            (translate("pos"), "barcode", lambda: self.switch_page('pos'), None),
            (translate("sales_invoices"), "file-invoice", lambda: self.switch_page('sales_invoices'), None),
            (translate("customers"), "user-friends", lambda: self.switch_page('customers'), None),
            (translate("receipt_vouchers"), "hand-holding-usd", lambda: self.switch_page('vouchers'), None),
            (translate("sales_returns"), "undo", lambda: self.switch_page('returns'), None),
            (translate("cashboxes_banks"), "cash-register", lambda: self.switch_page('cashboxes'), None),
        ])
        self.top_bar.add_menu_button(translate("purchases"), "truck", [
            (translate("purchase_invoices"), "file-invoice", lambda: self.switch_page('purchase_invoices'), None),
            (translate("suppliers"), "users", lambda: self.switch_page('suppliers'), None),
            (translate("payment_vouchers"), "money-bill", lambda: self.switch_page('vouchers'), None),
            (translate("purchase_returns"), "undo-alt", lambda: self.switch_page('purchase_returns'), None),
        ])
        self.top_bar.add_menu_button(translate("inventory"), "boxes", [
            (translate("items"), "box", lambda: self.switch_page('items'), None),
            (translate("categories"), "folder", lambda: self.switch_page('categories'), None),
            (translate("warehouses"), "warehouse", lambda: self.switch_page('warehouses'), None),
        ])
        self.top_bar.add_menu_button(translate("manufacturing"), "industry", [
            (translate("bom"), "list", lambda: self.switch_page('manufacturing'), None),
            (translate("production_orders"), "tasks", lambda: self.switch_page('manufacturing'), None),
        ])
        self.top_bar.add_menu_button(translate("reports"), "chart-line", [
            (translate("income_statement"), "chart-line", lambda: self.switch_page('reports'), None),
            (translate("balance_sheet"), "building", lambda: self.switch_page('reports'), None),
            (translate("customer_statement"), "user", lambda: self.switch_page('reports'), None),
            (translate("supplier_statement"), "truck", lambda: self.switch_page('reports'), None),
        ])
        self.top_bar.add_menu_button(translate("management"), "cog", [
            (translate("settings"), "sliders-h", lambda: self.switch_page('settings'), None),
            (translate("branches"), "code-branch", lambda: self.switch_page('branches'), None),
            ("طباعة احترافية", "print", lambda: self.show_print_dialog(), None),
            ("تغيير كلمة المرور", "key", lambda: self.change_password(), None),
        ])
        if UserSession.is_admin():
            self.top_bar.add_menu_button(translate("users"), "user-cog", [
                (translate("users"), "users", lambda: self.switch_page('users'), None),
                (translate("audit_log"), "history", lambda: self.switch_page('audit_log'), None),
            ])
        self.top_bar.add_button(translate("help"), "question-circle", self.show_about, show_text=True)

        self.top_bar.search_box.returnPressed.connect(self.global_search)
        self.top_bar.theme_btn.clicked.connect(self.toggle_theme)
        self.top_bar.alert_btn.clicked.connect(self.show_alerts_menu)
        self.update_badges()


    def setup_shell_state(self):
        user = UserSession.get_current() or {}
        self.top_bar.set_user(user.get('username', ''), user.get('role', ''))
        if hasattr(self.top_bar, 'apply_styles'):
            self.top_bar.apply_styles()

    def toggle_theme(self):
        current = settings_service.get_theme() or 'light'
        next_theme = 'dark' if current != 'dark' else 'light'
        self.change_theme(next_theme)

    def show_alerts_menu(self):
        menu = QMenu(self)
        try:
            from core.services.alert_service import alert_service
            alerts = alert_service.dashboard_alerts(limit=8) if hasattr(alert_service, 'dashboard_alerts') else []
        except Exception:
            alerts = []
        if not alerts:
            action = menu.addAction(qta.icon('fa5s.check-circle'), 'لا توجد تنبيهات حرجة')
            action.setEnabled(False)
        else:
            for alert in alerts[:8]:
                title = alert.get('title') or alert.get('message') or str(alert)
                menu.addAction(qta.icon('fa5s.exclamation-triangle'), title)
            menu.addSeparator()
            menu.addAction(qta.icon('fa5s.tachometer-alt'), 'فتح لوحة التحكم').triggered.connect(lambda: self.switch_page('dashboard'))
        menu.exec_(self.top_bar.alert_btn.mapToGlobal(self.top_bar.alert_btn.rect().bottomLeft()))

    def _set_page_context(self, pid):
        title, breadcrumb = PAGE_META.get(pid, (pid, pid))
        if hasattr(self, 'top_bar'):
            self.top_bar.set_page_context(title, breadcrumb)
            self.top_bar.set_active(NAV_GROUP_BY_PAGE.get(pid, pid))
        self.title_label.setText(f"الراجحي للمحاسبة — {title}")

    def setup_shortcuts(self):
        self.esc_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.esc_shortcut.activated.connect(lambda: self.switch_page('dashboard'))
        self.dashboard_shortcut = QShortcut(QKeySequence('F1'), self)
        self.dashboard_shortcut.activated.connect(lambda: self.switch_page('dashboard'))
        self.pos_shortcut = QShortcut(QKeySequence('F2'), self)
        self.pos_shortcut.activated.connect(lambda: self.switch_page('pos'))
        self.sale_shortcut = QShortcut(QKeySequence('F3'), self)
        self.sale_shortcut.activated.connect(lambda: self.switch_page('sales_invoices'))
        self.new_item_shortcut = QShortcut(QKeySequence('F4'), self)
        self.new_item_shortcut.activated.connect(lambda: self.switch_page('items'))
        self.warehouse_shortcut = QShortcut(QKeySequence('F5'), self)
        self.warehouse_shortcut.activated.connect(lambda: self.switch_page('warehouses'))
        self.legacy_pos_shortcut = QShortcut(QKeySequence('F9'), self)
        self.legacy_pos_shortcut.activated.connect(lambda: self.switch_page('pos'))

    def update_badges(self):
        try:
            from core.services.invoice_service import invoice_service
            pending = invoice_service.pending_count()
            self.top_bar.set_badge(translate("sales_invoices"), pending)
        except:
            pass

    def global_search(self):
        text = self.top_bar.search_box.text().strip()
        if text:
            self.show_global_search(text)

    def show_global_search(self, text=None):
        if not text:
            return
        lowered = text.strip().lower()
        if lowered:
            # بحث مبدئي سريع: يفتح شاشة المواد لأنها تدعم الاسم/الباركود.
            self.switch_page('items')
            page = self.pages.get('items')
            if page and hasattr(page, 'search_input'):
                page.search_input.setText(text)
                if hasattr(page, 'refresh'):
                    page.refresh()
            else:
                QMessageBox.information(self, "بحث", f"تم البحث عن: {text}")

    def show_print_dialog(self):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "طباعة", "سيتم فتح نافذة الطباعة قريباً")

    def show_about(self):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.about(self, translate("about"),
            "<h3>الراجحي للمحاسبة</h3>"
            "<p>الإصدار 2.0</p>"
            "<p>نظام متكامل لإدارة المحاسبة والمخزون والتصنيع</p>")

    def toggle_title_bar(self, checked):
        self.title_bar.setVisible(checked)

    def toggle_touch_mode(self, checked):
        pass

    def change_theme(self, theme_id):
        settings_service.set_theme(theme_id)
        ThemeManager.apply_theme(theme_id, persist=True)
        for page in self.pages.values():
            if hasattr(page, 'apply_theme_colors'):
                page.apply_theme_colors()
        if hasattr(self.top_bar, 'apply_styles'):
            self.top_bar.apply_styles()

    def _mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def _mouse_move(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

    def _mouse_release(self, event):
        self.drag_pos = None

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self.max_btn.setIcon(qta.icon('fa5s.window-maximize'))
        else:
            self.showMaximized()
            self.max_btn.setIcon(qta.icon('fa5s.window-restore'))

    def switch_page(self, pid):
        if pid == 'invoices':
            pid = 'sales_invoices'
        if pid in self.pages:
            if self.stack.currentWidget() is not self.pages[pid]:
                self.stack.setCurrentWidget(self.pages[pid])
            self._set_page_context(pid)
            if hasattr(self.pages[pid], 'refresh'):
                self.pages[pid].refresh()

    def change_password(self):
        dlg = ChangePasswordDialog(self)
        if dlg.exec():
            QMessageBox.information(self, "نجاح", "تم تغيير كلمة المرور")

    def logout(self):
        reply = QMessageBox.question(self, translate("logout"), "هل تريد تسجيل الخروج؟",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            from database.connection import DatabaseConnection
            db = DatabaseConnection()
            if db.is_remote():
                try:
                    rest_client = db.get_rest_client()
                    if rest_client:
                        rest_client.logout()
                except Exception as e:
                    print(f"Logout error: {e}")
            UserSession.logout()
            self.hide()
            login = LoginDialog(self)
            if login.exec() == LoginDialog.Accepted:
                self.show()
                self.setup_shell_state()
                self.switch_page('dashboard')
            else:
                self.close()

    def close_app(self):
        QApplication.quit()

    # ========== Offline Queue Support ==========
    def setup_offline_queue(self):
        from database.connection import offline_queue, DatabaseConnection
        self.db_conn = DatabaseConnection()
        self.queue_timer = QTimer()
        self.queue_timer.timeout.connect(self.process_offline_queue)
        self.queue_timer.start(30000)

    def process_offline_queue(self):
        from database.connection import offline_queue
        from database.connection_rest import RestClient
        import requests
        import json

        if not self.db_conn.is_remote():
            return
        try:
            resp = requests.get(f"{self.db_conn.server_url}/health", timeout=3)
            if resp.status_code != 200:
                return
        except:
            return

        rest = self.db_conn.get_rest_client()
        for req in offline_queue.get_all_requests():
            try:
                if req['method'] == 'POST':
                    rest._request('POST', req['endpoint'], json.loads(req['data']) if req['data'] else None, queue_on_failure=False)
                elif req['method'] == 'PUT':
                    rest._request('PUT', req['endpoint'], json.loads(req['data']) if req['data'] else None, queue_on_failure=False)
                elif req['method'] == 'DELETE':
                    rest._request('DELETE', req['endpoint'], queue_on_failure=False)
                offline_queue.delete_request(req['id'])
                print(f"✅ تم إعادة إرسال الطلب المحفوظ: {req['endpoint']}")
            except Exception as e:
                print(f"⚠️ فشل إعادة محاولة الطلب {req['endpoint']}: {e}")


