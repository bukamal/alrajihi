# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QFormLayout, QLineEdit, QDoubleSpinBox, QComboBox, QPushButton,
                             QHBoxLayout, QVBoxLayout, QMessageBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QLabel, QWidget, QSplitter, QGroupBox, QApplication, QDialog,
                             QShortcut, QFrame)
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
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(14, 14, 14, 14)

        header_card = QFrame()
        header_card.setObjectName("HeaderCard")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(12)

        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        title_label = QLabel("📦 بيانات المادة" if not self.is_edit else "📦 تعديل بيانات المادة")
        title_label.setObjectName("DialogTitle")
        subtitle_label = QLabel("واجهة موحدة بدون تبويبات: بيانات أساسية، أسعار، مخزون، ووحدات في أقسام واضحة مثل الفواتير.")
        subtitle_label.setObjectName("DialogSubtitle")
        title_box.addWidget(title_label)
        title_box.addWidget(subtitle_label)
        header_layout.addLayout(title_box, 1)

        self.new_btn = QPushButton("جديد")
        self.new_btn.setObjectName("softAction")
        self.new_btn.clicked.connect(self.clear_for_new)
        self.top_save_btn = QPushButton("حفظ")
        self.top_save_btn.setObjectName("primary")
        self.top_save_btn.clicked.connect(self.save)
        self.top_cancel_btn = QPushButton("إلغاء")
        self.top_cancel_btn.clicked.connect(self.reject)
        header_layout.addWidget(self.new_btn)
        header_layout.addWidget(self.top_save_btn)
        header_layout.addWidget(self.top_cancel_btn)
        main_layout.addWidget(header_card)

        content_frame = QFrame()
        content_frame.setObjectName("ContentCard")
        content_layout = QHBoxLayout(content_frame)
        content_layout.setContentsMargins(14, 14, 14, 14)
        content_layout.setSpacing(12)

        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        general_group = QGroupBox("البيانات الأساسية")
        general_group.setObjectName("FormCard")
        general_form = QFormLayout(general_group)
        general_form.setLabelAlignment(Qt.AlignRight)
        general_form.setFormAlignment(Qt.AlignTop)
        general_form.setHorizontalSpacing(16)
        general_form.setVerticalSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("اسم المادة (مطلوب)")
        general_form.addRow("اسم المادة:", self.name_edit)
        self.name_error = make_error_label()
        general_form.addRow("", self.name_error)

        barcode_widget = QWidget()
        barcode_layout = QHBoxLayout(barcode_widget)
        barcode_layout.setContentsMargins(0, 0, 0, 0)
        barcode_layout.setSpacing(8)
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
        barcode_layout.addWidget(self.barcode_edit, 1)
        barcode_layout.addWidget(self.barcode_type_combo)
        barcode_layout.addWidget(generate_btn)
        barcode_layout.addWidget(camera_btn)
        general_form.addRow("الباركود:", barcode_widget)
        self.barcode_status_label = QLabel("")
        self.barcode_status_label.setStyleSheet("font-size: 11px; color: #666;")
        general_form.addRow("", self.barcode_status_label)
        self.barcode_error = make_error_label()
        general_form.addRow("", self.barcode_error)
        self.barcode_edit.textChanged.connect(self.update_barcode_status)

        self.category_combo = QComboBox()
        self.category_combo.addItems(self.category_names)
        general_form.addRow("التصنيف:", self.category_combo)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["مخزون", "منتج نهائي", "خدمة"])
        general_form.addRow("نوع المادة:", self.type_combo)

        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("مثال: قطعة، كيلو، متر")
        if not self.is_edit:
            self.unit_edit.setText("قطعة")
        general_form.addRow("الوحدة الأساسية:", self.unit_edit)
        self.unit_error = make_error_label()
        general_form.addRow("", self.unit_error)
        left_layout.addWidget(general_group)

        prices_group = QGroupBox("الأسعار")
        prices_group.setObjectName("FormCard")
        prices_form = QFormLayout(prices_group)
        prices_form.setLabelAlignment(Qt.AlignRight)
        prices_form.setHorizontalSpacing(16)
        prices_form.setVerticalSpacing(12)

        self.purchase_spin = QDoubleSpinBox()
        self.purchase_spin.setRange(0, 999999999)
        self.purchase_spin.setDecimals(2)
        self.purchase_spin.setPrefix(f"{self.symbol} ")
        prices_form.addRow("سعر الشراء:", self.purchase_spin)

        self.selling_spin = QDoubleSpinBox()
        self.selling_spin.setRange(0, 999999999)
        self.selling_spin.setDecimals(2)
        self.selling_spin.setPrefix(f"{self.symbol} ")
        prices_form.addRow("سعر البيع:", self.selling_spin)

        self.margin_label = QLabel("هامش الربح: —")
        self.margin_label.setObjectName("InfoLabel")
        prices_form.addRow("", self.margin_label)
        self.purchase_spin.valueChanged.connect(self.update_margin_preview)
        self.selling_spin.valueChanged.connect(self.update_margin_preview)
        left_layout.addWidget(prices_group)

        stock_group = QGroupBox("المخزون")
        stock_group.setObjectName("FormCard")
        stock_form = QFormLayout(stock_group)
        stock_form.setLabelAlignment(Qt.AlignRight)
        stock_form.setHorizontalSpacing(16)
        stock_form.setVerticalSpacing(12)

        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0, 999999)
        self.qty_spin.setDecimals(2)
        stock_form.addRow("الكمية الافتتاحية:", self.qty_spin)
        self.qty_error = make_error_label()
        stock_form.addRow("", self.qty_error)

        self.reorder_spin = QDoubleSpinBox()
        self.reorder_spin.setRange(0, 999999)
        self.reorder_spin.setDecimals(2)
        self.reorder_spin.setToolTip("عند وصول الكمية الحالية إلى هذا الحد تظهر المادة كمخزون منخفض. اتركه 0 لتعطيل التنبيه لهذه المادة.")
        stock_form.addRow("حد إعادة الطلب:", self.reorder_spin)
        self.reorder_error = make_error_label()
        stock_form.addRow("", self.reorder_error)

        self.stock_status_frame = QFrame()
        self.stock_status_frame.setObjectName("StockStatusFrame")
        stock_status_layout = QVBoxLayout(self.stock_status_frame)
        stock_status_layout.setContentsMargins(12, 10, 12, 10)
        self.current_stock_label = QLabel("الرصيد الحالي: —")
        self.current_stock_label.setObjectName("StockValueLabel")
        self.stock_warning_label = QLabel("لا يوجد تنبيه مخزون حالياً")
        self.stock_warning_label.setObjectName("StockWarningLabel")
        stock_status_layout.addWidget(self.current_stock_label)
        stock_status_layout.addWidget(self.stock_warning_label)
        stock_form.addRow("", self.stock_status_frame)

        self.qty_spin.valueChanged.connect(self.update_stock_preview)
        self.reorder_spin.valueChanged.connect(self.update_stock_preview)
        right_layout.addWidget(stock_group)

        units_group = QGroupBox("الوحدات الفرعية (للتحويل في الفواتير)")
        units_group.setObjectName("FormCard")
        units_layout = QVBoxLayout(units_group)
        self.units_table = QTableWidget()
        self.units_table.setColumnCount(3)
        self.units_table.setHorizontalHeaderLabels(["الوحدة", "عامل التحويل", ""])
        self.units_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.units_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.units_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.units_table.setColumnWidth(2, 58)
        self.units_table.verticalHeader().setVisible(False)
        self.units_table.setAlternatingRowColors(True)
        units_layout.addWidget(self.units_table)

        btn_units_layout = QHBoxLayout()
        add_unit_btn = QPushButton("➕ إضافة وحدة")
        add_unit_btn.clicked.connect(self.add_subunit)
        remove_unit_btn = QPushButton("🗑 حذف المحددة")
        remove_unit_btn.clicked.connect(self.remove_subunit)
        btn_units_layout.addStretch()
        btn_units_layout.addWidget(add_unit_btn)
        btn_units_layout.addWidget(remove_unit_btn)
        units_layout.addLayout(btn_units_layout)
        right_layout.addWidget(units_group, 1)

        content_layout.addWidget(left_column, 1)
        content_layout.addWidget(right_column, 1)
        main_layout.addWidget(content_frame, 1)

        action_card = QFrame()
        action_card.setObjectName("ActionCard")
        btn_layout = QHBoxLayout(action_card)
        btn_layout.setContentsMargins(12, 10, 12, 10)
        btn_layout.setSpacing(10)
        hint_label = QLabel("Ctrl+S للحفظ — Esc للإلغاء")
        hint_label.setObjectName("muted")
        self.save_btn = QPushButton("حفظ (Ctrl+S)")
        self.save_btn.setObjectName("primary")
        self.cancel_btn = QPushButton("إلغاء (Esc)")
        btn_layout.addWidget(hint_label)
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        main_layout.addWidget(action_card)

        self.save_btn.clicked.connect(self.save)
        self.cancel_btn.clicked.connect(self.reject)

        self.apply_modern_item_style()
        self.update_barcode_status()
        self.update_margin_preview()
        self.update_stock_preview()
        self.name_edit.setFocus()



    def apply_modern_item_style(self):
        accent = "#2563eb"
        self.setStyleSheet(self.styleSheet() + f"""
            QDialog {{
                background: #f8fafc;
            }}
            QLabel#DialogTitle {{
                color: #0f172a;
                font-size: 21px;
                font-weight: 800;
            }}
            QLabel#DialogSubtitle {{
                color: #64748b;
                font-size: 12px;
            }}
            QLabel#muted {{
                color: #64748b;
                font-size: 11px;
            }}
            QFrame#HeaderCard, QFrame#ActionCard, QFrame#ContentCard {{
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 14px;
            }}
            QGroupBox#FormCard {{
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 14px;
                margin-top: 14px;
                padding: 18px 14px 14px 14px;
                font-weight: 800;
                color: #0f172a;
            }}
            QGroupBox#FormCard::title {{
                subcontrol-origin: margin;
                right: 16px;
                padding: 0 8px;
                color: #0f172a;
                background: #ffffff;
            }}
            QLineEdit, QComboBox, QDoubleSpinBox {{
                min-height: 34px;
                border: 1px solid #cbd5e1;
                border-radius: 9px;
                padding: 5px 9px;
                background: #ffffff;
                font-size: 13px;
            }}
            QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {{
                border: 1px solid {accent};
                background: #f8fbff;
            }}
            QPushButton {{
                min-height: 34px;
                border-radius: 9px;
                padding: 6px 12px;
                border: 1px solid #cbd5e1;
                background: #ffffff;
                color: #0f172a;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: #f1f5f9; }}
            QPushButton#primary {{
                background: {accent};
                color: white;
                border: 1px solid {accent};
                font-weight: 800;
            }}
            QPushButton#softAction {{
                background: #f8fafc;
            }}
            QFrame#StockStatusFrame {{
                border: 1px solid #dbeafe;
                border-radius: 12px;
                background: #eff6ff;
            }}
            QLabel#StockValueLabel {{
                font-weight: 800;
                color: #1e3a8a;
            }}
            QLabel#StockWarningLabel, QLabel#InfoLabel {{
                color: #4b5563;
            }}
            QTableWidget {{
                background: #ffffff;
                alternate-background-color: #f8fafc;
                gridline-color: #e2e8f0;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                selection-background-color: #dbeafe;
                selection-color: #0f172a;
            }}
            QHeaderView::section {{
                background: #f1f5f9;
                color: #0f172a;
                font-weight: 700;
                padding: 8px;
                border: none;
                border-left: 1px solid #e2e8f0;
            }}
        """)

    def clear_for_new(self):
        if not self.is_edit:
            self.name_edit.clear()
            self.barcode_edit.setText(product_service.generate_barcode(self.barcode_type_combo.currentText()))
            self.category_combo.setCurrentIndex(0)
            self.type_combo.setCurrentIndex(0)
            self.unit_edit.setText("قطعة")
            self.purchase_spin.setValue(0)
            self.selling_spin.setValue(0)
            self.qty_spin.setValue(0)
            self.reorder_spin.setValue(0)
            self.units_table.setRowCount(0)
            self.update_barcode_status()
            self.update_margin_preview()
            self.update_stock_preview()
            self.name_edit.setFocus()
            return
        show_toast("زر جديد متاح عند إضافة مادة جديدة فقط", "info", self)

    def update_margin_preview(self):
        if not hasattr(self, 'margin_label'):
            return
        purchase = float(self.purchase_spin.value()) if hasattr(self, 'purchase_spin') else 0.0
        selling = float(self.selling_spin.value()) if hasattr(self, 'selling_spin') else 0.0
        profit = selling - purchase
        margin = (profit / selling * 100) if selling > 0 else 0.0
        self.margin_label.setText(f"هامش الربح: {profit:.2f} {self.symbol} ({margin:.1f}%)")
        if profit < 0:
            self.margin_label.setStyleSheet("color: #b91c1c; font-weight: 700;")
        elif profit > 0:
            self.margin_label.setStyleSheet("color: #047857; font-weight: 700;")
        else:
            self.margin_label.setStyleSheet("color: #4b5563;")

    def update_stock_preview(self):
        if not hasattr(self, 'current_stock_label'):
            return
        qty = float(self.qty_spin.value()) if hasattr(self, 'qty_spin') else 0.0
        reorder = float(self.reorder_spin.value()) if hasattr(self, 'reorder_spin') else 0.0
        self.current_stock_label.setText(f"الرصيد الحالي: {qty:.2f}")
        if reorder > 0 and qty <= reorder:
            self.stock_warning_label.setText("تنبيه: الرصيد الحالي أقل من أو يساوي حد إعادة الطلب")
            self.stock_warning_label.setStyleSheet("color: #b91c1c; font-weight: 700;")
            self.stock_status_frame.setStyleSheet("QFrame#StockStatusFrame { border: 1px solid #fecaca; border-radius: 10px; background: #fef2f2; }")
        else:
            self.stock_warning_label.setText("لا يوجد تنبيه مخزون حالياً")
            self.stock_warning_label.setStyleSheet("color: #047857; font-weight: 700;")
            self.stock_status_frame.setStyleSheet("QFrame#StockStatusFrame { border: 1px solid #dbeafe; border-radius: 10px; background: #eff6ff; }")

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
        self.unit_edit.setText(item.get('unit') or 'قطعة')

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
        unit = self.unit_edit.text().strip() or 'قطعة'

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
            units_payload = []
            for row in range(self.units_table.rowCount()):
                unit_item = self.units_table.item(row, 0)
                factor_item = self.units_table.item(row, 1)
                unit_name = unit_item.text().strip() if unit_item else ''
                if not unit_name:
                    continue
                factor = float(factor_item.text()) if factor_item and factor_item.text().strip() else 1
                units_payload.append({'unit_name': unit_name, 'conversion_factor': factor})

            if self.is_edit:
                product_service.update_item(self.item_id, data)
                product_service.replace_units(self.item_id, units_payload)
                show_toast("تم التعديل", "success", self)
            else:
                new_id = product_service.add_item(data)
                product_service.replace_units(new_id, units_payload)
                show_toast("تمت الإضافة", "success", self)
            self.accept()
        except Exception as e:
            show_toast(str(e), "error", self)


