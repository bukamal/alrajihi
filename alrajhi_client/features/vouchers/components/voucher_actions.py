# -*- coding: utf-8 -*-
from __future__ import annotations

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QWidget

from i18n import translate as tr


class VoucherActionsPanel(QWidget):
    """Local action buttons mirroring UnifiedActionBar commands."""

    saveRequested = pyqtSignal()
    printRequested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.addStretch()
        self.save_btn = QPushButton(tr('save'))
        self.save_btn.setObjectName('primary')
        self.print_btn = QPushButton(tr('print_button'))
        self.save_btn.clicked.connect(self.saveRequested)
        self.print_btn.clicked.connect(self.printRequested)
        layout.addWidget(self.save_btn)
        layout.addWidget(self.print_btn)
