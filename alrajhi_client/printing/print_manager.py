# -*- coding: utf-8 -*-
import os
from datetime import datetime
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QSpinBox, QCheckBox, QLabel, QGroupBox, QFormLayout, QMessageBox, QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextDocument, QFont, QTextCursor, QTextBlockFormat, QTextCharFormat, QTextTableFormat, QTextLength
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog, QPrintDialog
from printer_manager import PrinterManager
from config import get_company_info
from utils import clean_text
from .print_templates import invoice_html

class PrintManager:
    @staticmethod
    def get_printer_settings(parent=None):
        dialog = QDialog(parent)
        dialog.setWindowTitle("إعدادات الطباعة")
        dialog.setLayoutDirection(Qt.RightToLeft)
        dialog.resize(450, 400)
        layout = QVBoxLayout(dialog)

        printer_group = QGroupBox("إعدادات الطابعة")
        printer_layout = QFormLayout(printer_group)
        pm = PrinterManager()
        pm.load_default_printer()
        printer_combo = QComboBox()
        for p in pm.printers:
            printer_combo.addItem(p.name, p.id)
        printer_layout.addRow("الطابعة:", printer_combo)
        copies_spin = QSpinBox()
        copies_spin.setRange(1, 99)
        copies_spin.setValue(1)
        printer_layout.addRow("عدد النسخ:", copies_spin)
        color_check = QCheckBox("طباعة بالألوان")
        color_check.setChecked(True)
        printer_layout.addRow(color_check)
        layout.addWidget(printer_group)

        paper_group = QGroupBox("إعدادات الورق")
        paper_layout = QFormLayout(paper_group)
        paper_size_combo = QComboBox()
        paper_size_combo.addItems(["A4", "A5", "Letter", "Legal", "B5"])
        paper_size_combo.setCurrentText("A4")
        paper_layout.addRow("حجم الورق:", paper_size_combo)
        orientation_combo = QComboBox()
        orientation_combo.addItems(["عمودي", "أفقي"])
        paper_layout.addRow("الاتجاه:", orientation_combo)
        layout.addWidget(paper_group)

        options_group = QGroupBox("خيارات إضافية")
        options_layout = QFormLayout(options_group)
        show_logo_check = QCheckBox("إظهار شعار الشركة")
        show_logo_check.setChecked(True)
        options_layout.addRow(show_logo_check)
        show_footer_check = QCheckBox("إظهار التذييل")
        show_footer_check.setChecked(True)
        options_layout.addRow(show_footer_check)
        layout.addWidget(options_group)

        btn_layout = QHBoxLayout()
        preview_btn = QPushButton("معاينة")
        preview_btn.setObjectName("primary")
        print_btn = QPushButton("طباعة")
        cancel_btn = QPushButton("إلغاء")
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
        printer = QPrinter(QPrinter.HighResolution)
        if settings.get('orientation', 0) == 1:
            printer.setOrientation(QPrinter.Landscape)
        else:
            printer.setOrientation(QPrinter.Portrait)
        printer.setCopyCount(settings.get('copies', 1))
        printer.setColorMode(QPrinter.Color if settings.get('color', True) else QPrinter.GrayScale)
        printer_id = settings.get('printer_id')
        if printer_id:
            pm = PrinterManager()
            printer_info = pm.get_printer(printer_id)
            if printer_info and printer_info.type.value != 'pdf':
                printer.setPrinterName(printer_info.name)
        return printer

    @staticmethod
    def print_html(html, title, parent=None):
        from .printing_service import printing_service
        printing_service.preview_html(html, parent, title)

    @staticmethod
    def print_invoice(invoice_data, parent=None):
        from .printing_service import printing_service
        printing_service.invoice_preview(invoice_data, parent, paper='default')


class ProfessionalInvoicePrinter:
    @staticmethod
    def generate_invoice_html(invoice_data, paper='default'):
        return invoice_html(invoice_data, paper)


class ProfessionalPrintManager:
    @staticmethod
    def print_document(html, title, parent=None):
        PrintManager.print_html(html, title, parent)


