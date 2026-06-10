# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QTableWidgetItem,
                             QPushButton, QSpinBox, QHeaderView, QMessageBox, QComboBox, QLabel,
                             QListWidget, QListWidgetItem, QDialogButtonBox, QTableView, QCheckBox)
from PyQt5.QtCore import Qt
from views.centered_dialog import CenteredDialog
from views.custom_table_view import CustomTableView
from models.table_models import GenericTableModel
from core.services.catalog_service import catalog_service
from utils import show_toast
from printing.thermal_printer import ThermalPrinter, PDFPrinter, ImagePrinter
from printer_manager import PrinterManager

class BatchPrintDialog(CenteredDialog):
    def __init__(self, parent=None, selected_items=None):
        super().__init__(parent)
        self.setWindowTitle("طباعة باركودات متعددة")
        self.resize(750, 550)
        self.selected_items = selected_items or []
        self.printer_manager = PrinterManager()
        self.printer_manager.load_default_printer()
        self.items_data = []

        # التأكد من وجود layout في content_widget
        if self.content_widget.layout() is None:
            QVBoxLayout(self.content_widget)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("الطابعة:"))
        self.printer_combo = QComboBox()
        for p in self.printer_manager.printers:
            self.printer_combo.addItem(p.name, p.id)
        toolbar.addWidget(self.printer_combo)

        self.copies_spin = QSpinBox()
        self.copies_spin.setRange(1, 10)
        self.copies_spin.setValue(1)
        toolbar.addWidget(QLabel("عدد النسخ:"))
        toolbar.addWidget(self.copies_spin)

        self.label_size_combo = QComboBox()
        self.label_size_combo.addItems(["40x30", "50x30", "60x40", "80mm"])
        self.label_size_combo.setCurrentText("50x30")
        toolbar.addWidget(QLabel("حجم الملصق:"))
        toolbar.addWidget(self.label_size_combo)

        self.symbology_combo = QComboBox()
        self.symbology_combo.addItems(["AUTO", "EAN13", "CODE128"])
        toolbar.addWidget(QLabel("النوع:"))
        toolbar.addWidget(self.symbology_combo)
        self.content_widget.layout().addLayout(toolbar)

        options_row = QHBoxLayout()
        self.show_company_check = QCheckBox("اسم الشركة")
        self.show_company_check.setChecked(True)
        self.show_name_check = QCheckBox("اسم المادة")
        self.show_name_check.setChecked(True)
        self.show_price_check = QCheckBox("السعر")
        self.show_price_check.setChecked(True)
        self.show_text_check = QCheckBox("رقم الباركود")
        self.show_text_check.setChecked(True)
        for chk in (self.show_company_check, self.show_name_check, self.show_price_check, self.show_text_check):
            options_row.addWidget(chk)
        options_row.addStretch()
        self.content_widget.layout().addLayout(options_row)

        self.table = CustomTableView()
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.content_widget.layout().addWidget(self.table)

        self.update_table_model()

        btn_row = QHBoxLayout()
        select_btn = QPushButton("➕ إضافة مواد")
        select_btn.clicked.connect(self.select_items)
        remove_btn = QPushButton("🗑 حذف المحدد")
        remove_btn.clicked.connect(self.remove_selected)
        print_btn = QPushButton("🖨️ طباعة")
        print_btn.clicked.connect(self.do_print)
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(select_btn)
        btn_row.addWidget(remove_btn)
        btn_row.addWidget(print_btn)
        btn_row.addWidget(cancel_btn)
        self.content_widget.layout().addLayout(btn_row)

        self.load_items()

    def update_table_model(self):
        data = []
        for idx, it in enumerate(self.items_data):
            data.append([idx, it['name'], it['barcode'], it['price'], it['copies']])
        headers = ["#", "المادة", "الباركود", "السعر", "عدد النسخ"]
        self.model = GenericTableModel(data, headers, data_keys=['id', 'name', 'barcode', 'price', 'copies'])
        self.table.setModel(self.model)
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def load_items(self):
        if self.selected_items:
            for item in self.selected_items:
                self.add_item_to_data(item)
        else:
            self.select_items()

    def add_item_to_data(self, item, copies=1):
        # item يمكن أن يكون كائنًا (من selected_items) أو قاموسًا (من select_items)
        # نتعامل مع الحالتين:
        if hasattr(item, 'id'):
            item_id = item.id
            item_name = item.name
            item_barcode = getattr(item, 'barcode', '')
            selling_price = getattr(item, 'selling_price', 0)
        else:
            item_id = item['id']
            item_name = item['name']
            item_barcode = item.get('barcode', '')
            selling_price = item.get('selling_price', 0)

        # التحقق من عدم التكرار
        for it in self.items_data:
            if it['id'] == item_id:
                return
        from currency import currency
        price_display = currency.format_amount(currency.convert(selling_price, 'USD', currency.get_display_currency()))
        self.items_data.append({
            'id': item_id,
            'name': item_name,
            'barcode': item_barcode,
            'price': price_display,
            'copies': copies
        })
        self.update_table_model()

    def select_items(self):
        dialog = CenteredDialog(self)
        dialog.setWindowTitle("اختر المواد")
        dialog.resize(550, 450)
        layout = QVBoxLayout(dialog.content_widget)
        items = catalog_service.items(limit=1000)  # قائمة موحدة من المواد
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.MultiSelection)
        for it in items:
            if it.get('barcode'):
                item_text = f"{it['name']} - {it.get('barcode')}"
                list_item = QListWidgetItem(item_text)
                list_item.setData(Qt.UserRole, it['id'])
                list_widget.addItem(list_item)
        layout.addWidget(list_widget)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec():
            for list_item in list_widget.selectedItems():
                item_id = list_item.data(Qt.UserRole)
                # البحث عن المادة الكاملة في القائمة الأصلية
                it = next((x for x in items if x['id'] == item_id), None)
                if it:
                    self.add_item_to_data(it)

    def remove_selected(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return
        rows = sorted([idx.row() for idx in selected], reverse=True)
        for row in rows:
            if row < len(self.items_data):
                self.items_data.pop(row)
        self.update_table_model()


    def _print_options(self):
        return {
            'label_size': self.label_size_combo.currentText(),
            'symbology': self.symbology_combo.currentText(),
            'show_company': self.show_company_check.isChecked(),
            'show_name': self.show_name_check.isChecked(),
            'show_price': self.show_price_check.isChecked(),
            'show_barcode_text': self.show_text_check.isChecked(),
            'columns': 1 if self.label_size_combo.currentText() == '80mm' else 2,
        }

    def do_print(self):
        if not self.items_data:
            show_toast("لا توجد مواد للطباعة", "error", self)
            return
        printer_id = self.printer_combo.currentData()
        printer_info = self.printer_manager.get_printer(printer_id)
        if not printer_info:
            show_toast("لم يتم اختيار طابعة", "error", self)
            return
        items_for_print = []
        for it in self.items_data:
            items_for_print.append({
                'barcode': it['barcode'],
                'name': it['name'],
                'price': it['price'],
                'copies': it.get('copies', self.copies_spin.value())
            })
        success = True
        if printer_info.type.value == 'serial':
            tp = ThermalPrinter(printer_info.connection_string, baudrate=9600)
            for item in items_for_print:
                if not tp.print_label(item['barcode'], item['name'], item['price'], item.get('copies', 1)):
                    success = False
        elif printer_info.type.value == 'pdf':
            pdf_printer = PDFPrinter(self)
            if pdf_printer.print_labels_batch(items_for_print, self._print_options()):
                show_toast("تم حفظ PDF بنجاح", "success", self)
                self.accept()
            else:
                show_toast("فشل حفظ PDF", "error", self)
            return
        elif printer_info.type.value == 'image':
            img_printer = ImagePrinter(self)
            for item in items_for_print:
                for _ in range(item['copies']):
                    if not img_printer.print_label(item['barcode'], item['name'], item['price'], 1):
                        success = False
        else:
            pdf_printer = PDFPrinter(self)
            if pdf_printer.print_labels_batch(items_for_print, self._print_options()):
                show_toast("تم حفظ PDF بنجاح", "success", self)
                self.accept()
            else:
                show_toast("فشل حفظ PDF", "error", self)
            return
        if success:
            show_toast("تمت الطباعة بنجاح", "success", self)
            self.accept()
        else:
            show_toast("حدثت بعض الأخطاء أثناء الطباعة", "error", self)


