# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QFormLayout, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QDoubleSpinBox, QTextEdit, QPushButton, QGroupBox, QTableView,
                             QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt
from i18n import translate, qt_layout_direction
from views.centered_dialog import CenteredDialog
from core.services.catalog_service import catalog_service
from core.services.manufacturing_service import manufacturing_service
from core.services.warehouse_service import warehouse_service
from models.table_models import GenericTableModel
from ui.smart_table_view import SmartTableView
from currency import currency
from utils import show_toast
from core.offline_guard import is_offline_read_error, offline_read_message
from ui.form_validation import FormValidator, make_error_label
from decimal import Decimal
from views.widgets.modern_ui import apply_modern_dialog

def _num(value, default=0):
    """Convert API/DB numeric strings, Decimal, int, float, None to float safely for UI formatting."""
    try:
        if value is None or value == '':
            return float(default)
        return float(Decimal(str(value)))
    except Exception:
        return float(default)


def _material_label(row):
    name = (row.get('item_name') or row.get('name') or '').strip()
    if name:
        return name
    item_id = row.get('item_id')
    return translate("material_id_fallback", id=item_id) if item_id else '-'

class ProductionOrderDialog(CenteredDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = manufacturing_service
        self.setWindowTitle(translate("new_production_order_title"))
        self.resize(600, 550)

        layout = QFormLayout(self.content_widget)

        self.product_combo = QComboBox()
        try:
            items = catalog_service.items()
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(translate('manufacturing_products_offline')), 'warning', self)
                items = []
            else:
                raise
        self.product_bom_map = {}
        for it in items:
            if it.get('item_type') == 'منتج نهائي':
                bom = self.service.get_bom_for_product(it['id'])
                price_display = currency.format_amount(currency.convert(it.get('selling_price', 0), currency.storage_currency(), currency.get_display_currency()))
                if bom:
                    self.product_combo.addItem(f"{it['name']} ({price_display})", it['id'])
                else:
                    self.product_combo.addItem(f"{it['name']} ({price_display}) - {translate('no_bom_for_product')}", it['id'])
                self.product_bom_map[it['id']] = bom
        layout.addRow(translate("product_label"), self.product_combo)

        self.raw_warehouse_combo = QComboBox()
        self.output_warehouse_combo = QComboBox()
        self._load_warehouses()
        layout.addRow(translate("raw_warehouse_label"), self.raw_warehouse_combo)
        layout.addRow(translate("output_warehouse_label"), self.output_warehouse_combo)
        self.raw_warehouse_combo.currentIndexChanged.connect(self.update_materials_display)
        self.output_warehouse_combo.currentIndexChanged.connect(self.update_materials_display)

        self.product_error = make_error_label()
        layout.addRow("", self.product_error)

        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0.01, 999999)
        self.qty_spin.setValue(1)
        layout.addRow(translate("planned_quantity_label"), self.qty_spin)
        self.qty_error = make_error_label()
        layout.addRow("", self.qty_error)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        layout.addRow(translate("notes_label"), self.notes_edit)

        self.materials_group = QGroupBox(translate("required_materials_group"))
        materials_layout = QVBoxLayout(self.materials_group)
        self.materials_table = SmartTableView(identity='production_order.materials')
        self.materials_table.setMinimumHeight(200)
        materials_layout.addWidget(self.materials_table)
        layout.addRow(self.materials_group)
        self.materials_group.setVisible(False)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton(translate("create_ctrl_s"))
        self.save_btn.setObjectName("primary")
        cancel_btn = QPushButton(translate("cancel_esc"))
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

        self.product_combo.currentIndexChanged.connect(self.update_materials_display)
        self.qty_spin.valueChanged.connect(self.update_materials_display)
        self.save_btn.clicked.connect(self.save)
        cancel_btn.clicked.connect(self.reject)
        self.install_form_shortcuts(self.save)
        apply_modern_dialog(self, translate('production_order'))
        self.watch_dirty_widgets([self.product_combo, self.raw_warehouse_combo, self.output_warehouse_combo, self.qty_spin, self.notes_edit], reset=True)
        self.update_materials_display()

    def _load_warehouses(self):
        try:
            warehouses = warehouse_service.warehouses()
            default_id = warehouse_service.default_warehouse_id()
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(translate('manufacturing_warehouses_offline')), 'warning', self)
                warehouses = []
                default_id = None
            else:
                raise
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
            if is_offline_read_error(e):
                show_toast(offline_read_message(translate('manufacturing_items_offline')), 'warning', self)
            else:
                show_toast(translate("bom_parse_error", error=str(e)), "error", self)
            return
        data = []
        for mat in required:
            required_qty = _num(mat.get('required_qty'))
            available_qty = _num(mat.get('available_qty'))
            status = translate("sufficient") if bool(mat.get('is_sufficient')) else translate("insufficient")
            data.append({
                'item': _material_label(mat),
                'required': f"{required_qty:.2f}",
                'available': f"{available_qty:.2f}",
                'status': status
            })
        headers = [translate("item_header"), translate("required_qty"), translate("available_qty"), translate("status")]
        model = GenericTableModel(data, headers, data_keys=['item', 'required', 'available', 'status'])
        self.materials_table.setModel(model)
        self.materials_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.materials_group.setVisible(True)

    def save(self):
        validator = FormValidator()
        product_id = self.product_combo.currentData()
        validator.custom(bool(product_id), self.product_combo, self.product_error, translate("product"))
        validator.positive(self.qty_spin, self.qty_error, translate("quantity"))
        if not validator.is_valid:
            validator.focus_first_invalid()
            return
        qty = Decimal(str(self.qty_spin.value()))
        notes = self.notes_edit.toPlainText().strip()

        bom = self.product_bom_map.get(product_id)
        if not bom:
            show_toast(translate("no_bom_for_product_msg"), "error", self)
            return

        try:
            required = self.service.get_required_materials_recursive(product_id, qty)
        except Exception as e:
            show_toast(str(e), "error", self)
            return
        insufficient = [m for m in required if not bool(m.get('is_sufficient'))]
        if insufficient:
            msg = translate("insufficient_materials_title") + "\n".join(
                "- " + translate("insufficient_material_line", item=_material_label(m), required=_num(m.get('required_qty')), available=_num(m.get('available_qty')))
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
            show_toast(translate("production_order_created", number=order_id), "success", self)
            self.accept()
        except Exception as e:
            show_toast(str(e), "error", self)



# Phase110 offline guard markers: مستودعات التصنيع
