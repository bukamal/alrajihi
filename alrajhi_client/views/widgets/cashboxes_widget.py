# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTabWidget, QMessageBox, QHeaderView, QTableView, QStackedWidget
)

from core.services.cashbox_service import cashbox_service
from core.services.settings_service import settings_service
from core.services.finance_operation_policy import finance_operation_policy
from currency import currency
from models.table_models import GenericTableModel
from ui.smart_table_view import SmartTableView
from utils import show_toast
from core.offline_guard import is_offline_read_error, offline_read_message
from views.widgets.modern_ui import apply_modern_widget
from i18n import translate as tr, qt_layout_direction
from ui.components.responsive_master_detail import DetailPlaceholder, ResponsiveMasterDetail


class CashboxesWidget(QWidget):
    """Cashbox and bank workspace using inline master-detail editors."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(qt_layout_direction())
        self._cash_inline_editor = None
        self._bank_inline_editor = None
        self._setup_ui()
        self._apply_finance_policy()
        apply_modern_widget(self, tr('finance_cashbanks_title'), tr('finance_cashbanks_subtitle'))
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel(tr('finance_cashbanks_title'))
        title.setObjectName('sectionTitle')
        layout.addWidget(title)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)
        self.cash_tab = QWidget()
        self.bank_tab = QWidget()
        self.shift_tab = QWidget()
        self.mov_tab = QWidget()
        self.tabs.addTab(self.cash_tab, tr('cashboxes'))
        self.tabs.addTab(self.bank_tab, tr('bank_accounts'))
        self.tabs.addTab(self.shift_tab, tr('pos_shifts'))
        self.tabs.addTab(self.mov_tab, tr('financial_movements'))
        self._cash_ui()
        self._bank_ui()
        self._shift_ui()
        self._mov_ui()
        self._apply_shift_tab_visibility()

    def _apply_shift_tab_visibility(self):
        try:
            if not settings_service.pos_shifts_enabled():
                idx = self.tabs.indexOf(self.shift_tab)
                if idx >= 0:
                    self.tabs.removeTab(idx)
        except Exception:
            pass

    def _cash_ui(self):
        layout = QVBoxLayout(self.cash_tab)
        bar = QHBoxLayout()
        self.cash_search = QLineEdit()
        self.cash_search.setPlaceholderText(tr('search_cashboxes'))
        self.cash_search.textChanged.connect(self.refresh_cashboxes)
        self.add_cashbox_btn = QPushButton(tr('add_cashbox'))
        self.add_cashbox_btn.setObjectName('primary')
        self.add_cashbox_btn.clicked.connect(self.add_cashbox)
        self.edit_cashbox_btn = QPushButton(tr('edit'))
        self.edit_cashbox_btn.clicked.connect(self.edit_cashbox)
        self.archive_cashbox_btn = QPushButton(tr('archive'))
        self.archive_cashbox_btn.clicked.connect(self.archive_cashbox)
        bar.addWidget(self.cash_search, 1)
        bar.addWidget(self.add_cashbox_btn)
        bar.addWidget(self.edit_cashbox_btn)
        bar.addWidget(self.archive_cashbox_btn)
        layout.addLayout(bar)

        self.cash_table = SmartTableView(identity='cashboxes.cashboxes')
        self.cash_table.setSelectionBehavior(QTableView.SelectRows)
        self.cash_table.doubleClicked.connect(lambda _idx: self.edit_cashbox())
        self.cash_detail_panel = DetailPlaceholder(tr('cashbox'))
        self.cash_detail_stack = QStackedWidget(self.cash_tab)
        self.cash_detail_stack.addWidget(self.cash_detail_panel)
        self.cash_inline_page, self.cash_inline_title_label, self.cash_inline_back_btn, self.cash_inline_host, self.cash_inline_host_layout = self._build_inline_page(
            self.cash_tab, self._close_cashbox_inline_editor
        )
        self.cash_detail_stack.addWidget(self.cash_inline_page)
        self.cash_master_detail = ResponsiveMasterDetail(self.cash_table, self.cash_detail_stack, self.cash_tab)
        layout.addWidget(self.cash_master_detail, 1)

    def _bank_ui(self):
        layout = QVBoxLayout(self.bank_tab)
        bar = QHBoxLayout()
        self.bank_search = QLineEdit()
        self.bank_search.setPlaceholderText(tr('search_banks'))
        self.bank_search.textChanged.connect(self.refresh_banks)
        self.add_bank_btn = QPushButton(tr('add_bank_account'))
        self.add_bank_btn.setObjectName('primary')
        self.add_bank_btn.clicked.connect(self.add_bank)
        self.edit_bank_btn = QPushButton(tr('edit'))
        self.edit_bank_btn.clicked.connect(self.edit_bank)
        self.archive_bank_btn = QPushButton(tr('archive'))
        self.archive_bank_btn.clicked.connect(self.archive_bank)
        bar.addWidget(self.bank_search, 1)
        bar.addWidget(self.add_bank_btn)
        bar.addWidget(self.edit_bank_btn)
        bar.addWidget(self.archive_bank_btn)
        layout.addLayout(bar)

        self.bank_table = SmartTableView(identity='cashboxes.banks')
        self.bank_table.setSelectionBehavior(QTableView.SelectRows)
        self.bank_table.doubleClicked.connect(lambda _idx: self.edit_bank())
        self.bank_detail_panel = DetailPlaceholder(tr('bank_account'))
        self.bank_detail_stack = QStackedWidget(self.bank_tab)
        self.bank_detail_stack.addWidget(self.bank_detail_panel)
        self.bank_inline_page, self.bank_inline_title_label, self.bank_inline_back_btn, self.bank_inline_host, self.bank_inline_host_layout = self._build_inline_page(
            self.bank_tab, self._close_bank_inline_editor
        )
        self.bank_detail_stack.addWidget(self.bank_inline_page)
        self.bank_master_detail = ResponsiveMasterDetail(self.bank_table, self.bank_detail_stack, self.bank_tab)
        layout.addWidget(self.bank_master_detail, 1)

    def _build_inline_page(self, parent, back_callback):
        page = QWidget(parent)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        header = QHBoxLayout()
        title = QLabel('', page)
        title.setObjectName('InlineEditorTitle')
        back = QPushButton(tr('back') if tr('back') != 'back' else 'عودة', page)
        back.clicked.connect(back_callback)
        header.addWidget(title, 1)
        header.addWidget(back)
        layout.addLayout(header)
        host = QWidget(page)
        host_layout = QVBoxLayout(host)
        host_layout.setContentsMargins(0, 0, 0, 0)
        host_layout.setSpacing(0)
        layout.addWidget(host, 1)
        return page, title, back, host, host_layout

    def _shift_ui(self):
        layout = QVBoxLayout(self.shift_tab)
        bar = QHBoxLayout()
        refresh = QPushButton(tr('refresh'))
        refresh.clicked.connect(self.refresh_shifts)
        bar.addStretch()
        bar.addWidget(refresh)
        layout.addLayout(bar)
        self.shift_table = SmartTableView(identity='cashboxes.shifts')
        self.shift_table.setSelectionBehavior(QTableView.SelectRows)
        layout.addWidget(self.shift_table)

    def _mov_ui(self):
        layout = QVBoxLayout(self.mov_tab)
        bar = QHBoxLayout()
        refresh = QPushButton(tr('refresh'))
        refresh.clicked.connect(self.refresh_movements)
        bar.addStretch()
        bar.addWidget(refresh)
        layout.addLayout(bar)
        self.mov_table = SmartTableView(identity='cashboxes.movements')
        self.mov_table.setSelectionBehavior(QTableView.SelectRows)
        layout.addWidget(self.mov_table)

    def set_global_filter(self, text: str):
        text = (text or '').strip().lower()
        for table in (getattr(self, 'cash_table', None), getattr(self, 'bank_table', None), getattr(self, 'shift_table', None), getattr(self, 'mov_table', None)):
            if table is not None and hasattr(table, 'set_local_filter'):
                table.set_local_filter(text)

    def _apply_finance_policy(self):
        checks = [
            ('add_cashbox_btn', finance_operation_policy.OP_CASHBOX_CREATE),
            ('edit_cashbox_btn', finance_operation_policy.OP_CASHBOX_EDIT),
            ('archive_cashbox_btn', finance_operation_policy.OP_CASHBOX_ARCHIVE),
            ('add_bank_btn', finance_operation_policy.OP_BANK_CREATE),
            ('edit_bank_btn', finance_operation_policy.OP_BANK_EDIT),
            ('archive_bank_btn', finance_operation_policy.OP_BANK_ARCHIVE),
        ]
        for attr, op in checks:
            btn = getattr(self, attr, None)
            if btn is not None:
                try:
                    btn.setEnabled(finance_operation_policy.can(op))
                except Exception:
                    pass

    def _require_finance_operation(self, operation):
        try:
            finance_operation_policy.require(operation, context='CashboxesWidget')
            return True
        except Exception as exc:
            QMessageBox.warning(self, tr('error'), str(exc))
            return False

    def refresh(self):
        try:
            cashbox_service.bootstrap()
            self.refresh_cashboxes()
            self.refresh_banks()
            if settings_service.pos_shifts_enabled():
                self.refresh_shifts()
            self.refresh_movements()
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(tr('finance_cashbanks_title')), 'warning', self)
                return
            raise
        self._apply_finance_policy()

    def refresh_cashboxes(self):
        text = self.cash_search.text().strip().lower() if hasattr(self, 'cash_search') else ''
        rows = []
        try:
            cashboxes = cashbox_service.cashboxes(True)
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(tr('cashboxes')), 'warning', self)
                return
            raise
        for c in cashboxes:
            if text and text not in str(c.get('name', '')).lower() and text not in str(c.get('code', '')).lower():
                continue
            bal = currency.format_amount(currency.to_display(Decimal(str(c.get('balance') or 0))))
            rows.append({
                'id': c.get('id'),
                'branch': c.get('branch_name', ''),
                'name': c.get('name', ''),
                'code': c.get('code') or '—',
                'balance': bal,
                'default': tr('yes') if int(c.get('is_default') or 0) == 1 else tr('no'),
                'status': tr('archived') if c.get('deleted_at') or int(c.get('is_active') or 0) == 0 else tr('active_status'),
            })
        self.cash_model = GenericTableModel(rows, [tr('branch'), tr('cashbox'), tr('code'), tr('balance'), tr('default'), tr('status')], key_fields=['id'], data_keys=['branch', 'name', 'code', 'balance', 'default', 'status'])
        self.cash_table.setModel(self.cash_model)
        self.cash_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self._connect_cash_preview()

    def refresh_banks(self):
        text = self.bank_search.text().strip().lower() if hasattr(self, 'bank_search') else ''
        rows = []
        try:
            bank_accounts = cashbox_service.bank_accounts(True)
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(tr('bank_accounts')), 'warning', self)
                return
            raise
        for b in bank_accounts:
            if text and text not in str(b.get('bank_name', '')).lower() and text not in str(b.get('account_name', '')).lower():
                continue
            bal = currency.format_amount(currency.to_display(Decimal(str(b.get('balance') or 0))))
            rows.append({
                'id': b.get('id'),
                'branch': b.get('branch_name', ''),
                'bank': b.get('bank_name', ''),
                'account': b.get('account_name') or '—',
                'number': b.get('account_number') or '—',
                'balance': bal,
                'status': tr('archived') if b.get('deleted_at') or int(b.get('is_active') or 0) == 0 else tr('active_status'),
            })
        self.bank_model = GenericTableModel(rows, [tr('branch'), tr('bank'), tr('account'), tr('account_number'), tr('balance'), tr('status')], key_fields=['id'], data_keys=['branch', 'bank', 'account', 'number', 'balance', 'status'])
        self.bank_table.setModel(self.bank_model)
        self.bank_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self._connect_bank_preview()

    def refresh_shifts(self):
        rows = []
        try:
            shifts = cashbox_service.shifts(limit=200)
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(tr('pos_shifts')), 'warning', self)
                return
            raise
        for sh in shifts:
            diff = currency.format_amount(currency.to_display(Decimal(str(sh.get('difference_amount') or 0)))) if sh.get('difference_amount') not in (None, '') else '—'
            rows.append({'id': sh.get('id'), 'branch': sh.get('branch_name', ''), 'cashbox': sh.get('cashbox_name', ''), 'opened': sh.get('opened_at', ''), 'closed': sh.get('closed_at') or '—', 'status': tr('open_status') if sh.get('status') == 'open' else tr('closed_status'), 'sales': currency.format_amount(currency.to_display(Decimal(str(sh.get('total_sales') or 0)))), 'diff': diff})
        self.shift_model = GenericTableModel(rows, [tr('line_no'), tr('branch'), tr('cashbox'), tr('open_time'), tr('close_time'), tr('status'), tr('sales_total'), tr('difference')], data_keys=['id', 'branch', 'cashbox', 'opened', 'closed', 'status', 'sales', 'diff'])
        self.shift_table.setModel(self.shift_model)
        self.shift_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

    def refresh_movements(self):
        rows = []
        try:
            movements = cashbox_service.movements(limit=300)
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(tr('financial_movements')), 'warning', self)
                return
            raise
        for m in movements:
            amount = currency.format_amount(currency.to_display(Decimal(str(m.get('amount') or 0))))
            account = m.get('cashbox_name') or f"{m.get('bank_name') or ''} {m.get('account_name') or ''}".strip()
            rows.append({'date': m.get('movement_date', ''), 'branch': m.get('branch_name', ''), 'account': account, 'type': m.get('movement_type', ''), 'amount': amount, 'ref': f"{m.get('reference_type') or ''} #{m.get('reference_id') or ''}", 'desc': m.get('description', '')})
        self.mov_model = GenericTableModel(rows, [tr('date'), tr('branch'), tr('account'), tr('type'), tr('amount'), tr('reference'), tr('description')], data_keys=['date', 'branch', 'account', 'type', 'amount', 'ref', 'desc'])
        self.mov_table.setModel(self.mov_model)
        self.mov_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

    def _selected(self, table, model_attr):
        model = getattr(self, model_attr, None)
        if not model:
            return None
        row = table.current_source_row() if hasattr(table, 'current_source_row') else None
        if row is None:
            rows = table.selectionModel().selectedRows() if table.selectionModel() else []
            row = rows[0].row() if rows else None
        return model.get_id(row) if row is not None else None

    def _connect_cash_preview(self):
        sm = self.cash_table.selectionModel() if self.cash_table else None
        if sm is None:
            return
        try:
            sm.selectionChanged.disconnect(self._update_cash_preview)
        except Exception:
            pass
        sm.selectionChanged.connect(self._update_cash_preview)
        self._update_cash_preview()

    def _connect_bank_preview(self):
        sm = self.bank_table.selectionModel() if self.bank_table else None
        if sm is None:
            return
        try:
            sm.selectionChanged.disconnect(self._update_bank_preview)
        except Exception:
            pass
        sm.selectionChanged.connect(self._update_bank_preview)
        self._update_bank_preview()

    def _update_cash_preview(self, *args):
        data = self._selected_row_data(self.cash_table, 'cash_model')
        if not data:
            self.cash_detail_panel.clear_summary()
            return
        self.cash_detail_panel.set_summary(str(data.get('name') or tr('cashbox')), [
            f"{tr('branch')}: {data.get('branch', '')}",
            f"{tr('code')}: {data.get('code', '')}",
            f"{tr('balance')}: {data.get('balance', '')}",
            f"{tr('status')}: {data.get('status', '')}",
            tr('double_click_to_open_document') if tr('double_click_to_open_document') != 'double_click_to_open_document' else 'انقر مرتين للتحرير داخل نفس التبويب',
        ])

    def _update_bank_preview(self, *args):
        data = self._selected_row_data(self.bank_table, 'bank_model')
        if not data:
            self.bank_detail_panel.clear_summary()
            return
        self.bank_detail_panel.set_summary(str(data.get('bank') or tr('bank_account')), [
            f"{tr('branch')}: {data.get('branch', '')}",
            f"{tr('account')}: {data.get('account', '')}",
            f"{tr('account_number')}: {data.get('number', '')}",
            f"{tr('balance')}: {data.get('balance', '')}",
            f"{tr('status')}: {data.get('status', '')}",
            tr('double_click_to_open_document') if tr('double_click_to_open_document') != 'double_click_to_open_document' else 'انقر مرتين للتحرير داخل نفس التبويب',
        ])

    def _selected_row_data(self, table, model_attr):
        model = getattr(self, model_attr, None)
        if model is None:
            return {}
        row = table.current_source_row() if hasattr(table, 'current_source_row') else None
        if row is None:
            rows = table.selectionModel().selectedRows() if table.selectionModel() else []
            row = rows[0].row() if rows else None
        if row is None:
            return {}
        try:
            return model.get_row(row)
        except Exception:
            return {}

    def _wire_inline_close(self, editor, close_callback):
        for attr in ('bottom_close_btn', 'close_btn', 'cancel_btn'):
            btn = getattr(editor, attr, None)
            if btn is None or not hasattr(btn, 'clicked'):
                continue
            try:
                btn.clicked.disconnect()
            except Exception:
                pass
            btn.clicked.connect(close_callback)

    def _clear_cashbox_inline_editor(self):
        editor = getattr(self, '_cash_inline_editor', None)
        if editor is None:
            return
        try:
            self.cash_inline_host_layout.removeWidget(editor)
        except Exception:
            pass
        editor.setParent(None)
        editor.deleteLater()
        self._cash_inline_editor = None

    def _close_cashbox_inline_editor(self, *args, force=False):
        editor = getattr(self, '_cash_inline_editor', None)
        if editor is not None and not force and hasattr(editor, 'can_close') and not editor.can_close():
            return False
        self._clear_cashbox_inline_editor()
        self.cash_detail_stack.setCurrentWidget(self.cash_detail_panel)
        self._update_cash_preview()
        return True

    def _clear_bank_inline_editor(self):
        editor = getattr(self, '_bank_inline_editor', None)
        if editor is None:
            return
        try:
            self.bank_inline_host_layout.removeWidget(editor)
        except Exception:
            pass
        editor.setParent(None)
        editor.deleteLater()
        self._bank_inline_editor = None

    def _close_bank_inline_editor(self, *args, force=False):
        editor = getattr(self, '_bank_inline_editor', None)
        if editor is not None and not force and hasattr(editor, 'can_close') and not editor.can_close():
            return False
        self._clear_bank_inline_editor()
        self.bank_detail_stack.setCurrentWidget(self.bank_detail_panel)
        self._update_bank_preview()
        return True

    def _after_cashbox_saved(self, saved_id=None):
        self.refresh()
        self._close_cashbox_inline_editor(force=True)

    def _after_bank_saved(self, saved_id=None):
        self.refresh()
        self._close_bank_inline_editor(force=True)

    def open_cashbox_inline(self, cashbox_id=None):
        if getattr(self, '_cash_inline_editor', None) is not None and not self._close_cashbox_inline_editor():
            return None
        try:
            from features.finance import CashboxDocumentTab
            editor = CashboxDocumentTab(self.cash_inline_host, cashbox_id=cashbox_id)
            editor.setProperty('inlineEditor', True)
            self._wire_inline_close(editor, self._close_cashbox_inline_editor)
            editor.saved.connect(self._after_cashbox_saved)
            try:
                editor.titleChanged.connect(self.cash_inline_title_label.setText)
            except Exception:
                pass
            self.cash_inline_title_label.setText(editor.workspace_title() if hasattr(editor, 'workspace_title') else editor.windowTitle())
            self.cash_inline_host_layout.addWidget(editor)
            self._cash_inline_editor = editor
            self.tabs.setCurrentWidget(self.cash_tab)
            self.cash_detail_stack.setCurrentWidget(self.cash_inline_page)
            return editor
        except Exception as exc:
            show_toast(str(exc), 'error', self)
            return None

    def open_bank_inline(self, bank_account_id=None):
        if getattr(self, '_bank_inline_editor', None) is not None and not self._close_bank_inline_editor():
            return None
        try:
            from features.finance import BankAccountDocumentTab
            editor = BankAccountDocumentTab(self.bank_inline_host, bank_account_id=bank_account_id)
            editor.setProperty('inlineEditor', True)
            self._wire_inline_close(editor, self._close_bank_inline_editor)
            editor.saved.connect(self._after_bank_saved)
            try:
                editor.titleChanged.connect(self.bank_inline_title_label.setText)
            except Exception:
                pass
            self.bank_inline_title_label.setText(editor.workspace_title() if hasattr(editor, 'workspace_title') else editor.windowTitle())
            self.bank_inline_host_layout.addWidget(editor)
            self._bank_inline_editor = editor
            self.tabs.setCurrentWidget(self.bank_tab)
            self.bank_detail_stack.setCurrentWidget(self.bank_inline_page)
            return editor
        except Exception as exc:
            show_toast(str(exc), 'error', self)
            return None

    def add_cashbox(self):
        if not self._require_finance_operation(finance_operation_policy.OP_CASHBOX_CREATE):
            return
        # Phase378: صندوق جديد يفتح inline داخل تبويب الصناديق، لا تبويب فرعي.
        # Legacy route marker only: main_window.open_cashbox_document()
        return self.open_cashbox_inline()

    def edit_cashbox(self):
        if not self._require_finance_operation(finance_operation_policy.OP_CASHBOX_EDIT):
            return
        cid = self._selected(self.cash_table, 'cash_model')
        if not cid:
            QMessageBox.information(self, tr('edit_title'), tr('select_cashbox'))
            return
        return self.open_cashbox_inline(cid)

    def archive_cashbox(self):
        cid = self._selected(self.cash_table, 'cash_model')
        if not cid:
            return
        if QMessageBox.question(self, tr('confirm'), tr('archive_cashbox_confirm')) == QMessageBox.Yes:
            try:
                cashbox_service.archive_cashbox(cid)
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, tr('error'), str(e))

    def add_bank(self):
        if not self._require_finance_operation(finance_operation_policy.OP_BANK_CREATE):
            return
        # Phase378: حساب بنك جديد يفتح inline داخل تبويب الحسابات، لا تبويب فرعي.
        # Legacy route marker only: main_window.open_bank_account_document()
        return self.open_bank_inline()

    def edit_bank(self):
        if not self._require_finance_operation(finance_operation_policy.OP_BANK_EDIT):
            return
        bid = self._selected(self.bank_table, 'bank_model')
        if not bid:
            QMessageBox.information(self, tr('edit_title'), tr('select_bank_account'))
            return
        return self.open_bank_inline(bid)

    def archive_bank(self):
        bid = self._selected(self.bank_table, 'bank_model')
        if not bid:
            return
        if QMessageBox.question(self, tr('confirm'), tr('archive_bank_confirm')) == QMessageBox.Yes:
            try:
                cashbox_service.archive_bank_account(bid)
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, tr('error'), str(e))


# Phase110 offline guard markers: الصناديق والبنوك
