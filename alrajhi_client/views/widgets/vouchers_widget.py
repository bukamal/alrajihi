# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
                             QComboBox, QLabel, QHeaderView, QMessageBox, QMenu)
from core.services.voucher_service import voucher_service
from core.services.finance_operation_policy import finance_operation_policy
from currency import currency
from ui.smart_table_view import SmartTableView
from models.table_models import GenericTableModel
from utils import show_toast
from offline_read import is_offline_read_error, notify_offline_read
from views.widgets.modern_ui import apply_modern_widget
from i18n import translate as tr, qt_layout_direction
from workspace.lists.list_workspace_contract import bind_list_workspace

class VouchersWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        bind_list_workspace(self, 'vouchers')
        self.setLayoutDirection(qt_layout_direction())
        self.current_page = 0
        self.page_size = 50
        self.total_count = 0

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        top_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(tr("search_voucher"))
        self.search_edit.textChanged.connect(self.refresh)
        top_layout.addWidget(self.search_edit)

        self.type_filter = QComboBox()
        
        self.type_filter.addItem(tr("all"), "all")
        self.type_filter.addItem(tr("receipt"), "receipt")
        self.type_filter.addItem(tr("payment"), "payment")
        self.type_filter.addItem(tr("expense"), "expense")
        self.type_filter.currentIndexChanged.connect(self.refresh)
        top_layout.addWidget(QLabel(tr("type") + ":"))
        top_layout.addWidget(self.type_filter)

        self.add_btn = QPushButton(tr("add_voucher"))
        self.add_btn.setObjectName("primary")
        self.add_btn.clicked.connect(self.add_voucher)
        top_layout.addWidget(self.add_btn)

        self.delete_btn = QPushButton(tr("delete_voucher"))
        self.delete_btn.setObjectName("danger")
        self.delete_btn.clicked.connect(self.delete_selected_voucher)
        top_layout.addWidget(self.delete_btn)

        self.print_btn = QPushButton(tr("print_button"))
        self.print_btn.clicked.connect(lambda: self.print_selected('print'))
        top_layout.addWidget(self.print_btn)

        layout.addLayout(top_layout)

        self.table = SmartTableView(identity="vouchers.list")
        self.table.setSelectionBehavior(SmartTableView.SelectRows)
        self.table.doubleClicked.connect(self.edit_voucher)
        layout.addWidget(self.table)

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

        apply_modern_widget(self, tr('vouchers_title'), tr('vouchers_subtitle'))
        self._apply_operation_state()
        self.refresh()


    def _apply_operation_state(self):
        self.add_btn.setEnabled(finance_operation_policy.can(finance_operation_policy.OP_VOUCHER_CREATE))
        self.delete_btn.setEnabled(finance_operation_policy.can(finance_operation_policy.OP_VOUCHER_DELETE))
        self.print_btn.setEnabled(finance_operation_policy.can(finance_operation_policy.OP_VOUCHER_PRINT))

    def set_global_filter(self, text: str):
        text = text or ''
        field = getattr(self, 'search_edit', None)
        if field is not None and field.text() != text:
            field.setText(text)
        elif hasattr(self, 'refresh'):
            self.refresh()


    def refresh(self):
        filter_type = self.type_filter.currentData() or "all"
        vtype = None
        if filter_type == "receipt":
            vtype = 'receipt'
        elif filter_type == "payment":
            vtype = 'payment'
        elif filter_type == "expense":
            vtype = 'expense'
        search = self.search_edit.text().strip().lower() or None
        offset = self.current_page * self.page_size
        try:
            vouchers, self.total_count = voucher_service.list_vouchers(search=search, vtype=vtype, limit=self.page_size, offset=offset)
        except Exception as exc:
            if is_offline_read_error(exc):
                notify_offline_read(self, tr('vouchers_title'))
                return
            raise

        data = []
        for v in vouchers:
            type_text = tr("receipt") if v['type'] == 'receipt' else tr("payment") if v['type'] == 'payment' else tr("expense")
            party = voucher_service.party_name(v)
            data.append({
                'id': v['id'],
                'date': v['date'],
                'type': type_text,
                'party': party,
                'amount': currency.format_base_amount(v.get('amount') or 0),
                'account': v.get('cashbox_name') or v.get('bank_name') or '',
                'description': v.get('description', '')
            })
        headers = ['date', 'type', 'party', 'amount', 'account', 'description']
        display_headers = [tr('date'), tr('type'), tr('party'), tr('amount'), tr('account'), tr('description')]
        self.model = GenericTableModel(data, display_headers, key_fields=['id'], data_keys=headers)
        self.table.setModel(self.model)
        # id محفوظ داخلياً عبر key_fields ولا يوجد كعمود عرض؛ لا نخفي العمود الأول الحقيقي.
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.refresh_style()

        total_pages = (self.total_count + self.page_size - 1) // self.page_size
        self.page_label.setText(tr("page_of", page=self.current_page + 1, pages=total_pages))
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page + 1 < total_pages)

    def _selected_id(self):
        if not hasattr(self, 'model'):
            return None
        row = self.table.current_source_row() if hasattr(self.table, 'current_source_row') else None
        if row is None:
            rows = self.table.selectionModel().selectedRows() if self.table.selectionModel() else []
            row = rows[0].row() if rows else None
        if row is None:
            return None
        return self.model.get_id(row)

    def delete_selected_voucher(self):
        try:
            finance_operation_policy.require(finance_operation_policy.OP_VOUCHER_DELETE, context='voucher:widget:delete')
        except PermissionError as exc:
            show_toast(tr(str(exc)) if str(exc) else tr('permission_denied'), 'error', self)
            return
        vid = self._selected_id()
        if not vid:
            QMessageBox.information(self, tr("delete_voucher"), tr("select_voucher_first"))
            return
        voucher = voucher_service.get(vid)
        if not voucher:
            QMessageBox.warning(self, tr("delete_voucher"), tr("voucher_load_failed"))
            return
        amount = voucher.get('amount') or ''
        reply = QMessageBox.question(
            self,
            tr("delete_voucher"),
            tr("delete_voucher_confirm", id=vid, amount=amount),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            voucher_service.delete(vid)
            show_toast(tr("voucher_deleted"), "success", self)
            self.refresh()
        except Exception as exc:
            show_toast(str(exc), "error", self)

    def print_selected(self, mode='preview'):
        try:
            finance_operation_policy.require(finance_operation_policy.OP_VOUCHER_PRINT, context='voucher:widget:print', payload={'mode': mode})
        except PermissionError as exc:
            show_toast(tr(str(exc)) if str(exc) else tr('permission_denied'), 'error', self)
            return
        vid = self._selected_id()
        if not vid:
            QMessageBox.information(self, tr("print_button"), tr("select_voucher_first"))
            return
        voucher = voucher_service.get(vid)
        if not voucher:
            QMessageBox.warning(self, tr("print_button"), tr("voucher_load_failed"))
            return
        voucher = dict(voucher)
        voucher['party_name'] = voucher_service.party_name(voucher)
        from printing.printing_service import printing_service
        printing_service.voucher_print(voucher, self)

    def add_voucher(self):
        try:
            finance_operation_policy.require(finance_operation_policy.OP_VOUCHER_CREATE, context='voucher:widget:add')
        except PermissionError as exc:
            show_toast(tr(str(exc)) if str(exc) else tr('permission_denied'), 'error', self)
            return
        main = self.window()
        if hasattr(main, 'open_quick_voucher'):
            tab = main.open_quick_voucher('receipt')
            if tab and hasattr(tab, 'saved'):
                tab.saved.connect(lambda *_: self.refresh())
            return
        show_toast(tr('cannot_open_document_tab'), 'error', self)

    def edit_voucher(self, index):
        row = self.table.current_source_row() if hasattr(self.table, 'current_source_row') else index.row()
        if row is None:
            row = index.row()
        vid = self.model.get_id(row)
        if vid:
            voucher = voucher_service.get(vid)
            if voucher:
                main = self.window()
                if hasattr(main, 'open_quick_voucher'):
                    tab = main.open_quick_voucher(voucher_type=voucher.get('type') or 'receipt', voucher=voucher)
                    if tab and hasattr(tab, 'saved'):
                        tab.saved.connect(lambda *_: self.refresh())
                    return
                show_toast(tr('cannot_open_document_tab'), 'error', self)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh()

    def next_page(self):
        self.current_page += 1
        self.refresh()


# Phase110 offline guard markers: السندات

# Phase110 stable offline UI markers:
# notify_offline_read(self, 'السندات')
