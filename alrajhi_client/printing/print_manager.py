# -*- coding: utf-8 -*-
import os
from datetime import datetime
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QSpinBox, QCheckBox, QLabel, QGroupBox, QFormLayout, QMessageBox, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextDocument, QFont, QTextCursor, QTextBlockFormat, QTextCharFormat, QTextTableFormat, QTextLength
from utils import clean_text
from i18n import translate


class PrintManager:
    @staticmethod
    def get_printer_settings(parent=None):
        dialog = QDialog(parent)
        dialog.setWindowTitle(translate('phase233_allui_022'))
        dialog.setLayoutDirection(Qt.RightToLeft)
        dialog.resize(450, 400)
        layout = QVBoxLayout(dialog)

        printer_group = QGroupBox(translate('printing'))
        printer_layout = QFormLayout(printer_group)
        printer_combo = QComboBox()
        printer_combo.addItem('Browser HTML', 'browser')
        printer_combo.setEnabled(False)
        printer_layout.addRow(translate('phase233_ui_023'), printer_combo)
        copies_spin = QSpinBox()
        copies_spin.setRange(1, 99)
        copies_spin.setValue(1)
        printer_layout.addRow(translate('phase233_ui_024'), copies_spin)
        color_check = QCheckBox(translate('phase233_allui_024'))
        color_check.setChecked(True)
        printer_layout.addRow(color_check)
        layout.addWidget(printer_group)

        paper_group = QGroupBox(translate('phase233_allui_025'))
        paper_layout = QFormLayout(paper_group)
        paper_size_combo = QComboBox()
        paper_size_combo.addItems(["A4", "A5", "Letter", "Legal", "B5"])
        paper_size_combo.setCurrentText("A4")
        paper_layout.addRow("حجم الورق:", paper_size_combo)
        orientation_combo = QComboBox()
        orientation_combo.addItems(["عمودي", "أفقي"])
        paper_layout.addRow("الاتجاه:", orientation_combo)
        layout.addWidget(paper_group)

        options_group = QGroupBox(translate('phase233_allui_026'))
        options_layout = QFormLayout(options_group)
        show_logo_check = QCheckBox(translate('phase233_allui_027'))
        show_logo_check.setChecked(True)
        options_layout.addRow(show_logo_check)
        show_footer_check = QCheckBox(translate('phase233_allui_028'))
        show_footer_check.setChecked(True)
        options_layout.addRow(show_footer_check)
        layout.addWidget(options_group)

        btn_layout = QHBoxLayout()
        preview_btn = QPushButton(translate('phase233_allui_029'))
        preview_btn.setObjectName("primary")
        print_btn = QPushButton(translate('phase233_allui_004'))
        cancel_btn = QPushButton(translate('phase233_ui_020'))
        btn_layout.addWidget(preview_btn)
        btn_layout.addWidget(print_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        settings = {'printer_id': None, 'copies': 1, 'color': True,
                    'paper_size': 'A4', 'orientation': 0,
                    'show_logo': True, 'show_footer': True}

        def on_preview():
            settings['printer_id'] = printer_combo.currentData()
            settings['copies'] = copies_spin.value()
            settings['color'] = color_check.isChecked()
            settings['paper_size'] = paper_size_combo.currentText()
            settings['orientation'] = 1 if orientation_combo.currentIndex() == 1 else 0
            settings['show_logo'] = show_logo_check.isChecked()
            settings['show_footer'] = show_footer_check.isChecked()
            dialog.accept()
            return settings

        def on_print():
            settings.update(on_preview())
            dialog.done(2)

        preview_btn.clicked.connect(on_preview)
        print_btn.clicked.connect(on_print)
        cancel_btn.clicked.connect(dialog.reject)

        result = dialog.exec()
        if result == QDialog.Accepted:
            return settings
        elif result == 2:
            settings['direct_print'] = True
            return settings
        return None

    @staticmethod
    def create_printer(settings):
        """Legacy compatibility shim.

        Phase 242 removed Qt printer creation from the print pipeline.  Callers
        receive the normalized browser settings instead of a device object.
        """
        normalized = dict(settings or {})
        normalized['printer_id'] = 'browser'
        normalized['direct_print'] = False
        return normalized

    @staticmethod
    def print_html(html, title, parent=None):
        from .printing_service import printing_service
        printing_service.render_html(html, parent, title, mode='browser')

    @staticmethod
    def print_invoice(invoice_data, parent=None):
        from .printing_service import printing_service
        printing_service.invoice_print(invoice_data, parent, paper='default')


class ProfessionalInvoicePrinter:
    @staticmethod
    def generate_invoice_html(invoice_data, paper='default'):
        # Resolve through printing_service at call time so a missing packaged
        # _template_loader module cannot break application startup.
        from .printing_service import invoice_html
        return invoice_html(invoice_data, paper)


class ProfessionalPrintManager:
    @staticmethod
    def print_document(html, title, parent=None):
        PrintManager.print_html(html, title, parent)


