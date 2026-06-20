# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal

from PyQt5.QtWidgets import QFrame, QGridLayout, QLabel

from core.money_display_policy import format_money, format_quantity

from features.manufacturing.i18n import tr


class ProductionLifecycleSummaryPanel(QFrame):
    """Compact lifecycle summary panel for a production order."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('ProductionLifecycleSummaryPanel')
        layout = QGridLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(8)
        self.title = QLabel(tr('manufacturing_lifecycle_summary'))
        self.title.setObjectName('PanelTitle')
        layout.addWidget(self.title, 0, 0, 1, 2)
        self.values = {}
        for row, key in enumerate(['reserved', 'consumed', 'remaining', 'produced', 'consumption_cost', 'output_cost'], start=1):
            label = QLabel(tr(f'manufacturing_summary_{key}'))
            value = QLabel()
            value.setObjectName('SummaryValue')
            layout.addWidget(label, row, 0)
            layout.addWidget(value, row, 1)
            self.values[key] = value
            value.setText(str(0))

    def update_summary(self, *, reservations=None, consumptions=None, outputs=None) -> None:
        reservations = reservations or {}
        consumptions = consumptions or {}
        outputs = outputs or {}
        self._set('reserved', reservations.get('qty', reservations.get('reserved_qty', Decimal('0'))))
        self._set('consumed', consumptions.get('qty', Decimal('0')))
        self._set('remaining', reservations.get('remaining_qty', Decimal('0')))
        self._set('produced', outputs.get('qty', Decimal('0')))
        self._set('consumption_cost', consumptions.get('total_cost', Decimal('0')))
        self._set('output_cost', outputs.get('total_cost', Decimal('0')))

    def _set(self, key: str, value) -> None:
        try:
            if key in {'consumption_cost', 'output_cost'}:
                text = format_money(value)
            else:
                text = format_quantity(value, decimals=4)
        except Exception:
            text = str(value or '0')
        self.values[key].setText(text)
