# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QGridLayout, QPushButton, QComboBox, QHeaderView,
                             QSizePolicy, QToolButton)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QSettings
from decimal import Decimal
from core.services.dashboard_service import dashboard_service
from core.services.alert_service import alert_service
from core.services.cashbox_service import cashbox_service
from currency import currency
from views.custom_table_view import CustomTableView
from models.table_models import GenericTableModel
from utils import show_toast
import qtawesome as qta
import datetime

class KPICard(QFrame):
    clicked = pyqtSignal()

    def __init__(self, title, value, icon_name, color="#3b82f6", parent=None):
        super().__init__(parent)
        self.setObjectName("KPICard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            #KPICard {{
                background-color: palette(base);
                border-radius: 20px;
                border: 1px solid palette(mid);
                padding: 16px;
            }}
            #KPICard:hover {{
                border: 1px solid {color};
                background-color: palette(alternate-base);
            }}
            QLabel#value {{
                font-size: 28px;
                font-weight: bold;
                color: palette(text);
            }}
            QLabel#title {{
                font-size: 14px;
                font-weight: 500;
                color: palette(mid);
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        top_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(f'fa5s.{icon_name}', color=color).pixmap(QSize(32, 32)))
        icon_label.setAlignment(Qt.AlignRight)
        title_label = QLabel(title)
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignLeft)
        top_layout.addWidget(icon_label)
        top_layout.addWidget(title_label)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        self.value_label = QLabel(value)
        self.value_label.setObjectName("value")
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)

    def set_value(self, text):
        self.value_label.setText(text)

    def mouseReleaseEvent(self, event):
        self.clicked.emit()
        super().mouseReleaseEvent(event)


class CashPrivacyCard(QFrame):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CashPrivacyCard")
        self.setFrameShape(QFrame.StyledPanel)
        self._settings = QSettings("AlRajhi", "Dashboard")
        # Financial privacy: keep the cash balance hidden by default unless the
        # user explicitly chose otherwise in this workstation profile.
        self._visible = self._settings.value("cash_balance_visible", False, type=bool)
        self._balance_text = "0"
        self._has_data = False
        self.setMinimumHeight(260)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setStyleSheet("""
            QFrame#CashPrivacyCard {
                background-color: palette(base);
                border-radius: 20px;
                border: 1px solid palette(mid);
                padding: 16px;
            }
            QFrame#CashPrivacyCard:hover {
                border: 1px solid #10b981;
                background-color: palette(alternate-base);
            }
            QLabel#cashTitle {
                font-size: 14px;
                font-weight: 600;
                color: palette(mid);
            }
            QLabel#cashValue {
                font-size: 28px;
                font-weight: bold;
                color: palette(text);
            }
            QLabel#cashMetricLabel {
                font-size: 12px;
                color: #64748b;
                background: transparent;
            }
            QLabel#cashMetricValue {
                font-size: 13px;
                font-weight: bold;
                color: #111827;
                background: transparent;
            }
            QToolButton#eyeButton {
                border: none;
                border-radius: 12px;
                padding: 6px;
                background: transparent;
            }
            QToolButton#eyeButton:hover {
                background-color: palette(alternate-base);
            }
            QPushButton#detailsButton {
                border: 1px solid palette(mid);
                border-radius: 10px;
                padding: 6px 10px;
                font-weight: bold;
                background-color: palette(button);
            }
            QPushButton#detailsButton:hover {
                background-color: palette(alternate-base);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon('fa5s.money-bill-wave', color='#10b981').pixmap(QSize(30, 30)))
        self.title_label = QLabel("رصيد الصندوق")
        self.title_label.setObjectName("cashTitle")
        self.eye_btn = QToolButton()
        self.eye_btn.setObjectName("eyeButton")
        self.eye_btn.setCursor(Qt.PointingHandCursor)
        self.eye_btn.clicked.connect(self.toggle_visibility)
        header.addWidget(icon_label)
        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.eye_btn)
        layout.addLayout(header)

        self.value_label = QLabel()
        self.value_label.setObjectName("cashValue")
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)

        self.metrics = {}
        for key, label in (
            ('opening', 'رصيد بداية اليوم'),
            ('in', 'قبض اليوم'),
            ('out', 'دفع اليوم'),
            ('net', 'صافي حركة اليوم'),
            ('closing', 'رصيد نهاية اليوم'),
        ):
            row = QHBoxLayout()
            l = QLabel(label)
            l.setObjectName('cashMetricLabel')
            v = QLabel('0')
            v.setObjectName('cashMetricValue')
            v.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            row.addWidget(l)
            row.addStretch()
            row.addWidget(v)
            layout.addLayout(row)
            self.metrics[key] = v

        self.details_btn = QPushButton("تفاصيل حركة اليوم")
        self.details_btn.setObjectName("detailsButton")
        self.details_btn.setCursor(Qt.PointingHandCursor)
        self.details_btn.clicked.connect(self.clicked.emit)
        layout.addWidget(self.details_btn)
        self._update_eye()
        self._update_value()

    def toggle_visibility(self):
        self._visible = not self._visible
        self._settings.setValue("cash_balance_visible", self._visible)
        self._update_eye()
        self._update_value()

    def set_value(self, text):
        self._balance_text = str(text if text not in (None, '') else '0')
        self._has_data = True
        self._update_value()

    def set_daily_metrics(self, metrics):
        for key in self.metrics:
            self.metrics[key].setText('0')
        for key, value in (metrics or {}).items():
            if key in self.metrics:
                self.metrics[key].setText(str(value if value not in (None, '') else '0'))

    def _update_eye(self):
        icon_name = 'eye' if not self._visible else 'eye-slash'
        tooltip = 'إظهار الرصيد' if not self._visible else 'إخفاء الرصيد'
        self.eye_btn.setIcon(qta.icon(f'fa5s.{icon_name}', color='#64748b'))
        self.eye_btn.setToolTip(tooltip)

    def _update_value(self):
        self.value_label.setText(self._balance_text if self._visible else '••••••')

    def mouseReleaseEvent(self, event):
        self.clicked.emit()
        super().mouseReleaseEvent(event)


class InfoListCard(QFrame):
    def __init__(self, title, icon_name, color="#3b82f6", parent=None):
        super().__init__(parent)
        self.setObjectName("InfoListCard")
        self.setStyleSheet(f"""
            QFrame#InfoListCard {{
                background-color: palette(base);
                border-radius: 20px;
                border: 1px solid palette(mid);
                padding: 16px;
            }}
            QLabel#infoTitle {{
                font-size: 16px;
                font-weight: bold;
            }}
            QLabel.infoLine {{
                border-radius: 10px;
                padding: 6px 8px;
                background-color: palette(alternate-base);
                font-size: 12px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        header = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(f'fa5s.{icon_name}', color=color).pixmap(QSize(24, 24)))
        title_label = QLabel(title)
        title_label.setObjectName("infoTitle")
        header.addWidget(icon_label)
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)
        self.lines_layout = QVBoxLayout()
        self.lines_layout.setSpacing(6)
        layout.addLayout(self.lines_layout)
        layout.addStretch()

    def set_lines(self, lines):
        while self.lines_layout.count():
            item = self.lines_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        for text in (lines or ["لا توجد بيانات حالياً"]):
            lbl = QLabel(str(text))
            lbl.setProperty('class', 'infoLine')
            lbl.setWordWrap(True)
            self.lines_layout.addWidget(lbl)


class DashboardWidget(QWidget):
    refresh_needed = pyqtSignal()
    currency_changed = pyqtSignal(str)   # إشارة تُصدر عند تغيير العملة من شريط العملات

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setObjectName("DashboardWidget")
        self._loading_currencies = False

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        self.setup_currency_bar(main_layout)

        self.card_grid = QGridLayout()
        self.card_grid.setSpacing(20)
        self.card_grid.setContentsMargins(0, 0, 0, 0)

        self.cards = {}
        self.create_cards()
        self.arrange_cards()
        main_layout.addLayout(self.card_grid)

        self.setup_alerts_table(main_layout)

        # تأخير التحديث الأول لضمان اكتمال الإنشاء
        QTimer.singleShot(100, self.refresh_all)

    # ------------------------------------------------------------
    # 1. شريط العملات
    # ------------------------------------------------------------
    def setup_currency_bar(self, parent_layout):
        currency_bar = QFrame()
        currency_bar.setObjectName("currencyBar")
        currency_bar.setStyleSheet("""
            QFrame#currencyBar {
                border-radius: 16px;
                padding: 8px 16px;
                background-color: palette(base);
                border: 1px solid palette(mid);
            }
        """)
        bar_layout = QHBoxLayout(currency_bar)
        bar_layout.setContentsMargins(12, 8, 12, 8)

        bar_layout.addWidget(QLabel("العملة المعروضة:"))
        self.currency_combo = QComboBox()
        self.currency_combo.setMinimumWidth(140)
        self.currency_combo.currentIndexChanged.connect(self.on_currency_changed)
        bar_layout.addWidget(self.currency_combo)
        bar_layout.addStretch()
        self.rate_label = QLabel()
        bar_layout.addWidget(self.rate_label)

        parent_layout.addWidget(currency_bar)
        self.load_currencies()

    def load_currencies(self):
        """تعبئة قائمة العملات من قاعدة البيانات"""
        self._loading_currencies = True
        self.currency_combo.blockSignals(True)
        self.currency_combo.clear()
        rates = currency.get_all_currencies()
        current_display = currency.get_display_currency()
        current_index = 0
        for i, r in enumerate(rates):
            code = r['currency_code']
            symbol = currency.get_currency_symbol(code)
            self.currency_combo.addItem(f"{code} ({symbol})", code)
            if code == current_display:
                current_index = i
        self.currency_combo.setCurrentIndex(current_index)
        self.update_rate_label(current_display)
        self.currency_combo.blockSignals(False)
        self._loading_currencies = False

    def update_rate_label(self, currency_code):
        rate = currency.get_current_rate(currency_code)
        if rate and rate != 0:
            usd_per_curr = 1.0 / float(rate) if rate != 0 else 0
            self.rate_label.setText(f"1 {currency_code} = {usd_per_curr:.4f} USD")
        else:
            self.rate_label.setText("")

    def on_currency_changed(self, index):
        if self._loading_currencies:
            return
        new_curr = self.currency_combo.currentData()
        if not new_curr:
            return
        if currency.get_display_currency() == new_curr:
            return
        # حفظ الإعدادات
        from core.services.settings_service import settings_service
        settings_service.set_display_currency(new_curr)
        show_toast(f"تم تغيير العملة إلى {new_curr}", "success", self)
        # إصدار إشارة لإعلام بقية الواجهات (مثل صفحة الإعدادات)
        self.currency_changed.emit(new_curr)
        # تحديث الواجهة الحالية
        self.refresh_all()

    def reload_from_settings(self):
        """إعادة تحميل العملة من الإعدادات وتحديث الواجهة (تُستدعى من الإعدادات عند التغيير)"""
        self.load_currencies()
        self.refresh_all()

    # ------------------------------------------------------------
    # 2. البطاقات
    # ------------------------------------------------------------
    def create_cards(self):
        self.cards['cash'] = CashPrivacyCard()
        self.cards['cash'].clicked.connect(lambda: self._switch_page('cashboxes'))
        self.cards['receivables'] = KPICard("الذمم المدينة", "0", "users", "#8b5cf6")
        self.cards['payables'] = KPICard("الذمم الدائنة", "0", "truck", "#ec4899")
        self.actions_card = self.create_actions_card()
        self.work_alerts_card = InfoListCard("تنبيهات العمل", "exclamation-triangle", "#f59e0b")
        self.recent_ops_card = InfoListCard("آخر العمليات", "history", "#3b82f6")

    def create_actions_card(self):
        card = QFrame()
        card.setObjectName("ActionsCard")
        card.setStyleSheet("""
            QFrame#ActionsCard {
                border-radius: 20px;
                padding: 16px;
                background-color: palette(base);
                border: 1px solid palette(mid);
            }
            QPushButton#posActionButton {
                border: none;
                border-radius: 18px;
                padding: 18px;
                font-weight: bold;
                font-size: 18px;
                color: white;
                background-color: #059669;
                text-align: center;
            }
            QPushButton#posActionButton:hover {
                background-color: #047857;
            }
            QPushButton.quick-action {
                border: none;
                border-radius: 14px;
                padding: 12px;
                font-weight: bold;
                font-size: 13px;
                color: white;
                text-align: center;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(10)

        title = QLabel("⚡ اختصارات سريعة")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        title.setAlignment(Qt.AlignRight)
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setContentsMargins(0, 0, 0, 0)
        actions = [
            ("POS", 'barcode', '#059669', self._open_pos),
            ("فاتورة بيع", 'file-invoice-dollar', '#10b981', lambda: self._open_invoice('sale')),
            ("فاتورة شراء", 'shopping-cart', '#f59e0b', lambda: self._open_invoice('purchase')),
            ("مادة", 'box', '#3b82f6', self._open_add_item),
            ("عميل", 'user-plus', '#8b5cf6', self._open_add_customer),
            ("مورد", 'truck-loading', '#ec4899', self._open_add_supplier),
            ("قبض", 'hand-holding-usd', '#14b8a6', lambda: self._open_voucher('receipt')),
            ("دفع", 'money-bill-wave', '#ef4444', lambda: self._open_voucher('payment')),
            ("المواد", 'boxes', '#64748b', lambda: self._switch_page('items')),
            ("الصناديق", 'cash-register', '#0ea5e9', lambda: self._switch_page('cashboxes')),
            ("التقارير", 'chart-line', '#6366f1', lambda: self._switch_page('reports')),
            ("السجل", 'history', '#475569', lambda: self._switch_page('audit_log')),
        ]
        for i, (text, icon, color, callback) in enumerate(actions):
            btn = QPushButton(qta.icon(f'fa5s.{icon}'), f"\n{text}")
            btn.setProperty("class", "quick-action")
            btn.setStyleSheet(f"background-color: {color};")
            btn.clicked.connect(callback)
            btn.setMinimumHeight(74)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            grid.addWidget(btn, i // 4, i % 4)
        for col in range(4):
            grid.setColumnStretch(col, 1)
        layout.addLayout(grid)
        layout.addStretch()
        return card

    def _main_window(self):
        main_window = self.window()
        return main_window if hasattr(main_window, 'pages') else None

    def _open_pos(self):
        self._switch_page('pos')

    def _open_invoice(self, inv_type):
        main_window = self._main_window()
        if not main_window:
            show_toast("لا يمكن فتح الفاتورة من لوحة التحكم", "error", self)
            return
        page = main_window.pages.get('invoices')
        if not page or not hasattr(page, 'create_invoice'):
            self._switch_page('invoices')
            return
        main_window.switch_page('invoices')
        try:
            if hasattr(page, 'tabs'):
                page.tabs.setCurrentIndex(0 if inv_type == 'sale' else 1)
            page.create_invoice(inv_type)
        except Exception as e:
            show_toast(str(e), "error", self)

    def _open_add_item(self):
        main_window = self._main_window()
        if not main_window:
            return
        page = main_window.pages.get('items')
        main_window.switch_page('items')
        try:
            if hasattr(page, 'open_dialog'):
                page.open_dialog(is_edit=False)
            elif hasattr(page, 'add_item'):
                page.add_item()
        except Exception as e:
            show_toast(str(e), "error", self)

    def _open_add_customer(self):
        self._open_entity('customers', 'add_customer')

    def _open_add_supplier(self):
        self._open_entity('suppliers', 'add_supplier')

    def _open_entity(self, page_name, method_name):
        main_window = self._main_window()
        if not main_window:
            return
        page = main_window.pages.get(page_name)
        main_window.switch_page(page_name)
        try:
            if page and hasattr(page, method_name):
                getattr(page, method_name)()
        except Exception as e:
            show_toast(str(e), "error", self)

    def _open_voucher(self, voucher_type='receipt'):
        main_window = self._main_window()
        if not main_window:
            return
        page = main_window.pages.get('vouchers')
        main_window.switch_page('vouchers')
        try:
            # افتح نافذة السند مباشرة حتى يمكن اختيار قبض/دفع مسبقًا.
            from views.widgets.vouchers_widget import VoucherDialog
            dialog = VoucherDialog(page or self)
            if hasattr(dialog, 'type_combo'):
                dialog.type_combo.setCurrentIndex(0 if voucher_type == 'receipt' else 1)
            if dialog.exec() and page and hasattr(page, 'refresh'):
                page.refresh()
        except Exception:
            # fallback إلى سلوك صفحة السندات القديمة.
            try:
                if page and hasattr(page, 'add_voucher'):
                    page.add_voucher()
            except Exception as e:
                show_toast(str(e), "error", self)

    def arrange_cards(self):
        """Arrange dashboard cards without financial-total KPI cards.

        The dashboard intentionally keeps operational cards only:
        cash balance, receivables, payables, and quick actions.
        Hidden/removed cards such as total sales, purchases, expenses,
        and net profit are not referenced here to avoid KeyError during refresh.
        """
        # الصندوق يحتاج مساحة أوسع لأنه يحتوي على رصيد مخفي وحركة يومية.
        # لذلك يأخذ نصف عرض اللوحة ويمتد عمودياً، بينما تبقى الذمم
        # والاختصارات في النصف الآخر.
        self.card_grid.addWidget(self.cards['cash'], 0, 0, 2, 2)
        self.card_grid.addWidget(self.cards['receivables'], 0, 2)
        self.card_grid.addWidget(self.cards['payables'], 0, 3)
        self.card_grid.addWidget(self.actions_card, 1, 2, 1, 2)
        self.card_grid.addWidget(self.work_alerts_card, 2, 0, 1, 2)
        self.card_grid.addWidget(self.recent_ops_card, 2, 2, 1, 2)
        for col in range(4):
            self.card_grid.setColumnStretch(col, 1)

    # ------------------------------------------------------------
    # 3. مركز التنبيهات
    # ------------------------------------------------------------
    def setup_alerts_table(self, parent_layout):
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: palette(base);
                border-radius: 16px;
                border: 1px solid palette(mid);
                padding: 8px;
            }
        """)
        layout = QVBoxLayout(container)
        title = QLabel("مركز التنبيهات")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.alerts_table = CustomTableView()
        self.alerts_table.setMinimumHeight(170)
        layout.addWidget(self.alerts_table)
        parent_layout.addWidget(container)

    # ------------------------------------------------------------
    # 5. تحديث البيانات
    # ------------------------------------------------------------
    def refresh_all(self):
        """Refresh dashboard without letting one failing service empty the whole page."""
        if not hasattr(self, 'cards') or not self.cards:
            return

        display_curr = currency.get_display_currency()
        self.update_rate_label(display_curr)

        summary = self._safe_dashboard_summary()
        for key, card_key in (
            ('cash_balance', 'cash'),
            ('receivables', 'receivables'),
            ('payables', 'payables'),
        ):
            if card_key not in self.cards:
                continue
            amount = self._money(summary.get(key, 0))
            converted = currency.convert(amount, 'USD', display_curr)
            self.cards[card_key].set_value(currency.format_amount(converted))

        if 'cash' in self.cards and hasattr(self.cards['cash'], 'set_daily_metrics'):
            self.cards['cash'].set_daily_metrics(self._cash_daily_metrics(display_curr, summary))

        self.load_alerts()
        self.load_work_alerts()
        self.load_recent_operations()

    def _safe_dashboard_summary(self):
        """Return a summary dict even when reporting/dashboard services fail.

        The previous dashboard refreshed through a broad snapshot path.  If any
        secondary part of that path failed, the cash card could remain empty.
        This method isolates the three values actually shown on the dashboard.
        """
        try:
            summary = dashboard_service.summary()
            if isinstance(summary, dict):
                return summary
        except Exception:
            pass
        try:
            from core.services.reporting_service import reporting_service
            summary = reporting_service.summary()
            return summary if isinstance(summary, dict) else {}
        except Exception:
            return {}

    def _money(self, value):
        try:
            return Decimal(str(value or 0))
        except Exception:
            return Decimal('0')

    def _fmt_money(self, value, display_curr):
        return currency.format_amount(currency.convert(self._money(value), 'USD', display_curr))

    def _cash_daily_metrics(self, display_curr, summary=None):
        """Return a reliable daily cash summary.

        It uses cash_bank_movements directly when available.  If there are no
        movements yet, the card still displays zeros plus the current cash
        balance from the dashboard summary, so it never appears blank.
        """
        today = datetime.date.today().isoformat()
        current_balance_usd = self._money((summary or {}).get('cash_balance', 0))
        incoming = Decimal('0')
        outgoing = Decimal('0')
        try:
            from database.connection import DatabaseConnection
            conn = DatabaseConnection().get_connection()
            # Current cashbox balance from the authoritative cash movement table.
            try:
                row = conn.execute("""
                    SELECT COALESCE(SUM(CAST(amount AS REAL)), 0) AS balance
                    FROM cash_bank_movements
                    WHERE cashbox_id IS NOT NULL
                """).fetchone()
                if row is not None:
                    current_balance_usd = self._money(row['balance'] if hasattr(row, 'keys') else row[0])
            except Exception:
                pass
            rows = conn.execute("""
                SELECT amount, direction, movement_date, created_at
                FROM cash_bank_movements
                WHERE cashbox_id IS NOT NULL
                  AND substr(COALESCE(movement_date, created_at, ''), 1, 10) = ?
            """, (today,)).fetchall()
            for r in rows:
                row = dict(r)
                amount = self._money(row.get('amount'))
                direction = str(row.get('direction') or '').lower()
                if direction == 'out' or amount < 0:
                    outgoing += abs(amount)
                else:
                    incoming += abs(amount)
        except Exception:
            # Fallback through service API.  This is less direct but keeps the card
            # useful if the database schema is older or remote.
            try:
                movements = cashbox_service.movements(limit=5000)
                cashboxes = cashbox_service.cashboxes(True)
                if cashboxes:
                    current_balance_usd = sum(self._money(c.get('balance')) for c in cashboxes)
                for m in movements:
                    date_text = str(m.get('movement_date') or m.get('created_at') or '')[:10]
                    if date_text != today:
                        continue
                    amount = self._money(m.get('amount'))
                    direction = str(m.get('direction') or '').lower()
                    if direction == 'out' or amount < 0:
                        outgoing += abs(amount)
                    else:
                        incoming += abs(amount)
            except Exception:
                pass
        net = incoming - outgoing
        opening = current_balance_usd - net
        return {
            'opening': self._fmt_money(opening, display_curr),
            'in': self._fmt_money(incoming, display_curr),
            'out': self._fmt_money(outgoing, display_curr),
            'net': self._fmt_money(net, display_curr),
            'closing': self._fmt_money(current_balance_usd, display_curr),
        }

    def load_work_alerts(self):
        try:
            alerts = alert_service.dashboard_alerts(limit=5)
            lines = []
            for a in alerts:
                prefix = self._severity_label(a.get('severity', 'info'))
                title = a.get('title', '')
                message = a.get('message', '')
                lines.append(f"{prefix} {title} — {message}" if message else f"{prefix} {title}")
            if not lines:
                lines = ['✅ لا توجد تنبيهات تشغيلية حالياً']
            self.work_alerts_card.set_lines(lines)
        except Exception as e:
            self.work_alerts_card.set_lines([f'تعذر تحميل التنبيهات: {e}'])

    def load_recent_operations(self):
        try:
            from database.connection import DatabaseConnection
            conn = DatabaseConnection().get_connection()
            rows = conn.execute(
                """
                SELECT action, COALESCE(entity_type, table_name, '') AS entity,
                       COALESCE(entity_id, record_id, '') AS rid,
                       COALESCE(event_time, timestamp, '') AS ts, username
                FROM audit_log
                ORDER BY id DESC
                LIMIT 5
                """
            ).fetchall()
            lines = []
            entity_labels = {
                'INVOICE': 'فاتورة', 'ITEM': 'مادة', 'CUSTOMER': 'عميل',
                'SUPPLIER': 'مورد', 'VOUCHER': 'سند', 'CASHBOX': 'صندوق',
                'BANK_ACCOUNT': 'حساب بنكي', 'RETURN': 'مرتجع', 'POS_SHIFT': 'وردية',
            }
            action_labels = {
                'CREATE': 'إنشاء', 'UPDATE': 'تعديل', 'DELETE': 'حذف',
                'SOFT_DELETE': 'أرشفة', 'POS_SHIFT_OPEN': 'فتح وردية',
                'POS_SHIFT_CLOSE': 'إغلاق وردية',
            }
            for r in rows:
                row = dict(r)
                action = action_labels.get(str(row.get('action') or ''), str(row.get('action') or 'عملية'))
                entity = entity_labels.get(str(row.get('entity') or ''), str(row.get('entity') or 'سجل'))
                rid = row.get('rid') or ''
                ts = str(row.get('ts') or '')[:16].replace('T', ' ')
                lines.append(f"{action} {entity} #{rid} — {ts}")
            self.recent_ops_card.set_lines(lines or ['لا توجد عمليات مسجلة بعد'])
        except Exception:
            self.recent_ops_card.set_lines(['لا توجد عمليات مسجلة بعد'])

    def load_alerts(self):
        try:
            alerts = alert_service.dashboard_alerts(limit=8)
        except Exception:
            alerts = []
        data = []
        for a in alerts:
            data.append({
                'severity': self._severity_label(a.get('severity', 'info')),
                'title': a.get('title', ''),
                'message': a.get('message', ''),
            })
        if not data:
            data = [{'severity': '✅', 'title': 'لا توجد تنبيهات', 'message': 'كل المؤشرات التشغيلية ضمن الحدود الحالية'}]
        headers = ['severity', 'title', 'message']
        display_headers = ['الحالة', 'التنبيه', 'التفاصيل']
        model = GenericTableModel(data, display_headers, key_fields=['title'], data_keys=headers)
        self.alerts_table.setModel(model)
        self.alerts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.alerts_table.refresh_style()

    def _severity_label(self, severity):
        return {'critical': '🔴', 'warning': '🟠', 'info': '🔵'}.get(severity, '🔵')

    def _switch_page(self, page_name):
        main_window = self.window()
        if hasattr(main_window, 'switch_page'):
            main_window.switch_page(page_name)
        else:
            show_toast("لا يمكن الانتقال إلى الصفحة المطلوبة", "error", self)

    def apply_theme_colors(self):
        self.refresh_all()


