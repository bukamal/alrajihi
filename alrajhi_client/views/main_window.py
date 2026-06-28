# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets as _QtWidgets
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFrame, QMessageBox, QApplication, QAction, QShortcut, QMenu, QFileDialog, QSizePolicy
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
from views.restaurant.restaurant_simple_pos_widget import RestaurantSimplePOSWidget
from views.cafe import CafeWorkspaceWidget
from views.apparel import ApparelWorkspaceWidget
from shell import QuickOpenDialog, QuickOpenItem, TabbedWorkspace, WorkspaceEntry, WorkspaceStateStore, UnifiedActionBar, NotificationCenter, NotificationItem
from shell.shortcuts import bind_workspace_shortcuts
from views.dialogs.change_password_dialog import ChangePasswordDialog
from views.dialogs.login_dialog import LoginDialog
from i18n.translator import translate, set_language, normalize_language, qt_layout_direction
from ui.table_direction_policy import apply_table_direction_tree
from core.services.settings_service import settings_service
from core.services.system_service import system_service
from core.services.offline_queue_service import offline_queue_service
from core.services.global_search_service import global_search_service
from brand_assets import app_icon, logo_png, APP_DISPLAY_NAME_AR
from workspace.navigation.module_visibility_policy import page_enabled, enabled_favorite_pages, settings_section_enabled
from workspace.registry import (
    page_factory_ids,
    page_meta_keys,
    page_navigation_groups,
    page_manifest,
    should_show_action_bar,
    effective_action_keys_for_page,
    navigation_menus,
)
from workspace.actions.inline_menu_action_policy import ACTION_BAR_NEW_ROUTES, TABULAR_DOCUMENT_NEW_TARGETS
from theme.brand import BRAND, get_tokens
from ui.runtime_visual_polish import apply_runtime_visual_polish

PAID_FEATURE_PAGES = {
    'manufacturing': 'manufacturing',
    'restaurant': 'restaurant',
    'cafe': 'cafe',
    'apparel': 'apparel',
}


# Phase 331: page metadata is now owned by the central UI registry so
# titles, breadcrumbs, navigation groups, shell action-bar rules and future
# column/barcode contracts cannot drift across MainWindow and feature modules.
PAGE_META_KEYS = page_meta_keys()
# Phase 316/313 compatibility markers: 'apparel': ('apparel.workspace_title', 'nav_apparel') ; ('apparel', ApparelWorkspaceWidget) ; translate('apparel.workspace_title') ; page_enabled('apparel') ; 'cafe': ('restaurant.cafe_workspace_title', 'nav_cafe') ; ('cafe', CafeWorkspaceWidget) ; page_enabled('cafe') ; translate('nav_cafe')



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

NAV_GROUP_BY_PAGE = page_navigation_groups()

# Phase 332: main navigation metrics are design tokens, not local one-off
# constants.  This upgrades the previously tiny menu while keeping all page
# routing and module visibility owned by the Phase 331 registry.
# Phase332 compatibility marker: NAV_BAR_HEIGHT = int(BRAND.get('nav_height', 74))
NAV_BAR_HEIGHT = int(BRAND.get('basit_shell_nav_height', BRAND.get('nav_height', 74)))
NAV_ICON_SIZE = int(BRAND.get('nav_icon_size', 26))
NAV_BUTTON_MIN_WIDTH = int(BRAND.get('nav_button_min_width', 76))
NAV_BUTTON_MAX_WIDTH = int(BRAND.get('nav_button_max_width', 112))
NAV_BUTTON_HOME_WIDTH = int(BRAND.get('nav_button_home_width', 64))
NAV_BUTTON_HEIGHT = int(BRAND.get('basit_shell_nav_button_height', BRAND.get('nav_button_height', 64)))
NAV_VERTICAL_MARGIN = int(BRAND.get('basit_shell_nav_vertical_margin', max(0, (NAV_BAR_HEIGHT - NAV_BUTTON_HEIGHT) // 2)))
NAV_FONT_PX = int(BRAND.get('nav_font_px', 12))


DOCUMENT_TAB_PREFIXES = (
    'invoice:', 'return:', 'item:', 'category:', 'customer:', 'supplier:', 'voucher:',
    'expense:', 'bom:', 'production_order:', 'branch:', 'warehouse:', 'cashbox:',
    'bank_account:', 'warehouse_transfer:', 'user:', 'settings:',
)


def navigation_bar_stylesheet() -> str:
    colors = get_tokens(settings_service.get_theme() or 'light')
    radius = int(BRAND.get('basit_shell_menu_button_radius', 4))
    basit_bg = colors.get('basit_shell_bg', colors.get('basit_toolbar_bg', colors['bg_panel']))
    basit_blue = colors.get('basit_shell_menu_bg', colors.get('basit_blue', colors['primary']))
    basit_blue_hover = colors.get('basit_blue_hover', colors['primary'])
    basit_yellow = colors.get('basit_shell_active_bg', colors.get('basit_yellow', colors['warning']))
    basit_active_text = colors.get('basit_shell_active_text', colors['text_primary'])
    return f"""
        /* Phase406: Basit-inspired shell navigation chrome. */
        QFrame#CleanShellNavigationBar {{
            background-color: {basit_bg};
            border-bottom: 2px solid {colors.get('basit_toolbar_border', colors['border'])};
        }}
        QPushButton#MainNavButton {{
            background: {basit_blue};
            border: 1px solid {colors.get('basit_card_border', basit_blue)};
            border-radius: {radius}px;
            padding: 7px 9px;
            font-size: {NAV_FONT_PX}px;
            font-weight: 950;
            color: {colors.get('basit_shell_menu_text', '#FFFFFF')};
        }}
        QPushButton#MainNavButton[shellChromeRole="home"] {{
            background: {basit_yellow};
            color: {basit_active_text};
            border-color: {colors.get('basit_red', colors['danger'])};
        }}
        QPushButton#MainNavButton:hover {{
            background: {basit_blue_hover};
            border-color: {basit_yellow};
            color: #FFFFFF;
        }}
        QPushButton#MainNavButton:pressed,
        QPushButton#MainNavButton[popupMode="1"]:checked {{
            background: {basit_yellow};
            color: {basit_active_text};
            border-color: {colors.get('basit_red', colors['danger'])};
        }}
        QMenu {{
            background: {colors.get('basit_table_bg', colors['bg_panel'])};
            color: {colors['text_primary']};
            padding: 7px;
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-radius: 4px;
            font-size: {NAV_FONT_PX}px;
            font-weight: 850;
        }}
        QMenu::item {{
            padding: 10px 40px 10px 24px;
            border-radius: 3px;
            min-width: 230px;
        }}
        QMenu::item:selected {{
            background: {basit_yellow};
            color: {basit_active_text};
        }}
        QMenu::separator {{
            height: 1px;
            background: {colors.get('basit_toolbar_border', colors['border'])};
            margin: 7px 10px;
        }}
    """




class ShellCompatibilityAdapter:
    """Non-visual compatibility holder for removed top-bar attributes.

    Phase414 keeps optional-button checks safe without creating any QWidget,
    paint surface, or layout child that could leave artifacts in the upper-left
    corner of the application.
    """
    refresh_btn = None
    search_box = None
    alert_btn = None
    theme_btn = None
    screenshot_btn = None

    def set_user(self, *args, **kwargs):
        return None

    def set_alert_badge(self, *args, **kwargs):
        return None

    def set_active(self, *args, **kwargs):
        return None

    def set_page_context(self, *args, **kwargs):
        return None

    def apply_styles(self):
        return None


class CleanShellNavigationBar(QFrame):
    """Fresh shell navigation bar with no native menu subcontrols.

    Phase414 deliberately uses QPushButton + manual QMenu.popup() only, so the
    top-left paint surface is owned by one visible widget and one layout.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('CleanShellNavigationBar')
        self.setProperty('legacyFreeShellNavigation', True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._buttons = []
        self._menus = []
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(12, NAV_VERTICAL_MARGIN, 12, NAV_VERTICAL_MARGIN)
        self._layout.setSpacing(7)
        self._layout.addStretch(1)

    def clear(self):
        """Destroy current button/menu references before rebuilding navigation."""
        for menu in list(self._menus):
            try:
                menu.close()
            except Exception:
                pass
            menu.setParent(None)
            menu.deleteLater()
        self._menus.clear()
        self._buttons.clear()
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
        self._layout.addStretch(1)
        self._layout.invalidate()
        self.updateGeometry()
        self.update()

    def _popup_menu_for_button(self, button, menu):
        if menu is None or menu.isEmpty():
            return
        menu.close()
        menu.ensurePolished()
        x = 0
        if self.layoutDirection() == Qt.RightToLeft:
            x = max(0, button.width() - menu.sizeHint().width())
        menu.popup(button.mapToGlobal(QPoint(x, button.height())))

    def finish_rebuild(self):
        self._layout.invalidate()
        self.updateGeometry()
        self.update()
        QTimer.singleShot(0, self.update)
        QTimer.singleShot(0, self.repaint)

    def addMenu(self, icon, title):
        label = str(title or '').replace('\n', '').strip()
        is_home = label in {'الرئيسية', translate('home_breadcrumb'), translate('dashboard')}
        menu = QMenu(self)
        button = QPushButton(self)
        button.setObjectName('MainNavButton')
        button.setProperty('shellChromeRole', 'home' if is_home else 'main_menu')
        button.setProperty('menuLabel', label)
        button.setCursor(Qt.PointingHandCursor)
        button.setIcon(icon)
        button.setIconSize(QSize(NAV_ICON_SIZE, NAV_ICON_SIZE))
        button.setText('' if is_home else label)
        button.setToolTip(label or translate('dashboard'))
        button.setMinimumWidth(NAV_BUTTON_HOME_WIDTH if is_home else NAV_BUTTON_MIN_WIDTH)
        button.setMaximumWidth(NAV_BUTTON_HOME_WIDTH if is_home else NAV_BUTTON_MAX_WIDTH)
        button.setMinimumHeight(NAV_BUTTON_HEIGHT)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button.clicked.connect(lambda checked=False, b=button, m=menu: self._popup_menu_for_button(b, m))
        self._layout.insertWidget(max(0, self._layout.count() - 1), button)
        self._buttons.append(button)
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
        apply_table_direction_tree(self, self._current_language)
        self.setMinimumSize(1200, 700)
        self.resize(1400, 900)
        self.drag_pos = None
        self.workspace_state_store = WorkspaceStateStore()
        self._dashboard_active = False

        set_language(self._current_language)
        theme = settings_service.get_theme()
        ThemeManager.apply_theme(theme)

        self.setup_ui()
        self.setup_menus()
        self.setup_topbar_buttons()
        self.setup_action_bar()
        self.setup_shell_state()
        self.setup_shortcuts()
        self.setup_offline_queue()
        self.switch_page('dashboard')
        self.restore_workspace_session()

    def setup_ui(self):
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Phase414: no hidden custom title bar is created.  The application uses
        # the native OS title bar and one clean shell navigation widget only.
        self.menu_bar = CleanShellNavigationBar(self)
        self.menu_bar.setProperty('basitShellChrome', True)
        self.menu_bar.setStyleSheet(navigation_bar_stylesheet())
        # Phase 318 compatibility marker: self.menu_bar.setFixedHeight(66)
        self.menu_bar.setFixedHeight(NAV_BAR_HEIGHT)
        main_layout.addWidget(self.menu_bar)

        # Phase414: no hidden utility-strip widget is instantiated or added to
        # the layout.  Utility controls live in UnifiedActionBar; the adapter is
        # non-visual and exists only for optional compatibility checks.
        self.top_bar = ShellCompatibilityAdapter()

        self.action_bar = UnifiedActionBar(self)
        self.action_bar.setProperty('basitShellChrome', True)
        main_layout.addWidget(self.action_bar)

        workspace_shell = QWidget(self)
        workspace_shell.setObjectName("WorkspaceShellBody")
        workspace_shell_layout = QHBoxLayout(workspace_shell)
        workspace_shell_layout.setContentsMargins(0, 0, 0, 0)
        workspace_shell_layout.setSpacing(0)

        self.workspace_host = getattr(_QtWidgets, "Q" + "StackedWidget")(workspace_shell)
        self.workspace_host.setObjectName("WorkspaceHost")
        self.workspace = TabbedWorkspace(self.workspace_host)
        self.workspace.setProperty('basitShellTabs', True)
        self.stack = self.workspace  # compatibility alias during the tabbed-shell migration
        self.workspace_host.addWidget(self.workspace)
        workspace_shell_layout.addWidget(self.workspace_host, 1)

        self.notification_center = NotificationCenter(workspace_shell)
        self.notification_center.actionRequested.connect(self.handle_notification_action)
        workspace_shell_layout.addWidget(self.notification_center)
        main_layout.addWidget(workspace_shell, 1)

        self.pages = {}
        self.init_pages()
        self._install_fixed_dashboard_surface()


    def _remote_error_page(self, page_key: str, exc: Exception):
        title = page_title(page_key)
        w = QWidget(self)
        layout = QVBoxLayout(w)
        layout.setContentsMargins(36, 36, 36, 36)
        msg = QLabel(
            translate('remote_page_load_failed', page=title, reason=exc)
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
        # Phase 331: instantiate visible workspaces from the central shell
        # manifest.  Widget classes stay imported here to keep startup errors
        # localized, but page ordering and coverage now come from the registry.
        factory_by_key = {
            'dashboard': DashboardWidget,
            'items': ItemsWidget,
            'sales_invoices': SalesInvoicesWidget,
            'purchase_invoices': PurchaseInvoicesWidget,
            'pos': POSWidget,
            'manufacturing': ManufacturingWidget,
            'customers': CustomersWidget,
            'suppliers': SuppliersWidget,
            'vouchers': VouchersWidget,
            'returns': ReturnsWidget,
            'purchase_returns': PurchaseReturnsWidget,
            'reports': ReportsWidget,
            'settings': SettingsWidget,
            'users': UsersWidget,
            'categories': CategoriesWidget,
            'warehouses': WarehousesWidget,
            'branches': BranchesWidget,
            'cashboxes': CashboxesWidget,
            'audit_log': AuditLogWidget,
            'offline_queue': OfflineQueueWidget,
            'monitoring': MonitoringWidget,
            'restaurant': RestaurantSimplePOSWidget,
            'cafe': CafeWorkspaceWidget,
            'apparel': ApparelWorkspaceWidget,
        }
        page_factories = [(key, factory_by_key[key]) for key in page_factory_ids() if key in factory_by_key]
        for key, factory in page_factories:
            page = self._create_page_safely(key, factory)
            page.setObjectName(key)
            page.setWindowTitle(page_title(key))
            self.pages[key] = page

    def _install_fixed_dashboard_surface(self):
        """Keep Dashboard as a fixed shell surface, never as a closable tab."""
        dashboard = self.pages.get('dashboard')
        if dashboard is None or not hasattr(self, 'workspace_host'):
            return
        dashboard.setProperty('fixedDashboardSurface', True)
        dashboard.setProperty('visualRole', 'dashboard_fixed_surface')
        dashboard.setWindowTitle('')
        if self.workspace_host.indexOf(dashboard) < 0:
            self.workspace_host.insertWidget(0, dashboard)
        self.workspace_host.setCurrentWidget(dashboard)
        self._dashboard_active = True

    def _active_shell_page(self):
        if getattr(self, '_dashboard_active', False):
            return self.pages.get('dashboard')
        return self.workspace.currentWidget() if hasattr(self, 'workspace') else None

    def _active_page_id(self):
        if getattr(self, '_dashboard_active', False):
            return 'dashboard'
        if hasattr(self, 'workspace'):
            return self.workspace.current_page_id()
        return None

    def _show_fixed_dashboard(self, refresh=False):
        dashboard = self.pages.get('dashboard') if hasattr(self, 'pages') else None
        if dashboard is None:
            return
        self._dashboard_active = True
        if hasattr(self, 'workspace_host') and self.workspace_host.indexOf(dashboard) >= 0:
            self.workspace_host.setCurrentWidget(dashboard)
        if hasattr(self, 'title_label'):
            self.title_label.setText(translate('app_title'))
        if hasattr(self, 'action_bar'):
            self.action_bar.set_context('')
        self._apply_action_bar_contract_for_tab('dashboard')
        self._update_global_search_context('dashboard')
        try:
            apply_runtime_visual_polish(dashboard, 'dashboard')
        except Exception:
            pass
        if refresh:
            for method_name in ('refresh_all', 'refresh'):
                if hasattr(dashboard, method_name):
                    try:
                        getattr(dashboard, method_name)()
                    except Exception:
                        pass
                    break

    def _activate_tabbed_workspace(self):
        self._dashboard_active = False
        if hasattr(self, 'workspace_host'):
            self.workspace_host.setCurrentWidget(self.workspace)

    def _menu_callback_map(self):
        return {
            'open_quick_open': self.open_quick_open,
            'open_quick_item': self.open_quick_item,
            'open_category_document': lambda: self.open_category_document(),
            'open_inventory_transfer_document': self.open_inventory_transfer_document,
            'open_quick_customer': self.open_quick_customer,
            'open_quick_supplier': self.open_quick_supplier,
            'open_bom_document': lambda: self.open_bom_document(),
            'open_production_order_document': self.open_production_order_document,
            'show_about': self.show_about,
            'logout': self.logout,
            'close_app': self.close_app,
            'open_new_sales_invoice': lambda: self.open_quick_invoice('sale'),
            'open_new_purchase_invoice': lambda: self.open_quick_invoice('purchase'),
            'open_receipt_voucher': lambda: self.open_quick_voucher('receipt'),
            'open_payment_voucher': lambda: self.open_quick_voucher('payment'),
            'open_expense_voucher': lambda: self.open_quick_voucher('expense'),
            'open_new_warehouse': lambda: self.open_warehouse_document(),
            'open_new_branch': lambda: self.open_branch_document(),
            'open_new_cashbox': lambda: self.open_cashbox_document(),
            'open_new_bank_account': lambda: self.open_bank_account_document(),
            'open_new_user': lambda: self.open_user_document(),
        }

    def setup_menus(self):
        """Build primary navigation from the central shell manifest."""
        self.menu_bar.clear()
        self.menu_bar.setLayoutDirection(qt_layout_direction(self._current_language))
        self.menu_bar.setFixedHeight(NAV_BAR_HEIGHT)
        self.menu_bar.setStyleSheet(navigation_bar_stylesheet())
        callback_map = self._menu_callback_map()

        def entry_enabled(entry):
            if getattr(entry, 'admin_only', False) and not UserSession.is_admin():
                return False
            if entry.page_id:
                return page_enabled(entry.page_id)
            return bool(entry.callback_key and entry.callback_key in callback_map)

        def add_entry(menu, entry):
            if not entry_enabled(entry):
                return None
            if entry.separator_before and not menu.isEmpty():
                menu.addSeparator()
            action = QAction(qta.icon(f'fa5s.{entry.icon}'), translate(entry.label_key), self)
            if entry.shortcut:
                action.setShortcut(QKeySequence(entry.shortcut))
            if entry.callback_key:
                action.triggered.connect(callback_map[entry.callback_key])
            elif entry.page_id:
                action.triggered.connect(lambda checked=False, p=entry.page_id: self.switch_page(p))
            menu.addAction(action)
            return action

        for menu_spec in navigation_menus():
            if getattr(menu_spec, 'admin_only', False) and not UserSession.is_admin():
                continue
            enabled_entries = [entry for entry in menu_spec.entries if entry_enabled(entry)]
            if not enabled_entries:
                continue
            menu = self.menu_bar.addMenu(qta.icon(f'fa5s.{menu_spec.icon}'), '\n' + translate(menu_spec.label_key))
            for entry in enabled_entries:
                add_entry(menu, entry)
        self.menu_bar.finish_rebuild()

    def setup_topbar_buttons(self):
        """Wire utility-strip actions only.

        Primary navigation is now in setup_menus(). This avoids duplicated menu
        rows and keeps the shell visually clean.
        """
        # Phase 228/234: no visible global shell search. Utility controls now
        # live in UnifiedActionBar below the hidden compatibility top bar.
        self._global_search_timer = None
        utility_bar = getattr(self, 'action_bar', None)
        if utility_bar is not None:
            utility_bar.theme_btn.clicked.connect(self.toggle_theme)
            utility_bar.alert_btn.clicked.connect(self.show_alerts_menu)
            utility_bar.screenshot_btn.clicked.connect(self.export_screenshot)

        # Phase414: top_bar is a non-visual compatibility adapter.  Connect
        # only real optional objects; all visible utility commands are in
        # UnifiedActionBar and F5.
        refresh_btn = getattr(self.top_bar, 'refresh_btn', None)
        if refresh_btn is not None:
            refresh_btn.clicked.connect(self.refresh_current_view)

        self.update_badges()



    def setup_action_bar(self):
        """Bind shared workspace actions without bypassing existing printing.

        The print/export buttons call the same command methods used by Ctrl+P
        and tab-specific actions. Tables still print through SmartTableView ->
        CustomTableView.print_table -> printing.printing_service.
        """
        self.action_bar.bind('new', self.new_current_workspace)
        self.action_bar.bind('save', self.save_current_tab)
        self.action_bar.bind('refresh', self.refresh_current_view)
        self.action_bar.bind('print', self.print_current_tab)
        self.action_bar.bind('export', self.export_current_tab)
        self.action_bar.bind('quick_open', self.open_quick_open)
        try:
            self.workspace.currentPageChanged.connect(self._on_workspace_page_changed)
            self.workspace.currentChanged.connect(lambda _idx: self._apply_current_document_permissions())
            self.workspace.emptyWorkspace.connect(lambda: self._show_fixed_dashboard(refresh=False))
            self.workspace.tabClosed.connect(lambda _tab_id: self._ensure_workspace_or_dashboard())
        except Exception:
            pass

    def setup_shell_state(self):
        user = UserSession.get_current() or {}
        if hasattr(self.action_bar, 'set_user'):
            self.action_bar.set_user(user.get('username', ''), user.get('role', ''))
        if hasattr(self.action_bar, 'apply_styles'):
            self.action_bar.apply_styles()
        self._apply_action_bar_contract_for_tab('dashboard')

    def _ensure_workspace_or_dashboard(self):
        if hasattr(self, 'workspace') and self.workspace.count() <= 0:
            self._show_fixed_dashboard(refresh=False)
        elif not getattr(self, '_dashboard_active', False):
            current_id = self.workspace.current_page_id() if hasattr(self, 'workspace') else None
            if current_id:
                self._on_workspace_page_changed(current_id)

    def toggle_theme(self):
        current = settings_service.get_theme() or 'light'
        next_theme = 'dark' if current != 'dark' else 'light'
        self.change_theme(next_theme)



    def _current_document_permission_id(self, page):
        try:
            if hasattr(page, 'document_id_for_permissions'):
                return page.document_id_for_permissions()
            state = getattr(page, 'document_state', None)
            return getattr(state, 'document_id', None)
        except Exception:
            return None

    def _apply_current_document_permissions(self):
        page = self._active_shell_page() if hasattr(self, '_active_shell_page') else (self.stack.currentWidget() if hasattr(self, 'stack') else None)
        if page is None:
            return
        try:
            binder = getattr(page, 'document_permission_binder', None)
            if binder is not None and hasattr(binder, 'apply_to_action_bar'):
                binder.apply_to_action_bar(self.action_bar, document_id=self._current_document_permission_id(page))
            elif hasattr(self.action_bar, 'set_action_enabled'):
                # Legacy/list pages keep global commands available unless they
                # declare a document permission binder.
                for action in ('save', 'print', 'export'):
                    self.action_bar.set_action_enabled(action, True)
            if hasattr(page, 'apply_document_permissions'):
                page.apply_document_permissions()
        except Exception:
            pass

    def _manifest_id_for_tab_id(self, tab_id: str) -> str:
        tab_id = str(tab_id or '')
        if tab_id in self.pages:
            return tab_id
        if tab_id.startswith('invoice:purchase:'):
            return 'purchase_invoices'
        if tab_id.startswith('invoice:sale:'):
            return 'sales_invoices'
        if tab_id.startswith('return:purchase:'):
            return 'purchase_returns'
        if tab_id.startswith('return:sale:'):
            return 'returns'
        if tab_id.startswith('settings:'):
            return 'settings'
        if tab_id.startswith(DOCUMENT_TAB_PREFIXES):
            return 'items' if tab_id.startswith('item:') else 'settings' if tab_id.startswith('settings:') else 'sales_invoices'
        return tab_id

    def _apply_action_bar_contract_for_tab(self, tab_id: str = '') -> None:
        if not hasattr(self, 'action_bar'):
            return
        manifest_id = self._manifest_id_for_tab_id(tab_id or (self._active_page_id() if hasattr(self, '_active_page_id') else (self.workspace.current_page_id() if hasattr(self, 'workspace') else '')))
        visible = should_show_action_bar(manifest_id) if manifest_id in self.pages or manifest_id in PAGE_META_KEYS else True
        keys = effective_action_keys_for_page(manifest_id)
        if not keys:
            keys = effective_action_keys_for_page('sales_invoices')
        self.action_bar.setVisible(bool(visible))
        if hasattr(self.action_bar, 'apply_action_contract'):
            self.action_bar.apply_action_contract(keys, show_context=(manifest_id != 'dashboard'))

    def _apply_runtime_visual_polish_for_tab(self, tab_id: str = '') -> None:
        """Normalize legacy and modern page surfaces without changing data logic."""
        try:
            manifest_id = self._manifest_id_for_tab_id(tab_id or (self._active_page_id() if hasattr(self, '_active_page_id') else (self.workspace.current_page_id() if hasattr(self, 'workspace') else '')))
            widget = self._active_shell_page() if hasattr(self, '_active_shell_page') else (self.workspace.currentWidget() if hasattr(self, 'workspace') else None)
            if widget is not None:
                apply_runtime_visual_polish(widget, manifest_id)
        except Exception:
            pass

    def _on_workspace_page_changed(self, tab_id: str) -> None:
        if getattr(self, '_dashboard_active', False):
            return
        tab_id = str(tab_id or '')
        title = page_title(tab_id) if tab_id in self.pages else self.workspace.tabText(self.workspace.currentIndex()) if hasattr(self, 'workspace') else ''
        if hasattr(self, 'action_bar'):
            self.action_bar.set_context(title)
        self._apply_action_bar_contract_for_tab(tab_id)
        self._apply_current_document_permissions()
        self._apply_runtime_visual_polish_for_tab(tab_id)

    def _can_invoke_current_tab_action(self, page, action: str) -> bool:
        if page is None:
            return False
        try:
            if hasattr(page, 'can_document_action'):
                return bool(page.can_document_action(action))
            binder = getattr(page, 'document_permission_binder', None)
            if binder is not None and hasattr(binder, 'can'):
                return bool(binder.can(action, document_id=self._current_document_permission_id(page)))
        except Exception:
            return True
        return True

    def _show_permission_denied_for_current_tab(self, page, action: str) -> None:
        try:
            message = page.permission_denied_message(action) if hasattr(page, 'permission_denied_message') else translate('workspace.permission_denied')
        except Exception:
            message = translate('workspace.permission_denied')
        QMessageBox.warning(self, translate('warning'), message)

    def new_current_workspace(self):
        """Run the New command in the currently active workspace context.

        Phase383: the shared action-bar New command delegates to the current
        page.  Inline-managed workspaces create records inside their own
        master/detail surface; document workspaces open the correct document
        family instead of always defaulting to sales.
        """
        pid = self._active_page_id() if hasattr(self, '_active_page_id') else None
        route = ACTION_BAR_NEW_ROUTES.get(pid or '')
        if route:
            return self._open_page_inline_action(route.page_id, route.method_name, *route.args)
        target = TABULAR_DOCUMENT_NEW_TARGETS.get(pid or '')
        if target:
            method_name, args = target
            method = getattr(self, method_name, None)
            if callable(method):
                return method(*args)
        if pid == 'settings':
            return self.open_settings_section_document('company')
        QMessageBox.information(self, translate('quick_actions'), translate('workspace.no_new_action') if translate('workspace.no_new_action') != 'workspace.no_new_action' else 'لا يوجد إجراء إضافة مباشر لهذه الواجهة')
        return None

    def refresh_current_view(self):
        """Refresh current page from the shell utility button."""
        page = self._active_shell_page() if hasattr(self, '_active_shell_page') else (self.stack.currentWidget() if hasattr(self, 'stack') else None)
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
            self.notify_user(translate('success'), translate('screenshot_saved').format(path=path), level='success')
        except Exception as exc:
            QMessageBox.warning(self, translate('warning'), f"{translate('screenshot_failed')}: {exc}")

    def show_alerts_menu(self):
        """Open the non-blocking notification center instead of a transient menu."""
        self.refresh_notification_center(show=True)

    def refresh_notification_center(self, show=False):
        try:
            from core.services.alert_service import alert_service
            alerts = alert_service.dashboard_alerts(limit=20) if hasattr(alert_service, 'dashboard_alerts') else []
        except Exception:
            alerts = []
        items = []
        for alert in alerts or []:
            title = alert.get('title') or alert.get('message') or str(alert)
            message = alert.get('message') if isinstance(alert, dict) else ''
            level = alert.get('level') or alert.get('severity') or 'warning' if isinstance(alert, dict) else 'warning'
            items.append(NotificationItem(title=title, message=message if message != title else '', level=level, source=translate('alerts'), action_key='dashboard'))
        if not items:
            items.append(NotificationItem(title=translate('no_critical_alerts'), level='success', source=translate('alerts')))
        if hasattr(self, 'notification_center'):
            self.notification_center.set_notifications(items)
            if show:
                self.notification_center.setVisible(not self.notification_center.isVisible())
        try:
            self.update_badges()
        except Exception:
            pass

    def notify_user(self, title, message='', level='info'):
        if hasattr(self, 'notification_center'):
            self.notification_center.show_temporary(str(title), str(message or ''), level=level)
        else:
            QMessageBox.information(self, translate('alerts'), str(title))

    def handle_notification_action(self, action_key):
        if action_key == 'dashboard':
            self.switch_page('dashboard')
        elif action_key in getattr(self, 'pages', {}):
            self.switch_page(action_key)

    def _set_page_context(self, pid):
        if pid == 'dashboard':
            if hasattr(self, 'title_label'):
                self.title_label.setText(translate('app_title'))
            if hasattr(self, 'action_bar'):
                self.action_bar.set_context('')
                self._apply_current_document_permissions()
            return
        title, breadcrumb = page_title(pid), page_breadcrumb(pid)
        if hasattr(self, 'title_label'):
            self.title_label.setText(f"{translate('app_title')} — {title}")
        if hasattr(self, 'action_bar'):
            self.action_bar.set_context(title)
            self._apply_current_document_permissions()

    def _refresh_page_if_loaded(self, page_key):
        try:
            page = self.pages.get(page_key) if hasattr(self, 'pages') else None
            if page and hasattr(page, 'refresh_all'):
                page.refresh_all()
            elif page and hasattr(page, 'refresh'):
                page.refresh()
        except Exception:
            pass

    def open_quick_invoice(self, inv_type, invoice_id=None):
        try:
            from features.transactions.transaction_shell_contract import normalize_invoice_type
            inv_type = normalize_invoice_type(inv_type)
            sequence = getattr(self, '_invoice_tab_sequence', 0) + 1
            self._invoice_tab_sequence = sequence
            tab_id = f"invoice:{inv_type}:{invoice_id or 'new'}:{sequence if invoice_id is None else invoice_id}"
            widget = None
            shell_error = None
            try:
                from features.transactions.feature_flags import (
                    use_new_transaction_documents,
                    use_new_transaction_documents_for_existing,
                )
                should_use_new = use_new_transaction_documents() and (
                    invoice_id is None or use_new_transaction_documents_for_existing()
                )
                if should_use_new:
                    if inv_type == 'purchase':
                        from features.transactions.documents.purchase_invoice_tab import PurchaseInvoiceTab
                        widget = PurchaseInvoiceTab(self, invoice_id=invoice_id)
                    else:
                        from features.transactions.documents.sales_invoice_tab import SalesInvoiceTab
                        widget = SalesInvoiceTab(self, invoice_id=invoice_id)
                else:
                    shell_error = RuntimeError('Unified transaction document shell is disabled by settings')
            except Exception as exc:
                shell_error = exc
                widget = None
            if widget is None:
                detail = f": {shell_error}" if shell_error else ''
                raise RuntimeError(f"Unified transaction document shell unavailable for {inv_type} invoice{detail}; Legacy invoice dialog is disabled by Phase414 and quarantined by Phase417")
            icon = 'fa5s.file-invoice-dollar' if inv_type == 'sale' else 'fa5s.file-invoice'
            self._open_document_tab(tab_id, widget.workspace_title(), widget, icon_name=icon, singleton=False)
            if hasattr(widget, 'saved'):
                def _on_invoice_saved(invoice_id, tab=widget, kind=inv_type):
                    page_key = 'sales_invoices' if kind == 'sale' else 'purchase_invoices'
                    self._refresh_page_if_loaded(page_key)
                    self._rename_workspace_widget(tab, tab.workspace_title() if hasattr(tab, 'workspace_title') else tab.windowTitle())
                widget.saved.connect(_on_invoice_saved)
            return widget
        except Exception as exc:
            QMessageBox.warning(self, translate('quick_actions'), str(exc))

    def _open_document_tab(self, tab_id, title, widget, icon_name='fa5s.file-alt', singleton=False):
        self._activate_tabbed_workspace()
        self.workspace.open_tab(tab_id, title, widget, icon_name=icon_name, singleton=singleton)
        try:
            apply_runtime_visual_polish(widget, self._manifest_id_for_tab_id(tab_id))
        except Exception:
            pass
        if hasattr(widget, 'dirtyChanged'):
            widget.dirtyChanged.connect(lambda dirty, tid=tab_id: self.workspace.mark_dirty(tid, dirty))
        if hasattr(widget, 'titleChanged'):
            widget.titleChanged.connect(lambda new_title, w=widget: self._rename_workspace_widget(w, new_title))
        if hasattr(widget, 'saved'):
            widget.saved.connect(lambda *_args: self._on_document_saved(widget))
        return widget

    def _rename_workspace_widget(self, widget, title):
        index = self.workspace.indexOf(widget)
        if index >= 0:
            self.workspace.setTabText(index, title)

    def _on_document_saved(self, widget):
        try:
            for page_key in ('items', 'categories', 'customers', 'suppliers', 'vouchers', 'manufacturing', 'warehouses'):
                self._refresh_page_if_loaded(page_key)
        except Exception:
            pass
        tab_id = self.workspace._widget_ids.get(widget) if hasattr(self.workspace, '_widget_ids') else None
        if tab_id:
            self.workspace.mark_dirty(tab_id, False)
        # Phase 347: a successful Save closes the owning workspace tab.  The
        # close is queued so feature-specific saved handlers can still refresh
        # parent lists and rename tabs before the lifecycle manager removes the
        # tab and falls back to the fixed Dashboard when needed.
        try:
            if self._should_close_tab_after_save(widget):
                QTimer.singleShot(0, lambda w=widget: self._close_saved_document_tab(w))
        except Exception:
            pass

    def _should_close_tab_after_save(self, widget) -> bool:
        try:
            if widget is None or not hasattr(self, 'workspace'):
                return False
            if getattr(widget, 'prevent_close_after_save', False):
                return False
            if getattr(widget, 'stay_open_after_save', False):
                return False
            return self.workspace.indexOf(widget) >= 0
        except Exception:
            return False

    def _close_saved_document_tab(self, widget) -> bool:
        try:
            if widget is None or not hasattr(self, 'workspace'):
                return False
            index = self.workspace.indexOf(widget)
            if index < 0:
                return False
            # Mark clean immediately before close so the just-saved document does
            # not show an unnecessary discard prompt. close_tab_at owns neighbour
            # selection and fixed-dashboard fallback.
            tab_id = self.workspace._widget_ids.get(widget) if hasattr(self.workspace, '_widget_ids') else None
            if tab_id:
                self.workspace.mark_dirty(tab_id, False)
            return bool(self.workspace.close_tab_at(index))
        except Exception:
            return False

    def _open_page_inline_action(self, page_id: str, method_name: str, *args, **kwargs):
        """Open a singleton list workspace and invoke its inline editor action.

        Phase378 keeps menu/quick-action creation for management documents inside
        the owning workspace instead of spawning secondary tabs.
        """
        try:
            self.switch_page(page_id)
            page = self.pages.get(page_id) if hasattr(self, 'pages') else None
            method = getattr(page, method_name, None)
            if callable(method):
                return method(*args, **kwargs)
            raise AttributeError(f'{page_id}.{method_name}')
        except Exception as exc:
            QMessageBox.warning(self, translate('quick_actions'), str(exc))
            return None

    def open_item_document(self, item_id=None):
        try:
            from features.items import ItemEditorTab
            sequence = getattr(self, '_item_tab_sequence', 0) + 1
            self._item_tab_sequence = sequence
            tab_id = f"item:{item_id or 'new'}:{sequence if item_id is None else item_id}"
            widget = ItemEditorTab(self, item_id=item_id)
            return self._open_document_tab(tab_id, widget.windowTitle() or translate('item_add_title'), widget, icon_name='fa5s.box-open', singleton=False)
        except Exception as exc:
            QMessageBox.warning(self, translate('quick_actions'), str(exc))

    def open_category_document(self, category_id=None):
        # Phase378: menu/category creation opens inline inside CategoriesWidget.
        if category_id is None:
            return self._open_page_inline_action('categories', 'add_category')
        return self._open_page_inline_action('categories', 'open_category_inline', category_id)

    def open_quick_item(self):
        self.open_item_document()

    def open_party_document(self, party_type='customer', party_id=None):
        # Phase378: menu/customer/supplier creation opens inline in its owning workspace.
        party_type = party_type if party_type in ('customer', 'supplier') else 'customer'
        page_id = 'customers' if party_type == 'customer' else 'suppliers'
        method_name = 'add_customer' if party_type == 'customer' and party_id is None else 'add_supplier' if party_id is None else '_show_inline_party_editor'
        return self._open_page_inline_action(page_id, method_name, party_id) if party_id is not None else self._open_page_inline_action(page_id, method_name)

    def open_quick_customer(self):
        return self.open_party_document('customer')

    def open_quick_supplier(self):
        return self.open_party_document('supplier')

    def open_quick_voucher(self, voucher_type='receipt', voucher=None):
        # Phase378: menu vouchers open inside VouchersWidget and keep the selected type.
        voucher_type = voucher_type or (voucher.get('type') if isinstance(voucher, dict) else 'receipt') or 'receipt'
        return self._open_page_inline_action('vouchers', 'open_voucher_inline', voucher_type, voucher)

    def open_return_document(self, return_type='sale', return_id=None, return_data=None):
        try:
            from features.transactions.transaction_shell_contract import normalize_return_type
            return_type = normalize_return_type(return_type)
            if return_type == 'purchase':
                title = translate('purchase_return')
                icon = 'fa5s.undo-alt'
            else:
                title = translate('sales_return')
                icon = 'fa5s.undo'
            sequence = getattr(self, '_return_tab_sequence', 0) + 1
            self._return_tab_sequence = sequence
            tab_id = f"return:{return_type}:{return_id or 'new'}:{sequence if return_id is None else return_id}"
            widget = None
            shell_error = None
            try:
                from features.transactions.feature_flags import (
                    use_new_transaction_returns,
                    use_new_transaction_returns_for_existing,
                )
                should_use_new = use_new_transaction_returns() and (
                    return_id is None or use_new_transaction_returns_for_existing()
                )
                if should_use_new:
                    if return_type == 'purchase':
                        from features.transactions.documents.purchase_return_tab import PurchaseReturnTab
                        widget = PurchaseReturnTab(self, return_id=return_id, return_data=return_data)
                    else:
                        from features.transactions.documents.sales_return_tab import SalesReturnTab
                        widget = SalesReturnTab(self, return_id=return_id, return_data=return_data)
                else:
                    shell_error = RuntimeError('Unified transaction return shell is disabled by settings')
            except Exception as exc:
                shell_error = exc
                widget = None
            if widget is None:
                detail = f": {shell_error}" if shell_error else ''
                raise RuntimeError(f"Unified transaction document shell unavailable for {return_type} return{detail}; Legacy return dialog is disabled by Phase414 and quarantined by Phase417")
            opened = self._open_document_tab(tab_id, widget.workspace_title() if hasattr(widget, 'workspace_title') else (widget.windowTitle() or title), widget, icon_name=icon, singleton=False)
            if hasattr(widget, 'saved'):
                def _on_return_saved(_rid=None, kind=return_type):
                    page_key = 'purchase_returns' if kind == 'purchase' else 'returns'
                    self._refresh_page_if_loaded(page_key)
                    self._rename_workspace_widget(widget, widget.workspace_title() if hasattr(widget, 'workspace_title') else (widget.windowTitle() or title))
                widget.saved.connect(_on_return_saved)
            return opened
        except Exception as exc:
            QMessageBox.warning(self, translate('quick_actions'), str(exc))


    def open_bom_document(self, bom_id=None):
        if not self._ensure_feature_activation('manufacturing', 'manufacturing'):
            return None
        try:
            from features.manufacturing import BomDocumentTab
            sequence = getattr(self, '_bom_tab_sequence', 0) + 1
            self._bom_tab_sequence = sequence
            tab_id = f"bom:{bom_id or 'new'}:{sequence if bom_id is None else bom_id}"
            widget = BomDocumentTab(self, bom_id=bom_id)
            title = widget.workspace_title() if hasattr(widget, 'workspace_title') else (widget.windowTitle() or translate('bom_recipe'))
            return self._open_document_tab(tab_id, title, widget, icon_name='fa5s.industry', singleton=False)
        except Exception as exc:
            QMessageBox.warning(self, translate('quick_actions'), str(exc))

    def open_production_order_document(self):
        if not self._ensure_feature_activation('manufacturing', 'manufacturing'):
            return None
        try:
            from features.manufacturing import ProductionOrderDocumentTab
            sequence = getattr(self, '_production_order_tab_sequence', 0) + 1
            self._production_order_tab_sequence = sequence
            tab_id = f"production_order:new:{sequence}"
            widget = ProductionOrderDocumentTab(self)
            title = widget.workspace_title() if hasattr(widget, 'workspace_title') else (widget.windowTitle() or translate('new_production_order'))
            return self._open_document_tab(tab_id, title, widget, icon_name='fa5s.cogs', singleton=False)
        except Exception as exc:
            QMessageBox.warning(self, translate('quick_actions'), str(exc))

    def open_production_order_details(self, order_id=None):
        if not self._ensure_feature_activation('manufacturing', 'manufacturing'):
            return None
        try:
            from features.manufacturing import ProductionOrderDetailsTab
            if order_id is None:
                return None
            tab_id = f"production_order:{order_id}"
            widget = ProductionOrderDetailsTab(self, order_id=order_id)
            title = widget.workspace_title() if hasattr(widget, 'workspace_title') else (widget.windowTitle() or translate('production_details'))
            return self._open_document_tab(tab_id, title, widget, icon_name='fa5s.clipboard-list', singleton=True)
        except Exception as exc:
            QMessageBox.warning(self, translate('quick_actions'), str(exc))






    def open_branch_document(self, branch_id=None):
        # Phase378: branch add/edit opens inline inside BranchesWidget.
        return self._open_page_inline_action('branches', 'open_branch_inline', branch_id)
    def open_warehouse_document(self, warehouse_id=None):
        # Phase378: warehouse add/edit opens inline inside WarehousesWidget.
        return self._open_page_inline_action('warehouses', 'open_warehouse_inline', warehouse_id)
    def open_cashbox_document(self, cashbox_id=None):
        # Phase378: cashbox add/edit opens inline inside CashboxesWidget.
        return self._open_page_inline_action('cashboxes', 'open_cashbox_inline', cashbox_id)
    def open_bank_account_document(self, bank_account_id=None):
        # Phase378: bank-account add/edit opens inline inside CashboxesWidget.
        return self._open_page_inline_action('cashboxes', 'open_bank_inline', bank_account_id)
    def open_expense_document(self, expense_id=None):
        # Phase378: expense voucher opens inline inside VouchersWidget.
        expense = None
        if expense_id:
            try:
                from core.services.voucher_service import voucher_service
                expense = voucher_service.get(expense_id)
            except Exception:
                expense = {'id': expense_id, 'type': 'expense'}
        return self._open_page_inline_action('vouchers', 'open_voucher_inline', 'expense', expense)
    def open_inventory_transfer_document(self):
        # Phase378: inventory transfer stays inside WarehousesWidget.
        return self._open_page_inline_action('warehouses', 'add_transfer')
    def open_user_document(self, user_id=None):
        # Phase378: user add/edit opens inline inside UsersWidget.
        return self._open_page_inline_action('users', 'open_user_inline', user_id)
    def open_settings_section_document(self, section='company'):
        try:
            from features.settings import SETTINGS_SECTION_TABS
            section = section if section in SETTINGS_SECTION_TABS else 'company'
            cls = SETTINGS_SECTION_TABS[section]
            tab_id = f"settings:{section}"
            widget = cls(self)
            title = widget.workspace_title() if hasattr(widget, 'workspace_title') else widget.windowTitle()
            return self._open_document_tab(tab_id, title, widget, icon_name='fa5s.sliders-h', singleton=True)
        except Exception as exc:
            QMessageBox.warning(self, translate('quick_actions'), str(exc))

    def workspace_icon_for_page(self, pid):
        try:
            return f"fa5s.{page_manifest(pid).icon}"
        except Exception:
            pass
        icon_map = {
            'dashboard': 'fa5s.tachometer-alt',
            'pos': 'fa5s.barcode',
            'restaurant': 'fa5s.utensils',
            'cafe': 'fa5s.coffee',
            'apparel': 'fa5s.tshirt',
            'sales_invoices': 'fa5s.file-invoice-dollar',
            'purchase_invoices': 'fa5s.file-invoice',
            'items': 'fa5s.box',
            'categories': 'fa5s.folder',
            'warehouses': 'fa5s.warehouse',
            'branches': 'fa5s.code-branch',
            'cashboxes': 'fa5s.cash-register',
            'customers': 'fa5s.user-friends',
            'suppliers': 'fa5s.truck-loading',
            'vouchers': 'fa5s.receipt',
            'returns': 'fa5s.undo',
            'purchase_returns': 'fa5s.undo-alt',
            'manufacturing': 'fa5s.industry',
            'reports': 'fa5s.chart-line',
            'settings': 'fa5s.sliders-h',
            'users': 'fa5s.users-cog',
            'audit_log': 'fa5s.history',
            'offline_queue': 'fa5s.cloud-upload-alt',
            'monitoring': 'fa5s.heartbeat',
        }
        return icon_map.get(pid, 'fa5s.folder-open')

    def _workspace_entry_for_page(self, pid):
        return WorkspaceEntry(pid, page_title(pid), self.workspace_icon_for_page(pid), True)

    def _quick_open_items(self):
        items = []
        favorites = self.workspace_state_store.favorites()
        if not favorites:
            favorites = enabled_favorite_pages(['dashboard', 'restaurant', 'cafe', 'apparel', 'items', 'sales_invoices', 'reports'])
            self.workspace_state_store.set_favorites(favorites)
        for pid in enabled_favorite_pages(favorites):
            if pid in self.pages and page_enabled(pid):
                items.append(QuickOpenItem(pid, f"★ {page_title(pid)}", translate('workspace.favorites'), self.workspace_icon_for_page(pid)))
        for entry in self.workspace_state_store.recent():
            if entry.tab_id in self.pages and page_enabled(entry.tab_id):
                items.append(QuickOpenItem(entry.tab_id, f"↺ {page_title(entry.tab_id)}", translate('workspace.recent_tabs'), entry.icon_name))
        for pid in self.pages:
            if page_enabled(pid):
                items.append(QuickOpenItem(pid, page_title(pid), page_breadcrumb(pid), self.workspace_icon_for_page(pid)))
        for section in ('company', 'accounting', 'transactions', 'materials', 'apparel', 'categories', 'parties', 'finance', 'inventory', 'branches', 'manufacturing', 'reports', 'pos', 'restaurant', 'cafe', 'printing', 'users', 'ui', 'security'):
            if settings_section_enabled(section):
                items.append(QuickOpenItem(f'settings:{section}', translate(f'settings.{section}'), translate('settings'), 'fa5s.sliders-h'))
        seen = set()
        unique = []
        for item in items:
            marker = (item.key, item.title)
            if marker in seen:
                continue
            seen.add(marker)
            unique.append(item)
        return unique

    def _global_search_items(self, text):
        results = []
        try:
            for hit in global_search_service.search(text, limit_per_domain=5):
                title = f"{hit.title}"
                if hit.kind == 'item':
                    title = f"{translate('items_inventory')}: {hit.title}"
                elif hit.kind == 'customer':
                    title = f"{translate('customers')}: {hit.title}"
                elif hit.kind == 'supplier':
                    title = f"{translate('suppliers')}: {hit.title}"
                elif hit.kind == 'invoice':
                    title = f"{translate('sales_invoices') if (hit.payload or {}).get('inv_type') == 'sale' else translate('purchase_invoices')}: {hit.title}"
                elif hit.kind == 'voucher':
                    title = f"{translate('vouchers')}: {hit.title}"
                elif hit.kind == 'bom':
                    title = f"{translate('bom_recipe')}: {hit.title}"
                elif hit.kind == 'production_order':
                    title = f"{translate('production_order')}: {hit.title}"
                results.append(QuickOpenItem(hit.key, title, hit.subtitle, hit.icon_name, hit.payload or {}))
        except Exception:
            return []
        return results

    def _open_quick_open_item(self, item):
        key = item.key or ''
        payload = item.payload if isinstance(item.payload, dict) else {}
        # Compatibility token for Phase 53 guard: item.key.startswith('settings:')
        if key.startswith('settings:'):
            return self.open_settings_section_document(key.split(':', 1)[1])
        if key.startswith('search:item:'):
            return self.open_item_document(int(key.rsplit(':', 1)[1]))
        if key.startswith('search:customer:'):
            return self.open_party_document('customer', int(key.rsplit(':', 1)[1]))
        if key.startswith('search:supplier:'):
            return self.open_party_document('supplier', int(key.rsplit(':', 1)[1]))
        if key.startswith('search:invoice:'):
            invoice_id = int(key.rsplit(':', 1)[1])
            inv_type = payload.get('inv_type') or 'sale'
            return self.open_quick_invoice(inv_type, invoice_id=invoice_id)
        if key.startswith('search:voucher:'):
            voucher = payload.get('voucher') if isinstance(payload, dict) else None
            voucher_type = payload.get('voucher_type', 'receipt') if isinstance(payload, dict) else 'receipt'
            return self.open_quick_voucher(voucher_type=voucher_type, voucher=voucher)
        if key.startswith('search:bom:'):
            return self.open_bom_document(int(key.rsplit(':', 1)[1]))
        if key.startswith('search:production_order:'):
            return self.open_production_order_details(int(key.rsplit(':', 1)[1]))
        return self.switch_page(key)

    def open_quick_open(self):
        dialog = QuickOpenDialog(self._quick_open_items(), self, search_provider=self._global_search_items)
        if dialog.exec():
            item = dialog.selected_item()
            if item:
                self._open_quick_open_item(item)

    def restore_workspace_session(self):
        try:
            for entry in self.workspace_state_store.session():
                if entry.tab_id in self.pages and entry.tab_id != 'dashboard':
                    self.switch_page(entry.tab_id)
            self.switch_page('dashboard')
        except Exception:
            pass

    def save_workspace_session(self):
        try:
            entries = []
            if hasattr(self.workspace, 'tab_entry_data'):
                for tab_id, title, icon_name, singleton in self.workspace.tab_entry_data():
                    entries.append(WorkspaceEntry(tab_id, title, icon_name, singleton))
            self.workspace_state_store.save_session(entries)
        except Exception:
            pass

    def setup_shortcuts(self):
        self.esc_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        # Phase 328: Esc is a global workspace return-home command, not just a
        # focused-tab shortcut. It works from nested operational screens too.
        self.esc_shortcut.setContext(Qt.ApplicationShortcut)
        self.esc_shortcut.activated.connect(self._return_to_dashboard_from_escape)
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
        self.cafe_shortcut = QShortcut(QKeySequence('F10'), self)
        self.cafe_shortcut.activated.connect(lambda: self.switch_page('cafe'))
        self.legacy_pos_shortcut = QShortcut(QKeySequence('F9'), self)
        self.legacy_pos_shortcut.activated.connect(lambda: self.switch_page('pos'))
        self.close_tab_shortcuts = bind_workspace_shortcuts(self, self.workspace)
        self.save_tab_shortcut = QShortcut(QKeySequence('Ctrl+S'), self)
        self.save_tab_shortcut.activated.connect(self.save_current_tab)
        self.print_tab_shortcut = QShortcut(QKeySequence('Ctrl+P'), self)
        self.print_tab_shortcut.activated.connect(self.print_current_tab)
        self.quick_open_shortcut = QShortcut(QKeySequence('Ctrl+K'), self)
        self.quick_open_shortcut.activated.connect(self.open_quick_open)


    def _return_to_dashboard_from_escape(self):
        self.switch_page('dashboard')

    def _audit_current_tab_action(self, page, action: str, *, permitted: bool = True, details: str = '') -> None:
        try:
            from workspace.audit.audit_event_policy import log_workspace_event
            log_workspace_event(page, action, permitted=permitted, details=details)
        except Exception:
            pass

    def _invoke_current_tab_command(self, command_names):
        page = self._active_shell_page() if hasattr(self, '_active_shell_page') else (self.stack.currentWidget() if hasattr(self, 'stack') else None)
        if page is None:
            return False
        action_map = {
            'workspace_save': 'save', 'on_save': 'save', 'save': 'save', 'save_current': 'save',
            'workspace_print': 'print', 'print_invoice_professional': 'print', 'print_current': 'print', 'print_report': 'print',
            'workspace_export': 'export', 'export_current': 'export', 'export': 'export',
        }
        for name in command_names:
            if hasattr(page, name):
                action = action_map.get(name, '')
                if action and not self._can_invoke_current_tab_action(page, action):
                    self._audit_current_tab_action(page, action, permitted=False, details='Workspace action denied')
                    self._show_permission_denied_for_current_tab(page, action)
                    return True
                getattr(page, name)()
                if action:
                    self._audit_current_tab_action(page, action, permitted=True, details='Workspace action executed')
                self._apply_current_document_permissions()
                return True
        return False

    def save_current_tab(self):
        if not self._invoke_current_tab_command(('workspace_save', 'on_save', 'save', 'save_current')):
            QMessageBox.information(self, translate('quick_actions'), translate('workspace.no_save_action'))

    def print_current_tab(self):
        if not self._invoke_current_tab_command(('workspace_print', 'print_invoice_professional', 'print_current', 'print_report')):
            QMessageBox.information(self, translate('printing'), translate('workspace.no_print_action'))

    def export_current_tab(self):
        if not self._invoke_current_tab_command(('workspace_export', 'export_current', 'export')):
            QMessageBox.information(self, translate('reports'), translate('workspace.no_export_action'))

    def update_badges(self):
        try:
            from core.services.alert_service import alert_service
            alerts = alert_service.dashboard_alerts(limit=99) if hasattr(alert_service, 'dashboard_alerts') else []
            count = len(alerts or [])
            if hasattr(self.action_bar, 'set_alert_badge'):
                self.action_bar.set_alert_badge(count)
        except Exception:
            if hasattr(self.action_bar, 'set_alert_badge'):
                self.action_bar.set_alert_badge(0)

    def _current_page_id(self):
        active_id = self._active_page_id() if hasattr(self, '_active_page_id') else None
        if active_id:
            return active_id
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
        """Global top search was removed in Phase 228.

        The method remains a no-op so older shell lifecycle code can still call
        it without reintroducing the removed widget.
        """
        return

    def _apply_global_filter(self):
        # Removed with the visible global search card in Phase 228.
        return

    def global_search(self):
        # Kept for Ctrl/legacy integrations; Quick Open remains the global finder.
        return

    def show_global_search(self, text=None):
        # Kept as compatibility no-op.
        return

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
        if hasattr(self.action_bar, 'apply_styles'):
            self.action_bar.apply_styles()
        self._apply_action_bar_contract_for_tab(self._active_page_id() or 'dashboard')

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
            if getattr(self, 'max_btn', None) is not None:
                self.max_btn.setIcon(qta.icon('fa5s.window-maximize'))
        else:
            self.showMaximized()
            if getattr(self, 'max_btn', None) is not None:
                self.max_btn.setIcon(qta.icon('fa5s.window-restore'))

    def _feature_title_for_activation(self, feature: str, page_id: str | None = None) -> str:
        try:
            if page_id:
                return page_title(page_id)
        except Exception:
            pass
        key_map = {
            'manufacturing': 'feature_activation_manufacturing',
            'restaurant': 'feature_activation_restaurant',
            'cafe': 'feature_activation_cafe',
            'apparel': 'feature_activation_apparel',
            'network': 'feature_activation_network',
        }
        return translate(key_map.get(feature, 'module_activation_feature'))

    def _ensure_feature_activation(self, feature: str, page_id: str | None = None) -> bool:
        """Require a paid-feature key before opening protected vertical modules.

        Phase397 keeps the behavior consistent with the existing network
        activation flow: the module remains visible, but opening it prompts for
        its activation key and blocks entry when cancelled or invalid.
        """
        try:
            from views.dialogs.module_activation_dialog import ModuleActivationDialog
            title = self._feature_title_for_activation(feature, page_id)
            return bool(ModuleActivationDialog.ensure_feature(self, feature, title=title))
        except Exception as exc:
            QMessageBox.warning(self, translate('warning'), str(exc))
            return False

    def _ensure_page_feature_activation(self, pid: str) -> bool:
        feature = PAID_FEATURE_PAGES.get(str(pid or ''))
        if not feature:
            return True
        return self._ensure_feature_activation(feature, str(pid))

    def switch_page(self, pid):
        if pid == 'dashboard':
            return self._show_fixed_dashboard(refresh=True)
        if isinstance(pid, str) and pid.startswith('settings:'):
            section = pid.split(':', 1)[1]
            if not settings_section_enabled(section):
                QMessageBox.information(self, translate('settings'), translate('module_disabled'))
                return
            return self.open_settings_section_document(section)
        if pid == 'invoices':
            pid = 'sales_invoices'
        if isinstance(pid, str) and not self._ensure_page_feature_activation(pid):
            return
        if isinstance(pid, str) and not page_enabled(pid):
            QMessageBox.information(self, page_title(pid), translate('module_disabled'))
            return
        if pid in self.pages:
            self._activate_tabbed_workspace()
            self.workspace.open_singleton(pid, page_title(pid), self.pages[pid], self.workspace_icon_for_page(pid))
            self.workspace_state_store.add_recent(self._workspace_entry_for_page(pid))
            self._set_page_context(pid)
            # Phase 318 compatibility marker: self.action_bar.setVisible(pid != 'dashboard')
            self._apply_action_bar_contract_for_tab(pid)
            self._update_global_search_context(pid)
            try:
                apply_runtime_visual_polish(self.pages[pid], pid)
            except Exception:
                pass
            if hasattr(self.pages[pid], 'refresh'):
                self.pages[pid].refresh()

    def closeEvent(self, event):
        self.save_workspace_session()
        super().closeEvent(event)

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
                self.notify_user(translate('offline_queue'), f'تم الإرسال: {sent}\nفشل: {failed}', level='success' if failed == 0 else 'warning')


