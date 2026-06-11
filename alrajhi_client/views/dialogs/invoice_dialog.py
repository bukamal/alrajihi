# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDoubleSpinBox,
                             QDateEdit, QTextEdit, QFormLayout, QMessageBox, QShortcut, QLineEdit,
                             QApplication, QTableView, QHeaderView, QAbstractItemView, QWidget,
                             QStyledItemDelegate, QCompleter, QPushButton, QSpinBox, QCheckBox, QFrame,
                             QSplitter, QSizePolicy)
from PyQt5.QtCore import Qt, QDate, QAbstractTableModel, QModelIndex, QStringListModel, QEvent, QTimer
from PyQt5.QtGui import QKeySequence, QFont
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
    COL_ROW = 0
    COL_BARCODE = 1
    COL_ITEM_NAME = 2
    COL_QUANTITY = 3
    COL_UNIT = 4
    COL_PRICE = 5
    COL_DISCOUNT = 6
    COL_TAX = 7
    COL_TOTAL = 8
    COL_DELETE = 9

    EDITABLE_COLUMNS = (COL_BARCODE, COL_ITEM_NAME, COL_QUANTITY, COL_UNIT, COL_PRICE, COL_DISCOUNT, COL_TAX)

    def __init__(self, inv_type, parent=None):
        super().__init__(parent)
        self.inv_type = inv_type
        self.display_curr = currency.get_display_currency()
        self.lines = []

    def rowCount(self, parent=QModelIndex()):
        return len(self.lines)

    def columnCount(self, parent=QModelIndex()):
        return 10

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        line = self.lines[row]
        if col == self.COL_DELETE:
            if role == Qt.DisplayRole:
                return "🗑"
            if role == Qt.TextAlignmentRole:
                return Qt.AlignCenter
            return None
        if role == Qt.TextAlignmentRole:
            if col in (self.COL_ROW, self.COL_QUANTITY, self.COL_PRICE, self.COL_DISCOUNT, self.COL_TAX, self.COL_TOTAL):
                return Qt.AlignCenter
            return Qt.AlignVCenter | Qt.AlignRight
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if col == self.COL_ROW:
                return row + 1
            if col == self.COL_BARCODE:
                return line.get('barcode', '')
            if col == self.COL_ITEM_NAME:
                return line.get('item_name', '')
            if col == self.COL_QUANTITY:
                return f"{line['qty']:.2f}"
            if col == self.COL_UNIT:
                return line.get('unit_display', '')
            if col == self.COL_PRICE:
                return f"{line['price']:.2f}"
            if col == self.COL_DISCOUNT:
                return f"{line.get('discount_percent', Decimal('0')):.2f}"
            if col == self.COL_TAX:
                return f"{line.get('tax_percent', Decimal('0')):.2f}"
            if col == self.COL_TOTAL:
                return f"{line['total']:.2f} {self.display_curr}"
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        row = index.row()
        col = index.column()
        line = self.lines[row]
        try:
            if col == self.COL_BARCODE:
                line['barcode'] = str(value or '').strip()
            elif col == self.COL_QUANTITY:
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
            elif col == self.COL_DISCOUNT:
                discount = Decimal(str(value))
                if discount < 0 or discount > 100:
                    return False
                line['discount_percent'] = discount
            elif col == self.COL_TAX:
                tax = Decimal(str(value))
                if tax < 0 or tax > 100:
                    return False
                line['tax_percent'] = tax
            else:
                return False
            self.update_row_total(row)
            self.dataChanged.emit(index, index)
            return True
        except Exception:
            return False

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        if index.column() == self.COL_DELETE:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() in self.EDITABLE_COLUMNS:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            headers = ["#", "الباركود", "المادة", "الكمية", "الوحدة", "السعر", "خصم %", "ضريبة %", "الإجمالي", ""]
            return headers[section]
        return None

    def add_empty_row(self):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.lines.append({
            'item_id': None,
            'barcode': '',
            'item_name': '',
            'qty': Decimal('1'),
            'unit_id': None,
            'unit_display': '',
            'conversion_factor': Decimal('1'),
            'price': Decimal('0'),
            'discount_percent': Decimal('0'),
            'tax_percent': Decimal('0'),
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
            if self.rowCount() > 0:
                self.dataChanged.emit(self.index(0, self.COL_ROW), self.index(self.rowCount() - 1, self.COL_ROW))

    def set_item(self, row, item_id, item_name, units_data, default_price, barcode=''):
        if 0 <= row < self.rowCount():
            self.lines[row]['item_id'] = item_id
            self.lines[row]['item_name'] = item_name
            self.lines[row]['barcode'] = barcode or ''
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
            self.update_row_total(row)
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
            item = product_service.item_by_id(item_id) if item_id else None
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
                'barcode': (item or {}).get('barcode', '') or (item or {}).get('code', '') or '',
                'item_name': val(line, 'item_name', '') or '',
                'qty': quantity,
                'unit_id': current_unit_id,
                'unit_display': current_unit,
                'conversion_factor': current_factor,
                'price': price_display,
                'discount_percent': Decimal(str(val(line, 'discount_percent', 0) or 0)),
                'tax_percent': Decimal(str(val(line, 'tax_percent', 0) or 0)),
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
            if Decimal(str(line.get('qty', 0))) <= 0:
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
                'description': line.get('notes', ''),
                'discount_percent': float(line.get('discount_percent', Decimal('0'))),
                'tax_percent': float(line.get('tax_percent', Decimal('0')))
            })
        return result

    def update_row_total(self, row):
        if 0 <= row < self.rowCount():
            line = self.lines[row]
            subtotal = Decimal(str(line.get('qty', 0))) * Decimal(str(line.get('price', 0)))
            discount_percent = Decimal(str(line.get('discount_percent', 0)))
            tax_percent = Decimal(str(line.get('tax_percent', 0)))
            after_discount = subtotal - (subtotal * discount_percent / Decimal('100'))
            line['total'] = after_discount + (after_discount * tax_percent / Decimal('100'))
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
        self.resize(1280, 760)
        self.setMinimumSize(1120, 680)

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

    def _invoice_accent(self):
        return "#2563eb" if self.inv_type == 'sale' else "#7c3aed"

    def _apply_modern_invoice_style(self):
        accent = self._invoice_accent()
        self.setStyleSheet(f"""
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
            QFrame#HeaderCard, QFrame#TotalsCard, QFrame#ActionCard {{
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 14px;
            }}
            QFrame#RightPanel {{
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 14px;
            }}
            QLabel#SectionTitle {{
                color: #0f172a;
                font-size: 14px;
                font-weight: 700;
            }}
            QLabel#muted {{
                color: #64748b;
                font-size: 11px;
            }}
            QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox {{
                min-height: 34px;
                border: 1px solid #cbd5e1;
                border-radius: 9px;
                padding: 5px 9px;
                background: #ffffff;
                font-size: 13px;
            }}
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus {{
                border: 1px solid {accent};
                background: #f8fbff;
            }}
            QTextEdit {{
                border: 1px solid #cbd5e1;
                border-radius: 9px;
                padding: 7px;
                background: #ffffff;
            }}
            QTableView {{
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
            }}
            QPushButton#danger {{
                color: #b91c1c;
                border-color: #fecaca;
                background: #fff1f2;
            }}
            QPushButton#softAction {{
                background: #f8fafc;
            }}
            QLabel#TotalMain {{
                color: {accent};
                font-size: 18px;
                font-weight: 800;
            }}
            QLabel#TotalPaid {{
                color: #15803d;
                font-size: 14px;
                font-weight: 800;
            }}
            QLabel#TotalRemaining {{
                color: #b91c1c;
                font-size: 14px;
                font-weight: 800;
            }}
        """)

    def _make_field_block(self, label_text, widget, stretch=1):
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        label = QLabel(label_text)
        label.setObjectName("muted")
        layout.addWidget(label)
        layout.addWidget(widget)
        box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return box

    def init_ui(self):
        self._apply_modern_invoice_style()
        root_layout = QVBoxLayout(self.content_widget)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        title_frame = QFrame()
        title_frame.setObjectName("HeaderCard")
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(16, 12, 16, 12)
        title_layout.setSpacing(12)

        title_box = QVBoxLayout()
        title = QLabel("فاتورة بيع" if self.inv_type == 'sale' else "فاتورة شراء")
        title.setObjectName("DialogTitle")
        subtitle = QLabel("إدخال سريع للمواد، المستودع، الدفع، والطباعة من نافذة واحدة")
        subtitle.setObjectName("DialogSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        title_layout.addLayout(title_box)
        title_layout.addStretch()

        self.new_btn = QPushButton("جديد")
        self.new_btn.setObjectName("softAction")
        self.save_btn = QPushButton("حفظ Ctrl+S")
        self.save_btn.setObjectName("primary")
        self.print_btn = QPushButton("طباعة F6")
        self.print_btn.setObjectName("softAction")
        self.cancel_btn = QPushButton("إلغاء Esc")
        for btn in (self.new_btn, self.save_btn, self.print_btn, self.cancel_btn):
            btn.setMinimumWidth(96)
            title_layout.addWidget(btn)
        root_layout.addWidget(title_frame)

        self.form_error_label = make_error_label()
        root_layout.addWidget(self.form_error_label)

        header_frame = QFrame()
        header_frame.setObjectName("HeaderCard")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(14, 12, 14, 12)
        header_layout.setSpacing(10)
        header_title = QLabel("بيانات الفاتورة")
        header_title.setObjectName("SectionTitle")
        header_layout.addWidget(header_title)

        self.entity_search = QLineEdit()
        self.entity_search.setPlaceholderText("نقدي أو ابدأ بكتابة الاسم")
        self.entity_search.textChanged.connect(self.on_entity_text_changed)
        self.entity_completer = QCompleter()
        self.entity_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.entity_completer.activated.connect(self.on_entity_selected)
        self.entity_search.setCompleter(self.entity_completer)

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)

        self.warehouse_combo = QComboBox()
        self._load_warehouses()
        self.warehouse_combo.currentIndexChanged.connect(lambda *_: self.update_warehouse_availability_label())

        self.ref_edit = QLineEdit()
        self.ref_edit.setPlaceholderText("يُولد تلقائياً عند تركه فارغاً")

        self.balance_label = QLabel()
        self.balance_label.setObjectName("muted")
        self.balance_label.setWordWrap(True)

        row1 = QHBoxLayout()
        row1.setSpacing(10)
        row1.addWidget(self._make_field_block("العميل" if self.inv_type == 'sale' else "المورد", self.entity_search), 2)
        row1.addWidget(self._make_field_block("التاريخ", self.date_edit), 1)
        row1.addWidget(self._make_field_block("المرجع", self.ref_edit), 1)
        header_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(10)
        row2.addWidget(self._make_field_block("المستودع" if self.inv_type == 'sale' else "مستودع الاستلام", self.warehouse_combo), 2)
        self.add_entity_btn = QPushButton("إضافة عميل" if self.inv_type == 'sale' else "إضافة مورد")
        self.add_entity_btn.setObjectName("softAction")
        self.add_entity_btn.clicked.connect(self.add_new_entity)
        row2.addWidget(self._make_field_block("إجراء سريع", self.add_entity_btn), 1)
        row2.addStretch(1)
        header_layout.addLayout(row2)

        header_layout.addWidget(self.balance_label)
        root_layout.addWidget(header_frame)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        search_frame = QFrame()
        search_frame.setObjectName("ActionCard")
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(12, 10, 12, 10)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("حقل الباركود / بحث المادة — امسح الباركود ثم Enter")
        self.search_input.returnPressed.connect(self.add_item_from_search)
        self.camera_scan_btn = QPushButton("📷 مسح")
        self.camera_scan_btn.setObjectName("softAction")
        self.camera_scan_btn.setToolTip("مسح باركود أو QR بالكاميرا. يعمل قارئ USB أيضًا داخل حقل البحث مباشرة.")
        self.camera_scan_btn.clicked.connect(self.scan_barcode_with_camera)
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(self.camera_scan_btn)
        left_layout.addWidget(search_frame)

        self.lines_model = LinesModel(self.inv_type)
        self.lines_table = QTableView()
        self.lines_table.setModel(self.lines_model)
        self.lines_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.lines_table.setAlternatingRowColors(True)
        self.lines_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.lines_table.verticalHeader().setVisible(False)
        self.lines_table.verticalHeader().setDefaultSectionSize(38)
        self.lines_table.setShowGrid(True)
        header = self.lines_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionResizeMode(LinesModel.COL_ITEM_NAME, QHeaderView.Stretch)
        self.lines_table.setColumnWidth(LinesModel.COL_ROW, 42)
        self.lines_table.setColumnWidth(LinesModel.COL_BARCODE, 135)
        self.lines_table.setColumnWidth(LinesModel.COL_QUANTITY, 88)
        self.lines_table.setColumnWidth(LinesModel.COL_UNIT, 95)
        self.lines_table.setColumnWidth(LinesModel.COL_PRICE, 105)
        self.lines_table.setColumnWidth(LinesModel.COL_DISCOUNT, 78)
        self.lines_table.setColumnWidth(LinesModel.COL_TAX, 78)
        self.lines_table.setColumnWidth(LinesModel.COL_TOTAL, 130)
        self.lines_table.setColumnWidth(LinesModel.COL_DELETE, 48)
        self.lines_table.installEventFilter(self)

        from views.dialogs.invoice_delegates import ItemComboDelegate, UnitComboBoxDelegate, DoubleSpinDelegate
        self.item_delegate = ItemComboDelegate(self.items_for_combo, self.lines_table)
        self.lines_table.setItemDelegateForColumn(LinesModel.COL_ITEM_NAME, self.item_delegate)
        self.unit_delegate = UnitComboBoxDelegate()
        self.lines_table.setItemDelegateForColumn(LinesModel.COL_UNIT, self.unit_delegate)
        self.double_delegate = DoubleSpinDelegate()
        self.lines_table.setItemDelegateForColumn(LinesModel.COL_QUANTITY, self.double_delegate)
        self.lines_table.setItemDelegateForColumn(LinesModel.COL_PRICE, self.double_delegate)
        self.lines_table.setItemDelegateForColumn(LinesModel.COL_DISCOUNT, self.double_delegate)
        self.lines_table.setItemDelegateForColumn(LinesModel.COL_TAX, self.double_delegate)

        self.lines_table.clicked.connect(self.on_table_clicked)
        if not self.invoice_id:
            self.lines_model.add_empty_row()
        self.lines_model.dataChanged.connect(self.on_line_data_changed)
        self.lines_model.dataChanged.connect(lambda *_: self.update_warehouse_availability_label())
        left_layout.addWidget(self.lines_table, 1)

        btn_line_layout = QHBoxLayout()
        self.add_line_btn = QPushButton("➕ إضافة بند Insert")
        self.add_line_btn.setObjectName("softAction")
        self.add_line_btn.clicked.connect(self.add_empty_line)
        self.remove_line_btn = QPushButton("🗑 حذف البند Delete")
        self.remove_line_btn.setObjectName("danger")
        self.remove_line_btn.clicked.connect(self.remove_selected_line)
        btn_line_layout.addWidget(self.add_line_btn)
        btn_line_layout.addWidget(self.remove_line_btn)
        btn_line_layout.addStretch()
        left_layout.addLayout(btn_line_layout)

        left_layout.addWidget(QLabel("ملاحظات عامة:"))
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(78)
        left_layout.addWidget(self.notes_edit)

        right_panel = QFrame()
        right_panel.setObjectName("RightPanel")
        right_panel.setFixedWidth(330)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(14, 14, 14, 14)
        right_layout.setSpacing(10)

        totals_title = QLabel("ملخص الفاتورة")
        totals_title.setObjectName("SectionTitle")
        right_layout.addWidget(totals_title)

        self.warehouse_availability_label = QLabel("اختر مستودعاً لعرض الرصيد المتاح")
        self.warehouse_availability_label.setObjectName("muted")
        self.warehouse_availability_label.setWordWrap(True)
        right_layout.addWidget(self.warehouse_availability_label)

        self.discount_type = QComboBox()
        self.discount_type.addItems(["نسبة %", "مبلغ"])
        self.discount_value = QDoubleSpinBox()
        self.discount_value.setRange(0, 999999999)
        self.discount_value.setDecimals(2)
        self.discount_value.setPrefix(f"{self.symbol} ")
        discount_container = QWidget()
        discount_layout = QHBoxLayout(discount_container)
        discount_layout.setContentsMargins(0, 0, 0, 0)
        discount_layout.setSpacing(8)
        discount_layout.addWidget(self.discount_type, 1)
        discount_layout.addWidget(self.discount_value, 2)
        right_layout.addWidget(self._make_field_block("الخصم", discount_container))

        self.paid_spin = QDoubleSpinBox()
        self.paid_spin.setRange(0, 999999999)
        self.paid_spin.setDecimals(2)
        self.paid_spin.setPrefix(f"{self.symbol} ")
        right_layout.addWidget(self._make_field_block("المدفوع", self.paid_spin))

        payment_tools = QHBoxLayout()
        self.full_payment_btn = QPushButton("دفع كامل")
        self.full_payment_btn.setObjectName("softAction")
        self.no_payment_btn = QPushButton("آجل")
        self.no_payment_btn.setObjectName("softAction")
        payment_tools.addWidget(self.full_payment_btn)
        payment_tools.addWidget(self.no_payment_btn)
        right_layout.addLayout(payment_tools)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #e2e8f0;")
        right_layout.addWidget(separator)

        self.total_before_label = QLabel("الإجمالي قبل الخصم: 0")
        self.discount_amount_label = QLabel("الخصم: 0")
        self.total_after_label = QLabel("الإجمالي بعد الخصم: 0")
        self.remaining_label = QLabel("المتبقي: 0")
        self.total_after_label.setObjectName("TotalMain")
        self.remaining_label.setObjectName("TotalRemaining")
        self.total_before_label.setObjectName("TotalPaid")
        for lbl in (self.total_before_label, self.discount_amount_label, self.total_after_label, self.remaining_label):
            lbl.setWordWrap(True)
            right_layout.addWidget(lbl)

        right_layout.addStretch()
        hint = QLabel("اختصارات: Ctrl+S حفظ، F6 طباعة، Insert بند جديد، Delete حذف بند، Ctrl+L بحث المادة، Enter انتقال ذكي داخل الجدول.")
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        right_layout.addWidget(hint)

        content_layout.addWidget(left_panel, 1)
        content_layout.addWidget(right_panel)
        root_layout.addLayout(content_layout, 1)

        self.discount_value.valueChanged.connect(self.update_total_display)
        self.discount_type.currentIndexChanged.connect(self.update_total_display)
        self.paid_spin.valueChanged.connect(self.on_paid_changed)
        self.full_payment_btn.clicked.connect(self.set_paid_full)
        self.no_payment_btn.clicked.connect(self.set_paid_zero)
        self.save_btn.clicked.connect(self.on_save)
        self.print_btn.clicked.connect(self.print_invoice_professional)
        self.cancel_btn.clicked.connect(self.reject)
        self.new_btn.clicked.connect(self._clear_invoice_form)
        QTimer.singleShot(0, self.focus_barcode_input)


    def focus_barcode_input(self):
        """Keep barcode/item quick-entry ready for continuous invoicing."""
        if hasattr(self, 'search_input') and self.search_input is not None:
            self.search_input.setFocus()
            self.search_input.selectAll()

    def _clear_invoice_form(self):
        if self.invoice_id:
            show_toast("زر جديد متاح عند إنشاء فاتورة جديدة فقط", "warning", self)
            return
        self.entity_search.clear()
        self.selected_entity_id = None
        self.ref_edit.clear()
        self.notes_edit.clear()
        self.discount_value.setValue(0)
        self.paid_spin.setValue(0)
        self.lines_model.beginResetModel()
        self.lines_model.lines.clear()
        self.lines_model.endResetModel()
        self.lines_model.add_empty_row()
        self.focus_barcode_input()
        self._paid_manually_changed = False
        self.update_total_display()

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
            self.lines_model.update_row_total(row)
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

    def eventFilter(self, obj, event):
        if obj is getattr(self, 'lines_table', None) and event.type() == QEvent.KeyPress:
            key = event.key()
            if key in (Qt.Key_Return, Qt.Key_Enter):
                self._move_to_next_invoice_cell()
                return True
            if key == Qt.Key_Delete:
                self.remove_selected_line()
                return True
        return super().eventFilter(obj, event)

    def _move_to_next_invoice_cell(self):
        index = self.lines_table.currentIndex()
        if not index.isValid():
            self.focus_barcode_input()
            return
        editable = [LinesModel.COL_BARCODE, LinesModel.COL_ITEM_NAME, LinesModel.COL_QUANTITY, LinesModel.COL_UNIT, LinesModel.COL_PRICE, LinesModel.COL_DISCOUNT, LinesModel.COL_TAX]
        row, col = index.row(), index.column()
        if col == LinesModel.COL_BARCODE:
            text = str(self.lines_model.lines[row].get('barcode', '') or '').strip()
            if text and not self.lines_model.lines[row].get('item_id'):
                self.search_input.setText(text)
                self.add_item_from_search()
                return
        next_cols = [c for c in editable if c > col]
        if next_cols:
            next_index = self.lines_model.index(row, next_cols[0])
        else:
            if row == self.lines_model.rowCount() - 1:
                self.add_empty_line()
            next_index = self.lines_model.index(row + 1, LinesModel.COL_BARCODE)
        self.lines_table.setCurrentIndex(next_index)
        self.lines_table.edit(next_index)


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
                'barcode': it.get('barcode') or it.get('code') or '',
                'unit': it.get('unit', 'قطعة'),
                'price': price_display,
                'units_list': units_list
            })
        if hasattr(self, 'item_delegate'):
            self.item_delegate.items = self.items_for_combo
        if hasattr(self, 'search_input'):
            search_terms = []
            for item in self.items_for_combo:
                if item.get('name'):
                    search_terms.append(item['name'])
                if item.get('barcode'):
                    search_terms.append(str(item['barcode']))
            completer = QCompleter(QStringListModel(search_terms), self.search_input)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            self.search_input.setCompleter(completer)

    def add_empty_line(self):
        self.mark_dirty()
        self.lines_model.add_empty_row()
        new_row = self.lines_model.rowCount() - 1
        self.lines_table.scrollTo(self.lines_model.index(new_row, 0))
        self.focus_barcode_input()

    def remove_selected_line(self):
        self.mark_dirty()
        selected = self.lines_table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            if self.lines_model.rowCount() == 1 and self.lines_model.lines[0]['item_id'] is None:
                self.lines_model.lines[0].update({
                    'item_id': None, 'barcode': '', 'item_name': '', 'qty': Decimal('1'),
                    'unit_id': None, 'unit_display': '', 'conversion_factor': Decimal('1'),
                    'price': Decimal('0'), 'discount_percent': Decimal('0'),
                    'tax_percent': Decimal('0'), 'total': Decimal('0'), 'units_data': []
                })
                self.lines_model.dataChanged.emit(self.lines_model.index(0, 0), self.lines_model.index(0, self.lines_model.columnCount()-1))
            else:
                self.lines_model.remove_row(row)
        self.update_total_display()
        self.focus_barcode_input()

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
                    self.focus_barcode_input()
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
                barcode_value = item.get('barcode') or item.get('code') or text if product_service.item_by_barcode(text) else (item.get('barcode') or item.get('code') or '')
                self.lines_model.set_item(last_row, item['id'], item['name'], units_list, price_display, barcode_value)
                self.lines_table.selectRow(last_row)
                self.search_input.clear()
                self.focus_barcode_input()
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
        QShortcut(QKeySequence("Ctrl+L"), self, self.focus_barcode_input)
        QShortcut(QKeySequence("F2"), self, self.focus_barcode_input)
        QShortcut(QKeySequence("Ctrl+N"), self, self._clear_invoice_form)
        self.watch_dirty_widgets([
            self.entity_search, self.ref_edit, self.date_edit, self.notes_edit,
            self.discount_type, self.discount_value, self.paid_spin, self.search_input
        ], reset=True)

    def on_save(self):
        validator = FormValidator()
        partial_rows = []
        for idx, line in enumerate(self.lines_model.lines, start=1):
            has_text = bool(str(line.get('barcode', '')).strip() or str(line.get('item_name', '')).strip())
            if has_text and not line.get('item_id'):
                partial_rows.append(str(idx))
            if line.get('item_id') and Decimal(str(line.get('qty', 0))) <= 0:
                partial_rows.append(str(idx))
        if partial_rows:
            validator.custom(False, self.search_input, self.form_error_label, "يوجد بند ناقص أو كمية غير صحيحة في السطر: " + ", ".join(partial_rows))
            validator.focus_first_invalid()
            show_toast("يوجد بند ناقص داخل جدول الفاتورة", "error", self)
            return
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
                    'barcode': line.get('barcode', ''),
                    'item_name': line.get('item_name', ''),
                    'quantity': str(line.get('qty', '')),
                    'unit': line.get('unit_display', ''),
                    'unit_price': currency.format_amount(line.get('price', 0)),
                    'discount_percent': str(line.get('discount_percent', 0)),
                    'tax_percent': str(line.get('tax_percent', 0)),
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
        printing_service.invoice_preview(invoice_payload, self, paper='default')

