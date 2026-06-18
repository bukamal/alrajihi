# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal

from PyQt5.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout

from features.manufacturing.i18n import tr


class BomSummaryPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('BomSummaryPanel')
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        title = QLabel(tr('manufacturing_bom_cost_summary'))
        title.setObjectName('PanelTitle')
        root.addWidget(title)
        grid = QGridLayout()
        root.addLayout(grid)
        self.material_cost_label = QLabel()
        self.waste_cost_label = QLabel()
        self.base_qty_label = QLabel()
        self.unit_cost_label = QLabel()
        self.line_count_label = QLabel()
        zero_money = format(Decimal('0.00'), '.2f')
        zero_qty = format(Decimal('0.00'), '.2f')
        zero_count = format(Decimal('0'), '.0f')
        self.material_cost_label.setText(zero_money)
        self.waste_cost_label.setText(zero_money)
        self.base_qty_label.setText(zero_qty)
        self.unit_cost_label.setText(zero_money)
        self.line_count_label.setText(zero_count)
        rows = [
            ('manufacturing_material_cost', self.material_cost_label),
            ('manufacturing_waste_cost', self.waste_cost_label),
            ('manufacturing_required_base_qty', self.base_qty_label),
            ('manufacturing_unit_cost_output', self.unit_cost_label),
            ('manufacturing_component_count', self.line_count_label),
        ]
        for row, (key, value_label) in enumerate(rows):
            name = QLabel(tr(key))
            value_label.setAlignment(value_label.alignment() | 2)
            value_label.setObjectName('SummaryValue')
            grid.addWidget(name, row, 0)
            grid.addWidget(value_label, row, 1)

    def update_summary(self, summary: dict, output_qty) -> None:
        material_cost = self._decimal(summary.get('material_cost'))
        waste_cost = self._decimal(summary.get('waste_cost'))
        base_qty = self._decimal(summary.get('base_qty'))
        line_count = self._decimal(summary.get('line_count'))
        output_qty = self._decimal(output_qty, '1')
        if output_qty <= 0:
            output_qty = Decimal('1')
        self.material_cost_label.setText(f'{material_cost:.2f}')
        self.waste_cost_label.setText(f'{waste_cost:.2f}')
        self.base_qty_label.setText(f'{base_qty:.4f}')
        self.unit_cost_label.setText(f'{(material_cost / output_qty):.2f}')
        self.line_count_label.setText(f'{line_count:.0f}')

    def _decimal(self, value, default='0') -> Decimal:
        try:
            if value in (None, ''):
                value = default
            return Decimal(str(value))
        except Exception:
            return Decimal(str(default))
