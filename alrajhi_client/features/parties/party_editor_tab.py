# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal
from typing import Dict, List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.services.entity_service import entity_service
from core.services.party_operation_policy import party_operation_policy
from core.services.invoice_service import invoice_service
from core.services.reporting_service import reporting_service
from core.services.voucher_service import voucher_service
from currency import currency
from i18n import qt_layout_direction, translate
from models.table_models import GenericTableModel
from ui.smart_table_view import SmartTableView
from utils import show_toast
from workspace.documents import BaseDocumentTab


def _tr(key: str, fallback: str) -> str:
    value = translate(key)
    return fallback if value == key else value


class PartyEditorTab(BaseDocumentTab):
    """Customer/supplier document tab.

    Phase 50 turns parties into workspace documents instead of modal add/edit
    dialogs. The tab keeps persistence behind EntityService and read-only
    business context behind Reporting/Invoice services.
    """

    def __init__(self, parent=None, party_type: str = 'customer', party_id: Optional[int] = None) -> None:
        party_type = 'supplier' if party_type == 'supplier' else 'customer'
        super().__init__(f'{party_type}_document', document_id=party_id, parent=parent)
        self.party_type = party_type
        self.party_id = party_id
        self.is_edit = party_id is not None
        self._build_ui()
        self._apply_operation_policy()
        if self.is_edit:
            self.load_party()
        else:
            self.set_document_title(self._new_title())
            self.refresh_context_tables()
        self._connect_dirty_tracking()
        self.set_dirty(False)

    def _new_title(self) -> str:
        return _tr('customer_new_tab', 'عميل جديد') if self.party_type == 'customer' else _tr('supplier_new_tab', 'مورد جديد')

    def _edit_title(self, name: str) -> str:
        prefix = _tr('customer_tab_prefix', 'عميل') if self.party_type == 'customer' else _tr('supplier_tab_prefix', 'مورد')
        return f'{prefix}: {name or self.party_id}'

    def _build_ui(self) -> None:
        self.setLayoutDirection(qt_layout_direction())
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        header = QFrame(self)
        header.setObjectName('DocumentHeaderCard')
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        titles = QVBoxLayout()
        self.title_label = QLabel(self._new_title())
        self.title_label.setObjectName('DocumentTitle')
        self.subtitle_label = QLabel(_tr('party_document_subtitle', 'بيانات الطرف وكشف الحساب والفواتير المرتبطة في تبويب واحد'))
        self.subtitle_label.setObjectName('DocumentSubtitle')
        titles.addWidget(self.title_label)
        titles.addWidget(self.subtitle_label)
        header_layout.addLayout(titles, 1)
        self.save_btn = QPushButton(translate('save'))
        self.save_btn.setObjectName('primary')
        self.save_btn.clicked.connect(self.workspace_save)
        header_layout.addWidget(self.save_btn)
        root.addWidget(header)

        self.tabs = QTabWidget(self)
        root.addWidget(self.tabs, 1)

        self.details_page = QWidget(self)
        details_layout = QVBoxLayout(self.details_page)
        details_layout.setContentsMargins(12, 12, 12, 12)
        details_card = QGroupBox(_tr('party_basic_data', 'البيانات الأساسية'), self.details_page)
        details_card.setObjectName('FormCard')
        form = QFormLayout(details_card)
        form.setLabelAlignment(Qt.AlignRight)
        self.name_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.name_edit.setPlaceholderText(_tr('name_required', 'الاسم مطلوب'))
        self.phone_edit.setPlaceholderText(_tr('phone_optional', 'الهاتف اختياري'))
        self.address_edit.setPlaceholderText(_tr('address_optional', 'العنوان اختياري'))
        form.addRow(translate('name'), self.name_edit)
        form.addRow(translate('phone'), self.phone_edit)
        form.addRow(translate('address'), self.address_edit)
        details_layout.addWidget(details_card)
        details_layout.addStretch(1)
        self.tabs.addTab(self.details_page, _tr('party_details_tab', 'البيانات'))

        self.statement_table = SmartTableView(identity=f'{self.party_type}_statement_document')
        self.tabs.addTab(self.statement_table, _tr('statement', 'كشف الحساب'))

        self.invoices_table = SmartTableView(identity=f'{self.party_type}_invoices_document')
        self.tabs.addTab(self.invoices_table, _tr('invoices', 'الفواتير'))

        self.vouchers_table = SmartTableView(identity=f'{self.party_type}_vouchers_document')
        self.tabs.addTab(self.vouchers_table, _tr('vouchers', 'السندات'))

        self.setStyleSheet('''
            QFrame#DocumentHeaderCard, QGroupBox#FormCard {
                border: 1px solid palette(mid);
                border-radius: 14px;
                background: palette(base);
            }
            QLabel#DocumentTitle { font-size: 18px; font-weight: 900; }
            QLabel#DocumentSubtitle { color: palette(mid); }
            QPushButton#primary { font-weight: 900; padding: 8px 16px; }
        ''')

    def _apply_operation_policy(self) -> None:
        operation = party_operation_policy.OP_CUSTOMER_EDIT if self.party_type == 'customer' else party_operation_policy.OP_SUPPLIER_EDIT
        if not self.is_edit:
            operation = party_operation_policy.OP_CUSTOMER_CREATE if self.party_type == 'customer' else party_operation_policy.OP_SUPPLIER_CREATE
        allowed = party_operation_policy.can(operation)
        for widget in (self.name_edit, self.phone_edit, self.address_edit):
            widget.setReadOnly(not allowed)
        self.save_btn.setEnabled(allowed)
        if not allowed:
            self.subtitle_label.setText(_tr('party_read_only', 'للقراءة فقط حسب الصلاحيات أو الإعدادات'))

    def _connect_dirty_tracking(self) -> None:
        for widget in (self.name_edit, self.phone_edit, self.address_edit):
            widget.textChanged.connect(lambda *_: self.set_dirty(True))

    def load_party(self) -> None:
        data = self._get_party() or {}
        self.name_edit.setText(str(data.get('name', '') or ''))
        self.phone_edit.setText(str(data.get('phone', '') or ''))
        self.address_edit.setText(str(data.get('address', '') or ''))
        title = self._edit_title(self.name_edit.text().strip())
        self.title_label.setText(title)
        self.set_document_title(title)
        self.refresh_context_tables()
        self.set_dirty(False)

    def _get_party(self) -> Optional[Dict]:
        if self.party_id is None:
            return None
        if self.party_type == 'customer':
            return entity_service.customer_by_id(int(self.party_id))
        return entity_service.supplier_by_id(int(self.party_id))

    def _payload(self) -> Dict[str, str]:
        return {
            'name': self.name_edit.text().strip(),
            'phone': self.phone_edit.text().strip(),
            'address': self.address_edit.text().strip(),
        }

    def workspace_save(self) -> None:
        payload = self._payload()
        if not payload['name']:
            QMessageBox.warning(self, translate('validation_error'), _tr('party_name_required', 'اسم العميل/المورد مطلوب'))
            return
        if self.party_type == 'customer':
            if self.party_id is None:
                self.party_id = entity_service.add_customer(payload['name'], payload['phone'], payload['address'])
                self.document_state.document_id = self.party_id
            else:
                entity_service.update_customer(int(self.party_id), payload['name'], payload['phone'], payload['address'])
        else:
            if self.party_id is None:
                self.party_id = entity_service.add_supplier(payload['name'], payload['phone'], payload['address'])
                self.document_state.document_id = self.party_id
            else:
                entity_service.update_supplier(int(self.party_id), payload['name'], payload['phone'], payload['address'])
        title = self._edit_title(payload['name'])
        self.title_label.setText(title)
        self.set_document_title(title)
        self.refresh_context_tables()
        self.set_dirty(False)
        self.saved.emit(self.party_id)
        show_toast(translate('save_done') if translate('save_done') != 'save_done' else _tr('saved', 'تم الحفظ'), 'success', self)

    def refresh_context_tables(self) -> None:
        self._load_statement()
        self._load_invoices()
        self._load_vouchers()

    def _load_statement(self) -> None:
        rows: List[Dict] = []
        if self.party_id is not None:
            try:
                if self.party_type == 'customer':
                    rows = reporting_service.customer_statement(int(self.party_id))
                else:
                    rows = reporting_service.supplier_statement(int(self.party_id))
            except Exception:
                rows = []
        data = []
        for row in rows:
            debit = Decimal(str(row.get('debit', row.get('Debit', 0)) or 0))
            credit = Decimal(str(row.get('credit', row.get('Credit', 0)) or 0))
            balance = Decimal(str(row.get('balance', row.get('Balance', debit - credit)) or 0))
            data.append({
                'date': row.get('date') or row.get('created_at') or row.get('Date') or '',
                'reference': row.get('reference') or row.get('description') or row.get('Reference') or '',
                'debit': currency.format_amount(debit),
                'credit': currency.format_amount(credit),
                'balance': currency.format_amount(balance),
            })
        headers = ['date', 'reference', 'debit', 'credit', 'balance']
        labels = [_tr('date', 'التاريخ'), _tr('reference', 'المرجع'), _tr('debit', 'مدين'), _tr('credit', 'دائن'), _tr('balance', 'الرصيد')]
        self.statement_model = GenericTableModel(data, labels, data_keys=headers)
        self.statement_table.setModel(self.statement_model)
        self.statement_table.refresh_style()

    def _load_invoices(self) -> None:
        records: List[Dict] = []
        if self.party_id is not None:
            try:
                if self.party_type == 'customer':
                    records = invoice_service.list_records(inv_type='sale', customer_id=int(self.party_id), limit=200, offset=0)
                else:
                    records = invoice_service.list_records(inv_type='purchase', supplier_id=int(self.party_id), limit=200, offset=0)
            except Exception:
                records = []
        data = []
        for inv in records:
            total = Decimal(str(inv.get('total', 0) or 0))
            paid = Decimal(str(inv.get('paid', 0) or 0))
            data.append({
                'id': inv.get('id', ''),
                'date': inv.get('date') or inv.get('created_at') or '',
                'reference': inv.get('reference') or inv.get('invoice_number') or '',
                'total': currency.format_amount(total),
                'paid': currency.format_amount(paid),
                'remaining': currency.format_amount(total - paid),
                'status': inv.get('workflow_status') or inv.get('status') or '',
            })
        headers = ['id', 'date', 'reference', 'total', 'paid', 'remaining', 'status']
        labels = [_tr('id', 'المعرف'), _tr('date', 'التاريخ'), _tr('reference', 'المرجع'), _tr('total', 'الإجمالي'), _tr('paid', 'المدفوع'), _tr('remaining', 'المتبقي'), _tr('status', 'الحالة')]
        self.invoices_model = GenericTableModel(data, labels, key_fields=['id'], data_keys=headers)
        self.invoices_table.setModel(self.invoices_model)
        self.invoices_table.refresh_style()

    def _load_vouchers(self) -> None:
        records: List[Dict] = []
        if self.party_id is not None:
            try:
                all_records, _count = voucher_service.list_vouchers(limit=500, offset=0)
                party_key = 'customer_id' if self.party_type == 'customer' else 'supplier_id'
                records = [row for row in all_records if str(row.get(party_key) or '') == str(self.party_id)]
            except Exception:
                records = []
        data = []
        for voucher in records:
            amount = Decimal(str(voucher.get('amount', 0) or 0))
            data.append({
                'id': voucher.get('id', ''),
                'date': voucher.get('date') or voucher.get('created_at') or '',
                'type': voucher.get('type') or '',
                'reference': voucher.get('reference') or voucher.get('description') or '',
                'amount': currency.format_amount(amount),
                'method': voucher.get('payment_method') or voucher.get('method') or '',
            })
        headers = ['id', 'date', 'type', 'reference', 'amount', 'method']
        labels = [_tr('id', 'المعرف'), _tr('date', 'التاريخ'), _tr('type', 'النوع'), _tr('reference', 'المرجع'), _tr('amount', 'المبلغ'), _tr('payment_method', 'طريقة الدفع')]
        self.vouchers_model = GenericTableModel(data, labels, key_fields=['id'], data_keys=headers)
        self.vouchers_table.setModel(self.vouchers_model)
        self.vouchers_table.refresh_style()

    def workspace_print(self) -> None:
        current = self.tabs.currentWidget()
        if hasattr(current, 'print_table'):
            current.print_table()
        else:
            self.tabs.setCurrentWidget(self.statement_table)
            self.statement_table.print_table()

    def workspace_export(self) -> None:
        current = self.tabs.currentWidget()
        if hasattr(current, 'export_to_excel'):
            current.export_to_excel()
        else:
            super().workspace_export()


class CustomerEditorTab(PartyEditorTab):
    def __init__(self, parent=None, customer_id: Optional[int] = None) -> None:
        super().__init__(parent=parent, party_type='customer', party_id=customer_id)


class SupplierEditorTab(PartyEditorTab):
    def __init__(self, parent=None, supplier_id: Optional[int] = None) -> None:
        super().__init__(parent=parent, party_type='supplier', party_id=supplier_id)
