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
from core.services.invoice_service import invoice_service
from core.services.party_operation_policy import party_operation_policy
from core.services.reporting_service import reporting_service
from core.services.voucher_service import voucher_service
from currency import currency
from i18n import qt_layout_direction, translate
from models.table_models import GenericTableModel
from ui.smart_table_view import SmartTableView
from utils import show_toast
from workspace.documents import BaseDocumentTab
from workspace.documents.document_contract import descriptor_for


def _tr(key: str, fallback: str) -> str:
    value = translate(key)
    return fallback if value == key else value


def _dec(value) -> Decimal:
    try:
        return Decimal(str(value or 0))
    except Exception:
        return Decimal('0')


def _money(value) -> str:
    try:
        return currency.format_base_amount(_dec(value))
    except Exception:
        return currency.format_amount(_dec(value))


class _MetricCard(QFrame):
    """Small side-panel metric card used by party document shell."""

    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName('MetricCard')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        self.title_label = QLabel(title, self)
        self.title_label.setObjectName('MetricTitle')
        self.value_label = QLabel(_money(0), self)
        self.value_label.setObjectName('MetricValue')
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value) -> None:
        self.value_label.setText(_money(value))


class PartyEditorTab(BaseDocumentTab):
    DOCUMENT_DESCRIPTOR_BY_PARTY_TYPE = {"customer": descriptor_for("customer"), "supplier": descriptor_for("supplier")}
    """Customer/supplier document shell.

    Phase 220 upgrades the party editor from a simple form-with-tabs into a
    document shell aligned with the transaction documents: header, identity and
    contact panels, financial summary side panel, related-data grids, and fixed
    bottom actions.  Persistence remains behind EntityService and all access is
    governed by party_operation_policy.
    """

    def __init__(self, parent=None, party_type: str = 'customer', party_id: Optional[int] = None, inline_mode: bool = False) -> None:
        party_type = 'supplier' if party_type == 'supplier' else 'customer'
        super().__init__(party_type, document_id=party_id, parent=parent)
        self.inline_mode = bool(inline_mode)
        self.party_type = party_type
        self.document_descriptor = self.DOCUMENT_DESCRIPTOR_BY_PARTY_TYPE[party_type]
        try:
            from workspace.documents.document_permission_binder import DocumentPermissionBinder
            self.document_permission_binder = DocumentPermissionBinder(self.document_descriptor)
        except Exception:
            pass
        self.party_id = party_id
        self.is_edit = party_id is not None
        self._statement_balance = Decimal('0')
        self._invoice_total = Decimal('0')
        self._invoice_paid = Decimal('0')
        self._invoice_remaining = Decimal('0')
        self._voucher_total = Decimal('0')
        self._build_ui()
        self._apply_operation_policy()
        try:
            self.apply_document_permissions()
        except Exception:
            pass
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
        if self.inline_mode:
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(8)
        else:
            root.setContentsMargins(14, 14, 14, 14)
            root.setSpacing(10)

        if not self.inline_mode:
            root.addWidget(self._build_header())
        root.addWidget(self._build_body(), 0)

        context_label = QLabel(_tr('party_context_title', 'السجل المرتبط بالطرف'), self)
        context_label.setObjectName('SectionTitle')
        root.addWidget(context_label)

        self.tabs = QTabWidget(self)
        self.statement_table = SmartTableView(identity=f'{self.party_type}_statement_document')
        self.invoices_table = SmartTableView(identity=f'{self.party_type}_invoices_document')
        self.vouchers_table = SmartTableView(identity=f'{self.party_type}_vouchers_document')
        self.tabs.addTab(self.statement_table, _tr('statement', 'كشف الحساب'))
        self.tabs.addTab(self.invoices_table, _tr('invoices', 'الفواتير'))
        self.tabs.addTab(self.vouchers_table, _tr('vouchers', 'السندات'))
        root.addWidget(self.tabs, 1)

        root.addWidget(self._build_bottom_actions())
        self._apply_shell_styles()

    def _build_header(self) -> QFrame:
        header = QFrame(self)
        header.setObjectName('DocumentHeaderCard')
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        titles = QVBoxLayout()
        titles.setSpacing(4)
        self.title_label = QLabel(self._new_title(), header)
        self.title_label.setObjectName('DocumentTitle')
        self.subtitle_label = QLabel(_tr('party_document_subtitle', 'تبويب مستند موحد: بيانات الطرف، الرصيد، كشف الحساب، الفواتير، والسندات.'), header)
        self.subtitle_label.setObjectName('DocumentSubtitle')
        titles.addWidget(self.title_label)
        titles.addWidget(self.subtitle_label)
        layout.addLayout(titles, 1)

        # Phase 229: document headers are informational only; all local
        # document commands live in BottomActionBar / UnifiedActionBar.
        return header

    def _build_body(self) -> QWidget:
        body = QWidget(self)
        layout = QHBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        details = QFrame(body)
        details.setObjectName('DocumentPanel')
        details_layout = QHBoxLayout(details)
        details_layout.setContentsMargins(12, 12, 12, 12)
        details_layout.setSpacing(10)

        identity_card = QGroupBox(_tr('party_identity_panel', 'هوية الطرف'), details)
        identity_card.setObjectName('FormCard')
        identity_form = QFormLayout(identity_card)
        identity_form.setLabelAlignment(Qt.AlignRight)
        self.name_edit = QLineEdit(identity_card)
        self.name_edit.setPlaceholderText(_tr('name_required', 'الاسم مطلوب'))
        identity_form.addRow(translate('name'), self.name_edit)

        contact_card = QGroupBox(_tr('party_contact_panel', 'التواصل والعنوان'), details)
        contact_card.setObjectName('FormCard')
        contact_form = QFormLayout(contact_card)
        contact_form.setLabelAlignment(Qt.AlignRight)
        self.phone_edit = QLineEdit(contact_card)
        self.address_edit = QLineEdit(contact_card)
        self.phone_edit.setPlaceholderText(_tr('phone_optional', 'الهاتف اختياري'))
        self.address_edit.setPlaceholderText(_tr('address_optional', 'العنوان اختياري'))
        contact_form.addRow(translate('phone'), self.phone_edit)
        contact_form.addRow(translate('address'), self.address_edit)

        details_layout.addWidget(identity_card, 1)
        details_layout.addWidget(contact_card, 1)
        layout.addWidget(details, 3)

        summary = QFrame(body)
        summary.setObjectName('SummaryPanel')
        summary_layout = QVBoxLayout(summary)
        summary_layout.setContentsMargins(12, 12, 12, 12)
        summary_layout.setSpacing(8)
        summary_title = QLabel(_tr('party_balance_panel', 'ملخص الرصيد والائتمان'), summary)
        summary_title.setObjectName('SectionTitle')
        summary_layout.addWidget(summary_title)
        self.balance_metric = _MetricCard(_tr('party_current_balance', 'الرصيد الحالي'), summary)
        self.invoice_total_metric = _MetricCard(_tr('party_invoice_total', 'إجمالي الفواتير'), summary)
        self.invoice_paid_metric = _MetricCard(_tr('party_invoice_paid', 'المدفوع من الفواتير'), summary)
        self.invoice_remaining_metric = _MetricCard(_tr('party_invoice_remaining', 'المتبقي على الفواتير'), summary)
        self.voucher_total_metric = _MetricCard(_tr('party_voucher_total', 'إجمالي السندات'), summary)
        for metric in (
            self.balance_metric,
            self.invoice_total_metric,
            self.invoice_paid_metric,
            self.invoice_remaining_metric,
            self.voucher_total_metric,
        ):
            summary_layout.addWidget(metric)
        summary_layout.addStretch(1)
        layout.addWidget(summary, 1)
        return body

    def _build_bottom_actions(self) -> QFrame:
        bar = QFrame(self)
        bar.setObjectName('BottomActionBar')
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)
        self.bottom_refresh_btn = QPushButton(_tr('refresh', 'تحديث'), bar)
        self.bottom_refresh_btn.clicked.connect(self.refresh_context_tables)
        self.bottom_print_btn = QPushButton(_tr('print', 'طباعة'), bar)
        self.bottom_print_btn.clicked.connect(self.workspace_print)
        self.bottom_export_btn = QPushButton(_tr('export', 'تصدير'), bar)
        self.bottom_export_btn.clicked.connect(self.workspace_export)
        self.bottom_save_btn = QPushButton(translate('save'), bar)
        self.bottom_save_btn.setObjectName('primary')
        self.bottom_save_btn.clicked.connect(self.workspace_save)
        # Backward-compatible alias for older code/tests; no header button.
        self.save_btn = self.bottom_save_btn
        for btn in (self.bottom_refresh_btn, self.bottom_print_btn, self.bottom_export_btn):
            layout.addWidget(btn)
        layout.addStretch(1)
        layout.addWidget(self.bottom_save_btn)
        return bar

    def _apply_shell_styles(self) -> None:
        self.setStyleSheet('''
            QFrame#DocumentHeaderCard, QFrame#DocumentPanel, QFrame#SummaryPanel, QFrame#BottomActionBar, QGroupBox#FormCard, QFrame#MetricCard {
                border: 1px solid palette(mid);
                border-radius: 14px;
                background: palette(base);
            }
            QFrame#BottomActionBar { background: palette(window); }
            QLabel#DocumentTitle { font-size: 18px; font-weight: 900; }
            QLabel#DocumentSubtitle { color: palette(mid); }
            QLabel#SectionTitle { font-weight: 900; }
            QLabel#MetricTitle { color: palette(mid); font-size: 11px; }
            QLabel#MetricValue { font-size: 15px; font-weight: 900; }
            QPushButton#primary { font-weight: 900; padding: 8px 16px; }
        ''')

    def _apply_operation_policy(self) -> None:
        operation = party_operation_policy.OP_CUSTOMER_EDIT if self.party_type == 'customer' else party_operation_policy.OP_SUPPLIER_EDIT
        if not self.is_edit:
            operation = party_operation_policy.OP_CUSTOMER_CREATE if self.party_type == 'customer' else party_operation_policy.OP_SUPPLIER_CREATE
        allowed = party_operation_policy.can(operation)
        for widget in (self.name_edit, self.phone_edit, self.address_edit):
            widget.setReadOnly(not allowed)
        self.bottom_save_btn.setEnabled(allowed)
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
        self._refresh_summary_panel()

    def _refresh_summary_panel(self) -> None:
        self.balance_metric.set_value(self._statement_balance)
        self.invoice_total_metric.set_value(self._invoice_total)
        self.invoice_paid_metric.set_value(self._invoice_paid)
        self.invoice_remaining_metric.set_value(self._invoice_remaining)
        self.voucher_total_metric.set_value(self._voucher_total)

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
        self._statement_balance = Decimal('0')
        for row in rows:
            debit = _dec(row.get('debit', row.get('Debit', 0)))
            credit = _dec(row.get('credit', row.get('Credit', 0)))
            balance = _dec(row.get('balance', row.get('Balance', debit - credit)))
            self._statement_balance = balance
            data.append({
                'date': row.get('date') or row.get('created_at') or row.get('Date') or '',
                'reference': row.get('reference') or row.get('description') or row.get('Reference') or '',
                'debit': _money(debit),
                'credit': _money(credit),
                'balance': _money(balance),
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
        self._invoice_total = Decimal('0')
        self._invoice_paid = Decimal('0')
        self._invoice_remaining = Decimal('0')
        for inv in records:
            total = _dec(inv.get('total', 0))
            paid = _dec(inv.get('paid', 0))
            remaining = total - paid
            self._invoice_total += total
            self._invoice_paid += paid
            self._invoice_remaining += remaining
            data.append({
                'id': inv.get('id', ''),
                'date': inv.get('date') or inv.get('created_at') or '',
                'reference': inv.get('reference') or inv.get('invoice_number') or '',
                'total': _money(total),
                'paid': _money(paid),
                'remaining': _money(remaining),
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
        self._voucher_total = Decimal('0')
        for voucher in records:
            amount = _dec(voucher.get('amount', 0))
            self._voucher_total += amount
            data.append({
                'id': voucher.get('id', ''),
                'date': voucher.get('date') or voucher.get('created_at') or '',
                'type': voucher.get('type') or '',
                'reference': voucher.get('reference') or voucher.get('description') or '',
                'amount': _money(amount),
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
    def __init__(self, parent=None, customer_id: Optional[int] = None, inline_mode: bool = False) -> None:
        super().__init__(parent=parent, party_type='customer', party_id=customer_id, inline_mode=inline_mode)


class SupplierEditorTab(PartyEditorTab):
    def __init__(self, parent=None, supplier_id: Optional[int] = None, inline_mode: bool = False) -> None:
        super().__init__(parent=parent, party_type='supplier', party_id=supplier_id, inline_mode=inline_mode)
