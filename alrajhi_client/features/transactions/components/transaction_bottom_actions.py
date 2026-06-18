from __future__ import annotations

from collections.abc import Callable, Iterable

from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QWidget

from ..i18n import tr


class TransactionBottomActions(QWidget):
    """Fixed bottom command bar for transaction documents."""

    def __init__(self, actions: Iterable[tuple[str, Callable]], parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        for text_key, callback in actions:
            button = QPushButton(tr(text_key), self)
            button.clicked.connect(callback)
            layout.addWidget(button)
        layout.addStretch(1)
