# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
                             QTabWidget, QMessageBox, QHeaderView, QTableView)
from decimal import Decimal
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

class CashboxesWidget(QWidget):
    def __init__(self,parent=None): super().__init__(parent); self.setLayoutDirection(qt_layout_direction()); self._setup_ui(); self._apply_finance_policy(); apply_modern_widget(self, tr('finance_cashbanks_title'), tr('finance_cashbanks_subtitle')); self.refresh()
    def _setup_ui(self):
        layout=QVBoxLayout(self); title=QLabel(tr('finance_cashbanks_title')); title.setObjectName('sectionTitle'); layout.addWidget(title); self.tabs=QTabWidget(); layout.addWidget(self.tabs)
        self.cash_tab=QWidget(); self.bank_tab=QWidget(); self.shift_tab=QWidget(); self.mov_tab=QWidget(); self.tabs.addTab(self.cash_tab,tr('cashboxes')); self.tabs.addTab(self.bank_tab,tr('bank_accounts')); self.tabs.addTab(self.shift_tab,tr('pos_shifts')); self.tabs.addTab(self.mov_tab,tr('financial_movements'))
        self._cash_ui(); self._bank_ui(); self._shift_ui(); self._mov_ui(); self._apply_shift_tab_visibility()
    def _apply_shift_tab_visibility(self):
        try:
            if not settings_service.pos_shifts_enabled():
                idx = self.tabs.indexOf(self.shift_tab)
                if idx >= 0:
                    self.tabs.removeTab(idx)
        except Exception:
            pass

    def _cash_ui(self):
        layout=QVBoxLayout(self.cash_tab); bar=QHBoxLayout(); self.cash_search=QLineEdit(); self.cash_search.setPlaceholderText(tr('search_cashboxes')); self.cash_search.textChanged.connect(self.refresh_cashboxes)
        self.add_cashbox_btn=QPushButton(tr('add_cashbox')); self.add_cashbox_btn.clicked.connect(self.add_cashbox); self.edit_cashbox_btn=QPushButton(tr('edit')); self.edit_cashbox_btn.clicked.connect(self.edit_cashbox); self.archive_cashbox_btn=QPushButton(tr('archive')); self.archive_cashbox_btn.clicked.connect(self.archive_cashbox)
        bar.addWidget(self.cash_search,1); bar.addWidget(self.add_cashbox_btn); bar.addWidget(self.edit_cashbox_btn); bar.addWidget(self.archive_cashbox_btn); layout.addLayout(bar); self.cash_table=SmartTableView(identity="cashboxes.cashboxes"); self.cash_table.setSelectionBehavior(QTableView.SelectRows); layout.addWidget(self.cash_table)
    def _bank_ui(self):
        layout=QVBoxLayout(self.bank_tab); bar=QHBoxLayout(); self.bank_search=QLineEdit(); self.bank_search.setPlaceholderText(tr('search_banks')); self.bank_search.textChanged.connect(self.refresh_banks)
        self.add_bank_btn=QPushButton(tr('add_bank_account')); self.add_bank_btn.clicked.connect(self.add_bank); self.edit_bank_btn=QPushButton(tr('edit')); self.edit_bank_btn.clicked.connect(self.edit_bank); self.archive_bank_btn=QPushButton(tr('archive')); self.archive_bank_btn.clicked.connect(self.archive_bank)
        bar.addWidget(self.bank_search,1); bar.addWidget(self.add_bank_btn); bar.addWidget(self.edit_bank_btn); bar.addWidget(self.archive_bank_btn); layout.addLayout(bar); self.bank_table=SmartTableView(identity="cashboxes.banks"); self.bank_table.setSelectionBehavior(QTableView.SelectRows); layout.addWidget(self.bank_table)
    def _shift_ui(self):
        layout=QVBoxLayout(self.shift_tab); bar=QHBoxLayout(); refresh=QPushButton(tr('refresh')); refresh.clicked.connect(self.refresh_shifts); bar.addStretch(); bar.addWidget(refresh); layout.addLayout(bar); self.shift_table=SmartTableView(identity="cashboxes.shifts"); self.shift_table.setSelectionBehavior(QTableView.SelectRows); layout.addWidget(self.shift_table)

    def _mov_ui(self):
        layout=QVBoxLayout(self.mov_tab); bar=QHBoxLayout(); refresh=QPushButton(tr('refresh')); refresh.clicked.connect(self.refresh_movements); bar.addStretch(); bar.addWidget(refresh); layout.addLayout(bar); self.mov_table=SmartTableView(identity="cashboxes.movements"); self.mov_table.setSelectionBehavior(QTableView.SelectRows); layout.addWidget(self.mov_table)
    def set_global_filter(self, text: str):
        text = (text or '').strip().lower()
        # Generic visual filter for widgets that expose one or more Qt tables.
        for name, table in self.__dict__.items():
            if not hasattr(table, 'rowCount') or not hasattr(table, 'setRowHidden'):
                continue
            try:
                rows = table.rowCount()
                cols = table.columnCount()
            except Exception:
                continue
            for row in range(rows):
                hay = []
                for col in range(cols):
                    try:
                        item = table.item(row, col) if hasattr(table, 'item') else None
                        if item is not None:
                            hay.append(item.text())
                        elif hasattr(table, 'model') and table.model() is not None:
                            idx = table.model().index(row, col)
                            hay.append(str(table.model().data(idx) or ''))
                    except Exception:
                        pass
                table.setRowHidden(row, bool(text) and text not in ' '.join(hay).lower())


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
                try: btn.setEnabled(finance_operation_policy.can(op))
                except Exception: pass

    def _require_finance_operation(self, operation):
        try:
            finance_operation_policy.require(operation, context='CashboxesWidget')
            return True
        except Exception as exc:
            QMessageBox.warning(self, tr('error'), str(exc))
            return False

    def refresh(self):
        try:
            cashbox_service.bootstrap(); self.refresh_cashboxes(); self.refresh_banks();
            if settings_service.pos_shifts_enabled(): self.refresh_shifts()
            self.refresh_movements()
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(tr('finance_cashbanks_title')), 'warning', self)
                return
            raise
    def refresh_cashboxes(self):
        text=self.cash_search.text().strip().lower() if hasattr(self,'cash_search') else ''; rows=[]
        try:
            cashboxes = cashbox_service.cashboxes(True)
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(tr('cashboxes')), 'warning', self)
                return
            raise
        for c in cashboxes:
            if text and text not in str(c.get('name','')).lower() and text not in str(c.get('code','')).lower(): continue
            bal=currency.format_amount(currency.to_display(Decimal(str(c.get('balance') or 0))))
            rows.append({'id':c.get('id'),'branch':c.get('branch_name',''),'name':c.get('name',''),'code':c.get('code') or '—','balance':bal,'default':tr('yes') if int(c.get('is_default') or 0)==1 else tr('no'),'status':tr('archived') if c.get('deleted_at') or int(c.get('is_active') or 0)==0 else tr('active_status')})
        self.cash_model=GenericTableModel(rows,[tr('branch'),tr('cashbox'),tr('code'),tr('balance'),tr('default'),tr('status')],key_fields=['id'],data_keys=['branch','name','code','balance','default','status']); self.cash_table.setModel(self.cash_model); self.cash_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
    def refresh_banks(self):
        text=self.bank_search.text().strip().lower() if hasattr(self,'bank_search') else ''; rows=[]
        try:
            bank_accounts = cashbox_service.bank_accounts(True)
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(tr('bank_accounts')), 'warning', self)
                return
            raise
        for b in bank_accounts:
            if text and text not in str(b.get('bank_name','')).lower() and text not in str(b.get('account_name','')).lower(): continue
            bal=currency.format_amount(currency.to_display(Decimal(str(b.get('balance') or 0))))
            rows.append({'id':b.get('id'),'branch':b.get('branch_name',''),'bank':b.get('bank_name',''),'account':b.get('account_name') or '—','number':b.get('account_number') or '—','balance':bal,'status':tr('archived') if b.get('deleted_at') or int(b.get('is_active') or 0)==0 else tr('active_status')})
        self.bank_model=GenericTableModel(rows,[tr('branch'),tr('bank'),tr('account'),tr('account_number'),tr('balance'),tr('status')],key_fields=['id'],data_keys=['branch','bank','account','number','balance','status']); self.bank_table.setModel(self.bank_model); self.bank_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
    def refresh_shifts(self):
        rows=[]
        try:
            shifts = cashbox_service.shifts(limit=200)
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(tr('pos_shifts')), 'warning', self)
                return
            raise
        for sh in shifts:
            diff=currency.format_amount(currency.to_display(Decimal(str(sh.get('difference_amount') or 0)))) if sh.get('difference_amount') not in (None,'') else '—'
            rows.append({'id':sh.get('id'),'branch':sh.get('branch_name',''),'cashbox':sh.get('cashbox_name',''),'opened':sh.get('opened_at',''),'closed':sh.get('closed_at') or '—','status':tr('open_status') if sh.get('status')=='open' else tr('closed_status'),'sales':currency.format_amount(currency.to_display(Decimal(str(sh.get('total_sales') or 0)))),'diff':diff})
        self.shift_model=GenericTableModel(rows,[tr('line_no'),tr('branch'),tr('cashbox'),tr('open_time'),tr('close_time'),tr('status'),tr('sales_total'),tr('difference')],data_keys=['id','branch','cashbox','opened','closed','status','sales','diff']); self.shift_table.setModel(self.shift_model); self.shift_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

    def refresh_movements(self):
        rows=[]
        try:
            movements = cashbox_service.movements(limit=300)
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(tr('financial_movements')), 'warning', self)
                return
            raise
        for m in movements:
            amount=currency.format_amount(currency.to_display(Decimal(str(m.get('amount') or 0)))); account=m.get('cashbox_name') or f"{m.get('bank_name') or ''} {m.get('account_name') or ''}".strip()
            rows.append({'date':m.get('movement_date',''),'branch':m.get('branch_name',''),'account':account,'type':m.get('movement_type',''),'amount':amount,'ref':f"{m.get('reference_type') or ''} #{m.get('reference_id') or ''}",'desc':m.get('description','')})
        self.mov_model=GenericTableModel(rows,[tr('date'),tr('branch'),tr('account'),tr('type'),tr('amount'),tr('reference'),tr('description')],data_keys=['date','branch','account','type','amount','ref','desc']); self.mov_table.setModel(self.mov_model); self.mov_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
    def _selected(self, table, model_attr):
        model=getattr(self,model_attr,None)
        if not model:
            return None
        row = table.current_source_row() if hasattr(table, 'current_source_row') else None
        if row is None:
            rows=table.selectionModel().selectedRows() if table.selectionModel() else []
            row = rows[0].row() if rows else None
        return model.get_id(row) if row is not None else None
    def add_cashbox(self):
        if not self._require_finance_operation(finance_operation_policy.OP_CASHBOX_CREATE): return
        mw=self.window()
        if hasattr(mw,'open_cashbox_document'):
            return mw.open_cashbox_document()
        show_toast(tr('cannot_open_document_tab'), 'error', self)
    def edit_cashbox(self):
        cid=self._selected(self.cash_table,'cash_model')
        if not cid: QMessageBox.information(self,tr('edit_title'),tr('select_cashbox')); return
        try:
            data=next((c for c in cashbox_service.cashboxes(True) if int(c.get('id'))==int(cid)),None)
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(tr('cashbox')), 'warning', self)
                return
            raise
        mw=self.window()
        if hasattr(mw,'open_cashbox_document'):
            return mw.open_cashbox_document(cid)
        show_toast(tr('cannot_open_document_tab'), 'error', self)
    def archive_cashbox(self):
        cid=self._selected(self.cash_table,'cash_model')
        if not cid: return
        if QMessageBox.question(self,tr('confirm'),tr('archive_cashbox_confirm'))==QMessageBox.Yes:
            try: cashbox_service.archive_cashbox(cid); self.refresh()
            except Exception as e: QMessageBox.warning(self,tr('error'),str(e))
    def add_bank(self):
        if not self._require_finance_operation(finance_operation_policy.OP_BANK_CREATE): return
        mw=self.window()
        if hasattr(mw,'open_bank_account_document'):
            return mw.open_bank_account_document()
        show_toast(tr('cannot_open_document_tab'), 'error', self)
    def edit_bank(self):
        bid=self._selected(self.bank_table,'bank_model')
        if not bid: QMessageBox.information(self,tr('edit_title'),tr('select_bank_account')); return
        try:
            data=next((b for b in cashbox_service.bank_accounts(True) if int(b.get('id'))==int(bid)),None)
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(tr('bank_account')), 'warning', self)
                return
            raise
        mw=self.window()
        if hasattr(mw,'open_bank_account_document'):
            return mw.open_bank_account_document(bid)
        show_toast(tr('cannot_open_document_tab'), 'error', self)
    def archive_bank(self):
        bid=self._selected(self.bank_table,'bank_model')
        if not bid: return
        if QMessageBox.question(self,tr('confirm'),tr('archive_bank_confirm'))==QMessageBox.Yes:
            try: cashbox_service.archive_bank_account(bid); self.refresh()
            except Exception as e: QMessageBox.warning(self,tr('error'),str(e))

# Phase110 offline guard markers: الصناديق والبنوك
