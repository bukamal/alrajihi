# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QGridLayout, QPushButton, QComboBox, QHeaderView)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer
from decimal import Decimal
from core.services.dashboard_service import dashboard_service
from core.services.alert_service import alert_service
from currency import currency
from views.custom_table_view import CustomTableView
from models.table_models import GenericTableModel
from utils import show_toast
import qtawesome as qta

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
        self.cards['cash'] = KPICard("رصيد الصندوق", "0", "money-bill-wave", "#10b981")
        self.cards['sales'] = KPICard("إجمالي المبيعات", "0", "chart-line", "#3b82f6")
        self.cards['purchases'] = KPICard("إجمالي المشتريات", "0", "shopping-cart", "#f59e0b")
        self.cards['expenses'] = KPICard("إجمالي المصروفات", "0", "receipt", "#ef4444")
        self.cards['receivables'] = KPICard("الذمم المدينة", "0", "users", "#8b5cf6")
        self.cards['payables'] = KPICard("الذمم الدائنة", "0", "truck", "#ec4899")
        self.cards['net_profit'] = KPICard("صافي الربح", "0", "chart-pie", "#14b8a6")
        self.actions_card = self.create_actions_card()

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

        pos_btn = QPushButton(qta.icon('fa5s.barcode'), " نقطة البيع POS   F9")
        pos_btn.setObjectName("posActionButton")
        pos_btn.setMinimumHeight(58)
        pos_btn.clicked.connect(self._open_pos)
        layout.addWidget(pos_btn)

        grid = QGridLayout()
        grid.setSpacing(8)
        actions = [
            ("فاتورة بيع", 'file-invoice-dollar', '#10b981', lambda: self._open_invoice('sale')),
            ("فاتورة شراء", 'shopping-cart', '#f59e0b', lambda: self._open_invoice('purchase')),
            ("إضافة مادة", 'box', '#3b82f6', self._open_add_item),
            ("إضافة عميل", 'user-plus', '#8b5cf6', self._open_add_customer),
            ("إضافة مورد", 'truck-loading', '#ec4899', self._open_add_supplier),
            ("سند قبض", 'hand-holding-usd', '#14b8a6', lambda: self._open_voucher('receipt')),
            ("سند دفع", 'money-bill-wave', '#ef4444', lambda: self._open_voucher('payment')),
            ("المواد", 'boxes', '#64748b', lambda: self._switch_page('items')),
        ]
        for i, (text, icon, color, callback) in enumerate(actions):
            btn = QPushButton(qta.icon(f'fa5s.{icon}'), f" {text}")
            btn.setProperty("class", "quick-action")
            btn.setStyleSheet(f"background-color: {color};")
            btn.clicked.connect(callback)
            btn.setMinimumHeight(42)
            grid.addWidget(btn, i // 2, i % 2)
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
        self.card_grid.addWidget(self.cards['cash'], 0, 0)
        self.card_grid.addWidget(self.cards['sales'], 0, 1)
        self.card_grid.addWidget(self.cards['purchases'], 0, 2)
        self.card_grid.addWidget(self.cards['expenses'], 1, 0)
        self.card_grid.addWidget(self.cards['receivables'], 1, 1)
        self.card_grid.addWidget(self.cards['payables'], 1, 2)
        self.card_grid.addWidget(self.cards['net_profit'], 2, 0)
        self.card_grid.addWidget(self.actions_card, 2, 1, 1, 2)
        for col in range(3):
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
        if not hasattr(self, 'cards') or not self.cards:
            return

        display_curr = currency.get_display_currency()
        self.update_rate_label(display_curr)
        snapshot = dashboard_service.snapshot(use_cache=False)
        summary = snapshot.get('summary', {})

        for key, card_key in (
            ('cash_balance', 'cash'),
            ('total_sales', 'sales'),
            ('total_purchases', 'purchases'),
            ('total_expenses', 'expenses'),
            ('receivables', 'receivables'),
            ('payables', 'payables'),
            ('net_profit', 'net_profit'),
        ):
            amount = currency.convert(Decimal(str(summary.get(key, 0))), 'USD', display_curr)
            self.cards[card_key].set_value(currency.format_amount(amount))

        self.load_alerts()

    def load_alerts(self):
        alerts = alert_service.dashboard_alerts(limit=8)
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


