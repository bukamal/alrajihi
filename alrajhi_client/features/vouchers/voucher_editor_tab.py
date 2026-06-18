# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Optional

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QMessageBox

from core.services.voucher_service import voucher_service
from core.services.finance_operation_policy import finance_operation_policy
from features.vouchers.components import VoucherActionsPanel, VoucherHeaderPanel, VoucherLinkPanel, VoucherPaymentPanel
from i18n import translate as tr
from printing.printing_service import printing_service
from utils import show_toast
from workspace.documents import BaseDocumentTab


class VoucherEditorTab(BaseDocumentTab):
    """Receipt/payment/expense voucher as a first-class workspace document tab.

    This replaces the legacy modal voucher adapter with decomposed panels:
    header, party/invoice linkage, payment target, and actions.  Persistence stays
    behind VoucherService and all printing goes through UnifiedPrintingService.
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
        self.actions_panel = VoucherActionsPanel(self)

        self._build_layout()
        self._connect_signals()
        self._sync_type_visibility()
        self._apply_operation_state()
        self.set_document_title(self._title())
        self.set_dirty(False)

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        for panel in (self.header_panel, self.link_panel, self.payment_panel):
            frame = QFrame()
            frame.setObjectName('documentSection')
            frame_layout = QVBoxLayout(frame)
            frame_layout.setContentsMargins(12, 12, 12, 12)
            frame_layout.addWidget(panel)
            layout.addWidget(frame)
        layout.addStretch()
        layout.addWidget(self.actions_panel)

    def _connect_signals(self) -> None:
        self.header_panel.changed.connect(self._on_changed)
        self.link_panel.changed.connect(self._on_changed)
        self.payment_panel.changed.connect(self._on_changed)
        self.header_panel.type_combo.currentIndexChanged.connect(lambda *_: self._sync_type_visibility())
        self.link_panel.remainingSelected.connect(self.payment_panel.set_amount_usd)
        self.actions_panel.saveRequested.connect(self.workspace_save)
        self.actions_panel.printRequested.connect(self.workspace_print)


    def _operation_for_save(self) -> str:
        return finance_operation_policy.OP_VOUCHER_EDIT if self.is_edit else finance_operation_policy.OP_VOUCHER_CREATE

    def _apply_operation_state(self) -> None:
        can_save = finance_operation_policy.can(self._operation_for_save())
        can_print = finance_operation_policy.can(finance_operation_policy.OP_VOUCHER_PRINT)
        for panel in (self.header_panel, self.link_panel, self.payment_panel):
            panel.setEnabled(can_save)
        if hasattr(self.actions_panel, 'save_btn'):
            self.actions_panel.save_btn.setEnabled(can_save)
        if hasattr(self.actions_panel, 'print_btn'):
            self.actions_panel.print_btn.setEnabled(can_print)
        if not can_save:
            self.setToolTip(tr('voucher_read_only'))

    def _on_changed(self) -> None:
        self.set_dirty(True)
        self.set_document_title(self._title())

    def _sync_type_visibility(self) -> None:
        self.link_panel.set_voucher_type(self.header_panel.voucher_type())

    def _title(self) -> str:
        if self._last_saved_id:
            label = tr('receipt') if self.header_panel.voucher_type() == 'receipt' else tr('payment') if self.header_panel.voucher_type() == 'payment' else tr('expense')
            return f"{label} #{self._last_saved_id}"
        label = tr('new_voucher')
        suffix = ' *' if self.is_dirty() else ''
        return f"{label}{suffix}"

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
            self.set_document_title(self._title())
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
        printing_service.voucher_pdf(voucher, self)
