# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QComboBox, QDoubleSpinBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QSizePolicy, QToolButton, QWidget

from core.services.cashbox_service import cashbox_service
from currency import currency
from i18n import qt_layout_direction, translate as tr
from ui.inline_quick_create import InlineQuickCreatePanel, quick_create_can


def _field_label(text: str, parent: QWidget) -> QLabel:
    label = QLabel(text if str(text).endswith(':') else f"{text}:", parent)
    label.setObjectName('FieldLabel')
    label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    return label


class VoucherPaymentPanel(QWidget):
    """Amount and cash/bank target panel for vouchers.

    Phase461 connects the payment targets to the unified inline quick-create
    system: new cashboxes and bank accounts can be created/selected inline from
    vouchers and expense documents without opening dialogs or tabs.
    """

    changed = pyqtSignal()

    def __init__(self, parent=None, voucher=None) -> None:
        super().__init__(parent)
        self.setObjectName('VoucherPaymentPanel')
        self.setProperty('phase461InlineQuickCreateHost', True)
        self.setLayoutDirection(qt_layout_direction())
        self._field_labels: dict[str, QLabel] = {}

        layout = QGridLayout(self)
        self._layout = layout
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(8)
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 0)
        layout.setColumnStretch(3, 1)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setObjectName('voucher_amount_spin')
        self.amount_spin.setRange(0, 99999999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setAlignment(Qt.AlignRight)

        self.payment_method_combo = QComboBox()
        self.payment_method_combo.setObjectName('voucher_payment_method_combo')
        self.payment_method_combo.addItem(tr('cash'), 'cash')
        self.payment_method_combo.addItem(tr('bank_payment'), 'bank')

        self.cashbox_combo = QComboBox()
        self.cashbox_combo.setObjectName('voucher_cashbox_combo')
        self._reload_cashboxes()

        self.bank_combo = QComboBox()
        self.bank_combo.setObjectName('voucher_bank_combo')
        self._reload_bank_accounts()

        for widget in (self.amount_spin, self.payment_method_combo, self.cashbox_combo, self.bank_combo):
            widget.setMinimumHeight(30)
            widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.quick_cashbox_btn = self._quick_button('cashbox', tr('inline_quick_create_cashbox_tooltip'))
        self.quick_bank_btn = self._quick_button('bank_account', tr('inline_quick_create_bank_account_tooltip'))
        self.quick_cashbox_btn.clicked.connect(lambda *_: self.quick_cashbox_panel.toggle_panel())
        self.quick_bank_btn.clicked.connect(lambda *_: self.quick_bank_panel.toggle_panel())
        self.cashbox_field = self._combo_with_inline_button('VoucherCashboxInlineCreateField', self.cashbox_combo, self.quick_cashbox_btn)
        self.bank_field = self._combo_with_inline_button('VoucherBankInlineCreateField', self.bank_combo, self.quick_bank_btn)

        self._add_pair(layout, 'amount', 0, 0, tr('amount_label'), self.amount_spin)
        self._add_pair(layout, 'method', 0, 2, tr('payment_method_label'), self.payment_method_combo)
        self._add_pair(layout, 'cashbox', 1, 0, tr('cashbox'), self.cashbox_field)
        self._add_pair(layout, 'bank', 1, 2, tr('bank_account'), self.bank_field)

        self.quick_cashbox_panel = InlineQuickCreatePanel('cashbox', self)
        self.quick_cashbox_panel.setObjectName('VoucherInlineQuickCashboxPanel')
        self.quick_cashbox_panel.created.connect(self._on_inline_payment_target_created)
        self.quick_cashbox_panel.setVisible(False)
        layout.addWidget(self.quick_cashbox_panel, 2, 0, 1, 4)

        self.quick_bank_panel = InlineQuickCreatePanel('bank_account', self)
        self.quick_bank_panel.setObjectName('VoucherInlineQuickBankAccountPanel')
        self.quick_bank_panel.created.connect(self._on_inline_payment_target_created)
        self.quick_bank_panel.setVisible(False)
        layout.addWidget(self.quick_bank_panel, 3, 0, 1, 4)

        self.amount_spin.valueChanged.connect(lambda *_: self.changed.emit())
        self.payment_method_combo.currentIndexChanged.connect(lambda *_: (self.update_payment_visibility(), self.changed.emit()))
        self.cashbox_combo.currentIndexChanged.connect(lambda *_: self.changed.emit())
        self.bank_combo.currentIndexChanged.connect(lambda *_: self.changed.emit())

        self._refresh_inline_create_state()
        if isinstance(voucher, dict):
            self.load(voucher)
        self.update_payment_visibility()

    def _quick_button(self, entity: str, tooltip: str) -> QToolButton:
        button = QToolButton(self)
        button.setObjectName(f'VoucherInlineQuick{entity.title().replace("_", "")}Button')
        button.setProperty('visualRole', 'document_inline_create_action')
        button.setProperty('quickCreateEntity', entity)
        button.setText('+')
        button.setToolTip(tooltip)
        return button

    def _combo_with_inline_button(self, object_name: str, combo: QComboBox, button: QToolButton) -> QFrame:
        frame = QFrame(self)
        frame.setObjectName(object_name)
        frame.setProperty('voucherInlineQuickCreateField', True)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(combo, 1)
        layout.addWidget(button)
        return frame

    def _refresh_inline_create_state(self) -> None:
        for entity, button in (('cashbox', self.quick_cashbox_btn), ('bank_account', self.quick_bank_btn)):
            allowed = quick_create_can(entity)
            button.setEnabled(allowed)
            button.setToolTip(tr(f'inline_quick_create_{entity}_tooltip') if allowed else tr('inline_quick_create_permission_denied'))

    def _reload_cashboxes(self, select_id=None) -> None:
        current = select_id if select_id is not None else self.cashbox_combo.currentData() if hasattr(self, 'cashbox_combo') else None
        self.cashbox_combo.blockSignals(True)
        self.cashbox_combo.clear()
        try:
            cashboxes = cashbox_service.cashboxes()
        except Exception:
            cashboxes = []
        for box in cashboxes:
            label = f"{box.get('branch_name','')} - {box.get('name','')}".strip(' -')
            self.cashbox_combo.addItem(label, box.get('id'))
        if current is not None:
            idx = self.cashbox_combo.findData(current)
            if idx >= 0:
                self.cashbox_combo.setCurrentIndex(idx)
        self.cashbox_combo.blockSignals(False)

    def _reload_bank_accounts(self, select_id=None) -> None:
        current = select_id if select_id is not None else self.bank_combo.currentData() if hasattr(self, 'bank_combo') else None
        self.bank_combo.blockSignals(True)
        self.bank_combo.clear()
        self.bank_combo.addItem(tr('select_bank_account_placeholder'), None)
        try:
            banks = cashbox_service.bank_accounts()
        except Exception:
            banks = []
        for bank in banks:
            label = f"{bank.get('branch_name','')} - {bank.get('bank_name','')} {bank.get('account_name') or ''}".strip(' -')
            self.bank_combo.addItem(label, bank.get('id'))
        if current is not None:
            idx = self.bank_combo.findData(current)
            if idx >= 0:
                self.bank_combo.setCurrentIndex(idx)
        self.bank_combo.blockSignals(False)

    def _on_inline_payment_target_created(self, entity_type: str, result: dict) -> None:
        target_id = result.get('id')
        if entity_type == 'cashbox':
            self._reload_cashboxes(target_id)
            idx = self.cashbox_combo.findData(target_id)
            if idx >= 0:
                self.cashbox_combo.setCurrentIndex(idx)
        elif entity_type == 'bank_account':
            self._reload_bank_accounts(target_id)
            idx = self.bank_combo.findData(target_id)
            if idx >= 0:
                self.bank_combo.setCurrentIndex(idx)
        else:
            return
        self.changed.emit()

    def _add_pair(self, layout: QGridLayout, key: str, row: int, col: int, label_text: str, widget: QWidget) -> None:
        label = _field_label(label_text, self)
        self._field_labels[key] = label
        layout.addWidget(label, row, col)
        layout.addWidget(widget, row, col + 1)

    def _set_field_visible(self, key: str, widget: QWidget, visible: bool) -> None:
        label = self._field_labels.get(key)
        if label is not None:
            label.setVisible(visible)
        widget.setVisible(visible)

    def update_payment_visibility(self) -> None:
        is_bank = self.payment_method_combo.currentData() == 'bank'
        self._set_field_visible('bank', self.bank_field, is_bank)
        self._set_field_visible('cashbox', self.cashbox_field, not is_bank)
        if is_bank:
            self.quick_cashbox_panel.setVisible(False)
        else:
            self.quick_bank_panel.setVisible(False)

    def load(self, voucher: dict) -> None:
        try:
            amount_display = currency.to_display(Decimal(str(voucher.get('amount') or 0)))
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
            display_amount = currency.to_display(amount)
            self.amount_spin.setValue(float(display_amount))
        except Exception:
            self.amount_spin.setValue(float(amount))

    def amount_usd(self) -> Decimal:
        amount_display = Decimal(str(self.amount_spin.value()))
        return currency.from_display(amount_display)

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
