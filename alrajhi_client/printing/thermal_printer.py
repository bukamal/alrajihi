# -*- coding: utf-8 -*-
import os
import io
import base64
from PIL import Image
from barcode import Code128
from barcode.writer import ImageWriter
from PyQt5.QtWidgets import QFileDialog
from .label_designer import get_current_template
from utils import show_toast
from core.services.barcode_label_service import barcode_label_service
from core.services.barcode_service import barcode_service

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

class ThermalPrinter:
    CMD_INIT = b'\x1b\x40'
    CMD_ALIGN_CENTER = b'\x1b\x61\x01'
    CMD_BARCODE_CODE128 = b'\x1d\x6b\x73'
    CMD_CUT = b'\x1d\x56\x42\x00'
    CMD_LINE_FEED = b'\x0a'

    def __init__(self, port: str, baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self._serial = None

    def connect(self) -> bool:
        if not SERIAL_AVAILABLE:
            return False
        try:
            self._serial = serial.Serial(self.port, self.baudrate, timeout=2)
            self._serial.write(self.CMD_INIT)
            return True
        except:
            return False

    def disconnect(self):
        if self._serial and self._serial.is_open:
            self._serial.close()

    def print_barcode(self, barcode: str, height: int = 80):
        if not self._serial:
            return
        self._serial.write(b'\x1d\x68' + bytes([height]))
        n = len(barcode)
        self._serial.write(self.CMD_BARCODE_CODE128 + bytes([n]) + barcode.encode() + b'\x00')

    def print_label(self, barcode: str, item_name: str, price: str = "", copies: int = 1) -> bool:
        """Open a thermal-sized browser HTML label instead of raw serial print."""
        try:
            from .printing_service import printing_service
            item = {'barcode': barcode, 'name': item_name, 'price': price, 'copies': copies}
            html = barcode_label_service.labels_document_html([item], {'columns': 1, 'label_size': 'thermal'})
            return printing_service.open_html_in_browser(html, None, 'barcode_label')
        except Exception as e:
            print(f"خطأ في الطباعة: {e}")
            return False

    def print_receipt(self, lines: list, double_height: bool = False) -> bool:
        """Open receipt content as browser HTML using the report template."""
        try:
            from .printing_service import printing_service
            rows = [[line] for line in (lines or [])]
            html = printing_service.report_html('receipt', rows, [''], subtitle='')
            return printing_service.open_html_in_browser(html, None, 'receipt')
        except Exception as e:
            print(f"خطأ في الطباعة: {e}")
            return False

class PDFPrinter:
    """Backward-compatible barcode PDF facade.

    The project no longer renders barcode PDFs through Qt.  These methods open
    the same settings-driven browser HTML used by barcode label printing; users
    can print or save as PDF from the browser.
    """
    def __init__(self, parent_widget=None):
        self.parent = parent_widget

    def _barcode_to_base64(self, barcode: str, symbology: str = 'AUTO') -> str:
        return barcode_label_service.barcode_png_base64(barcode, symbology)

    def print_label(self, barcode: str, item_name: str, price: str = "", copies: int = 1, options: dict | None = None) -> bool:
        from .printing_service import printing_service
        item = {'barcode': barcode, 'name': item_name, 'price': price, 'copies': copies}
        html = barcode_label_service.labels_document_html([item], options or {'columns': 1})
        return printing_service.open_html_in_browser(html, self.parent, 'barcode_label')

    def print_labels_batch(self, items_data: list, options: dict | None = None) -> bool:
        from .printing_service import printing_service
        html = barcode_label_service.labels_document_html(items_data or [], options or {})
        return printing_service.open_html_in_browser(html, self.parent, 'barcode_labels_batch')

class ImagePrinter:
    def __init__(self, parent_widget=None):
        self.parent = parent_widget

    def print_label(self, barcode: str, item_name: str, price: str = "", copies: int = 1) -> bool:
        if self.parent is None:
            return False
        filename, _ = QFileDialog.getSaveFileName(self.parent, "حفظ PNG", f"barcode_{item_name}.png", "PNG (*.png)")
        if not filename:
            return False
        sym = barcode_label_service.resolve_symbology(barcode, 'AUTO')
        code = EAN13(barcode, writer=ImageWriter()) if sym == 'EAN13' else Code128(barcode, writer=ImageWriter())
        code.save(filename)
        if self.parent:
            show_toast(f"تم حفظ الصورة بنجاح: {os.path.basename(filename)}", "success", self.parent)
        return True


