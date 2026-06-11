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
from i18n.translator import t, use_language
from core.services.settings_service import settings_service


class PrintingService:
    """Unified printing facade used by dialogs, widgets and table views."""

    def _print_lang(self) -> str:
        try:
            return (settings_service.get_printing_settings() or {}).get('template_language', 'auto') or 'auto'
        except Exception:
            return 'auto'

    def _make_document(self, html: str) -> QTextDocument:
        doc = QTextDocument()
        doc.setHtml(html or "")
        return doc

    def preview_html(self, html: str, parent=None, title: str = t("print_preview")) -> None:
        if not html:
            QMessageBox.warning(parent, t("warning"), t("no_print_content"))
            return
        doc = self._make_document(html)
        printer = QPrinter(QPrinter.HighResolution)
        preview = QPrintPreviewDialog(printer, parent)
        preview.setWindowTitle(title)
        preview.paintRequested.connect(lambda p: doc.print(p))
        preview.exec()

    def print_html(self, html: str, parent=None, title: str = t("print")) -> bool:
        if not html:
            QMessageBox.warning(parent, t("warning"), t("no_print_content"))
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
            QMessageBox.warning(parent, t("warning"), t("no_pdf_content"))
            return False
        filename, _ = QFileDialog.getSaveFileName(parent, t("save_pdf"), default_name, "PDF (*.pdf)")
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
        
        with use_language(self._print_lang()):
            return invoice_html(invoice, paper)

    def invoice_preview(self, invoice: Dict[str, Any], parent=None, paper: str = 'default') -> None:
        html = self.invoice_html(invoice, paper)
        self.preview_html(html, parent, t("print_preview") + " - " + t("invoice"))

    def invoice_print(self, invoice: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.print_html(self.invoice_html(invoice, paper), parent, t("print") + " - " + t("invoice"))

    def invoice_pdf(self, invoice: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        ref = invoice.get('reference') or invoice.get('ref') or 'invoice'
        return self.save_pdf(self.invoice_html(invoice, paper), parent, f"invoice_{ref}.pdf")

    def voucher_html(self, voucher: Dict[str, Any], paper: str = 'default') -> str:
        
        with use_language(self._print_lang()):
            return voucher_html(voucher, paper)

    def voucher_preview(self, voucher: Dict[str, Any], parent=None, paper: str = 'default') -> None:
        self.preview_html(self.voucher_html(voucher, paper), parent, t("print_preview") + " - " + t("voucher"))

    def voucher_print(self, voucher: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.print_html(self.voucher_html(voucher, paper), parent, t("print") + " - " + t("voucher"))

    def voucher_pdf(self, voucher: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        ref = voucher.get('reference') or voucher.get('id') or 'voucher'
        return self.save_pdf(self.voucher_html(voucher, paper), parent, f"voucher_{ref}.pdf")

    def return_preview(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> None:
        
        with use_language(self._print_lang()):
            html = return_html(data, paper)
            title = t("print_preview") + " - " + t("return_doc")
        self.preview_html(html, parent, title)

    def report_html(self, title: str, rows: List[List[Any]], headers: List[str], subtitle: str = '', summary: Optional[Dict[str, Any]] = None, paper: str = 'default') -> str:
        
        with use_language(self._print_lang()):
            return report_html(title, rows, headers, subtitle, summary, paper=paper)

    def report_preview(self, title: str, rows: List[List[Any]], headers: List[str], parent=None, subtitle: str = '', summary: Optional[Dict[str, Any]] = None, paper: str = 'default') -> None:
        html = self.report_html(title, rows, headers, subtitle, summary, paper)
        self.preview_html(html, parent, f"{t('print_preview')} - {title}")

    def report_print(self, title: str, rows: List[List[Any]], headers: List[str], parent=None, subtitle: str = '', summary: Optional[Dict[str, Any]] = None, paper: str = 'default') -> bool:
        html = self.report_html(title, rows, headers, subtitle, summary, paper)
        return self.print_html(html, parent, f"{t('print')} - {title}")

    def report_pdf(self, title: str, rows: List[List[Any]], headers: List[str], parent=None, subtitle: str = '', summary: Optional[Dict[str, Any]] = None, paper: str = 'default') -> bool:
        html = self.report_html(title, rows, headers, subtitle, summary, paper)
        safe_title = ''.join(ch if ch.isalnum() or ch in ('_', '-') else '_' for ch in title).strip('_') or 'report'
        return self.save_pdf(html, parent, f"{safe_title}.pdf")


printing_service = PrintingService()
