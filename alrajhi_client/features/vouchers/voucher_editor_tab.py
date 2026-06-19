# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from core.services.voucher_service import voucher_service
from core.services.finance_operation_policy import finance_operation_policy
from currency import currency
from features.vouchers.components import VoucherHeaderPanel, VoucherLinkPanel, VoucherPaymentPanel
from i18n import qt_layout_direction, translate as tr
from printing.printing_service import printing_service
from utils import show_toast
from workspace.documents import BaseDocumentTab


def _tr(key: str, fallback: str) -> str:
    value = tr(key)
    return fallback if value == key else value


def _money(value) -> str:
    try:
        return currency.format_base_amount(Decimal(str(value or 0)))
    except Exception:
        try:
            return currency.format_amount(Decimal(str(value or 0)))
        except Exception:
            return str(value or '')


class _VoucherMetricCard(QFrame):
    """Small financial metric card for the voucher document shell."""

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


class _ActionsCompat(QWidget):
    """Compatibility surface for older code that expects actions_panel.save_btn/print_btn."""

    def __init__(self, save_btn: QPushButton, print_btn: QPushButton, parent=None) -> None:
        super().__init__(parent)
        self.save_btn = save_btn
        self.print_btn = print_btn


class VoucherEditorTab(BaseDocumentTab):
    """Receipt/payment voucher as a Finance Document Shell.

    Phase 221 upgrades the voucher editor from stacked form panels into a shell
    aligned with the invoice/document UX: header card, finance body panels,
    summary side panel, and fixed bottom action bar.  Persistence stays behind
    VoucherService; operation control stays behind finance_operation_policy;
    currency display uses the project currency contract.
    """

    def __init__(self, parent=None, voucher: Optional[dict] = None, voucher_type: str = 'receipt') -> None:
        document_id = voucher.get('id') if isinstance(voucher, dict) else None
        super().__init__('voucher', document_id=document_id, parent=parent)
        self.voucher = dict(voucher or {})
        self.is_edit = bool(voucher)
        self._last_saved_id = document_id

        self.header_panel = VoucherHeaderPanel(self, voucher=self.voucher, voucher_type=voucher_type)
        self.link_panel = VoucherLinkPanel(self, voucher=self.voucher)
        self.payment_panel = VoucherPaymentPanel(self, voucher=self.voucher)

        self._build_layout()
        self._connect_signals()
        self._sync_type_visibility()
        self._apply_operation_state()
        self.set_document_title(self._title())
        self._refresh_summary_panel()
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
        header.setObjectName('DocumentHeaderCard')
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        self.title_label = QLabel(self._title(), header)
        self.title_label.setObjectName('DocumentTitle')
        self.subtitle_label = QLabel(_tr('voucher_document_subtitle', 'مستند مالي موحد: طرف، فاتورة مرتبطة، وسيلة دفع، ومبلغ بعملة العرض.'), header)
        self.subtitle_label.setObjectName('DocumentSubtitle')
        title_box.addWidget(self.title_label)
        title_box.addWidget(self.subtitle_label)
        layout.addLayout(title_box, 1)

        # Phase 229: header is informational; commands live in BottomActionBar.
        return header

    def _build_body(self) -> QWidget:
        body = QWidget(self)
        layout = QHBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        panels = QFrame(body)
        panels.setObjectName('DocumentPanel')
        panels_layout = QVBoxLayout(panels)
        panels_layout.setContentsMargins(12, 12, 12, 12)
        panels_layout.setSpacing(10)
        panels_layout.addWidget(self._section(_tr('voucher_identity_panel', 'بيانات السند'), self.header_panel))
        panels_layout.addWidget(self._section(_tr('voucher_party_link_panel', 'الطرف والفاتورة المرتبطة'), self.link_panel))
        panels_layout.addWidget(self._section(_tr('voucher_payment_panel', 'الدفع والصندوق/البنك'), self.payment_panel))
        panels_layout.addStretch(1)
        layout.addWidget(panels, 3)

        summary = QFrame(body)
        summary.setObjectName('SummaryPanel')
        summary_layout = QVBoxLayout(summary)
        summary_layout.setContentsMargins(12, 12, 12, 12)
        summary_layout.setSpacing(8)
        summary_title = QLabel(_tr('voucher_summary_panel', 'ملخص السند'), summary)
        summary_title.setObjectName('SectionTitle')
        summary_layout.addWidget(summary_title)
        self.type_metric = _VoucherMetricCard(_tr('voucher_metric_type', 'نوع السند'), '', summary)
        self.amount_metric = _VoucherMetricCard(_tr('voucher_metric_amount', 'المبلغ'), _money(0), summary)
        self.invoice_metric = _VoucherMetricCard(_tr('voucher_metric_invoice_remaining', 'المتبقي على الفاتورة'), _money(0), summary)
        self.method_metric = _VoucherMetricCard(_tr('voucher_metric_payment_method', 'طريقة الدفع'), '', summary)
        self.target_metric = _VoucherMetricCard(_tr('voucher_metric_target', 'الصندوق/الحساب'), '', summary)
        for metric in (self.type_metric, self.amount_metric, self.invoice_metric, self.method_metric, self.target_metric):
            summary_layout.addWidget(metric)
        summary_layout.addStretch(1)
        layout.addWidget(summary, 1)
        return body

    def _section(self, title: str, widget: QWidget) -> QFrame:
        frame = QFrame(self)
        frame.setObjectName('DocumentSection')
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
        bar.setObjectName('BottomActionBar')
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

        # Backward-compatible handle expected by ExpenseDocumentTab and any older tests.
        self.actions_panel = _ActionsCompat(self.bottom_save_btn, self.bottom_print_btn, self)
        return bar

    def _apply_shell_styles(self) -> None:
        self.setStyleSheet('''
            QFrame#DocumentHeaderCard, QFrame#DocumentPanel, QFrame#SummaryPanel, QFrame#BottomActionBar {
                border: 1px solid rgba(120, 120, 120, 0.22);
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.03);
            }
            QFrame#DocumentSection, QFrame#MetricCard {
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
        self.header_panel.changed.connect(self._on_changed)
        self.link_panel.changed.connect(self._on_changed)
        self.payment_panel.changed.connect(self._on_changed)
        self.header_panel.type_combo.currentIndexChanged.connect(lambda *_: self._sync_type_visibility())
        self.link_panel.remainingSelected.connect(self.payment_panel.set_amount_usd)
        self.link_panel.remainingSelected.connect(lambda *_: self._refresh_summary_panel())
        self.payment_panel.amount_spin.valueChanged.connect(lambda *_: self._refresh_summary_panel())
        self.payment_panel.payment_method_combo.currentIndexChanged.connect(lambda *_: self._refresh_summary_panel())
        self.payment_panel.cashbox_combo.currentIndexChanged.connect(lambda *_: self._refresh_summary_panel())
        self.payment_panel.bank_combo.currentIndexChanged.connect(lambda *_: self._refresh_summary_panel())
        self.link_panel.invoice_combo.currentIndexChanged.connect(lambda *_: self._refresh_summary_panel())

    def _operation_for_save(self) -> str:
        return finance_operation_policy.OP_VOUCHER_EDIT if self.is_edit else finance_operation_policy.OP_VOUCHER_CREATE

    def _apply_operation_state(self) -> None:
        can_save = finance_operation_policy.can(self._operation_for_save())
        can_print = finance_operation_policy.can(finance_operation_policy.OP_VOUCHER_PRINT)
        for panel in (self.header_panel, self.link_panel, self.payment_panel):
            panel.setEnabled(can_save)
        self.bottom_save_btn.setEnabled(can_save)
        for btn in (self.bottom_print_btn, self.bottom_export_btn):
            btn.setEnabled(can_print)
        if not can_save:
            self.subtitle_label.setText(_tr('voucher_read_only', 'السند للعرض فقط حسب الصلاحيات أو الإعدادات.'))
            self.setToolTip(_tr('voucher_read_only', 'السند للعرض فقط حسب الصلاحيات أو الإعدادات.'))

    def _on_changed(self) -> None:
        self.set_dirty(True)
        title = self._title()
        self.set_document_title(title)
        self.title_label.setText(title)
        self._refresh_summary_panel()

    def _sync_type_visibility(self) -> None:
        self.link_panel.set_voucher_type(self.header_panel.voucher_type())
        self._refresh_summary_panel()

    def _title(self) -> str:
        voucher_type = self.header_panel.voucher_type() if hasattr(self, 'header_panel') else 'receipt'
        if self._last_saved_id:
            label = tr('receipt') if voucher_type == 'receipt' else tr('payment') if voucher_type == 'payment' else tr('expense')
            return f"{label} #{self._last_saved_id}"
        base = tr('receipt_voucher') if voucher_type == 'receipt' else tr('payment_voucher') if voucher_type == 'payment' else tr('expense')
        suffix = ' *' if self.is_dirty() else ''
        return f"{base}{suffix}"

    def _payload(self) -> dict:
        voucher_type = self.header_panel.voucher_type()
        data = {}
        data.update(self.header_panel.payload())
        data.update(self.link_panel.payload(voucher_type))
        data.update(self.payment_panel.payload())
        return data

    def _validate_payload(self, data: dict) -> bool:
        if data.get('type') == 'receipt' and not data.get('customer_id'):
            show_toast(tr('select_customer'), 'error', self)
            return False
        if data.get('type') == 'payment' and not data.get('supplier_id'):
            show_toast(tr('select_supplier'), 'error', self)
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
        voucher_type = self.header_panel.voucher_type()
        type_label = tr('receipt') if voucher_type == 'receipt' else tr('payment') if voucher_type == 'payment' else tr('expense')
        self.type_metric.set_value(type_label)
        try:
            self.amount_metric.set_value(_money(self.payment_panel.amount_usd()))
        except Exception:
            self.amount_metric.set_value(_money(0))
        try:
            invoice_id = self.link_panel.invoice_combo.currentData()
            remaining = self.link_panel._invoice_remaining_by_id.get(invoice_id, Decimal('0'))
            self.invoice_metric.set_value(_money(remaining))
        except Exception:
            self.invoice_metric.set_value(_money(0))
        try:
            self.method_metric.set_value(self.payment_panel.payment_method_combo.currentText())
            method = self.payment_panel.payment_method_combo.currentData() or 'cash'
            target = self.payment_panel.bank_combo.currentText() if method == 'bank' else self.payment_panel.cashbox_combo.currentText()
            self.target_metric.set_value(target or '-')
        except Exception:
            self.method_metric.set_value('-')
            self.target_metric.set_value('-')

    def workspace_save(self) -> None:
        try:
            finance_operation_policy.require(self._operation_for_save(), context='voucher:tab:save', payload={'id': self._last_saved_id})
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
            self.voucher = voucher_service.get(saved_id) or dict(data, id=saved_id)
            self.set_dirty(False)
            title = self._title()
            self.set_document_title(title)
            self.title_label.setText(title)
            self._refresh_summary_panel()
            self.saved.emit(saved_id)
        except Exception as exc:
            show_toast(str(exc), 'error', self)

    def _current_voucher_for_printing(self) -> Optional[dict]:
        voucher = dict(self.voucher or {})
        if self._last_saved_id:
            voucher = voucher_service.get(self._last_saved_id) or voucher
        if not voucher.get('id'):
            return None
        voucher['party_name'] = voucher_service.party_name(voucher)
        return voucher

    def workspace_print(self) -> None:
        try:
            finance_operation_policy.require(finance_operation_policy.OP_VOUCHER_PRINT, context='voucher:tab:print', payload={'id': self._last_saved_id})
        except PermissionError as exc:
            show_toast(tr(str(exc)) if str(exc) else tr('permission_denied'), 'error', self)
            return
        if self.is_dirty():
            reply = QMessageBox.question(
                self,
                tr('print_button'),
                tr('workspace.unsaved_close'),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
            self.workspace_save()
        voucher = self._current_voucher_for_printing()
        if not voucher:
            QMessageBox.information(self, tr('print_button'), tr('select_voucher_first'))
            return
        printing_service.voucher_preview(voucher, self)

    def workspace_export(self) -> None:
        try:
            finance_operation_policy.require(finance_operation_policy.OP_VOUCHER_PRINT, context='voucher:tab:export', payload={'id': self._last_saved_id})
        except PermissionError as exc:
            show_toast(tr(str(exc)) if str(exc) else tr('permission_denied'), 'error', self)
            return
        voucher = self._current_voucher_for_printing()
        if not voucher:
            QMessageBox.information(self, tr('print_button'), tr('select_voucher_first'))
            return
        printing_service.voucher_print(voucher, self)
