# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
                             QComboBox, QLabel, QHeaderView, QMessageBox, QMenu, QStackedWidget)
from core.services.voucher_service import voucher_service
from core.services.finance_operation_policy import finance_operation_policy
from currency import currency
from ui.smart_table_view import SmartTableView
from models.table_models import GenericTableModel
from utils import show_toast
from offline_read import is_offline_read_error, notify_offline_read
from views.widgets.modern_ui import apply_modern_widget
from i18n import translate as tr, qt_layout_direction
from ui.components.responsive_master_detail import DetailPlaceholder, ResponsiveMasterDetail
from workspace.lists.list_workspace_contract import bind_list_workspace


def _tr(key: str, fallback: str) -> str:
    value = tr(key)
    return fallback if value == key else value


class VouchersWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        bind_list_workspace(self, 'vouchers')
        self.setLayoutDirection(qt_layout_direction())
        self.current_page = 0
        self.page_size = 50
        self.total_count = 0
        self._inline_editor = None

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
        self.add_menu = QMenu(self.add_btn)
        self.add_receipt_action = self.add_menu.addAction(tr('receipt_voucher'))
        self.add_payment_action = self.add_menu.addAction(tr('payment_voucher'))
        self.add_expense_action = self.add_menu.addAction(_tr('expense_voucher', 'سند مصروف'))
        self.add_receipt_action.triggered.connect(lambda: self.add_voucher('receipt'))
        self.add_payment_action.triggered.connect(lambda: self.add_voucher('payment'))
        self.add_expense_action.triggered.connect(lambda: self.add_voucher('expense'))
        self.add_btn.setMenu(self.add_menu)
        top_layout.addWidget(self.add_btn)

        self.delete_btn = QPushButton(tr("delete_voucher"))
        self.delete_btn.setObjectName("danger")
        self.delete_btn.clicked.connect(self.delete_selected_voucher)
        top_layout.addWidget(self.delete_btn)

        self.print_btn = QPushButton(tr("print_button"))
        self.print_btn.clicked.connect(lambda: self.print_selected('print'))
        top_layout.addWidget(self.print_btn)

        layout.addLayout(top_layout)

        # Phase376: السندات تستخدم نفس هيكلية العملاء/الموردين: Master-Detail داخل نفس التبويب.
        self.table = SmartTableView(identity="vouchers.list")
        self.table.setSelectionBehavior(SmartTableView.SelectRows)
        self.table.doubleClicked.connect(self.edit_voucher)

        self.detail_panel = DetailPlaceholder(_tr('voucher_details', 'تفاصيل السند'))
        self.detail_stack = QStackedWidget(self)
        self.detail_stack.addWidget(self.detail_panel)

        self.inline_editor_page = QWidget(self)
        inline_layout = QVBoxLayout(self.inline_editor_page)
        inline_layout.setContentsMargins(0, 0, 0, 0)
        inline_layout.setSpacing(8)
        inline_header = QHBoxLayout()
        self.inline_title_label = QLabel('', self.inline_editor_page)
        self.inline_title_label.setObjectName('InlineEditorTitle')
        self.inline_back_btn = QPushButton(tr('back') if tr('back') != 'back' else 'عودة', self.inline_editor_page)
        self.inline_back_btn.clicked.connect(self._close_inline_editor)
        inline_header.addWidget(self.inline_title_label, 1)
        inline_header.addWidget(self.inline_back_btn)
        inline_layout.addLayout(inline_header)
        self.inline_editor_host = QWidget(self.inline_editor_page)
        self.inline_editor_host_layout = QVBoxLayout(self.inline_editor_host)
        self.inline_editor_host_layout.setContentsMargins(0, 0, 0, 0)
        self.inline_editor_host_layout.setSpacing(0)
        inline_layout.addWidget(self.inline_editor_host, 1)
        self.detail_stack.addWidget(self.inline_editor_page)

        self.master_detail = ResponsiveMasterDetail(self.table, self.detail_stack, self)
        layout.addWidget(self.master_detail, 1)

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
        can_create = finance_operation_policy.can(finance_operation_policy.OP_VOUCHER_CREATE)
        self.add_btn.setEnabled(can_create)
        for action in (self.add_receipt_action, self.add_payment_action, self.add_expense_action):
            action.setEnabled(can_create)
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
                'raw_type': v.get('type') or '',
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
        if sm is None or not sm.selectedRows() or not getattr(self, 'model', None):
            self.detail_panel.clear_summary()
            return
        row = self.table.current_source_row() if hasattr(self.table, 'current_source_row') else sm.selectedRows()[0].row()
        data = self.model.get_row(row) if hasattr(self.model, 'get_row') else {}
        title = f"{data.get('type', tr('voucher'))} #{data.get('id', '')}".strip()
        self.detail_panel.set_summary(title, [
            f"{tr('date')}: {data.get('date', '')}",
            f"{tr('party')}: {data.get('party', '')}",
            f"{tr('amount')}: {data.get('amount', '')}",
            f"{tr('account')}: {data.get('account', '')}",
            f"{tr('description')}: {data.get('description', '')}",
            tr('double_click_to_open_document') if tr('double_click_to_open_document') != 'double_click_to_open_document' else 'انقر مرتين لفتح محرر السند داخل نفس التبويب',
        ])

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

    def _clear_inline_editor(self):
        editor = getattr(self, '_inline_editor', None)
        if editor is None:
            return
        try:
            self.inline_editor_host_layout.removeWidget(editor)
        except Exception:
            pass
        editor.setParent(None)
        editor.deleteLater()
        self._inline_editor = None

    def _close_inline_editor(self, *args, force: bool = False):
        editor = getattr(self, '_inline_editor', None)
        if editor is not None and not force and hasattr(editor, 'can_close'):
            if not editor.can_close():
                return False
        self._clear_inline_editor()
        self.detail_stack.setCurrentWidget(self.detail_panel)
        self._update_detail_preview()
        return True

    def _after_inline_voucher_saved(self, saved_id=None):
        self.refresh()
        self._close_inline_editor(force=True)

    def _show_inline_voucher_editor(self, voucher_type='receipt', voucher=None):
        # Phase376: سند قبض/سند دفع/سند مصروف open in the detail panel, like customers/suppliers.
        # Compatibility marker only: main.open_quick_voucher was the legacy tab route.
        if getattr(self, '_inline_editor', None) is not None:
            if not self._close_inline_editor():
                return None
        try:
            voucher_type = voucher_type or (voucher.get('type') if isinstance(voucher, dict) else 'receipt') or 'receipt'
            if voucher_type == 'expense':
                from features.finance.documents import ExpenseDocumentTab
                editor = ExpenseDocumentTab(self.inline_editor_host, expense=voucher if isinstance(voucher, dict) else None)
            else:
                from features.vouchers import VoucherEditorTab
                editor = VoucherEditorTab(self.inline_editor_host, voucher=voucher if isinstance(voucher, dict) else None, voucher_type=voucher_type)
            editor.saved.connect(self._after_inline_voucher_saved)
            try:
                editor.titleChanged.connect(self.inline_title_label.setText)
            except Exception:
                pass
            self.inline_title_label.setText(editor.windowTitle() or _tr('new_voucher', 'سند جديد'))
            self.inline_editor_host_layout.addWidget(editor)
            self._inline_editor = editor
            self.detail_stack.setCurrentWidget(self.inline_editor_page)
            return editor
        except Exception as exc:
            show_toast(str(exc), 'error', self)
            return None

    def add_voucher(self, voucher_type='receipt'):
        try:
            finance_operation_policy.require(finance_operation_policy.OP_VOUCHER_CREATE, context='voucher:widget:add', payload={'type': voucher_type})
        except PermissionError as exc:
            show_toast(tr(str(exc)) if str(exc) else tr('permission_denied'), 'error', self)
            return
        if self._show_inline_voucher_editor(voucher_type=voucher_type) is None:
            show_toast(tr('cannot_open_document_tab'), 'error', self)

    def edit_voucher(self, index):
        row = self.table.current_source_row() if hasattr(self.table, 'current_source_row') else index.row()
        if row is None:
            row = index.row()
        vid = self.model.get_id(row)
        if vid:
            voucher = voucher_service.get(vid)
            if voucher:
                if self._show_inline_voucher_editor(voucher_type=voucher.get('type') or 'receipt', voucher=voucher) is None:
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
