# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QFormLayout, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QDoubleSpinBox, QTextEdit, QPushButton, QGroupBox, QTableView,
                             QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt
from views.centered_dialog import CenteredDialog
from core.services.catalog_service import catalog_service
from core.services.manufacturing_service import manufacturing_service
from core.services.warehouse_service import warehouse_service
from models.table_models import GenericTableModel
from views.custom_table_view import CustomTableView
from currency import currency
from utils import show_toast
from ui.form_validation import FormValidator, make_error_label
from decimal import Decimal
from views.widgets.modern_ui import apply_modern_dialog

class ProductionOrderDialog(CenteredDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = manufacturing_service
        self.setWindowTitle("أمر إنتاج جديد")
        self.resize(600, 550)

        layout = QFormLayout(self.content_widget)

        self.product_combo = QComboBox()
        items = catalog_service.items()
        self.product_bom_map = {}
        for it in items:
            if it.get('item_type') == 'منتج نهائي':
                bom = self.service.get_bom_for_product(it['id'])
                price_display = currency.format_amount(currency.convert(it.get('selling_price', 0), 'USD', currency.get_display_currency()))
                if bom:
                    self.product_combo.addItem(f"{it['name']} ({price_display})", it['id'])
                else:
                    self.product_combo.addItem(f"{it['name']} ({price_display}) - ⚠️ لا توجد BOM", it['id'])
                self.product_bom_map[it['id']] = bom
        layout.addRow("المنتج:", self.product_combo)

        self.raw_warehouse_combo = QComboBox()
        self.output_warehouse_combo = QComboBox()
        self._load_warehouses()
        layout.addRow("مستودع المواد الخام:", self.raw_warehouse_combo)
        layout.addRow("مستودع المنتج النهائي:", self.output_warehouse_combo)
        self.raw_warehouse_combo.currentIndexChanged.connect(self.update_materials_display)
        self.output_warehouse_combo.currentIndexChanged.connect(self.update_materials_display)

        self.product_error = make_error_label()
        layout.addRow("", self.product_error)

        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0.01, 999999)
        self.qty_spin.setValue(1)
        layout.addRow("الكمية المخططة:", self.qty_spin)
        self.qty_error = make_error_label()
        layout.addRow("", self.qty_error)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        layout.addRow("ملاحظات:", self.notes_edit)

        self.materials_group = QGroupBox("المواد المطلوبة (حسب BOM - متعدد المستويات)")
        materials_layout = QVBoxLayout(self.materials_group)
        self.materials_table = CustomTableView()
        self.materials_table.setMinimumHeight(200)
        materials_layout.addWidget(self.materials_table)
        layout.addRow(self.materials_group)
        self.materials_group.setVisible(False)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("إنشاء (Ctrl+S)")
        self.save_btn.setObjectName("primary")
        cancel_btn = QPushButton("إلغاء (Esc)")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

        self.product_combo.currentIndexChanged.connect(self.update_materials_display)
        self.qty_spin.valueChanged.connect(self.update_materials_display)
        self.save_btn.clicked.connect(self.save)
        cancel_btn.clicked.connect(self.reject)
        self.install_form_shortcuts(self.save)
        apply_modern_dialog(self, 'أمر إنتاج')
        self.watch_dirty_widgets([self.product_combo, self.raw_warehouse_combo, self.output_warehouse_combo, self.qty_spin, self.notes_edit], reset=True)
        self.update_materials_display()

    def _load_warehouses(self):
        warehouses = warehouse_service.warehouses()
        default_id = warehouse_service.default_warehouse_id()
        for combo in (self.raw_warehouse_combo, self.output_warehouse_combo):
            combo.clear()
            for wh in warehouses:
                label = wh.get('name', '')
                combo.addItem(label, wh.get('id'))
                if default_id and int(wh.get('id') or 0) == int(default_id):
                    combo.setCurrentIndex(combo.count() - 1)

    def update_materials_display(self):
        product_id = self.product_combo.currentData()
        planned_qty = Decimal(str(self.qty_spin.value()))
        if not product_id:
            self.materials_group.setVisible(False)
            return
        try:
            required = self.service.get_required_materials_recursive(product_id, planned_qty, self.raw_warehouse_combo.currentData())
        except Exception as e:
            self.materials_group.setVisible(False)
            show_toast(f"خطأ في تحليل BOM: {str(e)}", "error", self)
            return
        data = []
        for mat in required:
            status = "✅ كافٍ" if mat['is_sufficient'] else "❌ غير كافٍ"
            data.append({
                'item': mat['item_name'],
                'required': f"{mat['required_qty']:.2f}",
                'available': f"{mat['available_qty']:.2f}",
                'status': status
            })
        headers = ["المادة", "الكمية المطلوبة", "الكمية المتوفرة", "الحالة"]
        model = GenericTableModel(data, headers, data_keys=['item', 'required', 'available', 'status'])
        self.materials_table.setModel(model)
        self.materials_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.materials_group.setVisible(True)

    def save(self):
        validator = FormValidator()
        product_id = self.product_combo.currentData()
        validator.custom(bool(product_id), self.product_combo, self.product_error, "اختر المنتج")
        validator.positive(self.qty_spin, self.qty_error, "الكمية")
        if not validator.is_valid:
            validator.focus_first_invalid()
            return
        qty = Decimal(str(self.qty_spin.value()))
        notes = self.notes_edit.toPlainText().strip()

        bom = self.product_bom_map.get(product_id)
        if not bom:
            show_toast("لا توجد قائمة مواد (BOM) لهذا المنتج", "error", self)
            return

        try:
            required = self.service.get_required_materials_recursive(product_id, qty)
        except Exception as e:
            show_toast(str(e), "error", self)
            return
        insufficient = [m for m in required if not m['is_sufficient']]
        if insufficient:
            msg = "المواد التالية غير كافية:\n" + "\n".join(
                f"- {m['item_name']}: المطلوب {m['required_qty']:.2f}، المتوفر {m['available_qty']:.2f}"
                for m in insufficient
            )
            show_toast(msg, "error", self)
            return

        try:
            order_id = self.service.create_production_order(
                product_id, qty, notes,
                raw_warehouse_id=self.raw_warehouse_combo.currentData(),
                output_warehouse_id=self.output_warehouse_combo.currentData()
            )
            show_toast(f"تم إنشاء أمر الإنتاج رقم {order_id}", "success", self)
            self.accept()
        except Exception as e:
            show_toast(str(e), "error", self)


