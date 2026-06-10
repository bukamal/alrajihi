# -*- coding: utf-8 -*-
"""Centralized printing service for previews and PDF export."""
from __future__ import annotations

from typing import Any, Dict, List

from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog, QPrintDialog

from printing.print_templates import invoice_html, voucher_html, report_html


class PrintingService:
    def preview_html(self, html: str, parent=None, title: str = "معاينة الطباعة") -> None:
        if not html:
            QMessageBox.warning(parent, "تنبيه", "لا يوجد محتوى للطباعة")
            return
        doc = QTextDocument()
        doc.setHtml(html)
        printer = QPrinter(QPrinter.HighResolution)
        preview = QPrintPreviewDialog(printer, parent)
        preview.setWindowTitle(title)
        preview.paintRequested.connect(lambda p: doc.print(p))
        preview.exec()

    def print_html(self, html: str, parent=None) -> None:
        if not html:
            QMessageBox.warning(parent, "تنبيه", "لا يوجد محتوى للطباعة")
            return
        doc = QTextDocument()
        doc.setHtml(html)
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, parent)
        if dialog.exec() == QPrintDialog.Accepted:
            doc.print(printer)

    def save_pdf(self, html: str, parent=None, default_name: str = "document.pdf") -> bool:
        filename, _ = QFileDialog.getSaveFileName(parent, "حفظ PDF", default_name, "PDF (*.pdf)")
        if not filename:
            return False
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
        doc = QTextDocument()
        doc.setHtml(html)
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(filename)
        doc.print(printer)
        return True

    def invoice_preview(self, invoice: Dict[str, Any], parent=None, paper: str = 'default') -> None:
        html = invoice_html(invoice, paper)
        self.preview_html(html, parent, "معاينة الفاتورة")

    def voucher_preview(self, voucher: Dict[str, Any], parent=None, paper: str = 'a4') -> None:
        html = voucher_html(voucher, paper)
        self.preview_html(html, parent, "معاينة السند")

    def report_preview(self, title: str, rows: List[List[Any]], headers: List[str], parent=None, subtitle: str = '', summary: Dict[str, Any] | None = None) -> None:
        html = report_html(title, rows, headers, subtitle, summary)
        self.preview_html(html, parent, f"معاينة {title}")


printing_service = PrintingService()
