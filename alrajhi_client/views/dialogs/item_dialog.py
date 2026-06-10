# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QFormLayout, QLineEdit, QDoubleSpinBox, QComboBox, QPushButton,
                             QHBoxLayout, QVBoxLayout, QMessageBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLabel, QWidget, QSplitter, QGroupBox, QApplication, QDialog,
                             QShortcut)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from views.centered_dialog import CenteredDialog
from core.services.product_service import product_service
from core.services.barcode_service import barcode_service, BarcodeError
from currency import currency
from utils import show_toast
from ui.form_validation import FormValidator, make_error_label

class ItemDialog(CenteredDialog):
    def __init__(self, parent=None, item_id=None):
        super().__init__(parent)
        self.item_id = item_id
        self.is_edit = item_id is not None
        self.setWindowTitle("تعديل مادة" if self.is_edit else "إضافة مادة جديدة")
        self.resize(950, 600)

        self.display_curr = currency.get_display_currency()
        self.symbol = currency.get_currency_symbol(self.display_curr)

        self.categories = product_service.categories()
        self.category_names = ["بدون تصنيف"] + [c.get('full_name') or c.get('name', '') for c in self.categories]

        self.setup_ui()
        if self.is_edit:
            self.load_item_data()
        self.setup_shortcuts()

    def setup_ui(self):
        main_layout = QVBoxLayout(self.content_widget)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(15)
        left_layout.setContentsMargins(10, 10, 10, 10)

        left_layout.addWidget(QLabel("اسم المادة:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("اسم المادة (مطلوب)")
        left_layout.addWidget(self.name_edit)
        self.name_error = make_error_label()
        left_layout.addWidget(self.name_error)

        left_layout.addWidget(QLabel("الباركود:"))
        barcode_widget = QWidget()
        barcode_layout = QHBoxLayout(barcode_widget)
        barcode_layout.setContentsMargins(0, 0, 0, 0)
        self.barcode_edit = QLineEdit()
        self.barcode_edit.setPlaceholderText("EAN-13 أو Code128")
        self.barcode_type_combo = QComboBox()
        self.barcode_type_combo.addItems(["EAN13", "CODE128"])
        if not self.is_edit:
            self.barcode_edit.setText(product_service.generate_barcode('EAN13'))
        generate_btn = QPushButton("إنشاء")
        generate_btn.clicked.connect(self.generate_barcode)
        camera_btn = QPushButton("📷 مسح")
        camera_btn.setToolTip("مسح باركود/QR بالكاميرا إن كانت متاحة")
        camera_btn.clicked.connect(self.scan_barcode_with_camera)
        barcode_layout.addWidget(self.barcode_edit)
        barcode_layout.addWidget(self.barcode_type_combo)
        barcode_layout.addWidget(generate_btn)
        barcode_layout.addWidget(camera_btn)
        left_layout.addWidget(barcode_widget)
        self.barcode_status_label = QLabel("")
        self.barcode_status_label.setStyleSheet("font-size: 11px; color: #666;")
        left_layout.addWidget(self.barcode_status_label)
        self.barcode_error = make_error_label()
        left_layout.addWidget(self.barcode_error)
        self.barcode_edit.textChanged.connect(self.update_barcode_status)
        self.update_barcode_status()

        left_layout.addWidget(QLabel("التصنيف:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.category_names)
        left_layout.addWidget(self.category_combo)

        left_layout.addWidget(QLabel("نوع المادة:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["مخزون", "منتج نهائي", "خدمة"])
        left_layout.addWidget(self.type_combo)

        left_layout.addWidget(QLabel("الوحدة الأساسية:"))
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("مثال: قطعة، كيلو، متر")
        left_layout.addWidget(self.unit_edit)
        self.unit_error = make_error_label()
        left_layout.addWidget(self.unit_error)

        prices_widget = QWidget()
        prices_layout = QHBoxLayout(prices_widget)
        prices_layout.setContentsMargins(0, 0, 0, 0)
        self.purchase_spin = QDoubleSpinBox()
        self.purchase_spin.setRange(0, 999999999)
        self.purchase_spin.setDecimals(2)
        self.purchase_spin.setPrefix(f"{self.symbol} ")
        self.selling_spin = QDoubleSpinBox()
        self.selling_spin.setRange(0, 999999999)
        self.selling_spin.setDecimals(2)
        self.selling_spin.setPrefix(f"{self.symbol} ")
        prices_layout.addWidget(QLabel("سعر الشراء:"))
        prices_layout.addWidget(self.purchase_spin)
        prices_layout.addWidget(QLabel("سعر البيع:"))
        prices_layout.addWidget(self.selling_spin)
        left_layout.addWidget(prices_widget)

        left_layout.addWidget(QLabel("الكمية الافتتاحية:"))
        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0, 999999)
        self.qty_spin.setDecimals(2)
        left_layout.addWidget(self.qty_spin)
        self.qty_error = make_error_label()
        left_layout.addWidget(self.qty_error)

        left_layout.addWidget(QLabel("حد إعادة الطلب:"))
        self.reorder_spin = QDoubleSpinBox()
        self.reorder_spin.setRange(0, 999999)
        self.reorder_spin.setDecimals(2)
        self.reorder_spin.setToolTip("عند وصول الكمية الحالية إلى هذا الحد تظهر المادة كمخزون منخفض. اتركه 0 لتعطيل التنبيه لهذه المادة.")
        left_layout.addWidget(self.reorder_spin)
        self.reorder_error = make_error_label()
        left_layout.addWidget(self.reorder_error)
        left_layout.addStretch()

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(15)
        right_layout.setContentsMargins(10, 10, 10, 10)

        units_group = QGroupBox("الوحدات الفرعية (للتحويل في الفواتير)")
        units_layout = QVBoxLayout(units_group)
        self.units_table = QTableWidget()
        self.units_table.setColumnCount(3)
        self.units_table.setHorizontalHeaderLabels(["الوحدة", "عامل التحويل", ""])
        self.units_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.units_table.setColumnWidth(2, 50)
        self.units_table.verticalHeader().setVisible(False)
        units_layout.addWidget(self.units_table)

        btn_units_layout = QHBoxLayout()
        add_unit_btn = QPushButton("➕ إضافة وحدة")
        add_unit_btn.clicked.connect(self.add_subunit)
        remove_unit_btn = QPushButton("🗑 حذف المحددة")
        remove_unit_btn.clicked.connect(self.remove_subunit)
        btn_units_layout.addWidget(add_unit_btn)
        btn_units_layout.addWidget(remove_unit_btn)
        units_layout.addLayout(btn_units_layout)
        right_layout.addWidget(units_group)
        right_layout.addStretch()

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([550, 350])

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("حفظ (Ctrl+S)")
        self.save_btn.setObjectName("primary")
        self.cancel_btn = QPushButton("إلغاء (Esc)")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(btn_layout)

        self.save_btn.clicked.connect(self.save)
        self.cancel_btn.clicked.connect(self.reject)


    def scan_barcode_with_camera(self):
        try:
            from views.dialogs.barcode_camera_dialog import BarcodeCameraDialog
            dialog = BarcodeCameraDialog(self)
            dialog.barcode_scanned.connect(self.on_camera_barcode_scanned)
            dialog.exec()
        except Exception as e:
            show_toast(f"تعذر تشغيل مسح الكاميرا: {e}", "error", self)

    def on_camera_barcode_scanned(self, value, symbology=None):
        self.barcode_edit.setText(str(value or '').strip())
        self.update_barcode_status()

    def generate_barcode(self):
        sym = self.barcode_type_combo.currentText()
        try:
            self.barcode_edit.setText(product_service.generate_barcode(sym))
            self.update_barcode_status()
        except Exception as e:
            show_toast(str(e), "error", self)

    def update_barcode_status(self):
        value = self.barcode_edit.text().strip()
        if not value:
            self.barcode_status_label.setText("اختياري: اتركه فارغًا أو أنشئ باركودًا تلقائيًا")
            self.barcode_status_label.setStyleSheet("font-size: 11px; color: #666;")
            return
        try:
            info = barcode_service.validate(value, allow_empty=False)
            self.barcode_status_label.setText(f"✓ باركود صالح ({info.symbology})")
            self.barcode_status_label.setStyleSheet("font-size: 11px; color: #2e7d32;")
        except BarcodeError as e:
            self.barcode_status_label.setText(f"✗ {e}")
            self.barcode_status_label.setStyleSheet("font-size: 11px; color: #c62828;")

    def add_subunit(self):
        from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDoubleSpinBox
        dialog = QDialog(self)
        dialog.setWindowTitle("إضافة وحدة فرعية")
        dialog.setLayoutDirection(Qt.RightToLeft)
        dialog.resize(350, 180)
        layout = QFormLayout(dialog)

        unit_name_edit = QLineEdit()
        unit_name_edit.setPlaceholderText("مثال: كرتونة، دستة")
        layout.addRow("اسم الوحدة:", unit_name_edit)

        factor_spin = QDoubleSpinBox()
        factor_spin.setRange(0.001, 999999)
        factor_spin.setValue(1.0)
        layout.addRow("عامل التحويل:", factor_spin)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("إضافة")
        cancel_btn = QPushButton("إلغاء")
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

        def on_add():
            name = unit_name_edit.text().strip()
            if not name:
                show_toast("اسم الوحدة مطلوب", "error", dialog)
                return
            factor = factor_spin.value()
            if factor <= 0:
                show_toast("عامل التحويل يجب أن يكون أكبر من صفر", "error", dialog)
                return
            row = self.units_table.rowCount()
            self.units_table.insertRow(row)
            self.units_table.setItem(row, 0, QTableWidgetItem(name))
            self.units_table.setItem(row, 1, QTableWidgetItem(str(factor)))
            del_btn = QPushButton("🗑")
            del_btn.setFixedSize(30, 30)
            del_btn.clicked.connect(lambda checked, r=row: self.units_table.removeRow(r))
            self.units_table.setCellWidget(row, 2, del_btn)
            dialog.accept()

        add_btn.clicked.connect(on_add)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec()

    def remove_subunit(self):
        row = self.units_table.currentRow()
        if row >= 0:
            self.units_table.removeRow(row)

    def load_item_data(self):
        item = product_service.item_by_id(self.item_id)
        if not item:
            show_toast("المادة غير موجودة", "error", self)
            self.reject()
            return

        self.name_edit.setText(item['name'])
        self.barcode_edit.setText(item.get('barcode') or '')
        if item.get('category_id'):
            cat = next((c for c in self.categories if c['id'] == item['category_id']), None)
            if cat:
                idx = self.category_combo.findText(cat['name'])
                if idx >= 0:
                    self.category_combo.setCurrentIndex(idx)
        self.type_combo.setCurrentText(item.get('item_type', 'مخزون'))
        self.unit_edit.setText(item.get('unit', ''))

        purchase_display = currency.convert(item.get('purchase_price', 0), 'USD', self.display_curr)
        selling_display = currency.convert(item.get('selling_price', 0), 'USD', self.display_curr)
        self.purchase_spin.setValue(float(purchase_display))
        self.selling_spin.setValue(float(selling_display))
        self.qty_spin.setValue(float(item.get('opening_quantity', item.get('quantity', 0))))
        self.reorder_spin.setValue(float(item.get('reorder_level', 0) or 0))

        subunits = product_service.item_units(self.item_id)
        self.units_table.setRowCount(len(subunits))
        for row, su in enumerate(subunits):
            self.units_table.setItem(row, 0, QTableWidgetItem(su['unit_name']))
            self.units_table.setItem(row, 1, QTableWidgetItem(str(su['conversion_factor'])))
            del_btn = QPushButton("🗑")
            del_btn.setFixedSize(30, 30)
            del_btn.clicked.connect(lambda checked, r=row: self.units_table.removeRow(r))
            self.units_table.setCellWidget(row, 2, del_btn)

    def setup_shortcuts(self):
        self.install_form_shortcuts(self.save)
        self.watch_dirty_widgets([
            self.name_edit, self.barcode_edit, self.category_combo, self.type_combo,
            self.unit_edit, self.purchase_spin, self.selling_spin, self.qty_spin, self.reorder_spin
        ], reset=True)

    def validate_form(self) -> bool:
        validator = FormValidator()
        validator.required(self.name_edit, self.name_error, "اسم المادة")
        validator.required(self.unit_edit, self.unit_error, "الوحدة الأساسية")
        validator.positive(self.qty_spin, self.qty_error, "الكمية الافتتاحية", allow_zero=True)
        validator.positive(self.reorder_spin, self.reorder_error, "حد إعادة الطلب", allow_zero=True)
        barcode = self.barcode_edit.text().strip()
        if barcode:
            try:
                barcode_service.validate(barcode, allow_empty=False)
                FormValidator.clear(self.barcode_error, self.barcode_edit)
            except BarcodeError as e:
                validator.custom(False, self.barcode_edit, self.barcode_error, str(e))
        else:
            FormValidator.clear(self.barcode_error, self.barcode_edit)
        if not validator.is_valid:
            validator.focus_first_invalid()
            show_toast("يرجى تصحيح الحقول المحددة", "error", self)
        return validator.is_valid

    def save(self):
        if not self.validate_form():
            return
        name = self.name_edit.text().strip()

        barcode = self.barcode_edit.text().strip() or None

        cat_name = self.category_combo.currentText()
        cat_id = None
        if cat_name != "بدون تصنيف":
            for c in self.categories:
                if (c.get('full_name') or c.get('name', '')) == cat_name:
                    cat_id = c['id']
                    break
            if cat_id is None:
                try:
                    cat_id = product_service.add_category(cat_name)
                    self.categories = product_service.categories()
                except Exception as e:
                    show_toast(f"فشل إنشاء التصنيف: {str(e)}", "error", self)
                    return

        item_type = self.type_combo.currentText()
        unit = self.unit_edit.text().strip()

        purchase_display = self.purchase_spin.value()
        selling_display = self.selling_spin.value()
        purchase_usd = currency.convert(purchase_display, self.display_curr, 'USD')
        selling_usd = currency.convert(selling_display, self.display_curr, 'USD')
        qty = self.qty_spin.value()

        data = {
            'name': name,
            'barcode': barcode,
            'category_id': cat_id,
            'item_type': item_type,
            'purchase_price': purchase_usd,
            'selling_price': selling_usd,
            'quantity': qty,
            'unit': unit,
            'average_cost': purchase_usd,
            'reorder_level': self.reorder_spin.value()
        }

        try:
            if self.is_edit:
                product_service.update_item(self.item_id, data)
                product_service.clear_units(self.item_id)
                for row in range(self.units_table.rowCount()):
                    unit_name = self.units_table.item(row, 0).text()
                    factor = float(self.units_table.item(row, 1).text())
                    product_service.add_unit(self.item_id, unit_name, factor)
                show_toast("تم التعديل", "success", self)
            else:
                new_id = product_service.add_item(data)
                for row in range(self.units_table.rowCount()):
                    unit_name = self.units_table.item(row, 0).text()
                    factor = float(self.units_table.item(row, 1).text())
                    product_service.add_unit(new_id, unit_name, factor)
                show_toast("تمت الإضافة", "success", self)
            self.accept()
        except Exception as e:
            show_toast(str(e), "error", self)


