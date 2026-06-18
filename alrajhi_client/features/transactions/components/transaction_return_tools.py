from __future__ import annotations

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

from ..i18n import tr


class TransactionReturnTools(QWidget):
    """Compact return workflow toolbar for TransactionDocumentTab."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.frame = QFrame(self)
        self.frame.setFrameShape(QFrame.StyledPanel)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.frame)

        row = QHBoxLayout(self.frame)
        row.setContentsMargins(8, 6, 8, 6)
        row.setSpacing(8)

        self.load_btn = QPushButton(tr("transaction_load_invoice_lines"), self.frame)
        self.fill_all_btn = QPushButton(tr("transaction_return_fill_all"), self.frame)
        self.clear_btn = QPushButton(tr("transaction_return_clear_qty"), self.frame)
        self.summary_label = QLabel(tr("ready"), self.frame)
        self.summary_label.setMinimumWidth(260)

        row.addWidget(QLabel(tr("transaction_return_tools_label")), 0)
        row.addWidget(self.load_btn, 0)
        row.addWidget(self.fill_all_btn, 0)
        row.addWidget(self.clear_btn, 0)
        row.addWidget(self.summary_label, 1)

    def set_summary(self, selected_qty, returnable_qty, selected_total) -> None:
        self.summary_label.setText(
            tr(
                "transaction_return_summary",
                selected=self._fmt(selected_qty),
                returnable=self._fmt(returnable_qty),
                amount=self._money(selected_total),
            )
        )

    def set_message(self, text: str) -> None:
        self.summary_label.setText(text or "")

    def _fmt(self, value) -> str:
        try:
            value = float(value or 0)
            if value.is_integer():
                return str(int(value))
            return f"{value:.3f}".rstrip("0").rstrip(".")
        except Exception:
            return "0"

    def _money(self, value) -> str:
        try:
            return f"{float(value or 0):.2f}"
        except Exception:
            return "0.00"
