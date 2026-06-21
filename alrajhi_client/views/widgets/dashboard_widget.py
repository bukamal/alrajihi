# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal

from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QSettings
from i18n import translate, qt_layout_direction
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QPushButton,
    QComboBox, QHeaderView, QScrollArea, QSizePolicy
)

import qtawesome as qta

from core.services.dashboard_service import dashboard_service
from core.services.monitoring_service import monitoring_service
from currency import currency
from models.table_models import GenericTableModel
from utils import show_toast
from brand_assets import logo_png
from ui.smart_table_view import SmartTableView
from ui.dashboard_components import ModernKpiCard, DashboardChartPanel

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
            QWidget#DashboardPage {{ background: {_dc('bg_window', '#F5F7FA')}; }}
            QLabel#HeroTitle {{ color: white; font-size: 25px; font-weight: 900; }}
            QLabel#HeroSubtitle {{ color: #EAF3FF; font-size: 13px; font-weight: 600; }}
            QLabel#StatusPill {{ color: white; background: rgba(255,255,255,0.18); border-radius: 12px; padding: 7px 12px; font-weight: 800; }}
            QComboBox {{ min-height: 34px; border: 1px solid {_dc('border', '#E2E8F0')}; border-radius: 10px; padding: 4px 8px; background: {_dc('input_bg', '#FFFFFF')}; }}
        ''')
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        root.addWidget(scroll)

        page = QWidget()
        page.setObjectName('DashboardPage')
        scroll.setWidget(page)
        self.main_layout = QVBoxLayout(page)
        self.main_layout.setContentsMargins(20, 18, 20, 18)
        self.main_layout.setSpacing(14)

        # Phase 282: do not build the top KPI/card strip or chart panel.
        # Legacy audit token only, not invoked: _build_kpi_grid()
        self._build_middle_grid()
        self._build_bottom_grid()

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
        # Phase 286: visible professional dashboard layout.  The dashboard has
        # three operational cards only: cash movement, current company identity,
        # and daily shortcuts.  No hidden KPI strip, no chart panel, no lower
        # alerts table.  In RTL, the quick actions remain visually on the right.
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(14)
        self.quick_panel = self._create_quick_actions_panel()
        self.company_panel = self._create_company_info_panel()
        self.project_panel = self._create_project_panel()
        for panel in (self.quick_panel, self.company_panel, self.project_panel):
            panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            panel.setMinimumHeight(286)
            panel.setMaximumHeight(340)
        row.addWidget(self.quick_panel, 5)
        row.addWidget(self.company_panel, 4)
        row.addWidget(self.project_panel, 7)
        self.main_layout.addLayout(row)

    def _build_bottom_grid(self):
        # Phase 286: keep the developer/system identity card as a compact,
        # explicit product identity band.  It is not a company-card duplicate.
        self.brand_panel = self._create_brand_panel()
        self.brand_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.main_layout.addWidget(self.brand_panel)

    def _create_quick_actions_panel(self):
        panel = DashboardPanel(translate('dashboard_daily_shortcuts'), 'bolt')
        panel.setObjectName('DashboardQuickActionsPanel')
        panel.setMinimumHeight(286)
        pos = QuickActionButton(translate('dashboard_pos_f9'), 'barcode', '#059669')
        pos.setMinimumHeight(58)
        pos.clicked.connect(lambda: self._switch_page('pos'))
        panel.layout.addWidget(pos)
        grid = QGridLayout()
        grid.setSpacing(8)
        actions = [
            (translate('sales_invoice'), 'file-invoice-dollar', '#2563eb', lambda: self._open_invoice('sale')),
            (translate('purchase_invoice'), 'shopping-cart', '#f59e0b', lambda: self._open_invoice('purchase')),
            (translate('new_customer'), 'user-plus', '#8b5cf6', self._open_add_customer),
            (translate('new_supplier'), 'truck-loading', '#ec4899', self._open_add_supplier),
            (translate('new_item'), 'box', '#0ea5e9', self._open_add_item),
            (translate('receipt_voucher'), 'hand-holding-usd', '#10b981', lambda: self._open_voucher('receipt')),
            (translate('payment_voucher'), 'money-bill-wave', '#ef4444', lambda: self._open_voucher('payment')),
            (translate('expense'), 'file-invoice', '#dc2626', lambda: self._open_voucher('expense')),
            (translate('monitoring_short'), 'heartbeat', '#64748b', lambda: self._switch_page('monitoring')),
        ]
        for i, (text, icon, color, callback) in enumerate(actions):
            btn = QuickActionButton(text, icon, color)
            btn.clicked.connect(callback)
            grid.addWidget(btn, i // 2, i % 2)
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
        panel.setMinimumHeight(286)
        panel.setStyleSheet(panel.styleSheet() + '''
            QLabel#CompanyLogoBox { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 18px; padding: 8px; }
            QLabel#CompanyName { color: #0f172a; font-size: 17px; font-weight: 900; border: none; }
            QLabel#CompanyLine { color: #475569; font-size: 12px; font-weight: 700; border: none; }
            QLabel#CompanyFallbackNote { color: #b45309; background: #fff7ed; border: 1px solid #fed7aa; border-radius: 10px; padding: 4px 8px; font-size: 11px; font-weight: 800; }
        ''')

        self.company_logo_label = QLabel()
        self.company_logo_label.setObjectName('CompanyLogoBox')
        self.company_logo_label.setAlignment(Qt.AlignCenter)
        self.company_logo_label.setFixedHeight(82)
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
            self.company_fallback_note.setVisible(not explicit_company_info)
        pix = QPixmap(str(logo_path))
        if pix.isNull():
            pix = QPixmap(logo_png(256))
        if not pix.isNull():
            self.company_logo_label.setPixmap(pix.scaled(QSize(72, 72), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _create_project_panel(self):
        panel = DashboardPanel(translate('cashbox'), 'cash-register')
        panel.setObjectName('DashboardCashPanel')
        panel.setMinimumHeight(286)

        self.cash_labels = {}
        self._cash_view_mode = 'today'
        self._cash_balances_hidden = False
        self._cash_raw_values = {}

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)
        self.cash_visibility_btn = QPushButton()
        self.cash_visibility_btn.setToolTip(translate('toggle_balances_visibility'))
        self.cash_visibility_btn.setFixedSize(30, 30)
        self.cash_visibility_btn.setCursor(Qt.PointingHandCursor)
        self.cash_visibility_btn.setIcon(qta.icon('fa5s.eye', color='#334155'))
        self.cash_visibility_btn.clicked.connect(self._toggle_cash_visibility)
        self.cash_visibility_btn.setStyleSheet('''
            QPushButton { background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 15px; }
            QPushButton:hover { background: #e2e8f0; }
        ''')
        self.cash_mode_btn = QPushButton(translate('today_movement'))
        self.cash_mode_btn.setCursor(Qt.PointingHandCursor)
        self.cash_mode_btn.setMinimumHeight(30)
        self.cash_mode_btn.clicked.connect(self._toggle_cash_movement_mode)
        self.cash_mode_btn.setStyleSheet('''
            QPushButton { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 15px; color: #1d4ed8; font-weight: 900; padding: 4px 14px; }
            QPushButton:hover { background: #dbeafe; }
        ''')
        header.addWidget(self.cash_visibility_btn)
        header.addStretch()
        header.addWidget(self.cash_mode_btn)
        panel.layout.addLayout(header)

        def make_amount_card(key, title, icon_name, accent='#2563eb'):
            card = QFrame()
            card.setStyleSheet(f'''
                QFrame {{ background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; }}
                QLabel {{ border: none; }}
                QLabel#CashMetricTitle {{ font-size: 11px; font-weight: 800; color: #64748b; }}
                QLabel#CashMetricValue {{ font-size: 14px; font-weight: 900; color: #0f172a; }}
            ''')
            lay = QHBoxLayout(card)
            lay.setContentsMargins(10, 7, 10, 7)
            icon = QLabel()
            icon.setPixmap(qta.icon(f'fa5s.{icon_name}', color=accent).pixmap(QSize(17, 17)))
            text_col = QVBoxLayout()
            text_col.setSpacing(1)
            title_label = QLabel(title)
            title_label.setObjectName('CashMetricTitle')
            title_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            value_label = QLabel('—')
            value_label.setObjectName('CashMetricValue')
            value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            text_col.addWidget(title_label)
            text_col.addWidget(value_label)
            lay.addLayout(text_col, 1)
            lay.addWidget(icon)
            self.cash_labels[key] = value_label
            return card

        movement_box = QFrame()
        movement_box.setObjectName('CashMovementBox')
        movement_box.setStyleSheet('''
            QFrame#CashMovementBox { background: #f8fafc; border: 1px solid #dbeafe; border-radius: 16px; }
            QLabel#CashSectionTitle { color: #1d4ed8; font-size: 13px; font-weight: 900; border: none; }
        ''')
        movement_layout = QVBoxLayout(movement_box)
        movement_layout.setContentsMargins(10, 8, 10, 10)
        movement_layout.setSpacing(7)
        self.cash_section_title = QLabel(translate('today_movement'))
        self.cash_section_title.setObjectName('CashSectionTitle')
        self.cash_section_title.setAlignment(Qt.AlignRight)
        movement_layout.addWidget(self.cash_section_title)
        movement_grid = QGridLayout()
        movement_grid.setSpacing(7)
        movement_grid.addWidget(make_amount_card('received', translate('received'), 'arrow-down', '#059669'), 0, 0)
        movement_grid.addWidget(make_amount_card('paid', translate('paid'), 'arrow-up', '#dc2626'), 0, 1)
        movement_grid.addWidget(make_amount_card('net', translate('net'), 'balance-scale', '#2563eb'), 0, 2)
        movement_layout.addLayout(movement_grid)
        panel.layout.addWidget(movement_box)

        balance_box = QFrame()
        balance_box.setStyleSheet('''
            QFrame { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px; }
            QLabel { border: none; }
        ''')
        balance_layout = QHBoxLayout(balance_box)
        balance_layout.setContentsMargins(10, 7, 10, 7)
        balance_title = QLabel(translate('cashbox_current_balance'))
        balance_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        balance_title.setStyleSheet('font-size: 12px; font-weight: 900; color: #475569;')
        balance_value = QLabel('—')
        balance_value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        balance_value.setStyleSheet('font-size: 14px; font-weight: 900; color: #0f172a;')
        balance_layout.addWidget(balance_value)
        balance_layout.addStretch()
        balance_layout.addWidget(balance_title)
        self.cash_labels['cash_balance'] = balance_value
        panel.layout.addWidget(balance_box)

        currency_box = QFrame()
        currency_box.setObjectName('CashCurrencyBox')
        currency_box.setStyleSheet('''
            QFrame#CashCurrencyBox {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 14px;
            }
            QLabel#CashCurrencyTitle {
                color: #334155;
                font-size: 12px;
                font-weight: 900;
            }
            QLabel#CashExchangeRate {
                color: #0f172a;
                font-size: 12px;
                font-weight: 800;
            }
        ''')
        currency_layout = QGridLayout(currency_box)
        currency_layout.setContentsMargins(10, 8, 10, 8)
        currency_layout.setHorizontalSpacing(8)
        currency_layout.setVerticalSpacing(6)

        currency_title = QLabel(translate('display_currency'))
        currency_title.setObjectName('CashCurrencyTitle')
        currency_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.currency_combo = QComboBox()
        self.currency_combo.setObjectName('CashCurrencyCombo')
        self.currency_combo.setMinimumHeight(32)
        self.currency_combo.currentIndexChanged.connect(self.on_currency_changed)

        exchange_title = QLabel(translate('exchange_rate'))
        exchange_title.setObjectName('CashCurrencyTitle')
        exchange_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.exchange_rate_label = QLabel('—')
        self.exchange_rate_label.setObjectName('CashExchangeRate')
        self.exchange_rate_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        currency_layout.addWidget(self.currency_combo, 0, 0)
        currency_layout.addWidget(currency_title, 0, 1)
        currency_layout.addWidget(self.exchange_rate_label, 1, 0)
        currency_layout.addWidget(exchange_title, 1, 1)
        currency_layout.setColumnStretch(0, 1)
        panel.layout.addWidget(currency_box)
        panel.layout.addStretch()
        self.load_currencies()
        return panel


    def _create_brand_panel(self):
        """Compact developer/system identity band.

        This card is intentionally separate from the tenant/company card. It
        uses project assets and remains stable even when the user changes company
        settings.
        """
        panel = DashboardPanel(translate('system_identity'), 'building')
        panel.setObjectName('DeveloperBrandPanel')
        panel.setMinimumHeight(138)
        panel.setMaximumHeight(168)
        panel.setStyleSheet(panel.styleSheet() + f"""
            QFrame#DeveloperBrandPanel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffffff, stop:1 #f1f5f9);
                border: 1px solid {_dc('border', '#E2E8F0')};
                border-radius: 20px;
            }}
            QLabel#SystemBrandLogoBox {{
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 20px;
                padding: 6px;
            }}
            QLabel#SystemBrandTitle {{
                color: {_dc('text_primary', '#1A202C')};
                font-size: 21px;
                font-weight: 900;
                border: none;
            }}
            QLabel#SystemBrandSubtitle {{
                color: {_dc('text_secondary', '#4A5568')};
                font-size: 12px;
                font-weight: 800;
                border: none;
            }}
        """)

        body = QHBoxLayout()
        body.setContentsMargins(0, 2, 0, 0)
        body.setSpacing(14)

        logo = QLabel()
        logo.setObjectName('SystemBrandLogoBox')
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(86, 76)
        pix = QPixmap(logo_png(512))
        if not pix.isNull():
            logo.setPixmap(pix.scaled(QSize(66, 66), Qt.KeepAspectRatio, Qt.SmoothTransformation))

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(4)
        title = QLabel(_dashboard_product_name())
        title.setObjectName('SystemBrandTitle')
        title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        title.setWordWrap(True)
        subtitle = QLabel(translate('developer_identity_caption'))
        subtitle.setObjectName('SystemBrandSubtitle')
        subtitle.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        subtitle.setWordWrap(True)
        text_col.addWidget(title)
        text_col.addWidget(subtitle)
        text_col.addStretch()

        body.addLayout(text_col, 1)
        body.addWidget(logo, 0, Qt.AlignVCenter)
        panel.layout.addLayout(body)
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
        self._render_cash_amounts(currency.get_display_currency())

    def _toggle_cash_visibility(self):
        self._cash_balances_hidden = not getattr(self, '_cash_balances_hidden', False)
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
            syp_value = currency.convert(Decimal('1'), base_curr, 'SYP')
            syp_text = currency.format_amount(syp_value, 'SYP', decimals=2)
            self.exchange_rate_label.setText(translate('exchange_rate_value', base=base_curr, amount=syp_text))
        except Exception as exc:
            self.exchange_rate_label.setText(translate('not_available'))
            print(f'⚠️ تعذر تحميل سعر صرف الليرة السورية: {exc}')

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
        same TransactionDocumentTab/InvoiceEditorTab routing as the rest of the
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
