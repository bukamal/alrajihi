from __future__ import annotations

from decimal import Decimal

from PyQt5.QtCore import Qt, pyqtSignal, QSignalBlocker
from PyQt5.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QSizePolicy,
    QWidget,
)

from ..i18n import tr, html_bold
from core.money_display_policy import policy_for


class TransactionTotalsPanel(QWidget):
    """Reusable invoice totals + payment summary panel."""

    paidChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # Phase326: the footer summary is an inline operational strip.  The old
        # vertical cards consumed too much height below the invoice grid and made
        # the purchase/sales footer feel crowded in RTL layouts.
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.summary_frame = QFrame(self)
        self.summary_frame.setFrameShape(QFrame.StyledPanel)
        self.summary_frame.setObjectName("TransactionHorizontalSummaryFrame")
        self.summary_frame.setProperty("transaction_footer_role", "summary")
        self.summary_frame.setProperty("basitPanel", True)
        self.summary_frame.setProperty("basitTransactionSummary", True)
        self.summary_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        summary = QGridLayout(self.summary_frame)
        summary.setContentsMargins(8, 6, 8, 6)
        summary.setHorizontalSpacing(10)
        summary.setVerticalSpacing(3)
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
        title_label = QLabel(html_bold("transaction_totals_summary"))
        title_label.setObjectName("TransactionSummaryCaption")
        title_label.setAlignment(Qt.AlignCenter)
        summary.addWidget(title_label, 0, 0, 2, 1)
        for col, (title_key, widget) in enumerate(rows, start=1):
            caption = QLabel(tr(title_key))
            caption.setObjectName("TransactionSummaryCaption")
            caption.setProperty("transaction_footer_role", "caption")
            caption.setAlignment(Qt.AlignCenter)
            widget.setObjectName("TransactionSummaryValue")
            widget.setProperty("transaction_footer_role", "value")
            widget.setProperty("basitTotal", title_key == "transaction_net_total")
            widget.setAlignment(Qt.AlignCenter) if hasattr(widget, "setAlignment") else None
            summary.addWidget(caption, 0, col)
            summary.addWidget(widget, 1, col)
            summary.setColumnStretch(col, 1)
        layout.addWidget(self.summary_frame, 5)

        self.payment_frame = QFrame(self)
        self.payment_frame.setFrameShape(QFrame.StyledPanel)
        self.payment_frame.setObjectName("TransactionHorizontalPaymentFrame")
        self.payment_frame.setProperty("transaction_footer_role", "payment")
        self.payment_frame.setProperty("basitPanel", True)
        self.payment_frame.setProperty("basitTransactionPayment", True)
        self.payment_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        payment = QHBoxLayout(self.payment_frame)
        payment.setContentsMargins(8, 6, 8, 6)
        payment.setSpacing(6)
        payment_title = QLabel(html_bold("transaction_payment"))
        payment_title.setObjectName("TransactionPaymentCaption")
        payment_title.setProperty("transaction_footer_role", "caption")
        payment.addWidget(payment_title)
        payment_method_label = QLabel(tr("transaction_payment_method"))
        payment_method_label.setObjectName("TransactionPaymentCaption")
        payment_method_label.setProperty("transaction_footer_role", "caption")
        payment.addWidget(payment_method_label)
        self.payment_method_combo = QComboBox(self)
        self.payment_method_combo.addItem(tr("payment_cash"), "cash")
        self.payment_method_combo.addItem(tr("payment_card"), "card")
        self.payment_method_combo.addItem(tr("payment_bank_transfer"), "bank_transfer")
        self.payment_method_combo.addItem(tr("payment_credit"), "credit")
        self.payment_method_combo.setMaximumWidth(132)
        payment.addWidget(self.payment_method_combo)
        self.paid_spin = QDoubleSpinBox(self)
        self.paid_spin.setMaximum(999999999.0)
        self.paid_spin.setDecimals(2)
        self.paid_spin.valueChanged.connect(self.paidChanged)
        self.paid_title_label = QLabel(tr("transaction_paid"))
        self.paid_title_label.setObjectName("TransactionPaymentCaption")
        self.paid_title_label.setProperty("transaction_footer_role", "caption")
        payment.addWidget(self.paid_title_label)
        payment.addWidget(self.paid_spin)
        self.pay_full_btn = QPushButton(tr("transaction_pay_full"), self)
        self.unpaid_btn = QPushButton(tr("transaction_unpaid"), self)
        self.pay_full_btn.setProperty("basitToolbarButton", True)
        self.unpaid_btn.setProperty("basitToolbarButton", True)
        self.pay_full_btn.setObjectName("TransactionFooterMiniButton")
        self.unpaid_btn.setObjectName("TransactionFooterMiniButton")
        self.pay_full_btn.setMinimumWidth(98)
        self.unpaid_btn.setMinimumWidth(98)
        self.pay_full_btn.setMaximumWidth(128)
        self.unpaid_btn.setMaximumWidth(128)
        payment.addWidget(self.pay_full_btn)
        payment.addWidget(self.unpaid_btn)
        layout.addWidget(self.payment_frame, 3)



    def set_transaction_type(self, transaction_type: str | None) -> None:
        """Use user-facing payment wording that matches the document direction."""
        key = "transaction_paid" if str(transaction_type or "sale") == "purchase" else "transaction_received"
        try:
            self.paid_title_label.setText(tr(key))
        except Exception:
            pass

    def set_currency(self, currency_code: str | None) -> None:
        """Apply the active display currency to labels and paid input.

        Transaction amounts shown in this panel are user-facing display-currency
        values.  Persistence converts them back to the system base currency.
        """
        self._currency_code = currency_code or None
        try:
            policy = policy_for(currency_code=self._currency_code)
            symbol = policy.currency_symbol if self._currency_code else ""
            self.paid_spin.setPrefix(f"{symbol} " if symbol else "")
            self.paid_spin.setDecimals(policy.decimals)
        except Exception:
            pass

    def _money_text(self, value) -> str:
        try:
            return policy_for(currency_code=self._currency_code).format_money(value)
        except Exception:
            try:
                amount = Decimal(str(value or 0))
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
