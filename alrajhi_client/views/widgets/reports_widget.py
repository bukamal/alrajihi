# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
                             QDateEdit, QLabel, QTabWidget, QHeaderView, QMenu)
from PyQt5.QtCore import Qt, QDate
from i18n import translate as tr, qt_layout_direction
from decimal import Decimal
from core.services.reporting_service import reporting_service
from core.services.settings_service import settings_service
from core.services.warehouse_service import warehouse_service
from core.services.entity_service import entity_service
from currency import currency
from views.custom_table_view import CustomTableView
from models.table_models import GenericTableModel
from views.widgets.modern_ui import apply_modern_widget


class ReportsWidget(QWidget):
    """Financial and warehouse reports.

    Warehouse-5 adds valuation, balances, movements and transfers while keeping
    financial reports unchanged. All report data is read through services.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(qt_layout_direction())
        layout = QVBoxLayout(self)

        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel(tr("period_label")))
        self.period_type = QComboBox()
        self.period_type.addItems([tr("period_month"), tr("period_year"), tr("period_custom")])
        self.period_type.currentIndexChanged.connect(self.on_period_type_changed)
        period_layout.addWidget(self.period_type)

        self.year_combo = QComboBox()
        from datetime import datetime
        current_year = datetime.now().year
        for y in range(current_year - 5, current_year + 2):
            self.year_combo.addItem(str(y))
        period_layout.addWidget(self.year_combo)

        self.month_combo = QComboBox()
        self.month_combo.addItems([tr("month_january"), tr("month_february"), tr("month_march"), tr("month_april"), tr("month_may"), tr("month_june"),
                                   tr("month_july"), tr("month_august"), tr("month_september"), tr("month_october"), tr("month_november"), tr("month_december")])
        period_layout.addWidget(self.month_combo)

        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        period_layout.addWidget(self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        period_layout.addWidget(self.end_date)

        period_layout.addWidget(QLabel(tr("warehouse_label")))
        self.warehouse_filter = QComboBox()
        self._load_warehouses()
        period_layout.addWidget(self.warehouse_filter)

        period_layout.addWidget(QLabel(tr("cashbox_label")))
        self.cashbox_filter = QComboBox()
        self._load_cashboxes()
        period_layout.addWidget(self.cashbox_filter)

        period_layout.addWidget(QLabel(tr("bank_label")))
        self.bank_filter = QComboBox()
        self._load_banks()
        period_layout.addWidget(self.bank_filter)

        period_layout.addWidget(QLabel(tr("customer_label")))
        self.customer_filter = QComboBox()
        self._load_customers()
        period_layout.addWidget(self.customer_filter)

        period_layout.addWidget(QLabel(tr("supplier_label")))
        self.supplier_filter = QComboBox()
        self._load_suppliers()
        period_layout.addWidget(self.supplier_filter)

        period_layout.addWidget(QLabel(tr("item_label")))
        self.item_filter = QComboBox()
        self._load_items()
        period_layout.addWidget(self.item_filter)

        refresh_btn = QPushButton(tr("refresh_report"))
        refresh_btn.clicked.connect(self.refresh_report)
        period_layout.addWidget(refresh_btn)

        reset_btn = QPushButton(tr("reset_filters"))
        reset_btn.clicked.connect(self.reset_report_filters)
        period_layout.addWidget(reset_btn)

        print_btn = QPushButton(tr("printing"))
        print_menu = QMenu(print_btn)
        print_menu.addAction(tr("preview_in_app"), lambda: self.print_report('preview'))
        print_menu.addAction(tr("open_html_browser"), lambda: self.print_report('browser'))  # فتح HTML في المتصفح
        print_menu.addAction(tr("direct_print"), lambda: self.print_report('direct'))
        print_menu.addAction(tr("export_pdf"), lambda: self.print_report('pdf'))
        print_btn.setMenu(print_menu)
        period_layout.addWidget(print_btn)

        layout.addLayout(period_layout)

        self.tabs = QTabWidget()
        self.income_tab = QWidget()
        self.balance_tab = QWidget()
        self.wh_valuation_tab = QWidget()
        self.wh_balances_tab = QWidget()
        self.wh_movements_tab = QWidget()
        self.wh_transfers_tab = QWidget()
        self.cash_summary_tab = QWidget()
        self.cash_movements_tab = QWidget()
        self.bank_movements_tab = QWidget()
        self.pos_shifts_tab = QWidget()
        self.trial_balance_tab = QWidget()
        self.customer_statement_tab = QWidget()
        self.supplier_statement_tab = QWidget()
        self.customer_balances_tab = QWidget()
        self.supplier_balances_tab = QWidget()
        self.customer_aging_tab = QWidget()
        self.supplier_aging_tab = QWidget()
        self.ledger_reconciliation_tab = QWidget()
        self.ledger_dual_read_tab = QWidget()
        self.ledger_readiness_tab = QWidget()
        self.offline_queue_tab = QWidget()
        self.unit_audit_tab = QWidget()
        self.item_movement_tab = QWidget()
        self.invoice_profit_tab = QWidget()
        self.net_profit_tab = QWidget()
        self.manufacturing_orders_tab = QWidget()
        self.product_cost_tab = QWidget()
        self.general_ledger_tab = QWidget()
        self.full_trial_balance_tab = QWidget()
        self.slow_items_tab = QWidget()
        self.top_items_tab = QWidget()
        self.low_items_tab = QWidget()
        self.reorder_items_tab = QWidget()
        self.report_audit_tab = QWidget()
        self.setup_income_tab()
        self.setup_balance_tab()
        self.setup_warehouse_tabs()
        self.setup_cash_bank_tabs()
        self.setup_phase36_tabs()
        self.tabs.addTab(self.income_tab, tr("report_income_statement"))
        self.tabs.addTab(self.balance_tab, tr("report_balance_sheet"))
        self.tabs.addTab(self.wh_valuation_tab, tr("report_warehouse_valuation"))
        self.tabs.addTab(self.wh_balances_tab, tr("report_warehouse_balances"))
        self.tabs.addTab(self.wh_movements_tab, tr("report_warehouse_movements"))
        self.tabs.addTab(self.wh_transfers_tab, tr("report_warehouse_transfers"))
        self.tabs.addTab(self.cash_summary_tab, tr("report_cash_bank_summary"))
        self.tabs.addTab(self.cash_movements_tab, tr("report_cash_movements"))
        self.tabs.addTab(self.bank_movements_tab, tr("report_bank_movements"))
        self.tabs.addTab(self.pos_shifts_tab, tr("report_pos_shifts"))
        self.tabs.addTab(self.trial_balance_tab, tr("report_trial_balance"))
        self.tabs.addTab(self.customer_statement_tab, tr("report_customer_statement"))
        self.tabs.addTab(self.supplier_statement_tab, tr("report_supplier_statement"))
        self.tabs.addTab(self.item_movement_tab, tr("report_item_movement"))
        self.tabs.addTab(self.invoice_profit_tab, tr("report_invoice_profit"))
        self.tabs.addTab(self.net_profit_tab, tr("report_net_profit"))
        self.tabs.addTab(self.manufacturing_orders_tab, tr("report_manufacturing_orders"))
        self.tabs.addTab(self.product_cost_tab, tr("report_product_cost"))
        self.tabs.addTab(self.general_ledger_tab, tr("report_general_ledger"))
        self.tabs.addTab(self.full_trial_balance_tab, tr("report_full_trial_balance"))
        self.tabs.addTab(self.slow_items_tab, tr("report_slow_items"))
        self.tabs.addTab(self.top_items_tab, tr("report_top_items"))
        self.tabs.addTab(self.low_items_tab, tr("report_low_items"))
        self.tabs.addTab(self.reorder_items_tab, tr("report_reorder_items"))
        self.tabs.addTab(self.report_audit_tab, tr("report_consistency_audit"))
        self.tabs.addTab(self.customer_balances_tab, tr("report_customer_balances"))
        self.tabs.addTab(self.supplier_balances_tab, tr("report_supplier_balances"))
        self.tabs.addTab(self.customer_aging_tab, tr("report_customer_aging"))
        self.tabs.addTab(self.supplier_aging_tab, tr("report_supplier_aging"))
        self.tabs.addTab(self.ledger_reconciliation_tab, tr("report_ledger_reconciliation"))
        self.tabs.addTab(self.ledger_dual_read_tab, tr("report_ledger_dual_read"))
        self.tabs.addTab(self.ledger_readiness_tab, tr("report_ledger_readiness"))
        self.tabs.addTab(self.offline_queue_tab, tr("report_offline_queue"))
        self.tabs.addTab(self.unit_audit_tab, tr("report_unit_audit"))
        self._apply_pos_shift_report_visibility()
        self.tabs.currentChanged.connect(lambda _idx: self.refresh_report())
        layout.addWidget(self.tabs)

        self.report_summary = QLabel()
        self.report_summary.setObjectName('reportSummaryBar')
        self.report_summary.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.report_summary)

        self._install_report_table_identities()
        self.on_period_type_changed()
        apply_modern_widget(self, tr('reports_page_title'), tr('reports_page_subtitle'))
        self.refresh_report()

    def _load_warehouses(self):
        self.warehouse_filter.clear()
        self.warehouse_filter.addItem(tr("all_warehouses"), None)
        try:
            for wh in warehouse_service.warehouses(include_archived=False):
                self.warehouse_filter.addItem(wh.get('name', ''), wh.get('id'))
        except Exception:
            pass

    def _load_cashboxes(self):
        self.cashbox_filter.clear()
        self.cashbox_filter.addItem(tr("all_cashboxes"), None)
        try:
            for c in reporting_service.cashboxes_report():
                self.cashbox_filter.addItem(c.get('name', ''), c.get('id'))
        except Exception:
            pass

    def _load_banks(self):
        self.bank_filter.clear()
        self.bank_filter.addItem(tr("all_banks"), None)
        try:
            for b in reporting_service.bank_accounts_report():
                title = b.get('bank_name') or ''
                if b.get('account_name'):
                    title += f" - {b.get('account_name')}"
                self.bank_filter.addItem(title, b.get('id'))
        except Exception:
            pass

    def _load_customers(self):
        self.customer_filter.clear()
        self.customer_filter.addItem(tr("choose_customer"), None)
        try:
            rows, _ = entity_service.customers(limit=1000)
            for c in rows:
                self.customer_filter.addItem(c.get('name', ''), c.get('id'))
        except Exception:
            pass

    def _load_suppliers(self):
        self.supplier_filter.clear()
        self.supplier_filter.addItem(tr("choose_supplier"), None)
        try:
            rows, _ = entity_service.suppliers(limit=1000)
            for s in rows:
                self.supplier_filter.addItem(s.get('name', ''), s.get('id'))
        except Exception:
            pass

    def _load_items(self):
        self.item_filter.clear()
        self.item_filter.addItem(tr("all_items"), None)
        try:
            from core.services.product_service import product_service
            rows = product_service.items(limit=2000)
            for item in rows or []:
                label = item.get('name', '')
                if item.get('barcode'):
                    label = f"{label} - {item.get('barcode')}"
                self.item_filter.addItem(label, item.get('id'))
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

    def setup_cash_bank_tabs(self):
        self.cash_summary_status = QLabel()
        cash_layout = QVBoxLayout(self.cash_summary_tab)
        cash_layout.addWidget(self.cash_summary_status)
        self.cash_summary_table = CustomTableView()
        cash_layout.addWidget(self.cash_summary_table)

        cash_mov_layout = QVBoxLayout(self.cash_movements_tab)
        self.cash_movements_table = CustomTableView()
        cash_mov_layout.addWidget(self.cash_movements_table)

        bank_mov_layout = QVBoxLayout(self.bank_movements_tab)
        self.bank_movements_table = CustomTableView()
        bank_mov_layout.addWidget(self.bank_movements_table)

        shifts_layout = QVBoxLayout(self.pos_shifts_tab)
        self.pos_shifts_table = CustomTableView()
        shifts_layout.addWidget(self.pos_shifts_table)

    def setup_phase36_tabs(self):
        for attr, tab in [
            ('trial_balance_table', self.trial_balance_tab),
            ('customer_statement_table', self.customer_statement_tab),
            ('supplier_statement_table', self.supplier_statement_tab),
            ('customer_balances_table', self.customer_balances_tab),
            ('supplier_balances_table', self.supplier_balances_tab),
            ('customer_aging_table', self.customer_aging_tab),
            ('supplier_aging_table', self.supplier_aging_tab),
            ('ledger_reconciliation_table', self.ledger_reconciliation_tab),
            ('ledger_dual_read_table', self.ledger_dual_read_tab),
            ('ledger_readiness_table', self.ledger_readiness_tab),
            ('offline_queue_table', self.offline_queue_tab),
            ('unit_audit_table', self.unit_audit_tab),
            ('item_movement_table', self.item_movement_tab),
            ('invoice_profit_table', self.invoice_profit_tab),
            ('net_profit_table', self.net_profit_tab),
            ('manufacturing_orders_table', self.manufacturing_orders_tab),
            ('product_cost_table', self.product_cost_tab),
            ('general_ledger_table', self.general_ledger_tab),
            ('full_trial_balance_table', self.full_trial_balance_tab),
            ('slow_items_table', self.slow_items_tab),
            ('top_items_table', self.top_items_tab),
            ('low_items_table', self.low_items_tab),
            ('reorder_items_table', self.reorder_items_tab),
            ('report_audit_table', self.report_audit_tab),
        ]:
            layout = QVBoxLayout(tab)
            table = CustomTableView()
            setattr(self, attr, table)
            layout.addWidget(table)

    def _install_report_table_identities(self):
        """Attach stable identities for saved column layouts and unified print titles."""
        for name in (
            'income_table', 'balance_table', 'wh_valuation_table', 'wh_balances_table',
            'wh_movements_table', 'wh_transfers_table', 'cash_summary_table',
            'cash_movements_table', 'bank_movements_table', 'pos_shifts_table',
            'trial_balance_table', 'customer_statement_table', 'supplier_statement_table',
            'customer_balances_table', 'supplier_balances_table', 'customer_aging_table',
            'supplier_aging_table', 'ledger_reconciliation_table', 'ledger_dual_read_table',
            'ledger_readiness_table', 'offline_queue_table', 'unit_audit_table',
            'item_movement_table', 'invoice_profit_table', 'net_profit_table',
            'manufacturing_orders_table', 'product_cost_table', 'general_ledger_table',
            'full_trial_balance_table', 'slow_items_table', 'top_items_table',
            'low_items_table', 'reorder_items_table', 'report_audit_table'
        ):
            table = getattr(self, name, None)
            if table is not None:
                table.set_table_identity(f'reports_{name}')

    def _set_summary(self, text=''):
        if hasattr(self, 'report_summary'):
            self.report_summary.setText(text or '')
            self.report_summary.setVisible(bool(text))

    def reset_report_filters(self):
        self.period_type.setCurrentIndex(0)
        from datetime import datetime
        self.year_combo.setCurrentText(str(datetime.now().year))
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        for combo_name in ('warehouse_filter', 'cashbox_filter', 'bank_filter', 'customer_filter', 'supplier_filter', 'item_filter'):
            combo = getattr(self, combo_name, None)
            if combo is not None and combo.count():
                combo.setCurrentIndex(0)
        self.refresh_report()

    def _report_source_label(self, source):
        return {
            'opening_balance': tr('opening_balance'),
            'sale_invoice': tr('sales_invoice'),
            'purchase_invoice': tr('purchase_invoice'),
            'sales_return': tr('sales_returns'),
            'purchase_return': tr('purchase_returns'),
            'receipt_voucher': tr('receipt_voucher'),
            'payment_voucher': tr('payment_voucher'),
        }.get(source or '', source or '')

    def _statement_summary(self, rows):
        debit = sum((Decimal(str(r.get('debit_raw') or 0)) for r in rows), Decimal('0'))
        credit = sum((Decimal(str(r.get('credit_raw') or 0)) for r in rows), Decimal('0'))
        last_balance = Decimal(str(rows[-1].get('balance_raw') or 0)) if rows else Decimal('0')
        return f"{tr('rows_count')}: {len(rows)} | {tr('debit')}: {currency.format_amount(debit)} | {tr('credit')}: {currency.format_amount(credit)} | {tr('balance')}: {currency.format_amount(last_balance)}"

    def _set_table(self, table, rows, headers, keys):
        model = GenericTableModel(rows, headers, data_keys=keys)
        table.setModel(model)
        try:
            table.setProperty('print_title', self.tabs.tabText(self.tabs.currentIndex()))
        except Exception:
            pass
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.horizontalHeader().setStretchLastSection(True)
        try:
            table.restore_layout()
        except Exception:
            pass
        return model

    def _apply_pos_shift_report_visibility(self):
        try:
            if not settings_service.pos_shifts_enabled():
                idx = self.tabs.indexOf(self.pos_shifts_tab)
                if idx >= 0:
                    self.tabs.removeTab(idx)
        except Exception:
            pass

    def refresh_report(self):
        """Refresh the active report tab only.

        Phase 37 stabilization: older code refreshed every report during page
        construction. That made ReportsWidget vulnerable to optional/remote
        report failures and slow server responses. The page now opens with the
        active tab only, while tab changes trigger this same method lazily.
        """
        start, end = self.get_date_range()
        self._set_summary('')
        display_curr = currency.get_display_currency()
        tab = self.tabs.currentWidget() if hasattr(self, 'tabs') else None
        try:
            if tab is self.income_tab:
                self._refresh_income(start, end, display_curr)
            elif tab is self.balance_tab:
                self._refresh_balance(start, end, display_curr)
            elif tab in (self.wh_valuation_tab, self.wh_balances_tab, self.wh_movements_tab, self.wh_transfers_tab):
                self._refresh_warehouse_reports(display_curr)
            elif tab in (self.cash_summary_tab, self.cash_movements_tab, self.bank_movements_tab, self.pos_shifts_tab):
                self._refresh_cash_bank_reports(display_curr)
            elif tab in (self.trial_balance_tab, self.customer_statement_tab, self.supplier_statement_tab,
                         self.customer_balances_tab, self.supplier_balances_tab, self.customer_aging_tab,
                         self.supplier_aging_tab, self.ledger_reconciliation_tab, self.ledger_dual_read_tab,
                         self.ledger_readiness_tab, self.offline_queue_tab, self.unit_audit_tab,
                         self.item_movement_tab, self.invoice_profit_tab, self.net_profit_tab,
                         self.manufacturing_orders_tab, self.product_cost_tab, self.general_ledger_tab,
                         self.full_trial_balance_tab, self.slow_items_tab, self.top_items_tab,
                         self.low_items_tab, self.reorder_items_tab, self.report_audit_tab):
                self._refresh_phase36_reports(start, end, display_curr)
            else:
                self._refresh_income(start, end, display_curr)
        except Exception as exc:
            # Do not block opening the reports page because one optional report failed.
            print('⚠️ ' + tr('reports_refresh_failed', error=str(exc)))

    def refresh_all_reports(self):
        """Developer/test helper to refresh every report group defensively."""
        start, end = self.get_date_range()
        display_curr = currency.get_display_currency()
        for fn in (
            lambda: self._refresh_income(start, end, display_curr),
            lambda: self._refresh_balance(start, end, display_curr),
            lambda: self._refresh_warehouse_reports(display_curr),
            lambda: self._refresh_cash_bank_reports(display_curr),
            lambda: self._refresh_phase36_reports(start, end, display_curr),
        ):
            try:
                fn()
            except Exception as exc:
                print('⚠️ ' + tr('reports_refresh_failed', error=str(exc)))

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
        self._set_table(self.income_table, income_list, [tr('statement'), tr('amount')], ['statement', 'amount'])

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

    def _refresh_cash_bank_reports(self, display_curr):
        cashbox_id = self.cashbox_filter.currentData() if hasattr(self, 'cashbox_filter') else None
        bank_id = self.bank_filter.currentData() if hasattr(self, 'bank_filter') else None
        summary = reporting_service.cash_bank_summary()
        cash_total = currency.convert(Decimal(str(summary.get('cash_total') or 0)), 'USD', display_curr)
        bank_total = currency.convert(Decimal(str(summary.get('bank_total') or 0)), 'USD', display_curr)
        available = currency.convert(Decimal(str(summary.get('available_total') or 0)), 'USD', display_curr)
        self.cash_summary_status.setText(
            f"الصناديق: {currency.format_amount(cash_total)} | البنوك: {currency.format_amount(bank_total)} | الإجمالي المتاح: {currency.format_amount(available)}"
        )
        summary_rows = []
        for c in reporting_service.cashboxes_report():
            bal = currency.convert(Decimal(str(c.get('balance') or 0)), 'USD', display_curr)
            summary_rows.append({
                'type': 'صندوق',
                'branch': c.get('branch_name') or '',
                'name': c.get('name') or '',
                'code': c.get('code') or '',
                'balance': currency.format_amount(bal),
                'status': 'نشط' if int(c.get('is_active') or 0) else 'مؤرشف',
            })
        for b in reporting_service.bank_accounts_report():
            bal = currency.convert(Decimal(str(b.get('balance') or 0)), 'USD', display_curr)
            summary_rows.append({
                'type': 'بنك',
                'branch': b.get('branch_name') or '',
                'name': f"{b.get('bank_name') or ''} - {b.get('account_name') or ''}".strip(' -'),
                'code': b.get('account_number') or b.get('iban') or '',
                'balance': currency.format_amount(bal),
                'status': 'نشط' if int(b.get('is_active') or 0) else 'مؤرشف',
            })
        self._set_table(self.cash_summary_table, summary_rows, ['النوع', 'الفرع', 'الاسم', 'الرقم/الكود', 'الرصيد', 'الحالة'], ['type','branch','name','code','balance','status'])

        cash_rows = []
        cash_running = Decimal('0')
        for m in reporting_service.cash_bank_movements(cashbox_id=cashbox_id, limit=1000):
            if m.get('cashbox_id') is None:
                continue
            raw_amount = Decimal(str(m.get('amount') or 0))
            cash_running += raw_amount
            amount = currency.convert(raw_amount, 'USD', display_curr)
            running_display = currency.convert(cash_running, 'USD', display_curr)
            cash_rows.append({
                'date': m.get('movement_date') or m.get('created_at') or '',
                'branch': m.get('branch_name') or '',
                'cashbox': m.get('cashbox_name') or '',
                'type': self._cash_movement_label(m.get('movement_type')),
                'direction': 'داخل' if Decimal(str(m.get('amount') or 0)) >= 0 else 'خارج',
                'amount': currency.format_amount(amount),
                'balance': currency.format_amount(running_display),
                'ref': m.get('reference_type') or '—',
                'desc': m.get('description') or '',
            })
        self._set_table(self.cash_movements_table, cash_rows, [tr('date'), tr('branch'), tr('cashbox_label'), tr('type'), tr('direction'), tr('amount'), tr('running_balance'), tr('reference'), tr('description')], ['date','branch','cashbox','type','direction','amount','balance','ref','desc'])

        bank_rows = []
        bank_running = Decimal('0')
        for m in reporting_service.cash_bank_movements(bank_account_id=bank_id, limit=1000):
            if m.get('bank_account_id') is None:
                continue
            raw_amount = Decimal(str(m.get('amount') or 0))
            bank_running += raw_amount
            amount = currency.convert(raw_amount, 'USD', display_curr)
            running_display = currency.convert(bank_running, 'USD', display_curr)
            bank_rows.append({
                'date': m.get('movement_date') or m.get('created_at') or '',
                'branch': m.get('branch_name') or '',
                'bank': f"{m.get('bank_name') or ''} - {m.get('account_name') or ''}".strip(' -'),
                'type': self._cash_movement_label(m.get('movement_type')),
                'direction': 'داخل' if Decimal(str(m.get('amount') or 0)) >= 0 else 'خارج',
                'amount': currency.format_amount(amount),
                'balance': currency.format_amount(running_display),
                'ref': m.get('reference_type') or '—',
                'desc': m.get('description') or '',
            })
        self._set_table(self.bank_movements_table, bank_rows, [tr('date'), tr('branch'), tr('bank_account'), tr('type'), tr('direction'), tr('amount'), tr('running_balance'), tr('reference'), tr('description')], ['date','branch','bank','type','direction','amount','balance','ref','desc'])

        shift_rows = []
        for s in reporting_service.pos_shifts_report(limit=1000):
            shift_rows.append({
                'id': s.get('id'),
                'branch': s.get('branch_name') or '',
                'cashbox': s.get('cashbox_name') or '',
                'opened': s.get('opened_at') or '',
                'closed': s.get('closed_at') or '—',
                'opening': currency.format_amount(s.get('opening_amount') or 0),
                'cash': currency.format_amount(s.get('total_cash') or 0),
                'card': currency.format_amount(s.get('total_card') or 0),
                'expected': currency.format_amount(s.get('expected_amount') or 0),
                'actual': currency.format_amount(s.get('actual_amount') or 0),
                'diff': currency.format_amount(s.get('difference_amount') or 0),
                'status': 'مفتوحة' if s.get('status') == 'open' else 'مغلقة',
            })
        self._set_table(self.pos_shifts_table, shift_rows, ['#', 'الفرع', 'الصندوق', 'الفتح', 'الإغلاق', 'افتتاحي', 'نقد', 'بطاقة', 'متوقع', 'فعلي', 'الفرق', 'الحالة'], ['id','branch','cashbox','opened','closed','opening','cash','card','expected','actual','diff','status'])

    def _cash_movement_label(self, mtype):
        return {
            'receipt': 'قبض',
            'payment': 'دفع',
            'expense': 'مصروف',
            'pos_sale_cash': 'بيع POS نقدي',
            'pos_sale_card': 'بيع POS بطاقة',
            'cash_transfer': 'تحويل نقدي',
            'bank_deposit': 'إيداع بنكي',
            'bank_withdrawal': 'سحب بنكي',
        }.get(mtype or '', mtype or '')

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


    def _rows_from(self, data, *keys):
        """Normalize service/reporting responses to a list of dictionaries."""
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in keys:
                value = data.get(key)
                if isinstance(value, list):
                    return value
            for key in ('rows', 'data', 'items', 'ledger', 'entries', 'results', 'mismatches', 'differences', 'blockers', 'warnings'):
                value = data.get(key)
                if isinstance(value, list):
                    return value
        return []

    def _refresh_phase36_reports(self, start, end, display_curr):
        """Refresh Phase 36 extended reports.

        This method is intentionally defensive: one optional diagnostic report
        should not prevent the Reports page from opening.  Critical business
        reports are still populated when their service/API is available, while
        unavailable diagnostics show an empty table instead of raising.
        """
        customer_id = self.customer_filter.currentData() if hasattr(self, 'customer_filter') else None
        supplier_id = self.supplier_filter.currentData() if hasattr(self, 'supplier_filter') else None
        wh_id = self.warehouse_filter.currentData() if hasattr(self, 'warehouse_filter') else None
        item_id = self.item_filter.currentData() if hasattr(self, 'item_filter') else None

        if self.tabs.currentWidget() in (self.general_ledger_tab, self.full_trial_balance_tab, self.slow_items_tab, self.top_items_tab, self.low_items_tab, self.reorder_items_tab, self.report_audit_tab):
            self._refresh_phase141_reports(start, end, display_curr)
            return

        # Trial balance
        try:
            rows = []
            for r in reporting_service.trial_balance():
                debit = Decimal(str(r.get('debit') or r.get('debit_total') or 0))
                credit = Decimal(str(r.get('credit') or r.get('credit_total') or 0))
                rows.append({
                    'account': r.get('account_name') or r.get('name') or r.get('account') or '',
                    'code': r.get('code') or r.get('account_code') or '',
                    'debit': currency.format_amount(currency.convert(debit, 'USD', display_curr)),
                    'credit': currency.format_amount(currency.convert(credit, 'USD', display_curr)),
                    'balance': currency.format_amount(currency.convert(debit - credit, 'USD', display_curr)),
                })
            self._set_table(self.trial_balance_table, rows, ['الحساب', 'الكود', 'مدين', 'دائن', 'الرصيد'], ['account', 'code', 'debit', 'credit', 'balance'])
        except Exception:
            self._set_table(self.trial_balance_table, [], ['الحساب', 'الكود', 'مدين', 'دائن', 'الرصيد'], ['account', 'code', 'debit', 'credit', 'balance'])

        # Customer statement
        try:
            rows = []
            if customer_id:
                for r in reporting_service.customer_statement(customer_id, start, end):
                    debit = Decimal(str(r.get('debit') or 0))
                    credit = Decimal(str(r.get('credit') or 0))
                    balance = Decimal(str(r.get('balance') if r.get('balance') is not None else debit - credit))
                    debit_display = currency.convert(debit, 'USD', display_curr)
                    credit_display = currency.convert(credit, 'USD', display_curr)
                    balance_display = currency.convert(balance, 'USD', display_curr)
                    rows.append({
                        'date': r.get('date') or r.get('created_at') or r.get('invoice_date') or '',
                        'type': self._report_source_label(r.get('source_type') or r.get('type') or r.get('source') or r.get('movement_type')),
                        'ref': r.get('reference') or r.get('reference_no') or r.get('invoice_no') or r.get('voucher_no') or '',
                        'desc': self._report_source_label(r.get('description') or r.get('source_type')),
                        'debit': currency.format_amount(debit_display),
                        'credit': currency.format_amount(credit_display),
                        'balance': currency.format_amount(balance_display),
                        'debit_raw': debit_display,
                        'credit_raw': credit_display,
                        'balance_raw': balance_display,
                    })
            self._set_table(self.customer_statement_table, rows, [tr('date'), tr('type'), tr('reference'), tr('description'), tr('debit'), tr('credit'), tr('balance')], ['date','type','ref','desc','debit','credit','balance'])
            if self.tabs.currentWidget() is self.customer_statement_tab:
                self._set_summary(self._statement_summary(rows) if rows else tr('choose_customer'))
        except Exception as exc:
            self._set_table(self.customer_statement_table, [], [tr('date'), tr('type'), tr('reference'), tr('description'), tr('debit'), tr('credit'), tr('balance')], ['date','type','ref','desc','debit','credit','balance'])
            if self.tabs.currentWidget() is self.customer_statement_tab:
                self._set_summary(tr('reports_refresh_failed', error=str(exc)))

        # Supplier statement
        try:
            rows = []
            if supplier_id:
                for r in reporting_service.supplier_statement(supplier_id, start, end):
                    debit = Decimal(str(r.get('debit') or 0))
                    credit = Decimal(str(r.get('credit') or 0))
                    balance = Decimal(str(r.get('balance') if r.get('balance') is not None else credit - debit))
                    debit_display = currency.convert(debit, 'USD', display_curr)
                    credit_display = currency.convert(credit, 'USD', display_curr)
                    balance_display = currency.convert(balance, 'USD', display_curr)
                    rows.append({
                        'date': r.get('date') or r.get('created_at') or r.get('invoice_date') or '',
                        'type': self._report_source_label(r.get('source_type') or r.get('type') or r.get('source') or r.get('movement_type')),
                        'ref': r.get('reference') or r.get('reference_no') or r.get('invoice_no') or r.get('voucher_no') or '',
                        'desc': self._report_source_label(r.get('description') or r.get('source_type')),
                        'debit': currency.format_amount(debit_display),
                        'credit': currency.format_amount(credit_display),
                        'balance': currency.format_amount(balance_display),
                        'debit_raw': debit_display,
                        'credit_raw': credit_display,
                        'balance_raw': balance_display,
                    })
            self._set_table(self.supplier_statement_table, rows, [tr('date'), tr('type'), tr('reference'), tr('description'), tr('debit'), tr('credit'), tr('balance')], ['date','type','ref','desc','debit','credit','balance'])
            if self.tabs.currentWidget() is self.supplier_statement_tab:
                self._set_summary(self._statement_summary(rows) if rows else tr('choose_supplier'))
        except Exception as exc:
            self._set_table(self.supplier_statement_table, [], [tr('date'), tr('type'), tr('reference'), tr('description'), tr('debit'), tr('credit'), tr('balance')], ['date','type','ref','desc','debit','credit','balance'])
            if self.tabs.currentWidget() is self.supplier_statement_tab:
                self._set_summary(tr('reports_refresh_failed', error=str(exc)))

        # Customer/Supplier balances
        try:
            rows = []
            for r in reporting_service.customer_balances():
                bal = Decimal(str(r.get('balance') or r.get('current_balance') or 0))
                rows.append({'name': r.get('name') or r.get('customer_name') or '', 'phone': r.get('phone') or '', 'balance': currency.format_amount(currency.convert(bal, 'USD', display_curr))})
            self._set_table(self.customer_balances_table, rows, ['العميل', 'الهاتف', 'الرصيد'], ['name','phone','balance'])
        except Exception:
            self._set_table(self.customer_balances_table, [], ['العميل', 'الهاتف', 'الرصيد'], ['name','phone','balance'])
        try:
            rows = []
            for r in reporting_service.supplier_balances():
                bal = Decimal(str(r.get('balance') or r.get('current_balance') or 0))
                rows.append({'name': r.get('name') or r.get('supplier_name') or '', 'phone': r.get('phone') or '', 'balance': currency.format_amount(currency.convert(bal, 'USD', display_curr))})
            self._set_table(self.supplier_balances_table, rows, ['المورد', 'الهاتف', 'الرصيد'], ['name','phone','balance'])
        except Exception:
            self._set_table(self.supplier_balances_table, [], ['المورد', 'الهاتف', 'الرصيد'], ['name','phone','balance'])

        # Aging
        try:
            rows = []
            for r in reporting_service.customer_aging(end):
                rows.append({
                    'name': r.get('name') or r.get('customer_name') or '',
                    'current': currency.format_amount(currency.convert(Decimal(str(r.get('current') or r.get('not_due') or 0)), 'USD', display_curr)),
                    'd30': currency.format_amount(currency.convert(Decimal(str(r.get('days_1_30') or r.get('d30') or 0)), 'USD', display_curr)),
                    'd60': currency.format_amount(currency.convert(Decimal(str(r.get('days_31_60') or r.get('d60') or 0)), 'USD', display_curr)),
                    'd90': currency.format_amount(currency.convert(Decimal(str(r.get('days_61_90') or r.get('d90') or 0)), 'USD', display_curr)),
                    'over': currency.format_amount(currency.convert(Decimal(str(r.get('over_90') or r.get('older') or 0)), 'USD', display_curr)),
                    'total': currency.format_amount(currency.convert(Decimal(str(r.get('total') or r.get('balance') or 0)), 'USD', display_curr)),
                })
            self._set_table(self.customer_aging_table, rows, ['العميل', 'حالي', '1-30', '31-60', '61-90', '+90', 'الإجمالي'], ['name','current','d30','d60','d90','over','total'])
        except Exception:
            self._set_table(self.customer_aging_table, [], ['العميل', 'حالي', '1-30', '31-60', '61-90', '+90', 'الإجمالي'], ['name','current','d30','d60','d90','over','total'])
        try:
            rows = []
            for r in reporting_service.supplier_aging(end):
                rows.append({
                    'name': r.get('name') or r.get('supplier_name') or '',
                    'current': currency.format_amount(currency.convert(Decimal(str(r.get('current') or r.get('not_due') or 0)), 'USD', display_curr)),
                    'd30': currency.format_amount(currency.convert(Decimal(str(r.get('days_1_30') or r.get('d30') or 0)), 'USD', display_curr)),
                    'd60': currency.format_amount(currency.convert(Decimal(str(r.get('days_31_60') or r.get('d60') or 0)), 'USD', display_curr)),
                    'd90': currency.format_amount(currency.convert(Decimal(str(r.get('days_61_90') or r.get('d90') or 0)), 'USD', display_curr)),
                    'over': currency.format_amount(currency.convert(Decimal(str(r.get('over_90') or r.get('older') or 0)), 'USD', display_curr)),
                    'total': currency.format_amount(currency.convert(Decimal(str(r.get('total') or r.get('balance') or 0)), 'USD', display_curr)),
                })
            self._set_table(self.supplier_aging_table, rows, ['المورد', 'حالي', '1-30', '31-60', '61-90', '+90', 'الإجمالي'], ['name','current','d30','d60','d90','over','total'])
        except Exception:
            self._set_table(self.supplier_aging_table, [], ['المورد', 'حالي', '1-30', '31-60', '61-90', '+90', 'الإجمالي'], ['name','current','d30','d60','d90','over','total'])

        # Ledger diagnostics
        try:
            from core.services.inventory_service import inventory_service
            rec = inventory_service.ledger_reconciliation(warehouse_id=wh_id, tolerance='0')
            rec_rows = self._rows_from(rec, 'mismatches', 'rows')
            if not rec_rows and isinstance(rec, dict):
                rec_rows = rec.get('item_differences') or rec.get('warehouse_differences') or []
            rows = []
            for r in rec_rows:
                diff = Decimal(str(r.get('difference') or r.get('delta') or 0))
                rows.append({
                    'scope': r.get('scope') or r.get('level') or '',
                    'item': r.get('item_name') or r.get('item_id') or '',
                    'warehouse': r.get('warehouse_name') or r.get('warehouse_id') or '',
                    'operational': r.get('operational_balance') or r.get('operational_qty') or r.get('quantity') or '0',
                    'ledger': r.get('ledger_balance') or r.get('ledger_qty') or '0',
                    'difference': str(diff),
                })
            self._set_table(self.ledger_reconciliation_table, rows, ['النطاق', 'المادة', 'المستودع', 'التشغيلي', 'Ledger', 'الفرق'], ['scope','item','warehouse','operational','ledger','difference'])

            dual = inventory_service.ledger_dual_read(warehouse_id=wh_id, tolerance='0', include_matches=False)
            dual_rows = self._rows_from(dual, 'rows', 'differences', 'mismatches')
            rows = []
            for r in dual_rows:
                rows.append({
                    'item': r.get('item_name') or r.get('item_id') or '',
                    'warehouse': r.get('warehouse_name') or r.get('warehouse_id') or '',
                    'operational': r.get('operational_balance') or r.get('operational_qty') or '0',
                    'ledger': r.get('ledger_balance') or r.get('ledger_qty') or '0',
                    'difference': r.get('difference') or r.get('delta') or '0',
                    'status': r.get('status') or ('مطابق' if str(r.get('difference') or '0') == '0' else 'فرق'),
                })
            self._set_table(self.ledger_dual_read_table, rows, ['المادة', 'المستودع', 'التشغيلي', 'Ledger', 'الفرق', 'الحالة'], ['item','warehouse','operational','ledger','difference','status'])

            ready = inventory_service.ledger_readiness(warehouse_id=wh_id, tolerance='0')
            rows = []
            for key in ('blockers', 'warnings'):
                for value in ready.get(key, []) if isinstance(ready, dict) else []:
                    rows.append({'type': 'مانع' if key == 'blockers' else 'تحذير', 'message': str(value)})
            if isinstance(ready, dict):
                rows.insert(0, {'type': 'القرار', 'message': ready.get('recommendation') or ('جاهز للقراءة المزدوجة' if ready.get('safe_for_dual_read') else 'غير جاهز')})
            self._set_table(self.ledger_readiness_table, rows, ['النوع', 'الرسالة'], ['type','message'])
        except Exception:
            self._set_table(self.ledger_reconciliation_table, [], ['النطاق', 'المادة', 'المستودع', 'التشغيلي', 'Ledger', 'الفرق'], ['scope','item','warehouse','operational','ledger','difference'])
            self._set_table(self.ledger_dual_read_table, [], ['المادة', 'المستودع', 'التشغيلي', 'Ledger', 'الفرق', 'الحالة'], ['item','warehouse','operational','ledger','difference','status'])
            self._set_table(self.ledger_readiness_table, [], ['النوع', 'الرسالة'], ['type','message'])


        # Item movement report
        try:
            rows = []
            total_in = Decimal('0')
            total_out = Decimal('0')
            for r in reporting_service.item_movement_report(item_id=item_id, warehouse_id=wh_id, start_date=start, end_date=end):
                in_qty = Decimal(str(r.get('in_qty') or 0))
                out_qty = Decimal(str(r.get('out_qty') or 0))
                total_in += in_qty
                total_out += out_qty
                rows.append({
                    'date': r.get('movement_date') or '',
                    'reference': f"{r.get('reference_type') or ''} #{r.get('reference_id') or ''}".strip(),
                    'item': r.get('item_name') or r.get('item_id') or '',
                    'barcode': r.get('barcode') or '',
                    'warehouse': r.get('warehouse_name') or '',
                    'movement': self._movement_label(r.get('movement_type')),
                    'in_qty': f"{in_qty:.4f}".rstrip('0').rstrip('.'),
                    'out_qty': f"{out_qty:.4f}".rstrip('0').rstrip('.'),
                    'balance': f"{Decimal(str(r.get('balance_qty') or 0)):.4f}".rstrip('0').rstrip('.'),
                    'unit_cost': currency.format_amount(currency.convert(Decimal(str(r.get('unit_cost') or 0)), 'USD', display_curr)),
                    'total_cost': currency.format_amount(currency.convert(Decimal(str(r.get('total_cost') or 0)), 'USD', display_curr)),
                    'notes': r.get('notes') or '',
                })
            self._set_table(
                self.item_movement_table,
                rows,
                [tr('date'), tr('reference'), tr('print_item'), tr('barcode'), tr('warehouse_label'), tr('movement_type'), tr('in_qty'), tr('out_qty'), tr('balance'), tr('unit_cost'), tr('total_cost'), tr('notes')],
                ['date', 'reference', 'item', 'barcode', 'warehouse', 'movement', 'in_qty', 'out_qty', 'balance', 'unit_cost', 'total_cost', 'notes']
            )
            if self.tabs.currentWidget() is self.item_movement_tab:
                self._set_summary(f"{tr('rows_count')}: {len(rows)} | {tr('in_qty')}: {total_in} | {tr('out_qty')}: {total_out}")
        except Exception:
            self._set_table(self.item_movement_table, [], [tr('date'), tr('reference'), tr('print_item'), tr('barcode'), tr('warehouse_label'), tr('movement_type'), tr('in_qty'), tr('out_qty'), tr('balance'), tr('unit_cost'), tr('total_cost'), tr('notes')], ['date','reference','item','barcode','warehouse','movement','in_qty','out_qty','balance','unit_cost','total_cost','notes'])

        # Invoice profitability report
        try:
            rows = []
            total_sales = Decimal('0')
            total_cost = Decimal('0')
            total_profit = Decimal('0')
            for r in reporting_service.invoice_profit_report(start_date=start, end_date=end, customer_id=customer_id):
                invoice_total = Decimal(str(r.get('invoice_total') or 0))
                cost_total = Decimal(str(r.get('cost_total') or 0))
                profit = Decimal(str(r.get('profit') or 0))
                total_sales += invoice_total
                total_cost += cost_total
                total_profit += profit
                rows.append({
                    'date': r.get('date') or '',
                    'reference': r.get('reference') or r.get('id') or '',
                    'customer': r.get('customer_name') or '',
                    'sales': currency.format_amount(currency.convert(invoice_total, 'USD', display_curr)),
                    'cost': currency.format_amount(currency.convert(cost_total, 'USD', display_curr)),
                    'profit': currency.format_amount(currency.convert(profit, 'USD', display_curr)),
                    'margin': f"{Decimal(str(r.get('profit_margin') or 0)):.2f}%",
                })
            self._set_table(
                self.invoice_profit_table,
                rows,
                [tr('date'), tr('reference'), tr('customer_label'), tr('sales_value'), tr('cost'), tr('profit'), tr('profit_margin')],
                ['date', 'reference', 'customer', 'sales', 'cost', 'profit', 'margin']
            )
            if self.tabs.currentWidget() is self.invoice_profit_tab:
                self._set_summary(f"{tr('rows_count')}: {len(rows)} | {tr('sales_value')}: {currency.format_amount(currency.convert(total_sales, 'USD', display_curr))} | {tr('cost')}: {currency.format_amount(currency.convert(total_cost, 'USD', display_curr))} | {tr('profit')}: {currency.format_amount(currency.convert(total_profit, 'USD', display_curr))}")
        except Exception:
            self._set_table(self.invoice_profit_table, [], [tr('date'), tr('reference'), tr('customer_label'), tr('sales_value'), tr('cost'), tr('profit'), tr('profit_margin')], ['date','reference','customer','sales','cost','profit','margin'])

        # Offline queue diagnostics
        try:
            from core.services.offline_queue_service import offline_queue_service
            rows = []
            for r in offline_queue_service.recent(limit=300):
                rows.append({
                    'id': r.get('id'),
                    'method': r.get('method') or '',
                    'endpoint': r.get('endpoint') or '',
                    'status': r.get('status') or '',
                    'attempts': r.get('attempts') or 0,
                    'error': r.get('last_error') or r.get('error') or '',
                    'created': r.get('created_at') or '',
                })
            self._set_table(self.offline_queue_table, rows, ['#', 'الطريقة', 'المسار', 'الحالة', 'المحاولات', 'الخطأ', 'التاريخ'], ['id','method','endpoint','status','attempts','error','created'])
        except Exception:
            self._set_table(self.offline_queue_table, [], ['#', 'الطريقة', 'المسار', 'الحالة', 'المحاولات', 'الخطأ', 'التاريخ'], ['id','method','endpoint','status','attempts','error','created'])

        # Unit conversion audit
        try:
            from core.services.product_service import product_service
            rows = []
            for item in product_service.items(limit=1000):
                units = product_service.item_units(item.get('id')) if item.get('id') else []
                base_unit = item.get('unit') or item.get('base_unit') or ''
                if not units:
                    rows.append({'item': item.get('name') or '', 'base': base_unit, 'unit': '—', 'factor': '1', 'status': 'لا توجد وحدات فرعية'})
                    continue
                seen = set()
                for u in units:
                    name = u.get('unit_name') or u.get('name') or ''
                    factor = Decimal(str(u.get('conversion_factor') or 0))
                    status = 'سليم'
                    if not name:
                        status = 'اسم وحدة فارغ'
                    elif name in seen:
                        status = 'وحدة مكررة'
                    elif factor <= 0:
                        status = 'معامل غير صالح'
                    seen.add(name)
                    rows.append({'item': item.get('name') or '', 'base': base_unit, 'unit': name, 'factor': str(factor), 'status': status})
            self._set_table(self.unit_audit_table, rows, [tr('print_item'), tr('base_unit'), tr('print_unit'), tr('conversion_factor'), tr('status')], ['item','base','unit','factor','status'])
        except Exception:
            self._set_table(self.unit_audit_table, [], [tr('print_item'), tr('base_unit'), tr('print_unit'), tr('conversion_factor'), tr('status')], ['item','base','unit','factor','status'])


    def _refresh_phase141_reports(self, start, end, display_curr):
        tab = self.tabs.currentWidget()
        wh_id = self.warehouse_filter.currentData() if hasattr(self, 'warehouse_filter') else None
        # General ledger
        if tab is self.general_ledger_tab:
            rows=[]
            for r in reporting_service.general_ledger_report(start_date=start, end_date=end):
                rows.append({
                    'date': r.get('entry_date') or '',
                    'account': f"{r.get('account_code') or ''} {r.get('account_name') or ''}".strip(),
                    'reference': r.get('reference') or r.get('entry_id') or '',
                    'description': r.get('description') or '',
                    'debit': currency.format_amount(currency.convert(Decimal(str(r.get('debit') or 0)), 'USD', display_curr)),
                    'credit': currency.format_amount(currency.convert(Decimal(str(r.get('credit') or 0)), 'USD', display_curr)),
                    'balance': currency.format_amount(currency.convert(Decimal(str(r.get('balance') or 0)), 'USD', display_curr)),
                })
            self._set_table(self.general_ledger_table, rows, [tr('date'), tr('account'), tr('reference'), tr('description'), tr('debit'), tr('credit'), tr('balance')], ['date','account','reference','description','debit','credit','balance'])
            self._set_summary(f"{tr('rows_count')}: {len(rows)}")
            return
        # Full trial balance
        if tab is self.full_trial_balance_tab:
            tb = reporting_service.full_trial_balance_report(start, end)
            rows=[]
            for r in tb.get('rows') or []:
                rows.append({
                    'code': r.get('code') or r.get('account_code') or '',
                    'account': r.get('account_name') or r.get('name') or r.get('account') or '',
                    'debit': currency.format_amount(currency.convert(Decimal(str(r.get('debit') or 0)), 'USD', display_curr)),
                    'credit': currency.format_amount(currency.convert(Decimal(str(r.get('credit') or 0)), 'USD', display_curr)),
                    'balance': currency.format_amount(currency.convert(Decimal(str(r.get('balance') or 0)), 'USD', display_curr)),
                })
            self._set_table(self.full_trial_balance_table, rows, [tr('code'), tr('account'), tr('debit'), tr('credit'), tr('balance')], ['code','account','debit','credit','balance'])
            self._set_summary(f"{tr('debit')}: {currency.format_amount(currency.convert(Decimal(str(tb.get('total_debit') or 0)), 'USD', display_curr))} | {tr('credit')}: {currency.format_amount(currency.convert(Decimal(str(tb.get('total_credit') or 0)), 'USD', display_curr))} | {tr('difference')}: {currency.format_amount(currency.convert(Decimal(str(tb.get('difference') or 0)), 'USD', display_curr))}")
            return
        # Smart item reports
        smart_map = {
            self.slow_items_tab: ('slow', self.slow_items_table),
            self.top_items_tab: ('top', self.top_items_table),
            self.low_items_tab: ('low', self.low_items_table),
            self.reorder_items_tab: ('reorder', self.reorder_items_table),
        }
        if tab in smart_map:
            kind, table = smart_map[tab]
            rows=[]
            for r in reporting_service.smart_items_report(kind, start_date=start, end_date=end, warehouse_id=wh_id):
                rows.append({
                    'item': r.get('name') or r.get('item_name') or '',
                    'barcode': r.get('barcode') or '',
                    'warehouse': r.get('warehouse_name') or '',
                    'qty': str(r.get('qty') if r.get('qty') is not None else r.get('quantity') or 0),
                    'min_stock': str(r.get('min_stock') or ''),
                    'shortage': str(r.get('shortage') or ''),
                    'last_sale': r.get('last_sale_date') or '',
                    'days': str(r.get('days_without_movement') if r.get('days_without_movement') is not None else ''),
                    'sales': currency.format_amount(currency.convert(Decimal(str(r.get('sales_value') or 0)), 'USD', display_curr)),
                    'profit': currency.format_amount(currency.convert(Decimal(str(r.get('profit') or 0)), 'USD', display_curr)),
                })
            if kind == 'reorder':
                headers=[tr('print_item'), tr('barcode'), tr('warehouse_label'), tr('quantity'), tr('min_stock'), tr('shortage')]
                keys=['item','barcode','warehouse','qty','min_stock','shortage']
            elif kind == 'slow':
                headers=[tr('print_item'), tr('barcode'), tr('last_sale'), tr('days_without_movement'), tr('quantity')]
                keys=['item','barcode','last_sale','days','qty']
            else:
                headers=[tr('print_item'), tr('barcode'), tr('quantity'), tr('sales_value'), tr('profit')]
                keys=['item','barcode','qty','sales','profit']
            self._set_table(table, rows, headers, keys)
            self._set_summary(f"{tr('rows_count')}: {len(rows)}")
            return
        # Consistency audit
        if tab is self.report_audit_tab:
            rows=[]
            for r in reporting_service.report_consistency_audit(start, end):
                rows.append({'scope': r.get('scope') or '', 'status': r.get('status') or '', 'severity': r.get('severity') or '', 'message': r.get('message') or ''})
            self._set_table(self.report_audit_table, rows, [tr('scope'), tr('status'), tr('severity'), tr('message')], ['scope','status','severity','message'])
            self._set_summary(f"{tr('rows_count')}: {len(rows)}")
            return

    def print_report(self, mode='preview'):
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
        elif tab is self.cash_summary_tab:
            table = self.cash_summary_table
        elif tab is self.cash_movements_tab:
            table = self.cash_movements_table
        elif tab is self.bank_movements_tab:
            table = self.bank_movements_table
        elif tab is self.pos_shifts_tab:
            table = self.pos_shifts_table
        elif tab is self.trial_balance_tab:
            table = self.trial_balance_table
        elif tab is self.customer_statement_tab:
            table = self.customer_statement_table
        elif tab is self.supplier_statement_tab:
            table = self.supplier_statement_table
        elif tab is self.customer_balances_tab:
            table = self.customer_balances_table
        elif tab is self.supplier_balances_tab:
            table = self.supplier_balances_table
        elif tab is self.customer_aging_tab:
            table = self.customer_aging_table
        elif tab is self.supplier_aging_tab:
            table = self.supplier_aging_table
        elif tab is self.ledger_reconciliation_tab:
            table = self.ledger_reconciliation_table
        elif tab is self.ledger_dual_read_tab:
            table = self.ledger_dual_read_table
        elif tab is self.ledger_readiness_tab:
            table = self.ledger_readiness_table
        elif tab is self.offline_queue_tab:
            table = self.offline_queue_table
        elif tab is self.unit_audit_tab:
            table = self.unit_audit_table
        elif tab is self.item_movement_tab:
            table = self.item_movement_table
        elif tab is self.invoice_profit_tab:
            table = self.invoice_profit_table
        elif tab is self.net_profit_tab:
            table = self.net_profit_table
        elif tab is self.manufacturing_orders_tab:
            table = self.manufacturing_orders_table
        elif tab is self.product_cost_tab:
            table = self.product_cost_table
        elif tab is self.general_ledger_tab:
            table = self.general_ledger_table
        elif tab is self.full_trial_balance_tab:
            table = self.full_trial_balance_table
        elif tab is self.slow_items_tab:
            table = self.slow_items_table
        elif tab is self.top_items_tab:
            table = self.top_items_table
        elif tab is self.low_items_tab:
            table = self.low_items_table
        elif tab is self.reorder_items_tab:
            table = self.reorder_items_table
        elif tab is self.report_audit_tab:
            table = self.report_audit_table
        if not table or not table.model():
            return
        model = table.model()
        headers = [model.headerData(i, Qt.Horizontal, Qt.DisplayRole) for i in range(model.columnCount())]
        rows = []
        for r in range(model.rowCount()):
            rows.append([model.data(model.index(r, c), Qt.DisplayRole) or '' for c in range(model.columnCount())])
        subtitle = tr('period_subtitle', start=start, end=end)
        if mode == 'browser':
            printing_service.report_browser(title, rows, headers, self, subtitle=subtitle)
        elif mode == 'direct':
            printing_service.report_print(title, rows, headers, self, subtitle=subtitle)
        elif mode == 'pdf':
            printing_service.report_pdf(title, rows, headers, self, subtitle=subtitle)
        else:
            printing_service.report_preview(title, rows, headers, self, subtitle=subtitle)
