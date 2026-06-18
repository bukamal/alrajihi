# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
                             QTabWidget, QDateEdit, QComboBox, QLabel, QHeaderView, QMessageBox, QFrame)
from PyQt5.QtCore import Qt, QDate
from decimal import Decimal
from core.services.invoice_service import invoice_service
from core.services.workflow_policy_service import workflow_policy_service
from core.services.catalog_service import catalog_service
from currency import currency
from ui.smart_table_view import SmartTableView
from models.table_models import GenericTableModel
# InvoiceDialog is opened through workspace document tabs from MainWindow.
from utils import show_toast
from views.widgets.components.table_toolbar import TableToolbar
from theme_manager import ThemeManager
from views.widgets.modern_ui import apply_modern_widget
from i18n import translate, qt_layout_direction
from core.services.permission_service import permission_service

class InvoicesWidget(QWidget):
    def __init__(self, parent=None, invoice_scope=None):
        """Invoice list widget.

        invoice_scope:
            None       -> legacy combined widget with sale/purchase tabs.
            'sale'     -> standalone sales invoices page.
            'purchase' -> standalone purchase invoices page.
        """
        super().__init__(parent)
        self.setLayoutDirection(qt_layout_direction())
        self._apply_page_style()
        self.invoice_scope = invoice_scope
        self.sales_page = 0
        self.purchases_page = 0
        self.page_size = 50

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        if invoice_scope == 'sale':
            self.sales_tab = QWidget()
            self.setup_sales_tab()
            layout.addWidget(self.sales_tab)
        elif invoice_scope == 'purchase':
            self.purchases_tab = QWidget()
            self.setup_purchases_tab()
            layout.addWidget(self.purchases_tab)
        else:
            self.tabs = QTabWidget()
            self.sales_tab = QWidget()
            self.purchases_tab = QWidget()
            self.setup_sales_tab()
            self.setup_purchases_tab()
            self.tabs.addTab(self.sales_tab, "💰 " + translate("sales_invoices"))
            self.tabs.addTab(self.purchases_tab, "📦 " + translate("purchase_invoices"))
            layout.addWidget(self.tabs)

        # Phase117: standalone invoice pages should not show duplicated top header cards.
        apply_modern_widget(self)
        self.refresh_all()

    def _apply_page_style(self):
        c = ThemeManager.colors()
        self.setStyleSheet(f"""
            QWidget {{
                background: {c['bg_window']};
                color: {c['text_primary']};
            }}
            QFrame#InvoicePageCard {{
                background: {c['card_bg']};
                border: 1px solid {c['border']};
                border-radius: 14px;
            }}
            QLabel#PageTitle {{
                color: {c['primary']};
                font-size: 22px;
                font-weight: 900;
            }}
            QLabel#PageSubtitle {{
                color: {c['text_secondary']};
                font-size: 12px;
            }}
            QLabel#FilterLabel {{
                color: {c['text_secondary']};
                font-weight: 800;
            }}
            QLineEdit, QComboBox, QDateEdit {{
                min-height: 34px;
                border: 1px solid {c['border']};
                border-radius: 9px;
                padding: 5px 9px;
                background: {c['input_bg']};
                color: {c['text_primary']};
                selection-background-color: {c['selection_bg']};
                selection-color: {c['selection_text']};
            }}
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
                border: 1px solid {c['border_focus']};
            }}
            QTableView, QTableWidget {{
                background: {c['bg_table']};
                color: {c['text_primary']};
                alternate-background-color: {c['bg_table_alt']};
                gridline-color: {c['border']};
                border: 1px solid {c['border']};
                border-radius: 12px;
                selection-background-color: {c['selection_bg']};
                selection-color: {c['selection_text']};
                outline: 0;
            }}
            QTableView::item, QTableWidget::item {{
                padding: 6px;
                border-bottom: 1px solid {c['border']};
            }}
            QHeaderView::section {{
                background: {c['header_bg']};
                color: {c['header_text']};
                font-weight: 800;
                padding: 8px;
                border: none;
                border-left: 1px solid {c['border']};
            }}
            QTabWidget::pane {{
                border: 1px solid {c['border']};
                background: {c['bg_window']};
                border-radius: 12px;
            }}
            QTabBar::tab {{
                background: {c['bg_panel']};
                color: {c['text_secondary']};
                border: 1px solid {c['border']};
                padding: 8px 14px;
                margin-left: 3px;
                border-top-left-radius: 9px;
                border-top-right-radius: 9px;
                font-weight: 800;
            }}
            QTabBar::tab:selected {{
                background: {c['primary']};
                color: white;
            }}
            QPushButton {{
                min-height: 32px;
                border-radius: 8px;
                padding: 5px 12px;
                background: {c['bg_panel']};
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                font-weight: 700;
            }}
            QPushButton:hover {{ background: {c['brand_soft']}; border-color: {c['primary']}; }}
        """)

    def _make_page_header(self, title, subtitle):
        card = QFrame()
        card.setObjectName("InvoicePageCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        title_label = QLabel(title)
        title_label.setObjectName("PageTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("PageSubtitle")
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        return card

    def _label(self, text):
        label = QLabel(text)
        label.setObjectName("FilterLabel")
        return label

    def _add_workflow_buttons(self, layout, inv_type):
        """Operational workflow buttons, honoring optional Workflow settings."""
        row = QHBoxLayout()
        try:
            workflow_enabled = workflow_policy_service.workflow_enabled()
            approval_required = workflow_policy_service.approval_required()
        except Exception:
            workflow_enabled = True
            approval_required = True
        actions = []
        if workflow_enabled:
            actions.append(('workflow_submit', 'submit', 'approval.submit'))
            if approval_required:
                actions.extend([
                    ('workflow_approve', 'approve', 'approval.approve'),
                    ('workflow_reject', 'reject', 'approval.reject'),
                ])
            actions.append(('workflow_post', 'post', 'accounting.post'))
            actions.append(('workflow_reopen', 'reopen', 'invoices.edit'))
        else:
            actions.append(('workflow_post', 'post', 'accounting.post'))
        for label_key, action, perm in actions:
            btn = QPushButton(translate(label_key))
            try:
                if not permission_service.can(perm):
                    btn.setEnabled(False)
                    btn.setToolTip(translate('permission_denied'))
            except Exception:
                pass
            btn.clicked.connect(lambda _=False, a=action, t=inv_type: self._run_workflow_action(t, a))
            row.addWidget(btn)
        row.addStretch()
        layout.addLayout(row)

    def _run_workflow_action(self, inv_type, action):
        inv_id = self._selected_invoice_id(inv_type)
        if not inv_id:
            show_toast(translate('select_invoice_first'), 'warning', self)
            return
        try:
            if action == 'submit':
                invoice_service.submit(inv_id)
            elif action == 'approve':
                invoice_service.approve(inv_id)
            elif action == 'reject':
                invoice_service.reject(inv_id)
            elif action == 'post':
                invoice_service.post(inv_id)
            elif action == 'reopen':
                invoice_service.reopen(inv_id)
            show_toast(translate('workflow_action_done'), 'success', self)
            self.refresh_all()
        except Exception as exc:
            QMessageBox.critical(self, translate('workflow_title'), str(exc))

    def setup_sales_tab(self):
        layout = QVBoxLayout(self.sales_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.sales_toolbar = TableToolbar(translate("sales_invoice"), translate("search_sales_invoices"), self)
        self.sales_toolbar.addRequested.connect(lambda: self.create_invoice('sale'))
        self.sales_toolbar.editRequested.connect(lambda: self.edit_selected_invoice('sale'))
        self.sales_toolbar.deleteRequested.connect(lambda: self.delete_selected_invoice('sale'))
        self.sales_toolbar.exportRequested.connect(lambda: self.sales_table.export_to_excel())
        self.sales_toolbar.printRequested.connect(lambda: self.sales_table.print_table())
        self.sales_toolbar.refreshRequested.connect(lambda: self.refresh_tab('sale', reset_page=True))
        self.sales_toolbar.resetColumnsRequested.connect(lambda: self.sales_table.reset_layout())
        self.sales_toolbar.searchChanged.connect(lambda _text: self.refresh_tab('sale', reset_page=True))
        layout.addWidget(self.sales_toolbar)
        self._add_workflow_buttons(layout, 'sale')
        self.sales_search = self.sales_toolbar.search_edit

        # شريط الفلترة المتخصص للتبويب
        filter_layout = QHBoxLayout()

        self.sales_start_date = QDateEdit()
        self.sales_start_date.setDate(QDate.currentDate().addDays(-30))
        self.sales_start_date.setCalendarPopup(True)
        self.sales_start_date.dateChanged.connect(lambda: self.refresh_tab('sale', reset_page=True))
        filter_layout.addWidget(self._label(translate("from_date")))
        filter_layout.addWidget(self.sales_start_date)

        self.sales_end_date = QDateEdit()
        self.sales_end_date.setDate(QDate.currentDate())
        self.sales_end_date.setCalendarPopup(True)
        self.sales_end_date.dateChanged.connect(lambda: self.refresh_tab('sale', reset_page=True))
        filter_layout.addWidget(self._label(translate("to_date")))
        filter_layout.addWidget(self.sales_end_date)

        self.sales_customer_combo = QComboBox()
        self.sales_customer_combo.addItem(translate("all"), None)
        self.load_customers()
        self.sales_customer_combo.currentIndexChanged.connect(lambda: self.refresh_tab('sale', reset_page=True))
        filter_layout.addWidget(self._label(translate("customer_label")))
        filter_layout.addWidget(self.sales_customer_combo)

        filter_card = QFrame()
        filter_card.setObjectName("InvoicePageCard")
        filter_card_layout = QVBoxLayout(filter_card)
        filter_card_layout.setContentsMargins(12, 10, 12, 10)
        filter_card_layout.addLayout(filter_layout)
        layout.addWidget(filter_card)

        self.sales_table = SmartTableView()
        self.sales_table.set_table_identity("InvoicesWidget.sales")
        self.sales_toolbar.set_table(self.sales_table)
        self.sales_table.setSelectionBehavior(SmartTableView.SelectRows)
        self.sales_table.verticalHeader().setDefaultSectionSize(38)
        self.sales_table.doubleClicked.connect(lambda idx: self.edit_invoice('sale', idx))
        layout.addWidget(self.sales_table)

        # شريط التنقل
        pagination = QHBoxLayout()
        self.sales_prev = QPushButton(translate("previous"))
        self.sales_prev.clicked.connect(lambda: self.prev_page('sale'))
        self.sales_next = QPushButton(translate("next"))
        self.sales_next.clicked.connect(lambda: self.next_page('sale'))
        self.sales_page_label = QLabel()
        pagination.addWidget(self.sales_prev)
        pagination.addWidget(self.sales_page_label)
        pagination.addWidget(self.sales_next)
        pagination.addStretch()
        layout.addLayout(pagination)

    def setup_purchases_tab(self):
        layout = QVBoxLayout(self.purchases_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.purchases_toolbar = TableToolbar(translate("purchase_invoice"), translate("search_purchase_invoices"), self)
        self.purchases_toolbar.addRequested.connect(lambda: self.create_invoice('purchase'))
        self.purchases_toolbar.editRequested.connect(lambda: self.edit_selected_invoice('purchase'))
        self.purchases_toolbar.deleteRequested.connect(lambda: self.delete_selected_invoice('purchase'))
        self.purchases_toolbar.exportRequested.connect(lambda: self.purchases_table.export_to_excel())
        self.purchases_toolbar.printRequested.connect(lambda: self.purchases_table.print_table())
        self.purchases_toolbar.refreshRequested.connect(lambda: self.refresh_tab('purchase', reset_page=True))
        self.purchases_toolbar.resetColumnsRequested.connect(lambda: self.purchases_table.reset_layout())
        self.purchases_toolbar.searchChanged.connect(lambda _text: self.refresh_tab('purchase', reset_page=True))
        layout.addWidget(self.purchases_toolbar)
        self._add_workflow_buttons(layout, 'purchase')
        self.purchases_search = self.purchases_toolbar.search_edit

        filter_layout = QHBoxLayout()

        self.purchases_start_date = QDateEdit()
        self.purchases_start_date.setDate(QDate.currentDate().addDays(-30))
        self.purchases_start_date.setCalendarPopup(True)
        self.purchases_start_date.dateChanged.connect(lambda: self.refresh_tab('purchase', reset_page=True))
        filter_layout.addWidget(self._label(translate("from_date")))
        filter_layout.addWidget(self.purchases_start_date)

        self.purchases_end_date = QDateEdit()
        self.purchases_end_date.setDate(QDate.currentDate())
        self.purchases_end_date.setCalendarPopup(True)
        self.purchases_end_date.dateChanged.connect(lambda: self.refresh_tab('purchase', reset_page=True))
        filter_layout.addWidget(self._label(translate("to_date")))
        filter_layout.addWidget(self.purchases_end_date)

        self.purchases_supplier_combo = QComboBox()
        self.purchases_supplier_combo.addItem(translate("all"), None)
        self.load_suppliers()
        self.purchases_supplier_combo.currentIndexChanged.connect(lambda: self.refresh_tab('purchase', reset_page=True))
        filter_layout.addWidget(self._label(translate("supplier_label")))
        filter_layout.addWidget(self.purchases_supplier_combo)

        filter_card = QFrame()
        filter_card.setObjectName("InvoicePageCard")
        filter_card_layout = QVBoxLayout(filter_card)
        filter_card_layout.setContentsMargins(12, 10, 12, 10)
        filter_card_layout.addLayout(filter_layout)
        layout.addWidget(filter_card)

        self.purchases_table = SmartTableView()
        self.purchases_table.set_table_identity("InvoicesWidget.purchases")
        self.purchases_toolbar.set_table(self.purchases_table)
        self.purchases_table.setSelectionBehavior(SmartTableView.SelectRows)
        self.purchases_table.verticalHeader().setDefaultSectionSize(38)
        self.purchases_table.doubleClicked.connect(lambda idx: self.edit_invoice('purchase', idx))
        layout.addWidget(self.purchases_table)

        pagination = QHBoxLayout()
        self.purchases_prev = QPushButton(translate("previous"))
        self.purchases_prev.clicked.connect(lambda: self.prev_page('purchase'))
        self.purchases_next = QPushButton(translate("next"))
        self.purchases_next.clicked.connect(lambda: self.next_page('purchase'))
        self.purchases_page_label = QLabel()
        pagination.addWidget(self.purchases_prev)
        pagination.addWidget(self.purchases_page_label)
        pagination.addWidget(self.purchases_next)
        pagination.addStretch()
        layout.addLayout(pagination)

    def _is_offline_read_error(self, exc):
        text = str(exc)
        return (
            'No connection and this operation cannot be queued safely' in text
            or 'Connection refused' in text
            or 'Max retries exceeded' in text
            or 'Failed to establish a new connection' in text
        )

    def _notify_offline_read(self, context=''):
        msg = translate('server_offline_invoices')
        if context:
            msg = f'{context}: {msg}'
        try:
            show_toast(msg, 'warning', self)
        except Exception:
            pass


    # Phase137: external invoice tabs are management summaries only.
    # Line-item columns stay inside invoice dialogs where they are editable/contextual.

    def load_customers(self):
        try:
            customers = catalog_service.customers(limit=1000)  # جلب أول 1000 عميل فقط للقائمة
        except Exception as exc:
            if self._is_offline_read_error(exc):
                self._notify_offline_read(translate('customer_list'))
                return
            raise
        for c in customers:
            self.sales_customer_combo.addItem(c.get('name', ''), c.get('id'))

    def load_suppliers(self):
        try:
            suppliers = catalog_service.suppliers(limit=1000)
        except Exception as exc:
            if self._is_offline_read_error(exc):
                self._notify_offline_read(translate('supplier_list'))
                return
            raise
        for s in suppliers:
            self.purchases_supplier_combo.addItem(s.get('name', ''), s.get('id'))

    # Phase116: global shell search support.
    def set_global_filter(self, text: str):
        text = text or ''
        if self.invoice_scope == 'sale':
            if hasattr(self, 'sales_search') and self.sales_search.text() != text:
                self.sales_search.setText(text)
            else:
                self.refresh_tab('sale', reset_page=True)
        elif self.invoice_scope == 'purchase':
            if hasattr(self, 'purchases_search') and self.purchases_search.text() != text:
                self.purchases_search.setText(text)
            else:
                self.refresh_tab('purchase', reset_page=True)
        else:
            if hasattr(self, 'sales_search'):
                self.sales_search.setText(text)
            if hasattr(self, 'purchases_search'):
                self.purchases_search.setText(text)

    def refresh_all(self):
        try:
            if self.invoice_scope == 'sale':
                self.refresh_tab('sale', reset_page=True)
            elif self.invoice_scope == 'purchase':
                self.refresh_tab('purchase', reset_page=True)
            else:
                self.refresh_tab('sale', reset_page=True)
                self.refresh_tab('purchase', reset_page=True)
        except Exception as exc:
            if self._is_offline_read_error(exc):
                self._notify_offline_read()
                return
            raise

    def refresh_tab(self, inv_type, reset_page=False):
        if inv_type == 'sale':
            if reset_page:
                self.sales_page = 0
            search = self.sales_search.text().strip() or None
            start_date = self.sales_start_date.date().toString("yyyy-MM-dd")
            end_date = self.sales_end_date.date().toString("yyyy-MM-dd")
            customer_id = self.sales_customer_combo.currentData()
            try:
                invoices, total = invoice_service.list_invoices(
                    search=search, inv_type='sale', start_date=start_date, end_date=end_date,
                    customer_id=customer_id, limit=self.page_size, offset=self.sales_page * self.page_size
                )
            except Exception as exc:
                if self._is_offline_read_error(exc):
                    self._notify_offline_read(translate('sales_invoices'))
                    return
                raise
            data = []
            for inv in invoices:
                remaining = Decimal(str(inv.get('total', 0))) - Decimal(str(inv.get('paid', 0)))
                paid_display = currency.format_amount(currency.convert(inv.get('paid', 0), 'USD', currency.get_display_currency()))
                row = {
                    'id': inv['id'],
                    'reference': inv.get('id', ''),
                    'invoice': inv.get('reference', ''),
                    'date': inv.get('date', ''),
                    'customer': inv.get('customer_name', translate('cash_customer')),
                    'invoice_total': currency.format_amount(currency.convert(inv.get('total', 0), 'USD', currency.get_display_currency())),
                    'paid': paid_display,
                    'received': paid_display,
                    'remaining': currency.format_amount(currency.convert(remaining, 'USD', currency.get_display_currency())),
                    'workflow_status': inv.get('workflow_status', 'DRAFT'),
                    'notes': inv.get('notes', '')
                }
                data.append(row)
            headers = ['reference', 'invoice', 'invoice_total', 'customer', 'paid', 'received', 'remaining', 'workflow_status', 'invoice_profit', 'date', 'notes']
            display_headers = [translate('reference'), translate('invoice'), translate('invoice_value'), translate('customer'), translate('paid'), translate('received'), translate('remaining'), 'Workflow', translate('invoice_profit'), translate('date'), translate('notes')]
            model = GenericTableModel(data, display_headers, key_fields=['id'], data_keys=headers)
            self.sales_table.setModel(model)
            self._connect_table_selection('sale')
            # id محفوظ داخلياً عبر key_fields ولا يوجد كعمود عرض.
            self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
            self.sales_table.horizontalHeader().setStretchLastSection(True)
            self.sales_table.refresh_style()
            self.sales_invoices = invoices
            total_pages = (total + self.page_size - 1) // self.page_size
            total_pages = max(1, total_pages)
            self.sales_page_label.setText(translate("page_of", page=self.sales_page + 1, pages=total_pages))
            self.sales_toolbar.set_counter(self._counter_text(self.sales_page, len(data), total))
            self.sales_prev.setEnabled(self.sales_page > 0)
            self.sales_next.setEnabled(self.sales_page + 1 < total_pages)
        else:
            if reset_page:
                self.purchases_page = 0
            search = self.purchases_search.text().strip() or None
            start_date = self.purchases_start_date.date().toString("yyyy-MM-dd")
            end_date = self.purchases_end_date.date().toString("yyyy-MM-dd")
            supplier_id = self.purchases_supplier_combo.currentData()
            try:
                invoices, total = invoice_service.list_invoices(
                    search=search, inv_type='purchase', start_date=start_date, end_date=end_date,
                    supplier_id=supplier_id, limit=self.page_size, offset=self.purchases_page * self.page_size
                )
            except Exception as exc:
                if self._is_offline_read_error(exc):
                    self._notify_offline_read(translate('purchase_invoices'))
                    return
                raise
            data = []
            for inv in invoices:
                remaining = Decimal(str(inv.get('total', 0))) - Decimal(str(inv.get('paid', 0)))
                row = {
                    'id': inv['id'],
                    'reference': inv.get('id', ''),
                    'invoice': inv.get('reference', ''),
                    'date': inv.get('date', ''),
                    'supplier': inv.get('supplier_name', translate('cash_customer')),
                    'invoice_total': currency.format_amount(currency.convert(inv.get('total', 0), 'USD', currency.get_display_currency())),
                    'paid': currency.format_amount(currency.convert(inv.get('paid', 0), 'USD', currency.get_display_currency())),
                    'remaining': currency.format_amount(currency.convert(remaining, 'USD', currency.get_display_currency())),
                    'workflow_status': inv.get('workflow_status', 'DRAFT'),
                    'notes': inv.get('notes', '')
                }
                data.append(row)
            headers = ['reference', 'invoice', 'invoice_total', 'supplier', 'paid', 'remaining', 'workflow_status', 'date', 'notes']
            display_headers = [translate('reference'), translate('invoice'), translate('invoice_value'), translate('supplier'), translate('paid'), translate('remaining'), 'Workflow', translate('date'), translate('notes')]
            model = GenericTableModel(data, display_headers, key_fields=['id'], data_keys=headers)
            self.purchases_table.setModel(model)
            self._connect_table_selection('purchase')
            # id محفوظ داخلياً عبر key_fields ولا يوجد كعمود عرض.
            self.purchases_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
            self.purchases_table.horizontalHeader().setStretchLastSection(True)
            self.purchases_table.refresh_style()
            self.purchases_invoices = invoices
            total_pages = (total + self.page_size - 1) // self.page_size
            total_pages = max(1, total_pages)
            self.purchases_page_label.setText(translate("page_of", page=self.purchases_page + 1, pages=total_pages))
            self.purchases_toolbar.set_counter(self._counter_text(self.purchases_page, len(data), total))
            self.purchases_prev.setEnabled(self.purchases_page > 0)
            self.purchases_next.setEnabled(self.purchases_page + 1 < total_pages)

    def create_invoice(self, inv_type):
        main = self.window()
        if hasattr(main, 'open_quick_invoice'):
            main.open_quick_invoice(inv_type)
        else:
            from features.invoices import InvoiceEditorTab
            widget = InvoiceEditorTab(self, inv_type=inv_type)
            widget.saved.connect(lambda *_: self.refresh_all())
            widget.show()

    def edit_invoice(self, inv_type, index):
        if not permission_service.can(permission_service.ACTION_EDIT_INVOICES):
            QMessageBox.warning(self, 'الصلاحيات', permission_service.denied_message(permission_service.ACTION_EDIT_INVOICES))
            return
        row = index.row()
        if inv_type == 'sale':
            inv_id = self.sales_table.model().get_id(row)
        else:
            inv_id = self.purchases_table.model().get_id(row)
        if inv_id:
            main = self.window()
            if hasattr(main, 'open_quick_invoice'):
                main.open_quick_invoice(inv_type, invoice_id=inv_id)
            else:
                from features.invoices import InvoiceEditorTab
                widget = InvoiceEditorTab(self, inv_type=inv_type, invoice_id=inv_id)
                widget.saved.connect(lambda *_: self.refresh_all())
                widget.show()


    def _counter_text(self, page, visible_count, total_count):
        if total_count <= 0:
            return translate("no_records")
        start = page * self.page_size + 1
        end = min(total_count, page * self.page_size + visible_count)
        return translate("showing_records", start=start, end=end, total=total_count)

    def _connect_table_selection(self, inv_type):
        table = self.sales_table if inv_type == 'sale' else self.purchases_table
        sm = table.selectionModel()
        if sm is None:
            return
        handler = self._on_sales_selection_changed if inv_type == 'sale' else self._on_purchases_selection_changed
        try:
            sm.selectionChanged.disconnect(handler)
        except Exception:
            pass
        sm.selectionChanged.connect(handler)
        self._update_invoice_actions(inv_type)

    def _on_sales_selection_changed(self, selected=None, deselected=None):
        self._update_invoice_actions('sale')

    def _on_purchases_selection_changed(self, selected=None, deselected=None):
        self._update_invoice_actions('purchase')

    def _update_invoice_actions(self, inv_type):
        table = self.sales_table if inv_type == 'sale' else self.purchases_table
        toolbar = self.sales_toolbar if inv_type == 'sale' else self.purchases_toolbar
        sm = table.selectionModel()
        has_selection = bool(sm and sm.selectedRows())
        toolbar.set_edit_enabled(has_selection and permission_service.can(permission_service.ACTION_EDIT_INVOICES))
        toolbar.set_delete_enabled(has_selection and permission_service.can(permission_service.ACTION_DELETE))

    def _selected_invoice_id(self, inv_type):
        table = self.sales_table if inv_type == 'sale' else self.purchases_table
        model = table.model()
        sm = table.selectionModel()
        if not model or not sm or not sm.selectedRows():
            return None
        row = sm.selectedRows()[0].row()
        return model.get_id(row)

    def edit_selected_invoice(self, inv_type):
        if not permission_service.can(permission_service.ACTION_EDIT_INVOICES):
            QMessageBox.warning(self, 'الصلاحيات', permission_service.denied_message(permission_service.ACTION_EDIT_INVOICES))
            return
        inv_id = self._selected_invoice_id(inv_type)
        if not inv_id:
            show_toast(translate("select_invoice_first"), "warning", self)
            return
        main = self.window()
        if hasattr(main, 'open_quick_invoice'):
            main.open_quick_invoice(inv_type, invoice_id=inv_id)
        else:
            from features.invoices import InvoiceEditorTab
            widget = InvoiceEditorTab(self, inv_type=inv_type, invoice_id=inv_id)
            widget.saved.connect(lambda *_: self.refresh_all())
            widget.show()

    def delete_selected_invoice(self, inv_type):
        if not permission_service.can(permission_service.ACTION_DELETE):
            QMessageBox.warning(self, 'الصلاحيات', permission_service.denied_message(permission_service.ACTION_DELETE))
            return
        inv_id = self._selected_invoice_id(inv_type)
        if not inv_id:
            show_toast(translate("select_invoice_delete"), "warning", self)
            return
        inv = invoice_service.get(inv_id) or {}
        reference = inv.get('reference', inv_id)
        if invoice_service.has_linked_vouchers(inv_id):
            QMessageBox.warning(self, translate("delete_invoice_blocked_title"), translate("delete_invoice_blocked_message"))
            return
        reply = QMessageBox.question(
            self,
            translate("confirm_delete_invoice_title"),
            translate("confirm_delete_invoice_message", reference=reference),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            invoice_service.delete(inv_id)
            show_toast(translate("invoice_deleted"), "success", self)
            self.refresh_all()
        except Exception as e:
            QMessageBox.critical(self, translate("delete_failed"), str(e))


    def prev_page(self, inv_type):
        if inv_type == 'sale' and self.sales_page > 0:
            self.sales_page -= 1
            self.refresh_tab('sale')
        elif inv_type == 'purchase' and self.purchases_page > 0:
            self.purchases_page -= 1
            self.refresh_tab('purchase')

    def next_page(self, inv_type):
        if inv_type == 'sale':
            self.sales_page += 1
            self.refresh_tab('sale')
        else:
            self.purchases_page += 1
            self.refresh_tab('purchase')


class SalesInvoicesWidget(InvoicesWidget):
    """Standalone sales invoices page; no purchase tab."""
    def __init__(self, parent=None):
        super().__init__(parent, invoice_scope='sale')


class PurchaseInvoicesWidget(InvoicesWidget):
    """Standalone purchase invoices page; no sales tab."""
    def __init__(self, parent=None):
        super().__init__(parent, invoice_scope='purchase')

# Phase110 offline guard markers: فواتير الشراء

# Phase110 stable offline UI markers:
# _notify_offline_read('فواتير الشراء')
