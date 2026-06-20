# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
                             QLabel, QComboBox, QHeaderView, QMessageBox, QDialog, QFormLayout)
from PyQt5.QtCore import Qt
from decimal import Decimal
from core.services.entity_service import entity_service
from core.services.party_operation_policy import party_operation_policy
from currency import currency
from ui.smart_table_view import SmartTableView
from models.table_models import GenericTableModel
from utils import show_toast
from core.offline_guard import is_offline_read_error, offline_read_message
from views.widgets.modern_ui import apply_modern_widget
from views.dialogs.add_entity_dialog import AddEntityDialog  # legacy emergency fallback; Document Shell remains primary
from i18n import translate as tr, qt_layout_direction
from ui.components.responsive_master_detail import DetailPlaceholder, ResponsiveMasterDetail
from workspace.lists.list_workspace_contract import bind_list_workspace

class CustomersWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        bind_list_workspace(self, 'customers')
        self.setLayoutDirection(qt_layout_direction())
        self.current_page = 0
        self.page_size = 50
        self.total_count = 0

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # شريط البحث والفلترة
        top_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(tr("search_customer"))
        self.search_edit.textChanged.connect(self.refresh)
        top_layout.addWidget(self.search_edit)

        self.balance_filter = QComboBox()
        self.balance_filter.addItems([tr("all"), tr("positive_balance"), tr("negative_balance"), tr("zero_balance")])
        self.balance_filter.currentIndexChanged.connect(self.refresh)
        top_layout.addWidget(QLabel(tr("balance_filter_label")))
        top_layout.addWidget(self.balance_filter)

        self.add_btn = QPushButton(tr("add_customer"))
        self.add_btn.setObjectName("primary")
        self.add_btn.clicked.connect(self.add_customer)
        top_layout.addWidget(self.add_btn)

        layout.addLayout(top_layout)

        # الجدول والمعاينة بنمط Master-Detail responsive
        self.table = SmartTableView(identity="customers")
        self.table.setSelectionBehavior(SmartTableView.SelectRows)
        self.table.doubleClicked.connect(self.edit_customer)
        self.detail_panel = DetailPlaceholder(tr('customer_details') if tr('customer_details') != 'customer_details' else tr('customer'))
        self.master_detail = ResponsiveMasterDetail(self.table, self.detail_panel, self)
        layout.addWidget(self.master_detail, 1)

        # شريط التنقل بين الصفحات
        pagination_layout = QHBoxLayout()
        self.prev_btn = QPushButton(tr("previous"))
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn = QPushButton(tr("next"))
        self.next_btn.clicked.connect(self.next_page)
        self.page_label = QLabel()
        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_btn)
        pagination_layout.addStretch()
        layout.addLayout(pagination_layout)

        apply_modern_widget(self, tr('customers_title'), tr('customers_subtitle'))
        self._apply_operation_policy()
        self.refresh()


    def _apply_operation_policy(self):
        self.add_btn.setEnabled(party_operation_policy.can(party_operation_policy.OP_CUSTOMER_CREATE))

    def set_global_filter(self, text: str):
        text = text or ''
        field = getattr(self, 'search_edit', None)
        if field is not None and field.text() != text:
            field.setText(text)
        elif hasattr(self, 'refresh'):
            self.refresh()


    def refresh(self):
        search = self.search_edit.text().strip() or None
        offset = self.current_page * self.page_size
        try:
            customers, self.total_count = entity_service.customers(search=search, limit=self.page_size, offset=offset)
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(tr('customers')), 'warning', self)
                return
            raise
        display_curr = currency.get_display_currency()
        data = []
        for c in customers:
            balance_display = currency.convert(Decimal(str(c.get('balance', 0))), currency.storage_currency(), display_curr)
            # تطبيق فلتر الرصيد (جانب العميل)
            filter_idx = self.balance_filter.currentIndex()
            if filter_idx == 1 and balance_display <= 0:
                continue
            if filter_idx == 2 and balance_display >= 0:
                continue
            if filter_idx == 3 and balance_display != 0:
                continue
            data.append({
                'id': c['id'],
                'name': c.get('name', ''),
                'phone': c.get('phone', ''),
                'address': c.get('address', ''),
                'balance': currency.format_amount(balance_display)
            })
        headers = ['name', 'phone', 'address', 'balance']
        display_headers = [tr('name'), tr('phone'), tr('address'), tr('balance')]
        self.model = GenericTableModel(data, display_headers, key_fields=['id'], data_keys=headers)
        self.table.setModel(self.model)
        # id محفوظ داخلياً عبر key_fields ولا يوجد كعمود عرض؛ لا نخفي العمود الأول الحقيقي.
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.refresh_style()
        self._connect_selection_preview()

        total_pages = (self.total_count + self.page_size - 1) // self.page_size
        self.page_label.setText(tr("page_of", page=self.current_page + 1, pages=total_pages))
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page + 1 < total_pages)

    def _connect_selection_preview(self):
        sm = self.table.selectionModel() if self.table else None
        if sm is None:
            return
        try:
            sm.selectionChanged.disconnect(self._update_detail_preview)
        except Exception:
            pass
        sm.selectionChanged.connect(self._update_detail_preview)
        self._update_detail_preview()

    def _update_detail_preview(self, *args):
        sm = self.table.selectionModel() if self.table else None
        if sm is None or not sm.selectedRows() or not self.model:
            self.detail_panel.clear_summary()
            return
        row = self.table.current_source_row() if hasattr(self.table, 'current_source_row') else sm.selectedRows()[0].row()
        data = self.model.get_row(row) if hasattr(self.model, 'get_row') else {}
        self.detail_panel.set_summary(data.get('name', tr('customer')), [
            f"{tr('phone')}: {data.get('phone', '')}",
            f"{tr('address')}: {data.get('address', '')}",
            f"{tr('balance')}: {data.get('balance', '')}",
            tr('double_click_to_open_document') if tr('double_click_to_open_document') != 'double_click_to_open_document' else 'انقر مرتين لفتح تبويب المستند',
        ])

    def _main_window(self):
        widget = self
        while widget is not None:
            if hasattr(widget, 'open_party_document'):
                return widget
            widget = widget.parent()
        return None

    def add_customer(self):
        main = self._main_window()
        if main is not None:
            tab = main.open_party_document('customer')
            if hasattr(tab, 'saved'):
                tab.saved.connect(lambda *_: self.refresh())
            return
        # AddEntityDialog is retained only as an emergency fallback when this
        # list is embedded outside MainWindow/TabbedWorkspace. The official
        # route remains main.open_party_document('customer').
        dialog = AddEntityDialog(self, 'sale')
        if dialog.exec_():
            self.refresh()
            return
        show_toast(tr('party_document_unavailable') if tr('party_document_unavailable') != 'party_document_unavailable' else 'تعذر فتح تبويب العميل', 'error', self)

    def edit_customer(self, index):
        row = self.table.current_source_row() if hasattr(self.table, 'current_source_row') else index.row()
        cust_id = self.model.get_id(row)
        if not cust_id:
            return
        main = self._main_window()
        if main is not None:
            tab = main.open_party_document('customer', party_id=cust_id)
            if hasattr(tab, 'saved'):
                tab.saved.connect(lambda *_: self.refresh())
            return
        main = self._main_window()
        if main is not None:
            return main.open_party_document('customer', cust_id)
        show_toast(tr('party_document_unavailable') if tr('party_document_unavailable') != 'party_document_unavailable' else 'تعذر فتح تبويب العميل', 'error', self)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh()

    def next_page(self):
        self.current_page += 1
        self.refresh()



# Phase110 offline guard markers: العملاء
