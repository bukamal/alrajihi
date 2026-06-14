# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QPushButton, QLabel, QFrame, QMessageBox, QApplication, QMenuBar, QAction, QShortcut, QMenu, QFileDialog
from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation, QTimer, QDateTime
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
from views.widgets.offline_queue_widget import OfflineQueueWidget
from views.widgets.monitoring_widget import MonitoringWidget
from views.dialogs.change_password_dialog import ChangePasswordDialog
from views.dialogs.login_dialog import LoginDialog
from views.modern_topbar import ModernTopBar
from i18n.translator import translate, set_language, normalize_language, qt_layout_direction
from core.services.settings_service import settings_service
from core.services.system_service import system_service
from core.services.offline_queue_service import offline_queue_service
from brand_assets import app_icon, logo_png, APP_DISPLAY_NAME_AR

PAGE_META_KEYS = {
    'dashboard': ('dashboard', 'home_breadcrumb'),
    'pos': ('pos', 'nav_sales'),
    'sales_invoices': ('sales_invoices', 'nav_sales'),
    'purchase_invoices': ('purchase_invoices', 'nav_purchases'),
    'items': ('items_inventory', 'nav_inventory'),
    'categories': ('categories', 'nav_inventory'),
    'warehouses': ('warehouses', 'nav_inventory'),
    'branches': ('branches', 'nav_admin'),
    'cashboxes': ('cashboxes', 'nav_finance'),
    'customers': ('customers', 'nav_parties'),
    'suppliers': ('suppliers', 'nav_parties'),
    'vouchers': ('vouchers', 'nav_finance'),
    'returns': ('sales_returns', 'nav_sales'),
    'purchase_returns': ('purchase_returns', 'nav_purchases'),
    'manufacturing': ('nav_manufacturing', 'nav_manufacturing'),
    'reports': ('reports', 'reports'),
    'settings': ('settings', 'nav_admin'),
    'users': ('users', 'nav_users'),
    'audit_log': ('audit_log', 'nav_users'),
    'offline_queue': ('offline_queue', 'nav_admin'),
    'monitoring': ('monitoring', 'nav_admin'),
}


def page_title(pid):
    title_key, _ = PAGE_META_KEYS.get(pid, (pid, 'home_breadcrumb'))
    return translate(title_key)


def page_breadcrumb(pid):
    title_key, group_key = PAGE_META_KEYS.get(pid, (pid, 'home_breadcrumb'))
    home = translate('home_breadcrumb')
    group = translate(group_key)
    title = translate(title_key)
    return f"{home} > {group} > {title}" if group != home and title != group else f"{home} > {title}"


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
    'offline_queue': 'الإدارة',
    'monitoring': 'الإدارة',
}

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Phase 41: use the native OS title bar again so the window can be moved
        # normally and the minimize/maximize/close buttons remain available.
        self.setWindowTitle(translate('app_title'))
        self.setWindowIcon(QIcon(app_icon()))
        self._current_language = normalize_language(settings_service.get_language())
        set_language(self._current_language)
        self.setLayoutDirection(qt_layout_direction(self._current_language))
        self.setMinimumSize(1200, 700)
        self.resize(1400, 900)
        self.drag_pos = None

        set_language(self._current_language)
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

        icon_label = QLabel()
        icon_label.setFixedSize(24, 24)
        icon_label.setPixmap(QIcon(app_icon()).pixmap(24, 24))
        title_layout.addWidget(icon_label)
        self.title_label = QLabel(APP_DISPLAY_NAME_AR)
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

        # Legacy custom title strip is no longer part of the visible shell.
        self.title_bar.setVisible(False)

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

    def _remote_error_page(self, page_key: str, exc: Exception):
        title = page_title(page_key)
        w = QWidget(self)
        layout = QVBoxLayout(w)
        layout.setContentsMargins(36, 36, 36, 36)
        msg = QLabel(
            f"تعذر تحميل صفحة {title}.\n\n"
            f"السبب: {exc}\n\n"
            "لن يتم إغلاق البرنامج. تحقق من اتصال الخادم أو من توفر واجهة REST المطلوبة ثم افتح الصفحة مرة أخرى."
        )
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignCenter)
        msg.setStyleSheet("QLabel { font-size: 15px; color: #7f1d1d; padding: 24px; background:#fff1f2; border:1px solid #fecdd3; border-radius:12px; }")
        layout.addWidget(msg)
        return w

    def _create_page_safely(self, page_key: str, factory):
        try:
            return factory(self)
        except Exception as exc:
            print(f"WARNING: failed to load page {page_key}: {exc}")
            return self._remote_error_page(page_key, exc)

    def init_pages(self):
        page_factories = [
            ('dashboard', DashboardWidget),
            ('items', ItemsWidget),
            ('sales_invoices', SalesInvoicesWidget),
            ('purchase_invoices', PurchaseInvoicesWidget),
            ('pos', POSWidget),
            ('manufacturing', ManufacturingWidget),
            ('customers', CustomersWidget),
            ('suppliers', SuppliersWidget),
            ('vouchers', VouchersWidget),
            ('returns', ReturnsWidget),
            ('purchase_returns', PurchaseReturnsWidget),
            ('reports', ReportsWidget),
            ('settings', SettingsWidget),
            ('users', UsersWidget),
            ('categories', CategoriesWidget),
            ('warehouses', WarehousesWidget),
            ('branches', BranchesWidget),
            ('cashboxes', CashboxesWidget),
            ('audit_log', AuditLogWidget),
            ('offline_queue', OfflineQueueWidget),
            ('monitoring', MonitoringWidget),
        ]
        for key, factory in page_factories:
            self.pages[key] = self._create_page_safely(key, factory)
            self.stack.addWidget(self.pages[key])

    def setup_menus(self):
        """Build the primary ERP navigation menu.

        Phase 46 replaces the legacy File/View/Theme/Help menu with business
        navigation grouped by actual ERP workflows. The utility strip below it
        remains dedicated to search, alerts, theme and user identity.
        """
        self.menu_bar.clear()
        self.menu_bar.setLayoutDirection(qt_layout_direction(self._current_language))
        self.menu_bar.setFixedHeight(62)
        self.menu_bar.setStyleSheet("""
            QMenuBar {
                background-color: palette(window);
                border-bottom: 1px solid palette(mid);
                padding: 3px 10px;
                spacing: 4px;
                font-weight: 700;
            }
            QMenuBar::item {
                padding: 6px 14px;
                min-width: 74px;
                border-radius: 10px;
                background: transparent;
            }
            QMenuBar::item:selected {
                background: palette(alternate-base);
            }
            QMenu {
                padding: 5px;
                border: 1px solid palette(mid);
                border-radius: 8px;
            }
            QMenu::item {
                padding: 8px 34px 8px 20px;
                border-radius: 6px;
                min-width: 190px;
            }
            QMenu::item:selected {
                background: palette(highlight);
                color: palette(highlighted-text);
            }
        """)

        def add_action(menu, text, icon_name, page=None, callback=None, shortcut=None):
            action = QAction(qta.icon(f'fa5s.{icon_name}'), text, self)
            if shortcut:
                action.setShortcut(QKeySequence(shortcut))
            if callback is not None:
                action.triggered.connect(callback)
            elif page:
                action.triggered.connect(lambda checked=False, p=page: self.switch_page(p))
            menu.addAction(action)
            return action

        home_menu = self.menu_bar.addMenu(qta.icon('fa5s.home'), '\nالرئيسية')
        add_action(home_menu, translate('dashboard'), 'tachometer-alt', 'dashboard', shortcut='F1')
        add_action(home_menu, translate('pos'), 'barcode', 'pos', shortcut='F2')
        home_menu.addSeparator()
        add_action(home_menu, translate('monitoring'), 'heartbeat', 'monitoring')

        sales_menu = self.menu_bar.addMenu(qta.icon('fa5s.shopping-cart'), '\nالمبيعات')
        add_action(sales_menu, translate('pos'), 'barcode', 'pos', shortcut='F2')
        add_action(sales_menu, translate('sales_invoices'), 'file-invoice-dollar', 'sales_invoices', shortcut='F3')
        add_action(sales_menu, translate('sales_returns'), 'undo', 'returns')
        sales_menu.addSeparator()
        add_action(sales_menu, translate('receipt_voucher'), 'hand-holding-usd', 'vouchers')

        purchase_menu = self.menu_bar.addMenu(qta.icon('fa5s.truck'), '\nالمشتريات')
        add_action(purchase_menu, translate('purchase_invoices'), 'file-invoice', 'purchase_invoices')
        add_action(purchase_menu, translate('purchase_returns'), 'undo-alt', 'purchase_returns')
        purchase_menu.addSeparator()
        add_action(purchase_menu, translate('payment_voucher'), 'money-bill-wave', 'vouchers')

        inventory_menu = self.menu_bar.addMenu(qta.icon('fa5s.boxes'), '\nالمخزون')
        add_action(inventory_menu, translate('items'), 'box', 'items', shortcut='F4')
        add_action(inventory_menu, translate('categories'), 'folder', 'categories')
        add_action(inventory_menu, translate('warehouses'), 'warehouse', 'warehouses', shortcut='F5')

        manufacturing_menu = self.menu_bar.addMenu(qta.icon('fa5s.industry'), '\nالتصنيع')
        add_action(manufacturing_menu, translate('nav_manufacturing'), 'industry', 'manufacturing')

        parties_menu = self.menu_bar.addMenu(qta.icon('fa5s.users'), '\nالأطراف')
        add_action(parties_menu, translate('customers'), 'user-friends', 'customers')
        add_action(parties_menu, translate('suppliers'), 'truck-loading', 'suppliers')

        finance_menu = self.menu_bar.addMenu(qta.icon('fa5s.wallet'), '\nالمالية')
        add_action(finance_menu, translate('cashboxes'), 'cash-register', 'cashboxes')
        add_action(finance_menu, translate('vouchers'), 'receipt', 'vouchers')

        reports_menu = self.menu_bar.addMenu(qta.icon('fa5s.chart-line'), '\nالتقارير')
        add_action(reports_menu, translate('reports'), 'chart-line', 'reports')
        add_action(reports_menu, translate('customer_statement'), 'user', 'reports')
        add_action(reports_menu, translate('supplier_statement'), 'truck', 'reports')
        add_action(reports_menu, translate('ledger_reconciliation'), 'balance-scale', 'reports')

        admin_menu = self.menu_bar.addMenu(qta.icon('fa5s.cog'), '\nالإدارة')
        add_action(admin_menu, translate('settings'), 'sliders-h', 'settings')
        add_action(admin_menu, translate('branches'), 'code-branch', 'branches')
        add_action(admin_menu, translate('offline_queue'), 'cloud-upload-alt', 'offline_queue')
        add_action(admin_menu, translate('monitoring'), 'heartbeat', 'monitoring')
        admin_menu.addSeparator()
        add_action(admin_menu, translate('professional_printing'), 'print', callback=self.show_print_dialog)
        add_action(admin_menu, translate('change_password'), 'key', callback=self.change_password)
        admin_menu.addSeparator()
        add_action(admin_menu, translate('about_app'), 'info-circle', callback=self.show_about, shortcut='F12')
        add_action(admin_menu, translate('logout'), 'sign-out-alt', callback=self.logout, shortcut='Ctrl+Q')
        add_action(admin_menu, translate('exit'), 'times-circle', callback=self.close_app, shortcut='Alt+F4')

        if UserSession.is_admin():
            users_menu = self.menu_bar.addMenu(qta.icon('fa5s.user-shield'), '\nالمستخدمون')
            add_action(users_menu, translate('users'), 'users-cog', 'users')
            add_action(users_menu, translate('audit_log'), 'history', 'audit_log')

        quick_menu = self.menu_bar.addMenu(qta.icon('fa5s.bolt'), '\nإجراءات سريعة')
        add_action(quick_menu, translate('new_sales_invoice'), 'file-invoice-dollar', 'sales_invoices', shortcut='Ctrl+N')
        add_action(quick_menu, translate('new_purchase_invoice'), 'file-invoice', 'purchase_invoices')
        add_action(quick_menu, translate('receipt_voucher'), 'hand-holding-usd', 'vouchers')
        add_action(quick_menu, translate('payment_voucher'), 'money-bill-wave', 'vouchers')
        quick_menu.addSeparator()
        add_action(quick_menu, translate('new_customer'), 'user-plus', 'customers')
        add_action(quick_menu, translate('new_item'), 'box-open', 'items')

    def setup_topbar_buttons(self):
        """Wire utility-strip actions only.

        Primary navigation is now in setup_menus(). This avoids duplicated menu
        rows and keeps the shell visually clean.
        """
        self.top_bar.search_box.returnPressed.connect(self.global_search)
        self.top_bar.theme_btn.clicked.connect(self.toggle_theme)
        self.top_bar.alert_btn.clicked.connect(self.show_alerts_menu)
        if hasattr(self.top_bar, 'screenshot_btn'):
            self.top_bar.screenshot_btn.clicked.connect(self.export_screenshot)
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


    def export_screenshot(self):
        """Capture the current application window and export it as an image."""
        try:
            default_name = f"alrajhi_screenshot_{QDateTime.currentDateTime().toString('yyyyMMdd_HHmmss')}.png"
            path, selected_filter = QFileDialog.getSaveFileName(
                self,
                translate('export_screenshot'),
                default_name,
                f"{translate('png_image')} (*.png);;{translate('jpeg_image')} (*.jpg *.jpeg)"
            )
            if not path:
                return
            suffix = path.lower().rsplit('.', 1)[-1] if '.' in path else ''
            if suffix not in {'png', 'jpg', 'jpeg'}:
                path += '.png'
            screen = QApplication.primaryScreen()
            if screen is None:
                QMessageBox.warning(self, translate('warning'), translate('screenshot_failed'))
                return
            pixmap = screen.grabWindow(self.winId())
            if pixmap.isNull() or not pixmap.save(path):
                QMessageBox.warning(self, translate('warning'), translate('screenshot_failed'))
                return
            QMessageBox.information(self, translate('success'), translate('screenshot_saved').format(path=path))
        except Exception as exc:
            QMessageBox.warning(self, translate('warning'), f"{translate('screenshot_failed')}: {exc}")

    def show_alerts_menu(self):
        menu = QMenu(self)
        try:
            from core.services.alert_service import alert_service
            alerts = alert_service.dashboard_alerts(limit=8) if hasattr(alert_service, 'dashboard_alerts') else []
        except Exception:
            alerts = []
        if not alerts:
            action = menu.addAction(qta.icon('fa5s.check-circle'), translate('no_critical_alerts'))
            action.setEnabled(False)
        else:
            for alert in alerts[:8]:
                title = alert.get('title') or alert.get('message') or str(alert)
                menu.addAction(qta.icon('fa5s.exclamation-triangle'), title)
            menu.addSeparator()
            menu.addAction(qta.icon('fa5s.tachometer-alt'), translate('open_dashboard')).triggered.connect(lambda: self.switch_page('dashboard'))
        try:
            self.update_badges()
        except Exception:
            pass
        menu.exec_(self.top_bar.alert_btn.mapToGlobal(self.top_bar.alert_btn.rect().bottomLeft()))

    def _set_page_context(self, pid):
        title, breadcrumb = page_title(pid), page_breadcrumb(pid)
        if hasattr(self, 'top_bar'):
            self.top_bar.set_page_context(title, breadcrumb)
            self.top_bar.set_active(NAV_GROUP_BY_PAGE.get(pid, pid))
        if hasattr(self, 'title_label'):
            self.title_label.setText(f"{translate('app_title')} — {title}")

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
            self.top_bar.set_badge("فواتير البيع", pending)
        except Exception:
            pass
        try:
            pending_offline = offline_queue_service.count_pending()
            self.top_bar.set_badge(translate('offline_queue'), pending_offline)
        except Exception:
            pass
        try:
            from core.services.alert_service import alert_service
            alerts = alert_service.dashboard_alerts(limit=99) if hasattr(alert_service, 'dashboard_alerts') else []
            count = len(alerts or [])
            if hasattr(self.top_bar, 'set_alert_badge'):
                self.top_bar.set_alert_badge(count)
            if hasattr(self.top_bar, 'alert_btn'):
                base = translate('alerts')
                self.top_bar.alert_btn.setToolTip(f"{base} ({count})" if count else base)
        except Exception:
            if hasattr(self.top_bar, 'set_alert_badge'):
                self.top_bar.set_alert_badge(0)

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
                QMessageBox.information(self, translate('search_title'), translate('search_done', text=text))

    def show_print_dialog(self):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, translate('printing'), translate('printing_soon'))

    def show_about(self):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.about(self, translate('about_app'), translate('about_html'))

    def toggle_title_bar(self, checked):
        # Kept for backward compatibility with older shortcuts/plugins.
        return

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
            QMessageBox.information(self, translate('success'), translate('password_changed'))

    def logout(self):
        reply = QMessageBox.question(self, translate('logout'), translate('logout_confirm'),
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                system_service.logout_remote()
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
        self.queue_timer = QTimer()
        self.queue_timer.timeout.connect(self.process_offline_queue)
        self.queue_timer.start(30000)

    def process_offline_queue(self, show_messages=False):
        result = offline_queue_service.process_pending()
        sent = int(result.get('sent', 0) or 0)
        failed = int(result.get('failed', 0) or 0)
        if sent or failed:
            try:
                self.update_badges()
                page = self.pages.get('offline_queue')
                if page and hasattr(page, 'refresh'):
                    page.refresh()
            except Exception:
                pass
        if show_messages:
            try:
                from utils import show_toast
                show_toast(f"{translate('sent') if False else 'تم الإرسال'}: {sent}\n{'فشل'}: {failed}", 'success' if failed == 0 else 'warning', self)
            except Exception:
                QMessageBox.information(self, translate('offline_queue'), f'تم الإرسال: {sent}\nفشل: {failed}')


