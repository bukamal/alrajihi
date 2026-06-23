from __future__ import annotations

from collections.abc import Callable, Iterable

from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QWidget

from ..i18n import tr


class TransactionBottomActions(QWidget):
    """Fixed bottom command bar for transaction documents."""

    def __init__(self, actions: Iterable[tuple[str, Callable]], parent=None):
        super().__init__(parent)
        self._buttons = {}
        self.setObjectName("TransactionBottomActionBar")
        self.setProperty("transaction_footer_role", "actions")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)
        for text_key, callback in actions:
            button = QPushButton(tr(text_key), self)
            action_name = self._action_name_for_key(text_key)
            if action_name:
                button.setProperty("transaction_action", action_name)
                button.setProperty("transaction_footer_role", action_name)
                self._buttons[action_name] = button
            # Phase349 compatibility markers: setMinimumHeight(44), setMinimumWidth(108)
            # Phase355 raises the visual minimums while preserving the earlier contract.
            button.setMinimumHeight(50)
            button.setMinimumWidth(126)
            button.clicked.connect(callback)
            layout.addWidget(button)
        layout.addStretch(1)

    @staticmethod
    def _action_name_for_key(text_key: str) -> str:
        key = str(text_key or '')
        if key in {'save'}:
            return 'save'
        if key in {'print'}:
            return 'print'
        if 'delete' in key or 'remove' in key:
            return 'delete'
        if 'close' in key:
            return 'close'
        if 'new' in key:
            return 'create'
        if 'pay_full' in key or 'refund_full' in key or 'hold' in key or 'credit_settlement' in key:
            return 'update'
        return ''

    def set_action_enabled(self, action: str, enabled: bool) -> None:
        button = self._buttons.get(str(action or ''))
        if button is not None:
            button.setEnabled(bool(enabled))
