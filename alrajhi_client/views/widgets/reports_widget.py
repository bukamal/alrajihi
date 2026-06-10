# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
                             QDateEdit, QLabel, QTabWidget, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt, QDate
from decimal import Decimal
from core.services.reporting_service import reporting_service
from currency import currency
from views.custom_table_view import CustomTableView
from models.table_models import GenericTableModel

class ReportsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        layout = QVBoxLayout(self)

        # شريط التحكم بالفترة
        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel("الفترة:"))
        self.period_type = QComboBox()
        self.period_type.addItems(["شهر محدد", "سنة محددة", "فترة مخصصة"])
        self.period_type.currentIndexChanged.connect(self.on_period_type_changed)
        period_layout.addWidget(self.period_type)

        self.year_combo = QComboBox()
        from datetime import datetime
        current_year = datetime.now().year
        for y in range(current_year - 5, current_year + 2):
            self.year_combo.addItem(str(y))
        period_layout.addWidget(self.year_combo)

        self.month_combo = QComboBox()
        self.month_combo.addItems(["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
                                   "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"])
        period_layout.addWidget(self.month_combo)

        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        period_layout.addWidget(self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        period_layout.addWidget(self.end_date)

        refresh_btn = QPushButton("تحديث")
        refresh_btn.clicked.connect(self.refresh_report)
        period_layout.addWidget(refresh_btn)

        print_btn = QPushButton("طباعة")
        print_btn.clicked.connect(self.print_report)
        period_layout.addWidget(print_btn)

        layout.addLayout(period_layout)

        self.tabs = QTabWidget()
        self.income_tab = QWidget()
        self.balance_tab = QWidget()
        self.setup_income_tab()
        self.setup_balance_tab()
        self.tabs.addTab(self.income_tab, "قائمة الدخل")
        self.tabs.addTab(self.balance_tab, "الميزانية العمومية")
        layout.addWidget(self.tabs)

        self.on_period_type_changed()
        self.refresh_report()

    def on_period_type_changed(self):
        period = self.period_type.currentIndex()
        self.year_combo.setVisible(period in (0, 1))
        self.month_combo.setVisible(period == 0)
        self.start_date.setVisible(period == 2)
        self.end_date.setVisible(period == 2)

    def get_date_range(self):
        period = self.period_type.currentIndex()
        if period == 0:
            year = int(self.year_combo.currentText())
            month = self.month_combo.currentIndex() + 1
            from datetime import date
            start = date(year, month, 1)
            if month == 12:
                end = date(year, month, 31)
            else:
                end = date(year, month+1, 1) - __import__('datetime').timedelta(days=1)
            return start.isoformat(), end.isoformat()
        elif period == 1:
            year = int(self.year_combo.currentText())
            return f"{year}-01-01", f"{year}-12-31"
        else:
            return self.start_date.date().toString("yyyy-MM-dd"), self.end_date.date().toString("yyyy-MM-dd")

    def setup_income_tab(self):
        layout = QVBoxLayout(self.income_tab)
        self.income_table = CustomTableView()
        layout.addWidget(self.income_table)

    def setup_balance_tab(self):
        layout = QVBoxLayout(self.balance_tab)
        self.balance_table = CustomTableView()
        layout.addWidget(self.balance_table)

    def refresh_report(self):
        start, end = self.get_date_range()
        stmt = reporting_service.income_statement(start, end)
        display_curr = currency.get_display_currency()
        
        # بناء بيانات قائمة الدخل
        income_data = []
        for inc in stmt.get('income', []):
            amount = currency.convert(Decimal(str(inc.get('balance', 0))), 'USD', display_curr)
            income_data.append([inc.get('name', ''), currency.format_amount(amount)])
        
        total_income = currency.convert(Decimal(str(stmt.get('total_income', 0))), 'USD', display_curr)
        income_data.append(["إجمالي الإيرادات", currency.format_amount(total_income)])
        income_data.append([])  # فاصل
        
        for exp in stmt.get('expenses', []):
            amount = currency.convert(Decimal(str(exp.get('balance', 0))), 'USD', display_curr)
            income_data.append([exp.get('name', ''), currency.format_amount(amount)])
        
        total_expenses = currency.convert(Decimal(str(stmt.get('total_expenses', 0))), 'USD', display_curr)
        income_data.append(["إجمالي المصروفات", currency.format_amount(total_expenses)])
        
        net_profit = currency.convert(Decimal(str(stmt.get('net_profit', 0))), 'USD', display_curr)
        income_data.append(["صافي الربح", currency.format_amount(net_profit)])
        
        # بناء النموذج
        income_list = []
        for item in income_data:
            if len(item) >= 2:
                income_list.append({'statement': item[0], 'amount': item[1]})
            else:
                income_list.append({'statement': '', 'amount': ''})
        
        income_model = GenericTableModel(income_list, ['البيان', 'المبلغ'], data_keys=['statement', 'amount'])
        self.income_table.setModel(income_model)
        self.income_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # بناء الميزانية العمومية
        bs = reporting_service.balance_sheet(start, end)
        assets = []
        for a in bs.get('assets', []):
            amount = currency.convert(Decimal(str(a.get('debit', 0))), 'USD', display_curr)
            assets.append([a.get('name', ''), currency.format_amount(amount)])
        total_assets = currency.convert(Decimal(str(bs.get('total_assets', 0))), 'USD', display_curr)
        assets.append(["إجمالي الأصول", currency.format_amount(total_assets)])
        
        # عرض الأصول فقط في هذا الجدول المبسط
        balance_list = []
        for item in assets:
            if len(item) >= 2:
                balance_list.append({'account': item[0], 'amount': item[1]})
            else:
                balance_list.append({'account': '', 'amount': ''})
        
        balance_model = GenericTableModel(balance_list, ['الحساب', 'المبلغ'], data_keys=['account', 'amount'])
        self.balance_table.setModel(balance_model)
        self.balance_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def print_report(self):
        from printing.printing_service import printing_service
        start, end = self.get_date_range()
        stmt = reporting_service.income_statement(start, end)
        display_curr = currency.get_display_currency()
        rows = []
        for inc in stmt.get('income', []):
            amount = currency.convert(Decimal(str(inc.get('balance', 0))), 'USD', display_curr)
            rows.append([inc.get('name', ''), currency.format_amount(amount)])
        total_income = currency.convert(Decimal(str(stmt.get('total_income', 0))), 'USD', display_curr)
        rows.append(['إجمالي الإيرادات', currency.format_amount(total_income)])
        rows.append(['', ''])
        for exp in stmt.get('expenses', []):
            amount = currency.convert(Decimal(str(exp.get('balance', 0))), 'USD', display_curr)
            rows.append([exp.get('name', ''), currency.format_amount(amount)])
        total_expenses = currency.convert(Decimal(str(stmt.get('total_expenses', 0))), 'USD', display_curr)
        rows.append(['إجمالي المصروفات', currency.format_amount(total_expenses)])
        net_profit = currency.convert(Decimal(str(stmt.get('net_profit', 0))), 'USD', display_curr)
        rows.append(['صافي الربح', currency.format_amount(net_profit)])
        printing_service.report_preview('قائمة الدخل', rows, ['البيان', 'المبلغ'], self, subtitle=f'الفترة: {start} إلى {end}', summary={
            'إجمالي الإيرادات': data.get('sales', data.get('revenue', 0)),
            'إجمالي المصروفات': data.get('expenses', 0),
            'صافي الربح': data.get('net_profit', data.get('profit', 0)),
        })

