# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
                             QTabWidget, QDialog, QFormLayout, QDialogButtonBox, QComboBox,
                             QTextEdit, QCheckBox, QMessageBox, QHeaderView, QTableView)
from PyQt5.QtCore import Qt
from decimal import Decimal
from core.services.cashbox_service import cashbox_service
from core.services.branch_service import branch_service
from currency import currency
from models.table_models import GenericTableModel
from views.custom_table_view import CustomTableView
from utils import show_toast

class CashboxDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent); self.data=data or {}; self.setWindowTitle('صندوق جديد' if not data else 'تعديل صندوق'); self.setLayoutDirection(Qt.RightToLeft); self.resize(430,300)
        layout=QVBoxLayout(self); form=QFormLayout()
        self.branch_combo=QComboBox()
        for b in branch_service.branches(): self.branch_combo.addItem(b.get('name',''), b.get('id'))
        if self.data.get('branch_id'):
            i=self.branch_combo.findData(self.data.get('branch_id'))
            if i>=0: self.branch_combo.setCurrentIndex(i)
        self.name_edit=QLineEdit(self.data.get('name','')); self.code_edit=QLineEdit(self.data.get('code',''))
        self.notes_edit=QTextEdit(self.data.get('notes','')); self.notes_edit.setMaximumHeight(70)
        self.active_check=QCheckBox('نشط'); self.active_check.setChecked(bool(int(self.data.get('is_active',1) or 0)))
        form.addRow('الفرع:', self.branch_combo); form.addRow('اسم الصندوق:', self.name_edit); form.addRow('الكود:', self.code_edit); form.addRow('ملاحظات:', self.notes_edit); form.addRow('', self.active_check)
        layout.addLayout(form); buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel); buttons.button(QDialogButtonBox.Save).setText('حفظ'); buttons.button(QDialogButtonBox.Cancel).setText('إلغاء'); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); layout.addWidget(buttons)
    def payload(self): return {'branch_id':self.branch_combo.currentData(),'name':self.name_edit.text().strip(),'code':self.code_edit.text().strip(),'notes':self.notes_edit.toPlainText().strip(),'is_active':1 if self.active_check.isChecked() else 0}

class BankDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent); self.data=data or {}; self.setWindowTitle('حساب بنكي جديد' if not data else 'تعديل حساب بنكي'); self.setLayoutDirection(Qt.RightToLeft); self.resize(460,360)
        layout=QVBoxLayout(self); form=QFormLayout(); self.branch_combo=QComboBox()
        for b in branch_service.branches(): self.branch_combo.addItem(b.get('name',''), b.get('id'))
        if self.data.get('branch_id'):
            i=self.branch_combo.findData(self.data.get('branch_id'))
            if i>=0: self.branch_combo.setCurrentIndex(i)
        self.bank_edit=QLineEdit(self.data.get('bank_name','')); self.account_name=QLineEdit(self.data.get('account_name','')); self.account_number=QLineEdit(self.data.get('account_number','')); self.iban=QLineEdit(self.data.get('iban',''))
        self.notes=QTextEdit(self.data.get('notes','')); self.notes.setMaximumHeight(70); self.active_check=QCheckBox('نشط'); self.active_check.setChecked(bool(int(self.data.get('is_active',1) or 0)))
        form.addRow('الفرع:', self.branch_combo); form.addRow('البنك:', self.bank_edit); form.addRow('اسم الحساب:', self.account_name); form.addRow('رقم الحساب:', self.account_number); form.addRow('IBAN:', self.iban); form.addRow('ملاحظات:', self.notes); form.addRow('', self.active_check)
        layout.addLayout(form); buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel); buttons.button(QDialogButtonBox.Save).setText('حفظ'); buttons.button(QDialogButtonBox.Cancel).setText('إلغاء'); buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); layout.addWidget(buttons)
    def payload(self): return {'branch_id':self.branch_combo.currentData(),'bank_name':self.bank_edit.text().strip(),'account_name':self.account_name.text().strip(),'account_number':self.account_number.text().strip(),'iban':self.iban.text().strip(),'notes':self.notes.toPlainText().strip(),'is_active':1 if self.active_check.isChecked() else 0}

class CashboxesWidget(QWidget):
    def __init__(self,parent=None): super().__init__(parent); self.setLayoutDirection(Qt.RightToLeft); self._setup_ui(); self.refresh()
    def _setup_ui(self):
        layout=QVBoxLayout(self); title=QLabel('💰 الصناديق والبنوك'); title.setObjectName('sectionTitle'); layout.addWidget(title); self.tabs=QTabWidget(); layout.addWidget(self.tabs)
        self.cash_tab=QWidget(); self.bank_tab=QWidget(); self.shift_tab=QWidget(); self.mov_tab=QWidget(); self.tabs.addTab(self.cash_tab,'الصناديق'); self.tabs.addTab(self.bank_tab,'الحسابات البنكية'); self.tabs.addTab(self.shift_tab,'ورديات POS'); self.tabs.addTab(self.mov_tab,'الحركات المالية')
        self._cash_ui(); self._bank_ui(); self._shift_ui(); self._mov_ui()
    def _cash_ui(self):
        layout=QVBoxLayout(self.cash_tab); bar=QHBoxLayout(); self.cash_search=QLineEdit(); self.cash_search.setPlaceholderText('بحث في الصناديق...'); self.cash_search.textChanged.connect(self.refresh_cashboxes)
        add=QPushButton('➕ صندوق'); add.clicked.connect(self.add_cashbox); edit=QPushButton('✏️ تعديل'); edit.clicked.connect(self.edit_cashbox); arch=QPushButton('🗑️ أرشفة'); arch.clicked.connect(self.archive_cashbox)
        bar.addWidget(self.cash_search,1); bar.addWidget(add); bar.addWidget(edit); bar.addWidget(arch); layout.addLayout(bar); self.cash_table=CustomTableView(); self.cash_table.setSelectionBehavior(QTableView.SelectRows); layout.addWidget(self.cash_table)
    def _bank_ui(self):
        layout=QVBoxLayout(self.bank_tab); bar=QHBoxLayout(); self.bank_search=QLineEdit(); self.bank_search.setPlaceholderText('بحث في البنوك...'); self.bank_search.textChanged.connect(self.refresh_banks)
        add=QPushButton('➕ حساب بنكي'); add.clicked.connect(self.add_bank); edit=QPushButton('✏️ تعديل'); edit.clicked.connect(self.edit_bank); arch=QPushButton('🗑️ أرشفة'); arch.clicked.connect(self.archive_bank)
        bar.addWidget(self.bank_search,1); bar.addWidget(add); bar.addWidget(edit); bar.addWidget(arch); layout.addLayout(bar); self.bank_table=CustomTableView(); self.bank_table.setSelectionBehavior(QTableView.SelectRows); layout.addWidget(self.bank_table)
    def _shift_ui(self):
        layout=QVBoxLayout(self.shift_tab); bar=QHBoxLayout(); refresh=QPushButton('تحديث'); refresh.clicked.connect(self.refresh_shifts); bar.addStretch(); bar.addWidget(refresh); layout.addLayout(bar); self.shift_table=CustomTableView(); self.shift_table.setSelectionBehavior(QTableView.SelectRows); layout.addWidget(self.shift_table)

    def _mov_ui(self):
        layout=QVBoxLayout(self.mov_tab); bar=QHBoxLayout(); refresh=QPushButton('تحديث'); refresh.clicked.connect(self.refresh_movements); bar.addStretch(); bar.addWidget(refresh); layout.addLayout(bar); self.mov_table=CustomTableView(); self.mov_table.setSelectionBehavior(QTableView.SelectRows); layout.addWidget(self.mov_table)
    def refresh(self): cashbox_service.bootstrap(); self.refresh_cashboxes(); self.refresh_banks(); self.refresh_shifts(); self.refresh_movements()
    def refresh_cashboxes(self):
        text=self.cash_search.text().strip().lower() if hasattr(self,'cash_search') else ''; rows=[]
        for c in cashbox_service.cashboxes(True):
            if text and text not in str(c.get('name','')).lower() and text not in str(c.get('code','')).lower(): continue
            bal=currency.format_amount(currency.convert(Decimal(str(c.get('balance') or 0)),'USD',currency.get_display_currency()))
            rows.append({'id':c.get('id'),'branch':c.get('branch_name',''),'name':c.get('name',''),'code':c.get('code') or '—','balance':bal,'default':'نعم' if int(c.get('is_default') or 0)==1 else 'لا','status':'مؤرشف' if c.get('deleted_at') or int(c.get('is_active') or 0)==0 else 'نشط'})
        self.cash_model=GenericTableModel(rows,['الفرع','الصندوق','الكود','الرصيد','رئيسي','الحالة'],key_fields=['id'],data_keys=['branch','name','code','balance','default','status']); self.cash_table.setModel(self.cash_model); self.cash_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
    def refresh_banks(self):
        text=self.bank_search.text().strip().lower() if hasattr(self,'bank_search') else ''; rows=[]
        for b in cashbox_service.bank_accounts(True):
            if text and text not in str(b.get('bank_name','')).lower() and text not in str(b.get('account_name','')).lower(): continue
            bal=currency.format_amount(currency.convert(Decimal(str(b.get('balance') or 0)),'USD',currency.get_display_currency()))
            rows.append({'id':b.get('id'),'branch':b.get('branch_name',''),'bank':b.get('bank_name',''),'account':b.get('account_name') or '—','number':b.get('account_number') or '—','balance':bal,'status':'مؤرشف' if b.get('deleted_at') or int(b.get('is_active') or 0)==0 else 'نشط'})
        self.bank_model=GenericTableModel(rows,['الفرع','البنك','الحساب','رقم الحساب','الرصيد','الحالة'],key_fields=['id'],data_keys=['branch','bank','account','number','balance','status']); self.bank_table.setModel(self.bank_model); self.bank_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
    def refresh_shifts(self):
        rows=[]
        for sh in cashbox_service.shifts(limit=200):
            diff=currency.format_amount(currency.convert(Decimal(str(sh.get('difference_amount') or 0)),'USD',currency.get_display_currency())) if sh.get('difference_amount') not in (None,'') else '—'
            rows.append({'id':sh.get('id'),'branch':sh.get('branch_name',''),'cashbox':sh.get('cashbox_name',''),'opened':sh.get('opened_at',''),'closed':sh.get('closed_at') or '—','status':'مفتوحة' if sh.get('status')=='open' else 'مغلقة','sales':currency.format_amount(currency.convert(Decimal(str(sh.get('total_sales') or 0)),'USD',currency.get_display_currency())),'diff':diff})
        self.shift_model=GenericTableModel(rows,['#','الفرع','الصندوق','الفتح','الإغلاق','الحالة','المبيعات','الفرق'],data_keys=['id','branch','cashbox','opened','closed','status','sales','diff']); self.shift_table.setModel(self.shift_model); self.shift_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

    def refresh_movements(self):
        rows=[]
        for m in cashbox_service.movements(limit=300):
            amount=currency.format_amount(currency.convert(Decimal(str(m.get('amount') or 0)),'USD',currency.get_display_currency())); account=m.get('cashbox_name') or f"{m.get('bank_name') or ''} {m.get('account_name') or ''}".strip()
            rows.append({'date':m.get('movement_date',''),'branch':m.get('branch_name',''),'account':account,'type':m.get('movement_type',''),'amount':amount,'ref':f"{m.get('reference_type') or ''} #{m.get('reference_id') or ''}",'desc':m.get('description','')})
        self.mov_model=GenericTableModel(rows,['التاريخ','الفرع','الحساب','النوع','المبلغ','المرجع','الوصف'],data_keys=['date','branch','account','type','amount','ref','desc']); self.mov_table.setModel(self.mov_model); self.mov_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
    def _selected(self, table, model_attr):
        model=getattr(self,model_attr,None); rows=table.selectionModel().selectedRows() if table.selectionModel() else []
        return model.get_id(rows[0].row()) if rows and model else None
    def add_cashbox(self):
        d=CashboxDialog(self)
        if d.exec_():
            try: cashbox_service.add_cashbox(d.payload()); show_toast(self,'تم إنشاء الصندوق','success'); self.refresh()
            except Exception as e: QMessageBox.warning(self,'خطأ',str(e))
    def edit_cashbox(self):
        cid=self._selected(self.cash_table,'cash_model')
        if not cid: QMessageBox.information(self,'تعديل','اختر صندوقاً'); return
        data=next((c for c in cashbox_service.cashboxes(True) if int(c.get('id'))==int(cid)),None); d=CashboxDialog(self,data)
        if d.exec_():
            try: cashbox_service.update_cashbox(cid,d.payload()); show_toast(self,'تم التعديل','success'); self.refresh()
            except Exception as e: QMessageBox.warning(self,'خطأ',str(e))
    def archive_cashbox(self):
        cid=self._selected(self.cash_table,'cash_model')
        if not cid: return
        if QMessageBox.question(self,'تأكيد','أرشفة الصندوق؟')==QMessageBox.Yes:
            try: cashbox_service.archive_cashbox(cid); self.refresh()
            except Exception as e: QMessageBox.warning(self,'خطأ',str(e))
    def add_bank(self):
        d=BankDialog(self)
        if d.exec_():
            try: cashbox_service.add_bank_account(d.payload()); show_toast(self,'تم إنشاء الحساب','success'); self.refresh()
            except Exception as e: QMessageBox.warning(self,'خطأ',str(e))
    def edit_bank(self):
        bid=self._selected(self.bank_table,'bank_model')
        if not bid: QMessageBox.information(self,'تعديل','اختر حساباً'); return
        data=next((b for b in cashbox_service.bank_accounts(True) if int(b.get('id'))==int(bid)),None); d=BankDialog(self,data)
        if d.exec_():
            try: cashbox_service.update_bank_account(bid,d.payload()); show_toast(self,'تم التعديل','success'); self.refresh()
            except Exception as e: QMessageBox.warning(self,'خطأ',str(e))
    def archive_bank(self):
        bid=self._selected(self.bank_table,'bank_model')
        if not bid: return
        if QMessageBox.question(self,'تأكيد','أرشفة الحساب البنكي؟')==QMessageBox.Yes:
            try: cashbox_service.archive_bank_account(bid); self.refresh()
            except Exception as e: QMessageBox.warning(self,'خطأ',str(e))
