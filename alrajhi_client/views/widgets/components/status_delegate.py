# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor


class StatusColorDelegate(QStyledItemDelegate):
    """Delegate reserved for future cell-level status painting.

    Row-level painting currently happens in GenericTableModel via _severity/_row_status.
    This delegate keeps table rendering extension centralized without touching widgets.
    """
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
