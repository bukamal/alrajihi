# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDoubleSpinBox,
                             QDateEdit, QTextEdit, QFormLayout, QMessageBox, QShortcut, QLineEdit,
                             QApplication, QTableView, QHeaderView, QAbstractItemView, QWidget,
                             QStyledItemDelegate, QCompleter, QPushButton, QSpinBox, QCheckBox, QFrame,
                             QSplitter)
from PyQt5.QtCore import Qt, QDate, QAbstractTableModel, QModelIndex, QStringListModel
from PyQt5.QtGui import QKeySequence
from decimal import Decimal

from core.services.product_service import product_service
from core.services.catalog_service import catalog_service
from core.services.invoice_service import invoice_service
from core.services.warehouse_service import warehouse_service
from currency import currency
from views.centered_dialog import CenteredDialog
from utils import show_toast
from ui.form_validation import FormValidator, make_error_label
import qtawesome as qta

class LinesModel(QAbstractTableModel):
    COL_ITEM_ID = 0
    COL_ITEM_NAME = 1
    COL_QUANTITY = 2
    COL_UNIT = 3
    COL_PRICE = 4
    COL_TOTAL = 5
    COL_DELETE = 6

    def __init__(self, inv_type, parent=None):
        super().__init__(parent)
        self.inv_type = inv_type
        self.display_curr = currency.get_display_currency()
        self.lines = []

    def rowCount(self, parent=QModelIndex()):
        return len(self.lines)

    def columnCount(self, parent=QModelIndex()):
        return 7

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        line = self.lines[row]
        if col == self.COL_DELETE:
            if role == Qt.DisplayRole:
                return "🗑"
            elif role == Qt.TextAlignmentRole:
                return Qt.AlignCenter
            return None
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if col == self.COL_ITEM_ID:
                return line.get('item_id', 0)
            elif col == self.COL_ITEM_NAME:
                return line.get('item_name', '')
            elif col == self.COL_QUANTITY:
                return f"{line['qty']:.2f}"
            elif col == self.COL_UNIT:
                return line.get('unit_display', '')
            elif col == self.COL_PRICE:
                return f"{line['price']:.2f}"
            elif col == self.COL_TOTAL:
                return f"{line['total']:.2f} {self.display_curr}"
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        row = index.row()
        col = index.column()
        line = self.lines[row]
        try:
            if col == self.COL_QUANTITY:
                qty = Decimal(str(value))
                if qty <= 0:
                    return False
                line['qty'] = qty
            elif col == self.COL_UNIT:
                if isinstance(value, tuple) and len(value) == 3:
                    line['unit_id'] = value[0]
                    line['unit_display'] = value[1]
                    line['conversion_factor'] = value[2]
                else:
                    line['unit_display'] = value
            elif col == self.COL_PRICE:
                price = Decimal(str(value))
                if price < 0:
                    return False
                line['price'] = price
            else:
                return False
            line['total'] = line['qty'] * line['price']
            self.dataChanged.emit(self.index(row, self.COL_TOTAL), self.index(row, self.COL_TOTAL))
            self.dataChanged.emit(index, index)
            return True
        except:
            return False

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        if index.column() == self.COL_DELETE:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() in (self.COL_ITEM_NAME, self.COL_QUANTITY, self.COL_UNIT, self.COL_PRICE):
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            headers = ["#", "المادة", "الكمية", "الوحدة", "السعر", "الإجمالي", ""]
            return headers[section]
        return None

    def add_empty_row(self):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.lines.append({
            'item_id': None,
            'item_name': '',
            'qty': Decimal('1'),
            'unit_id': None,
            'unit_display': '',
            'conversion_factor': Decimal('1'),
            'price': Decimal('0'),
            'total': Decimal('0'),
            'notes': '',
            'units_data': []
        })
        self.endInsertRows()

    def remove_row(self, row):
        if 0 <= row < self.rowCount():
            self.beginRemoveRows(QModelIndex(), row, row)
            del self.lines[row]
            self.endRemoveRows()

    def set_item(self, row, item_id, item_name, units_data, default_price):
        if 0 <= row < self.rowCount():
            self.lines[row]['item_id'] = item_id
            self.lines[row]['item_name'] = item_name
            self.lines[row]['units_data'] = units_data
            if units_data and len(units_data) > 0:
                first = units_data[0]
                self.lines[row]['unit_id'] = first.get('id')
                self.lines[row]['unit_display'] = first.get('unit_name', '')
                self.lines[row]['conversion_factor'] = first.get('conversion_factor', Decimal('1'))
            else:
                self.lines[row]['unit_id'] = None
                self.lines[row]['unit_display'] = ''
                self.lines[row]['conversion_factor'] = Decimal('1')
            self.lines[row]['price'] = default_price
            self.lines[row]['total'] = self.lines[row]['qty'] * default_price
            self.dataChanged.emit(self.index(row, 0), self.index(row, self.columnCount()-1))

    def load_invoice_lines(self, lines):
        def val(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        self.beginResetModel()
        self.lines.clear()
        for line in lines or []:
            item_id = val(line, 'item_id')
            units = product_service.item_units(item_id)
            base_unit = val(line, 'unit', 'قطعة') or 'قطعة'
            units_list = [{'id': None, 'unit_name': base_unit, 'conversion_factor': Decimal('1')}]
            for u in units:
                if not isinstance(u, dict):
                    continue
                factor = Decimal(str(u.get('conversion_factor', 1)))
                if factor == 0:
                    factor = Decimal('1')
                units_list.append({'id': u.get('id'), 'unit_name': u.get('unit_name', ''), 'conversion_factor': factor})
            current_unit = base_unit
            current_factor = Decimal('1')
            current_unit_id = None
            for u in units_list:
                if u.get('unit_name') == current_unit:
                    current_factor = u.get('conversion_factor', Decimal('1'))
                    current_unit_id = u.get('id')
                    break
            stored_factor = val(line, 'conversion_factor')
            if stored_factor is not None and Decimal(str(stored_factor)) > 0:
                current_factor = Decimal(str(stored_factor))
            quantity = Decimal(str(val(line, 'quantity', 0) or 0))
            unit_price = Decimal(str(val(line, 'unit_price', 0) or 0))
            total = Decimal(str(val(line, 'total', 0) or 0))
            price_display = currency.convert(unit_price, 'USD', self.display_curr)
            total_display = currency.convert(total, 'USD', self.display_curr)
            self.lines.append({
                'item_id': item_id,
                'item_name': val(line, 'item_name', '') or '',
                'qty': quantity,
                'unit_id': current_unit_id,
                'unit_display': current_unit,
                'conversion_factor': current_factor,
                'price': price_display,
                'total': total_display,
                'notes': val(line, 'description', '') or '',
                'units_data': units_list
            })
        self.endResetModel()
        if not self.lines:
            self.add_empty_row()

    def get_lines_data(self):
        result = []
        for line in self.lines:
            if line['item_id'] is None:
                continue
            base_qty = line['qty'] * line.get('conversion_factor', Decimal('1'))
            price_usd = currency.convert(line['price'], self.display_curr, 'USD')
            total_usd = currency.convert(line['total'], self.display_curr, 'USD')
            result.append({
                'item_id': line['item_id'],
                'quantity': line['qty'],
                'unit': line.get('unit_display', ''),
                'conversion_factor': line.get('conversion_factor', Decimal('1')),
                'base_qty': base_qty,
                'unit_price': price_usd,
                'total': total_usd,
                'description': line.get('notes', '')
            })
        return result

    def update_row_total(self, row):
        if 0 <= row < self.rowCount():
            line = self.lines[row]
            line['total'] = line['qty'] * line['price']
            self.dataChanged.emit(self.index(row, self.COL_TOTAL), self.index(row, self.COL_TOTAL))

class InvoiceDialog(CenteredDialog):
    def __init__(self, inv_type, parent=None, invoice_id=None):
        super().__init__(parent)
        self.inv_type = inv_type
        self.invoice_id = invoice_id
        self.display_curr = currency.get_display_currency()
        self.symbol = currency.get_currency_symbol(self.display_curr)
        self.items_for_combo = []
        self.customers = []
        self.suppliers = []
        self.selected_entity_id = None
        self._updating_payment = False
        self._paid_manually_changed = False
        self.setWindowTitle(f"تعديل فاتورة {'بيع' if inv_type=='sale' else 'شراء'}" if invoice_id else f"فاتورة {'بيع' if inv_type=='sale' else 'شراء'} جديدة")
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(1200, 700)

        self.init_ui()
        self.setup_shortcuts()
        self.load_items_for_combo()
        self.load_entities()
        if invoice_id:
            self.load_invoice_data(invoice_id)
        self.update_total_display()

    def load_invoice_data(self, invoice_id):
        inv = invoice_service.get(invoice_id)
        if not inv:
            show_toast("الفاتورة غير موجودة", "error", self)
            self.reject()
            return
        # التحقق من اختلاف الأسعار
        self.check_price_differences(inv)
        if self.inv_type == 'sale':
            if inv.get('customer_id'):
                cust = next((c for c in self.customers if c.get('id') == inv['customer_id']), None)
                if cust:
                    self.entity_search.setText(cust.get('name', ''))
                    self.selected_entity_id = cust.get('id')
            else:
                self.entity_search.setText("نقدي")
                self.selected_entity_id = None
        else:
            if inv.get('supplier_id'):
                supp = next((s for s in self.suppliers if s.get('id') == inv['supplier_id']), None)
                if supp:
                    self.entity_search.setText(supp.get('name', ''))
                    self.selected_entity_id = supp.get('id')
            else:
                self.entity_search.setText("نقدي")
                self.selected_entity_id = None
        self.date_edit.setDate(QDate.fromString(inv['date'], "yyyy-MM-dd"))
        self.ref_edit.setText(inv.get('reference', ''))
        self.notes_edit.setPlainText(inv.get('notes', ''))
        self.lines_model.load_invoice_lines(inv.get('lines', []))
        self.update_total_display()

    def check_price_differences(self, invoice):
        """التحقق من اختلاف أسعار المواد الحالية عن المسجلة في الفاتورة"""
        changes = []
        for line in invoice.get('lines', []):
            item = product_service.item_by_id(line.get('item_id') if isinstance(line, dict) else getattr(line, 'item_id', None))
            if not item:
                continue
            current_price = item.get('selling_price' if invoice['type'] == 'sale' else 'purchase_price', 0)
            current_price_display = currency.convert(current_price, 'USD', self.display_curr)
            old_price = line.get('unit_price') if isinstance(line, dict) else getattr(line, 'unit_price', 0)
            old_price_display = currency.convert(old_price, 'USD', self.display_curr)
            if abs(current_price_display - old_price_display) > 0.01:
                changes.append(f"{item['name']}: كان {currency.format_amount(old_price_display)}، الآن {currency.format_amount(current_price_display)}")
        if changes:
            msg = "تغيرت أسعار بعض المواد منذ إنشاء الفاتورة:\n" + "\n".join(changes) + "\n\nهل تريد تحديث الأسعار إلى الأسعار الحالية؟"
            reply = QMessageBox.question(self, "تحديث الأسعار", msg, QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                for idx, line in enumerate(self.lines_model.lines):
                    if line['item_id']:
                        item = product_service.item_by_id(line['item_id'])
                        if item:
                            new_price = item.get('selling_price' if self.inv_type == 'sale' else 'purchase_price', 0)
                            new_price_display = currency.convert(new_price, 'USD', self.display_curr)
                            self.lines_model.setData(self.lines_model.index(idx, LinesModel.COL_PRICE), new_price_display, Qt.EditRole)
                self.update_total_display()

    def init_ui(self):
        main_layout = QHBoxLayout(self.content_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # اللوحة اليمنى
        right_panel = QFrame()
        right_panel.setObjectName("RightPanel")
        right_panel.setFixedWidth(320)
        right_panel.setStyleSheet("""
            #RightPanel {
                background-color: palette(alternate-base);
                border-radius: 12px;
                padding: 15px;
            }
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(12)

        right_layout.addWidget(QLabel("العميل:" if self.inv_type == 'sale' else "المورد:"))
        self.entity_search = QLineEdit()
        self.entity_search.setPlaceholderText("نقدي (اتركه فارغاً) أو ابدأ بكتابة الاسم")
        self.entity_search.textChanged.connect(self.on_entity_text_changed)
        self.entity_completer = QCompleter()
        self.entity_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.entity_completer.activated.connect(self.on_entity_selected)
        self.entity_search.setCompleter(self.entity_completer)
        right_layout.addWidget(self.entity_search)

        self.balance_label = QLabel()
        self.balance_label.setWordWrap(True)
        self.balance_label.setStyleSheet("color: #3b82f6; font-size: 12px;")
        right_layout.addWidget(self.balance_label)

        self.add_entity_btn = QPushButton("➕ إضافة جديد")
        self.add_entity_btn.setFixedHeight(30)
        self.add_entity_btn.clicked.connect(self.add_new_entity)
        right_layout.addWidget(self.add_entity_btn)

        right_layout.addWidget(QLabel("التاريخ:"))
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        right_layout.addWidget(self.date_edit)

        right_layout.addWidget(QLabel("المستودع:" if self.inv_type == 'sale' else "مستودع الاستلام:"))
        self.warehouse_combo = QComboBox()
        self._load_warehouses()
        self.warehouse_combo.currentIndexChanged.connect(lambda *_: self.update_warehouse_availability_label())
        right_layout.addWidget(self.warehouse_combo)
        self.warehouse_availability_label = QLabel("اختر مستودعاً لعرض الرصيد المتاح")
        self.warehouse_availability_label.setObjectName("muted")
        self.warehouse_availability_label.setWordWrap(True)
        right_layout.addWidget(self.warehouse_availability_label)

        right_layout.addWidget(QLabel("المرجع:"))
        self.ref_edit = QLineEdit()
        self.ref_edit.setPlaceholderText("يُولد تلقائياً")
        right_layout.addWidget(self.ref_edit)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: palette(mid);")
        right_layout.addWidget(line)

        right_layout.addWidget(QLabel("الخصم:"))
        discount_container = QWidget()
        discount_layout = QHBoxLayout(discount_container)
        discount_layout.setContentsMargins(0, 0, 0, 0)
        self.discount_type = QComboBox()
        self.discount_type.addItems(["نسبة %", "مبلغ"])
        self.discount_value = QDoubleSpinBox()
        self.discount_value.setRange(0, 999999999)
        self.discount_value.setDecimals(2)
        self.discount_value.setPrefix(f"{self.symbol} ")
        discount_layout.addWidget(self.discount_type)
        discount_layout.addWidget(self.discount_value)
        right_layout.addWidget(discount_container)

        right_layout.addWidget(QLabel("المدفوع:"))
        self.paid_spin = QDoubleSpinBox()
        self.paid_spin.setRange(0, 999999999)
        self.paid_spin.setDecimals(2)
        self.paid_spin.setPrefix(f"{self.symbol} ")
        right_layout.addWidget(self.paid_spin)

        payment_tools = QHBoxLayout()
        self.full_payment_btn = QPushButton("دفع كامل")
        self.no_payment_btn = QPushButton("آجل")
        self.full_payment_btn.setFixedHeight(28)
        self.no_payment_btn.setFixedHeight(28)
        payment_tools.addWidget(self.full_payment_btn)
        payment_tools.addWidget(self.no_payment_btn)
        right_layout.addLayout(payment_tools)

        self.total_before_label = QLabel("الإجمالي قبل الخصم: 0")
        self.discount_amount_label = QLabel("الخصم: 0")
        self.total_after_label = QLabel("الإجمالي بعد الخصم: 0")
        self.remaining_label = QLabel("المتبقي: 0")
        for lbl in (self.total_before_label, self.discount_amount_label, self.total_after_label, self.remaining_label):
            lbl.setStyleSheet("font-weight: bold; margin-top: 5px;")
            right_layout.addWidget(lbl)

        right_layout.addStretch()

        btn_layout = QHBoxLayout()
        self.form_error_label = make_error_label()
        main_layout.addWidget(self.form_error_label)

        self.save_btn = QPushButton("حفظ (Ctrl+S)")
        self.save_btn.setObjectName("primary")
        self.print_btn = QPushButton("طباعة (F6)")
        self.cancel_btn = QPushButton("إلغاء (Esc)")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.print_btn)
        btn_layout.addWidget(self.cancel_btn)
        right_layout.addLayout(btn_layout)

        # اللوحة اليسرى
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث سريع: اسم المادة أو الباركود — Enter للإضافة، 📷 للمسح")
        self.search_input.returnPressed.connect(self.add_item_from_search)
        self.camera_scan_btn = QPushButton("📷 مسح")
        self.camera_scan_btn.setToolTip("مسح باركود أو QR بالكاميرا. يعمل قارئ USB أيضًا داخل حقل البحث مباشرة.")
        self.camera_scan_btn.clicked.connect(self.scan_barcode_with_camera)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.camera_scan_btn)
        left_layout.addLayout(search_layout)

        self.lines_model = LinesModel(self.inv_type)
        self.lines_table = QTableView()
        self.lines_table.setModel(self.lines_model)
        self.lines_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.lines_table.setAlternatingRowColors(True)
        self.lines_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.lines_table.verticalHeader().setVisible(False)
        self.lines_table.setColumnHidden(LinesModel.COL_ITEM_ID, True)
        self.lines_table.setColumnWidth(LinesModel.COL_DELETE, 50)

        from views.dialogs.invoice_delegates import ItemComboDelegate, UnitComboBoxDelegate, DoubleSpinDelegate
        self.item_delegate = ItemComboDelegate(self.items_for_combo, self.lines_table)
        self.lines_table.setItemDelegateForColumn(LinesModel.COL_ITEM_NAME, self.item_delegate)
        self.unit_delegate = UnitComboBoxDelegate()
        self.lines_table.setItemDelegateForColumn(LinesModel.COL_UNIT, self.unit_delegate)
        self.double_delegate = DoubleSpinDelegate()
        self.lines_table.setItemDelegateForColumn(LinesModel.COL_QUANTITY, self.double_delegate)
        self.lines_table.setItemDelegateForColumn(LinesModel.COL_PRICE, self.double_delegate)

        self.lines_table.clicked.connect(self.on_table_clicked)
        if not self.invoice_id:
            self.lines_model.add_empty_row()
        self.lines_model.dataChanged.connect(self.on_line_data_changed)
        self.lines_model.dataChanged.connect(lambda *_: self.update_warehouse_availability_label())
        left_layout.addWidget(self.lines_table)

        btn_line_layout = QHBoxLayout()
        self.add_line_btn = QPushButton("➕ إضافة بند (Insert)")
        self.add_line_btn.clicked.connect(self.add_empty_line)
        self.remove_line_btn = QPushButton("🗑 حذف البند المحدد (Delete)")
        self.remove_line_btn.clicked.connect(self.remove_selected_line)
        btn_line_layout.addWidget(self.add_line_btn)
        btn_line_layout.addWidget(self.remove_line_btn)
        left_layout.addLayout(btn_line_layout)

        left_layout.addWidget(QLabel("ملاحظات عامة:"))
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        left_layout.addWidget(self.notes_edit)

        main_layout.addWidget(left_panel, 2)
        main_layout.addWidget(right_panel, 1)

        self.discount_value.valueChanged.connect(self.update_total_display)
        self.discount_type.currentIndexChanged.connect(self.update_total_display)
        self.paid_spin.valueChanged.connect(self.on_paid_changed)
        self.full_payment_btn.clicked.connect(self.set_paid_full)
        self.no_payment_btn.clicked.connect(self.set_paid_zero)
        self.save_btn.clicked.connect(self.on_save)
        self.print_btn.clicked.connect(self.print_invoice_professional)
        self.cancel_btn.clicked.connect(self.reject)

    def _first_empty_line_row(self):
        for row, line in enumerate(self.lines_model.lines):
            if not line.get('item_id'):
                return row
        return None

    def _target_line_for_new_item(self):
        row = self._first_empty_line_row()
        if row is None:
            self.add_empty_line()
            row = self.lines_model.rowCount() - 1
        return row

    def _find_line_by_item_id(self, item_id):
        try:
            item_id = int(item_id)
        except Exception:
            return None
        for row, line in enumerate(self.lines_model.lines):
            try:
                if line.get('item_id') is not None and int(line.get('item_id')) == item_id:
                    return row
            except Exception:
                continue
        return None

    def _increment_existing_line(self, row, qty):
        if row is None or row < 0 or row >= self.lines_model.rowCount():
            return False
        line = self.lines_model.lines[row]
        try:
            qty = Decimal(str(qty))
            line['qty'] = Decimal(str(line.get('qty', 0))) + qty
            line['total'] = line['qty'] * Decimal(str(line.get('price', 0)))
            self.lines_model.dataChanged.emit(
                self.lines_model.index(row, LinesModel.COL_QUANTITY),
                self.lines_model.index(row, LinesModel.COL_TOTAL)
            )
            self.lines_table.selectRow(row)
            self.mark_dirty()
            self.update_total_display()
            return True
        except Exception:
            return False


    def _load_warehouses(self):
        try:
            warehouses = warehouse_service.warehouses()
        except Exception:
            warehouses = []
        self.warehouse_combo.clear()
        default_id = None
        try:
            default_id = warehouse_service.default_warehouse_id()
        except Exception:
            pass
        for wh in warehouses:
            self.warehouse_combo.addItem(wh.get('name', f"#{wh.get('id')}"), wh.get('id'))
            if default_id and int(wh.get('id')) == int(default_id):
                self.warehouse_combo.setCurrentIndex(self.warehouse_combo.count() - 1)

    def _selected_warehouse_id(self):
        if not hasattr(self, 'warehouse_combo'):
            return None
        value = self.warehouse_combo.currentData()
        try:
            return int(value) if value else None
        except Exception:
            return None

    def update_warehouse_availability_label(self):
        if not hasattr(self, 'warehouse_availability_label'):
            return
        wh_id = self._selected_warehouse_id()
        if not wh_id:
            self.warehouse_availability_label.setText("لم يتم اختيار مستودع")
            return
        selected = [line for line in getattr(self.lines_model, 'lines', []) if line.get('item_id')]
        if not selected:
            self.warehouse_availability_label.setText("سيتم استخدام المستودع المحدد لهذه الفاتورة")
            return
        parts = []
        for line in selected[:3]:
            try:
                available = warehouse_service.available_qty(int(line.get('item_id')), wh_id)
                parts.append(f"{line.get('item_name','')}: {available}")
            except Exception:
                pass
        self.warehouse_availability_label.setText("المتاح في المستودع: " + " | ".join(parts) if parts else "سيتم استخدام المستودع المحدد لهذه الفاتورة")

    def _stock_available_for_item(self, item_id):
        item = product_service.item_by_id(item_id)
        if not item or item.get('item_type') == 'خدمة':
            return None
        try:
            return Decimal(str(item.get('available', item.get('quantity', 0)) or 0))
        except Exception:
            return Decimal('0')

    def _validate_stock_before_save(self):
        if self.inv_type != 'sale':
            return True
        shortages = []
        totals = {}
        names = {}
        for line in self.lines_model.lines:
            if not line.get('item_id'):
                continue
            item_id = int(line.get('item_id'))
            base_qty = Decimal(str(line.get('qty', 0))) * Decimal(str(line.get('conversion_factor', 1)))
            totals[item_id] = totals.get(item_id, Decimal('0')) + base_qty
            names[item_id] = line.get('item_name', str(item_id))
        for item_id, needed in totals.items():
            available = self._stock_available_for_item(item_id)
            if available is not None and needed > available:
                shortages.append(f"{names.get(item_id, item_id)}: المطلوب {needed}، المتاح {available}")
        if shortages:
            QMessageBox.warning(self, "المخزون غير كافٍ", "لا يمكن حفظ الفاتورة بسبب نقص المخزون:\n" + "\n".join(shortages))
            return False
        return True

    def _set_paid_value(self, value, manual=False):
        self._updating_payment = True
        try:
            self.paid_spin.setValue(float(value))
        finally:
            self._updating_payment = False
        if manual:
            self._paid_manually_changed = True

    def on_paid_changed(self, value):
        if not self._updating_payment:
            self._paid_manually_changed = True
        self.update_total_display()

    def set_paid_full(self):
        self._set_paid_value(getattr(self, 'total_after_discount', Decimal('0')), manual=True)
        self.update_total_display()

    def set_paid_zero(self):
        self._set_paid_value(0, manual=True)
        self.update_total_display()

    def load_entities(self):
        if self.inv_type == 'sale':
            self.customers = catalog_service.customers()
            names = ["نقدي"] + [c.get('name', '') for c in self.customers if c.get('name')]
        else:
            self.suppliers = catalog_service.suppliers()
            names = ["نقدي"] + [s.get('name', '') for s in self.suppliers if s.get('name')]
        self.entity_completer.setModel(QStringListModel(names))

    def on_entity_text_changed(self, text):
        if not text.strip() or text.strip() == "نقدي":
            self.selected_entity_id = None
            self.balance_label.setText("")
            return
        if self.inv_type == 'sale':
            for c in self.customers:
                if c['name'] == text.strip():
                    self.selected_entity_id = c['id']
                    balance_display = currency.convert(c['balance'], 'USD', self.display_curr)
                    self.balance_label.setText(f"رصيد العميل: {currency.format_amount(balance_display)}")
                    return
        else:
            for s in self.suppliers:
                if s['name'] == text.strip():
                    self.selected_entity_id = s['id']
                    balance_display = currency.convert(s['balance'], 'USD', self.display_curr)
                    self.balance_label.setText(f"رصيد المورد: {currency.format_amount(balance_display)}")
                    return
        self.selected_entity_id = None
        self.balance_label.setText("⚠️ جهة غير مسجلة (سيتم التعامل كنقدي)")

    def on_entity_selected(self, text):
        self.entity_search.setText(text)
        self.on_entity_text_changed(text)

    def add_new_entity(self):
        from views.dialogs.add_entity_dialog import AddEntityDialog
        dialog = AddEntityDialog(self, self.inv_type)
        if dialog.exec():
            self.load_entities()
            self.entity_search.setText(dialog.entity_name)
            self.on_entity_text_changed(dialog.entity_name)

    def load_items_for_combo(self):
        items = catalog_service.items()
        self.items_for_combo = []
        for it in items:
            price = it.get('selling_price', 0) if self.inv_type == 'sale' else it.get('purchase_price', 0)
            price_display = currency.convert(price, 'USD', self.display_curr)
            units = catalog_service.item_units(it['id'])
            units_list = [{'id': None, 'unit_name': it.get('unit', 'قطعة'), 'conversion_factor': Decimal('1')}]
            for u in units:
                factor = Decimal(str(u.get('conversion_factor', 1)))
                if factor == 0:
                    factor = Decimal('1')
                units_list.append({'id': u['id'], 'unit_name': u['unit_name'], 'conversion_factor': factor})
            self.items_for_combo.append({
                'id': it['id'],
                'name': it['name'],
                'unit': it.get('unit', 'قطعة'),
                'price': price_display,
                'units_list': units_list
            })
        if hasattr(self, 'item_delegate'):
            self.item_delegate.items = self.items_for_combo

    def add_empty_line(self):
        self.mark_dirty()
        self.lines_model.add_empty_row()
        new_row = self.lines_model.rowCount() - 1
        self.lines_table.scrollTo(self.lines_model.index(new_row, 0))

    def remove_selected_line(self):
        self.mark_dirty()
        selected = self.lines_table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            if self.lines_model.rowCount() == 1 and self.lines_model.lines[0]['item_id'] is None:
                self.lines_model.lines[0]['item_name'] = ''
                self.lines_model.lines[0]['qty'] = Decimal('1')
                self.lines_model.lines[0]['price'] = Decimal('0')
                self.lines_model.lines[0]['total'] = Decimal('0')
                self.lines_model.dataChanged.emit(self.lines_model.index(0, 0), self.lines_model.index(0, self.lines_model.columnCount()-1))
            else:
                self.lines_model.remove_row(row)
        self.update_total_display()

    def on_table_clicked(self, index):
        if index.column() == LinesModel.COL_DELETE:
            self.remove_selected_line()

    def on_line_data_changed(self, topLeft, bottomRight):
        self.update_total_display()
        last_row = self.lines_model.rowCount() - 1
        if last_row >= 0 and self.lines_model.lines[last_row]['item_id'] is not None:
            self.add_empty_line()

    def update_total_display(self):
        total_before = Decimal('0')
        for line in self.lines_model.lines:
            if line.get('item_id'):
                total_before += line['total']
        discount = Decimal(str(self.discount_value.value()))
        if self.discount_type.currentText() == "نسبة %":
            discount_amount = total_before * discount / 100
        else:
            discount_amount = discount
        total_after = total_before - discount_amount

        self.total_before_label.setText(f"الإجمالي قبل الخصم: {currency.format_amount(total_before)}")
        self.discount_amount_label.setText(f"الخصم: {currency.format_amount(discount_amount)}")
        self.total_after_label.setText(f"الإجمالي بعد الخصم: {currency.format_amount(total_after)}")
        if not self._paid_manually_changed and not self.invoice_id:
            self._set_paid_value(total_after, manual=False)
        paid = Decimal(str(self.paid_spin.value()))
        if paid > total_after:
            paid = total_after
        remaining = total_after - paid
        self.remaining_label.setText(f"المتبقي: {currency.format_amount(remaining)}")

        self.total_before_discount = total_before
        self.discount_amount = discount_amount
        self.total_after_discount = total_after

    def scan_barcode_with_camera(self):
        try:
            from views.dialogs.barcode_camera_dialog import BarcodeCameraDialog
            dialog = BarcodeCameraDialog(self)
            dialog.barcode_scanned.connect(self.on_camera_barcode_scanned)
            dialog.exec()
        except Exception as e:
            show_toast(f"تعذر تشغيل مسح الكاميرا: {e}", "error", self)

    def on_camera_barcode_scanned(self, value, symbology=None):
        self.search_input.setText(str(value or '').strip())
        self.add_item_from_search()

    def add_item_from_search(self):
        text = self.search_input.text().strip()
        if not text:
            return
        try:
            item = product_service.item_by_barcode(text)
            if not item:
                items = catalog_service.items(search=text)
                if items:
                    item = items[0]
            if item:
                existing_row = self._find_line_by_item_id(item['id'])
                if existing_row is not None and product_service.item_by_barcode(text):
                    self._increment_existing_line(existing_row, Decimal('1'))
                    self.search_input.clear()
                    self.search_input.setFocus()
                    show_toast("تمت زيادة كمية المادة الموجودة", "success", self)
                    return
                last_row = self._target_line_for_new_item()
                price = item.get('selling_price', 0) if self.inv_type == 'sale' else item.get('purchase_price', 0)
                price_display = currency.convert(price, 'USD', self.display_curr)
                units = catalog_service.item_units(item['id'])
                units_list = [{'id': None, 'unit_name': item.get('unit', 'قطعة'), 'conversion_factor': Decimal('1')}]
                for u in units:
                    factor = Decimal(str(u.get('conversion_factor', 1)))
                    if factor == 0:
                        factor = Decimal('1')
                    units_list.append({'id': u['id'], 'unit_name': u['unit_name'], 'conversion_factor': factor})
                self.lines_model.set_item(last_row, item['id'], item['name'], units_list, price_display)
                self.lines_table.selectRow(last_row)
                self.search_input.clear()
                self.search_input.setFocus()
                self.update_total_display()
            else:
                reply = QMessageBox.question(self, "مادة غير موجودة", f"لم يتم العثور على '{text}'. هل تريد إضافتها كمنتج جديد؟",
                                             QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.open_add_item_dialog(text)
        except Exception as e:
            show_toast(f"حدث خطأ أثناء إضافة البند: {str(e)}", "error", self)

    def open_add_item_dialog(self, prefill_name):
        from views.dialogs.item_dialog import ItemDialog
        dialog = ItemDialog(self)
        dialog.name_edit.setText(prefill_name)
        if dialog.exec():
            self.load_items_for_combo()
            self.add_item_from_search()

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Insert"), self, self.add_empty_line)
        QShortcut(QKeySequence("Delete"), self, self.remove_selected_line)
        QShortcut(QKeySequence("Ctrl+Return"), self, self.on_save)
        QShortcut(QKeySequence("Ctrl+S"), self, self.on_save)
        QShortcut(QKeySequence("Escape"), self, self.reject)
        QShortcut(QKeySequence("F6"), self, self.print_invoice_professional)
        QShortcut(QKeySequence("F8"), self, lambda: self.discount_value.setFocus())
        QShortcut(QKeySequence("Ctrl+L"), self, lambda: self.search_input.setFocus())
        self.watch_dirty_widgets([
            self.entity_search, self.ref_edit, self.date_edit, self.notes_edit,
            self.discount_type, self.discount_value, self.paid_spin, self.search_input
        ], reset=True)

    def on_save(self):
        validator = FormValidator()
        lines = self.lines_model.get_lines_data()
        if not lines:
            validator.custom(False, self.search_input, self.form_error_label, "أضف بنداً واحداً على الأقل قبل حفظ الفاتورة")
            validator.focus_first_invalid()
            show_toast("أضف بنداً واحداً على الأقل", "error", self)
            return
        FormValidator.clear(self.form_error_label, self.search_input)
        if not self._validate_stock_before_save():
            return
        total_usd = currency.convert(self.total_after_discount, self.display_curr, 'USD')
        paid_display = Decimal(str(self.paid_spin.value()))
        paid_usd = currency.convert(paid_display, self.display_curr, 'USD')
        if paid_usd > total_usd:
            paid_usd = total_usd
        entity_id = self.selected_entity_id
        reference = self.ref_edit.text().strip()
        if not reference:
            reference = invoice_service.next_reference(self.inv_type)
        else:
            if invoice_service.reference_exists(reference, exclude_invoice_id=self.invoice_id):
                show_toast("المرجع موجود مسبقاً", "error", self)
                return
        data = {
            'type': self.inv_type,
            'customer_id': entity_id if self.inv_type == 'sale' else None,
            'supplier_id': entity_id if self.inv_type == 'purchase' else None,
            'date': self.date_edit.date().toString("yyyy-MM-dd"),
            'reference': reference,
            'notes': self.notes_edit.toPlainText().strip(),
            'total': total_usd,
            'paid_amount': paid_usd,
            'lines': lines,
            'exchange_rate_to_usd': float(currency.get_current_rate(self.display_curr)),
            'original_currency': self.display_curr,
            'warehouse_id': self._selected_warehouse_id()
        }
        try:
            if self.invoice_id:
                invoice_service.update(self.invoice_id, data)
                show_toast("تم تعديل الفاتورة", "success", self)
            else:
                invoice_id = invoice_service.create(data)
                show_toast("تم حفظ الفاتورة", "success", self)
            self.accept()
        except Exception as e:
            show_toast(str(e), "error", self)

    def print_invoice_professional(self):
        from printing.printing_service import printing_service
        inv_ref = self.ref_edit.text() or "جديدة"
        inv_date = self.date_edit.date().toString("yyyy-MM-dd")
        if self.selected_entity_id:
            if self.inv_type == 'sale':
                cust = next((c for c in self.customers if c.get('id') == self.selected_entity_id), None)
                entity_name = cust.get('name', 'نقدي') if cust else "نقدي"
            else:
                supp = next((s for s in self.suppliers if s.get('id') == self.selected_entity_id), None)
                entity_name = supp.get('name', 'نقدي') if supp else "نقدي"
        else:
            entity_name = "نقدي"

        lines = []
        for line in self.lines_model.lines:
            if line.get('item_id'):
                lines.append({
                    'item_name': line.get('item_name', ''),
                    'quantity': str(line.get('qty', '')),
                    'unit': line.get('unit_display', ''),
                    'unit_price': currency.format_amount(line.get('price', 0)),
                    'total': currency.format_amount(line.get('total', 0)),
                })
        total_before = self.total_before_discount if hasattr(self, 'total_before_discount') else 0
        discount_amt = self.discount_amount if hasattr(self, 'discount_amount') else 0
        total_after = self.total_after_discount if hasattr(self, 'total_after_discount') else 0
        paid = self.paid_spin.value()
        remaining = total_after - paid
        invoice_payload = {
            'type': self.inv_type,
            'reference': inv_ref,
            'date': inv_date,
            'entity_name': entity_name,
            'lines': lines,
            'total_before_discount': currency.format_amount(total_before),
            'discount': currency.format_amount(discount_amt),
            'total': currency.format_amount(total_after),
            'paid_amount': currency.format_amount(paid),
            'remaining': currency.format_amount(remaining),
            'notes': self.notes_edit.toPlainText().strip(),
        }
        printing_service.invoice_preview(invoice_payload, self, paper='a4')

