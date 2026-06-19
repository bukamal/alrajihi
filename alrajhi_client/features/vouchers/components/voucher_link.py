# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QComboBox, QFormLayout, QWidget

from core.services.catalog_service import catalog_service
from core.services.invoice_service import invoice_service
from currency import currency
from i18n import translate as tr
from offline_read import is_offline_read_error, notify_offline_read


class VoucherLinkPanel(QWidget):
    """Party and invoice linkage for receipt/payment vouchers."""

    changed = pyqtSignal()
    remainingSelected = pyqtSignal(object)

    def __init__(self, parent=None, voucher=None) -> None:
        super().__init__(parent)
        self.voucher = voucher or {}
        self._invoice_remaining_by_id: dict[int, Decimal] = {}
        self._loading = False

        layout = QFormLayout(self)
        self.customer_combo = QComboBox()
        self.customer_combo.addItem(tr('no_customer'), None)
        for customer in self._safe_customers():
            self.customer_combo.addItem(customer.get('name', ''), customer.get('id'))
        layout.addRow(tr('customer_label'), self.customer_combo)

        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem(tr('no_supplier'), None)
        for supplier in self._safe_suppliers():
            self.supplier_combo.addItem(supplier.get('name', ''), supplier.get('id'))
        layout.addRow(tr('supplier_label'), self.supplier_combo)

        self.invoice_combo = QComboBox()
        self.invoice_combo.addItem(tr('no_invoice'), None)
        layout.addRow(tr('invoice_label'), self.invoice_combo)

        self.customer_combo.currentIndexChanged.connect(lambda *_: (self.update_invoice_list(), self.changed.emit()))
        self.supplier_combo.currentIndexChanged.connect(lambda *_: (self.update_invoice_list(), self.changed.emit()))
        self.invoice_combo.currentIndexChanged.connect(lambda *_: (self._emit_remaining(), self.changed.emit()))

        if isinstance(voucher, dict):
            self.load(voucher)

    def _safe_customers(self):
        try:
            return catalog_service.customers(limit=1000)
        except Exception as exc:
            if is_offline_read_error(exc):
                notify_offline_read(self, tr('customer_voucher_list'))
                return []
            raise

    def _safe_suppliers(self):
        try:
            return catalog_service.suppliers(limit=1000)
        except Exception as exc:
            if is_offline_read_error(exc):
                notify_offline_read(self, tr('supplier_voucher_list'))
                return []
            raise

    def load(self, voucher: dict) -> None:
        self._loading = True
        if voucher.get('customer_id'):
            idx = self.customer_combo.findData(voucher.get('customer_id'))
            if idx >= 0:
                self.customer_combo.setCurrentIndex(idx)
        if voucher.get('supplier_id'):
            idx = self.supplier_combo.findData(voucher.get('supplier_id'))
            if idx >= 0:
                self.supplier_combo.setCurrentIndex(idx)
        self._loading = False

    def set_voucher_type(self, voucher_type: str) -> None:
        is_receipt = voucher_type == 'receipt'
        is_payment = voucher_type == 'payment'
        self.customer_combo.setVisible(is_receipt)
        self.supplier_combo.setVisible(is_payment)
        self.invoice_combo.setVisible(is_receipt or is_payment)
        self.update_invoice_list(voucher_type)

    def _voucher_old_amount_for_invoice(self, invoice_id) -> Decimal:
        if not self.voucher or self.voucher.get('invoice_id') != invoice_id:
            return Decimal('0')
        try:
            return Decimal(str(self.voucher.get('amount') or 0))
        except Exception:
            return Decimal('0')

    def _add_invoice_option(self, inv: dict) -> None:
        try:
            inv_id = inv.get('id')
            remaining = Decimal(str(inv.get('total', 0))) - Decimal(str(inv.get('paid', 0))) + self._voucher_old_amount_for_invoice(inv_id)
        except Exception:
            remaining = Decimal('0')
        if remaining <= 0:
            return
        self._invoice_remaining_by_id[inv_id] = remaining
        amount_label = currency.format_base_amount(remaining)
        self.invoice_combo.addItem(tr('remaining_invoice_amount', reference=inv.get('reference', inv_id), amount=amount_label), inv_id)

    def update_invoice_list(self, voucher_type: str | None = None) -> None:
        voucher_type = voucher_type or self._infer_type()
        entity_id = self.customer_combo.currentData() if voucher_type == 'receipt' else self.supplier_combo.currentData() if voucher_type == 'payment' else None
        self.invoice_combo.blockSignals(True)
        self.invoice_combo.clear()
        self._invoice_remaining_by_id = {}
        self.invoice_combo.addItem(tr('no_invoice'), None)
        if entity_id:
            invoices = invoice_service.unpaid_invoices(
                inv_type='sale' if voucher_type == 'receipt' else 'purchase',
                customer_id=entity_id if voucher_type == 'receipt' else None,
                supplier_id=entity_id if voucher_type == 'payment' else None,
                limit=100,
            )
            seen = set()
            for inv in invoices:
                seen.add(inv.get('id'))
                self._add_invoice_option(inv)
            current_invoice_id = self.voucher.get('invoice_id') if self.voucher else None
            if current_invoice_id and current_invoice_id not in seen:
                current = invoice_service.get(current_invoice_id)
                if current:
                    self._add_invoice_option(current)
        self.invoice_combo.blockSignals(False)
        if self.voucher.get('invoice_id'):
            idx = self.invoice_combo.findData(self.voucher.get('invoice_id'))
            if idx >= 0:
                self.invoice_combo.setCurrentIndex(idx)
        self._emit_remaining()

    def _infer_type(self) -> str:
        if self.customer_combo.currentData():
            return 'receipt'
        if self.supplier_combo.currentData():
            return 'payment'
        return 'expense'

    def _emit_remaining(self) -> None:
        if self._loading:
            return
        invoice_id = self.invoice_combo.currentData()
        remaining = self._invoice_remaining_by_id.get(invoice_id)
        if remaining and remaining > 0:
            self.remainingSelected.emit(remaining)

    def payload(self, voucher_type: str) -> dict:
        return {
            'customer_id': self.customer_combo.currentData() if voucher_type == 'receipt' else None,
            'supplier_id': self.supplier_combo.currentData() if voucher_type == 'payment' else None,
            'invoice_id': self.invoice_combo.currentData() or None,
        }
