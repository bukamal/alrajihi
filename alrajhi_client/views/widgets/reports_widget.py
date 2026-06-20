# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
                             QDateEdit, QLabel, QTabWidget, QHeaderView, QMenu)
from PyQt5.QtCore import Qt, QDate
from i18n import translate as tr, qt_layout_direction
from decimal import Decimal
from core.services.reporting_service import reporting_service
from core.services.report_operation_policy import report_operation_policy
from core.services.settings_service import settings_service
from core.services.warehouse_service import warehouse_service
from core.services.entity_service import entity_service
from currency import currency
from ui.smart_table_view import SmartTableView
from models.table_models import GenericTableModel
from views.widgets.modern_ui import apply_modern_widget
from views.widgets.reports_phase36_mixin import ReportsPhase36Mixin
from workspace.documents.document_contract import descriptor_for
from workspace.documents.document_permission_binder import DocumentPermissionBinder
from features.reports.report_shell_contract import (
    REPORTS_DOCUMENT_DESCRIPTOR,
    all_report_descriptors,
    bind_report_widgets,
    report_descriptor_for_tab_attr,
)


class ReportsWidget(ReportsPhase36Mixin, QWidget):
    DOCUMENT_DESCRIPTOR = REPORTS_DOCUMENT_DESCRIPTOR
    REPORT_SHELL_DESCRIPTORS = all_report_descriptors()
    """Financial and warehouse reports.

    Warehouse-5 adds valuation, balances, movements and transfers while keeping
    financial reports unchanged. All report data is read through services.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.document_descriptor = self.DOCUMENT_DESCRIPTOR
        self.permission_binder = DocumentPermissionBinder(self.document_descriptor)
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

        self.refresh_btn = QPushButton(tr("refresh_report"))
        self.refresh_btn.clicked.connect(self.refresh_report)
        period_layout.addWidget(self.refresh_btn)

        reset_btn = QPushButton(tr("reset_filters"))
        reset_btn.clicked.connect(self.reset_report_filters)
        period_layout.addWidget(reset_btn)

        self.print_btn = QPushButton(tr("printing"))
        self.print_btn.setObjectName('reportPrintButton')
        self.print_btn.setToolTip(tr('settings_operation_reports_print'))
        self.print_btn.clicked.connect(lambda: self.print_report('print'))
        period_layout.addWidget(self.print_btn)

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
        self._build_grouped_report_tabs()
        self._apply_pos_shift_report_visibility()
        self.tabs.currentChanged.connect(lambda _idx: self.refresh_report())
        layout.addWidget(self.tabs)

        self.report_summary = QLabel()
        self.report_summary.setObjectName('reportSummaryBar')
        self.report_summary.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.report_summary)

        self._install_report_table_identities()
        bind_report_widgets(self)
        self.on_period_type_changed()
        apply_modern_widget(self, tr('reports_page_title'), tr('reports_page_subtitle'))
        self._apply_report_operation_state()
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

    def _build_grouped_report_tabs(self):
        """Group report tabs into high-level work areas without changing report widgets.

        The old ReportsWidget placed more than thirty tabs at the top level.  That
        made Arabic/English/German titles drift and made users think unrelated
        reports shared filters/calculation rules.  The top level is now a small
        set of report families; each family contains the existing concrete report
        tabs.  All refresh/print/export code resolves the active inner report via
        _active_report_tab(), so API, RBAC, branch scope, currency, and print
        contracts remain intact.
        """
        self._report_group_tabs = {}
        self._report_tab_to_group = {}
        groups = [
            ("reports_group_financial", [
                (self.income_tab, "report_income_statement"),
                (self.balance_tab, "report_balance_sheet"),
                (self.trial_balance_tab, "report_trial_balance"),
                (self.general_ledger_tab, "report_general_ledger"),
                (self.full_trial_balance_tab, "report_full_trial_balance"),
            ]),
            ("reports_group_parties", [
                (self.customer_statement_tab, "report_customer_statement"),
                (self.supplier_statement_tab, "report_supplier_statement"),
                (self.customer_balances_tab, "report_customer_balances"),
                (self.supplier_balances_tab, "report_supplier_balances"),
                (self.customer_aging_tab, "report_customer_aging"),
                (self.supplier_aging_tab, "report_supplier_aging"),
            ]),
            ("reports_group_inventory", [
                (self.wh_valuation_tab, "report_warehouse_valuation"),
                (self.wh_balances_tab, "report_warehouse_balances"),
                (self.wh_movements_tab, "report_warehouse_movements"),
                (self.wh_transfers_tab, "report_warehouse_transfers"),
                (self.item_movement_tab, "report_item_movement"),
                (self.slow_items_tab, "report_slow_items"),
                (self.top_items_tab, "report_top_items"),
                (self.low_items_tab, "report_low_items"),
                (self.reorder_items_tab, "report_reorder_items"),
                (self.ledger_reconciliation_tab, "report_ledger_reconciliation"),
                (self.ledger_dual_read_tab, "report_ledger_dual_read"),
                (self.ledger_readiness_tab, "report_ledger_readiness"),
                (self.unit_audit_tab, "report_unit_audit"),
            ]),
            ("reports_group_cash_pos", [
                (self.cash_summary_tab, "report_cash_bank_summary"),
                (self.cash_movements_tab, "report_cash_movements"),
                (self.bank_movements_tab, "report_bank_movements"),
                (self.pos_shifts_tab, "report_pos_shifts"),
            ]),
            ("reports_group_profit_manufacturing", [
                (self.invoice_profit_tab, "report_invoice_profit"),
                (self.net_profit_tab, "report_net_profit"),
                (self.manufacturing_orders_tab, "report_manufacturing_orders"),
                (self.product_cost_tab, "report_product_cost"),
            ]),
            ("reports_group_diagnostics", [
                (self.report_audit_tab, "report_consistency_audit"),
                (self.offline_queue_tab, "report_offline_queue"),
            ]),
        ]
        self.tabs.setUsesScrollButtons(True)
        self.tabs.setElideMode(Qt.ElideRight)
        for group_key, items in groups:
            group_tabs = QTabWidget()
            group_tabs.setObjectName(group_key)
            group_tabs.setUsesScrollButtons(True)
            group_tabs.setElideMode(Qt.ElideRight)
            group_tabs.currentChanged.connect(lambda _idx, _tabs=group_tabs: self.refresh_report())
            for tab, title_key in items:
                group_tabs.addTab(tab, tr(title_key))
                self._report_tab_to_group[tab] = group_tabs
            self._report_group_tabs[group_key] = group_tabs
            self.tabs.addTab(group_tabs, tr(group_key))

    def _active_report_group_tabs(self):
        current = self.tabs.currentWidget() if hasattr(self, 'tabs') else None
        return current if isinstance(current, QTabWidget) else None

    def _active_report_tab(self):
        group_tabs = self._active_report_group_tabs()
        if group_tabs is not None:
            return group_tabs.currentWidget()
        return self.tabs.currentWidget() if hasattr(self, 'tabs') else None

    def _active_report_title(self):
        group_tabs = self._active_report_group_tabs()
        if group_tabs is not None:
            return group_tabs.tabText(group_tabs.currentIndex())
        return self.tabs.tabText(self.tabs.currentIndex()) if hasattr(self, 'tabs') else tr('print_report_default')

    def _report_table_for_tab(self, tab):
        for descriptor in self.REPORT_SHELL_DESCRIPTORS:
            if getattr(self, descriptor.tab_attr, None) is tab:
                return getattr(self, descriptor.table_attr, None)
        return None

    def _to_decimal(self, value):
        from core.money_display_policy import decimal_value
        return decimal_value(value)

    def _money(self, value, display_curr=None, *, from_currency=None):
        display_curr = display_curr or currency.get_display_currency()
        amount = currency.convert(self._to_decimal(value), from_currency or currency.storage_currency(), display_curr)
        return currency.format_amount(amount, display_curr)

    def _money_sum(self, values, display_curr=None, *, from_currency=None):
        total = sum((self._to_decimal(v) for v in values), Decimal('0'))
        return self._money(total, display_curr=display_curr, from_currency=from_currency)

    def _qty(self, value, decimals=2):
        from core.money_display_policy import format_quantity
        return format_quantity(value, decimals=decimals)

    def _apply_report_table_profile(self, table, descriptor=None):
        """Apply a compact, accounting-friendly table profile to report grids."""
        try:
            table.set_density('compact')
        except Exception:
            pass
        try:
            table.setAlternatingRowColors(True)
            table.setWordWrap(False)
            table.set_responsive_columns(True)
            table.setProperty('layout_profile', 'reports_compact')
            if descriptor is not None:
                table.setProperty('report_grouped_navigation', True)
        except Exception:
            pass

    def setup_income_tab(self):
        layout = QVBoxLayout(self.income_tab)
        self.income_table = SmartTableView()
        layout.addWidget(self.income_table)

    def setup_balance_tab(self):
        layout = QVBoxLayout(self.balance_tab)
        self.balance_table = SmartTableView()
        layout.addWidget(self.balance_table)

    def setup_warehouse_tabs(self):
        self.wh_valuation_status = QLabel()
        val_layout = QVBoxLayout(self.wh_valuation_tab)
        val_layout.addWidget(self.wh_valuation_status)
        self.wh_valuation_table = SmartTableView()
        val_layout.addWidget(self.wh_valuation_table)

        self.wh_balances_status = QLabel()
        bal_layout = QVBoxLayout(self.wh_balances_tab)
        bal_layout.addWidget(self.wh_balances_status)
        self.wh_balances_table = SmartTableView()
        bal_layout.addWidget(self.wh_balances_table)

        mov_layout = QVBoxLayout(self.wh_movements_tab)
        self.wh_movements_table = SmartTableView()
        mov_layout.addWidget(self.wh_movements_table)

        trans_layout = QVBoxLayout(self.wh_transfers_tab)
        self.wh_transfers_table = SmartTableView()
        trans_layout.addWidget(self.wh_transfers_table)

    def setup_cash_bank_tabs(self):
        self.cash_summary_status = QLabel()
        cash_layout = QVBoxLayout(self.cash_summary_tab)
        cash_layout.addWidget(self.cash_summary_status)
        self.cash_summary_table = SmartTableView()
        cash_layout.addWidget(self.cash_summary_table)

        cash_mov_layout = QVBoxLayout(self.cash_movements_tab)
        self.cash_movements_table = SmartTableView()
        cash_mov_layout.addWidget(self.cash_movements_table)

        bank_mov_layout = QVBoxLayout(self.bank_movements_tab)
        self.bank_movements_table = SmartTableView()
        bank_mov_layout.addWidget(self.bank_movements_table)

        shifts_layout = QVBoxLayout(self.pos_shifts_tab)
        self.pos_shifts_table = SmartTableView()
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
            table = SmartTableView()
            setattr(self, attr, table)
            layout.addWidget(table)

    def _install_report_table_identities(self):
        """Attach stable Report Shell identities for saved layouts and printing."""
        for descriptor in self.REPORT_SHELL_DESCRIPTORS:
            table = getattr(self, descriptor.table_attr, None)
            if table is not None:
                try:
                    table.set_table_identity(descriptor.table_identity)
                    table.setProperty('report_key', descriptor.report_key)
                    table.setProperty('report_api_resource', descriptor.api_resource)
                    table.setProperty('report_network_mode', descriptor.network_mode)
                except Exception:
                    pass

    def _current_report_descriptor(self):
        """Return the ReportShellDescriptor for the active tab, if known."""
        tab = self._active_report_tab() if hasattr(self, '_active_report_tab') else (self.tabs.currentWidget() if hasattr(self, 'tabs') else None)
        for descriptor in self.REPORT_SHELL_DESCRIPTORS:
            if getattr(self, descriptor.tab_attr, None) is tab:
                return descriptor
        return None

    def report_permission_matrix(self):
        return self.permission_binder.matrix(document_id='reports')

    def can_report_action(self, action: str) -> bool:
        descriptor = self._current_report_descriptor()
        if descriptor is not None:
            if action == 'print' and not descriptor.supports_print:
                return False
            if action == 'export' and not descriptor.supports_export:
                return False
        return self.permission_binder.can(action, document_id='reports')

    def _require_report_print_permission(self, context=''):
        if not self.can_report_action('print'):
            raise PermissionError('reports.print')
        report_operation_policy.require(report_operation_policy.OP_PRINT, context=context or 'ReportsWidget.print')


    def report_print_settings(self):
        """Return the settings contract used by the report print button.

        Kept as a small runtime hook so diagnostics/tests can confirm that report
        printing uses the same SettingsService-backed contract as the rest of the
        project, including client/server profiles.
        """
        try:
            return settings_service.get_report_settings()
        except Exception:
            return {}

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
        descriptor = self._current_report_descriptor() if hasattr(self, '_current_report_descriptor') else None
        try:
            table.setProperty('print_title', self._active_report_title() if hasattr(self, '_active_report_title') else self.tabs.tabText(self.tabs.currentIndex()))
            if descriptor is not None:
                table.setProperty('report_key', descriptor.report_key)
                table.setProperty('report_api_resource', descriptor.api_resource)
                table.setProperty('report_network_mode', descriptor.network_mode)
                table.setProperty('report_currency_policy', descriptor.currency_policy)
        except Exception:
            pass
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.horizontalHeader().setStretchLastSection(True)
        self._apply_report_table_profile(table, descriptor)
        try:
            table.restore_layout()
        except Exception:
            pass
        return model

    def _apply_pos_shift_report_visibility(self):
        try:
            if not settings_service.pos_shifts_enabled():
                group = getattr(self, '_report_tab_to_group', {}).get(self.pos_shifts_tab)
                if group is not None:
                    idx = group.indexOf(self.pos_shifts_tab)
                    if idx >= 0:
                        group.removeTab(idx)
                else:
                    idx = self.tabs.indexOf(self.pos_shifts_tab)
                    if idx >= 0:
                        self.tabs.removeTab(idx)
        except Exception:
            pass

    def _apply_report_operation_state(self):
        can_view = self.permission_binder.can('view', document_id='reports') and report_operation_policy.can(report_operation_policy.OP_VIEW)
        can_print = self.permission_binder.can('print', document_id='reports') and report_operation_policy.can(report_operation_policy.OP_PRINT)
        for widget_name in ('refresh_btn', 'period_type', 'year_combo', 'month_combo', 'start_date', 'end_date',
                            'warehouse_filter', 'cashbox_filter', 'bank_filter', 'customer_filter', 'supplier_filter', 'item_filter'):
            widget = getattr(self, widget_name, None)
            if widget is not None:
                widget.setEnabled(can_view)
        if hasattr(self, 'tabs'):
            self.tabs.setEnabled(can_view)
        if hasattr(self, 'print_btn'):
            self.print_btn.setEnabled(can_view and can_print)
            if not can_print:
                try:
                    self.print_btn.setToolTip('reports.print')
                except Exception:
                    pass
        if not can_view:
            self._set_summary(tr('reports_access_denied'))

    def _require_report_operation(self, operation_key, context=''):
        return report_operation_policy.require(operation_key, context=context or 'ReportsWidget')

    def _refresh_phase36_reports(self, start, end, display_curr):
        """Compatibility wrapper for static reports contract checks.

        The implementation lives in ReportsPhase36Mixin; keeping this explicit
        method on ReportsWidget preserves the public/private widget contract
        expected by tools/reports_contract_check.py while avoiding duplicate
        report logic.
        """
        return super()._refresh_phase36_reports(start, end, display_curr)

    def refresh_report(self):
        """Refresh the active report tab only.

        Phase 37 stabilization: older code refreshed every report during page
        construction. That made ReportsWidget vulnerable to optional/remote
        report failures and slow server responses. The page now opens with the
        active tab only, while tab changes trigger this same method lazily.
        """
        try:
            self._require_report_operation(report_operation_policy.OP_VIEW, 'refresh_report')
        except PermissionError as exc:
            self._set_summary(tr('reports_access_denied'))
            print('⚠️ ' + tr('reports_refresh_failed', error=str(exc)))
            return
        start, end = self.get_date_range()
        self._set_summary('')
        display_curr = currency.get_display_currency()
        tab = self._active_report_tab() if hasattr(self, '_active_report_tab') else (self.tabs.currentWidget() if hasattr(self, 'tabs') else None)
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
        self._require_report_operation(report_operation_policy.OP_VIEW, 'refresh_all_reports')
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
            amount = Decimal(str(inc.get('balance', 0)))
            income_list.append({'statement': inc.get('name', ''), 'amount': self._money(amount, display_curr)})
        total_income = Decimal(str(stmt.get('total_income', 0)))
        income_list.append({'statement': tr('total_income'), 'amount': self._money(total_income, display_curr)})
        income_list.append({'statement': '', 'amount': ''})
        for exp in stmt.get('expenses', []):
            amount = Decimal(str(exp.get('balance', 0)))
            income_list.append({'statement': exp.get('name', ''), 'amount': self._money(amount, display_curr)})
        total_expenses = Decimal(str(stmt.get('total_expenses', 0)))
        net_profit = Decimal(str(stmt.get('net_profit', 0)))
        income_list.append({'statement': tr('total_expenses'), 'amount': self._money(total_expenses, display_curr)})
        income_list.append({'statement': tr('net_profit'), 'amount': self._money(net_profit, display_curr)})
        self._set_table(self.income_table, income_list, [tr('statement'), tr('amount')], ['statement', 'amount'])
        self._set_summary(f"{tr('total_income')}: {self._money(total_income, display_curr)} | {tr('total_expenses')}: {self._money(total_expenses, display_curr)} | {tr('net_profit')}: {self._money(net_profit, display_curr)}")

    def _refresh_balance(self, start, end, display_curr):
        bs = reporting_service.balance_sheet(start, end)
        rows = []
        for a in bs.get('assets', []):
            amount = Decimal(str(a.get('debit', 0)))
            rows.append({'account': a.get('name', ''), 'amount': self._money(amount, display_curr)})
        total_assets = Decimal(str(bs.get('total_assets', 0)))
        rows.append({'account': tr('total_assets'), 'amount': self._money(total_assets, display_curr)})
        self._set_table(self.balance_table, rows, [tr('account'), tr('amount')], ['account', 'amount'])
        self._set_summary(f"{tr('total_assets')}: {self._money(total_assets, display_curr)}")

    def _refresh_warehouse_reports(self, display_curr):
        wh_id = self.warehouse_filter.currentData()
        valuation = reporting_service.warehouse_valuation(warehouse_id=wh_id)
        val_rows = []
        for wh in valuation.get('warehouses', []):
            val = currency.convert(Decimal(str(wh.get('total_value', 0))), currency.storage_currency(), display_curr)
            val_rows.append({
                'warehouse': wh.get('warehouse_name', ''),
                'item_count': wh.get('item_count', 0),
                'total_qty': self._qty(wh.get('total_qty', 0)),
                'total_value': currency.format_amount(val),
            })
        grand = currency.convert(Decimal(str(valuation.get('grand_total', 0))), currency.storage_currency(), display_curr)
        self.wh_valuation_status.setText(tr('reports_inventory_total_value', amount=currency.format_amount(grand)))
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
                'qty': self._qty(qty),
                'unit': b.get('unit') or '',
                'avg': self._money(avg, display_curr),
                'value': self._money(value, display_curr),
            })
        self.wh_balances_status.setText(tr('reports_records_total_value', count=len(bal_rows), amount=currency.format_amount(total_value)))
        self._set_table(self.wh_balances_table, bal_rows, ['المستودع', 'المادة', 'الباركود', 'الكمية', 'الوحدة', 'متوسط التكلفة', 'قيمة المخزون'], ['warehouse', 'item', 'barcode', 'qty', 'unit', 'avg', 'value'])

        mov_rows = []
        for m in reporting_service.warehouse_movements(warehouse_id=wh_id, limit=500):
            mov_rows.append({
                'date': m.get('movement_date') or m.get('created_at') or '',
                'warehouse': m.get('warehouse_name', ''),
                'item': m.get('item_name', ''),
                'type': self._movement_label(m.get('movement_type')),
                'qty': self._qty(m.get('quantity') or 0),
                'cost': self._money(m.get('unit_cost') or 0, display_curr),
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
                'qty': self._qty(t.get('quantity') or 0),
                'status': tr('cancelled') if t.get('status') == 'cancelled' else tr('active'),
                'notes': t.get('notes') or '',
            })
        self._set_table(self.wh_transfers_table, trans_rows, ['رقم التحويل', 'التاريخ', 'المادة', 'من', 'إلى', 'الكمية', 'الحالة', 'ملاحظات'], ['no', 'date', 'item', 'from', 'to', 'qty', 'status', 'notes'])

    def _refresh_cash_bank_reports(self, display_curr):
        cashbox_id = self.cashbox_filter.currentData() if hasattr(self, 'cashbox_filter') else None
        bank_id = self.bank_filter.currentData() if hasattr(self, 'bank_filter') else None
        summary = reporting_service.cash_bank_summary()
        cash_total = currency.convert(Decimal(str(summary.get('cash_total') or 0)), currency.storage_currency(), display_curr)
        bank_total = currency.convert(Decimal(str(summary.get('bank_total') or 0)), currency.storage_currency(), display_curr)
        available = currency.convert(Decimal(str(summary.get('available_total') or 0)), currency.storage_currency(), display_curr)
        self.cash_summary_status.setText(
            tr('reports_cash_bank_available', cash=currency.format_amount(cash_total), bank=currency.format_amount(bank_total), total=currency.format_amount(available))
        )
        summary_rows = []
        for c in reporting_service.cashboxes_report():
            bal = currency.convert(Decimal(str(c.get('balance') or 0)), currency.storage_currency(), display_curr)
            summary_rows.append({
                'type': tr('cashbox'),
                'branch': c.get('branch_name') or '',
                'name': c.get('name') or '',
                'code': c.get('code') or '',
                'balance': currency.format_amount(bal),
                'status': 'نشط' if int(c.get('is_active') or 0) else 'مؤرشف',
            })
        for b in reporting_service.bank_accounts_report():
            bal = currency.convert(Decimal(str(b.get('balance') or 0)), currency.storage_currency(), display_curr)
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
            amount = currency.convert(raw_amount, currency.storage_currency(), display_curr)
            running_display = currency.convert(cash_running, currency.storage_currency(), display_curr)
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
            amount = currency.convert(raw_amount, currency.storage_currency(), display_curr)
            running_display = currency.convert(bank_running, currency.storage_currency(), display_curr)
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
                'opening': self._money(s.get('opening_amount') or 0, display_curr),
                'cash': self._money(s.get('total_cash') or 0, display_curr),
                'card': self._money(s.get('total_card') or 0, display_curr),
                'expected': self._money(s.get('expected_amount') or 0, display_curr),
                'actual': self._money(s.get('actual_amount') or 0, display_curr),
                'diff': self._money(s.get('difference_amount') or 0, display_curr),
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

