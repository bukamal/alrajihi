# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
                             QDateEdit, QLabel, QTabWidget, QHeaderView)
from PyQt5.QtCore import Qt, QDate
from decimal import Decimal
from core.services.reporting_service import reporting_service
from core.services.warehouse_service import warehouse_service
from currency import currency
from views.custom_table_view import CustomTableView
from models.table_models import GenericTableModel


class ReportsWidget(QWidget):
    """Financial and warehouse reports.

    Warehouse-5 adds valuation, balances, movements and transfers while keeping
    financial reports unchanged. All report data is read through services.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        layout = QVBoxLayout(self)

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

        period_layout.addWidget(QLabel("المستودع:"))
        self.warehouse_filter = QComboBox()
        self._load_warehouses()
        period_layout.addWidget(self.warehouse_filter)

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
        self.wh_valuation_tab = QWidget()
        self.wh_balances_tab = QWidget()
        self.wh_movements_tab = QWidget()
        self.wh_transfers_tab = QWidget()
        self.setup_income_tab()
        self.setup_balance_tab()
        self.setup_warehouse_tabs()
        self.tabs.addTab(self.income_tab, "قائمة الدخل")
        self.tabs.addTab(self.balance_tab, "الميزانية العمومية")
        self.tabs.addTab(self.wh_valuation_tab, "تقييم المستودعات")
        self.tabs.addTab(self.wh_balances_tab, "أرصدة المستودعات")
        self.tabs.addTab(self.wh_movements_tab, "حركات المستودعات")
        self.tabs.addTab(self.wh_transfers_tab, "تحويلات المستودعات")
        layout.addWidget(self.tabs)

        self.on_period_type_changed()
        self.refresh_report()

    def _load_warehouses(self):
        self.warehouse_filter.clear()
        self.warehouse_filter.addItem("كل المستودعات", None)
        try:
            for wh in warehouse_service.warehouses(include_archived=False):
                self.warehouse_filter.addItem(wh.get('name', ''), wh.get('id'))
        except Exception:
            pass

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
        return self.start_date.date().toString("yyyy-MM-dd"), self.end_date.date().toString("yyyy-MM-dd")

    def setup_income_tab(self):
        layout = QVBoxLayout(self.income_tab)
        self.income_table = CustomTableView()
        layout.addWidget(self.income_table)

    def setup_balance_tab(self):
        layout = QVBoxLayout(self.balance_tab)
        self.balance_table = CustomTableView()
        layout.addWidget(self.balance_table)

    def setup_warehouse_tabs(self):
        self.wh_valuation_status = QLabel()
        val_layout = QVBoxLayout(self.wh_valuation_tab)
        val_layout.addWidget(self.wh_valuation_status)
        self.wh_valuation_table = CustomTableView()
        val_layout.addWidget(self.wh_valuation_table)

        self.wh_balances_status = QLabel()
        bal_layout = QVBoxLayout(self.wh_balances_tab)
        bal_layout.addWidget(self.wh_balances_status)
        self.wh_balances_table = CustomTableView()
        bal_layout.addWidget(self.wh_balances_table)

        mov_layout = QVBoxLayout(self.wh_movements_tab)
        self.wh_movements_table = CustomTableView()
        mov_layout.addWidget(self.wh_movements_table)

        trans_layout = QVBoxLayout(self.wh_transfers_tab)
        self.wh_transfers_table = CustomTableView()
        trans_layout.addWidget(self.wh_transfers_table)

    def _set_table(self, table, rows, headers, keys):
        model = GenericTableModel(rows, headers, data_keys=keys)
        table.setModel(model)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.horizontalHeader().setStretchLastSection(True)
        return model

    def refresh_report(self):
        start, end = self.get_date_range()
        display_curr = currency.get_display_currency()
        self._refresh_income(start, end, display_curr)
        self._refresh_balance(start, end, display_curr)
        self._refresh_warehouse_reports(display_curr)

    def _refresh_income(self, start, end, display_curr):
        stmt = reporting_service.income_statement(start, end)
        income_list = []
        for inc in stmt.get('income', []):
            amount = currency.convert(Decimal(str(inc.get('balance', 0))), 'USD', display_curr)
            income_list.append({'statement': inc.get('name', ''), 'amount': currency.format_amount(amount)})
        total_income = currency.convert(Decimal(str(stmt.get('total_income', 0))), 'USD', display_curr)
        income_list.append({'statement': 'إجمالي الإيرادات', 'amount': currency.format_amount(total_income)})
        income_list.append({'statement': '', 'amount': ''})
        for exp in stmt.get('expenses', []):
            amount = currency.convert(Decimal(str(exp.get('balance', 0))), 'USD', display_curr)
            income_list.append({'statement': exp.get('name', ''), 'amount': currency.format_amount(amount)})
        total_expenses = currency.convert(Decimal(str(stmt.get('total_expenses', 0))), 'USD', display_curr)
        net_profit = currency.convert(Decimal(str(stmt.get('net_profit', 0))), 'USD', display_curr)
        income_list.append({'statement': 'إجمالي المصروفات', 'amount': currency.format_amount(total_expenses)})
        income_list.append({'statement': 'صافي الربح', 'amount': currency.format_amount(net_profit)})
        self._set_table(self.income_table, income_list, ['البيان', 'المبلغ'], ['statement', 'amount'])

    def _refresh_balance(self, start, end, display_curr):
        bs = reporting_service.balance_sheet(start, end)
        rows = []
        for a in bs.get('assets', []):
            amount = currency.convert(Decimal(str(a.get('debit', 0))), 'USD', display_curr)
            rows.append({'account': a.get('name', ''), 'amount': currency.format_amount(amount)})
        total_assets = currency.convert(Decimal(str(bs.get('total_assets', 0))), 'USD', display_curr)
        rows.append({'account': 'إجمالي الأصول', 'amount': currency.format_amount(total_assets)})
        self._set_table(self.balance_table, rows, ['الحساب', 'المبلغ'], ['account', 'amount'])

    def _refresh_warehouse_reports(self, display_curr):
        wh_id = self.warehouse_filter.currentData()
        valuation = reporting_service.warehouse_valuation(warehouse_id=wh_id)
        val_rows = []
        for wh in valuation.get('warehouses', []):
            val = currency.convert(Decimal(str(wh.get('total_value', 0))), 'USD', display_curr)
            val_rows.append({
                'warehouse': wh.get('warehouse_name', ''),
                'item_count': wh.get('item_count', 0),
                'total_qty': f"{Decimal(str(wh.get('total_qty', 0))):.2f}",
                'total_value': currency.format_amount(val),
            })
        grand = currency.convert(Decimal(str(valuation.get('grand_total', 0))), 'USD', display_curr)
        self.wh_valuation_status.setText(f"إجمالي قيمة المخزون: {currency.format_amount(grand)}")
        self._set_table(self.wh_valuation_table, val_rows, ['المستودع', 'عدد المواد', 'إجمالي الكميات', 'قيمة المخزون'], ['warehouse', 'item_count', 'total_qty', 'total_value'])

        bal_rows = []
        total_value = Decimal('0')
        for b in reporting_service.warehouse_balances(warehouse_id=wh_id):
            qty = Decimal(str(b.get('quantity') or 0))
            avg = Decimal(str(b.get('average_cost') or 0))
            value = Decimal(str(b.get('stock_value') if b.get('stock_value') is not None else qty * avg))
            total_value += value
            bal_rows.append({
                'warehouse': b.get('warehouse_name', ''),
                'item': b.get('item_name', ''),
                'barcode': b.get('barcode') or '—',
                'qty': f"{qty:.2f}",
                'unit': b.get('unit') or '',
                'avg': currency.format_amount(avg),
                'value': currency.format_amount(value),
            })
        self.wh_balances_status.setText(f"عدد السجلات: {len(bal_rows)} | إجمالي القيمة: {currency.format_amount(total_value)}")
        self._set_table(self.wh_balances_table, bal_rows, ['المستودع', 'المادة', 'الباركود', 'الكمية', 'الوحدة', 'متوسط التكلفة', 'قيمة المخزون'], ['warehouse', 'item', 'barcode', 'qty', 'unit', 'avg', 'value'])

        mov_rows = []
        for m in reporting_service.warehouse_movements(warehouse_id=wh_id, limit=500):
            mov_rows.append({
                'date': m.get('movement_date') or m.get('created_at') or '',
                'warehouse': m.get('warehouse_name', ''),
                'item': m.get('item_name', ''),
                'type': self._movement_label(m.get('movement_type')),
                'qty': m.get('quantity') or '0',
                'cost': currency.format_amount(m.get('unit_cost') or 0),
                'ref': m.get('reference_type') or '—',
                'notes': m.get('notes') or '',
            })
        self._set_table(self.wh_movements_table, mov_rows, ['التاريخ', 'المستودع', 'المادة', 'النوع', 'الكمية', 'التكلفة', 'المرجع', 'ملاحظات'], ['date', 'warehouse', 'item', 'type', 'qty', 'cost', 'ref', 'notes'])

        trans_rows = []
        for t in reporting_service.warehouse_transfers(limit=500):
            if wh_id and wh_id not in (t.get('from_warehouse_id'), t.get('to_warehouse_id')):
                continue
            trans_rows.append({
                'no': t.get('transfer_no') or '',
                'date': t.get('created_at') or '',
                'item': t.get('item_name') or '',
                'from': t.get('from_warehouse_name') or '',
                'to': t.get('to_warehouse_name') or '',
                'qty': t.get('quantity') or '0',
                'status': 'ملغى' if t.get('status') == 'cancelled' else 'نشط',
                'notes': t.get('notes') or '',
            })
        self._set_table(self.wh_transfers_table, trans_rows, ['رقم التحويل', 'التاريخ', 'المادة', 'من', 'إلى', 'الكمية', 'الحالة', 'ملاحظات'], ['no', 'date', 'item', 'from', 'to', 'qty', 'status', 'notes'])

    def _movement_label(self, mtype):
        return {
            'migration_opening': 'ترحيل افتتاحي',
            'opening': 'افتتاحي',
            'invoice_sale_out': 'صرف فاتورة بيع',
            'invoice_purchase_in': 'استلام فاتورة شراء',
            'transfer_out': 'تحويل صادر',
            'transfer_in': 'تحويل وارد',
            'transfer_cancel_out': 'إلغاء تحويل صادر',
            'transfer_cancel_in': 'إلغاء تحويل وارد',
            'production_consume_out': 'استهلاك إنتاج',
            'production_output_in': 'إنتاج وارد',
            'adjustment': 'تسوية',
        }.get(mtype or '', mtype or '')

    def print_report(self):
        from printing.printing_service import printing_service
        start, end = self.get_date_range()
        tab = self.tabs.currentWidget()
        title = self.tabs.tabText(self.tabs.currentIndex())
        table = None
        if tab is self.income_tab:
            table = self.income_table
        elif tab is self.balance_tab:
            table = self.balance_table
        elif tab is self.wh_valuation_tab:
            table = self.wh_valuation_table
        elif tab is self.wh_balances_tab:
            table = self.wh_balances_table
        elif tab is self.wh_movements_tab:
            table = self.wh_movements_table
        elif tab is self.wh_transfers_tab:
            table = self.wh_transfers_table
        if not table or not table.model():
            return
        model = table.model()
        headers = [model.headerData(i, Qt.Horizontal, Qt.DisplayRole) for i in range(model.columnCount())]
        rows = []
        for r in range(model.rowCount()):
            rows.append([model.data(model.index(r, c), Qt.DisplayRole) or '' for c in range(model.columnCount())])
        printing_service.report_preview(title, rows, headers, self, subtitle=f'الفترة: {start} إلى {end}')
