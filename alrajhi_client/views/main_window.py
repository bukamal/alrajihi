# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QPushButton, QLabel, QFrame, QMessageBox, QApplication, QMenuBar, QAction, QShortcut, QMenu, QFileDialog, QToolButton
from PyQt5.QtCore import Qt, QPoint, QPropertyAnimation, QTimer, QDateTime, QSize
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
from views.restaurant.restaurant_dashboard import RestaurantDashboard
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
    'restaurant': ('restaurant.dashboard', 'nav_restaurant'),
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



# Phase116: page-aware global search. Each page decides whether the shell
# search box is visible and what business fields it filters. Unsupported
# pages, especially the dashboard, hide the box instead of showing a dead
# control.
GLOBAL_SEARCH_PLACEHOLDERS = {
    'pos': 'context_search_pos_placeholder',
    'sales_invoices': 'context_search_sales_invoices_placeholder',
    'purchase_invoices': 'context_search_purchase_invoices_placeholder',
    'items': 'context_search_items_placeholder',
    'categories': 'context_search_categories_placeholder',
    'warehouses': 'context_search_warehouses_placeholder',
    'branches': 'context_search_branches_placeholder',
    'cashboxes': 'context_search_cashboxes_placeholder',
    'customers': 'context_search_customers_placeholder',
    'suppliers': 'context_search_suppliers_placeholder',
    'vouchers': 'context_search_vouchers_placeholder',
    'returns': 'context_search_returns_placeholder',
    'purchase_returns': 'context_search_purchase_returns_placeholder',
    'manufacturing': 'context_search_manufacturing_placeholder',
    'users': 'context_search_users_placeholder',
    'audit_log': 'context_search_audit_log_placeholder',
    'offline_queue': 'context_search_offline_queue_placeholder',
    'monitoring': 'context_search_monitoring_placeholder',
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
    'offline_queue': 'الإدارة',
    'monitoring': 'الإدارة',
    'restaurant': 'المطعم',
}



class IconMenuBar(QWidget):
    """Icon-first business navigation bar with text below icons.

    It intentionally mimics the small subset of QMenuBar used by MainWindow:
    clear(), addMenu(), setLayoutDirection(), setFixedHeight(), setStyleSheet().
    Each top-level entry is a QToolButton with ToolButtonTextUnderIcon. The
    dashboard/home entry keeps the icon only by design.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('IconMenuBar')
        self._buttons = []
        self._menus = []
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(12, 4, 12, 5)
        self._layout.setSpacing(6)
        self._layout.addStretch(1)

    def clear(self):
        for btn in self._buttons:
            btn.setParent(None)
            btn.deleteLater()
        for menu in self._menus:
            menu.deleteLater()
        self._buttons.clear()
        self._menus.clear()
        # Keep the trailing stretch as the last layout item.
        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def addMenu(self, icon, title):
        label = str(title or '').replace('\n', '').strip()
        is_home = label in {'الرئيسية', translate('home_breadcrumb'), translate('dashboard')}
        menu = QMenu(self)
        btn = QToolButton(self)
        btn.setObjectName('MainNavToolButton')
        btn.setCursor(Qt.PointingHandCursor)
        btn.setIcon(icon)
        btn.setIconSize(QSize(32, 32))
        btn.setText('' if is_home else label)
        btn.setToolTip(label or translate('dashboard'))
        btn.setToolButtonStyle(Qt.ToolButtonIconOnly if is_home else Qt.ToolButtonTextUnderIcon)
        btn.setPopupMode(QToolButton.InstantPopup)
        btn.setMenu(menu)
        btn.setMinimumWidth(74 if is_home else 92)
        btn.setMinimumHeight(64)
        self._layout.insertWidget(max(0, self._layout.count() - 1), btn)
        self._buttons.append(btn)
        self._menus.append(menu)
        return menu

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

        self.menu_bar = IconMenuBar(self)
        self.menu_bar.setStyleSheet("""
            QWidget#IconMenuBar { background-color: palette(window); border-bottom: 1px solid palette(mid); }
            QToolButton#MainNavToolButton {
                background: transparent;
                border: none;
                border-radius: 12px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 800;
                color: palette(text);
            }
            QToolButton#MainNavToolButton:hover {
                background: palette(alternate-base);
            }
            QToolButton#MainNavToolButton::menu-indicator { image: none; width: 0px; }
        """)
        self.menu_bar.setFixedHeight(74)
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
            ('restaurant', RestaurantDashboard),
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
        self.menu_bar.setFixedHeight(74)
        self.menu_bar.setStyleSheet("""
            QWidget#IconMenuBar {
                background-color: palette(window);
                border-bottom: 1px solid palette(mid);
            }
            QToolButton#MainNavToolButton {
                background: transparent;
                border: none;
                border-radius: 12px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 800;
                color: palette(text);
            }
            QToolButton#MainNavToolButton:hover {
                background: palette(alternate-base);
            }
            QToolButton#MainNavToolButton::menu-indicator { image: none; width: 0px; }
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

        home_menu = self.menu_bar.addMenu(qta.icon('fa5s.home'), '\n' + translate('home_breadcrumb'))
        add_action(home_menu, translate('dashboard'), 'tachometer-alt', 'dashboard', shortcut='F1')
        add_action(home_menu, translate('pos'), 'barcode', 'pos', shortcut='F2')
        add_action(home_menu, translate('restaurant.dashboard'), 'utensils', 'restaurant', shortcut='F8')
        home_menu.addSeparator()
        add_action(home_menu, translate('monitoring'), 'heartbeat', 'monitoring')

        sales_menu = self.menu_bar.addMenu(qta.icon('fa5s.shopping-cart'), '\n' + translate('nav_sales'))
        add_action(sales_menu, translate('pos'), 'barcode', 'pos', shortcut='F2')
        add_action(sales_menu, translate('sales_invoices'), 'file-invoice-dollar', 'sales_invoices', shortcut='F3')
        add_action(sales_menu, translate('sales_returns'), 'undo', 'returns')
        sales_menu.addSeparator()
        add_action(sales_menu, translate('receipt_voucher'), 'hand-holding-usd', 'vouchers')

        restaurant_menu = self.menu_bar.addMenu(qta.icon('fa5s.utensils'), '\n' + translate('nav_restaurant'))
        add_action(restaurant_menu, translate('restaurant.dashboard'), 'utensils', 'restaurant', shortcut='F8')
        add_action(restaurant_menu, translate('restaurant.open_table'), 'door-open', 'restaurant')
        add_action(restaurant_menu, translate('restaurant.kitchen_ticket'), 'receipt', 'restaurant')

        purchase_menu = self.menu_bar.addMenu(qta.icon('fa5s.truck'), '\n' + translate('nav_purchases'))
        add_action(purchase_menu, translate('purchase_invoices'), 'file-invoice', 'purchase_invoices')
        add_action(purchase_menu, translate('purchase_returns'), 'undo-alt', 'purchase_returns')
        purchase_menu.addSeparator()
        add_action(purchase_menu, translate('payment_voucher'), 'money-bill-wave', 'vouchers')

        inventory_menu = self.menu_bar.addMenu(qta.icon('fa5s.boxes'), '\n' + translate('nav_inventory'))
        add_action(inventory_menu, translate('items'), 'box', 'items', shortcut='F4')
        add_action(inventory_menu, translate('categories'), 'folder', 'categories')
        add_action(inventory_menu, translate('warehouses'), 'warehouse', 'warehouses', shortcut='F5')

        manufacturing_menu = self.menu_bar.addMenu(qta.icon('fa5s.industry'), '\n' + translate('nav_manufacturing'))
        add_action(manufacturing_menu, translate('nav_manufacturing'), 'industry', 'manufacturing')

        parties_menu = self.menu_bar.addMenu(qta.icon('fa5s.users'), '\n' + translate('nav_parties'))
        add_action(parties_menu, translate('customers'), 'user-friends', 'customers')
        add_action(parties_menu, translate('suppliers'), 'truck-loading', 'suppliers')

        finance_menu = self.menu_bar.addMenu(qta.icon('fa5s.wallet'), '\n' + translate('nav_finance'))
        add_action(finance_menu, translate('cashboxes'), 'cash-register', 'cashboxes')
        add_action(finance_menu, translate('vouchers'), 'receipt', 'vouchers')

        reports_menu = self.menu_bar.addMenu(qta.icon('fa5s.chart-line'), '\n' + translate('reports'))
        add_action(reports_menu, translate('reports'), 'chart-line', 'reports')
        add_action(reports_menu, translate('customer_statement'), 'user', 'reports')
        add_action(reports_menu, translate('supplier_statement'), 'truck', 'reports')
        add_action(reports_menu, translate('ledger_reconciliation'), 'balance-scale', 'reports')

        admin_menu = self.menu_bar.addMenu(qta.icon('fa5s.cog'), '\n' + translate('nav_admin'))
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
            users_menu = self.menu_bar.addMenu(qta.icon('fa5s.user-shield'), '\n' + translate('nav_users'))
            add_action(users_menu, translate('users'), 'users-cog', 'users')
            add_action(users_menu, translate('audit_log'), 'history', 'audit_log')

        quick_menu = self.menu_bar.addMenu(qta.icon('fa5s.bolt'), '\n' + translate('quick_actions'))
        add_action(quick_menu, translate('new_sales_invoice'), 'file-invoice-dollar', callback=lambda: self.open_quick_invoice('sale'), shortcut='Ctrl+N')
        add_action(quick_menu, translate('new_purchase_invoice'), 'file-invoice', callback=lambda: self.open_quick_invoice('purchase'))
        add_action(quick_menu, translate('receipt_voucher'), 'hand-holding-usd', callback=lambda: self.open_quick_voucher('receipt'))
        add_action(quick_menu, translate('payment_voucher'), 'money-bill-wave', callback=lambda: self.open_quick_voucher('payment'))
        quick_menu.addSeparator()
        add_action(quick_menu, translate('new_customer'), 'user-plus', callback=self.open_quick_customer)
        add_action(quick_menu, translate('new_supplier'), 'truck-loading', callback=self.open_quick_supplier)
        add_action(quick_menu, translate('new_item'), 'box-open', callback=self.open_quick_item)

    def setup_topbar_buttons(self):
        """Wire utility-strip actions only.

        Primary navigation is now in setup_menus(). This avoids duplicated menu
        rows and keeps the shell visually clean.
        """
        self._global_search_timer = QTimer(self)
        self._global_search_timer.setSingleShot(True)
        self._global_search_timer.setInterval(220)
        self._global_search_timer.timeout.connect(self._apply_global_filter)
        self.top_bar.search_box.textChanged.connect(lambda _text: self._global_search_timer.start())
        self.top_bar.search_box.returnPressed.connect(self.global_search)
        self.top_bar.theme_btn.clicked.connect(self.toggle_theme)
        self.top_bar.alert_btn.clicked.connect(self.show_alerts_menu)
        if hasattr(self.top_bar, 'refresh_btn'):
            self.top_bar.refresh_btn.clicked.connect(self.refresh_current_view)
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


    def refresh_current_view(self):
        """Refresh current page from the shell utility button."""
        page = self.stack.currentWidget() if hasattr(self, 'stack') else None
        refreshed = False
        for method_name in ('refresh_all', 'refresh', 'load_data'):
            if page is not None and hasattr(page, method_name):
                try:
                    getattr(page, method_name)()
                    refreshed = True
                    break
                except Exception as exc:
                    QMessageBox.warning(self, translate('warning'), f"{translate('refresh_now')}: {exc}")
                    return
        try:
            self.update_badges()
        except Exception:
            pass
        if not refreshed and hasattr(self.pages.get('dashboard'), 'refresh_all'):
            self.pages['dashboard'].refresh_all()

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

    def _refresh_page_if_loaded(self, page_key):
        try:
            page = self.pages.get(page_key) if hasattr(self, 'pages') else None
            if page and hasattr(page, 'refresh_all'):
                page.refresh_all()
            elif page and hasattr(page, 'refresh'):
                page.refresh()
        except Exception:
            pass

    def open_quick_invoice(self, inv_type):
        try:
            from views.dialogs.invoice_dialog import InvoiceDialog
            dialog = InvoiceDialog(inv_type, self)
            if dialog.exec():
                self._refresh_page_if_loaded('sales_invoices' if inv_type == 'sale' else 'purchase_invoices')
        except Exception as exc:
            QMessageBox.warning(self, translate('quick_actions'), str(exc))

    def open_quick_item(self):
        try:
            from views.dialogs.item_dialog import ItemDialog
            dialog = ItemDialog(self)
            if dialog.exec():
                self._refresh_page_if_loaded('items')
        except Exception as exc:
            QMessageBox.warning(self, translate('quick_actions'), str(exc))

    def open_quick_customer(self):
        try:
            from views.dialogs.add_entity_dialog import AddEntityDialog
            dialog = AddEntityDialog(self, 'sale')
            if dialog.exec():
                self._refresh_page_if_loaded('customers')
        except Exception as exc:
            QMessageBox.warning(self, translate('quick_actions'), str(exc))

    def open_quick_supplier(self):
        try:
            from views.dialogs.add_entity_dialog import AddEntityDialog
            dialog = AddEntityDialog(self, 'purchase')
            if dialog.exec():
                self._refresh_page_if_loaded('suppliers')
        except Exception as exc:
            QMessageBox.warning(self, translate('quick_actions'), str(exc))

    def open_quick_voucher(self, voucher_type='receipt'):
        try:
            from views.widgets.vouchers_widget import VoucherDialog
            dialog = VoucherDialog(self)
            if hasattr(dialog, 'type_combo'):
                dialog.type_combo.setCurrentIndex(0 if voucher_type == 'receipt' else 1)
            if dialog.exec():
                self._refresh_page_if_loaded('vouchers')
        except Exception as exc:
            QMessageBox.warning(self, translate('quick_actions'), str(exc))

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
        self.restaurant_shortcut = QShortcut(QKeySequence('F8'), self)
        self.restaurant_shortcut.activated.connect(lambda: self.switch_page('restaurant'))
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

    def _current_page_id(self):
        current = self.stack.currentWidget() if hasattr(self, 'stack') else None
        for pid, widget in getattr(self, 'pages', {}).items():
            if widget is current:
                return pid
        return None

    def _page_supports_global_filter(self, page):
        if page is None:
            return False
        return (
            hasattr(page, 'set_global_filter')
            or hasattr(page, 'search_edit')
            or hasattr(page, 'sales_search')
            or hasattr(page, 'purchases_search')
            or hasattr(page, 'toolbar')
            or hasattr(page, 'barcode_input')
        )

    def _update_global_search_context(self, pid):
        box = getattr(getattr(self, 'top_bar', None), 'search_box', None)
        if box is None:
            return
        page = self.pages.get(pid) if hasattr(self, 'pages') else None
        supported = pid in GLOBAL_SEARCH_PLACEHOLDERS and self._page_supports_global_filter(page)
        box.blockSignals(True)
        try:
            box.clear()
            box.setVisible(bool(supported))
            box.setEnabled(bool(supported))
            if supported:
                box.setPlaceholderText(translate(GLOBAL_SEARCH_PLACEHOLDERS.get(pid, 'global_search_placeholder')))
            else:
                box.setPlaceholderText('')
        finally:
            box.blockSignals(False)

    def _apply_global_filter(self):
        pid = self._current_page_id()
        if not pid or pid not in GLOBAL_SEARCH_PLACEHOLDERS:
            return
        page = self.pages.get(pid)
        text = self.top_bar.search_box.text().strip()
        if page is None:
            return
        if hasattr(page, 'set_global_filter'):
            page.set_global_filter(text)
            return
        for attr in ('search_edit', 'sales_search', 'purchases_search'):
            field = getattr(page, attr, None)
            if field is not None and hasattr(field, 'setText'):
                if field.text() != text:
                    field.setText(text)
                elif hasattr(page, 'refresh'):
                    page.refresh()
                return
        toolbar = getattr(page, 'toolbar', None)
        field = getattr(toolbar, 'search_edit', None) if toolbar is not None else None
        if field is not None and hasattr(field, 'setText'):
            if field.text() != text:
                field.setText(text)
            elif hasattr(page, 'refresh'):
                page.refresh()
            return
        barcode = getattr(page, 'barcode_input', None)
        if barcode is not None and hasattr(barcode, 'setText'):
            barcode.setText(text)
            barcode.setFocus()

    def global_search(self):
        self._apply_global_filter()

    def show_global_search(self, text=None):
        if text is not None and hasattr(self.top_bar, 'search_box'):
            self.top_bar.search_box.setText(text)
        self._apply_global_filter()

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
            self._update_global_search_context(pid)
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


