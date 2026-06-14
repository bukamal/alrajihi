# -*- coding: utf-8 -*-
"""Centralized printing service for previews, direct printing and PDF export.

This module is the single entry point for printable HTML in the client.  It keeps
invoice, voucher, return, report and table printing on the same template family so
that company header, footer, RTL layout and paper selection remain consistent.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import os
import tempfile
import webbrowser

from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog, QPrintDialog

from printing.print_templates import invoice_html, voucher_html, report_html, return_html, production_order_html
from core.services.barcode_label_service import barcode_label_service
from core.services.settings_service import settings_service


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


    def open_html_in_browser(self, html: str, parent=None, title: str = "معاينة HTML") -> bool:
        """Write HTML to a temporary file and open it in the default browser.

        This is intentionally separate from Qt print preview because browser
        preview is easier for users to inspect, print, and save with native
        browser controls.
        """
        if not html:
            QMessageBox.warning(parent, "تنبيه", "لا يوجد محتوى للمعاينة")
            return False
        try:
            fd, path = tempfile.mkstemp(prefix="alrajhi_print_", suffix=".html")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(html)
            webbrowser.open_new_tab("file://" + os.path.abspath(path))
            return True
        except Exception as exc:
            QMessageBox.warning(parent, "تعذر فتح المتصفح", str(exc))
            return False

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


    # ========== Unified barcode label printing ==========
    def barcode_label_options(self, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Return barcode label options from printing settings plus optional overrides."""
        cfg = settings_service.get_printing_settings()
        opts = {
            'label_size': cfg.get('barcode_label_size', '50x30'),
            'symbology': cfg.get('barcode_symbology', 'AUTO'),
            'show_company': bool(cfg.get('barcode_show_company', True)),
            'show_name': bool(cfg.get('barcode_show_name', True)),
            'show_price': bool(cfg.get('barcode_show_price', True)),
            'show_barcode_text': bool(cfg.get('barcode_show_text', True)),
            'columns': int(cfg.get('barcode_columns', 2) or 2),
        }
        if overrides:
            opts.update({k: v for k, v in overrides.items() if v is not None})
        return opts

    def barcode_labels_html(self, items: List[Dict[str, Any]], options: Optional[Dict[str, Any]] = None) -> str:
        return barcode_label_service.labels_document_html(items or [], self.barcode_label_options(options))

    def barcode_labels_preview(self, items: List[Dict[str, Any]], parent=None, options: Optional[Dict[str, Any]] = None) -> None:
        self.preview_html(self.barcode_labels_html(items, options), parent, "معاينة الباركود")

    def barcode_labels_print(self, items: List[Dict[str, Any]], parent=None, options: Optional[Dict[str, Any]] = None, printer_name: str = '') -> bool:
        html = self.barcode_labels_html(items, options)
        if not html:
            QMessageBox.warning(parent, "تنبيه", "لا يوجد محتوى للطباعة")
            return False
        doc = self._make_document(html)
        printer = QPrinter(QPrinter.HighResolution)
        if printer_name:
            printer.setPrinterName(printer_name)
        if not printer_name:
            dialog = QPrintDialog(printer, parent)
            dialog.setWindowTitle("طباعة الباركود")
            if dialog.exec() != QPrintDialog.Accepted:
                return False
        doc.print(printer)
        return True

    def barcode_labels_pdf(self, items: List[Dict[str, Any]], parent=None, default_name: str = "barcodes.pdf", options: Optional[Dict[str, Any]] = None) -> bool:
        return self.save_pdf(self.barcode_labels_html(items, options), parent, default_name)

    def invoice_html(self, invoice: Dict[str, Any], paper: str = 'default') -> str:
        return invoice_html(invoice, paper)

    def invoice_browser_preview(self, invoice: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.open_html_in_browser(self.invoice_html(invoice, paper), parent, "معاينة HTML للفاتورة")

    def invoice_browser(self, invoice: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        # Backward-compatible public name used by invoice dialogs.
        return self.invoice_browser_preview(invoice, parent, paper)

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

    def voucher_browser(self, voucher: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.open_html_in_browser(self.voucher_html(voucher, paper), parent, "معاينة HTML للسند")

    def voucher_pdf(self, voucher: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        ref = voucher.get('reference') or voucher.get('id') or 'voucher'
        return self.save_pdf(self.voucher_html(voucher, paper), parent, f"voucher_{ref}.pdf")

    def return_html(self, data: Dict[str, Any], paper: str = 'default') -> str:
        return return_html(data, paper)

    def return_preview(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> None:
        self.preview_html(self.return_html(data, paper), parent, "معاينة المرتجع")

    def return_print(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.print_html(self.return_html(data, paper), parent, "طباعة المرتجع")

    def return_browser(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.open_html_in_browser(self.return_html(data, paper), parent, "معاينة HTML للمرتجع")

    def return_pdf(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        ref = data.get('reference') or data.get('return_no') or data.get('id') or 'return'
        return self.save_pdf(self.return_html(data, paper), parent, f"return_{ref}.pdf")

    def production_html(self, data: Dict[str, Any], paper: str = 'default') -> str:
        return production_order_html(data, paper)

    def production_preview(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> None:
        self.preview_html(self.production_html(data, paper), parent, "معاينة أمر الإنتاج")

    def production_print(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.print_html(self.production_html(data, paper), parent, "طباعة أمر الإنتاج")

    def production_browser(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.open_html_in_browser(self.production_html(data, paper), parent, "معاينة HTML لأمر الإنتاج")

    def production_pdf(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        order = data.get('order') or data
        ref = order.get('order_number') or order.get('id') or 'production_order'
        return self.save_pdf(self.production_html(data, paper), parent, f"production_{ref}.pdf")

    def report_html(self, title: str, rows: List[List[Any]], headers: List[str], subtitle: str = '', summary: Optional[Dict[str, Any]] = None, paper: str = 'default') -> str:
        return report_html(title, rows, headers, subtitle, summary, paper=paper)

    def report_preview(self, title: str, rows: List[List[Any]], headers: List[str], parent=None, subtitle: str = '', summary: Optional[Dict[str, Any]] = None, paper: str = 'default') -> None:
        html = self.report_html(title, rows, headers, subtitle, summary, paper)
        self.preview_html(html, parent, f"معاينة {title}")

    def report_print(self, title: str, rows: List[List[Any]], headers: List[str], parent=None, subtitle: str = '', summary: Optional[Dict[str, Any]] = None, paper: str = 'default') -> bool:
        html = self.report_html(title, rows, headers, subtitle, summary, paper)
        return self.print_html(html, parent, f"طباعة {title}")

    def report_browser(self, title: str, rows: List[List[Any]], headers: List[str], parent=None, subtitle: str = '', summary: Optional[Dict[str, Any]] = None, paper: str = 'default') -> bool:
        html = self.report_html(title, rows, headers, subtitle, summary, paper)
        return self.open_html_in_browser(html, parent, str(title or 'report'))

    def report_pdf(self, title: str, rows: List[List[Any]], headers: List[str], parent=None, subtitle: str = '', summary: Optional[Dict[str, Any]] = None, paper: str = 'default') -> bool:
        html = self.report_html(title, rows, headers, subtitle, summary, paper)
        safe_title = ''.join(ch if ch.isalnum() or ch in ('_', '-') else '_' for ch in title).strip('_') or 'report'
        return self.save_pdf(html, parent, f"{safe_title}.pdf")


printing_service = PrintingService()
