# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QComboBox, QDoubleSpinBox, QFormLayout, QWidget

from core.services.cashbox_service import cashbox_service
from currency import currency
from i18n import translate as tr


class VoucherPaymentPanel(QWidget):
    """Amount and cash/bank target panel for vouchers."""

    changed = pyqtSignal()

    def __init__(self, parent=None, voucher=None) -> None:
        super().__init__(parent)
        layout = QFormLayout(self)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 99999999)
        self.amount_spin.setDecimals(2)
        layout.addRow(tr('amount_label'), self.amount_spin)

        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItem(tr('cash'), 'cash')
        self.payment_method_combo.addItem(tr('bank_payment'), 'bank')
        layout.addRow(tr('payment_method_label'), self.payment_method_combo)

        self.cashbox_combo = QComboBox()
        try:
            cashboxes = cashbox_service.cashboxes()
        except Exception:
            cashboxes = []
        for box in cashboxes:
            label = f"{box.get('branch_name','')} - {box.get('name','')}"
            self.cashbox_combo.addItem(label, box.get('id'))
        layout.addRow(tr('cashbox') + ':', self.cashbox_combo)

        self.bank_combo = QComboBox()
        self.bank_combo.addItem(tr('select_bank_account_placeholder'), None)
        try:
            banks = cashbox_service.bank_accounts()
        except Exception:
            banks = []
        for bank in banks:
            label = f"{bank.get('branch_name','')} - {bank.get('bank_name','')} {bank.get('account_name') or ''}"
            self.bank_combo.addItem(label, bank.get('id'))
        layout.addRow(tr('bank_account') + ':', self.bank_combo)

        self.amount_spin.valueChanged.connect(lambda *_: self.changed.emit())
        self.payment_method_combo.currentIndexChanged.connect(lambda *_: (self.update_payment_visibility(), self.changed.emit()))
        self.cashbox_combo.currentIndexChanged.connect(lambda *_: self.changed.emit())
        self.bank_combo.currentIndexChanged.connect(lambda *_: self.changed.emit())

        if isinstance(voucher, dict):
            self.load(voucher)
        self.update_payment_visibility()

    def update_payment_visibility(self) -> None:
        is_bank = self.payment_method_combo.currentData() == 'bank'
        self.bank_combo.setVisible(is_bank)
        self.cashbox_combo.setVisible(not is_bank)

    def load(self, voucher: dict) -> None:
        try:
            amount_display = currency.convert(Decimal(str(voucher.get('amount') or 0)), 'USD', currency.get_display_currency())
        except Exception:
            amount_display = Decimal('0')
        self.amount_spin.setValue(float(amount_display))
        method = voucher.get('payment_method') or 'cash'
        idx = self.payment_method_combo.findData(method)
        if idx >= 0:
            self.payment_method_combo.setCurrentIndex(idx)
        if voucher.get('cashbox_id'):
            idx = self.cashbox_combo.findData(voucher.get('cashbox_id'))
            if idx >= 0:
                self.cashbox_combo.setCurrentIndex(idx)
        if voucher.get('bank_account_id'):
            idx = self.bank_combo.findData(voucher.get('bank_account_id'))
            if idx >= 0:
                self.bank_combo.setCurrentIndex(idx)

    def set_amount_usd(self, amount: Decimal) -> None:
        try:
            display_amount = currency.convert(amount, 'USD', currency.get_display_currency())
            self.amount_spin.setValue(float(display_amount))
        except Exception:
            self.amount_spin.setValue(float(amount))

    def amount_usd(self) -> Decimal:
        amount_display = Decimal(str(self.amount_spin.value()))
        return currency.convert(amount_display, currency.get_display_currency(), 'USD')

    def payload(self) -> dict:
        method = self.payment_method_combo.currentData() or 'cash'
        return {
            'amount': self.amount_usd(),
            'exchange_rate_to_usd': float(currency.get_current_rate(currency.get_display_currency())),
            'original_currency': currency.get_display_currency(),
            'payment_method': method,
            'cashbox_id': self.cashbox_combo.currentData() if method == 'cash' else None,
            'bank_account_id': self.bank_combo.currentData() if method == 'bank' else None,
        }
