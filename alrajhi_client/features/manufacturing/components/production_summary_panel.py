# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal

from PyQt5.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout

from core.money_display_policy import format_quantity

from features.manufacturing.i18n import tr


class ProductionSummaryPanel(QFrame):
    """Compact summary for production order material availability."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('ProductionSummaryPanel')
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        title = QLabel(tr('manufacturing_production_summary'))
        title.setObjectName('PanelTitle')
        root.addWidget(title)
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        self.values = {}
        rows = [
            ('line_count', 'manufacturing_component_count'),
            ('required_qty', 'manufacturing_total_required_qty'),
            ('available_qty', 'manufacturing_total_available_qty'),
            ('shortage_qty', 'manufacturing_total_shortage_qty'),
            ('insufficient_count', 'manufacturing_insufficient_lines'),
        ]
        for r, (key, label_key) in enumerate(rows):
            label = QLabel(tr(label_key))
            value = QLabel()
            value.setObjectName('SummaryValue')
            grid.addWidget(label, r, 0)
            grid.addWidget(value, r, 1)
            self.values[key] = value
        root.addLayout(grid)
        root.addStretch(1)

    def update_summary(self, summary: dict | None) -> None:
        summary = summary or {}
        for key, label in self.values.items():
            value = summary.get(key, Decimal('0'))
            try:
                if key.endswith('count') or key == 'line_count':
                    label.setText(format_quantity(value, decimals=0))
                else:
                    label.setText(format_quantity(value, decimals=4))
            except Exception:
                label.setText(str(value or '0'))
