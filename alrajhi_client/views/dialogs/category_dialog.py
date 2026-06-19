# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QVBoxLayout
from views.centered_dialog import CenteredDialog
from views.widgets.categories_widget import CategoriesWidget
from views.widgets.modern_ui import apply_modern_dialog
from i18n import translate


class CategoryDialog(CenteredDialog):
    """Legacy dialog wrapper around the professional category manager."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(translate('phase233_ui_026'))
        self.resize(760, 520)
        layout = QVBoxLayout(self.content_widget)
        layout.addWidget(CategoriesWidget(self))
        apply_modern_dialog(self, translate('phase233_ui_026'))
