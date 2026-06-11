# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QStyledItemDelegate, QComboBox, QDoubleSpinBox, QLineEdit, QCompleter
from PyQt5.QtCore import Qt, QStringListModel
from decimal import Decimal

class ItemComboDelegate(QStyledItemDelegate):
    def __init__(self, items_list, parent=None):
        super().__init__(parent)
        self.items = items_list

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.setEditable(True)
        for item in self.items:
            combo.addItem(item['name'], item)
        completer = QCompleter()
        model = QStringListModel([item['name'] for item in self.items])
        completer.setModel(model)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        combo.setCompleter(completer)
        combo.currentIndexChanged.connect(lambda: self.commitData.emit(combo))
        return combo

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        idx = editor.findText(value)
        if idx >= 0:
            editor.setCurrentIndex(idx)
        else:
            editor.setEditText(value)

    def setModelData(self, editor, model, index):
        current_text = editor.currentText()
        item_data = editor.currentData()
        if item_data:
            model.set_item(index.row(), item_data['id'], item_data['name'],
                           item_data['units_list'], item_data['price'], item_data.get('barcode', ''))
        else:
            for it in self.items:
                if it['name'] == current_text:
                    model.set_item(index.row(), it['id'], it['name'],
                                   it['units_list'], it['price'], it.get('barcode', ''))
                    break

class UnitComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.setEditable(False)
        return combo

    def setEditorData(self, editor, index):
        model = index.model()
        row = index.row()
        units_data = model.lines[row].get('units_data', [])
        editor.clear()
        current_display = model.data(index, Qt.EditRole)
        current_index = 0
        for i, u in enumerate(units_data):
            editor.addItem(u['unit_name'], (u['id'], u['unit_name'], u['conversion_factor']))
            if u['unit_name'] == current_display:
                current_index = i
        editor.setCurrentIndex(current_index)

    def setModelData(self, editor, model, index):
        selected_data = editor.currentData()
        if selected_data:
            row = index.row()
            try:
                old_factor = Decimal(str(model.lines[row].get('conversion_factor', Decimal('1'))))
            except Exception:
                old_factor = Decimal('1')
            try:
                new_factor = Decimal(str(selected_data[2]))
            except Exception:
                new_factor = Decimal('1')
            if new_factor <= 0:
                new_factor = Decimal('1')

            # تحديث الوحدة وعامل التحويل في النموذج
            model.setData(index, (selected_data[0], selected_data[1], new_factor), Qt.EditRole)

            # تعديل السعر بناءً على نسبة معاملات التحويل.
            # مهم: عمود الوحدة = 4، أما عمود السعر الحقيقي = 5.
            # الخطأ السابق كان يكتب السعر في عمود الوحدة، لذلك لا يتغير الإجمالي عند اختيار وحدة فرعية.
            price_col = getattr(model, 'COL_PRICE', 5)
            if old_factor != new_factor and old_factor > 0:
                old_price = Decimal(str(model.lines[row].get('price', Decimal('0'))))
                new_price = old_price * (new_factor / old_factor)
                model.setData(model.index(row, price_col), new_price, Qt.EditRole)
            else:
                model.update_row_total(row)

            model.dataChanged.emit(model.index(row, 0), model.index(row, model.columnCount() - 1))

class DoubleSpinDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        spin = QDoubleSpinBox(parent)
        spin.setRange(0, 999999999)
        spin.setDecimals(2)
        return spin

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        editor.setValue(float(value))

    def setModelData(self, editor, model, index):
        model.setData(index, Decimal(str(editor.value())), Qt.EditRole)
        model.update_row_total(index.row())


