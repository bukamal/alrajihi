# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import (
    QDateEdit,
    QFrame,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.services.finance_operation_policy import finance_operation_policy
from core.services.voucher_service import voucher_service
from currency import currency
from features.vouchers.components import VoucherPaymentPanel
from i18n import qt_layout_direction, translate as tr
from printing.printing_service import printing_service
from utils import show_toast
from workspace.documents import BaseDocumentTab


def _tr(key: str, fallback: str) -> str:
    value = tr(key)
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
        try:
            return currency.format_amount(_dec(value))
        except Exception:
            return str(value or '')


class _ExpenseMetricCard(QFrame):
    """Side-panel metric card for expense documents."""

    def __init__(self, title: str, value: str = '', parent=None) -> None:
        super().__init__(parent)
        self.setObjectName('MetricCard')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        self.title_label = QLabel(title, self)
        self.title_label.setObjectName('MetricTitle')
        self.value_label = QLabel(value or _money(0), self)
        self.value_label.setObjectName('MetricValue')
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class ExpenseIdentityPanel(QWidget):
    """Expense identity fields independent from the generic voucher header."""

    def __init__(self, parent=None, expense: Optional[dict] = None) -> None:
        super().__init__(parent)
        layout = QFormLayout(self)
        layout.setLabelAlignment(Qt.AlignRight)

        self.date_edit = QDateEdit(self)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        layout.addRow(tr('date_label'), self.date_edit)

        self.reference_edit = QLineEdit(self)
        self.reference_edit.setPlaceholderText(_tr('expense_reference_placeholder', 'رقم مرجع اختياري'))
        layout.addRow(tr('reference_label'), self.reference_edit)

        self.description_edit = QLineEdit(self)
        self.description_edit.setPlaceholderText(_tr('expense_description_placeholder', 'وصف المصروف أو سبب الصرف'))
        layout.addRow(tr('description_label'), self.description_edit)

        if isinstance(expense, dict):
            self.load(expense)

    def load(self, expense: dict) -> None:
        if expense.get('date'):
            parsed = QDate.fromString(str(expense.get('date')), 'yyyy-MM-dd')
            if parsed.isValid():
                self.date_edit.setDate(parsed)
        self.reference_edit.setText(str(expense.get('reference') or ''))
        self.description_edit.setText(str(expense.get('description') or ''))

    def set_read_only(self, read_only: bool) -> None:
        self.date_edit.setEnabled(not read_only)
        self.reference_edit.setReadOnly(read_only)
        self.description_edit.setReadOnly(read_only)

    def payload(self) -> dict:
        return {
            'type': 'expense',
            'date': self.date_edit.date().toString('yyyy-MM-dd'),
            'reference': self.reference_edit.text().strip(),
            'description': self.description_edit.text().strip(),
            'customer_id': None,
            'supplier_id': None,
            'invoice_id': None,
        }


class ExpenseDocumentTab(BaseDocumentTab):
    """Expense-specific finance document shell.

    Phase 222 separates expenses from the generic voucher editor surface.  The
    persistence contract remains compatible with expense vouchers, but the UX is
    now an explicit expense document: identity panel, payment panel, summary
    side panel, and fixed action bar.  It has no customer/supplier/invoice link
    panel and never exposes the voucher type selector.
    """

    def __init__(self, parent=None, expense: Optional[dict] = None) -> None:
        document_id = expense.get('id') if isinstance(expense, dict) else None
        super().__init__('expense', document_id=document_id, parent=parent)
        self.expense = dict(expense or {})
        self.is_edit = bool(document_id)
        self._last_saved_id = document_id
        self.identity_panel = ExpenseIdentityPanel(self, expense=self.expense)
        self.payment_panel = VoucherPaymentPanel(self, voucher=self.expense)
        self._build_layout()
        self._connect_signals()
        self._apply_operation_state()
        self._refresh_summary_panel()
        self.set_document_title(self._title())
        self.set_dirty(False)

    def _build_layout(self) -> None:
        self.setLayoutDirection(qt_layout_direction())
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)
        root.addWidget(self._build_header_card())
        root.addWidget(self._build_body(), 1)
        root.addWidget(self._build_bottom_actions())
        self._apply_shell_styles()

    def _build_header_card(self) -> QFrame:
        header = QFrame(self)
        header.setObjectName('ExpenseDocumentHeaderCard')
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        self.title_label = QLabel(self._title(), header)
        self.title_label.setObjectName('DocumentTitle')
        self.subtitle_label = QLabel(_tr('expense_document_subtitle', 'مستند مصروف مستقل: وصف، تاريخ، مرجع، طريقة دفع، وملخص مالي.'), header)
        self.subtitle_label.setObjectName('DocumentSubtitle')
        title_box.addWidget(self.title_label)
        title_box.addWidget(self.subtitle_label)
        layout.addLayout(title_box, 1)

        # Phase 229: header is informational; commands live in ExpenseBottomActionBar.
        return header

    def _build_body(self) -> QWidget:
        body = QWidget(self)
        layout = QHBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        panels = QFrame(body)
        panels.setObjectName('ExpenseDocumentPanel')
        panels_layout = QVBoxLayout(panels)
        panels_layout.setContentsMargins(12, 12, 12, 12)
        panels_layout.setSpacing(10)
        panels_layout.addWidget(self._section(_tr('expense_identity_panel', 'بيانات المصروف'), self.identity_panel))
        panels_layout.addWidget(self._section(_tr('expense_payment_panel', 'الدفع والصندوق/البنك'), self.payment_panel))
        panels_layout.addStretch(1)
        layout.addWidget(panels, 3)

        summary = QFrame(body)
        summary.setObjectName('ExpenseSummaryPanel')
        summary_layout = QVBoxLayout(summary)
        summary_layout.setContentsMargins(12, 12, 12, 12)
        summary_layout.setSpacing(8)
        summary_title = QLabel(_tr('expense_summary_panel', 'ملخص المصروف'), summary)
        summary_title.setObjectName('SectionTitle')
        summary_layout.addWidget(summary_title)
        self.amount_metric = _ExpenseMetricCard(_tr('expense_metric_amount', 'المبلغ'), _money(0), summary)
        self.method_metric = _ExpenseMetricCard(_tr('expense_metric_payment_method', 'طريقة الدفع'), '-', summary)
        self.target_metric = _ExpenseMetricCard(_tr('expense_metric_target', 'الصندوق/الحساب'), '-', summary)
        self.date_metric = _ExpenseMetricCard(_tr('expense_metric_date', 'التاريخ'), self.identity_panel.date_edit.date().toString('yyyy-MM-dd'), summary)
        self.reference_metric = _ExpenseMetricCard(_tr('expense_metric_reference', 'المرجع'), '-', summary)
        for metric in (self.amount_metric, self.method_metric, self.target_metric, self.date_metric, self.reference_metric):
            summary_layout.addWidget(metric)
        summary_layout.addStretch(1)
        layout.addWidget(summary, 1)
        return body

    def _section(self, title: str, widget: QWidget) -> QFrame:
        frame = QFrame(self)
        frame.setObjectName('ExpenseDocumentSection')
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        label = QLabel(title, frame)
        label.setObjectName('SectionTitle')
        layout.addWidget(label)
        layout.addWidget(widget)
        return frame

    def _build_bottom_actions(self) -> QFrame:
        bar = QFrame(self)
        bar.setObjectName('ExpenseBottomActionBar')
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)
        self.bottom_print_btn = QPushButton(_tr('print_button', 'طباعة'), bar)
        self.bottom_print_btn.clicked.connect(self.workspace_print)
        self.bottom_export_btn = QPushButton(_tr('export', 'تصدير'), bar)
        self.bottom_export_btn.clicked.connect(self.workspace_export)
        self.bottom_save_btn = QPushButton(_tr('save', 'حفظ'), bar)
        self.bottom_save_btn.setObjectName('primary')
        self.bottom_save_btn.clicked.connect(self.workspace_save)
        layout.addWidget(self.bottom_print_btn)
        layout.addWidget(self.bottom_export_btn)
        layout.addStretch(1)
        layout.addWidget(self.bottom_save_btn)
        return bar

    def _apply_shell_styles(self) -> None:
        self.setStyleSheet('''
            QFrame#ExpenseDocumentHeaderCard, QFrame#ExpenseDocumentPanel, QFrame#ExpenseSummaryPanel, QFrame#ExpenseBottomActionBar {
                border: 1px solid rgba(120, 120, 120, 0.22);
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.03);
            }
            QFrame#ExpenseDocumentSection, QFrame#MetricCard {
                border: 1px solid rgba(120, 120, 120, 0.16);
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.025);
            }
            QLabel#DocumentTitle { font-size: 18px; font-weight: 900; }
            QLabel#DocumentSubtitle { color: palette(mid); }
            QLabel#SectionTitle { font-weight: 800; }
            QLabel#MetricTitle { color: palette(mid); font-size: 11px; }
            QLabel#MetricValue { font-size: 15px; font-weight: 900; }
            QPushButton#primary { font-weight: 900; padding: 8px 16px; }
        ''')

    def _connect_signals(self) -> None:
        self.identity_panel.date_edit.dateChanged.connect(lambda *_: self._on_changed())
        self.identity_panel.reference_edit.textChanged.connect(lambda *_: self._on_changed())
        self.identity_panel.description_edit.textChanged.connect(lambda *_: self._on_changed())
        self.payment_panel.changed.connect(self._on_changed)
        self.payment_panel.amount_spin.valueChanged.connect(lambda *_: self._refresh_summary_panel())
        self.payment_panel.payment_method_combo.currentIndexChanged.connect(lambda *_: self._refresh_summary_panel())
        self.payment_panel.cashbox_combo.currentIndexChanged.connect(lambda *_: self._refresh_summary_panel())
        self.payment_panel.bank_combo.currentIndexChanged.connect(lambda *_: self._refresh_summary_panel())

    def _operation_for_save(self) -> str:
        return finance_operation_policy.OP_EXPENSE_EDIT if self.is_edit else finance_operation_policy.OP_EXPENSE_CREATE

    def _apply_operation_state(self) -> None:
        can_save = finance_operation_policy.can(self._operation_for_save())
        can_print = finance_operation_policy.can(finance_operation_policy.OP_EXPENSE_PRINT)
        self.identity_panel.set_read_only(not can_save)
        self.payment_panel.setEnabled(can_save)
        self.bottom_save_btn.setEnabled(can_save)
        for btn in (self.bottom_print_btn, self.bottom_export_btn):
            btn.setEnabled(can_print)
        if not can_save:
            self.subtitle_label.setText(_tr('expense_read_only', 'المصروف للقراءة فقط حسب الصلاحيات أو الإعدادات.'))
            self.setToolTip(_tr('expense_read_only', 'المصروف للقراءة فقط حسب الصلاحيات أو الإعدادات.'))

    def _on_changed(self) -> None:
        self.set_dirty(True)
        title = self._title()
        self.set_document_title(title)
        self.title_label.setText(title)
        self._refresh_summary_panel()

    def _title(self) -> str:
        if self._last_saved_id:
            return f"{tr('expense')} #{self._last_saved_id}"
        return _tr('expense_document_new', 'مصروف جديد') + (' *' if self.is_dirty() else '')

    def _payload(self) -> dict:
        data = {}
        data.update(self.identity_panel.payload())
        data.update(self.payment_panel.payload())
        data['type'] = 'expense'
        data['customer_id'] = None
        data['supplier_id'] = None
        data['invoice_id'] = None
        return data

    def _validate_payload(self, data: dict) -> bool:
        if not data.get('description'):
            show_toast(_tr('expense_description_required', 'وصف المصروف مطلوب'), 'error', self)
            return False
        if data.get('payment_method') == 'cash' and not data.get('cashbox_id'):
            show_toast(tr('select_cashbox_required'), 'error', self)
            return False
        if data.get('payment_method') == 'bank' and not data.get('bank_account_id'):
            show_toast(tr('select_bank_required'), 'error', self)
            return False
        try:
            if data.get('amount') <= 0:
                show_toast(tr('amount_positive_required'), 'error', self)
                return False
        except Exception:
            show_toast(tr('amount_positive_required'), 'error', self)
            return False
        return True

    def _refresh_summary_panel(self) -> None:
        if not hasattr(self, 'amount_metric'):
            return
        try:
            self.amount_metric.set_value(_money(self.payment_panel.amount_usd()))
        except Exception:
            self.amount_metric.set_value(_money(0))
        try:
            self.method_metric.set_value(self.payment_panel.payment_method_combo.currentText() or '-')
            method = self.payment_panel.payment_method_combo.currentData() or 'cash'
            target = self.payment_panel.bank_combo.currentText() if method == 'bank' else self.payment_panel.cashbox_combo.currentText()
            self.target_metric.set_value(target or '-')
        except Exception:
            self.method_metric.set_value('-')
            self.target_metric.set_value('-')
        self.date_metric.set_value(self.identity_panel.date_edit.date().toString('yyyy-MM-dd'))
        self.reference_metric.set_value(self.identity_panel.reference_edit.text().strip() or '-')

    def workspace_save(self) -> None:
        try:
            finance_operation_policy.require(self._operation_for_save(), context='expense:document:save', payload={'id': self._last_saved_id})
        except PermissionError as exc:
            show_toast(tr(str(exc)) if str(exc) else tr('permission_denied'), 'error', self)
            return
        data = self._payload()
        if not self._validate_payload(data):
            return
        try:
            if self.is_edit and self._last_saved_id:
                voucher_service.update(self._last_saved_id, data)
                saved_id = self._last_saved_id
                show_toast(tr('voucher_updated'), 'success', self)
            else:
                saved_id = voucher_service.add(data)
                self.is_edit = True
                self._last_saved_id = saved_id
                self.document_state.document_id = saved_id
                show_toast(tr('voucher_added'), 'success', self)
            self.expense = voucher_service.get(saved_id) or dict(data, id=saved_id)
            self.set_dirty(False)
            title = self._title()
            self.set_document_title(title)
            self.title_label.setText(title)
            self._refresh_summary_panel()
            self._apply_operation_state()
            self.saved.emit(saved_id)
        except Exception as exc:
            show_toast(str(exc), 'error', self)

    def _current_expense_for_printing(self) -> Optional[dict]:
        expense = dict(self.expense or {})
        if self._last_saved_id:
            expense = voucher_service.get(self._last_saved_id) or expense
        if not expense.get('id'):
            return None
        expense['type'] = 'expense'
        expense['party_name'] = ''
        return expense

    def workspace_print(self) -> None:
        try:
            finance_operation_policy.require(finance_operation_policy.OP_EXPENSE_PRINT, context='expense:document:print', payload={'id': self._last_saved_id})
        except PermissionError as exc:
            show_toast(tr(str(exc)) if str(exc) else tr('permission_denied'), 'error', self)
            return
        if self.is_dirty():
            reply = QMessageBox.question(self, tr('print_button'), tr('workspace.unsaved_close'), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
            self.workspace_save()
        expense = self._current_expense_for_printing()
        if not expense:
            QMessageBox.information(self, tr('print_button'), tr('select_voucher_first'))
            return
        printing_service.voucher_preview(expense, self)

    def workspace_export(self) -> None:
        try:
            finance_operation_policy.require(finance_operation_policy.OP_EXPENSE_PRINT, context='expense:document:export', payload={'id': self._last_saved_id})
        except PermissionError as exc:
            show_toast(tr(str(exc)) if str(exc) else tr('permission_denied'), 'error', self)
            return
        expense = self._current_expense_for_printing()
        if not expense:
            QMessageBox.information(self, tr('print_button'), tr('select_voucher_first'))
            return
        printing_service.voucher_pdf(expense, self)
