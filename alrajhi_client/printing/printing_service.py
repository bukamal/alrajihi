# -*- coding: utf-8 -*-
"""Centralized printing service for previews, direct printing and PDF export.

This module is the single entry point for printable HTML in the client.  It keeps
invoice, voucher, return, report and table printing on the same template family so
that company header, footer, RTL layout and paper selection remain consistent.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog, QPrintDialog

from printing.print_templates import invoice_html, voucher_html, report_html, return_html


class PrintingService:
    """Unified printing facade used by dialogs, widgets and table views."""

    def _make_document(self, html: str) -> QTextDocument:
        doc = QTextDocument()
        doc.setHtml(html or "")
        return doc

    def preview_html(self, html: str, parent=None, title: str = "معاينة الطباعة") -> None:
        if not html:
            QMessageBox.warning(parent, "تنبيه", "لا يوجد محتوى للطباعة")
            return
        doc = self._make_document(html)
        printer = QPrinter(QPrinter.HighResolution)
        preview = QPrintPreviewDialog(printer, parent)
        preview.setWindowTitle(title)
        preview.paintRequested.connect(lambda p: doc.print(p))
        preview.exec()

    def print_html(self, html: str, parent=None, title: str = "طباعة") -> bool:
        if not html:
            QMessageBox.warning(parent, "تنبيه", "لا يوجد محتوى للطباعة")
            return False
        doc = self._make_document(html)
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, parent)
        dialog.setWindowTitle(title)
        if dialog.exec() == QPrintDialog.Accepted:
            doc.print(printer)
            return True
        return False

    def save_pdf(self, html: str, parent=None, default_name: str = "document.pdf") -> bool:
        if not html:
            QMessageBox.warning(parent, "تنبيه", "لا يوجد محتوى للحفظ")
            return False
        filename, _ = QFileDialog.getSaveFileName(parent, "حفظ PDF", default_name, "PDF (*.pdf)")
        if not filename:
            return False
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
        doc = self._make_document(html)
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(filename)
        doc.print(printer)
        return True

    def invoice_html(self, invoice: Dict[str, Any], paper: str = 'default') -> str:
        return invoice_html(invoice, paper)

    def invoice_preview(self, invoice: Dict[str, Any], parent=None, paper: str = 'default') -> None:
        html = self.invoice_html(invoice, paper)
        self.preview_html(html, parent, "معاينة الفاتورة")

    def invoice_print(self, invoice: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.print_html(self.invoice_html(invoice, paper), parent, "طباعة الفاتورة")

    def invoice_pdf(self, invoice: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        ref = invoice.get('reference') or invoice.get('ref') or 'invoice'
        return self.save_pdf(self.invoice_html(invoice, paper), parent, f"invoice_{ref}.pdf")

    def voucher_html(self, voucher: Dict[str, Any], paper: str = 'default') -> str:
        return voucher_html(voucher, paper)

    def voucher_preview(self, voucher: Dict[str, Any], parent=None, paper: str = 'default') -> None:
        self.preview_html(self.voucher_html(voucher, paper), parent, "معاينة السند")

    def voucher_print(self, voucher: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.print_html(self.voucher_html(voucher, paper), parent, "طباعة السند")

    def voucher_pdf(self, voucher: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        ref = voucher.get('reference') or voucher.get('id') or 'voucher'
        return self.save_pdf(self.voucher_html(voucher, paper), parent, f"voucher_{ref}.pdf")

    def return_preview(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> None:
        self.preview_html(return_html(data, paper), parent, "معاينة المرتجع")

    def report_html(self, title: str, rows: List[List[Any]], headers: List[str], subtitle: str = '', summary: Optional[Dict[str, Any]] = None, paper: str = 'default') -> str:
        return report_html(title, rows, headers, subtitle, summary, paper=paper)

    def report_preview(self, title: str, rows: List[List[Any]], headers: List[str], parent=None, subtitle: str = '', summary: Optional[Dict[str, Any]] = None, paper: str = 'default') -> None:
        html = self.report_html(title, rows, headers, subtitle, summary, paper)
        self.preview_html(html, parent, f"معاينة {title}")

    def report_print(self, title: str, rows: List[List[Any]], headers: List[str], parent=None, subtitle: str = '', summary: Optional[Dict[str, Any]] = None, paper: str = 'default') -> bool:
        html = self.report_html(title, rows, headers, subtitle, summary, paper)
        return self.print_html(html, parent, f"طباعة {title}")

    def report_pdf(self, title: str, rows: List[List[Any]], headers: List[str], parent=None, subtitle: str = '', summary: Optional[Dict[str, Any]] = None, paper: str = 'default') -> bool:
        html = self.report_html(title, rows, headers, subtitle, summary, paper)
        safe_title = ''.join(ch if ch.isalnum() or ch in ('_', '-') else '_' for ch in title).strip('_') or 'report'
        return self.save_pdf(html, parent, f"{safe_title}.pdf")


printing_service = PrintingService()
