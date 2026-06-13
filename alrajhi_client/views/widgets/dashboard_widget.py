# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal

from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QPushButton,
    QComboBox, QHeaderView, QScrollArea, QSizePolicy
)

import qtawesome as qta

from core.services.dashboard_service import dashboard_service
from core.services.alert_service import alert_service
from core.services.monitoring_service import monitoring_service
from currency import currency
from models.table_models import GenericTableModel
from utils import show_toast
from views.custom_table_view import CustomTableView
# Branding assets are used in login/splash/application icon.


class KPIStatCard(QFrame):
    clicked = pyqtSignal()

    def __init__(self, title, value='0', icon_name='chart-line', color='#2563eb', hint='', parent=None):
        super().__init__(parent)
        self.color = color
        self.setObjectName('KPIStatCard')
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(116)
        self.setStyleSheet(f'''
            QFrame#KPIStatCard {{
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 18px;
            }}
            QFrame#KPIStatCard:hover {{
                border: 1px solid {color};
                background: #f8fafc;
            }}
            QLabel#KpiTitle {{
                color: #64748b;
                font-size: 13px;
                font-weight: 700;
            }}
            QLabel#KpiValue {{
                color: #0f172a;
                font-size: 24px;
                font-weight: 900;
            }}
            QLabel#KpiHint {{
                color: #94a3b8;
                font-size: 11px;
            }}
            QLabel#KpiIcon {{
                background: {color};
                border-radius: 15px;
                padding: 8px;
            }}
        ''')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        top = QHBoxLayout()
        self.icon_label = QLabel()
        self.icon_label.setObjectName('KpiIcon')
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(42, 42)
        self.icon_label.setPixmap(qta.icon(f'fa5s.{icon_name}', color='white').pixmap(QSize(22, 22)))
        self.title_label = QLabel(title)
        self.title_label.setObjectName('KpiTitle')
        self.title_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        top.addWidget(self.icon_label)
        top.addWidget(self.title_label, 1)
        layout.addLayout(top)

        self.value_label = QLabel(value)
        self.value_label.setObjectName('KpiValue')
        self.value_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.value_label)

        self.hint_label = QLabel(hint)
        self.hint_label.setObjectName('KpiHint')
        self.hint_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.hint_label)

    def set_value(self, text):
        self.value_label.setText(text)

    def set_hint(self, text):
        self.hint_label.setText(text or '')

    def mouseReleaseEvent(self, event):
        self.clicked.emit()
        super().mouseReleaseEvent(event)


class QuickActionButton(QPushButton):
    def __init__(self, text, icon_name, color, parent=None):
        super().__init__(qta.icon(f'fa5s.{icon_name}', color='white'), f'  {text}', parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(46)
        self.setStyleSheet(f'''
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                border-radius: 14px;
                padding: 9px 13px;
                font-size: 13px;
                font-weight: 800;
                text-align: right;
            }}
            QPushButton:hover {{ background: #0f172a; }}
        ''')


class DashboardPanel(QFrame):
    def __init__(self, title, icon_name='circle', parent=None):
        super().__init__(parent)
        self.setObjectName('DashboardPanel')
        self.setStyleSheet('''
            QFrame#DashboardPanel {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 18px;
            }
            QLabel#PanelTitle {
                color: #0f172a;
                font-size: 16px;
                font-weight: 900;
            }
        ''')
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 14, 16, 16)
        self.layout.setSpacing(12)
        header = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(qta.icon(f'fa5s.{icon_name}', color='#2563eb').pixmap(QSize(18, 18)))
        title_label = QLabel(title)
        title_label.setObjectName('PanelTitle')
        title_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header.addWidget(icon)
        header.addWidget(title_label)
        header.addStretch()
        self.layout.addLayout(header)


class DashboardWidget(QWidget):
    refresh_needed = pyqtSignal()
    currency_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setObjectName('DashboardWidget')
        self._loading_currencies = False
        self.cards = {}
        self._snapshot = {}
        self._build_ui()
        QTimer.singleShot(100, self.refresh_all)

    def _build_ui(self):
        self.setStyleSheet('''
            QWidget#DashboardWidget { background: #f1f5f9; }
            QLabel#HeroTitle { color: white; font-size: 25px; font-weight: 900; }
            QLabel#HeroSubtitle { color: #dbeafe; font-size: 13px; font-weight: 600; }
            QLabel#StatusPill { color: white; background: rgba(255,255,255,0.18); border-radius: 12px; padding: 7px 12px; font-weight: 800; }
            QComboBox { min-height: 34px; border: 1px solid #cbd5e1; border-radius: 10px; padding: 4px 8px; background: white; }
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
        self.main_layout.setContentsMargins(22, 22, 22, 22)
        self.main_layout.setSpacing(18)

        self._build_hero()
        self._build_middle_grid()
        self._build_bottom_grid()

    def _build_hero(self):
        hero = QFrame()
        hero.setObjectName('DashboardHero')
        hero.setMinimumHeight(128)
        hero.setStyleSheet('''
            QFrame#DashboardHero {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f172a, stop:0.55 #1d4ed8, stop:1 #0ea5e9);
                border-radius: 22px;
            }
            QPushButton#HeroButton {
                background: white;
                color: #0f172a;
                border: none;
                border-radius: 14px;
                padding: 10px 16px;
                font-weight: 900;
            }
            QPushButton#HeroButton:hover { background: #e0f2fe; }
        ''')
        layout = QHBoxLayout(hero)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        text_col = QVBoxLayout()
        title = QLabel('لوحة التحكم التشغيلية')
        title.setObjectName('HeroTitle')
        title.setAlignment(Qt.AlignRight)
        subtitle = QLabel('ملخص سريع للمبيعات، المشتريات، النقدية، التنبيهات، والتزامن')
        subtitle.setObjectName('HeroSubtitle')
        subtitle.setAlignment(Qt.AlignRight)
        text_col.addWidget(title)
        text_col.addWidget(subtitle)
        text_col.addStretch()

        pills = QHBoxLayout()
        self.api_status = QLabel('API: —')
        self.api_status.setObjectName('StatusPill')
        self.queue_status = QLabel('Queue: —')
        self.queue_status.setObjectName('StatusPill')
        self.ledger_status = QLabel('Ledger: —')
        self.ledger_status.setObjectName('StatusPill')
        pills.addWidget(self.api_status)
        pills.addWidget(self.queue_status)
        pills.addWidget(self.ledger_status)
        pills.addStretch()
        text_col.addLayout(pills)

        actions = QVBoxLayout()
        refresh_btn = QPushButton(qta.icon('fa5s.sync-alt'), ' تحديث الآن')
        refresh_btn.setObjectName('HeroButton')
        refresh_btn.clicked.connect(self.refresh_all)
        monitor_btn = QPushButton(qta.icon('fa5s.heartbeat'), ' مراقبة التشغيل')
        monitor_btn.setObjectName('HeroButton')
        monitor_btn.clicked.connect(lambda: self._switch_page('monitoring'))
        reports_btn = QPushButton(qta.icon('fa5s.chart-pie'), ' التقارير')
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
        # Phase 40: KPI cards removed by request. The project/cash card and
        # monitoring panel now carry the essential operational summary.
        return

    def _build_middle_grid(self):
        row = QHBoxLayout()
        row.setSpacing(16)
        self.quick_panel = self._create_quick_actions_panel()
        self.project_panel = self._create_project_panel()
        row.addWidget(self.quick_panel, 1)
        row.addWidget(self.project_panel, 2)
        self.main_layout.addLayout(row)

    def _build_bottom_grid(self):
        row = QHBoxLayout()
        row.setSpacing(16)
        self.alerts_panel = self._create_alerts_panel()
        self.health_panel = self._create_health_panel()
        row.addWidget(self.alerts_panel, 2)
        row.addWidget(self.health_panel, 1)
        self.main_layout.addLayout(row)

    def _create_quick_actions_panel(self):
        panel = DashboardPanel('اختصارات العمل اليومية', 'bolt')
        pos = QuickActionButton('نقطة البيع POS  F9', 'barcode', '#059669')
        pos.setMinimumHeight(58)
        pos.clicked.connect(lambda: self._switch_page('pos'))
        panel.layout.addWidget(pos)
        grid = QGridLayout()
        grid.setSpacing(8)
        actions = [
            ('فاتورة بيع', 'file-invoice-dollar', '#2563eb', lambda: self._open_invoice('sale')),
            ('فاتورة شراء', 'shopping-cart', '#f59e0b', lambda: self._open_invoice('purchase')),
            ('عميل جديد', 'user-plus', '#8b5cf6', self._open_add_customer),
            ('مورد جديد', 'truck-loading', '#ec4899', self._open_add_supplier),
            ('مادة جديدة', 'box', '#0ea5e9', self._open_add_item),
            ('سند قبض', 'hand-holding-usd', '#10b981', lambda: self._open_voucher('receipt')),
            ('سند دفع', 'money-bill-wave', '#ef4444', lambda: self._open_voucher('payment')),
            ('مراقبة', 'heartbeat', '#64748b', lambda: self._switch_page('monitoring')),
        ]
        for i, (text, icon, color, callback) in enumerate(actions):
            btn = QuickActionButton(text, icon, color)
            btn.clicked.connect(callback)
            grid.addWidget(btn, i // 2, i % 2)
        panel.layout.addLayout(grid)
        panel.layout.addStretch()
        return panel

    def _create_alerts_panel(self):
        panel = DashboardPanel('شريط التنبيهات', 'bell')
        panel.setMaximumHeight(150)
        panel.setMinimumHeight(118)
        self.alerts_table = CustomTableView()
        self.alerts_table.setMinimumHeight(58)
        self.alerts_table.setMaximumHeight(82)
        panel.layout.addWidget(self.alerts_table)
        return panel

    def _create_project_panel(self):
        panel = DashboardPanel('الصندوق', 'cash-register')
        panel.setMinimumHeight(220)

        self.project_labels = {}
        grid = QGridLayout()
        grid.setSpacing(8)
        for i, (key, label, icon_name) in enumerate((
            ('cash_balance', 'رصيد الصندوق', 'money-bill-wave'),
            ('daily_sales', 'حركة البيع اليوم', 'chart-line'),
            ('daily_purchases', 'حركة الشراء اليوم', 'shopping-cart'),
            ('daily_net', 'صافي الحركة اليومية', 'exchange-alt'),
        )):
            card = QFrame()
            card.setStyleSheet("""
                QFrame { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; }
                QLabel { border: none; }
            """)
            lay = QHBoxLayout(card)
            lay.setContentsMargins(10, 8, 10, 8)
            icon = QLabel()
            icon.setPixmap(qta.icon(f'fa5s.{icon_name}', color='#2563eb').pixmap(QSize(18, 18)))
            value = QLabel('—')
            value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            value.setStyleSheet('font-size: 13px; font-weight: 900; color: #0f172a;')
            title = QLabel(label)
            title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            title.setStyleSheet('font-size: 12px; font-weight: 800; color: #475569;')
            lay.addWidget(value)
            lay.addStretch()
            lay.addWidget(title)
            lay.addWidget(icon)
            grid.addWidget(card, i // 2, i % 2)
            self.project_labels[key] = value
        panel.layout.addLayout(grid)

        currency_box = QFrame()
        currency_box.setObjectName('CashCurrencyBox')
        currency_box.setStyleSheet("""
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
        """)
        currency_layout = QGridLayout(currency_box)
        currency_layout.setContentsMargins(10, 8, 10, 8)
        currency_layout.setHorizontalSpacing(8)
        currency_layout.setVerticalSpacing(6)

        currency_title = QLabel('العملة المعروضة')
        currency_title.setObjectName('CashCurrencyTitle')
        currency_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.currency_combo = QComboBox()
        self.currency_combo.setObjectName('CashCurrencyCombo')
        self.currency_combo.setMinimumHeight(32)
        self.currency_combo.currentIndexChanged.connect(self.on_currency_changed)

        exchange_title = QLabel('سعر الصرف')
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

    def _create_health_panel(self):
        panel = DashboardPanel('حالة التشغيل', 'heartbeat')
        self.health_labels = {}
        for key, title in (
            ('api', 'اتصال الخادم'),
            ('queue', 'طلبات المزامنة'),
            ('ledger', 'مطابقة Ledger'),
            ('errors', 'أخطاء حديثة'),
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
        show_toast(f'تم تغيير العملة إلى {new_curr}', 'success', self)
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
        self._refresh_alerts()
        self._refresh_project_card(display_curr)
        self._refresh_health()

    def _refresh_kpis(self, display_curr):
        # KPI cards were intentionally removed in Phase 40.
        return

    def _refresh_alerts(self):
        try:
            alerts = alert_service.dashboard_alerts(limit=12)
        except Exception as exc:
            print(f'⚠️ تعذر تحميل تنبيهات لوحة التحكم: {exc}')
            alerts = []
        data = []
        for alert in alerts:
            data.append({
                'severity': self._severity_label(alert.get('severity', 'info')),
                'title': alert.get('title', ''),
                'message': alert.get('message', ''),
            })
        if not data:
            data = [{'severity': '✅', 'title': 'لا توجد تنبيهات', 'message': 'كل المؤشرات التشغيلية ضمن الحدود الحالية'}]
        self._set_table(self.alerts_table, data, ['severity', 'title', 'message'], ['الحالة', 'التنبيه', 'التفاصيل'])

    def _refresh_project_card(self, display_curr):
        if not hasattr(self, 'project_labels'):
            return
        summary = self._snapshot.get('summary', {}) if isinstance(self._snapshot, dict) else {}
        sales = Decimal(str(summary.get('total_sales', 0) or 0))
        purchases = Decimal(str(summary.get('total_purchases', 0) or 0))
        expenses = Decimal(str(summary.get('total_expenses', 0) or 0))
        cash_balance = Decimal(str(summary.get('cash_balance', 0) or 0))
        daily_net = sales - purchases - expenses
        values = {
            'cash_balance': cash_balance,
            'daily_sales': sales,
            'daily_purchases': purchases,
            'daily_net': daily_net,
        }
        for key, amount in values.items():
            converted = currency.convert(amount, 'USD', display_curr)
            self.project_labels[key].setText(currency.format_amount(converted))
        self._refresh_cash_currency_info(display_curr)

    def _refresh_cash_currency_info(self, display_curr):
        if not hasattr(self, 'exchange_rate_label'):
            return
        try:
            syp_rate = currency.get_current_rate('SYP')
            syp_text = currency.format_amount(syp_rate, 'SYP', decimals=2)
            self.exchange_rate_label.setText(f'1 USD = {syp_text}')
        except Exception as exc:
            self.exchange_rate_label.setText('غير متوفر')
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

        self.api_status.setText('API: متصل' if api_ok else 'API: تحقق')
        self.queue_status.setText(f'Queue: {queue_pending}')
        self.ledger_status.setText('Ledger: جاهز' if not ledger_blockers else f'Ledger: {ledger_blockers}')
        self.health_labels['api'].setText('متصل' if api_ok else 'غير مؤكد')
        self.health_labels['queue'].setText(f'{queue_pending} معلق / {queue_failed} فاشل')
        self.health_labels['ledger'].setText('مطابق' if not ledger_blockers else f'{ledger_blockers} مانع')
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
            show_toast('لا يمكن الانتقال إلى الصفحة المطلوبة', 'error', self)

    def _open_invoice(self, inv_type):
        page_key = 'sales_invoices' if inv_type == 'sale' else 'purchase_invoices'
        main_window = self._main_window()
        if not main_window:
            show_toast('لا يمكن فتح الفاتورة من لوحة التحكم', 'error', self)
            return
        page = main_window.pages.get(page_key)
        main_window.switch_page(page_key)
        try:
            if page and hasattr(page, 'create_invoice'):
                page.create_invoice(inv_type)
        except Exception as exc:
            show_toast(str(exc), 'error', self)

    def _open_add_item(self):
        self._open_page_action('items', ('open_dialog', 'add_item'), {'open_dialog': {'is_edit': False}})

    def _open_add_customer(self):
        self._open_page_action('customers', ('add_customer', 'open_dialog'))

    def _open_add_supplier(self):
        self._open_page_action('suppliers', ('add_supplier', 'open_dialog'))

    def _open_page_action(self, page_key, methods, kwargs_by_method=None):
        kwargs_by_method = kwargs_by_method or {}
        main_window = self._main_window()
        if not main_window:
            return
        page = main_window.pages.get(page_key)
        main_window.switch_page(page_key)
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
        main_window = self._main_window()
        if not main_window:
            return
        page = main_window.pages.get('vouchers')
        main_window.switch_page('vouchers')
        try:
            from views.widgets.vouchers_widget import VoucherDialog
            dialog = VoucherDialog(page or self)
            if hasattr(dialog, 'type_combo'):
                dialog.type_combo.setCurrentIndex(0 if voucher_type == 'receipt' else 1)
            if dialog.exec() and page and hasattr(page, 'refresh'):
                page.refresh()
        except Exception:
            try:
                if page and hasattr(page, 'add_voucher'):
                    page.add_voucher()
            except Exception as exc:
                show_toast(str(exc), 'error', self)

    def apply_theme_colors(self):
        self.refresh_all()
