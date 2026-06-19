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
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtGui import QTextDocument, QImage, QPainter
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog, QPrintDialog

from ._template_loader import require_template

invoice_html = require_template("invoice_html")
voucher_html = require_template("voucher_html")
report_html = require_template("report_html")
return_html = require_template("return_html")
production_order_html = require_template("production_order_html")
restaurant_receipt_html = require_template("restaurant_receipt_html")
restaurant_kitchen_ticket_html = require_template("restaurant_kitchen_ticket_html")
manufacturing_bom_html = require_template("manufacturing_bom_html")
manufacturing_pick_ticket_html = require_template("manufacturing_pick_ticket_html")
manufacturing_cost_report_html = require_template("manufacturing_cost_report_html")
inventory_transfer_html = require_template("inventory_transfer_html")
inventory_balances_html = require_template("inventory_balances_html")
inventory_movements_html = require_template("inventory_movements_html")
inventory_ledger_html = require_template("inventory_ledger_html")
from core.services.barcode_label_service import barcode_label_service
from core.services.settings_service import settings_service


def _tr(key: str, **kwargs) -> str:
    try:
        from i18n.translator import translate
        return translate(key, **kwargs)
    except Exception:
        return key


class PrintingService:
    """Unified printing facade used by dialogs, widgets and table views."""

    def _printing_settings(self) -> Dict[str, Any]:
        try:
            return dict(settings_service.get_printing_settings() or {})
        except Exception:
            return {}

    def print_button_mode(self, document_type: str = 'document') -> str:
        """Return the configured single print-button action.

        UI print buttons must not decide between preview/browser/direct/PDF. The
        project setting owns that decision. PDF/export is deliberately sanitized
        back to normal print because the visible PDF buttons were removed.
        """
        cfg = self._printing_settings()
        candidates = (
            cfg.get(f'{document_type}_print_mode'),
            cfg.get('print_button_mode'),
            cfg.get('default_print_mode'),
            cfg.get('print_mode'),
            'browser',
        )
        mode = next((str(x).lower().strip() for x in candidates if x not in (None, '')), 'print')
        # Phase 237: all visible print buttons open the generated HTML in the
        # system browser.  Legacy settings such as print/preview/pdf are treated
        # as browser output so users get one consistent path and can print from
        # browser controls.
        if mode in {'browser', 'html', 'open', 'print', 'printer', 'direct', 'preview', 'view', 'pdf', 'save_pdf', 'export', 'file'}:
            return 'browser'
        return 'browser'

    def _print_button_render(self, html: str, parent=None, title: str = None, document_type: str = 'document', default_name: str = 'document.pdf') -> bool:
        return self.render_html(html, parent, title, mode=self.print_button_mode(document_type), default_name=default_name)

    def _make_document(self, html: str) -> QTextDocument:
        doc = QTextDocument()
        doc.setHtml(html or "")
        return doc

    def preview_html(self, html: str, parent=None, title: str = None) -> None:
        if not html:
            QMessageBox.warning(parent, _tr("warning"), _tr("print_no_content"))
            return
        doc = self._make_document(html)
        printer = QPrinter(QPrinter.HighResolution)
        preview = QPrintPreviewDialog(printer, parent)
        preview.setWindowTitle(title or _tr("print_preview_title"))
        preview.paintRequested.connect(lambda p: doc.print(p))
        preview.exec()


    def open_html_in_browser(self, html: str, parent=None, title: str = None) -> bool:
        """Write HTML to a temporary file and open it in the default browser.

        This is intentionally separate from Qt print preview because browser
        preview is easier for users to inspect, print, and save with native
        browser controls.
        """
        if not html:
            QMessageBox.warning(parent, _tr("warning"), _tr("print_no_preview_content"))
            return False
        try:
            fd, path = tempfile.mkstemp(prefix="alrajhi_print_", suffix=".html")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(html)
            webbrowser.open_new_tab("file://" + os.path.abspath(path))
            return True
        except Exception as exc:
            QMessageBox.warning(parent, _tr("print_browser_open_failed"), str(exc))
            return False

    def print_html(self, html: str, parent=None, title: str = None) -> bool:
        if not html:
            QMessageBox.warning(parent, _tr("warning"), _tr("print_no_content"))
            return False
        doc = self._make_document(html)
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, parent)
        dialog.setWindowTitle(title or _tr("print_dialog_title"))
        if dialog.exec() == QPrintDialog.Accepted:
            doc.print(printer)
            return True
        return False

    def save_pdf(self, html: str, parent=None, default_name: str = "document.pdf") -> bool:
        if not html:
            QMessageBox.warning(parent, _tr("warning"), _tr("print_no_save_content"))
            return False
        filename, _ = QFileDialog.getSaveFileName(parent, _tr("print_save_pdf"), default_name, "PDF (*.pdf)")
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



    def render_html(self, html: str, parent=None, title: str = None, mode: str = 'preview', default_name: str = 'document.pdf') -> bool:
        """Single HTML rendering dispatcher for preview/browser/print/pdf.

        Phase 228 makes every project print path converge here. Domain helpers
        such as invoice_print(), voucher_pdf(), and report_preview() should only
        build HTML, then call this dispatcher.
        """
        action = (mode or 'preview').lower().strip()
        if action in {'browser', 'html', 'open'}:
            return self.open_html_in_browser(html, parent, title)
        if action in {'direct', 'print', 'printer'}:
            return self.print_html(html, parent, title)
        if action in {'pdf', 'save_pdf', 'export'}:
            return self.save_pdf(html, parent, default_name)
        self.preview_html(html, parent, title)
        return True

    def save_html_png(self, html: str, parent=None, default_name: str = "document.png") -> bool:
        """Render printable HTML to a PNG image using Qt's text engine.

        This path is used for barcode labels when a consistent visual output is
        needed on label printers that handle images more reliably than raw text.
        """
        if not html:
            QMessageBox.warning(parent, _tr("warning"), _tr("print_no_save_content"))
            return False
        filename, _ = QFileDialog.getSaveFileName(parent, _tr("print_save_png"), default_name, "PNG (*.png);;JPEG (*.jpg *.jpeg)")
        if not filename:
            return False
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filename += '.png'
        doc = self._make_document(html)
        # A practical sheet width for label grids; QTextDocument then computes height.
        doc.setTextWidth(920)
        size = doc.size().toSize()
        width = max(420, size.width() + 24)
        height = max(220, size.height() + 24)
        image = QImage(width, height, QImage.Format_ARGB32)
        image.fill(Qt.white)
        painter = QPainter(image)
        painter.translate(12, 12)
        doc.drawContents(painter)
        painter.end()
        return bool(image.save(filename))


    # ========== Unified barcode label printing ==========
    def barcode_label_options(self, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Return barcode label options from printing settings plus optional overrides."""
        cfg = settings_service.get_printing_settings()
        opts = {
            'label_size': cfg.get('barcode_label_size', '50x30'),
            'symbology': cfg.get('barcode_symbology', 'AUTO'),
            'show_company': bool(cfg.get('barcode_show_company', True)),
            'show_logo': bool(cfg.get('barcode_show_logo', cfg.get('show_logo', True))),
            'show_qr': bool(cfg.get('barcode_show_qr', True)),
            'show_name': bool(cfg.get('barcode_show_name', True)),
            'show_price': bool(cfg.get('barcode_show_price', True)),
            'show_barcode_text': bool(cfg.get('barcode_show_text', True)),
            'columns': int(cfg.get('barcode_columns', 2) or 2),
        }
        if overrides:
            opts.update({k: v for k, v in overrides.items() if v is not None})
        return opts


    def barcode_default_printer_name(self) -> str:
        """Return the configured Qt printer name for barcode labels, if any.

        The UI no longer exposes PDF/PNG pseudo-printer buttons. If settings still
        contain a legacy pdf:/image: value, fall back to the normal print dialog.
        """
        try:
            cfg = settings_service.get_printing_settings()
            printer_id = str(cfg.get('barcode_default_printer') or '').strip()
            if printer_id.startswith('qt:'):
                return printer_id[3:]
        except Exception:
            pass
        return ''

    def barcode_labels_print_settings(self, items: List[Dict[str, Any]], parent=None, options: Optional[Dict[str, Any]] = None) -> bool:
        """Open barcode labels as settings-driven browser HTML.

        Barcode, material-card and batch-label buttons now follow the same
        visible print contract as invoices, returns and BOMs: generate HTML from
        project settings, open it in the browser, and let the browser perform
        the physical print.
        """
        html = self.barcode_labels_html(items, options)
        return self._print_button_render(html, parent, _tr("barcode_print_title"), document_type='barcode_labels')

    def barcode_labels_html(self, items: List[Dict[str, Any]], options: Optional[Dict[str, Any]] = None) -> str:
        return barcode_label_service.labels_document_html(items or [], self.barcode_label_options(options))

    def barcode_labels_preview(self, items: List[Dict[str, Any]], parent=None, options: Optional[Dict[str, Any]] = None) -> None:
        self.preview_html(self.barcode_labels_html(items, options), parent, _tr("barcode_preview_title"))

    def barcode_labels_print(self, items: List[Dict[str, Any]], parent=None, options: Optional[Dict[str, Any]] = None, printer_name: str = '') -> bool:
        html = self.barcode_labels_html(items, options)
        if not html:
            QMessageBox.warning(parent, _tr("warning"), _tr("print_no_content"))
            return False
        doc = self._make_document(html)
        printer = QPrinter(QPrinter.HighResolution)
        if printer_name:
            printer.setPrinterName(printer_name)
        if not printer_name:
            dialog = QPrintDialog(printer, parent)
            dialog.setWindowTitle(_tr("barcode_print_title"))
            if dialog.exec() != QPrintDialog.Accepted:
                return False
        doc.print(printer)
        return True

    def barcode_labels_pdf(self, items: List[Dict[str, Any]], parent=None, default_name: str = "barcodes.pdf", options: Optional[Dict[str, Any]] = None) -> bool:
        return self.save_pdf(self.barcode_labels_html(items, options), parent, default_name)

    def barcode_labels_png(self, items: List[Dict[str, Any]], parent=None, default_name: str = "barcodes.png", options: Optional[Dict[str, Any]] = None) -> bool:
        return self.save_html_png(self.barcode_labels_html(items, options), parent, default_name)

    def invoice_html(self, invoice: Dict[str, Any], paper: str = 'default') -> str:
        return invoice_html(invoice, paper)

    def invoice_browser_preview(self, invoice: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.open_html_in_browser(self.invoice_html(invoice, paper), parent, _tr("invoice_html_preview_title"))

    def invoice_browser(self, invoice: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        # Backward-compatible public name used by invoice dialogs.
        return self.invoice_browser_preview(invoice, parent, paper)

    def invoice_preview(self, invoice: Dict[str, Any], parent=None, paper: str = 'default') -> None:
        html = self.invoice_html(invoice, paper)
        self.preview_html(html, parent, _tr("invoice_preview_title"))

    def invoice_print(self, invoice: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self._print_button_render(self.invoice_html(invoice, paper), parent, _tr("invoice_print_title"), document_type='invoice')

    def invoice_pdf(self, invoice: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        ref = invoice.get('reference') or invoice.get('ref') or 'invoice'
        return self.save_pdf(self.invoice_html(invoice, paper), parent, f"invoice_{ref}.pdf")

    def voucher_html(self, voucher: Dict[str, Any], paper: str = 'default') -> str:
        return voucher_html(voucher, paper)

    def voucher_preview(self, voucher: Dict[str, Any], parent=None, paper: str = 'default') -> None:
        self.render_html(self.voucher_html(voucher, paper), parent, _tr("voucher_preview_title"), mode='preview')

    def voucher_print(self, voucher: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self._print_button_render(self.voucher_html(voucher, paper), parent, _tr("voucher_print_title"), document_type='voucher')

    def voucher_browser(self, voucher: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.render_html(self.voucher_html(voucher, paper), parent, _tr("voucher_html_preview_title"), mode='browser')

    def voucher_pdf(self, voucher: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        ref = voucher.get('reference') or voucher.get('id') or 'voucher'
        return self.render_html(self.voucher_html(voucher, paper), parent, _tr("voucher_preview_title"), mode='pdf', default_name=f"voucher_{ref}.pdf")

    def return_html(self, data: Dict[str, Any], paper: str = 'default') -> str:
        return return_html(data, paper)

    def return_preview(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> None:
        self.preview_html(self.return_html(data, paper), parent, _tr("return_preview_title"))

    def return_print(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self._print_button_render(self.return_html(data, paper), parent, _tr("return_print_title"), document_type='return')

    def return_browser(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.open_html_in_browser(self.return_html(data, paper), parent, _tr("return_html_preview_title"))

    def return_pdf(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        ref = data.get('reference') or data.get('return_no') or data.get('id') or 'return'
        return self.save_pdf(self.return_html(data, paper), parent, f"return_{ref}.pdf")


    def restaurant_receipt_html(self, data: Dict[str, Any], paper: str = 'default') -> str:
        return restaurant_receipt_html(data, paper)

    def restaurant_receipt_preview(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> None:
        self.preview_html(self.restaurant_receipt_html(data, paper), parent, _tr("restaurant_receipt_preview_title"))

    def restaurant_receipt_print(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self._print_button_render(self.restaurant_receipt_html(data, paper), parent, _tr("restaurant_receipt_print_title"), document_type='restaurant_receipt')

    def restaurant_receipt_browser(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.open_html_in_browser(self.restaurant_receipt_html(data, paper), parent, _tr("restaurant_receipt_html_preview_title"))

    def restaurant_receipt_pdf(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        session = (data or {}).get('session') or data or {}
        ref = session.get('invoice_reference') or session.get('invoice_id') or session.get('id') or 'restaurant_receipt'
        return self.save_pdf(self.restaurant_receipt_html(data, paper), parent, f"restaurant_receipt_{ref}.pdf")

    def restaurant_kitchen_ticket_html(self, data: Dict[str, Any], paper: str = 'default') -> str:
        return restaurant_kitchen_ticket_html(data, paper)

    def restaurant_kitchen_ticket_preview(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> None:
        self.preview_html(self.restaurant_kitchen_ticket_html(data, paper), parent, _tr("restaurant_kitchen_ticket_preview_title"))

    def restaurant_kitchen_ticket_print(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self._print_button_render(self.restaurant_kitchen_ticket_html(data, paper), parent, _tr("restaurant_kitchen_ticket_print_title"), document_type='restaurant_kitchen')

    def restaurant_kitchen_ticket_browser(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.open_html_in_browser(self.restaurant_kitchen_ticket_html(data, paper), parent, _tr("restaurant_kitchen_ticket_html_preview_title"))

    def restaurant_kitchen_ticket_pdf(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        ref = (data or {}).get('id') or 'kitchen_ticket'
        return self.save_pdf(self.restaurant_kitchen_ticket_html(data, paper), parent, f"kitchen_ticket_{ref}.pdf")

    # ========== Manufacturing printing ==========
    def manufacturing_bom_html(self, data: Dict[str, Any], paper: str = 'default') -> str:
        return manufacturing_bom_html(data, paper)

    def manufacturing_bom_preview(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> None:
        self.preview_html(self.manufacturing_bom_html(data, paper), parent, _tr("manufacturing_bom_preview_title"))

    def manufacturing_bom_print(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self._print_button_render(self.manufacturing_bom_html(data, paper), parent, _tr("manufacturing_bom_print_title"), document_type='manufacturing_bom')

    def manufacturing_bom_browser(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.open_html_in_browser(self.manufacturing_bom_html(data, paper), parent, _tr("manufacturing_bom_html_preview_title"))

    def manufacturing_bom_pdf(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        bom = (data or {}).get('bom') or data or {}
        ref = bom.get('id') or bom.get('bom_id') or bom.get('product_id') or 'bom'
        return self.save_pdf(self.manufacturing_bom_html(data, paper), parent, f"bom_{ref}.pdf")

    def production_html(self, data: Dict[str, Any], paper: str = 'default') -> str:
        return production_order_html(data, paper)

    def manufacturing_production_order_html(self, data: Dict[str, Any], paper: str = 'default') -> str:
        return production_order_html(data, paper)

    def manufacturing_production_order_preview(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> None:
        self.preview_html(self.manufacturing_production_order_html(data, paper), parent, _tr("production_order_preview_title"))

    def manufacturing_production_order_print(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self._print_button_render(self.manufacturing_production_order_html(data, paper), parent, _tr("production_order_print_title"), document_type='production_order')

    def manufacturing_production_order_browser(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.open_html_in_browser(self.manufacturing_production_order_html(data, paper), parent, _tr("production_order_html_preview_title"))

    def manufacturing_production_order_pdf(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        order = (data or {}).get('order') or data or {}
        ref = order.get('order_number') or order.get('id') or 'production_order'
        return self.save_pdf(self.manufacturing_production_order_html(data, paper), parent, f"production_{ref}.pdf")

    # Backward-compatible names used by older manufacturing code.
    def production_preview(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> None:
        self.manufacturing_production_order_preview(data, parent, paper)

    def production_print(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.manufacturing_production_order_print(data, parent, paper)

    def production_browser(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.manufacturing_production_order_browser(data, parent, paper)

    def production_pdf(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.manufacturing_production_order_pdf(data, parent, paper)

    def manufacturing_pick_ticket_html(self, data: Dict[str, Any], paper: str = 'default') -> str:
        return manufacturing_pick_ticket_html(data, paper)

    def manufacturing_pick_ticket_preview(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> None:
        self.preview_html(self.manufacturing_pick_ticket_html(data, paper), parent, _tr("manufacturing_pick_ticket_preview_title"))

    def manufacturing_pick_ticket_print(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self._print_button_render(self.manufacturing_pick_ticket_html(data, paper), parent, _tr("manufacturing_pick_ticket_print_title"), document_type='manufacturing_pick_ticket')

    def manufacturing_pick_ticket_browser(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.open_html_in_browser(self.manufacturing_pick_ticket_html(data, paper), parent, _tr("manufacturing_pick_ticket_html_preview_title"))

    def manufacturing_pick_ticket_pdf(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        order = (data or {}).get('order') or {}
        ref = order.get('order_number') or order.get('id') or 'pick_ticket'
        return self.save_pdf(self.manufacturing_pick_ticket_html(data, paper), parent, f"pick_ticket_{ref}.pdf")

    def manufacturing_cost_report_html(self, data: Dict[str, Any], paper: str = 'default') -> str:
        return manufacturing_cost_report_html(data, paper)

    def manufacturing_cost_report_preview(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> None:
        self.preview_html(self.manufacturing_cost_report_html(data, paper), parent, _tr("manufacturing_cost_report_preview_title"))

    def manufacturing_cost_report_print(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self._print_button_render(self.manufacturing_cost_report_html(data, paper), parent, _tr("manufacturing_cost_report_print_title"), document_type='manufacturing_cost_report')

    def manufacturing_cost_report_browser(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.open_html_in_browser(self.manufacturing_cost_report_html(data, paper), parent, _tr("manufacturing_cost_report_html_preview_title"))

    def manufacturing_cost_report_pdf(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        order = (data or {}).get('order') or {}
        ref = order.get('order_number') or order.get('id') or 'cost_report'
        return self.save_pdf(self.manufacturing_cost_report_html(data, paper), parent, f"production_cost_{ref}.pdf")


    # ========== Inventory / warehouse printing ==========
    def inventory_transfer_html(self, data: Dict[str, Any], paper: str = 'default') -> str:
        return inventory_transfer_html(data, paper)

    def inventory_transfer_preview(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> None:
        self.preview_html(self.inventory_transfer_html(data, paper), parent, _tr("inventory_transfer_preview_title"))

    def inventory_transfer_print(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self._print_button_render(self.inventory_transfer_html(data, paper), parent, _tr("inventory_transfer_print_title"), document_type='inventory_transfer')

    def inventory_transfer_browser(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.open_html_in_browser(self.inventory_transfer_html(data, paper), parent, _tr("inventory_transfer_html_preview_title"))

    def inventory_transfer_pdf(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        transfer = (data or {}).get('transfer') or data or {}
        ref = transfer.get('transfer_no') or transfer.get('id') or 'warehouse_transfer'
        return self.save_pdf(self.inventory_transfer_html(data, paper), parent, f"warehouse_transfer_{ref}.pdf")

    def inventory_balances_html(self, data: Dict[str, Any], paper: str = 'default') -> str:
        return inventory_balances_html(data, paper)

    def inventory_balances_preview(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> None:
        self.preview_html(self.inventory_balances_html(data, paper), parent, _tr("inventory_balances_preview_title"))

    def inventory_balances_print(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self._print_button_render(self.inventory_balances_html(data, paper), parent, _tr("inventory_balances_print_title"), document_type='inventory_balances')

    def inventory_balances_pdf(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.save_pdf(self.inventory_balances_html(data, paper), parent, "inventory_balances.pdf")

    def inventory_movements_html(self, data: Dict[str, Any], paper: str = 'default') -> str:
        return inventory_movements_html(data, paper)

    def inventory_movements_preview(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> None:
        self.preview_html(self.inventory_movements_html(data, paper), parent, _tr("inventory_movements_preview_title"))

    def inventory_movements_print(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self._print_button_render(self.inventory_movements_html(data, paper), parent, _tr("inventory_movements_print_title"), document_type='inventory_movements')

    def inventory_movements_pdf(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.save_pdf(self.inventory_movements_html(data, paper), parent, "inventory_movements.pdf")

    def inventory_ledger_html(self, data: Dict[str, Any], paper: str = 'default') -> str:
        return inventory_ledger_html(data, paper)

    def inventory_ledger_preview(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> None:
        self.preview_html(self.inventory_ledger_html(data, paper), parent, _tr("inventory_ledger_preview_title"))

    def inventory_ledger_print(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self._print_button_render(self.inventory_ledger_html(data, paper), parent, _tr("inventory_ledger_print_title"), document_type='inventory_ledger')

    def inventory_ledger_pdf(self, data: Dict[str, Any], parent=None, paper: str = 'default') -> bool:
        return self.save_pdf(self.inventory_ledger_html(data, paper), parent, "inventory_ledger.pdf")

    def report_html(self, title: str, rows: List[List[Any]], headers: List[str], subtitle: str = '', summary: Optional[Dict[str, Any]] = None, paper: str = 'default') -> str:
        return report_html(title, rows, headers, subtitle, summary, paper=paper)

    def report_preview(self, title: str, rows: List[List[Any]], headers: List[str], parent=None, subtitle: str = '', summary: Optional[Dict[str, Any]] = None, paper: str = 'default') -> None:
        html = self.report_html(title, rows, headers, subtitle, summary, paper)
        self.render_html(html, parent, _tr("report_preview_title", title=title), mode='preview')

    def report_print(self, title: str, rows: List[List[Any]], headers: List[str], parent=None, subtitle: str = '', summary: Optional[Dict[str, Any]] = None, paper: str = 'default') -> bool:
        html = self.report_html(title, rows, headers, subtitle, summary, paper)
        return self._print_button_render(html, parent, _tr("report_print_title", title=title), document_type='report')

    def report_browser(self, title: str, rows: List[List[Any]], headers: List[str], parent=None, subtitle: str = '', summary: Optional[Dict[str, Any]] = None, paper: str = 'default') -> bool:
        html = self.report_html(title, rows, headers, subtitle, summary, paper)
        return self.render_html(html, parent, str(title or 'report'), mode='browser')

    def report_pdf(self, title: str, rows: List[List[Any]], headers: List[str], parent=None, subtitle: str = '', summary: Optional[Dict[str, Any]] = None, paper: str = 'default') -> bool:
        html = self.report_html(title, rows, headers, subtitle, summary, paper)
        safe_title = ''.join(ch if ch.isalnum() or ch in ('_', '-') else '_' for ch in title).strip('_') or 'report'
        return self.render_html(html, parent, str(title or 'report'), mode='pdf', default_name=f"{safe_title}.pdf")


printing_service = PrintingService()
