from __future__ import annotations

from decimal import Decimal

from PyQt5.QtCore import pyqtSignal, QSignalBlocker
from PyQt5.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..i18n import tr, html_bold


class TransactionTotalsPanel(QWidget):
    """Reusable invoice totals + payment summary panel."""

    paidChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.summary_frame = QFrame(self)
        self.summary_frame.setFrameShape(QFrame.StyledPanel)
        summary = QGridLayout(self.summary_frame)
        summary.setContentsMargins(10, 10, 10, 10)
        summary.setHorizontalSpacing(12)
        summary.setVerticalSpacing(6)
        summary.addWidget(QLabel(html_bold("transaction_totals_summary")), 0, 0, 1, 2)
        self.subtotal_label = QLabel("0.00")
        self.discount_label = QLabel("0.00")
        self.tax_label = QLabel("0.00")
        self.remaining_label = QLabel("0.00")
        self.net_total_label = QLabel("0.00")
        self._currency_code = None
        rows = [
            ("transaction_subtotal", self.subtotal_label),
            ("transaction_discount", self.discount_label),
            ("transaction_tax", self.tax_label),
            ("transaction_remaining", self.remaining_label),
            ("transaction_net_total", self.net_total_label),
        ]
        for row, (title_key, widget) in enumerate(rows, start=1):
            summary.addWidget(QLabel(tr(title_key)), row, 0)
            summary.addWidget(widget, row, 1)
        layout.addWidget(self.summary_frame)

        self.payment_frame = QFrame(self)
        self.payment_frame.setFrameShape(QFrame.StyledPanel)
        payment = QGridLayout(self.payment_frame)
        payment.setContentsMargins(10, 10, 10, 10)
        payment.setHorizontalSpacing(12)
        payment.setVerticalSpacing(6)
        payment.addWidget(QLabel(html_bold("transaction_payment")), 0, 0, 1, 2)
        self.payment_method_combo = QComboBox(self)
        self.payment_method_combo.addItem(tr("payment_cash"), "cash")
        self.payment_method_combo.addItem(tr("payment_card"), "card")
        self.payment_method_combo.addItem(tr("payment_bank_transfer"), "bank_transfer")
        self.payment_method_combo.addItem(tr("payment_credit"), "credit")
        self.paid_spin = QDoubleSpinBox(self)
        self.paid_spin.setMaximum(999999999.0)
        self.paid_spin.setDecimals(2)
        self.paid_spin.valueChanged.connect(self.paidChanged)
        payment.addWidget(QLabel(tr("transaction_payment_method")), 1, 0)
        payment.addWidget(self.payment_method_combo, 1, 1)
        payment.addWidget(QLabel(tr("transaction_paid")), 2, 0)
        payment.addWidget(self.paid_spin, 2, 1)
        quick = QHBoxLayout()
        self.pay_full_btn = QPushButton(tr("transaction_pay_full"), self)
        self.unpaid_btn = QPushButton(tr("transaction_unpaid"), self)
        quick.addWidget(self.pay_full_btn)
        quick.addWidget(self.unpaid_btn)
        payment.addLayout(quick, 3, 0, 1, 2)
        layout.addWidget(self.payment_frame)
        layout.addStretch(1)

    def set_currency(self, currency_code: str | None) -> None:
        """Apply the active display currency to labels and paid input.

        Transaction amounts shown in this panel are user-facing display-currency
        values.  Persistence converts them back to the system base currency.
        """
        self._currency_code = currency_code or None
        try:
            from currency import currency
            symbol = currency.get_currency_symbol(self._currency_code) if self._currency_code else ""
            self.paid_spin.setPrefix(f"{symbol} " if symbol else "")
            self.paid_spin.setDecimals(currency.get_currency_decimals())
        except Exception:
            pass

    def _money_text(self, value) -> str:
        try:
            amount = Decimal(str(value or 0))
            if self._currency_code:
                try:
                    from currency import currency
                    return currency.format_amount(amount, self._currency_code)
                except Exception:
                    pass
            return f"{amount:.2f}"
        except Exception:
            return "0.00"

    def paid_amount(self) -> Decimal:
        try:
            return Decimal(str(self.paid_spin.value() or 0))
        except Exception:
            return Decimal("0")

    def set_paid(self, value, emit: bool = False) -> None:
        blocker = None if emit else QSignalBlocker(self.paid_spin)
        try:
            self.paid_spin.setValue(float(Decimal(str(value or 0))))
        finally:
            del blocker

    def payment_method(self) -> str:
        return str(self.payment_method_combo.currentData() or "cash")

    def set_payment_method(self, method: str | None) -> None:
        if not method:
            return
        for index in range(self.payment_method_combo.count()):
            if str(self.payment_method_combo.itemData(index)) == str(method):
                self.payment_method_combo.setCurrentIndex(index)
                return

    def set_totals(self, subtotal, discount, tax, paid, remaining, net_total) -> None:
        self.subtotal_label.setText(self._money_text(subtotal))
        self.discount_label.setText(self._money_text(discount))
        self.tax_label.setText(self._money_text(tax))
        self.remaining_label.setText(self._money_text(remaining))
        self.net_total_label.setText(self._money_text(net_total))

    def mark_paid_full(self, total) -> None:
        self.set_paid(total, emit=True)
        self.paidChanged.emit()

    def mark_unpaid(self) -> None:
        self.set_paid(0, emit=True)
        self.paidChanged.emit()
