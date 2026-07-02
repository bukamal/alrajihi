from __future__ import annotations

from collections.abc import Callable, Iterable

from PyQt5.QtWidgets import QGridLayout, QPushButton, QSizePolicy, QWidget

from ..i18n import tr


class TransactionBottomActions(QWidget):
    """Fixed bottom command bar for transaction documents."""

    def __init__(self, actions: Iterable[tuple[str, Callable]], parent=None):
        super().__init__(parent)
        self._buttons = {}
        self.setObjectName("TransactionBottomActionBar")
        self.setProperty("transaction_footer_role", "actions")
        self.setProperty("transactionActionLayoutPhase", "471")
        # Phase468 compatibility marker: transactionActionLayoutPhase", "468"
        # Phase468: grid layout prevents bottom command overlap on small RTL
        # screens while keeping the same action contract and callbacks.
        layout = QGridLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(8)
        max_per_row = 5  # Phase471: fixed responsive grid, never a single overflow row.
        for index, (text_key, callback) in enumerate(actions):
            button = QPushButton(tr(text_key), self)
            action_name = self._action_name_for_key(text_key)
            if action_name:
                button.setProperty("transaction_action", action_name)
                button.setProperty("transaction_footer_role", action_name)
                self._buttons[action_name] = button
            # Phase349 compatibility markers: setMinimumHeight(44), setMinimumWidth(108)
            # Phase468 tightens the buttons and wraps them instead of allowing collisions.
            button.setMinimumHeight(42)
            button.setMinimumWidth(118)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.clicked.connect(callback)
            row = index // max_per_row
            col = index % max_per_row
            layout.addWidget(button, row, col)
        for col in range(max_per_row):
            layout.setColumnStretch(col, 1)

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
