# -*- coding: utf-8 -*-
import os
import io
import base64
from PIL import Image
from barcode import Code128
from barcode.writer import ImageWriter
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter
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
        if not self.connect():
            return False
        try:
            for _ in range(copies):
                self._serial.write(self.CMD_ALIGN_CENTER)
                self._serial.write(item_name.encode('utf-8') + b'\n')
                self.print_barcode(barcode)
                if price:
                    self._serial.write(f"السعر: {price}".encode('utf-8') + b'\n')
                self._serial.write(b'\n\n')
            self._serial.write(self.CMD_CUT)
            return True
        except Exception as e:
            print(f"خطأ في الطباعة: {e}")
            return False
        finally:
            self.disconnect()

    def print_receipt(self, lines: list, double_height: bool = False) -> bool:
        if not self.connect():
            return False
        try:
            self._serial.write(self.CMD_ALIGN_CENTER)
            self._serial.write("الراجحي للمحاسبة".encode('utf-8') + b'\n')
            self._serial.write(b'-' * 32 + b'\n')
            for line in lines:
                self._serial.write(line.encode('utf-8') + b'\n')
            self._serial.write(b'-' * 32 + b'\n')
            self._serial.write("شكراً لتعاملكم معنا".encode('utf-8') + b'\n\n')
            self._serial.write(self.CMD_CUT)
            return True
        except:
            return False
        finally:
            self.disconnect()

class PDFPrinter:
    def __init__(self, parent_widget=None):
        self.parent = parent_widget

    def _barcode_to_base64(self, barcode: str, symbology: str = 'AUTO') -> str:
        return barcode_label_service.barcode_png_base64(barcode, symbology)

    def print_label(self, barcode: str, item_name: str, price: str = "", copies: int = 1, options: dict | None = None) -> bool:
        if self.parent is None:
            print("خطأ: لا يوجد نافذة أبوية لفتح حوار الحفظ")
            return False
        filename, _ = QFileDialog.getSaveFileName(self.parent, "حفظ PDF", f"barcode_{item_name}.pdf", "PDF (*.pdf)")
        if not filename:
            return False
        item = {'barcode': barcode, 'name': item_name, 'price': price, 'copies': copies}
        html = barcode_label_service.labels_document_html([item], options or {'columns': 1})
        doc = QTextDocument()
        doc.setHtml(html)
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(filename)
        doc.print(printer)
        if self.parent:
            show_toast(f"تم حفظ PDF بنجاح: {os.path.basename(filename)}", "success", self.parent)
        return True

    def print_labels_batch(self, items_data: list, options: dict | None = None) -> bool:
        if self.parent is None:
            return False
        filename, _ = QFileDialog.getSaveFileName(self.parent, "حفظ الباركودات كـ PDF", "barcodes_batch.pdf", "PDF (*.pdf)")
        if not filename:
            return False
        html = barcode_label_service.labels_document_html(items_data, options or {})
        doc = QTextDocument()
        doc.setHtml(html)
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(filename)
        doc.print(printer)
        if self.parent:
            show_toast(f"تم حفظ PDF بنجاح: {os.path.basename(filename)}", "success", self.parent)
        return True

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


