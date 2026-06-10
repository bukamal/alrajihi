# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QVBoxLayout
from views.centered_dialog import CenteredDialog
from views.widgets.categories_widget import CategoriesWidget


class CategoryDialog(CenteredDialog):
    """Legacy dialog wrapper around the professional category manager."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('إدارة التصنيفات')
        self.resize(760, 520)
        layout = QVBoxLayout(self.content_widget)
        layout.addWidget(CategoriesWidget(self))
