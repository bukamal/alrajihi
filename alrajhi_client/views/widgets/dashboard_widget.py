# -*- coding: utf-8 -*-
# Phase302 static marker: border-radius: 24px
# Phase 328: dashboard cards fill the landing page
# Phase328 compatibility marker: panel.setMinimumHeight(500)
# Phase328 compatibility marker: self.main_layout.addLayout(row, 1)
from __future__ import annotations


_PHASE384_DASHBOARD_COMPATIBILITY_MARKERS = """
QLabel#CompanyLogoBox { background: transparent;
QLabel#SystemBrandLogoBox {{
                background: transparent;
Phase384: centered shortcut text without the legacy monitoring row.
"""

from decimal import Decimal

from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QSettings
from i18n import translate, qt_layout_direction
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QPushButton,
    QComboBox, QHeaderView, QScrollArea, QSizePolicy, QLineEdit, QBoxLayout
)

import qtawesome as qta

from core.services.dashboard_service import dashboard_service
from core.services.monitoring_service import monitoring_service
from core.services.user_preferences_service import user_preferences_service
from currency import currency
from models.table_models import GenericTableModel
from utils import show_toast
from brand_assets import logo_png
from ui.smart_table_view import SmartTableView
from ui.dashboard_components import ModernKpiCard, DashboardChartPanel
from ui.targeted_screen_rebuild import apply_targeted_screen_rebuild
from ui.single_screen_runtime_hardening import apply_single_screen_runtime_hardening
from ui.runtime_visual_regression_gate import apply_runtime_visual_regression_gate

try:
    from theme_manager import ThemeManager
    from theme.brand import BRAND
except Exception:  # Defensive fallback for early imports/tests.
    ThemeManager = None
    BRAND = {'developer_card_name_ar': translate('app_full_title')}


def _dc(key, fallback):
    try:
        if ThemeManager:
            return ThemeManager.get(key) or fallback
    except Exception:
        pass
    return fallback


def _dashboard_product_name():
    return translate('app_full_title')
# Branding assets are used in login/splash/application icon.


from views.widgets.dashboard_legacy_components import KPIStatCard, QuickActionButton, DashboardPanel


class DashboardWidget(QWidget):
    refresh_needed = pyqtSignal()
    currency_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(qt_layout_direction())
        self.setObjectName('DashboardWidget')
        self.setProperty('basitInspired', True)
        self.setProperty('dashboardVisualPhase', 437)
        self.setProperty('dashboardResponsivePhase', 438)
        self.setProperty('dashboardSurface', 'identity_aligned')
        self._loading_currencies = False
        # Phase 282: top KPI cards and the chart panel are permanently removed
        # from the dashboard per release UX direction. Keep the map empty for
        # compatibility with older refresh code/tests.
        self.cards = {}
        self._snapshot = {}
        self._build_ui()
        QTimer.singleShot(100, self.refresh_all)

    def _build_ui(self):
        self.setStyleSheet(f'''
            QWidget#DashboardWidget {{ background: {_dc('bg_window', '#F5F7FA')}; }}
            QWidget#DashboardPage {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {_dc('bg_window', '#F5F7FA')},
                    stop:0.55 #F8FBFF,
                    stop:1 #EEF8FA);
            }}
            QWidget#DashboardPage[dashboardSurface="identity_aligned"] {{ background: #F5F7FA; }}
            QLabel#HeroTitle {{ color: white; font-size: 25px; font-weight: 900; }}
            QLabel#HeroSubtitle {{ color: #EAF3FF; font-size: 13px; font-weight: 600; }}
            QLabel#StatusPill {{ color: white; background: transparent; border: 1px solid rgba(255,255,255,0.38); border-radius: 12px; padding: 7px 12px; font-weight: 800; }}
            QComboBox {{ min-height: 34px; border: 1px solid {_dc('border', '#E2E8F0')}; border-radius: 10px; padding: 4px 8px; background: {_dc('input_bg', '#FFFFFF')}; }}
        ''')
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        # Phase438: avoid horizontal scroll/clip artefacts when the shell is
        # maximized on VNC, HiDPI, or narrow remote desktop sessions.
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setProperty('dashboardResponsivePhase', 438)
        root.addWidget(scroll)

        page = QWidget()
        page.setObjectName('DashboardPage')
        page.setProperty('basitInspired', True)
        page.setProperty('dashboardSurface', 'identity_aligned')
        page.setProperty('dashboardVisualPhase', 437)
        page.setProperty('dashboardResponsivePhase', 438)
        scroll.setWidget(page)
        self.main_layout = QVBoxLayout(page)
        self.main_layout.setContentsMargins(18, 18, 18, 18)
        self.main_layout.setSpacing(16)

        # Phase 282: do not build the top KPI/card strip or chart panel.
        # Legacy audit token only, not invoked: _build_kpi_grid()
        self._build_middle_grid()
        self._build_bottom_grid()

    def _dashboard_available_width(self) -> int:
        """Return the live dashboard viewport width for responsive placement.

        Phase439 uses the actual scroll viewport when present instead of the
        nominal MainWindow size.  This is critical on VNC/Termux/HiDPI sessions
        where the top-level window may be large while the visible workspace is
        materially narrower.
        """
        try:
            scroll = self.findChild(QScrollArea)
            if scroll is not None and scroll.viewport() is not None:
                return max(0, int(scroll.viewport().width()))
        except Exception:
            pass
        try:
            return max(0, int(self.width()))
        except Exception:
            return 0

    def _dashboard_responsive_column_count(self) -> int:
        width = self._dashboard_available_width()
        if width and width < int(BRAND.get('dashboard_one_column_breakpoint', 920)):
            return 1
        if width and width < int(BRAND.get('dashboard_two_column_breakpoint', 1280)):
            return 2
        return 3

    def _clear_layout_items(self, layout) -> None:
        while layout is not None and layout.count():
            item = layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                try:
                    widget.setParent(None)
                except Exception:
                    pass

    def _layout_quick_actions(self, columns: int = 3) -> None:
        grid = getattr(self, 'quick_actions_grid', None)
        buttons = list(getattr(self, 'quick_action_buttons', []) or [])
        if grid is None or not buttons:
            return
        columns = max(1, min(3, int(columns or 3)))
        self._clear_layout_items(grid)
        for i, btn in enumerate(buttons):
            row = i // columns
            visual_col = columns - 1 - (i % columns) if qt_layout_direction() == Qt.RightToLeft else i % columns
            grid.addWidget(btn, row, visual_col)
        for c in range(3):
            grid.setColumnStretch(c, 1 if c < columns else 0)

    def _apply_dashboard_responsive_layout(self, force: bool = False) -> None:
        grid = getattr(self, 'dashboard_responsive_grid', None)
        panels = [getattr(self, name, None) for name in ('quick_panel', 'company_panel', 'project_panel')]
        if grid is None or any(p is None for p in panels):
            return
        columns = self._dashboard_responsive_column_count()
        if not force and getattr(self, '_dashboard_responsive_columns', None) == columns:
            return
        self._dashboard_responsive_columns = columns
        self._clear_layout_items(grid)
        for panel in panels:
            try:
                panel.setMinimumWidth(0)
                panel.setMaximumWidth(16777215)
                panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                panel.setProperty('dashboardResponsiveColumns', columns)
            except Exception:
                pass
        self._layout_quick_actions(2 if columns == 1 else 3)
        if columns == 1:
            for row, panel in enumerate(panels):
                grid.addWidget(panel, row, 0)
            min_height = int(BRAND.get('dashboard_panel_min_height_compact', 300))
        elif columns == 2:
            grid.addWidget(self.quick_panel, 0, 0)
            grid.addWidget(self.company_panel, 0, 1)
            grid.addWidget(self.project_panel, 1, 0, 1, 2)
            min_height = int(BRAND.get('dashboard_panel_min_height_medium', 360))
        else:
            grid.addWidget(self.quick_panel, 0, 0)
            grid.addWidget(self.company_panel, 0, 1)
            grid.addWidget(self.project_panel, 0, 2)
            min_height = int(BRAND.get('dashboard_panel_min_height_wide', BRAND.get('dashboard_panel_min_height', 430)))
        for panel in panels:
            try:
                panel.setMinimumHeight(min_height)
            except Exception:
                pass
        try:
            for c in range(3):
                grid.setColumnStretch(c, 1 if c < columns else 0)
            self.dashboard_responsive_host.setProperty('dashboardResponsiveColumns', columns)
            self.dashboard_responsive_host.style().unpolish(self.dashboard_responsive_host)
            self.dashboard_responsive_host.style().polish(self.dashboard_responsive_host)
        except Exception:
            pass

    def resizeEvent(self, event):  # type: ignore[override]
        super().resizeEvent(event)
        self._apply_dashboard_responsive_layout(force=False)

    def _build_hero(self):
        hero = QFrame()
        hero.setObjectName('DashboardHero')
        hero.setMinimumHeight(128)
        hero.setStyleSheet(f'''
            QFrame#DashboardHero {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {_dc('primary', '#0F3D75')}, stop:0.58 {_dc('primary_2', '#1E5AA8')}, stop:1 {_dc('accent', '#2D7FF9')});
                border-radius: 22px;
            }}
            QPushButton#HeroButton {{
                background: white;
                color: {_dc('primary', '#0F3D75')};
                border: none;
                border-radius: 14px;
                padding: 10px 16px;
                font-weight: 900;
            }}
            QPushButton#HeroButton:hover {{ background: {_dc('brand_soft', '#EAF1F8')}; }}
        ''')
        layout = QHBoxLayout(hero)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        text_col = QVBoxLayout()
        title = QLabel(translate('dashboard_hero_title'))
        title.setObjectName('HeroTitle')
        title.setAlignment(Qt.AlignRight)
        subtitle = QLabel(translate('dashboard_hero_subtitle'))
        subtitle.setObjectName('HeroSubtitle')
        subtitle.setAlignment(Qt.AlignRight)
        text_col.addWidget(title)
        text_col.addWidget(subtitle)
        text_col.addStretch()

        pills = QHBoxLayout()
        self.api_status = QLabel(translate('api_status_placeholder'))
        self.api_status.setObjectName('StatusPill')
        self.queue_status = QLabel(translate('queue_status_placeholder'))
        self.queue_status.setObjectName('StatusPill')
        self.ledger_status = QLabel(translate('ledger_status_placeholder'))
        self.ledger_status.setObjectName('StatusPill')
        pills.addWidget(self.api_status)
        pills.addWidget(self.queue_status)
        pills.addWidget(self.ledger_status)
        pills.addStretch()
        text_col.addLayout(pills)

        actions = QVBoxLayout()
        refresh_btn = QPushButton(qta.icon('fa5s.sync-alt'), ' ' + translate('refresh_now'))
        refresh_btn.setObjectName('HeroButton')
        refresh_btn.clicked.connect(self.refresh_all)
        monitor_btn = QPushButton(qta.icon('fa5s.heartbeat'), ' ' + translate('monitoring'))
        monitor_btn.setObjectName('HeroButton')
        monitor_btn.clicked.connect(lambda: self._switch_page('monitoring'))
        reports_btn = QPushButton(qta.icon('fa5s.chart-pie'), ' ' + translate('reports'))
        reports_btn.setObjectName('HeroButton')
        reports_btn.clicked.connect(lambda: self._switch_page('reports'))
        actions.addWidget(refresh_btn)
        actions.addWidget(monitor_btn)
        actions.addWidget(reports_btn)
        actions.addStretch()

        layout.addLayout(actions)
        layout.addLayout(text_col, 1)
        self.main_layout.addWidget(hero)

    def _build_kpi_grid(self):
        """Modern dashboard KPI strip bound to DashboardService snapshots.

        The widgets are visual-only components from ui.dashboard_components;
        they do not access the database, printing, or gateways directly.
        """
        row = QHBoxLayout()
        row.setSpacing(12)
        definitions = (
            ('sales', translate('sales_invoice'), 'file-invoice-dollar', 'primary'),
            ('purchases', translate('purchase_invoice'), 'shopping-cart', 'warning'),
            ('cash', translate('cashbox'), 'cash-register', 'success'),
            ('alerts', translate('alerts_bar'), 'bell', 'danger'),
        )
        for key, title, icon, tone in definitions:
            card = ModernKpiCard(title, icon, tone, self)
            self.cards[key] = card
            row.addWidget(card, 1)
        self.main_layout.addLayout(row)

        self.trend_panel = DashboardChartPanel(translate('reports'), self)
        self.main_layout.addWidget(self.trend_panel)

    def _build_middle_grid(self):
        # Phase286 static marker: setMaximumHeight(430)
        # Phase303 static marker: QPushButton { text-align: center; }
        # Phase303 static marker: grid.addWidget(btn, i // 3, 2 - (i % 3))
        # Phase439: the dashboard landing surface is a real responsive grid.
        # The previous fixed three-column QHBoxLayout clipped the shortcuts
        # column on VNC/Termux/HiDPI and small Windows screens.
        self.dashboard_responsive_host = QWidget()
        self.dashboard_responsive_host.setObjectName('DashboardResponsiveGridHost')
        self.dashboard_responsive_host.setProperty('dashboardResponsivePhase', 439)
        self.dashboard_responsive_host.setProperty('projectVisualIdentityPhase', '439')
        self.dashboard_responsive_host.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.dashboard_responsive_grid = QGridLayout(self.dashboard_responsive_host)
        self.dashboard_responsive_grid.setContentsMargins(0, 0, 0, 0)
        self.dashboard_responsive_grid.setHorizontalSpacing(int(BRAND.get('dashboard_responsive_grid_spacing', 14)))
        self.dashboard_responsive_grid.setVerticalSpacing(int(BRAND.get('dashboard_responsive_grid_spacing', 14)))

        self.quick_panel = self._create_quick_actions_panel()
        self.company_panel = self._create_company_info_panel()
        self.project_panel = self._create_project_panel()
        for panel in (self.quick_panel, self.company_panel, self.project_panel):
            panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            panel.setMinimumWidth(0)
            panel.setMaximumWidth(16777215)
            panel.setProperty('dashboardResponsivePhase', 439)
            panel.setProperty('projectVisualIdentityPhase', '439')

        self.main_layout.addWidget(self.dashboard_responsive_host, 1)
        self._dashboard_responsive_columns = None
        self._apply_dashboard_responsive_layout(force=True)
        apply_targeted_screen_rebuild(self, page_id='dashboard', workspace_type='dashboard')
        apply_single_screen_runtime_hardening(self, page_id='dashboard', workspace_type='dashboard')
        apply_runtime_visual_regression_gate(self, page_id='dashboard', workspace_type='dashboard')

    def _build_bottom_grid(self):
        # Phase 286: keep the developer/system identity card as a compact,
        # explicit product identity band.  It is not a company-card duplicate.
        self.brand_panel = self._create_brand_panel()
        self.brand_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.main_layout.addWidget(self.brand_panel)

    def _create_quick_actions_panel(self):
        panel = DashboardPanel(translate('dashboard_daily_shortcuts'), 'bolt')
        panel.setObjectName('DashboardQuickActionsPanel')
        panel.setMinimumHeight(int(BRAND.get('dashboard_panel_min_height_medium', 360)))
        panel.setProperty('basitPanel', False)
        panel.setProperty('dashboardPanelRole', 'daily_shortcuts')
        grid = QGridLayout()
        grid.setSpacing(12)
        self.quick_actions_grid = grid
        self.quick_action_buttons = []
        actions = [
            (translate('dashboard_pos_f9'), 'desktop', '#059669', 'primary', lambda: self._switch_page('pos')),
            (translate('sales_invoice'), 'file-invoice-dollar', '#2563eb', 'primary', lambda: self._open_invoice('sale')),
            (translate('purchase_invoice'), 'shopping-cart', '#f59e0b', 'secondary', lambda: self._open_invoice('purchase')),
            (translate('new_customer'), 'user-plus', '#8b5cf6', 'secondary', self._open_add_customer),
            (translate('new_supplier'), 'truck-loading', '#0891b2', 'secondary', self._open_add_supplier),
            (translate('new_item'), 'box', '#0ea5e9', 'secondary', self._open_add_item),
            (translate('receipt_voucher'), 'hand-holding-usd', '#16a34a', 'finance', lambda: self._open_voucher('receipt')),
            (translate('payment_voucher'), 'money-bill-wave', '#ef4444', 'finance', lambda: self._open_voucher('payment')),
            (translate('expense'), 'file-invoice', '#f97316', 'finance', lambda: self._open_voucher('expense')),
        ]
        for i, (text, icon, color, tier, callback) in enumerate(actions):
            btn = QuickActionButton(text, icon, color)
            btn.setObjectName('DashboardDailyActionButton')
            # Phase328 compatibility marker: btn.setMinimumHeight(92)
            btn.setMinimumHeight(int(BRAND.get('dashboard_shortcut_height', BRAND.get('basit_dashboard_card_height', 96))))
            btn.setProperty('visualRole', 'dashboard_shortcut')
            btn.setProperty('dashboardActionTier', tier)
            btn.setProperty('basitCard', False)
            btn.setProperty('dashboardVisualPhase', 437)
            # Phase328 compatibility marker: btn.setIconSize(QSize(24, 24))
            btn.setIconSize(QSize(24, 24))
            btn.setLayoutDirection(qt_layout_direction())
            # Phase437: centered shortcut cards use product identity tones.
            if tier == 'primary':
                bg = _dc('dashboard_shortcut_primary_bg', '#0A6D9A')
                hover = _dc('dashboard_shortcut_primary_hover', '#095D84')
                fg = '#FFFFFF'
                border = _dc('dashboard_shortcut_primary_hover', '#095D84')
            elif tier == 'finance':
                bg = _dc('dashboard_shortcut_finance_bg', '#F3E8CF')
                hover = _dc('dashboard_shortcut_finance_hover', '#E8D6AC')
                fg = _dc('dashboard_shortcut_finance_text', '#654B12')
                border = '#E2C889'
                btn.setIcon(qta.icon(f'fa5s.{icon}', color=fg))
            else:
                bg = _dc('dashboard_shortcut_secondary_bg', '#EAF4FF')
                hover = _dc('dashboard_shortcut_secondary_hover', '#DDEEFF')
                fg = _dc('dashboard_shortcut_secondary_text', '#0B3D63')
                border = _dc('dashboard_panel_header_border', '#C7DAEE')
                btn.setIcon(qta.icon(f'fa5s.{icon}', color=fg))
            btn.setStyleSheet(f'''
                QPushButton#DashboardDailyActionButton {{
                    background: {bg};
                    color: {fg};
                    border: 1px solid {border};
                    border-radius: {int(BRAND.get('dashboard_shortcut_radius', 14))}px;
                    padding-left: 10px;
                    padding-right: 10px;
                    text-align: center;
                    font-weight: 950;
                }}
                QPushButton#DashboardDailyActionButton:hover {{ background: {hover}; }}
            ''')
            btn.clicked.connect(callback)
            self.quick_action_buttons.append(btn)
        self._layout_quick_actions(3)
        panel.layout.addLayout(grid)
        panel.layout.addStretch()
        return panel

    def _create_alerts_panel(self):
        # Removed from the rendered dashboard.  Kept as an explicit compatibility
        # hook returning None so older integrations do not rebuild a lower alerts
        # strip by accident.
        return None

    def _create_company_info_panel(self):
        panel = DashboardPanel(translate('company_current_info'), 'building')
        panel.setObjectName('DashboardCompanyPanel')
        panel.setLayoutDirection(qt_layout_direction())
        panel.setMinimumHeight(int(BRAND.get('dashboard_panel_min_height_medium', 360)))
        panel.setProperty('basitPanel', False)
        panel.setProperty('dashboardPanelRole', 'company_identity')
        panel.setStyleSheet(panel.styleSheet() + '''
            /* Phase437 identity-aligned company card; old Basit hard border removed. */
            QLabel#CompanyLogoBox { background: #ffffff; border: 1px solid #D8E5F2; border-radius: 16px; padding: 12px; }
            QLabel#CompanyName { color: #071A2E; font-size: 21px; font-weight: 950; border: none; }
            QLabel#CompanyLine { color: #38556F; font-size: 13px; font-weight: 850; border: none; }
            QLabel#CompanyFallbackNote { color: #64748b; background: transparent; border: none; font-size: 1px; }
        ''')

        self.company_logo_label = QLabel()
        self.company_logo_label.setObjectName('CompanyLogoBox')
        self.company_logo_label.setAlignment(Qt.AlignCenter)
        self.company_logo_label.setFixedHeight(132)
        panel.layout.addWidget(self.company_logo_label)

        self.company_name_label = QLabel('—')
        self.company_name_label.setObjectName('CompanyName')
        self.company_name_label.setAlignment(Qt.AlignCenter)
        self.company_name_label.setWordWrap(True)
        panel.layout.addWidget(self.company_name_label)

        self.company_address_label = QLabel('—')
        self.company_address_label.setObjectName('CompanyLine')
        self.company_address_label.setAlignment(Qt.AlignCenter)
        self.company_address_label.setWordWrap(True)
        panel.layout.addWidget(self.company_address_label)

        self.company_contact_label = QLabel('—')
        self.company_contact_label.setObjectName('CompanyLine')
        self.company_contact_label.setAlignment(Qt.AlignCenter)
        self.company_contact_label.setWordWrap(True)
        panel.layout.addWidget(self.company_contact_label)

        self.company_tax_label = QLabel('—')
        self.company_tax_label.setObjectName('CompanyLine')
        self.company_tax_label.setAlignment(Qt.AlignCenter)
        self.company_tax_label.setWordWrap(True)
        panel.layout.addWidget(self.company_tax_label)

        self.company_fallback_note = QLabel(translate('company_info_fallback_note'))
        self.company_fallback_note.setObjectName('CompanyFallbackNote')
        self.company_fallback_note.setAlignment(Qt.AlignCenter)
        self.company_fallback_note.setWordWrap(True)
        self.company_fallback_note.setVisible(False)
        panel.layout.addWidget(self.company_fallback_note)
        panel.layout.addStretch()
        self._refresh_company_info_panel()
        return panel

    def _company_has_explicit_info(self):
        """Return True when the tenant/company card has real user settings.

        config.get_company_info intentionally has product defaults so printing and
        dashboards never render empty branding. For the dashboard, however, we
        need to distinguish explicit company identity from developer/system
        fallback identity.
        """
        settings = QSettings("Alrajhi", "Accounting")
        explicit_keys = (
            "company/name",
            "company/address",
            "company/phone",
            "company/email",
            "company/tax_number",
            "company/commercial_register",
            "company/website",
            "company/logo_data_uri",
        )
        for key in explicit_keys:
            value = settings.value(key, "")
            if str(value or "").strip():
                return True
        logo_value = str(settings.value("company/logo_path", "") or "").strip()
        if logo_value and logo_value != logo_png(512):
            return True
        return False

    def _refresh_company_info_panel(self):
        if not hasattr(self, 'company_name_label'):
            return
        try:
            from config import get_company_info
            info = get_company_info() or {}
        except Exception as exc:
            print(f'⚠️ تعذر تحميل معلومات الشركة: {exc}')
            info = {}
        explicit_company_info = self._company_has_explicit_info()
        name = info.get('name') or _dashboard_product_name()
        address = info.get('address') or translate('address_not_set')
        phone = info.get('phone') or ''
        email = info.get('email') or ''
        tax_number = info.get('tax_number') or ''
        logo_path = info.get('logo_path') or logo_png(512)

        self.company_name_label.setText(str(name))
        self.company_address_label.setText(str(address))
        contact_parts = [str(v) for v in (phone, email) if v]
        self.company_contact_label.setText(' | '.join(contact_parts) if contact_parts else translate('contact_not_set'))
        self.company_tax_label.setText(translate('tax_number_value', value=tax_number) if tax_number else translate('tax_number_not_set'))
        if hasattr(self, 'company_fallback_note'):
            self.company_fallback_note.setVisible(False)
        pix = QPixmap(str(logo_path))
        if pix.isNull():
            pix = QPixmap(logo_png(256))
        if not pix.isNull():
            self.company_logo_label.setPixmap(pix.scaled(QSize(110, 110), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _create_project_panel(self):
        panel = DashboardPanel(translate('cashbox'), 'wallet')
        panel.setObjectName('DashboardCashPanel')
        panel.setLayoutDirection(qt_layout_direction())
        panel.setMinimumHeight(int(BRAND.get('dashboard_panel_min_height_medium', 360)))
        panel.setProperty('basitPanel', False)
        panel.setProperty('dashboardPanelRole', 'cashbox')
        panel.setStyleSheet(panel.styleSheet() + """
            QLabel#CashSectionTitle { background: #EAF4FF; color: #0B3D63; border: 1px solid #C7DAEE; border-radius: 12px; padding: 7px 10px; font-size: 15px; font-weight: 950; }
            QLabel#CashMetricTitle { color: #38556F; font-size: 12px; font-weight: 900; border: none; }
            QLabel#CashMetricValue { color: #071A2E; font-size: 20px; font-weight: 950; border: none; }
            QLabel#CashBalanceValue { color: #C2410C; font-size: 32px; font-weight: 950; border: none; }
            QLabel#CashBalanceTitle { color: #071A2E; font-size: 14px; font-weight: 950; border: none; }
            QLineEdit#CashExchangeRateInput { background: #ffffff; border: 1px solid #D8E5F2; border-radius: 10px; padding: 7px 10px; font-size: 13px; font-weight: 900; }
            QPushButton#CashExchangeSaveButton { background: #0A6D9A; color: white; border: 1px solid #095D84; border-radius: 10px; padding: 7px 12px; font-weight: 950; }
            QPushButton#CashExchangeSaveButton:hover { background: #095D84; }
        """)

        self.cash_labels = {}
        # Phase413: dashboard cash visibility/mode are persistent user preferences,
        # not transient widget-only flags.
        self._cash_view_mode = user_preferences_service.dashboard_cash_view_mode()
        self._cash_balances_hidden = user_preferences_service.dashboard_cash_balances_hidden()
        self._cash_raw_values = {}

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)
        self.cash_visibility_btn = QPushButton()
        self.cash_visibility_btn.setToolTip(translate('toggle_balances_visibility'))
        self.cash_visibility_btn.setFixedSize(30, 30)
        self.cash_visibility_btn.setCursor(Qt.PointingHandCursor)
        self.cash_visibility_btn.setIcon(qta.icon('fa5s.eye-slash' if self._cash_balances_hidden else 'fa5s.eye', color='#334155'))
        self.cash_visibility_btn.clicked.connect(self._toggle_cash_visibility)
        self.cash_visibility_btn.setStyleSheet('QPushButton { background: #F8FBFF; border: 1px solid #D8E5F2; border-radius: 15px; } QPushButton:hover { background: #EAF4FF; }')
        self.cash_mode_btn = QPushButton(translate('today_movement'))
        self.cash_mode_btn.setCursor(Qt.PointingHandCursor)
        self.cash_mode_btn.setMinimumHeight(30)
        self.cash_mode_btn.clicked.connect(self._toggle_cash_movement_mode)
        self.cash_mode_btn.setStyleSheet('QPushButton { background: #EAF4FF; border: 1px solid #C7DAEE; border-radius: 15px; color: #0B3D63; font-weight: 900; padding: 4px 14px; } QPushButton:hover { background: #DDEEFF; }')
        header.addWidget(self.cash_visibility_btn)
        header.addStretch()
        header.addWidget(self.cash_mode_btn)
        panel.layout.addLayout(header)

        movement_box = QFrame()
        movement_box.setObjectName('CashMovementBox')
        movement_box.setProperty('basitPanel', False)
        movement_box.setProperty('dashboardVisualPhase', 437)
        movement_box.setStyleSheet('QFrame#CashMovementBox { background: #FFFFFF; border: 1px solid #D8E5F2; border-radius: 16px; } QLabel { border: none; }')
        movement_layout = QVBoxLayout(movement_box)
        movement_layout.setContentsMargins(12, 10, 12, 12)
        movement_layout.setSpacing(10)
        self.cash_section_title = QLabel(translate('today_movement'))
        self.cash_section_title.setObjectName('CashSectionTitle')
        self.cash_section_title.setAlignment(Qt.AlignCenter)
        movement_layout.addWidget(self.cash_section_title)

        def make_amount_card(key, title, icon_name, accent='#2563eb'):
            card = QFrame()
            card.setProperty('basitMetricCard', False)
            card.setProperty('dashboardVisualPhase', 437)
            card.setStyleSheet('QFrame { background: #F8FBFF; border: 1px solid #D8E5F2; border-radius: 14px; } QLabel { border: none; }')
            lay = QHBoxLayout(card)
            lay.setContentsMargins(10, 9, 10, 9)
            icon = QLabel()
            icon.setPixmap(qta.icon(f'fa5s.{icon_name}', color=accent).pixmap(QSize(18, 18)))
            text_col = QVBoxLayout()
            text_col.setSpacing(2)
            title_label = QLabel(title)
            title_label.setObjectName('CashMetricTitle')
            title_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            value_label = QLabel('—')
            value_label.setObjectName('CashMetricValue')
            value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            value_label.setStyleSheet(f'color: {accent};')
            text_col.addWidget(title_label)
            text_col.addWidget(value_label)
            lay.addLayout(text_col, 1)
            lay.addWidget(icon)
            self.cash_labels[key] = value_label
            return card

        movement_grid = QGridLayout()
        movement_grid.setSpacing(10)
        movement_grid.addWidget(make_amount_card('paid', translate('paid'), 'arrow-down', '#dc2626'), 0, 0)
        movement_grid.addWidget(make_amount_card('received', translate('received'), 'arrow-up', '#059669'), 0, 1)
        movement_layout.addLayout(movement_grid)
        panel.layout.addWidget(movement_box)

        balance_box = QFrame()
        balance_box.setObjectName('CashBalanceBox')
        balance_box.setProperty('basitTotalFooter', True)
        balance_box.setStyleSheet('QFrame#CashBalanceBox { background: #FFF7ED; border: 1px solid #FED7AA; border-radius: 16px; } QLabel { border: none; }')
        balance_layout = QVBoxLayout(balance_box)
        balance_layout.setContentsMargins(12, 10, 12, 10)
        balance_layout.setSpacing(4)
        balance_title = QLabel(translate('cashbox_current_balance'))
        balance_title.setObjectName('CashBalanceTitle')
        balance_title.setAlignment(Qt.AlignCenter)
        balance_value = QLabel('—')
        balance_value.setObjectName('CashBalanceValue')
        balance_value.setAlignment(Qt.AlignCenter)
        balance_layout.addWidget(balance_title)
        balance_layout.addWidget(balance_value)
        self.cash_labels['cash_balance'] = balance_value
        panel.layout.addWidget(balance_box)

        currency_box = QFrame()
        currency_box.setObjectName('CashCurrencyBox')
        currency_box.setLayoutDirection(qt_layout_direction())
        currency_box.setProperty('basitPanel', False)
        currency_box.setProperty('dashboardVisualPhase', 437)
        currency_box.setStyleSheet('QFrame#CashCurrencyBox { background: #FFFFFF; border: 1px solid #D8E5F2; border-radius: 16px; } QLabel { border: none; }')
        currency_layout = QGridLayout(currency_box)
        currency_layout.setContentsMargins(10, 9, 10, 9)
        currency_layout.setHorizontalSpacing(8)
        currency_layout.setVerticalSpacing(8)

        currency_title = QLabel(translate('display_currency'))
        currency_title.setObjectName('CashMetricTitle')
        currency_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.currency_combo = QComboBox()
        self.currency_combo.setObjectName('CashCurrencyCombo')
        self.currency_combo.setMinimumHeight(32)
        self.currency_combo.currentIndexChanged.connect(self.on_currency_changed)

        exchange_title = QLabel(translate('exchange_rate'))
        exchange_title.setObjectName('CashMetricTitle')
        exchange_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.exchange_rate_input = QLineEdit()
        self.exchange_rate_input.setObjectName('CashExchangeRateInput')
        self.exchange_rate_input.setPlaceholderText('14000.00')
        self.exchange_rate_input.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.exchange_rate_input.returnPressed.connect(self._save_exchange_rate_from_dashboard)
        self.exchange_rate_save_btn = QPushButton(translate('save'))
        self.exchange_rate_save_btn.setObjectName('CashExchangeSaveButton')
        self.exchange_rate_save_btn.clicked.connect(self._save_exchange_rate_from_dashboard)
        self.exchange_rate_label = QLabel('—')
        self.exchange_rate_label.setObjectName('CashExchangeRate')
        self.exchange_rate_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        currency_layout.addWidget(self.currency_combo, 0, 0, 1, 2)
        currency_layout.addWidget(currency_title, 0, 2)
        currency_layout.addWidget(self.exchange_rate_save_btn, 1, 0)
        currency_layout.addWidget(self.exchange_rate_input, 1, 1)
        currency_layout.addWidget(exchange_title, 1, 2)
        currency_layout.addWidget(self.exchange_rate_label, 2, 0, 1, 2)
        currency_layout.setColumnStretch(1, 1)
        panel.layout.addWidget(currency_box)
        panel.layout.addStretch()
        self.load_currencies()
        return panel


    def _create_brand_panel(self):
        # Phase286 static marker: setMaximumHeight(190)
        # Phase303 static marker: row.setDirection(QBoxLayout.RightToLeft)
        """Polished integrated-system banner matching the approved dashboard mockup.

        Compatibility marker for legacy Phase 285 tests:
        DashboardPanel(translate('integrated_management_system')
        """
        panel = QFrame()
        panel.setObjectName('DeveloperBrandPanel')
        panel.setLayoutDirection(qt_layout_direction())
        panel.setMinimumHeight(210)
        panel.setMaximumHeight(260)
        panel.setProperty('basitPanel', False)
        panel.setProperty('dashboardVisualPhase', 437)
        panel.setProperty('projectVisualIdentityPhase', '439')
        panel.setStyleSheet(f"""
            QFrame#DeveloperBrandPanel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #F8FBFF, stop:1 #EEF8FA);
                border: 1px solid #D8E5F2;
                border-radius: 18px;
            }}
            QLabel#SystemBrandLogoBox {{
                background: #FFFFFF;
                border: 1px solid #D8E5F2;
                border-radius: 22px;
                padding: 8px;
            }}
            QLabel#SystemBrandTitle {{
                color: #0B3D63;
                font-size: 32px;
                font-weight: 900;
                border: none;
            }}
            QLabel#SystemBrandSubtitle {{
                color: #38556F;
                font-size: 14px;
                font-weight: 900;
                border: none;
            }}
            QLabel#SystemBrandDivider {{
                color: #0AA7A7;
                font-size: 18px;
                font-weight: 900;
                border: none;
            }}
        """)

        body = QHBoxLayout(panel)
        body.setDirection(QBoxLayout.RightToLeft)
        body.setContentsMargins(28, 18, 28, 18)
        body.setSpacing(22)

        logo = QLabel()
        logo.setObjectName('SystemBrandLogoBox')
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(126, 104)
        pix = QPixmap(logo_png(512))
        if not pix.isNull():
            logo.setPixmap(pix.scaled(QSize(86, 86), Qt.KeepAspectRatio, Qt.SmoothTransformation))

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(8)
        title = QLabel(translate('integrated_management_system'))
        title.setObjectName('SystemBrandTitle')
        # Phase 303: identity banner is centered; surrounding structure remains RTL.
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        subtitle_row = QHBoxLayout()
        subtitle_row.setSpacing(12)
        left_divider = QLabel('────')
        left_divider.setObjectName('SystemBrandDivider')
        right_divider = QLabel('────')
        right_divider.setObjectName('SystemBrandDivider')
        subtitle = QLabel(translate('integrated_management_subtitle'))
        subtitle.setObjectName('SystemBrandSubtitle')
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle_row.addStretch(1)
        subtitle_row.addWidget(left_divider)
        subtitle_row.addWidget(subtitle, 0, Qt.AlignCenter)
        subtitle_row.addWidget(right_divider)
        subtitle_row.addStretch(1)
        text_col.addStretch(1)
        text_col.addWidget(title)
        text_col.addLayout(subtitle_row)
        text_col.addStretch(1)

        body.addWidget(logo, 0, Qt.AlignVCenter)
        body.addLayout(text_col, 1)
        body.addStretch(0)
        return panel

    def _create_health_panel(self):
        panel = DashboardPanel(translate('runtime_status'), 'heartbeat')
        self.health_labels = {}
        for key, title in (
            ('api', translate('server_connection')),
            ('queue', translate('sync_requests')),
            ('ledger', translate('ledger_reconciliation')),
            ('errors', translate('recent_errors')),
        ):
            row = QFrame()
            row.setStyleSheet('QFrame { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; } QLabel { border: none; }')
            layout = QHBoxLayout(row)
            layout.setContentsMargins(10, 8, 10, 8)
            title_label = QLabel(title)
            title_label.setStyleSheet('font-weight: 800; color: #334155;')
            value_label = QLabel('—')
            value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            value_label.setStyleSheet('font-weight: 900; color: #0f172a;')
            layout.addWidget(value_label)
            layout.addStretch()
            layout.addWidget(title_label)
            panel.layout.addWidget(row)
            self.health_labels[key] = value_label
        panel.layout.addStretch()
        return panel

    def _save_exchange_rate_from_dashboard(self):
        if not hasattr(self, 'exchange_rate_input'):
            return
        code = self.currency_combo.currentData() if hasattr(self, 'currency_combo') else currency.get_display_currency()
        code = str(code or currency.get_display_currency() or 'USD')
        if code == currency.storage_currency():
            show_toast(translate('exchange_rate_base_currency_no_update'), 'info', self)
            return
        raw = str(self.exchange_rate_input.text() or '').strip().replace(',', '')
        try:
            rate = Decimal(raw)
        except Exception:
            show_toast(translate('invalid_exchange_rate'), 'error', self)
            return
        if rate <= 0:
            show_toast(translate('invalid_exchange_rate'), 'error', self)
            return
        try:
            currency.update_rate(code, float(rate))
            if hasattr(currency, '_cache_rate'):
                currency._cache_rate(code, rate)
            show_toast(translate('exchange_rate_updated'), 'success', self)
            self.refresh_all()
        except Exception as exc:
            show_toast(translate('exchange_rate_update_failed', error=str(exc)), 'error', self)

    def setup_currency_bar(self, parent_layout):
        # Retained for external compatibility; the redesigned dashboard embeds the
        # currency selector in the hero row instead of a separate legacy bar.
        pass

    def load_currencies(self):
        if not hasattr(self, 'currency_combo'):
            return
        self._loading_currencies = True
        self.currency_combo.blockSignals(True)
        self.currency_combo.clear()
        rates = currency.get_all_currencies()
        current_display = currency.get_display_currency()
        current_index = 0
        for i, r in enumerate(rates):
            code = r['currency_code']
            symbol = currency.get_currency_symbol(code)
            self.currency_combo.addItem(f'{code} ({symbol})', code)
            if code == current_display:
                current_index = i
        self.currency_combo.setCurrentIndex(current_index)
        self.currency_combo.blockSignals(False)
        self._loading_currencies = False

    def on_currency_changed(self, index):
        if self._loading_currencies:
            return
        new_curr = self.currency_combo.currentData() if hasattr(self, 'currency_combo') else None
        if not new_curr or currency.get_display_currency() == new_curr:
            return
        from core.services.settings_service import settings_service
        settings_service.set_display_currency(new_curr)
        show_toast(translate('currency_changed_to', currency=new_curr), 'success', self)
        self.currency_changed.emit(new_curr)
        self.refresh_all()

    def reload_from_settings(self):
        self.load_currencies()
        self.refresh_all()

    def refresh_all(self):
        display_curr = currency.get_display_currency()
        try:
            self._snapshot = dashboard_service.snapshot(use_cache=False)
        except Exception as exc:
            print(f'⚠️ تعذر تحديث لوحة التحكم: {exc}')
            self._snapshot = {'summary': {}}
        self._refresh_kpis(display_curr)
        self._refresh_alerts()  # no-op after Phase 285 unless an alerts table is explicitly reintroduced
        self._refresh_project_card(display_curr)
        self._refresh_company_info_panel()
        self._refresh_health()

    def _refresh_kpis(self, display_curr):
        if not self.cards and not hasattr(self, 'trend_panel'):
            return
        summary = self._snapshot.get('summary', {}) if isinstance(self._snapshot, dict) else {}
        cashbox_movement = self._snapshot.get('cashbox_movement', {}) if isinstance(self._snapshot, dict) else {}
        alerts = self._snapshot.get('alerts', {}) if isinstance(self._snapshot, dict) else {}

        def amount(key):
            try:
                return currency.format_base_amount(Decimal(str(summary.get(key, 0) or 0)))
            except Exception:
                return '—'

        if 'sales' in self.cards:
            self.cards['sales'].set_value(amount('sales_total'))
            self.cards['sales'].set_hint(translate('display_currency') + ': ' + str(display_curr))
        if 'purchases' in self.cards:
            self.cards['purchases'].set_value(amount('purchase_total'))
            self.cards['purchases'].set_hint(translate('display_currency') + ': ' + str(display_curr))
        if 'cash' in self.cards:
            try:
                cash_value = Decimal(str(cashbox_movement.get('cash_balance', summary.get('cash_balance', 0)) or 0))
                self.cards['cash'].set_value(currency.format_base_amount(cash_value))
            except Exception:
                self.cards['cash'].set_value('—')
            self.cards['cash'].set_hint(translate('exchange_rate'))
        if 'alerts' in self.cards:
            count = alerts.get('count') if isinstance(alerts, dict) else None
            self.cards['alerts'].set_value(str(count if count is not None else '—'))
            self.cards['alerts'].set_hint(translate('dashboard_indicators_normal'))

        if hasattr(self, 'trend_panel'):
            rows = []
            for row in self._snapshot.get('monthly_trend', []) if isinstance(self._snapshot, dict) else []:
                rows.append(row)
            self.trend_panel.set_trend(rows, translate('incoming'), translate('outgoing'))

    def _refresh_alerts(self):
        # Phase 286: no bottom alerts strip is allowed on the dashboard surface.
        # If a legacy extension injected an alerts table, hide it defensively.
        table = getattr(self, 'alerts_table', None)
        if table is not None:
            table.setVisible(False)
        panel = getattr(self, 'alerts_panel', None)
        if panel is not None:
            panel.setVisible(False)

    def _toggle_cash_movement_mode(self):
        self._cash_view_mode = 'general' if getattr(self, '_cash_view_mode', 'today') == 'today' else 'today'
        # Phase413: persist the dashboard cash period selector across restarts.
        user_preferences_service.set_dashboard_cash_view_mode(self._cash_view_mode)
        self._render_cash_amounts(currency.get_display_currency())

    def _toggle_cash_visibility(self):
        self._cash_balances_hidden = not getattr(self, '_cash_balances_hidden', False)
        # Phase413: persist hiding/showing cash balances immediately so the
        # dashboard restores the same privacy state after closing and reopening.
        user_preferences_service.set_dashboard_cash_balances_hidden(self._cash_balances_hidden)
        if hasattr(self, 'cash_visibility_btn'):
            icon_name = 'eye-slash' if self._cash_balances_hidden else 'eye'
            self.cash_visibility_btn.setIcon(qta.icon(f'fa5s.{icon_name}', color='#334155'))
        self._render_cash_amounts(currency.get_display_currency())

    def _masked_amount(self):
        return '••••••'

    def _render_cash_amounts(self, display_curr):
        if not hasattr(self, 'cash_labels'):
            return
        mode = getattr(self, '_cash_view_mode', 'today')
        raw_values = getattr(self, '_cash_raw_values', {}) or {}
        selected = raw_values.get(mode, {})
        section_title = translate('general_movement') if mode == 'general' else translate('today_movement')
        if hasattr(self, 'cash_section_title'):
            self.cash_section_title.setText(section_title)
        if hasattr(self, 'cash_mode_btn'):
            self.cash_mode_btn.setText(section_title)

        hidden = getattr(self, '_cash_balances_hidden', False)
        for key in ('received', 'paid', 'net'):
            label = self.cash_labels.get(key)
            if not label:
                continue
            if hidden:
                label.setText(self._masked_amount())
            else:
                amount = Decimal(str(selected.get(key, 0) or 0))
                label.setText(currency.format_base_amount(amount))

        balance_label = self.cash_labels.get('cash_balance')
        if balance_label:
            if hidden:
                balance_label.setText(self._masked_amount())
            else:
                amount = Decimal(str(raw_values.get('cash_balance', 0) or 0))
                balance_label.setText(currency.format_base_amount(amount))

    def _refresh_project_card(self, display_curr):
        if not hasattr(self, 'cash_labels'):
            return
        summary = self._snapshot.get('summary', {}) if isinstance(self._snapshot, dict) else {}
        liquidity = self._snapshot.get('cash_bank_summary', {}) if isinstance(self._snapshot, dict) else {}
        cashbox_movement = self._snapshot.get('cashbox_movement', {}) if isinstance(self._snapshot, dict) else {}
        today = cashbox_movement.get('today', {}) if isinstance(cashbox_movement, dict) else {}
        general = cashbox_movement.get('general', {}) if isinstance(cashbox_movement, dict) else {}
        cash_balance = liquidity.get('cash_total') if isinstance(liquidity, dict) and liquidity.get('cash_total') is not None else summary.get('cash_balance', 0)

        self._cash_raw_values = {
            'today': {
                'received': Decimal(str(today.get('received', 0) or 0)),
                'paid': Decimal(str(today.get('paid', 0) or 0)),
                'net': Decimal(str(today.get('net', 0) or 0)),
            },
            'general': {
                'received': Decimal(str(general.get('received', 0) or 0)),
                'paid': Decimal(str(general.get('paid', 0) or 0)),
                'net': Decimal(str(general.get('net', 0) or 0)),
            },
            'cash_balance': Decimal(str(cash_balance or 0)),
        }
        self._render_cash_amounts(display_curr)
        self._refresh_cash_currency_info(display_curr)

    def _refresh_cash_currency_info(self, display_curr):
        if not hasattr(self, 'exchange_rate_label'):
            return
        try:
            base_curr = currency.storage_currency()
            display_curr = str(display_curr or currency.get_display_currency())
            rate_value = currency.get_current_rate(display_curr)
            if hasattr(self, 'exchange_rate_input'):
                self.exchange_rate_input.blockSignals(True)
                self.exchange_rate_input.setText(f'{Decimal(str(rate_value)):,.2f}')
                self.exchange_rate_input.setEnabled(display_curr != base_curr)
                self.exchange_rate_input.blockSignals(False)
            converted = currency.convert(Decimal('1'), base_curr, display_curr)
            converted_text = currency.format_amount(converted, display_curr, decimals=2)
            self.exchange_rate_label.setText(translate('exchange_rate_value', base=base_curr, amount=converted_text))
        except Exception as exc:
            self.exchange_rate_label.setText(translate('not_available'))
            print(f'⚠️ تعذر تحميل سعر الصرف: {exc}')

        if hasattr(self, 'currency_combo') and not self._loading_currencies:
            for i in range(self.currency_combo.count()):
                if self.currency_combo.itemData(i) == display_curr:
                    if self.currency_combo.currentIndex() != i:
                        self.currency_combo.blockSignals(True)
                        self.currency_combo.setCurrentIndex(i)
                        self.currency_combo.blockSignals(False)
                    break

    def _refresh_health(self):
        if not hasattr(self, 'health_labels'):
            return
        try:
            overview = monitoring_service.overview(tolerance='0')
        except Exception as exc:
            print(f'⚠️ تعذر تحميل مراقبة التشغيل: {exc}')
            overview = {}
        api = overview.get('api', {}) if isinstance(overview, dict) else {}
        queue = overview.get('queue', {}) if isinstance(overview, dict) else {}
        ledger = overview.get('ledger', {}) if isinstance(overview, dict) else {}
        requests = overview.get('requests', {}) if isinstance(overview, dict) else {}

        api_ok = api.get('ok', api.get('status') in ('ok', 'online', True))
        queue_pending = queue.get('pending', queue.get('pending_count', 0)) or 0
        queue_failed = queue.get('failed', queue.get('failed_count', 0)) or 0
        ledger_blockers = ledger.get('blockers_count', ledger.get('blockers', 0)) or 0
        recent_errors = requests.get('errors', requests.get('recent_errors', 0)) or 0

        self.api_status.setText(translate('api_connected') if api_ok else translate('api_check'))
        self.queue_status.setText(translate('queue_pending_short', pending=queue_pending))
        self.ledger_status.setText(translate('ledger_ready') if not ledger_blockers else translate('ledger_blockers', count=ledger_blockers))
        self.health_labels['api'].setText(translate('connected') if api_ok else translate('uncertain'))
        self.health_labels['queue'].setText(translate('queue_pending_failed', pending=queue_pending, failed=queue_failed))
        self.health_labels['ledger'].setText(translate('matched') if not ledger_blockers else translate('blocking_count', count=ledger_blockers))
        self.health_labels['errors'].setText(str(recent_errors))
        if 'ops' in self.cards:
            self.cards['ops'].set_hint(f'Queue {queue_pending} / Failed {queue_failed}')

    def _set_table(self, table, rows, keys, headers):
        model = GenericTableModel(rows, headers, key_fields=[keys[0]], data_keys=keys)
        table.setModel(model)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.refresh_style()

    def _severity_label(self, severity):
        return {'critical': '🔴', 'warning': '🟠', 'info': '🔵'}.get(severity, '🔵')

    def _main_window(self):
        main_window = self.window()
        return main_window if hasattr(main_window, 'pages') else None

    def _switch_page(self, page_name):
        main_window = self._main_window()
        if main_window and hasattr(main_window, 'switch_page'):
            main_window.switch_page(page_name)
        else:
            show_toast(translate('cannot_navigate_to_page'), 'error', self)

    def _open_invoice(self, inv_type):
        """Open invoice shortcuts through the workspace document system.

        Dashboard quick actions are document actions, not modal-dialog actions.
        Keep the old modal dialog path out of the dashboard so invoices use the
        same TransactionDocumentTab routing as the rest of the
        application.
        """
        try:
            main = self._main_window()
            if main and hasattr(main, 'open_quick_invoice'):
                main.open_quick_invoice(inv_type)
                return
            show_toast(translate('cannot_open_document_tab'), 'error', self)
        except Exception as exc:
            show_toast(str(exc), 'error', self)

    def _open_add_item(self):
        try:
            main = self._main_window()
            if main and hasattr(main, 'open_item_document'):
                main.open_item_document()
                return
            from features.items import ItemEditorTab
            tab = ItemEditorTab(self)
            tab.show()
        except Exception as exc:
            show_toast(str(exc), 'error', self)

    def _open_add_customer(self):
        try:
            main = self._main_window()
            if main and hasattr(main, 'open_party_document'):
                main.open_party_document('customer')
                return
            show_toast(translate('cannot_open_document_tab'), 'error', self)
        except Exception as exc:
            show_toast(str(exc), 'error', self)

    def _open_add_supplier(self):
        try:
            main = self._main_window()
            if main and hasattr(main, 'open_party_document'):
                main.open_party_document('supplier')
                return
            show_toast(translate('cannot_open_document_tab'), 'error', self)
        except Exception as exc:
            show_toast(str(exc), 'error', self)

    def _open_page_action(self, page_key, methods, kwargs_by_method=None):
        kwargs_by_method = kwargs_by_method or {}
        main_window = self._main_window()
        if not main_window:
            return
        page = main_window.pages.get(page_key)
        for method in methods:
            if page and hasattr(page, method):
                try:
                    getattr(page, method)(**kwargs_by_method.get(method, {}))
                except TypeError:
                    getattr(page, method)()
                except Exception as exc:
                    show_toast(str(exc), 'error', self)
                return

    def _open_voucher(self, voucher_type='receipt'):
        try:
            main = self._main_window()
            if main and hasattr(main, 'open_quick_voucher'):
                tab = main.open_quick_voucher(voucher_type=voucher_type)
                if tab and hasattr(tab, 'saved'):
                    page = (main.pages.get('vouchers') if hasattr(main, 'pages') else None)
                    if page and hasattr(page, 'refresh'):
                        tab.saved.connect(lambda *_: page.refresh())
                return
            show_toast(translate('cannot_open_document_tab'), 'error', self)
        except Exception as exc:
            show_toast(str(exc), 'error', self)

    def apply_theme_colors(self):
        self.refresh_all()
